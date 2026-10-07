#!/usr/bin/env python3
"""Kesiği temizler: (1) kirli alfa kenetlenir (<8 → 0 arka plan sisi, >247 → 255 yarı geçirgen özne); (2) yarı
saydam kenar piksellerindeki eski arka plan rengi (hale), yakındaki tam opak özne renkleriyle değiştirilir.
Koyu ya da farklı renkli zemine konacak her kesikte kullan; sonucu kontak.py --zemin hepsi ile gör.

  $MEDYA/.venv/bin/python kenar_arindir.py kesik.png --cikti kesik-arindi.png [--esik 0.98]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def kutu_bulanik(x: np.ndarray, r: int) -> np.ndarray:
    """(2r+1)x(2r+1) kutu ortalaması, kenarlar yansıtılarak (toplam alanla)."""
    p = np.pad(x, [(r + 1, r), (r + 1, r)] + [(0, 0)] * (x.ndim - 2), mode="edge").cumsum(0).cumsum(1)
    k = 2 * r + 1
    return (p[k:, k:] - p[:-k, k:] - p[k:, :-k] + p[:-k, :-k]) / (k * k)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kesik")
    ap.add_argument("--cikti", required=True)
    ap.add_argument("--esik", type=float, default=0.98, help="bu alfanın üstü 'saf özne' sayılır")
    a = ap.parse_args()
    if Path(a.cikti).resolve() == Path(a.kesik).resolve():
        raise SystemExit("HATA: çıktı girdinin üzerine yazamaz")

    im = np.asarray(Image.open(a.kesik).convert("RGBA"), dtype=np.float64)
    a8 = np.where(im[..., 3] < 8, 0, np.where(im[..., 3] > 247, 255, im[..., 3]))
    rgb, alfa = im[..., :3], a8 / 255
    ic = (alfa >= a.esik).astype(np.float64)
    kenar = (alfa > 0) & (alfa < a.esik)
    renk = np.zeros_like(rgb)
    dolu = np.zeros(alfa.shape, bool)
    for r in (1, 2, 4, 8, 16, 32):                      # içten dışa: en yakın opak renkler önce
        pay = kutu_bulanik(rgb * ic[..., None], r)
        payda = kutu_bulanik(ic, r)
        yeni = (payda > 1e-3) & ~dolu
        renk[yeni] = pay[yeni] / payda[yeni][:, None]
        dolu |= yeni
    cikti = rgb.copy()
    sec = kenar & dolu
    cikti[sec] = renk[sec]
    Image.fromarray(np.dstack([np.clip(cikti + 0.5, 0, 255), a8]).astype(np.uint8), "RGBA").save(a.cikti)
    print(f"{int(sec.sum())} kenar pikselinin rengi arındı ({100 * sec.mean():.2f}%) → {a.cikti}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
