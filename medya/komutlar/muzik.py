"""medya muzik <ses|video> [--cikti analiz/muzik.json] [--tik] — vuruş, ölçü başı, bölüm + GÜVEN.

1) Tek bir ana WAV çözülür (48 kHz, 24 bit): analiz de kompozisyon da bu dosyayı kullanır ("ses saattir";
   sıkıştırılmış kaynağı iki kez çözmek 20–40 ms kaydırabilir).
2) Ritim komitesi (medya/isciler/muzik_isci.py, ortamlar/ses): Beat This! ×3 + Essentia + librosa; metrik düzey
   ve faz eşitlenir; uyum ölçülür. guven_seviye: yuksek (vuruşa sert kesim serbest) | orta | dusuk.
3) Görsel teşhis: her 20 sn için başlangıç zarfı + üyelerin vuruşları + ölçü başları (PNG; Read ile bakılır).
4) --tik: insan kontrolü için sol kulak müzik, sağ kulak vuruş tıkı WAV'ı (ölçü başında vurgulu). Claude
   duyamaz; güven yüksek değilse kullanıcıya 1 dakikalık dinleme önerilir.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ..ortak import KOK, MedyaHatasi, calistir, ffmpeg, json_oku, json_yaz, ses_oku
from .kontak import YAZI
from .senkron import baslangic_zarfi

SES_PY = KOK / "ortamlar" / "ses" / "bin" / "python"
ISCI = KOK / "medya" / "isciler" / "muzik_isci.py"


def ana_wav(girdi: str, hedef: Path) -> Path:
    calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", girdi, "-map", "0:a:0", "-vn", "-ac", "2",
              "-ar", "48000", "-c:a", "pcm_s24le", str(hedef)], hata_mesaji="ses çözülemedi")
    return hedef


def analiz(wav: Path, hizli: bool = False) -> dict:
    if not SES_PY.exists():
        raise MedyaHatasi("ses ortamı yok (ortamlar/ses). Kur: medya kur ses-ortami")
    with tempfile.NamedTemporaryFile(suffix=".json") as g:
        komut = [str(SES_PY), str(ISCI), str(Path(wav).resolve()), g.name] + (["--hizli"] if hizli else [])
        r = subprocess.run(komut, capture_output=True, stdin=subprocess.DEVNULL, cwd=KOK)
        if r.returncode:
            raise MedyaHatasi("müzik işçisi başarısız:\n" + r.stderr.decode("utf-8", "replace")[-2000:])
        return json_oku(g.name)


def ciz(wav: Path, sonuc: dict, cikti_kok: Path, pencere: float = 20.0) -> list[Path]:
    x, sr = ses_oku(wav, sr=22050)
    zarf, fps = baslangic_zarfi(x, sr)
    sure = len(x) / sr
    renk = {"beat_this:final0": (240, 240, 240), "beat_this:final1": (170, 170, 170), "beat_this:final2": (120, 120, 120),
            "essentia": (90, 200, 120), "librosa": (200, 120, 220)}
    try:
        f = ImageFont.truetype(YAZI, 13)
    except OSError:
        f = ImageFont.load_default()
    yollar = []
    sayfa_basina = 6
    pencereler = int(np.ceil(sure / pencere))
    for s0 in range(0, pencereler, sayfa_basina):
        W, H = 1800, 150
        n = min(sayfa_basina, pencereler - s0)
        im = Image.new("RGB", (W, n * H + 28), (14, 14, 18)); d = ImageDraw.Draw(im)
        for r in range(n):
            a = (s0 + r) * pencere; b = min(a + pencere, sure); y0 = 6 + r * H
            px = lambda t: 60 + int((t - a) / pencere * (W - 80))
            d.text((4, y0 + 60), f"{a:.0f}s", font=f, fill=(150, 150, 150))
            i0, i1 = int(a * fps), min(int(b * fps), len(zarf))
            for j in range(i0, i1, 2):
                h = int(zarf[j] * (H - 50))
                d.line([(px(j / fps), y0 + H - 12), (px(j / fps), y0 + H - 12 - h)], fill=(60, 100, 160))
            for k, (ad, vs) in enumerate(sonuc.get("uye_vuruslari", {}).items()):
                yk = y0 + 4 + k * 7
                for t in vs:
                    if a <= t < b:
                        d.line([(px(t), yk), (px(t), yk + 6)], fill=renk.get(ad, (200, 200, 0)), width=2)
            for t in sonuc["vuruslar"]:
                if a <= t < b:
                    d.line([(px(t), y0 + 40), (px(t), y0 + H - 12)], fill=(90, 90, 100))
            for t in sonuc["olcu_baslari"]:
                if a <= t < b:
                    d.line([(px(t), y0 + 40), (px(t), y0 + H - 12)], fill=(230, 200, 60), width=3)
        d.text((60, n * H + 8), "üst şeritler: beat_this f0/f1/f2 (beyaz/gri), essentia (yeşil), librosa (mor) · gri: seçilen "
               "vuruş · sarı: ölçü başı · mavi: başlangıç zarfı", font=f, fill=(200, 200, 200))
        yol = cikti_kok.with_name(cikti_kok.stem + f"-{s0 // sayfa_basina + 1}.png")
        im.save(yol); yollar.append(yol)
    return yollar


def tik_wav(wav: Path, sonuc: dict, cikti: Path) -> Path:
    """Sol: müzik, sağ: tık (ölçü başında yüksek ve tiz). ISMIR 2012 dinleme testi biçimi."""
    x, sr = ses_oku(wav, sr=44100)
    sag = np.zeros_like(x)
    olcu = set(round(t, 3) for t in sonuc["olcu_baslari"])
    for t in sonuc["vuruslar"]:
        k = int(t * sr); L = int(0.03 * sr); tt = np.arange(L) / sr
        vurgulu = round(t, 3) in olcu
        tik = np.sin(2 * np.pi * (1800 if vurgulu else 1200) * tt) * np.exp(-tt * 140) * (0.9 if vurgulu else 0.55)
        sag[k:k + L] += tik[: max(0, len(sag) - k)]
    sol = x / (np.abs(x).max() + 1e-9) * 0.8
    import wave
    st = (np.stack([sol, sag], 1).clip(-1, 1) * 32767).astype("<i2")
    with wave.open(str(cikti), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(st.tobytes())
    return cikti


def calistir_(args) -> int:
    cikti = Path(args.cikti or str(Path(args.girdi).with_suffix("")) + "-muzik.json")
    cikti.parent.mkdir(parents=True, exist_ok=True)
    wav = Path(args.ana or cikti.with_name(cikti.stem + "-ana.wav"))
    if not wav.exists() or args.yeniden:
        ana_wav(args.girdi, wav)
    sonuc = analiz(wav, args.hizli)
    sonuc["ana_wav"] = str(wav)
    sonuc["saglayici"] = "komite: beat_this(final0-2)+essentia(multifeature)+librosa"
    sonuc["kural"] = {"yuksek": "vuruşa sert kesim serbest (yine de medya senkron ile ölç)",
                      "orta": "yalnız ölçü başına / bölüm sınırına, erimeli geçişle; vuruş iddia etme",
                      "dusuk": "vuruşa dayalı kesim yok; cümle/bölüm sınırları + erime; kullanıcıya tık dinletisi öner"
                      }[sonuc["guven_seviye"]]
    json_yaz(cikti, sonuc)
    k = sonuc["komite"]
    print(f"güven: {sonuc['guven_seviye'].upper()} — {len(sonuc['vuruslar'])} vuruş, ~{sonuc['bpm_medyan'] or 0:.1f} BPM, "
          f"{len(sonuc['olcu_baslari'])} ölçü başı, {len(sonuc.get('bolumler', []))} bölüm")
    print(f"  komite: seçilen {k['secilen']} (karşı aile {k['karsi_aile']}: F={k['F_aile']}), essentia güveni "
          f"{k['essentia_guven']}, kontrol noktaları F≥{k['F_kontrol_noktalari_min']}, kayma {k['faz_kayma_ms']} ms "
          f"(sabit sapma {k['sabit_sapma_ms']} ms), başlangıç skoru {k['baslangic_skoru']}")
    eksik = [ad for ad, ok in k["kosullar"].items() if not ok]
    if eksik:
        print(f"  'yüksek' için eksik: {', '.join(eksik)}")
    print(f"  kural: {sonuc['kural']}")
    for g in ciz(wav, sonuc, cikti.with_suffix(".png")):
        print(f"  görsel → {g}")
    if args.tik or sonuc["guven_seviye"] != "yuksek":
        t = tik_wav(wav, sonuc, cikti.with_name(cikti.stem + "-tik.wav"))
        print(f"  insan kontrolü (sol müzik, sağ tık) → {t}")
    print(f"→ {cikti}")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="vuruş/ölçü/bölüm + güven (komite)")
    p.add_argument("girdi", help="ses ya da video dosyası")
    p.add_argument("--cikti", help="JSON yolu (ör. projeler/x/analiz/muzik.json)")
    p.add_argument("--ana", help="ana WAV yolu (varsayılan: <cikti>-ana.wav)")
    p.add_argument("--tik", action="store_true", help="tık dinletisi WAV'ı her durumda üret")
    p.add_argument("--hizli", action="store_true", help="yalnız final0 (kontrol noktası uyumu ölçülmez)")
    p.add_argument("--yeniden", action="store_true", help="ana WAV'ı yeniden çöz")
    p.set_defaults(islev=calistir_)
