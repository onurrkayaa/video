#!/usr/bin/env python3
"""Kurgu programına devir sınaması (medya nle → Kdenlive / DaVinci Resolve) için kare kodlu sınama medyası.

  .venv/bin/python testler/nle_sinama.py <proje_klasoru>     # ör. projeler/2026-10-08-nle-sinama

Üretir (proje köküne göre):
  kaynak/A.mov B.mov C.mov D.mov  her karede büyük "A 017" yazısı + altta 16 bitlik kod şeridi (4 bit klip, 12 bit kare);
                                   kare hızları BİLEREK karışık: A, B 30 fps · C 60 fps · D 24 fps (en sık devir hatası)
                                   ses: klip başına ayrı frekans; kaynak saniyesi s'de (s+1) adet 20 ms bip — sayıdan
                                   saniye okunur, giriş noktası kayması (tam saniye dahil) ölçülür
  kaynak/muzik.wav                 48 kHz; her 0,5 sn'de 20 ms ton, k. ton 1500 + 100·k Hz — frekanstan müzik anı okunur
                                   (düzenli tık tam periyotluk kaymayı göremiyordu: 2026-10-08 Kdenlive ölçümü)
  plan/kurgu.json                  kesim, 12 karelik erime, karışık fps, çekim sesi (B) ve müzik (bas 0,5)
  analiz/beklenen.json             zaman çizelgesi karesi → (klip, kaynak karesi) beklentisi ve doğrulama kuralları
Sonra: medya nle plan/kurgu.json --bicim hepsi → cikti/nle/kurgu.otio + kurgu.edl
Çizimden kod okuma: kod_oku(rgb_kare) → (klip_harfi, kare) ya da None (erime gibi karışık kare); bloklar(rgb_kare) →
16 blok parlaklığı (erimede karışım ağırlığı buradan ölçülür: nle_olc.py).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

KOK = Path(__file__).resolve().parents[1]
FF = str(KOK / "arac" / "ffmpeg")
W, H, SERIT, BLOK = 1280, 720, 60, 80
KLIPLER = {"A": (30, 4.0, (40, 90, 160), 440), "B": (30, 4.0, (160, 60, 60), 660),
           "C": (60, 4.0, (50, 140, 80), 880), "D": (24, 4.0, (140, 110, 40), 550)}
FPS = 30
SR = 48000
BIP_SURE, BIP_ARA = 0.02, 0.02                                   # klip sesi: s. saniyede (s+1) bip
TIK_HZ0, TIK_ADIM, TIK_SURE, TIK_ARALIK = 1500, 100, 0.02, 0.5   # müzik: k. ton k·0,5 sn'de, 1500 + 100·k Hz


def _yazi() -> ImageFont.FreeTypeFont:
    for f in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if Path(f).exists():
            return ImageFont.truetype(f, 170)
    return ImageFont.load_default()


def kare(harf: str, i: int, renk, yazi) -> np.ndarray:
    im = Image.new("RGB", (W, H), renk)
    d = ImageDraw.Draw(im)
    d.text((W / 2, (H - SERIT) / 2), f"{harf} {i:03d}", font=yazi, anchor="mm", fill=(255, 255, 255))
    kod = ((ord(harf) - 64) << 12) | i
    for b in range(16):
        bit = (kod >> (15 - b)) & 1
        d.rectangle([b * BLOK, H - SERIT, b * BLOK + BLOK - 1, H - 1], fill=(255, 255, 255) if bit else (0, 0, 0))
    return np.asarray(im)


def bloklar(rgb: np.ndarray) -> np.ndarray:
    """Kod şeridinin 16 bloğunun ortalama parlaklığı (0–255). Erimede iki klibin kodu karışır: blok değeri ağırlığı taşır."""
    h, w = rgb.shape[:2]
    sy = slice(int(h * (H - SERIT * 0.75) / H), int(h * (H - SERIT * 0.25) / H))
    return np.array([float(rgb[sy, int(w * (b * BLOK + BLOK * 0.25) / W):int(w * (b * BLOK + BLOK * 0.75) / W)].mean())
                     for b in range(16)])


def kod_oku(rgb: np.ndarray) -> tuple[str, int] | None:
    """Kod şeridini çözer; blok ortalaması belirsizse (erime, bozulma) None."""
    y = bloklar(rgb)
    if ((y > 60) & (y < 195)).any():
        return None
    kod = int("".join("1" if v >= 195 else "0" for v in y), 2)
    klip, i = kod >> 12, kod & 0xFFF
    return (chr(64 + klip), i) if 1 <= klip <= 4 else None


def _klip(hedef: Path, harf: str) -> None:
    fps, sure, renk, frekans = KLIPLER[harf]
    n = int(round(fps * sure))
    yazi = _yazi()
    ses = hedef.with_suffix(".ses.wav")
    _wav(ses, klip_sesi(frekans, sure))
    p = subprocess.Popen([FF, "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(fps), "-i", "-", "-i", str(ses), "-map", "0:v", "-map", "1:a",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-g", "1", "-pix_fmt", "yuv420p",
                          "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                          "-c:a", "pcm_s16le", "-shortest", str(hedef)], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(kare(harf, i, renk, yazi).tobytes())
    p.stdin.close()
    hata = p.wait()
    ses.unlink(missing_ok=True)
    if hata:
        raise SystemExit(f"{harf} üretilemedi")


def _ton(x: np.ndarray, bas: float, sure: float, hz: float, genlik: float) -> None:
    """x'e bas anından başlayan, kenarları 2 ms yumuşatılmış ton ekler (sıçrama tıkırtısı ve bant taşması olmasın)."""
    i0, n = int(round(bas * SR)), int(round(sure * SR))
    t = np.arange(n) / SR
    zarf = np.minimum(1.0, np.minimum(t, sure - t) / 0.002)
    x[i0:i0 + n] += (genlik * zarf * np.sin(2 * np.pi * hz * t))[: max(0, len(x) - i0)]


def klip_sesi(frekans: float, sure: float) -> np.ndarray:
    """Klibin kaynak saniyesi s'de (s+1) kısa bip: hangi saniyenin duyulduğu sayıdan okunur (giriş noktası ölçülür)."""
    x = np.zeros(int(SR * sure), "<f4")
    for s in range(int(sure)):
        for j in range(s + 1):
            _ton(x, s + j * (BIP_SURE + BIP_ARA), BIP_SURE, frekans, 0.5)
    return x


def muzik_sesi(sure: float = 10.0) -> np.ndarray:
    """Her 0,5 sn'de 20 ms ton; k. tonun frekansı TIK_HZ0 + k·TIK_ADIM: hangi müzik anının çaldığı frekanstan okunur."""
    x = np.zeros(int(SR * sure), "<f4")
    for k in range(int(sure / TIK_ARALIK)):
        _ton(x, k * TIK_ARALIK, TIK_SURE, TIK_HZ0 + k * TIK_ADIM, 0.6)
    return x


def _wav(hedef: Path, x: np.ndarray) -> None:
    subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                    "-c:a", "pcm_s24le", str(hedef)], input=x.astype("<f4").tobytes(), check=True)


def main() -> int:
    p = Path(sys.argv[1]).resolve()
    for d in ("kaynak", "plan", "analiz", "cikti"):
        (p / d).mkdir(parents=True, exist_ok=True)
    for h in KLIPLER:
        _klip(p / "kaynak" / f"{h}.mov", h)
    _wav(p / "kaynak" / "muzik.wav", muzik_sesi())
    k = lambda h: f"kaynak/{h}.mov"
    plan = {"ad": "nle-sinama", "fps": FPS, "boyut": [W, H],
            "muzik": {"dosya": "kaynak/muzik.wav", "bas": 0.5},
            "cekimler": [
                {"no": 1, "kaynak": k("A"), "kaynak_bas": 0.5, "cikti_bas": 0.0, "cikti_son": 2.0, "hiz": 1,
                 "ses": "muzik", "vurusa": False, "gecis": {"tur": "kesim"}},
                {"no": 2, "kaynak": k("B"), "kaynak_bas": 1.0, "cikti_bas": 2.0, "cikti_son": 4.0, "hiz": 1,
                 "ses": "kendi", "vurusa": False, "gecis": {"tur": "kesim"}},
                {"no": 3, "kaynak": k("C"), "kaynak_bas": 0.5, "cikti_bas": 3.6, "cikti_son": 5.6, "hiz": 1,
                 "ses": "muzik", "vurusa": False, "gecis": {"tur": "erime", "sure_kare": 12}},
                {"no": 4, "kaynak": k("D"), "kaynak_bas": 0.25, "cikti_bas": 5.6, "cikti_son": 7.6, "hiz": 1,
                 "ses": "muzik", "vurusa": False, "gecis": {"tur": "kesim"}}]}
    (p / "plan" / "kurgu.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1))
    beklenen = []                                   # zaman çizelgesi karesi (30 fps) → beklenen görüntü
    for t in range(int(7.6 * FPS)):
        if t < 60:
            beklenen.append({"t": t, "klip": "A", "kare": 15 + t})
        elif t < 108:
            beklenen.append({"t": t, "klip": "B", "kare": 30 + (t - 60)})
        elif t < 120:
            beklenen.append({"t": t, "klip": "B+C", "erime": True})
        elif t < 168:
            beklenen.append({"t": t, "klip": "C", "kare": 30 + 2 * (t - 108)})
        else:
            beklenen.append({"t": t, "klip": "D", "kare": int((0.25 + (t - 168) / FPS) * 24), "tolerans": 1})
    (p / "analiz" / "beklenen.json").write_text(json.dumps({
        "kural": "Her zaman çizelgesi karesi kod şeridiyle okunur (testler/nle_sinama.py kod_oku). Kesim kareleri "
                 "(60, 168) ±0 kare; erime 108–119 arası iki klibin karışımı (kod okunamaz); D (24 fps) için ±1 kare; "
                 "C (60 fps) 30 fps zaman çizelgesinde her 2. kaynak karesi. Müzik: k. ton (1500 + 100·k Hz) videoda "
                 "k·0,5 − 0,5 sn'de (müzik dosyasının 0,5. sn'si = video 0). B'nin sesi 2,0–4,0 sn'de (A2 izi): 2,0 sn'de "
                 "2 bip (kaynak 1. sn), 3,0 sn'de 3 bip (kaynak 2. sn). Ölçüm: testler/nle_olc.py.",
        "kareler": beklenen}, ensure_ascii=False, indent=1))
    print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
