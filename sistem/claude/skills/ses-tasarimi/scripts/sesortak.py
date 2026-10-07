"""ses-tasarimi betiklerinin ortak yardımcıları. Tek başına çalıştırılmaz.

Ortam: ortamlar/ses Python'u (numpy, scipy, soundfile). İçerik: ses okuma/yazma, BS.1770 K-ağırlıklı ses
yüksekliği (libebur128/ffmpeg ebur128 ile aynı süzgeç katsayıları), ffmpeg ebur128 ölçümü (kapılı entegre LUFS,
LRA, gerçek tepe), konuşma aralığı okuma, aralık birleştirme ve RMS kapısıyla konuşma bulma.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import lfilter

MEDYA = Path(os.environ.get("MEDYA", "/Users/onurkaya/Projects/video"))
FFMPEG = str(MEDYA / "arac" / "ffmpeg")

# medya ses-olay sınıfları: kısmada "konuşan ses" sayılanlar (kahkaha dahil: doğal ses parçaları)
SES_OLAY_KONUSMA = ("speech", "whispering", "laughter", "giggling", "belly_laugh")


def hata(mesaj: str) -> None:
    print(f"HATA: {mesaj}", file=sys.stderr)
    sys.exit(2)


def oku(yol) -> tuple[np.ndarray, int]:
    """Ses dosyası → (kanal, örnek) float32 dizi, örnekleme hızı."""
    if not Path(yol).exists():
        hata(f"dosya yok: {yol}")
    x, sr = sf.read(str(yol), dtype="float32", always_2d=True)
    return np.ascontiguousarray(x.T), int(sr)


def yaz(yol, x: np.ndarray, sr: int, alt: str = "FLOAT") -> Path:
    """(kanal, örnek) dizi → WAV. alt: FLOAT (32 bit kayan) | PCM_24 | PCM_16.
    FLOAT scipy ile yazılır: libsndfile kayan WAV'a zaman damgalı PEAK bloğu ekler, aynı ses farklı bayt olur
    (ölçüldü) — lisans defterindeki özet (hash) tekrar üretilebilir kalsın."""
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    if alt == "FLOAT":
        from scipy.io import wavfile
        wavfile.write(str(yol), sr, np.ascontiguousarray(np.asarray(x, dtype=np.float32).T))
    else:
        sf.write(str(yol), np.asarray(x, dtype=np.float32).T, sr, subtype=alt, format="WAV")
    return yol


def json_yaz(yol, veri) -> Path:
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return yol


# ------------------------------------------------------------------ ses yüksekliği (BS.1770)
def _k_katsayilari(sr: int):
    """K-ağırlık süzgeci (raf + yüksek geçiren); libebur128 formülü, 48 kHz'de BS.1770 tablosunun aynısı."""
    f0, g, q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    k = math.tan(math.pi * f0 / sr)
    vh = 10 ** (g / 20)
    vb = vh ** 0.4996667741545416
    a0 = 1 + k / q + k * k
    raf_b = [(vh + vb * k / q + k * k) / a0, 2 * (k * k - vh) / a0, (vh - vb * k / q + k * k) / a0]
    raf_a = [1.0, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0]
    f0, q = 38.13547087602444, 0.5003270373238773
    k = math.tan(math.pi * f0 / sr)
    d = 1 + k / q + k * k
    yg_b = [1.0, -2.0, 1.0]
    yg_a = [1.0, 2 * (k * k - 1) / d, (1 - k / q + k * k) / d]
    return (raf_b, raf_a), (yg_b, yg_a)


def k_agirlikla(x: np.ndarray, sr: int) -> np.ndarray:
    (b1, a1), (b2, a2) = _k_katsayilari(sr)
    return lfilter(b2, a2, lfilter(b1, a1, x.astype(np.float64), axis=-1), axis=-1)


def yukseklik(xk: np.ndarray, maske: np.ndarray | None = None) -> float:
    """K-ağırlıklı sinyalin (kanal, örnek) kapısız ses yüksekliği, LUFS. Kanal enerjileri toplanır (BS.1770)."""
    if maske is not None:
        xk = xk[:, maske[: xk.shape[1]]]
    if xk.shape[1] == 0:
        return float("nan")
    ms = float(np.sum(np.mean(xk ** 2, axis=1)))
    return -0.691 + 10 * math.log10(ms) if ms > 0 else float("-inf")


def ffmpeg_olc(yol) -> dict:
    """ffmpeg ebur128: kapılı entegre LUFS, LRA ve gerçek tepe (medya ustala --olc ile aynı yöntem)."""
    s = subprocess.run([FFMPEG, "-nostdin", "-nostats", "-i", str(yol), "-vn", "-af",
                        "ebur128=peak=true:framelog=quiet", "-f", "null", "-"],
                       capture_output=True, stdin=subprocess.DEVNULL)
    metin = s.stderr.decode("utf-8", "replace")
    ozet = metin[metin.rfind("Summary:"):]

    def sayi(desen):
        m = re.search(desen, ozet)
        return float(m.group(1)) if m else float("nan")

    return {"lufs": sayi(r"I:\s+(-?[\d.]+|-inf) LUFS"), "lra": sayi(r"LRA:\s+(-?[\d.]+) LU"),
            "tepe_dbtp": sayi(r"Peak:\s+(-?[\d.]+|-inf) dBFS")}


# ------------------------------------------------------------------ aralıklar
def araliklar_oku(yol, kaydir: float = 0.0, siniflar=SES_OLAY_KONUSMA) -> list[tuple[float, float]]:
    """medya yaziya-dok JSON'u (kelimeler), medya ses-olay JSON'u (olaylar) ya da [[bas, son], …] → aralıklar."""
    try:
        v = json.loads(Path(yol).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        hata(f"aralık dosyası okunamadı: {yol} ({e})")
    if isinstance(v, dict) and "kelimeler" in v:
        r = [(float(w["bas"]), float(w["son"])) for w in v["kelimeler"]]
    elif isinstance(v, dict) and "olaylar" in v:
        r = [(float(o["bas"]), float(o["son"])) for o in v["olaylar"] if o.get("sinif") in siniflar]
    elif isinstance(v, list):
        r = [(float(a), float(b)) for a, b in v]
    else:
        hata(f"tanınmayan aralık biçimi: {yol} (yaziya-dok/ses-olay JSON'u ya da [[bas, son], …] bekleniyor)")
    return sorted((a + kaydir, b + kaydir) for a, b in r if b > a)


def birlestir(araliklar, bosluk: float) -> list[tuple[float, float]]:
    """Aralarındaki boşluk 'bosluk' sn'den kısa aralıkları birleştirir."""
    cikti: list[list[float]] = []
    for a, b in sorted(araliklar):
        if cikti and a - cikti[-1][1] < bosluk:
            cikti[-1][1] = max(cikti[-1][1], b)
        else:
            cikti.append([a, b])
    return [(a, b) for a, b in cikti]


def rms_kapisi(x: np.ndarray, sr: int, kare: float = 0.02, adim: float = 0.01, taban_db: float = -55.0,
               en_kisa: float = 0.15) -> list[tuple[float, float]]:
    """Konuşma katmanında etkin bölgeler. Eşik: taban gürültüsü (5. yüzdelik) ile konuşma tepesi (95. yüzdelik)
    ortası, en az taban+6 dB ve taban_db. Ortam sesi kalmış katmanda da konuşmayı ayırır; emin değilsen
    Whisper kelime zamanlarını kullan (--araliklar)."""
    m = x.mean(axis=0).astype(np.float64)
    n, h = int(kare * sr), int(adim * sr)
    if len(m) < n:
        return []
    c = np.concatenate([[0.0], np.cumsum(m * m)])
    bas = np.arange(0, len(m) - n + 1, h)
    db = np.maximum(10 * np.log10((c[bas + n] - c[bas]) / n + 1e-20), -100.0)
    if db.max() <= -70:
        return []
    taban, tepe = float(np.percentile(db, 5)), float(np.percentile(db, 95))
    esik = max(taban_db, (taban + tepe) / 2, taban + 6)
    acik = np.concatenate([[False], db > esik, [False]])
    d = np.flatnonzero(np.diff(acik.astype(np.int8)))
    r = []
    for i, j in zip(d[0::2], d[1::2]):                      # [i, j) açık kareler
        a, b = bas[i] / sr, (bas[j - 1] + n) / sr
        if b - a >= en_kisa:
            r.append((round(a, 4), round(b, 4)))
    return r


def maske(araliklar, sr: int, n: int) -> np.ndarray:
    """Aralıkların kapsadığı örnekler (bool, uzunluk n)."""
    m = np.zeros(n, dtype=bool)
    for a, b in araliklar:
        i, j = max(0, int(round(a * sr))), min(n, int(round(b * sr)))
        if j > i:
            m[i:j] = True
    return m
