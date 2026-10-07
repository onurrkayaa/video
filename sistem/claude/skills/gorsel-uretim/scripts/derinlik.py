#!/usr/bin/env python3
"""Tek görselden göreli derinlik haritası (Depth Anything V2 Small ONNX, Apache-2.0) → 16 bit PNG (yakın = açık).

  $MEDYA/ortamlar/gorsel/bin/python derinlik.py GIRDI.png --model $MEDYA/modeller/derinlik/da2s_fp16.onnx --cikti analiz/ad-derinlik.png

Girdi yönü pişmiş sRGB çalışma kopyası olmalı (disa_aktar.py --asil). Çıktı girdiyle aynı boyutta. Değerler göreli
(metre değil); katmanlara ayırmak için eşik seç, sonucu kontak.py ile gör.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
from PIL import Image, ImageOps
from pathlib import Path

ORT, SAP = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("girdi")
    ap.add_argument("--model", required=True)
    ap.add_argument("--cikti", required=True)
    ap.add_argument("--uzerine", action="store_true", help="var olan çıktının üzerine yaz")
    a = ap.parse_args()
    c = Path(a.cikti)
    if c.resolve() == Path(a.girdi).resolve():
        sys.exit("HATA: çıktı girdiyle aynı olamaz")
    if c.exists() and not a.uzerine:
        sys.exit(f"HATA: {c} zaten var (üzerine yazmak için --uzerine)")
    import onnxruntime as ort                                 # yalnız ortamlar/gorsel'de var


    im = ImageOps.exif_transpose(Image.open(a.girdi)).convert("RGB")
    W, H = im.size
    olcek = 518 / min(W, H)                                   # kısa kenar 518, en-boy korunur, 14'ün katı
    w, h = (max(14, round(v * olcek / 14) * 14) for v in (W, H))
    x = (np.asarray(im.resize((w, h), Image.BICUBIC), dtype=np.float32) / 255 - ORT) / SAP
    x = x.transpose(2, 0, 1)[None].astype(np.float32)
    s = ort.InferenceSession(a.model, providers=["CPUExecutionProvider"])
    t = time.time()
    d = s.run(None, {s.get_inputs()[0].name: x})[0][0]
    sure = time.time() - t
    d = np.asarray(Image.fromarray(d.astype(np.float32), "F").resize((W, H), Image.BICUBIC))
    d = (d - d.min()) / max(float(d.max() - d.min()), 1e-6)
    Image.fromarray((d * 65535 + 0.5).astype(np.uint16)).save(a.cikti)
    print(f"{W}x{H} (model {w}x{h}, {sure:.2f} sn) → {a.cikti}")
    return 0


if __name__ == "__main__":
    kod = main()
    sys.stdout.flush()
    os._exit(kod)                  # onnxruntime 1.30 kapanışta ara sıra "recursive_mutex lock failed" ile çöküyor (ölçüldü)
