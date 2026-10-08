"""medya ciz <plan.json> [--cikti cikti/<ad>.mp4] [--crf 16] [--preset medium] [--kok <proje>]
                        [--yalniz-konusma calisma/ses/konusma.wav]

Kurgu planını (plan/kurgu.json, `medya nle` ile aynı sözleşme) HyperFrames'siz, doğrudan ffmpeg ile çizer. Kare dökümü
yok: disk tepesi ≈ çıktı + ses ara dosyası (HyperFrames gerçek çekimde kaynak karelerini diske açar). Gerçek çekim
kurgusu içindir; hareketli grafik, yazı, süslü geçiş HyperFrames'te kalır.

Kapsam: kesim (eslesme = kesim), erime (örtüşme), kadraj (cover + `kadraj.ilgi`, sabit mod), punch / Ken Burns
(`hareket.olcek`), hazır ara klipler (`klip`/`klip_bas`: yavaslat, sdr, cfr), pişmemiş hızlandırma (`hiz > 1`), çekimin
kendi sesi (`ses: kendi`) + müzik (`muzik.dosya`, `muzik.bas`). Kısma: `--yalniz-konusma` konuşma katmanını yazar →
ses-tasarimi `kisma.py` → kısılmış WAV `muzik.dosya` olur (ciz kendi kısma mantığını yazmaz).
Kapsam dışı (hata verir, HyperFrames önerir; sessizce kesime çevirmez): savurma, yakinlasma, isik, flas, siyah-dip,
beyaz-dip, j-kesim/l-kesim, paralaks, kadraj.mod pan/takip/dolgu, fotoğraf, HDR kaynak, `gecis`/`kadraj`/`hareket`
içindeki bilinmeyen anahtarlar. Öteki bilinmeyen alanlar (ör. `yazi`) çizilmez ama hata da vermez — `plan_denetle` uyarır.

Kare kuralı (HyperFrames ile aynı): çıktı karesi n'de çekimin medya anı t = klip_bas|kaynak_bas + (n − bas_n)·hız/fps;
gösterilen kaynak karesi, zamanı ≤ t olan son kare. Kare zamanları ffmpeg 6.0'ın paket zaman damgalarından kesir olarak
hesaplanır (yuvarlama birikmez); çözücü bir anahtar kareden çözer, ilk kare `select=gte(pts,P)` ile tam seçilir (açık
GOP'lu HEVC'de anahtar kareden hemen önceye arama öncü kareleri kaybettiriyor — ölçüldü 2026-10-08).
Erime: gelen çekimin ağırlığı egri((n − bas_n)/örtüşme), örtüşmenin ilk karesinde 0 (GSAP opaklık tween'i gibi),
Y'CbCr'de karıştırılır (opaklık karışımıyla aynı, doğrusal dönüşüm). Hareket: kenburns olcek[0] ilk karede, olcek[1]
son karede (son_n − 1); punch olcek[0]→olcek[1] `kare` karede, sonra durur. Çapa: kadraj.ilgi'nin ekrandaki yeri (yoksa
orta) = GSAP transform-origin. Eğri: `gecis.egri` / `hareket.egri` GSAP adı (yoksa doğrusal `none`). Yakınlaştırma alt
piksel: perspective (kübik, kare başı) + lanczos; `zoompan` yok (tam piksele yuvarlar, titrer).
Ses: tek sürekli PCM miks (müzik + kendi parçaları, birim kazanç; kendi parçasının iki ucunda 8 ms doğrusal geçiş),
tek AAC kodlaması (AudioToolbox 320k). Çekim sesi `kaynak`/`kaynak_bas`'tan (medya nle ve denetle --plan gibi).
Görüntü: libx264, HyperFrames 'looks' ile aynı ayarlar (medium, CRF 16, B kare yok, aq-mode=3) + açık seviye/VBV
(1080x1920'de 4.2), bt709 etiketleri, faststart, üst veri yok.
"""
from __future__ import annotations

import bisect
import math
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

from ..ortak import MedyaHatasi, bilgi, ffmpeg, json_oku, probe, ses_akisi, ses_oku, uyar, video_akisi

SR = 48000
SES_GECIS = 0.008                                  # kendi sesinin uçlarında doğrusal geçiş (ses-tasarimi: 5–10 ms)
ARAMA_PAYI = 0.5                                   # anahtar kareden önceye arama payı (sn; öncü kare kaybı olmasın)
GORSEL = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff"}
NTSC = {23.976: Fraction(24000, 1001), 29.97: Fraction(30000, 1001), 47.952: Fraction(48000, 1001),
        59.94: Fraction(60000, 1001), 119.88: Fraction(120000, 1001)}
DESTEKLI_GECIS = {"kesim", "eslesme", "erime"}
KADRAJ_ALAN, HAREKET_ALAN, GECIS_ALAN = {"ilgi", "mod"}, {"tur", "olcek", "kare", "egri"}, {"tur", "sure_kare", "egri"}
SEVIYE = ((40, 8192, 245760, 20000, 25000), (41, 8192, 245760, 50000, 62500), (42, 8704, 522240, 50000, 62500),
          (50, 22080, 589824, 135000, 135000), (51, 36864, 983040, 240000, 240000),
          (52, 36864, 2073600, 240000, 240000))   # H.264 Tablo A-1: seviye, MaxFS, MaxMBPS, MaxBR, MaxCPB (kbit)

# ---------------------------------------------------------------- eğriler (GSAP 3 gsap-core _insertEase ile aynı)
# taban easeIn: (python, ffmpeg ifadesi); out(p) = 1 − in(1 − p); inOut(p) = p<½ ? in(2p)/2 : 1 − in(2(1 − p))/2.
_TABAN = {
    "power0": (lambda x: x, "({x})"),
    "power1": (lambda x: x ** 2, "pow({x},2)"),
    "power2": (lambda x: x ** 3, "pow({x},3)"),
    "power3": (lambda x: x ** 4, "pow({x},4)"),
    "power4": (lambda x: x ** 5, "pow({x},5)"),
    "sine": (lambda x: 1.0 if x == 1 else 1 - math.cos(x * math.pi / 2), "if(eq({x},1),1,1-cos(({x})*PI/2))"),
    "expo": (lambda x: 2 ** (10 * (x - 1)) if x else 0.0, "if(eq({x},0),0,pow(2,10*(({x})-1)))"),
    "circ": (lambda x: 1 - math.sqrt(max(0.0, 1 - x * x)), "(1-sqrt(1-({x})*({x})))"),
}
_ESAD = {"linear": "power0", "none": "power0", "quad": "power1", "cubic": "power2", "quart": "power3",
         "quint": "power4"}


def _egri_coz(ad: str | None) -> tuple[str, str]:
    """GSAP 3 ease dizgesi → (taban, tür). GSAP'ın ayrıştırdığı biçim, büyük-küçük harf duyarlı ('Sine.InOut' GSAP'ta
    tanınmaz, varsayılana düşer): 'none' / 'linear' doğrusal; çıplak ad (ör. 'sine') GSAP'ta .out'tur."""
    ad = ad or "none"
    taban, _, tur = ad.partition(".")
    taban = _ESAD.get(taban, taban)
    tur = tur or ("in" if taban == "power0" else "out")
    if taban not in _TABAN or tur not in ("in", "out", "inOut"):
        raise ValueError(ad)
    return taban, tur


def egri_gecerli(ad) -> bool:
    """None (doğrusal) ya da tanınan GSAP adı."""
    if ad is None:
        return True
    if not isinstance(ad, str):
        return False
    try:
        _egri_coz(ad)
        return True
    except ValueError:
        return False


def egri(ad: str | None, p: float) -> float:
    taban, tur = _egri_coz(ad)
    f = _TABAN[taban][0]
    p = min(1.0, max(0.0, p))
    if tur == "in":
        return f(p)
    if tur == "out":
        return 1 - f(1 - p)
    return f(2 * p) / 2 if p < 0.5 else 1 - f(2 * (1 - p)) / 2


def egri_ifadesi(ad: str | None, x: str) -> str:
    """Aynı eğrinin ffmpeg ifadesi (perspective eval=frame); x: [0,1] ifadesi."""
    taban, tur = _egri_coz(ad)
    f = _TABAN[taban][1]
    if tur == "in":
        return f.format(x=x)
    if tur == "out":
        return f"(1-({f.format(x=f'(1-({x}))')}))"
    return f"if(lt({x},0.5),({f.format(x=f'(2*({x}))')})/2,1-({f.format(x=f'(2*(1-({x})))')})/2)"


# ---------------------------------------------------------------- yardımcılar
def kare_hizi(fps) -> Fraction:
    for yaklasik, kesin in NTSC.items():
        if abs(float(fps) - yaklasik) < 0.01:
            return kesin
    return Fraction(str(fps))


def _an(sn, F: Fraction) -> Fraction:
    """Plandaki saniye → kesir. Plan ızgarasındaysa (4+ ondalıkla yazılmış k/fps) tam k/fps; değilse yazıldığı ondalık."""
    k = float(sn) * float(F)
    if abs(k - round(k)) <= 2e-3:
        return Fraction(round(k)) / F
    return Fraction(repr(float(sn)))


def _cift(x: float) -> int:
    return 2 * int(round(x / 2))


def _seviye(w: int, h: int, fps: float) -> tuple[int, int, int]:
    """teslim.py seviye_sec ile aynı tablo (taban 4.2: dikey/yatay teslim kapısının sınırı); VBV High profil × 1,25."""
    mb = -(-w // 16) * -(-h // 16)
    for s, fs, mbps, br, cpb in SEVIYE:
        if s >= 42 and mb <= fs and mb * fps <= mbps:
            return s, br * 5 // 4, cpb * 5 // 4
    raise MedyaHatasi(f"{w}x{h}@{fps:g}: H.264 seviye 5.2'yi aşıyor")


def _hepsini_yaz(f, veri: bytes) -> None:
    """Tamponsuz boruya yazma kısmi dönebilir (FileIO.write); kare bölünürse akış kayar — hepsi yazılana dek sürer."""
    m = memoryview(veri)
    while m:
        m = m[f.write(m):]


class _Gunluk:
    """Alt sürecin stderr'i geçici dosyaya (boru dolup süreci kilitlemesin); hata iletisinde son satırlar."""

    def __init__(self):
        self.f = tempfile.TemporaryFile()

    def son(self, n: int = 1500) -> str:
        self.f.seek(0)
        return self.f.read().decode("utf-8", "replace")[-n:]


# ---------------------------------------------------------------- medya künyesi ve kare zamanları
class _Ortam:
    def __init__(self, yol: Path):
        self.yol = yol
        if yol.suffix.lower() in GORSEL:
            raise MedyaHatasi(f"{yol.name}: fotoğraf ciz'de henüz yok (EXIF yönü ve Ken Burns sınanmadı) → HyperFrames "
                              "kompozisyonu")
        p = probe(yol)
        v = video_akisi(p)
        if not v:
            raise MedyaHatasi(f"{yol.name}: video akışı yok")
        self.codec, self.pix = v.get("codec_name"), v.get("pix_fmt") or ""
        don = 0
        for sd in v.get("side_data_list") or []:
            if "rotation" in sd:
                don = int(round(float(sd["rotation"])))
        don = don or int((v.get("tags") or {}).get("rotate", 0) or 0)
        w, h = int(v["width"]), int(v["height"])
        self.W, self.H = (h, w) if abs(don) % 180 == 90 else (w, h)            # görünen (ffmpeg kendiliğinden döndürür)
        self.matris, self.aralik = v.get("color_space"), v.get("color_range")
        self.aktarim = v.get("color_transfer")
        if self.aktarim in ("arib-std-b67", "smpte2084"):
            raise MedyaHatasi(f"{yol.name}: HDR ({self.aktarim}) → önce medya sdr {yol} --cikti calisma/klipler/"
                              f"{yol.stem}-sdr.mp4 ve planda klip olarak ver")
        sar = v.get("sample_aspect_ratio")
        if sar not in (None, "", "N/A", "0:1", "1:1"):
            raise MedyaHatasi(f"{yol.name}: anamorfik piksel (SAR {sar}) desteklenmiyor")
        self.bicim_bas = float(p.get("format", {}).get("start_time") or 0.0)
        self.ses = ses_akisi(p) is not None
        self._t = None

    def giris_matrisi(self) -> str:
        """yavaslat._giris_matrisi ile aynı: etiketliyse etiket, etiketsizse HyperFrames'in tahmini (≥720 satır BT.709)."""
        if self.matris and self.matris != "unknown":
            return "auto"
        return "bt709" if min(self.W, self.H) >= 720 and self.codec not in ("vp9", "av1") else "bt601"

    def donusum_gerekmez(self) -> bool:
        m = self.giris_matrisi()
        return (self.pix == "yuv420p" and self.aralik in (None, "", "unknown", "tv")
                and (m == "bt709" or (m == "auto" and self.matris == "bt709")))

    def zamanlar(self):
        """(T, tb, kok): kare zamanları (ilk karenin pts'ine göre, kesir, sıralı), zaman tabanı, ilk karenin pts'i.
        pts: ffmpeg 6.0 paket damgaları (-c copy -copyts, çözmeden); ilk kare: gerçekten çözülen ilk karenin pts'i."""
        if self._t is None:
            r = subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-copyts", "-i", str(self.yol), "-map", "0:v:0",
                                "-c", "copy", "-f", "framemd5", "-"], capture_output=True, text=True)
            if r.returncode:
                raise MedyaHatasi(f"{self.yol.name}: zaman damgaları okunamadı\n{r.stderr[-800:]}")
            tbs = next((l.split(":", 1)[1].strip() for l in r.stdout.splitlines() if l.startswith("#tb 0:")), None)
            pts = sorted(int(l.split(",")[2]) for l in r.stdout.splitlines() if l and not l.startswith("#")
                         and l.split(",")[2].strip().lstrip("-").isdigit())
            if not tbs or not pts:
                raise MedyaHatasi(f"{self.yol.name}: kare zaman damgası yok")
            s = subprocess.run([ffmpeg(), "-nostdin", "-v", "info", "-copyts", "-i", str(self.yol), "-map", "0:v:0",
                                "-frames:v", "1", "-vf", "showinfo", "-f", "null", "-"], capture_output=True, text=True)
            m = re.search(r"\bpts:\s*(-?\d+)", s.stderr)
            kok = int(m.group(1)) if m else pts[0]
            tb = Fraction(tbs)
            T = [Fraction(x - kok) * tb for x in pts if x >= kok]
            self._t = (T, tb, kok)
        return self._t


# ---------------------------------------------------------------- çekim: kare kaynağı
class _Cekim:
    def __init__(self, c: dict, ortam: _Ortam, m0: Fraction, hiz: Fraction, F: Fraction, Wc: int, Hc: int,
                 bas_n: int, son_n: int):
        self.c, self.o, self.no = c, ortam, c.get("no")
        self.bas_n, self.son_n, self.F, self.Wc, self.Hc = bas_n, son_n, F, Wc, Hc
        self.surec: list[tuple[subprocess.Popen, _Gunluk]] = []
        self.besleyici = None
        self.hata = None
        T, tb, kok = ortam.zamanlar()
        n = son_n - bas_n
        hz = hiz if hiz > 1 else Fraction(1)
        secim = []
        for j in range(n):
            t = m0 + j * hz / F
            secim.append(max(0, bisect.bisect_right(T, t) - 1))
        araliklar = [b - a for a, b in zip(T, T[1:])]
        kare_sure = sorted(araliklar)[len(araliklar) // 2] if araliklar else Fraction(1, 30)
        t_son = m0 + (n - 1) * hz / F
        if t_son >= T[-1] + kare_sure + Fraction(1, 1000):
            raise MedyaHatasi(f"çekim {self.no}: {ortam.yol.name} {float(T[-1] + kare_sure):.3f} sn'de bitiyor, plan "
                              f"{float(t_son):.3f} sn'ye kadar okuyor (son kare donardı)")
        self.secim, self.i0, self.i1 = secim, secim[0], secim[-1]
        self.p0 = kok + int((T[self.i0] / tb))                     # ilk gereken karenin pts'i (akış zaman tabanında)
        self.arama = float(T[self.i0] + kok * tb) - ortam.bicim_bas - ARAMA_PAYI
        self._geometri(c)

    # ---- kadraj ve hareket (kompozisyon.md: object-fit cover + object-position; .ic ölçeği, transform-origin = ilgi)
    def _geometri(self, c: dict) -> None:
        Ws, Hs, Wc, Hc = self.o.W, self.o.H, self.Wc, self.Hc
        k = max(Wc / Ws, Hc / Hs)
        ww, wh = Wc / k, Hc / k                                    # cover penceresi (kaynak pikseli)
        ilgi = (c.get("kadraj") or {}).get("ilgi")
        ix, iy = (float(ilgi[0]), float(ilgi[1])) if ilgi else (0.5, 0.5)

        def konum(i, kaynak, cikti):                               # object-position: P = clamp((i·Wö − Wç/2)/(Wö − Wç))
            o = kaynak * k
            return min(1.0, max(0.0, (i * o - cikti / 2) / (o - cikti))) if o - cikti > 1e-9 else 0.5
        X0, Y0 = (Ws - ww) * konum(ix, Ws, Wc), (Hs - wh) * konum(iy, Hs, Hc)
        ax = (ix * Ws - X0) / ww if ilgi else 0.5                  # çapa: ilginin ekrandaki yeri (0–1)
        ay = (iy * Hs - Y0) / wh if ilgi else 0.5
        self.pencere = (X0, Y0, ww, wh)
        h = c.get("hareket") or {}
        olcek = h.get("olcek", 1.0)
        a, b = (float(olcek[0]), float(olcek[-1])) if isinstance(olcek, list) else (float(olcek), float(olcek))
        n = self.son_n - self.bas_n
        if h.get("tur") == "punch":
            j0, jd = 0, int(h.get("kare") or 0)
        else:                                                      # kenburns: ilk karede a, son karede b
            j0, jd = 0, n - 1
        self.olcek = (a, b, h.get("egri"), j0, jd)
        self.yakin = bool(h) and not (abs(a - 1) < 1e-9 and abs(b - 1) < 1e-9)
        if not self.yakin:                                         # tamsayı kırpma (çift) + lanczos
            cw, ch = min(_cift(ww), Ws - Ws % 2), min(_cift(wh), Hs - Hs % 2)
            cx = min(max(0, _cift(X0 + ww / 2 - cw / 2)), Ws - cw)
            cy = min(max(0, _cift(Y0 + wh / 2 - ch / 2)), Hs - ch)
            self.kirp = (cw, ch, cx, cy)
        else:                                                      # pencereyi kapsayan çift kutu; alt piksel perspective'te
            cx0, cy0 = 2 * int(math.floor(X0 / 2)), 2 * int(math.floor(Y0 / 2))
            cx1 = min(2 * int(math.ceil((X0 + ww) / 2)), Ws - Ws % 2)
            cy1 = min(2 * int(math.ceil((Y0 + wh) / 2)), Hs - Hs % 2)
            self.kirp = (cx1 - cx0, cy1 - cy0, cx0, cy0)
            self.capa = (ax, ay)

    def olcek_an(self, j: int) -> float:
        a, b, e, j0, jd = self.olcek
        p = 1.0 if jd <= 0 else (j - j0) / jd
        return a + (b - a) * egri(e, p)

    def kaynak_dikdortgeni(self, j: int) -> tuple[float, float, float, float]:
        """j. karede görünen kaynak dikdörtgeni (sol, üst, gen, yük; sürekli kaynak koordinatı) — sınamalar için."""
        X0, Y0, ww, wh = self.pencere
        if not self.yakin:
            return X0, Y0, ww, wh
        z = self.olcek_an(j)
        ax, ay = self.capa
        return X0 + ax * ww * (1 - 1 / z), Y0 + ay * wh * (1 - 1 / z), ww / z, wh / z

    def _persp(self) -> str:
        a, b, e, j0, jd = self.olcek
        cw, ch, cx, cy = self.kirp
        X0, Y0, ww, wh = self.pencere
        ax, ay = self.capa
        sayi = lambda x: f"{x:.12f}"
        p = f"clip((in-1-{j0})/{jd},0,1)" if jd > 0 else "1"
        z = f"({sayi(a)}+({sayi(b - a)})*({egri_ifadesi(e, p)}))"
        sol = f"({sayi(X0 - cx)}+{sayi(ax * ww)}*(1-1/{z}))"
        ust = f"({sayi(Y0 - cy)}+{sayi(ay * wh)}*(1-1/{z}))"
        gen, yuk = f"({sayi(ww)}/{z})", f"({sayi(wh)}/{z})"
        # perspective piksel dizini kuralı (ölçüldü): hedef x → kaynak a + x·s. Piksel merkezi eşlemesi için a = sol + s/2 − ½
        x0 = f"({sol}+0.5*{gen}/{cw}-0.5)"
        y0 = f"({ust}+0.5*{yuk}/{ch}-0.5)"
        x1, y1 = f"({x0}+{gen})", f"({y0}+{yuk})"
        sabit = jd <= 0 or abs(b - a) < 1e-12
        return (f"perspective=x0='{x0}':y0='{y0}':x1='{x1}':y1='{y0}':x2='{x0}':y2='{y1}':x3='{x1}':y3='{y1}'"
                f":interpolation=cubic:sense=source:eval={'init' if sabit else 'frame'}")

    # ---- süreçler
    def baslat(self) -> None:
        cw, ch, cx, cy = self.kirp
        o = self.o
        vf = [f"select='gte(pts,{self.p0})'"]
        if (cw, ch) != (o.W, o.H):
            vf.append(f"crop={cw}:{ch}:{cx}:{cy}:exact=1")
        renk = (f"in_color_matrix={o.giris_matrisi()}:out_color_matrix=bt709:out_range=tv")
        if not self.yakin and (cw, ch) != (self.Wc, self.Hc):
            vf.append(f"scale={self.Wc}:{self.Hc}:flags=lanczos:{renk}")
        elif not o.donusum_gerekmez():
            vf.append(f"scale=iw:ih:flags=lanczos:{renk}")
        vf.append("format=yuv420p")
        # -threads 4: 4K HEVC çözücüsü varsayılan iş parçacığıyla ~490 MB, 4 ile ~270 MB (ölçüldü 2026-10-08); aynı anda en çok
        # iki çekim açık (ciz: onden_ac) — uzun planda bellek tepesi bununla sınırlı kalır
        komut = [ffmpeg(), "-nostdin", "-v", "error", "-threads", "4", "-copyts"]
        if self.arama > 0:
            komut += ["-ss", f"{self.arama:.6f}"]
        komut += ["-i", str(o.yol), "-map", "0:v:0", "-an", "-sn", "-dn", "-vf", ",".join(vf),
                  "-frames:v", str(self.i1 - self.i0 + 1), "-fps_mode", "passthrough", "-f", "rawvideo",
                  "-pix_fmt", "yuv420p", "-"]
        self.cozucu = self._ac(komut)
        self.boy_k = (cw * ch * 3 // 2) if self.yakin else (self.Wc * self.Hc * 3 // 2)
        self.boy_c = self.Wc * self.Hc * 3 // 2
        self._i, self._kare, self._j = self.i0 - 1, None, 0
        if self.yakin:
            vf = [self._persp(), f"scale={self.Wc}:{self.Hc}:flags=lanczos:in_color_matrix=bt709:out_color_matrix=bt709"
                                 ":in_range=tv:out_range=tv", "format=yuv420p"]
            self.geo = self._ac([ffmpeg(), "-nostdin", "-v", "error", "-f", "rawvideo", "-pix_fmt", "yuv420p",
                                 "-s", f"{cw}x{ch}", "-framerate", str(self.F), "-i", "-", "-vf", ",".join(vf),
                                 "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], girdi=True)
            self.besleyici = threading.Thread(target=self._besle, daemon=True)
            self.besleyici.start()

    def _ac(self, komut: list[str], girdi: bool = False) -> subprocess.Popen:
        g = _Gunluk()
        p = subprocess.Popen(komut, stdin=subprocess.PIPE if girdi else subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=g.f, bufsize=0)
        self.surec.append((p, g))
        return p

    def _oku(self, p: subprocess.Popen, boy: int, ne: str) -> bytes:
        parca, kalan = [], boy
        while kalan:
            b = p.stdout.read(kalan)
            if not b:
                g = next(g for s, g in self.surec if s is p)
                raise MedyaHatasi(f"çekim {self.no}: {ne} erken bitti ({boy - kalan}/{boy} bayt)\n{g.son()}")
            parca.append(b)
            kalan -= len(b)
        return b"".join(parca)

    def _secili(self, j: int) -> bytes:
        hedef = self.secim[j]
        while self._i < hedef:
            self._kare = self._oku(self.cozucu, self.boy_k, f"çözücü ({self.o.yol.name})")
            self._i += 1
        return self._kare

    def _besle(self) -> None:
        try:
            for j in range(self.son_n - self.bas_n):
                _hepsini_yaz(self.geo.stdin, self._secili(j))
            self.geo.stdin.close()
        except Exception as e:                                     # ana iş parçacığı okurken görür
            self.hata = e
            try:
                self.geo.stdin.close()
            except OSError:
                pass

    def sonraki(self) -> bytes:
        if not self.yakin:
            k = self._secili(self._j)
        else:
            try:
                k = self._oku(self.geo, self.boy_c, "perspective süreci")
            except MedyaHatasi:
                if self.hata:
                    raise MedyaHatasi(f"çekim {self.no}: {self.hata}") from self.hata
                raise
        self._j += 1
        return k

    def kapat(self, zorla: bool = False) -> None:
        if self.besleyici is not None and not zorla:
            self.besleyici.join(timeout=30)
        for p, g in self.surec:
            if zorla:
                p.kill()
            try:
                p.wait(timeout=30)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
            if not zorla and p.returncode not in (0, -9, -15, 255):
                raise MedyaHatasi(f"çekim {self.no}: ffmpeg {p.returncode}\n{g.son()}")
        self.surec = []


# ---------------------------------------------------------------- plan
def _gecis(c: dict) -> dict:
    g = c.get("gecis") or {}
    return {"tur": g} if isinstance(g, str) else dict(g)


class _Plan:
    """Hazırlanmış plan: çekimler (süreçsiz), kare hızı, boyut, uyarılar, medya önbelleği (ortam(yol) → _Ortam)."""

    def __init__(self, cekimler, F, Wc, Hc, uyarilar, ortam):
        self.cekimler, self.F, self.Wc, self.Hc, self.uyarilar, self.ortam = cekimler, F, Wc, Hc, uyarilar, ortam
        self.toplam = cekimler[-1].son_n


def plani_hazirla(plan: dict, kok: Path) -> _Plan:
    """Plan → çekim nesneleri (süreç başlatmadan). Kapsam dışı ve tutarsızlıkların hepsini toplayıp tek hatada verir."""
    if not isinstance(plan.get("fps"), (int, float)) or plan["fps"] <= 0:
        raise MedyaHatasi("plan fps eksik ya da geçersiz")
    b = plan.get("boyut")
    if not (isinstance(b, list) and len(b) == 2 and all(isinstance(x, int) and x > 0 and x % 2 == 0 for x in b)):
        raise MedyaHatasi("plan boyut [genişlik, yükseklik] pozitif çift tamsayı olmalı")
    F, (Wc, Hc) = kare_hizi(plan["fps"]), b
    C = sorted(plan.get("cekimler") or [], key=lambda c: c["cikti_bas"])
    if not C:
        raise MedyaHatasi("planda çekim yok")
    sorun, uyarilar, ortamlar, cekimler = [], [], {}, []
    for c in C:
        no = c.get("no")
        g = _gecis(c)
        tur = str(g.get("tur") or "kesim").lower()
        if tur not in DESTEKLI_GECIS or (tur == "eslesme" and int(g.get("sure_kare") or 0)):
            sorun.append(f"çekim {no}: '{tur}' geçişi")
        for ad, alanlar, d in (("gecis", GECIS_ALAN, g), ("kadraj", KADRAJ_ALAN, c.get("kadraj") or {}),
                               ("hareket", HAREKET_ALAN, c.get("hareket") or {})):
            if not isinstance(d, dict):
                sorun.append(f"çekim {no}: {ad} nesne değil")
                continue
            for a in sorted(set(d) - alanlar):
                sorun.append(f"çekim {no}: {ad}.{a} sözleşmede yok" + (" (yakınlaştırma hareket.olcek)"
                                                                        if (ad, a) == ("kadraj", "olcek") else ""))
        if not egri_gecerli(g.get("egri")):
            sorun.append(f"çekim {no}: gecis.egri '{g.get('egri')}' tanınmıyor (GSAP adı: none, sine.inOut, expo.out…)")
        kd = c.get("kadraj") or {}
        if isinstance(kd, dict):
            if kd.get("mod") not in (None, "sabit"):
                sorun.append(f"çekim {no}: kadraj.mod '{kd.get('mod')}'")
            il = kd.get("ilgi")
            if il is not None and not (isinstance(il, list) and len(il) == 2
                                       and all(isinstance(x, (int, float)) and 0 <= x <= 1 for x in il)):
                sorun.append(f"çekim {no}: kadraj.ilgi [x, y] (0–1) olmalı")
        h = c.get("hareket") or {}
        if isinstance(h, dict) and h:
            if h.get("tur") not in ("punch", "kenburns"):
                sorun.append(f"çekim {no}: hareket.tur '{h.get('tur')}'")
            o = h.get("olcek", 1.0)
            ok = (isinstance(o, (int, float)) and not isinstance(o, bool)) or (
                isinstance(o, list) and len(o) == 2 and all(isinstance(x, (int, float)) for x in o))
            if not ok:
                sorun.append(f"çekim {no}: hareket.olcek sayı ya da [a, b] olmalı")
            elif min(o if isinstance(o, list) else [o]) < 1 - 1e-9:
                sorun.append(f"çekim {no}: hareket.olcek < 1 karede boşluk bırakır")
            if not egri_gecerli(h.get("egri")):
                sorun.append(f"çekim {no}: hareket.egri '{h.get('egri')}' tanınmıyor")
            if "kare" in h and not (isinstance(h["kare"], int) and h["kare"] >= 0):
                sorun.append(f"çekim {no}: hareket.kare tamsayı ≥ 0 olmalı")
        hiz = float(c.get("hiz", 1))
        hazir = bool(c.get("klip")) and c.get("klip") != c.get("kaynak")
        if hiz < 1 - 1e-9 and not hazir:
            sorun.append(f"çekim {no}: hiz {hiz:g} pişmiş klip ister (medya yavaslat)")
        if c.get("ses") == "kendi" and abs(hiz - 1) > 1e-9:
            sorun.append(f"çekim {no}: ses 'kendi' yalnız hiz 1'de")
    if sorun:
        raise MedyaHatasi("ciz bu planı çizemez (sessizce kesime çevirmez; bu öğeler için HyperFrames kompozisyonu: "
                          "kurgu-zanaati kompozisyon.md):\n  " + "\n  ".join(sorun))

    def ortam(y: str) -> _Ortam:
        p = Path(y).expanduser()
        p = (p if p.is_absolute() else kok / p).resolve()
        if not p.exists():
            raise MedyaHatasi(f"medya yok: {p}")
        if p not in ortamlar:
            ortamlar[p] = _Ortam(p)
        return ortamlar[p]

    for c in C:
        hazir = bool(c.get("klip")) and c.get("klip") != c.get("kaynak")
        o = ortam(c["klip"] if hazir else c["kaynak"])
        m0 = _an(c.get("klip_bas", 0.0) if hazir else c.get("kaynak_bas", 0.0), F)
        bas_n, son_n = round(c["cikti_bas"] * float(F)), round(c["cikti_son"] * float(F))
        if son_n - bas_n < 1:
            raise MedyaHatasi(f"çekim {c.get('no')}: süre ≤ 0 kare")
        if c.get("ses") == "kendi" and not ortam(c["kaynak"]).ses:
            raise MedyaHatasi(f"çekim {c.get('no')}: ses 'kendi' ama kaynakta ses akışı yok")
        cekimler.append(_Cekim(c, o, m0, Fraction(repr(float(c.get("hiz", 1)))), F, Wc, Hc, bas_n, son_n))
    if cekimler[0].bas_n != 0:
        raise MedyaHatasi(f"ilk çekim {cekimler[0].bas_n}. karede başlıyor (başta siyah olurdu)")
    for a, b in zip(cekimler, cekimler[1:]):
        L, tur = a.son_n - b.bas_n, str(_gecis(b.c).get("tur") or "kesim").lower()
        if tur == "erime":
            n = int(_gecis(b.c).get("sure_kare") or L)
            if L <= 0:
                raise MedyaHatasi(f"çekim {b.no}: erime örtüşmedir (cikti_bas = önceki cikti_son − sure_kare/fps)")
            if L != n:
                raise MedyaHatasi(f"çekim {b.no}: örtüşme {L} kare, gecis.sure_kare {n}")
            if L >= a.son_n - a.bas_n or L >= b.son_n - b.bas_n:
                raise MedyaHatasi(f"çekim {b.no}: {L} karelik erime çekimlerden birinden uzun")
        elif L > 0:
            raise MedyaHatasi(f"çekim {a.no}→{b.no}: {L} kare örtüşüyor ama geçiş '{tur}' (yalnız erime örtüşür)")
        elif L < 0:
            raise MedyaHatasi(f"çekim {a.no}→{b.no}: {-L} kare boşluk (siyah kare olurdu)")
    for a, c in zip(cekimler, cekimler[2:]):
        if a.son_n > c.bas_n:
            raise MedyaHatasi(f"çekim {a.no} ile {c.no} örtüşüyor: aynı anda en çok iki çekim (erime)")
    toplam = cekimler[-1].son_n
    if "sure" in plan and abs(round(float(plan["sure"]) * float(F)) - toplam) > 0:
        uyarilar.append(f"plan sure {plan['sure']} ama son çekim {toplam} karede bitiyor; son çekim esas alındı")
    return _Plan(cekimler, F, Wc, Hc, uyarilar, ortam)


# ---------------------------------------------------------------- ses
def _kendi_katmani(cekimler: list[_Cekim], ortam, F: Fraction, hedef: np.ndarray) -> int:
    """ses: kendi parçalarını hedefe (örnek x 2, float32) ekler: kaynak/kaynak_bas'tan (video kökünün saatinde),
    uçlarda 8 ms doğrusal geçiş. ortam: yol → _Ortam (plani_hazirla'nın önbelleği)."""
    sayi = 0
    for x in cekimler:
        c = x.c
        if c.get("ses") != "kendi":
            continue
        o = ortam(c["kaynak"])
        T, tb, kokpts = o.zamanlar()
        kayma = float(kokpts * tb) - o.bicim_bas                    # video kökünün biçim başlangıcına göre yeri
        b0 = round(Fraction(x.bas_n) / F * SR)
        L = round(Fraction(x.son_n) / F * SR) - b0
        bas = float(_an(c.get("kaynak_bas", 0.0), F)) + kayma
        on = max(0, round(-bas * SR))                               # kaynak başından önce: sessizlik
        ses, _ = ses_oku(o.yol, sr=SR, kanal=2, bas=max(0.0, bas), sure=L / SR + 0.05, zamanli=True)
        ses = np.concatenate([np.zeros((on, 2), np.float32), ses])[:L] if on else ses[:L]
        if len(ses) < L:
            ses = np.pad(ses, ((0, L - len(ses)), (0, 0)))
        g = min(int(SES_GECIS * SR), L // 2)
        if g:
            rampa = (np.arange(g, dtype=np.float32) + 0.5) / g
            ses[:g] *= rampa[:, None]
            ses[L - g:] *= rampa[::-1, None]
        son = min(len(hedef), b0 + L)
        hedef[b0:son] += ses[:son - b0]
        sayi += 1
    return sayi


def ses_hazirla(P: _Plan, plan: dict, kok: Path, yol: Path, yalniz_konusma: bool = False) -> dict:
    """Miks (ya da yalnız konuşma katmanı) → yol (ham f32le, 48 kHz stereo; büyük işte bellek değil disk: memmap)."""
    F = P.F
    ornek = round(Fraction(P.toplam) / F * SR)
    mz = plan.get("muzik") or {}
    bilgi_ = {"ornek": ornek, "muzik": None, "kendi": 0}
    if mz.get("dosya") and not yalniz_konusma:
        m = Path(mz["dosya"]).expanduser()
        m = (m if m.is_absolute() else kok / m).resolve()
        if not m.exists():
            raise MedyaHatasi(f"müzik yok: {m}")
        bas = float(mz.get("bas", 0.0))
        r = subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-y"] + (["-ss", f"{bas:.6f}"] if bas > 0 else [])
                           + ["-i", str(m), "-map", "0:a:0", "-af", f"aresample={SR}:async=1:first_pts=0", "-ac", "2",
                              "-t", f"{ornek / SR:.6f}", "-f", "f32le", str(yol)], capture_output=True)
        if r.returncode:
            raise MedyaHatasi(f"müzik çözülemedi: {m}\n{r.stderr.decode()[-800:]}")
        n = yol.stat().st_size // 8
        if n < ornek:
            bilgi_["muzik_eksik_kare"] = round((ornek - n) / SR * float(F))
        bilgi_["muzik"] = str(m)
        with open(yol, "r+b") as f:
            f.truncate(ornek * 8)                                   # kısaysa sessizlikle uzat
    else:
        with open(yol, "wb") as f:
            f.truncate(ornek * 8)
    hedef = np.memmap(yol, dtype=np.float32, mode="r+", shape=(ornek, 2))
    bilgi_["kendi"] = _kendi_katmani(P.cekimler, P.ortam, F, hedef)
    tepe = float(np.abs(hedef).max()) if ornek else 0.0
    hedef.flush()
    del hedef
    bilgi_["tepe"] = tepe
    return bilgi_


# ---------------------------------------------------------------- çizim
def ciz(plan_yolu: Path, cikti: Path, kok: Path, crf: float = 16, preset: str = "medium") -> dict:
    plan = json_oku(plan_yolu)
    P = plani_hazirla(plan, kok)
    cekimler, F, Wc, Hc, uyarilar, toplam = P.cekimler, P.F, P.Wc, P.Hc, P.uyarilar, P.toplam
    if cikti.exists():
        raise MedyaHatasi(f"{cikti} var; üzerine yazılmaz — yeni ad ver (--cikti)")
    cikti.parent.mkdir(parents=True, exist_ok=True)
    seviye, maxrate, bufsize = _seviye(Wc, Hc, float(F))
    tahmin = 20e6 * (Wc * Hc / (1080 * 1920)) * float(F) / 30 * (toplam / float(F)) / 8   # ~20 Mb/sn (1080p30) kabası
    bos = shutil.disk_usage(cikti.parent).free
    if bos - tahmin < 5e9:
        uyar(f"boş disk {bos / 1e9:.1f} GB; çıktı ~{tahmin / 1e9:.1f} GB (kaba) — 5 GB tabanına yakın")
    gecici = cikti.with_name(cikti.stem + ".ciz-gecici" + cikti.suffix)
    ses_yol = cikti.with_name(cikti.stem + ".ciz-ses.f32")
    for y in (gecici, ses_yol):                                     # yarıda kalmış eski koşunun kendi ara dosyaları
        y.unlink(missing_ok=True)
    t0 = time.monotonic()
    canli: list[_Cekim] = []
    enc = None
    try:
        sesli = bool((plan.get("muzik") or {}).get("dosya")) or any(x.c.get("ses") == "kendi" for x in cekimler)
        sb = ses_hazirla(P, plan, kok, ses_yol) if sesli else {"ornek": 0, "muzik": None, "kendi": 0, "tepe": 0.0}
        if sb.get("muzik_eksik_kare"):
            uyarilar.append(f"müzik {sb['muzik_eksik_kare']} kare erken bitiyor (sonu sessiz)")
        if sb["tepe"] > 1.0:
            uyarilar.append(f"miks tepesi {20 * math.log10(sb['tepe']):+.1f} dBFS (> 0): AAC kırpar → medya ustala öncesi "
                            "kazancı düşür (müzik ya da çekim sesi)")
        if not sesli:
            uyarilar.append("planda ses yok (müzik ve 'kendi' çekim yok): çıktı sessiz")
        x264 = "aq-mode=3:aq-strength=0.8:deblock=1,1"
        komut = [ffmpeg(), "-nostdin", "-v", "error", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{Wc}x{Hc}",
                 "-framerate", str(F), "-i", "-"]
        if sesli:
            komut += ["-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(ses_yol)]
        komut += ["-map", "0:v:0"] + (["-map", "1:a:0"] if sesli else [])
        # -threads 8: x264 1080x1920'de varsayılan 662 MB → 558 MB, 65 → 61 kare/sn (ölçüldü 2026-10-08); çizim çözücüde
        # darboğazlı (4K HEVC'den ~22 kare/sn), kodlayıcı yavaşlaması süreye yansımaz
        komut += ["-c:v", "libx264", "-threads", "8", "-preset", preset, "-crf", f"{crf:g}", "-bf", "0", "-x264-params", x264,
                  "-profile:v", "high", "-level:v", f"{seviye / 10:.1f}", "-maxrate", f"{maxrate}k",
                  "-bufsize", f"{bufsize}k", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
                  "-color_trc", "bt709", "-color_range", "tv"]
        if sesli:
            komut += ["-c:a", "aac_at", "-b:a", "320k", "-ar", str(SR)]
        komut += ["-map_metadata", "-1", "-map_chapters", "-1", "-fflags", "+bitexact", "-flags:v", "+bitexact",
                  "-flags:a", "+bitexact", "-movflags", "+faststart", "-n", str(gecici)]
        enc_log = _Gunluk()
        enc = subprocess.Popen(komut, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=enc_log.f, bufsize=0)
        sira = 0                                                   # sonraki başlatılacak çekim
        en_cok = 0

        def onden_ac():
            """Aynı anda en çok iki çekim açık: şimdiki + önden açılan (arama gecikmesi gizlenir) ya da erimedeki iki
            çekim. Üçüncü 4K çözücü bellek tepesini ~0,3 GB büyütüyordu (300 sn'lik 112 çekimli planda 2,25 GB)."""
            nonlocal sira
            while sira < len(cekimler) and len(canli) < 2:
                cekimler[sira].baslat()
                canli.append(cekimler[sira])
                sira += 1
        onden_ac()
        son_bilgi = time.monotonic()
        for n in range(toplam):
            if time.monotonic() - son_bilgi > 10:                 # uzun çizimde ilerleme (stderr)
                son_bilgi = time.monotonic()
                bilgi(f"  … {n}/{toplam} kare (%{100 * n / toplam:.0f}), {n / float(F) / (son_bilgi - t0):.2f}x gerçek zaman")
            onden_ac()
            etkin = [x for x in canli if x.bas_n <= n < x.son_n]
            if not etkin or any(x.bas_n <= n for x in cekimler[sira:]):
                raise MedyaHatasi(f"kare {n}: gereken çekim açılmadı (iç hata)")
            en_cok = max(en_cok, sum(len(x.surec) for x in canli))
            if len(etkin) == 1:
                kare = etkin[0].sonraki()
            else:
                a, b = etkin
                L = a.son_n - b.bas_n
                w = egri(_gecis(b.c).get("egri"), (n - b.bas_n) / L)
                fa = np.frombuffer(a.sonraki(), np.uint8)
                fb = np.frombuffer(b.sonraki(), np.uint8)
                kare = np.rint(fa * np.float32(1 - w) + fb * np.float32(w)).astype(np.uint8).tobytes()
            try:
                _hepsini_yaz(enc.stdin, kare)
            except BrokenPipeError:
                raise MedyaHatasi(f"kodlayıcı durdu\n{enc_log.son()}") from None
            for x in [x for x in canli if x.son_n == n + 1]:
                x.kapat()
                canli.remove(x)
        enc.stdin.close()
        if enc.wait() != 0:
            raise MedyaHatasi(f"kodlama başarısız ({enc.returncode})\n{enc_log.son()}")
        os.replace(gecici, cikti)
    except BaseException:
        for x in canli:
            x.kapat(zorla=True)
        if enc is not None and enc.poll() is None:
            enc.kill()
            enc.wait()
        gecici.unlink(missing_ok=True)
        raise
    finally:
        ses_yol.unlink(missing_ok=True)
    sure = time.monotonic() - t0
    return {"cikti": str(cikti), "kare": toplam, "fps": str(F), "boyut": [Wc, Hc], "sure_sn": round(sure, 2),
            "hiz_x": round(toplam / float(F) / sure, 2) if sure else None, "bayt": cikti.stat().st_size,
            "cekim": len(cekimler), "yakinlasan": sum(1 for x in cekimler if x.yakin), "ses": sb,
            "en_cok_surec": en_cok + 1, "seviye": seviye / 10, "uyarilar": uyarilar}


def yalniz_konusma(plan_yolu: Path, hedef: Path, kok: Path) -> dict:
    plan = json_oku(plan_yolu)
    P = plani_hazirla(plan, kok)
    if not any(x.c.get("ses") == "kendi" for x in P.cekimler):
        raise MedyaHatasi("planda 'ses: kendi' çekim yok: konuşma katmanı boş olurdu")
    if hedef.exists():
        raise MedyaHatasi(f"{hedef} var; üzerine yazılmaz")
    hedef.parent.mkdir(parents=True, exist_ok=True)
    ham = hedef.with_name(hedef.stem + ".ciz-ses.f32")
    try:
        b = ses_hazirla(P, plan, kok, ham, yalniz_konusma=True)
        r = subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-n", "-f", "f32le", "-ar", str(SR), "-ac", "2",
                            "-i", str(ham), "-c:a", "pcm_f32le", str(hedef)], capture_output=True)
        if r.returncode:
            raise MedyaHatasi(f"WAV yazılamadı: {r.stderr.decode()[-500:]}")
    finally:
        ham.unlink(missing_ok=True)
    return b


def calistir_(args) -> int:
    plan_yolu = Path(args.plan).resolve()
    kok = Path(args.kok).resolve() if args.kok else plan_yolu.parent.parent
    if args.yalniz_konusma:
        h = Path(args.yalniz_konusma)
        h = h if h.is_absolute() else Path.cwd() / h
        b = yalniz_konusma(plan_yolu, h, kok)
        print(f"konuşma katmanı ({b['kendi']} 'kendi' parçası, {b['ornek'] / SR:.3f} sn, çıktı zamanında, müziksiz) → {h}")
        print("sonra: ses-tasarimi kisma.py --konusma <bu dosya> → kısılmış WAV'ı plan muzik.dosya yap (aynı bas)")
        return 0
    plan = json_oku(plan_yolu)
    ad = plan.get("ad") or kok.name
    cikti = Path(args.cikti) if args.cikti else kok / "cikti" / f"{ad}.mp4"
    cikti = cikti if cikti.is_absolute() else Path.cwd() / cikti
    r = ciz(plan_yolu, cikti, kok, args.crf, args.preset)
    print(f"✓ {r['cikti']}  {r['boyut'][0]}x{r['boyut'][1]} @ {r['fps']} fps, {r['kare']} kare "
          f"({r['kare'] / float(Fraction(r['fps'])):.3f} sn), {r['cekim']} çekim ({r['yakinlasan']} yakınlaşan), "
          f"{r['bayt'] / 1e6:.1f} MB, H.264 seviye {r['seviye']:g}; çizim {r['sure_sn']:.1f} sn ({r['hiz_x']}x gerçek zaman)")
    s = r["ses"]
    print(f"  ses: {'müzik + ' if s['muzik'] else ''}{s['kendi']} 'kendi' parçası, tepe "
          f"{20 * math.log10(s['tepe']) if s['tepe'] > 0 else float('-inf'):+.1f} dBFS (ustalık: medya ustala)")
    for u in r["uyarilar"]:
        uyar(u)
    bilgi("sonra: medya denetle <çıktı> --plan plan/kurgu.json (ve güven yüksekse --muzik); teslim: medya ustala → "
          "medya meta-temizle")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="kurgu planını HyperFrames'siz, doğrudan ffmpeg ile çizer (gerçek çekim kurgusu)",
                       description=__doc__.split("\n\n")[1])
    p.add_argument("plan", help="plan/kurgu.json")
    p.add_argument("--cikti", help="çıktı .mp4 (varsayılan cikti/<plan adı>.mp4; var olanın üzerine yazılmaz)")
    p.add_argument("--crf", type=float, default=16, help="x264 CRF (varsayılan 16 = HyperFrames 'looks')")
    p.add_argument("--preset", default="medium", help="x264 hazır ayarı (varsayılan medium = HyperFrames 'looks')")
    p.add_argument("--kok", help="göreli yolların kökü (varsayılan: planın iki üstü = proje klasörü)")
    p.add_argument("--yalniz-konusma", metavar="WAV",
                   help="yalnız 'ses: kendi' katmanını (çıktı zamanında, müziksiz) yaz ve çık — kisma.py --konusma girdisi")
    p.set_defaults(islev=calistir_)
