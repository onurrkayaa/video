#!/usr/bin/env python3
"""Görsel temas sayfası: Claude sonuçları bununla Read ile görür (medya kontak yalnız video içindir).

  kontak.py A.png B.jpg ... --cikti analiz/kontak.png [--sutun 4]
  kontak.py kesik.png --zemin hepsi --cikti analiz/kenar.png          # saydamlık: siyah/beyaz/dama üstünde
  kontak.py asil.png lanczos.png esrgan.png --kirp 0.4,0.2,0.15,0.15 --cikti analiz/yakin.png
            # aynı bölge (0..1, yönü uygulanmış görselde) her dosyadan; büyütme en yakın komşu = gerçek pikseller
  kontak.py hikaye.jpg --guvenli dikey --cikti analiz/guvenli.png      # 9:16 bant bindirmesi (yalnız denetim)

Sayfanın uzun kenarı en çok --en-uzun (1568) px: Read küçültmeden görür. Etiket: ad, boyut, yakınlık.
HEIC/RAW açılmaz: önce disa_aktar.py --asil ile PNG çalışma kopyası.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

YAZI = "/System/Library/Fonts/Supplemental/Arial.ttf"
BANT = {"dikey": (0.14, 0.35, 0.06)}   # üst, alt, yan: Meta Reels reklam rehberi (references/teknikler.md)


def dama(boyut: tuple[int, int], k: int = 16) -> Image.Image:
    im = Image.new("RGB", boyut, (255, 255, 255))
    d = ImageDraw.Draw(im)
    for y in range(0, boyut[1], k):
        for x in range((y // k) % 2 * k, boyut[0], 2 * k):
            d.rectangle([x, y, x + k - 1, y + k - 1], fill=(200, 200, 200))
    return im


def zeminler(im: Image.Image, secim: str | None) -> list[tuple[str, Image.Image]]:
    if im.mode != "RGBA" or not secim:
        return [("", im.convert("RGB"))]
    cikti = []
    for ad in (["siyah", "beyaz", "dama"] if secim == "hepsi" else [secim]):
        z = dama(im.size) if ad == "dama" else Image.new("RGB", im.size, (0, 0, 0) if ad == "siyah" else (255, 255, 255))
        z.paste(im, mask=im.getchannel("A"))
        cikti.append((ad, z))
    return cikti


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gorseller", nargs="+")
    ap.add_argument("--cikti", required=True)
    ap.add_argument("--sutun", type=int)
    ap.add_argument("--zemin", choices=["siyah", "beyaz", "dama", "hepsi"], help="saydam görseller için")
    ap.add_argument("--kirp", help="x,y,g,y oranları (0..1): her dosyadan aynı bölge, hücreye büyütülür")
    ap.add_argument("--guvenli", choices=sorted(BANT), help="güvenli bant bindirmesi (teslime girmez)")
    ap.add_argument("--en-uzun", type=int, default=1568)
    ap.add_argument("--uzerine", action="store_true", help="var olan çıktının üzerine yaz")
    a = ap.parse_args()
    c = Path(a.cikti)
    if any(c.resolve() == Path(f).resolve() for f in a.gorseller):
        raise SystemExit("HATA: çıktı girdilerden biri olamaz")
    if c.exists() and not a.uzerine:
        raise SystemExit(f"HATA: {c} zaten var (üzerine yazmak için --uzerine)")

    karolar = []
    for f in a.gorseller:
        im = ImageOps.exif_transpose(Image.open(f))
        etiket = f"{Path(f).name} {im.width}x{im.height}"
        if im.mode in ("I;16", "I;16B", "I;16L", "I", "F"):         # 16 bit / kayan nokta (ör. derinlik): 8 bite ölçekle
            d = np.asarray(im, dtype=np.float64)
            im = Image.fromarray((255 * (d - d.min()) / max(float(np.ptp(d)), 1e-9)).astype(np.uint8))
        im = im.convert("RGBA") if ("A" in im.getbands() or "transparency" in im.info) else im.convert("RGB")
        if a.kirp:
            x, y, w, h = (float(v) for v in a.kirp.split(","))
            im = im.crop((round(x * im.width), round(y * im.height), round((x + w) * im.width), round((y + h) * im.height)))
        for ad, k in zeminler(im, a.zemin):
            if a.guvenli:
                ust, alt, yan = BANT[a.guvenli]
                kat = Image.new("RGBA", k.size, (0, 0, 0, 0))
                d = ImageDraw.Draw(kat)
                d.rectangle([0, 0, k.width, round(k.height * ust)], fill=(255, 0, 0, 90))
                d.rectangle([0, k.height - round(k.height * alt), k.width, k.height], fill=(255, 0, 0, 90))
                for x0 in (0, k.width - round(k.width * yan)):
                    d.rectangle([x0, 0, x0 + round(k.width * yan), k.height], fill=(255, 0, 0, 90))
                k = Image.alpha_composite(k.convert("RGBA"), kat).convert("RGB")
            karolar.append((etiket + (f" {ad}" if ad else ""), k))

    n = len(karolar)
    sutun = a.sutun or min(n, 4)
    satir = (n + sutun - 1) // sutun
    bosluk, etiket_h = 6, 22
    hucre = (a.en_uzun - bosluk * (sutun + 1)) // sutun
    oran = max(k.height / k.width for _, k in karolar)
    hucre_h = round(hucre * oran)
    if hucre_h > a.en_uzun - etiket_h - 2 * bosluk:          # uzun dikey görsel: hücreyi daralt, boşluk kalmasın
        hucre_h = a.en_uzun - etiket_h - 2 * bosluk
        hucre = round(hucre_h / oran)
    sayfa = Image.new("RGB", (bosluk + sutun * (hucre + bosluk), bosluk + satir * (hucre_h + etiket_h + bosluk)),
                      (40, 40, 40))
    try:
        yazi = ImageFont.truetype(YAZI, 14)
    except OSError:
        yazi = ImageFont.load_default()
    d = ImageDraw.Draw(sayfa)
    for i, (etiket, k) in enumerate(karolar):
        olcek = min(hucre / k.width, hucre_h / k.height)
        if a.kirp or olcek < 1:              # kırpıntı büyütülür (en yakın komşu: pikseller olduğu gibi); tam kare yalnız küçülür
            yeni = (max(1, round(k.width * olcek)), max(1, round(k.height * olcek)))
            k = k.resize(yeni, Image.NEAREST if olcek > 1 else Image.LANCZOS)
        x = bosluk + (i % sutun) * (hucre + bosluk)
        y = bosluk + (i // sutun) * (hucre_h + etiket_h + bosluk)
        sayfa.paste(k, (x + (hucre - k.width) // 2, y + etiket_h + (hucre_h - k.height) // 2))
        d.text((x + 2, y + 3), etiket + (f" ×{olcek:.1f}" if a.kirp else ""), font=yazi, fill=(255, 230, 0))
    if max(sayfa.size) > a.en_uzun:
        sayfa.thumbnail((a.en_uzun, a.en_uzun), Image.LANCZOS)
    Path(a.cikti).parent.mkdir(parents=True, exist_ok=True)
    sayfa.save(a.cikti)
    print(f"{n} karo, {sayfa.width}x{sayfa.height} → {a.cikti}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
