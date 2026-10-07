#!/usr/bin/env python3
"""Nesne silme (LaMa ONNX, Apache-2.0): yalnız maskenin genişletilmiş bölgesi değişir, dışındaki pikseller birebir aynı.

  $MEDYA/ortamlar/gorsel/bin/python lama_sil.py GIRDI.png MASKE.png --model $MEDYA/modeller/lama/lama_fp32.onnx \
      --cikti calisma/gorsel/ad-temiz.png [--genislet 12] [--yumusat 6]

GIRDI: yönü pişmiş sRGB PNG (disa_aktar.py --asil). MASKE: beyaz = silinecek (medya arkaplan-sil --maske ya da
çizilmiş çokgen). Değişen bölge <cikti>-bolge.png olarak yazılır: olc.py SONUC --referans GIRDI --maske BOLGE ile
dışarıda 0 piksel değiştiğini doğrula. Model girişi 512x512: bağlam bölgenin ~2,5 katı kırpılır, sonra geri ölçeklenir.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps


def genislet(m: Image.Image, px: int) -> Image.Image:
    return m.filter(ImageFilter.MaxFilter(2 * px + 1)) if px > 0 else m


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("girdi")
    ap.add_argument("maske")
    ap.add_argument("--model", required=True)
    ap.add_argument("--cikti", required=True)
    ap.add_argument("--genislet", type=int, default=12, help="maskeyi kaç px büyüt (gölge/kenar kalıntısı için)")
    ap.add_argument("--yumusat", type=int, default=6, help="bölgenin içinde kaç px yumuşak geçiş")
    ap.add_argument("--uzerine", action="store_true", help="var olan çıktının üzerine yaz")
    a = ap.parse_args()
    c = Path(a.cikti)
    bolge_c = c.with_name(c.stem + "-bolge.png")
    if c.resolve() in (Path(a.girdi).resolve(), Path(a.maske).resolve()):
        sys.exit("HATA: çıktı girdi ya da maskeyle aynı olamaz")
    if (c.exists() or bolge_c.exists()) and not a.uzerine:
        sys.exit(f"HATA: {c} ya da {bolge_c} zaten var (üzerine yazmak için --uzerine)")
    import onnxruntime as ort                                 # yalnız ortamlar/gorsel'de var


    im = ImageOps.exif_transpose(Image.open(a.girdi)).convert("RGB")
    W, H = im.size
    m = Image.open(a.maske).convert("L").resize((W, H), Image.NEAREST).point(lambda v: 255 if v > 127 else 0)
    bolge = genislet(m, a.genislet)                      # değişebilecek en geniş alan
    cekirdek = genislet(m, max(a.genislet - a.yumusat, 0))
    kutu = bolge.getbbox()
    if not kutu:
        raise SystemExit("HATA: maske boş")
    # bağlam kırpması: bölgenin ~2,5 katı, kare, görsel içinde kaydırılarak
    cx, cy = (kutu[0] + kutu[2]) / 2, (kutu[1] + kutu[3]) / 2
    kenar = min(max(int(2.5 * max(kutu[2] - kutu[0], kutu[3] - kutu[1])), 512), max(W, H))
    x0 = int(min(max(cx - kenar / 2, 0), max(W - kenar, 0)))
    y0 = int(min(max(cy - kenar / 2, 0), max(H - kenar, 0)))
    kirp = (x0, y0, min(x0 + kenar, W), min(y0 + kenar, H))
    if kenar > 1024:
        print(f"uyarı: bağlam {kenar} px → 512'ye küçülüyor, dolgu bulanık olur; uzak nesneleri ayrı maskelerle sil")
    parca = im.crop(kirp)
    pm = bolge.crop(kirp)
    x = np.asarray(parca.resize((512, 512), Image.BICUBIC), dtype=np.float32).transpose(2, 0, 1)[None] / 255
    mk = (np.asarray(pm.resize((512, 512), Image.NEAREST), dtype=np.float32) > 127).astype(np.float32)[None, None]
    s = ort.InferenceSession(a.model, providers=["CPUExecutionProvider"])
    t = time.time()
    y = s.run(None, {"image": x, "mask": mk})[0][0]
    sure = time.time() - t
    if y.max() <= 1.5:                                   # bazı dışa aktarımlar 0..1 verir
        y = y * 255
    dolgu = Image.fromarray(np.clip(y.transpose(1, 2, 0), 0, 255).round().astype(np.uint8)).resize(parca.size, Image.LANCZOS)
    tam = im.copy()
    tam.paste(dolgu, kirp[:2])
    alfa = np.asarray(cekirdek.filter(ImageFilter.GaussianBlur(max(a.yumusat / 2, 0.1))), dtype=np.float32) / 255
    alfa[np.asarray(bolge) == 0] = 0                     # bölge dışı: asıl piksel, birebir
    alfa[np.asarray(m) > 127] = 1                        # silinecek nesne: tamamen dolgu
    asil = np.asarray(im, dtype=np.float32)
    son = asil * (1 - alfa[..., None]) + np.asarray(tam, dtype=np.float32) * alfa[..., None]
    sonuc = Image.fromarray(np.clip(son, 0, 255).round().astype(np.uint8))
    sonuc.save(a.cikti)
    bolge_yol = Path(a.cikti).with_name(Path(a.cikti).stem + "-bolge.png")
    bolge.save(bolge_yol)
    disari = int((np.abs(np.asarray(sonuc, dtype=np.int16) - asil.astype(np.int16)).max(axis=2)[np.asarray(bolge) == 0] > 0).sum())
    print(f"{W}x{H}, bağlam {kirp}, LaMa {sure:.2f} sn, bölge dışında değişen piksel: {disari} → {a.cikti} (bölge: {bolge_yol})")
    return 0 if disari == 0 else 1


if __name__ == "__main__":
    kod = main()
    sys.stdout.flush()
    os._exit(kod)                  # onnxruntime 1.30 kapanışta ara sıra "recursive_mutex lock failed" ile çöküyor (ölçüldü)
