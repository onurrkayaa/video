#!/usr/bin/env python3
"""Deneme videosunun ses efektleri — tamamen kodla üretilir, lisans gerektirmez.

  python3 deneme/ses/efekt.py  ->  deneme/ses/cin.wav, deneme/ses/hisirti.wav  (44,1 kHz, 16 bit, stereo)

Belirlenimci: gürültü sabit tohumlu numpy üretecinden gelir; her çalıştırma aynı dosyayı yazar.
Başta sessizlik yok, son yumuşak sönümle biter (tık yok), tepe -3 dBFS.
"""
import wave
from pathlib import Path

import numpy as np

SR = 44100
KLASOR = Path(__file__).resolve().parent
TEPE = 10 ** (-3 / 20)
rng = np.random.default_rng(20261004)


def yaz(ad, sol, sag):
    x = np.stack([sol, sag], axis=1)
    x -= x.mean(axis=0)
    x *= TEPE / np.abs(x).max()
    n = int(0.03 * SR)                                   # son 30 ms yumuşak kapanış
    x[-n:] *= np.linspace(1, 0, n)[:, None]
    with wave.open(str(KLASOR / ad), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def cin(sure=1.6):
    """Yumuşak çan: kısmi tonlar üstel sönümle, hafif atak, sağ-sol küçük gecikme."""
    t = np.arange(int(sure * SR)) / SR
    atak = np.minimum(t / 0.004, 1.0)
    ton = np.zeros_like(t)
    for f, g, d in [(1318.5, 1.0, 0.55), (1975.5, 0.45, 0.35), (2637.0, 0.25, 0.22), (3951.0, 0.10, 0.12)]:
        ton += g * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
    ton *= atak
    gecik = int(0.006 * SR)
    sag = np.concatenate([np.zeros(gecik), ton[:-gecik]])
    return ton, sag


def hisirti(sure=0.7):
    """Kısa hışırtı: süzülmüş gürültü, ortası en yüksek; süzgeç frekansı yükselir."""
    n = int(sure * SR)
    t = np.arange(n) / SR
    zarf = np.sin(np.pi * t / sure) ** 2
    cikis = []
    for _ in range(2):
        g = rng.standard_normal(n)
        y = np.zeros(n)
        a = 0.0
        fc = 400 + 3600 * (t / sure)                     # tek kutuplu alçak geçiren, kayan kesim
        k = 1 - np.exp(-2 * np.pi * fc / SR)
        for i in range(n):
            a += k[i] * (g[i] - a)
            y[i] = a
        cikis.append(y * zarf)
    return cikis[0], cikis[1]


if __name__ == "__main__":
    yaz("cin.wav", *cin())
    yaz("hisirti.wav", *hisirti())
    print("yazıldı:", ", ".join(p.name for p in sorted(KLASOR.glob("*.wav"))))
