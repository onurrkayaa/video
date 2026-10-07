#!/usr/bin/env python3
"""Görsel dışa aktarma: yön pikselde pişirilir, renk sRGB'ye çevrilir (sRGB ICC gömülür), EXIF/GPS/XMP yazılmaz.

  disa_aktar.py GIRDI --asil --cikti calisma/gorsel/ad.png          # çalışma kopyası: boyut aynı, yön + sRGB
  disa_aktar.py GIRDI --hazir ig-hikaye --cikti cikti/ad_hikaye.jpg [--yerlesim kapla|sigdir]
                [--analiz analiz/ad.json | --merkez 0.5,0.4] [--zemin '#f4f2ee'] [--kalite 90]
  disa_aktar.py GIRDI --boyut 1200x627 --cikti cikti/ad_linkedin.jpg

HEIC ve RAW (DNG, CR2, NEF, ARW…) her zaman sips (Apple çözücüsü) ile geçici PNG'ye çözülür: Pillow TIFF tabanlı
RAW'da tam görüntü yerine gömülü küçük önizlemeyi açar. ICC ve yön etiketi korunur, sonra pişirilir.
--analiz: `medya analiz` çıktısı. medya analiz resimde EXIF yönünü UYGULAMAZ; bu yüzden yalnız yönü pişmiş
(--asil) kopyanın analizi kabul edilir. Yüz varsa yüzler, yoksa ilgi kutuları merkez olur; kutu kırpmanın %5
payına girmezse ya da yüz 9:16 arayüz bandına düşerse uyarır. Var olan dosyanın üzerine yazmaz (--uzerine).
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageCms, ImageColor, ImageFilter, ImageOps, UnidentifiedImageError

HAZIR = {  # kaynak ve doğrulama durumu: references/teknikler.md
    "ig-kare": (1080, 1080), "ig-dikey": (1080, 1350), "ig-hikaye": (1080, 1920),
    "yt-kapak": (3840, 2160), "yt-kapak-hd": (1280, 720), "yt-shorts-kapak": (2160, 3840),
}
SRGB_YOL = Path("/System/Library/ColorSync/Profiles/sRGB Profile.icc")
BANT_UST, BANT_ALT, BANT_YAN = 0.14, 0.35, 0.06      # 9:16 arayüz bandı: Meta Reels reklam rehberi


def srgb_bayt() -> bytes:
    if SRGB_YOL.exists():
        return SRGB_YOL.read_bytes()
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


SIPS = {".heic", ".heif", ".dng", ".cr2", ".cr3", ".nef", ".nrw", ".arw", ".raf", ".orf", ".rw2", ".pef", ".srw", ".raw"}


def ac(yol: Path) -> Image.Image:
    try:
        if yol.suffix.lower() in SIPS:
            raise UnidentifiedImageError(yol)
        im = Image.open(yol)
        im.load()
        return im
    except UnidentifiedImageError:
        with tempfile.TemporaryDirectory() as g:
            gecici = Path(g) / (yol.stem + ".png")
            r = subprocess.run(["sips", "-s", "format", "png", str(yol), "--out", str(gecici)], capture_output=True)
            if r.returncode or not gecici.exists():
                sys.exit(f"HATA: açılamadı (Pillow ve sips): {yol}")
            im = Image.open(gecici)
            im.load()
            return im


def srgbye(im: Image.Image, uyarilar: list[str]) -> tuple[Image.Image, str]:
    """Yön pişirilir; gömülü ICC sRGB değilse sRGB'ye dönüştürülür; alfa korunur."""
    icc = im.info.get("icc_profile")
    im = ImageOps.exif_transpose(im)
    alfa = None
    if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
        alfa = im.getchannel("A")
    taban = im if im.mode in ("RGB", "CMYK") else im.convert("RGB")
    renk = "sRGB (PNG sRGB etiketi)" if "srgb" in im.info else "etiketsiz (sRGB varsayıldı)"
    if icc:
        kaynak = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        ad = (ImageCms.getProfileDescription(kaynak) or "").strip()
        if "sRGB" in ad:
            renk = ad
        else:
            try:
                taban = ImageCms.profileToProfile(taban, kaynak, ImageCms.ImageCmsProfile(io.BytesIO(srgb_bayt())),
                                                  renderingIntent=0, outputMode="RGB")
                renk = f"{ad} → sRGB"
            except ImageCms.PyCMSError as e:
                uyarilar.append(f"ICC uygulanamadı ({ad}: {e}); sRGB varsayıldı")
    taban = taban.convert("RGB")
    if alfa is not None:
        taban.putalpha(alfa)
    return taban, renk


def analiz_merkezi(yol: str, girdi_yon: int, w: int, h: int) -> tuple[tuple[float, float], list[list[float]], str]:
    if not Path(yol).exists():
        sys.exit(f"HATA: analiz dosyası yok: {yol}")
    if girdi_yon not in (0, 1):
        sys.exit(f"HATA: girdinin EXIF yönü {girdi_yon}; medya analiz yönü uygulamadığı için kutular kayar. "
                 "Önce --asil ile yönü pişmiş kopya yap, analizi ve dışa aktarmayı o kopyada çalıştır.")
    d = json.loads(Path(yol).read_text())
    if d.get("analiz_boyutu") != f"{w}x{h}":
        sys.exit(f"HATA: analiz {d.get('analiz_boyutu')} boyutunda, görsel {w}x{h}: aynı dosyanın analizi değil.")
    k = d["kareler"][0]
    yuzler = [y["kutu"] for y in k.get("yuzler") or []]
    kutular, tur = (yuzler, "yüz") if yuzler else (k.get("ilgi") or [], "ilgi")
    if not kutular:
        return (0.5, 0.5), [], "yok"
    x0 = min(b[0] for b in kutular); y0 = min(b[1] for b in kutular)
    x1 = max(b[0] + b[2] for b in kutular); y1 = max(b[1] + b[3] for b in kutular)
    return ((x0 + x1) / 2, (y0 + y1) / 2), kutular, tur


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("girdi")
    ap.add_argument("--cikti", required=True, help=".jpg ya da .png")
    hedef = ap.add_mutually_exclusive_group(required=True)
    hedef.add_argument("--hazir", choices=sorted(HAZIR))
    hedef.add_argument("--boyut", help="GxY, ör. 1200x627")
    hedef.add_argument("--asil", action="store_true", help="boyutu koru (çalışma kopyası)")
    ap.add_argument("--yerlesim", choices=["kapla", "sigdir"], default="kapla",
                    help="kapla: kırparak doldur (varsayılan); sigdir: tümü görünür, kenarlar --zemin")
    merkez = ap.add_mutually_exclusive_group()
    merkez.add_argument("--merkez", help="kırpma merkezi x,y (0..1, yönü pişmiş görselde)")
    merkez.add_argument("--analiz", help="aynı (yönü pişmiş) görselin medya analiz JSON'u: yüz/ilgi merkezli kırpma")
    ap.add_argument("--zemin", default="#ffffff", help="sigdir kenarı ve JPEG'de saydamlığın zemini")
    ap.add_argument("--pay", type=float, default=0.0, help="sigdir: her kenarda boş bırakılacak oran (ör. 0.12)")
    ap.add_argument("--kalite", type=int, default=90)
    ap.add_argument("--keskin", type=int, choices=[0, 1], default=1, help="küçültmeden sonra hafif keskinlik")
    ap.add_argument("--uzerine", action="store_true", help="var olan çıktının üzerine yaz")
    a = ap.parse_args()

    g, c = Path(a.girdi), Path(a.cikti)
    if c.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        sys.exit("HATA: çıktı .jpg ya da .png olmalı")
    if c.resolve() == g.resolve() or "kaynak" in c.resolve().parent.parts:
        sys.exit("HATA: çıktı girdinin ya da kaynak/ klasörünün içine yazılamaz")
    if c.exists() and not a.uzerine:
        sys.exit(f"HATA: {c} zaten var (üzerine yazmak için --uzerine; kullanıcı dosyasıysa önce sor)")

    uyarilar: list[str] = []
    ham = ac(g)
    girdi_yon = ham.getexif().get(0x0112, 0)
    im, renk = srgbye(ham, uyarilar)
    W, H = im.size
    if a.asil:
        w, h = W, H
    elif a.hazir:
        w, h = HAZIR[a.hazir]
    else:
        w, h = (int(v) for v in a.boyut.lower().split("x"))

    kutular, tur = [], "yok"
    if a.analiz:
        (cx, cy), kutular, tur = analiz_merkezi(a.analiz, girdi_yon, W, H)
    elif a.merkez:
        cx, cy = (float(v) for v in a.merkez.split(","))
    else:
        cx, cy = 0.5, 0.5

    if a.yerlesim == "kapla":
        if W / H > w / h:
            kw, kh = H * w / h, float(H)
        else:
            kw, kh = float(W), W * h / w
        x0 = min(max(cx * W - kw / 2, 0.0), W - kw)
        y0 = min(max(cy * H - kh / 2, 0.0), H - kh)
        kutu = (x0, y0, x0 + kw, y0 + kh)
        olcek = w / kw
        sonuc = im.resize((w, h), Image.LANCZOS, box=kutu)
        for b in kutular:                                   # kutular normalize, sol-üst köken
            bx0, by0, bx1, by1 = b[0] * W, b[1] * H, (b[0] + b[2]) * W, (b[1] + b[3]) * H
            pay = 0.05 * min(kw, kh)
            if bx0 < x0 + pay or by0 < y0 + pay or bx1 > x0 + kw - pay or by1 > y0 + kh - pay:
                uyarilar.append(f"{tur} kutusu kırpmanın %5 payı içinde değil: {b}")
            if a.hazir == "ig-hikaye" and tur == "yüz":
                ust, alt = (by0 - y0) / kh, (by1 - y0) / kh
                sol, sag = (bx0 - x0) / kw, (bx1 - x0) / kw
                if ust < BANT_UST or alt > 1 - BANT_ALT or sol < BANT_YAN or sag > 1 - BANT_YAN:
                    uyarilar.append("yüz 9:16 arayüz bandında (üst %14, alt %35, yan %6)")
    else:
        olcek = min(w * (1 - 2 * a.pay) / W, h * (1 - 2 * a.pay) / H)
        kutu = (0.0, 0.0, float(W), float(H))
        icerik = im.resize((max(1, round(W * olcek)), max(1, round(H * olcek))), Image.LANCZOS)
        zemin = ImageColor.getrgb(a.zemin)[:3]
        saydam = icerik.mode == "RGBA" and c.suffix.lower() == ".png"
        sonuc = Image.new("RGBA" if saydam else "RGB", (w, h), (*zemin, 0) if saydam else zemin)
        sonuc.paste(icerik, ((w - icerik.width) // 2, (h - icerik.height) // 2),
                    icerik if icerik.mode == "RGBA" else None)

    if olcek > 1.001:
        uyarilar.append(f"büyütme ×{olcek:.2f} (Lanczos): ayrıntı oluşmaz; gerekiyorsa önce büyütme yolu")
    if a.keskin and olcek < 0.9:
        if sonuc.mode == "RGBA":
            alfa = sonuc.getchannel("A")
            sonuc = sonuc.convert("RGB").filter(ImageFilter.UnsharpMask(radius=0.6, percent=40, threshold=2))
            sonuc.putalpha(alfa)
        else:
            sonuc = sonuc.filter(ImageFilter.UnsharpMask(radius=0.6, percent=40, threshold=2))

    c.parent.mkdir(parents=True, exist_ok=True)
    if c.suffix.lower() == ".png":
        sonuc.save(c, "PNG", icc_profile=srgb_bayt())
    else:
        if sonuc.mode == "RGBA":
            duz = Image.new("RGB", sonuc.size, ImageColor.getrgb(a.zemin)[:3])
            duz.paste(sonuc, mask=sonuc.getchannel("A"))
            sonuc = duz
        sonuc.save(c, "JPEG", quality=a.kalite, subsampling=0, optimize=True, icc_profile=srgb_bayt())

    print(json.dumps({"cikti": str(c), "boyut": [w, h], "olcek": round(olcek, 4),
                      "kirpma": [round(v, 1) for v in kutu], "merkez": [round(cx, 3), round(cy, 3)],
                      "merkez_kaynagi": tur if a.analiz else ("elle" if a.merkez else "orta"), "renk": renk,
                      "mb": round(c.stat().st_size / 1e6, 3), "uyarilar": uyarilar}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
