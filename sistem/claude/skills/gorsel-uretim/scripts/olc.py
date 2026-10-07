#!/usr/bin/env python3
"""Görsel ölçümü ve teslim kapıları (Claude göremediğini sayıyla doğrular). Kapı kalırsa çıkış kodu 1.

  python3 olc.py DOSYA... [--boyut 1080x1920] [--en-cok-mb 8] [--teslim] [--json analiz/olcum.json]
  python3 olc.py BUYUK.png --referans ASIL.png          # büyütme sadakati: küçültüp aslıyla PSNR/SSIM
  python3 olc.py SONUC.png --referans ASIL.png --maske M.png   # maske (beyaz=düzenlenen) dışı değişmemeli

Ölçülenler: boyut (yönü uygulanmış), renk etiketi (gömülü ICC adı ya da PNG sRGB etiketi; sips ICC yokken de
"sRGB" der, ona güvenme), EXIF etiketleri/GPS/XMP/PNG metin parçaları, JPEG renk örneklemesi, parlaklıkta kırpık
piksel % (Y<=1 siyah, Y>=254 beyaz), ortalama L*a*b* (görünüm birliği; a* + kırmızı, b* + sarı), netlik (Laplace varyansı; yalnız aynı boyutta karşılaştır), alfa: kapsama %,
yumuşak kenar % (8..247), kirli alfa % (1..7 arka plan sisi + 248..254 yarı geçirgen özne; ~0 olmalı), bağlı parça
ve delik sayısı (en çok 512 px'e küçültülmüş maskede).
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import ExifTags, Image, ImageCms, ImageOps, JpegImagePlugin

KISISEL = {"GPSInfo", "Make", "Model", "BodySerialNumber", "CameraOwnerName", "LensMake", "LensModel",
           "LensSerialNumber", "DateTime", "DateTimeOriginal", "DateTimeDigitized", "Artist", "ImageUniqueID",
           "HostComputer", "UserComment", "MakerNote", "OffsetTime", "OffsetTimeOriginal", "SubsecTimeOriginal"}
ORNEKLEME = {0: "4:4:4", 1: "4:2:2", 2: "4:2:0"}


def exif_adlari(im: Image.Image) -> tuple[list[str], bool]:
    e = im.getexif()
    adlar = {ExifTags.TAGS.get(k, hex(k)) for k in e}
    for ifd in (ExifTags.IFD.Exif, ExifTags.IFD.GPSInfo):
        try:
            alt = e.get_ifd(ifd)
        except Exception:
            alt = {}
        adlar |= {(ExifTags.GPSTAGS if ifd == ExifTags.IFD.GPSInfo else ExifTags.TAGS).get(k, hex(k)) for k in alt}
    try:
        gps = bool(e.get_ifd(ExifTags.IFD.GPSInfo))
    except Exception:
        gps = False
    return sorted(adlar - {"ExifOffset", "GPSInfo"} | ({"GPSInfo"} if gps else set())), gps


def parca_say(m: np.ndarray) -> int:
    """4-komşulu bağlı parça sayısı (en küçük etiket yayılımı + işaretçi atlama)."""
    if not m.any():
        return 0
    h, w = m.shape
    buyuk = h * w
    lab = np.where(m, np.arange(buyuk).reshape(h, w), buyuk)
    while True:
        n = lab.copy()
        n[1:] = np.minimum(n[1:], lab[:-1]); n[:-1] = np.minimum(n[:-1], lab[1:])
        n[:, 1:] = np.minimum(n[:, 1:], lab[:, :-1]); n[:, :-1] = np.minimum(n[:, :-1], lab[:, 1:])
        n = np.where(m, n, buyuk)
        duz = n.ravel()
        on = duz < buyuk
        for _ in range(4):                                   # işaretçi atlama: etiketin etiketine geç
            duz[on] = duz[duz[on]]
        if np.array_equal(n, lab):
            return int(np.unique(n[m]).size)
        lab = n


def delik_say(m: np.ndarray) -> int:
    """Kenara değmeyen arka plan parçaları (ön planın içindeki delikler)."""
    arka = ~m
    if not arka.any():
        return 0
    cerceve = np.zeros((m.shape[0] + 2, m.shape[1] + 2), bool)
    cerceve[1:-1, 1:-1] = arka
    cerceve[0, :] = cerceve[-1, :] = cerceve[:, 0] = cerceve[:, -1] = True   # kenara değenler tek parça olur
    return parca_say(cerceve) - 1


def gri(rgb: np.ndarray) -> np.ndarray:
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


def bulanik(x: np.ndarray, sigma: float = 1.5, r: int = 5) -> np.ndarray:
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    p = np.pad(x, r, mode="reflect")
    y = sum(k[i] * p[:, i:i + x.shape[1]] for i in range(2 * r + 1))[r:-r]
    z = np.pad(y, ((r, r), (0, 0)), mode="reflect")
    return sum(k[i] * z[i:i + x.shape[0]] for i in range(2 * r + 1))


def ssim(a: np.ndarray, b: np.ndarray) -> float:
    """Wang 2004 SSIM, parlaklıkta, 11x11 Gauss (sigma 1.5)."""
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    ma, mb = bulanik(a), bulanik(b)
    va, vb, vab = bulanik(a * a) - ma ** 2, bulanik(b * b) - mb ** 2, bulanik(a * b) - ma * mb
    return float((((2 * ma * mb + c1) * (2 * vab + c2)) / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2))).mean())


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    mse = float(((a - b) ** 2).mean())
    return math.inf if mse == 0 else round(10 * math.log10(255 ** 2 / mse), 2)


def lab_ortalama(rgb: np.ndarray) -> list[float]:
    """sRGB (0..255) → CIELAB (D65) ortalaması: görünüm birliği için fotoğraflar arası L*, a*, b* karşılaştırması."""
    c = rgb / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T
    f = xyz / [0.95047, 1.0, 1.08883]
    f = np.where(f > 0.008856, np.cbrt(f), 7.787 * f + 16 / 116)
    lab = np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], -1)
    return [round(float(v), 2) for v in lab.mean(0)]


def rgb_dizi(im: Image.Image) -> np.ndarray:
    return np.asarray(ImageOps.exif_transpose(im).convert("RGB"), dtype=np.float64)


def olc(yol: Path) -> dict:
    im = Image.open(yol)
    ham = yol.read_bytes()
    d: dict = {"dosya": str(yol), "bicim": im.format, "mb": round(len(ham) / 1e6, 3), "mod": im.mode,
               "yon": im.getexif().get(0x0112, 1)}
    icc = im.info.get("icc_profile")
    if icc:
        d["icc"] = (ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))) or "?").strip()
    else:
        d["icc"] = "sRGB (PNG sRGB etiketi)" if "srgb" in im.info else None
    d["exif"], d["gps"] = exif_adlari(im)
    d["xmp"] = b"<x:xmpmeta" in ham or "xmp" in im.info or "XML:com.adobe.xmp" in im.info
    d["png_metin"] = sorted(getattr(im, "text", {}) or {})
    if im.format == "JPEG":
        d["ornekleme"] = ORNEKLEME.get(JpegImagePlugin.get_sampling(im), "?")
    yonlu = ImageOps.exif_transpose(im)
    d["boyut"] = list(yonlu.size)
    rgba = np.asarray(yonlu.convert("RGBA"))
    gorunur = rgba[..., 3] > 0
    y = (rgba[..., :3].astype(np.float64) @ [0.2126, 0.7152, 0.0722])[gorunur]
    if y.size:
        d["kirpik_siyah_%"] = round(100 * float((y <= 1).mean()), 3)
        d["kirpik_beyaz_%"] = round(100 * float((y >= 254).mean()), 3)
        d["lab_ort"] = lab_ortalama(rgba[..., :3].astype(np.float64)[gorunur])
    g = gri(rgba[..., :3].astype(np.float64))
    lap = g[1:-1, :-2] + g[1:-1, 2:] + g[:-2, 1:-1] + g[2:, 1:-1] - 4 * g[1:-1, 1:-1]
    tam = (rgba[..., 3] == 255)[1:-1, 1:-1]                  # saydam bölge netliği bozmasın
    d["netlik"] = round(float(lap[tam].var()), 1) if tam.any() else None
    if "A" in yonlu.getbands() or "transparency" in yonlu.info:
        a = rgba[..., 3]
        d["alfa_kapsama_%"] = round(100 * float((a >= 128).mean()), 2)
        d["alfa_kenar_%"] = round(100 * float(((a >= 8) & (a <= 247)).mean()), 2)
        d["alfa_kirli_%"] = round(100 * float((((a > 0) & (a < 8)) | ((a > 247) & (a < 255))).mean()), 2)
        k = Image.fromarray(a)
        k.thumbnail((512, 512), Image.BOX)
        m = np.asarray(k) >= 128
        d["alfa_parca"], d["alfa_delik"] = parca_say(m), delik_say(m)
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dosyalar", nargs="+")
    ap.add_argument("--boyut", help="beklenen GxY (yönü uygulanmış)")
    ap.add_argument("--en-cok-mb", type=float)
    ap.add_argument("--teslim", action="store_true",
                    help="sRGB ICC gömülü; GPS, kişisel EXIF, XMP, PNG metni yok")
    ap.add_argument("--referans", help="karşılaştırılacak asıl (kayıpsız)")
    ap.add_argument("--maske", help="--referans ile: beyaz = düzenlenen bölge; dışı birebir aynı olmalı")
    ap.add_argument("--psnr-alt", type=float, default=30.0)
    ap.add_argument("--ssim-alt", type=float, default=0.90)
    ap.add_argument("--json")
    ap.add_argument("--uzerine", action="store_true", help="--json var olan dosyanın üzerine yazsın")
    a = ap.parse_args()
    if a.json and Path(a.json).exists() and not a.uzerine:
        sys.exit(f"HATA: {a.json} zaten var (üzerine yazmak için --uzerine)")

    sonuclar, kalan = [], 0
    for f in a.dosyalar:
        d = olc(Path(f))
        kapi = []
        if a.boyut and d["boyut"] != [int(v) for v in a.boyut.lower().split("x")]:
            kapi.append(f"boyut {d['boyut'][0]}x{d['boyut'][1]} ≠ {a.boyut}")
        if a.en_cok_mb and d["mb"] > a.en_cok_mb:
            kapi.append(f"{d['mb']} MB > {a.en_cok_mb}")
        if a.teslim:
            if not (d["icc"] and "sRGB" in d["icc"]):
                kapi.append(f"ICC sRGB değil: {d['icc']}")
            kisisel = sorted(set(d["exif"]) & KISISEL)
            if kisisel or d["gps"]:
                kapi.append(f"kişisel üst veri: {kisisel}")
            if d["xmp"] or d["png_metin"]:
                kapi.append(f"XMP/PNG metni var: {d['png_metin'] or 'xmp'}")
        if a.referans:
            asil = rgb_dizi(Image.open(a.referans))
            im = ImageOps.exif_transpose(Image.open(f)).convert("RGB")
            geri = im.size != (asil.shape[1], asil.shape[0])
            if geri and a.maske:
                sys.exit("HATA: --maske karşılaştırması aynı boyuttaki kayıpsız dosyalarla yapılır")
            if abs(im.width / im.height - asil.shape[1] / asil.shape[0]) > 0.005 * asil.shape[1] / asil.shape[0]:
                sys.exit(f"HATA: {f} en-boy farklı ({im.width}x{im.height} / {asil.shape[1]}x{asil.shape[0]}): aynı sahne değil, "
                         "ölçüm yapılmadı (büyütmeyi aslın tam katında yap, kırpmadan önce ölç)")
            if geri:
                im = im.resize((asil.shape[1], asil.shape[0]), Image.LANCZOS)
            b = np.asarray(im, dtype=np.float64)
            d["psnr_db"], d["ssim"] = psnr(asil, b), round(ssim(gri(asil), gri(b)), 4)
            if a.maske:
                m = np.asarray(Image.open(a.maske).convert("L").resize(im.size, Image.NEAREST)) >= 128
                fark = np.abs(asil - b).max(axis=2)[~m]
                d["maske_disi_degisen_piksel"] = int((fark > 0).sum())
                d["maske_disi_en_buyuk_fark"] = float(fark.max()) if fark.size else 0.0
                if d["maske_disi_degisen_piksel"]:
                    kapi.append(f"maske dışında {d['maske_disi_degisen_piksel']} piksel değişmiş")
            elif geri:
                d["geri_izdusum"] = True
                if d["psnr_db"] < a.psnr_alt or d["ssim"] < a.ssim_alt:
                    kapi.append(f"geri izdüşüm PSNR {d['psnr_db']} dB / SSIM {d['ssim']} < {a.psnr_alt}/{a.ssim_alt}")
        d["kapi"] = kapi or "gecti"
        kalan += bool(kapi)
        sonuclar.append(d)
        print(json.dumps(d, ensure_ascii=False))
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(sonuclar, ensure_ascii=False, indent=1))
    print(f"{len(sonuclar) - kalan}/{len(sonuclar)} dosya kapılardan geçti", file=sys.stderr)
    return 1 if kalan else 0


if __name__ == "__main__":
    raise SystemExit(main())
