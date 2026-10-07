"""Kodla ses efekti: whoosh, riser, vurus (impact), tik — tohumlu (aynı komut = aynı dosya), tepe anı kare ızgarasında.

  PY=$MEDYA/ortamlar/ses/bin/python; B=$MEDYA/sistem/claude/skills/ses-tasarimi/scripts
  $PY $B/efekt.py --tur whoosh --fps 30 --tohum 3 --cikti calisma/ses/efektler/whoosh-3.wav --json calisma/ses/efektler/whoosh-3.json

Tarifler (araştırma 2026-10-05, audio-production.md "Procedural/synth SFX"):
  whoosh  pembe gürültü × zarf; bant geçiren merkez 300 Hz → 4 kHz (zarfla yükselir, sonra iner); soldan sağa kaydırma
  riser   üstel sinüs taraması + gürültü kabarması; tepe kesimden 1 kare ÖNCE, kesimde (tepe_sn) biter; yankı kuyruğu
  vurus   55 Hz civarı sinüs (60 → 45 Hz düşüş) + 5 ms gürültü vuruşu + kısa oda yankısı; vuruş tepe_sn'de
  tik     3 ms bant sınırlı gürültü patlaması (arayüz tıkı); tepe_sn'de
Çıktı: 48 kHz stereo 32 bit kayan WAV, tepe --tepe-db dBFS. Lisans riski yok (kendi kodumuz; pedalboard GPL-3 çıktıyı
kısıtlamaz). Yerleştirme: data-start (ya da adelay) = olay anı − tepe_sn; --fps verilince tepe_sn kare katıdır, olay anı
da kare ızgarasındaysa data-start ızgarada kalır. Seviye yaratıcı karardır: miksteki son seviyeyi kullanıcı dinleyerek onaylar.
Künye (--json): ayarlar, betik sürümü, tarih, WAV'ın sha256 özeti.
Çıkış kodu: 0 tamam, 2 kullanım hatası.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.signal import butter, istft, sosfilt, stft

import sesortak as so

SURUM = "1.1"  # künyeye yazılır; üretimi değiştiren her düzeltmede artır

SR = 48000
VARSAYILAN = {  # tür: (süre sn, tepe sn)
    "whoosh": (0.8, 0.45),
    "riser": (2.4, 2.0),
    "vurus": (1.6, 0.05),
    "tik": (0.08, 0.02),
}


def pembe(n: int, rng: np.random.Generator) -> np.ndarray:
    """Pembe gürültü (1/f güç): beyaz gürültünün tayfı 1/sqrt(f) ile şekillendirilir."""
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    X[1:] /= np.sqrt(f[1:])
    X[0] = 0
    x = np.fft.irfft(X, n)
    return x / (np.abs(x).max() + 1e-12)


def kaydir(x: np.ndarray, pan: np.ndarray) -> np.ndarray:
    """Eşit güçlü kaydırma; pan -1 (sol) … +1 (sağ), örnek başına."""
    a = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)])


def whoosh(sure: float, tepe: float, rng) -> np.ndarray:
    n = int(round(sure * SR))
    t = np.arange(n) / SR
    zarf = np.where(t <= tepe, (t / tepe) ** 2, np.clip(1 - (t - tepe) / (sure - tepe), 0, 1) ** 1.5)
    g = pembe(n, rng)
    # zamanla değişen bant geçiren: STFT karelerinde log-frekansta Gauss (≈1 oktav), merkez zarfla 300 Hz → 4 kHz
    f, tk, Z = stft(g, SR, nperseg=1024, noverlap=768)
    ek = np.interp(tk, t, zarf)
    merkez = 300 * (4000 / 300) ** ek
    lf = np.log2(np.maximum(f, 1.0))[:, None]
    Z *= np.exp(-0.5 * ((lf - np.log2(merkez)[None, :]) / 0.6) ** 2)
    _, y = istft(Z, SR, nperseg=1024, noverlap=768)
    y = np.pad(y, (0, max(0, n - len(y))))[:n] * zarf
    return kaydir(y, np.linspace(-0.7, 0.7, n))


def riser(sure: float, tepe: float, fps: float | None, rng) -> np.ndarray:
    n = int(round(sure * SR))
    t = np.arange(n) / SR
    zirve = max(0.05, tepe - (1 / fps if fps else 1 / 30))      # tepe kesimden 1 kare önce
    u = np.clip(t / zirve, 0, 1)
    f = 150 * (1500 / 150) ** u                                    # üstel tarama 150 → 1500 Hz
    faz = 2 * np.pi * np.cumsum(f) / SR
    zarf = u ** 3
    zarf[t > zirve] = np.clip(1 - (t[t > zirve] - zirve) / max(tepe - zirve, 1e-3), 0, 1)
    zarf[t >= tepe] = 0.0                                          # kesimde biter
    ton = 0.6 * np.sin(faz) + 0.25 * np.sin(2 * faz)
    nz = sosfilt(butter(2, 800, "highpass", fs=SR, output="sos"), pembe(n, rng))
    y = (ton + 0.5 * nz / (np.abs(nz).max() + 1e-12)) * zarf
    return kaydir(y, np.zeros(n))


def vurus(sure: float, tepe: float, rng) -> np.ndarray:
    n = int(round(sure * SR))
    t = np.arange(n) / SR - tepe
    on = t >= 0
    f = 45 + 15 * np.exp(-np.maximum(t, 0) / 0.08)                # 60 → 45 Hz düşüş
    faz = 2 * np.pi * np.cumsum(np.where(on, f, 0)) / SR
    gov = np.sin(faz) * np.exp(-np.maximum(t, 0) / 0.35) * on
    i0 = int(round(tepe * SR))
    L = int(0.005 * SR)
    patlama = np.zeros(n)
    patlama[i0:i0 + L] = sosfilt(butter(2, 1500, "highpass", fs=SR, output="sos"), rng.standard_normal(L)) * np.hanning(L)
    y = gov + 0.5 * patlama / (np.abs(patlama).max() + 1e-12)
    return kaydir(y, np.zeros(n))


def tik(sure: float, tepe: float, rng) -> np.ndarray:
    n = int(round(sure * SR))
    y = np.zeros(n)
    L = int(0.003 * SR)
    i0 = int(round(tepe * SR)) - L // 2
    y[i0:i0 + L] = sosfilt(butter(2, [2000, 6000], "bandpass", fs=SR, output="sos"), rng.standard_normal(L)) * np.hanning(L)
    return kaydir(y, np.zeros(n))


def yanki(x: np.ndarray, oda: float, islak: float) -> np.ndarray:
    from pedalboard import Pedalboard, Reverb
    kuyruk = int(0.5 * SR)
    x = np.pad(x, ((0, 0), (0, kuyruk))).astype(np.float32)
    y = Pedalboard([Reverb(room_size=oda, wet_level=islak, dry_level=1.0, width=1.0)])(x, SR)
    son = np.flatnonzero(np.abs(y).max(axis=0) > 1e-4)               # sessiz kuyruğu kırp, 5 ms sönümle bitir
    y = y[:, : (son[-1] + 1 if len(son) else y.shape[1])]
    L = min(int(0.005 * SR), y.shape[1])
    y[:, -L:] *= np.linspace(1, 0, L)
    return y


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tur", required=True, choices=list(VARSAYILAN))
    p.add_argument("--cikti", required=True)
    p.add_argument("--sure", type=float, help="dosya süresi sn (yankı kuyruğu hariç)")
    p.add_argument("--tepe", type=float, help="olayın (kesim/vuruş) dosyadaki anı, sn")
    p.add_argument("--fps", type=float, help="tepe anını bu kare ızgarasına oturt (ör. 30)")
    p.add_argument("--tohum", type=int, default=1, help="rastgelelik tohumu (farklı geçişlere farklı tohum)")
    p.add_argument("--tepe-db", type=float, default=-18.0, help="çıktı tepe düzeyi dBFS (başlangıç; miks seviyesi ayrı)")
    p.add_argument("--json", help="künye JSON'u (lisans defteri için)")
    a = p.parse_args()
    sure, tepe = VARSAYILAN[a.tur]
    sure = a.sure or sure
    tepe = a.tepe if a.tepe is not None else tepe
    if a.fps:
        tepe = round(tepe * a.fps) / a.fps
    if not 0 < tepe < sure:
        so.hata(f"tepe ({tepe:.4f}) 0 ile süre ({sure}) arasında olmalı")
    rng = np.random.default_rng(a.tohum)
    if a.tur == "whoosh":
        x = yanki(whoosh(sure, tepe, rng), 0.25, 0.12)
    elif a.tur == "riser":
        x = yanki(riser(sure, tepe, a.fps, rng), 0.5, 0.25)
    elif a.tur == "vurus":
        x = yanki(vurus(sure, tepe, rng), 0.3, 0.18)
    else:
        x = tik(sure, tepe, rng)
    x = x / (np.abs(x).max() + 1e-12) * 10 ** (a.tepe_db / 20)
    so.yaz(a.cikti, x, SR)
    olc = so.ffmpeg_olc(a.cikti)
    kunye = {"dosya": a.cikti, "tur": a.tur, "tohum": a.tohum, "sure_sn": round(x.shape[1] / SR, 4), "tepe_sn": round(tepe, 6),
             "fps": a.fps, "tepe_db": a.tepe_db, "gercek_tepe_dbtp": olc["tepe_dbtp"],
             "uretim": "sistem/claude/skills/ses-tasarimi/scripts/efekt.py (kendi kodumuz)", "lisans": "kendi üretimimiz; kısıt yok",
             "yerlestirme": "data-start = olay anı − tepe_sn", "betik_surumu": SURUM, "argumanlar": vars(a),
             "tarih": datetime.date.today().isoformat(), "sha256": hashlib.sha256(Path(a.cikti).read_bytes()).hexdigest()}
    if a.json:
        so.json_yaz(a.json, kunye)
    print(f"{a.tur} (tohum {a.tohum}) {kunye['sure_sn']:.3f} sn, olay anı {tepe:.4f} sn, gerçek tepe {olc['tepe_dbtp']:.1f} dBTP"
          f" → {a.cikti}\n  yerleştirme: data-start = olay anı − {tepe:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
