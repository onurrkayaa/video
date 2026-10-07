#!/usr/bin/env python3
"""Kolaj: satır başına görsel sayısıyla düzen, eşit boşluk, her hücre yüz/ilgi merkezli kırpılır → sRGB PNG usta.

  kolaj.py A.png B.png C.png --duzen 2,1 --boyut 1080x1350 --cikti calisma/kolaj.png \
      [--analiz a.json b.json c.json | --merkez 0.5,0.35 - 0.6,0.4] [--bosluk 0.015] [--zemin '#f4f2ee'] [--dikey]

--duzen 2,1: üstte 2, altta 1 hücre (sırayla A, B / C). --dikey: sayılar sütun başına (1,2 = solda büyük, sağda 2).
--analiz: her görselin (yönü pişmiş kopyanın) medya analiz JSON'u, aynı sırayla ("-" = analiz yok, orta). Yüz hücre kenarına
%5 paydan yakınsa uyarır. Teslim için ardından disa_aktar.py (JPEG + ICC) ve olc.py --teslim.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageColor

sys.path.insert(0, str(Path(__file__).parent))
from disa_aktar import ac, analiz_merkezi, srgb_bayt, srgbye  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gorseller", nargs="+")
    ap.add_argument("--duzen", required=True, help="satır (ya da --dikey ile sütun) başına hücre sayısı, ör. 2,1")
    ap.add_argument("--boyut", required=True, help="GxY, ör. 1080x1350")
    ap.add_argument("--cikti", required=True, help=".png")
    ap.add_argument("--analiz", nargs="*", default=[])
    ap.add_argument("--merkez", nargs="*", default=[], help="görsel başına x,y (0..1, yönü pişmiş görselde) ya da '-'; "
                    "--analiz yerine (ör. ANE takılıyken elle)")
    ap.add_argument("--bosluk", type=float, default=0.015, help="kısa kenarın oranı; dış pay da aynı")
    ap.add_argument("--zemin", default="#f4f2ee")
    ap.add_argument("--dikey", action="store_true")
    ap.add_argument("--uzerine", action="store_true")
    a = ap.parse_args()

    sayilar = [int(v) for v in a.duzen.split(",")]
    if sum(sayilar) != len(a.gorseller):
        sys.exit(f"HATA: düzen {sum(sayilar)} hücre, {len(a.gorseller)} görsel")
    if a.analiz and len(a.analiz) != len(a.gorseller):
        sys.exit("HATA: --analiz her görsel için bir JSON (aynı sıra)")
    if a.merkez and (a.analiz or len(a.merkez) != len(a.gorseller)):
        sys.exit("HATA: --merkez her görsel için bir x,y ya da '-' (aynı sıra) ve --analiz ile birlikte kullanılmaz")
    try:
        elle = [None if m == "-" else tuple(float(v) for v in m.split(",")) for m in a.merkez]
    except ValueError:
        sys.exit("HATA: --merkez değerleri x,y biçiminde (0..1)")
    if any(m and (len(m) != 2 or not all(0 <= v <= 1 for v in m)) for m in elle):
        sys.exit("HATA: --merkez değerleri x,y biçiminde (0..1)")
    c = Path(a.cikti)
    if c.suffix.lower() != ".png" or (c.exists() and not a.uzerine):
        sys.exit("HATA: çıktı .png olmalı ve var olan dosyanın üzerine yazılmaz (--uzerine)")
    W, H = (int(v) for v in a.boyut.lower().split("x"))
    b = round(a.bosluk * min(W, H))
    if a.dikey:
        W, H = H, W                                          # sütun düzenini satır düzeni gibi kur, sonra çevir

    hucreler = []
    satir_h = (H - b * (len(sayilar) + 1)) / len(sayilar)
    for i, n in enumerate(sayilar):
        hucre_w = (W - b * (n + 1)) / n
        y0 = b + i * (satir_h + b)
        hucreler += [(b + j * (hucre_w + b), y0, hucre_w, satir_h) for j in range(n)]
    if a.dikey:
        W, H = H, W
        hucreler = [(y, x, h, w) for x, y, w, h in hucreler]

    tuval = Image.new("RGB", (W, H), ImageColor.getrgb(a.zemin)[:3])
    rapor, uyarilar = [], []
    for k, (yol, (x, y, w, h)) in enumerate(zip(a.gorseller, hucreler)):
        ham = ac(Path(yol))
        yon = ham.getexif().get(0x0112, 0)
        im, _ = srgbye(ham, uyarilar)
        im = im.convert("RGB")
        iw, ih = im.size
        hx0, hy0, hx1, hy1 = round(x), round(y), round(x + w), round(y + h)
        tw, th = hx1 - hx0, hy1 - hy0
        if elle and elle[k]:
            (cx, cy), kutular, tur = elle[k], [], "elle"
        elif a.analiz and a.analiz[k] != "-":
            (cx, cy), kutular, tur = analiz_merkezi(a.analiz[k], yon, iw, ih)
        else:
            (cx, cy), kutular, tur = (0.5, 0.5), [], "orta"
        kw, kh = (ih * tw / th, float(ih)) if iw / ih > tw / th else (float(iw), iw * th / tw)
        kx = min(max(cx * iw - kw / 2, 0.0), iw - kw)
        ky = min(max(cy * ih - kh / 2, 0.0), ih - kh)
        tuval.paste(im.resize((tw, th), Image.LANCZOS, box=(kx, ky, kx + kw, ky + kh)), (hx0, hy0))
        pay = 0.05 * min(kw, kh)
        for bx, by, bw, bh in kutular:
            if bx * iw < kx + pay or by * ih < ky + pay or (bx + bw) * iw > kx + kw - pay or (by + bh) * ih > ky + kh - pay:
                uyarilar.append(f"{Path(yol).name}: {tur} kutusu hücre kenarına %5 paydan yakın ya da dışında")
        olcek = tw / kw
        if olcek > 1.001:
            uyarilar.append(f"{Path(yol).name}: hücrede ×{olcek:.2f} büyütme (ayrıntı oluşmaz)")
        rapor.append({"gorsel": yol, "hucre": [hx0, hy0, tw, th], "merkez": tur, "olcek": round(olcek, 3)})

    c.parent.mkdir(parents=True, exist_ok=True)
    tuval.save(c, "PNG", icc_profile=srgb_bayt())
    print(json.dumps({"cikti": str(c), "boyut": [W, H], "bosluk_px": b, "hucreler": rapor, "uyarilar": uyarilar},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
