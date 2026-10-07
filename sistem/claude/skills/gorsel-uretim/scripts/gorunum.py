#!/usr/bin/env python3
"""Parametrik renk görünümü → .cube 3B LUT (fotoğraf ve video aynı LUT'la aynı görünümü alır).

  gorunum.py --hazir sicak-sinematik --cikti plan/gorunum.cube
  gorunum.py --sicaklik -0.03 --cikti calisma/foto3-duzelt.cube        # tek fotoğrafa ön düzeltme
  arac/ffmpeg -nostdin -v error -i A.png -vf "lut3d=file=plan/gorunum.cube:interp=tetrahedral" -frames:v 1 B.png
  # ön düzeltme + görünüm: -vf "lut3d=file=calisma/foto3-duzelt.cube,lut3d=file=plan/gorunum.cube"

Girdi sRGB (gama) değerleri kabul edilir: önce disa_aktar.py --asil ile sRGB çalışma kopyası. Yalnız piksel başına
renk işlemleri; keskinlik, vinyet, gren LUT'a giremez. Çıktıda nötr gri rampanın kayması ve kanal tekdüzeliği yazılır.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

HAZIR = {  # sicaklik, kontrast, doygunluk, siyah, golge
    "notr": (0.0, 0.0, 0.0, 0.0, 0.0),
    "sicak-sinematik": (0.045, 0.30, -0.10, 0.025, 0.020),   # sıcak ışıklar, hafif camgöbeği gölge, mat siyah
}
LUMA = np.array([0.2126, 0.7152, 0.0722])


def uygula(x: np.ndarray, sicaklik: float, kontrast: float, doygunluk: float, siyah: float, golge: float) -> np.ndarray:
    """x: [..., 3] 0..1 sRGB."""
    y = x + kontrast * (x * x * (3 - 2 * x) - x)            # S eğrisi (kontrast 0..1 aralığında tekdüze)
    L = (y @ LUMA)[..., None]
    y = L + (1 + doygunluk) * (y - L)                        # doygunluk
    isik, gol = L, (1 - L) ** 2
    y = y + np.concatenate([sicaklik * isik, 0.25 * sicaklik * isik, -sicaklik * isik], -1)   # sıcak ışıklar
    y = y + np.concatenate([-golge * gol, 0.3 * golge * gol, golge * gol], -1)               # serin gölgeler
    y = siyah + (1 - siyah) * y                              # mat siyah (siyah noktası kalkar)
    return np.clip(y, 0, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cikti", required=True)
    ap.add_argument("--hazir", choices=sorted(HAZIR), default="notr")
    for ad, yard in (("sicaklik", "+ sıcak / - soğuk (0.03-0.06 ölçülü)"), ("kontrast", "0..1 S eğrisi"),
                     ("doygunluk", "-0.2..0.2"), ("siyah", "mat siyah kaldırma 0..0.05"), ("golge", "gölge camgöbeği 0..0.04")):
        ap.add_argument(f"--{ad}", type=float, help=yard)
    ap.add_argument("--boyut", type=int, default=33, help="LUT ızgarası (33 ya da 65)")
    ap.add_argument("--uzerine", action="store_true", help="var olan çıktının üzerine yaz")
    a = ap.parse_args()
    if Path(a.cikti).exists() and not a.uzerine:
        sys.exit(f"HATA: {a.cikti} zaten var (elle ayarlı .cube olabilir; üzerine yazmak için --uzerine)")
    p = dict(zip(("sicaklik", "kontrast", "doygunluk", "siyah", "golge"), HAZIR[a.hazir]))
    p.update({k: getattr(a, k) for k in p if getattr(a, k) is not None})
    if not 0 <= p["kontrast"] <= 1:
        sys.exit("HATA: kontrast 0..1 olmalı (dışında eğri tekdüze olmaz)")

    n = a.boyut
    v = np.linspace(0, 1, n)
    b, g, r = np.meshgrid(v, v, v, indexing="ij")            # .cube: kırmızı en hızlı değişir
    tablo = uygula(np.stack([r, g, b], -1).reshape(-1, 3), **p)
    with open(a.cikti, "w") as f:
        f.write(f'TITLE "{Path(a.cikti).stem}"\nLUT_3D_SIZE {n}\n')
        f.writelines(f"{x:.6f} {y:.6f} {z:.6f}\n" for x, y, z in tablo)

    rampa = uygula(np.repeat(np.linspace(0, 1, 256)[:, None], 3, 1), **p)
    tekduze = bool((np.diff(rampa, axis=0) >= -1e-9).all())
    orta = rampa[128] * 255
    print(f"{n}^3 LUT → {a.cikti}  {p}")
    print(f"nötr gri 128 → RGB {orta.round(1).tolist()} (R-B {orta[0] - orta[2]:+.1f}); siyah → {(rampa[0] * 255).round(1).tolist()}; "
          f"beyaz → {(rampa[-1] * 255).round(1).tolist()}; gri rampada kanal tekdüze: {'evet' if tekduze else 'HAYIR'}")
    return 0 if tekduze else 1


if __name__ == "__main__":
    raise SystemExit(main())
