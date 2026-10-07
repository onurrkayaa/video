"""medya kontak <video> — zaman damgalı kare ızgarası (Claude'un videoyu "görme" aracı).

Kareler ffmpeg ile hızlı aramayla tek tek çıkarılır, PIL ile etiketlenip ızgara yapılır. Belirli anlar
(--anlar 1.5,3,10) ya da eşit aralık (--aralik 2) seçilebilir. Çıktı bir PNG; Read ile açılıp incelenir.
"""
from __future__ import annotations

import math
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from ..ortak import MedyaHatasi, calistir, ffmpeg, oran, probe, video_akisi

YAZI = "/System/Library/Fonts/Supplemental/Arial.ttf"


def _yazi(boy):
    try:
        return ImageFont.truetype(YAZI, boy)
    except OSError:
        return ImageFont.load_default()


def kare_al(video: str, t: float, hedef: Path, genislik: int, fps: float | None = None) -> None:
    """t anında EKRANDA olan kareyi alır. ffmpeg'in -ss'i 't'den sonraki ilk kareyi verir (t bir karenin süresi
    içindeyse SONRAKİ kareyi) — bu yüzden o karenin başlangıcının çeyrek kare öncesine aranır."""
    if fps is None:
        fps = oran((video_akisi(probe(video)) or {}).get("avg_frame_rate")) or 30.0
    k = math.floor(t * fps + 1e-6)
    ara = max(0.0, (k - 0.25) / fps)
    calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-ss", f"{ara:.6f}", "-i", video, "-frames:v", "1",
              "-vf", f"scale={genislik}:-2", str(hedef)], hata_mesaji=f"kare alınamadı: {t:.2f} sn")


def kontak_sayfasi(video: str, anlar: list[float], cikti: str | Path, *, genislik: int = 220, sutun: int = 8,
                   etiketler: list[str] | None = None) -> Path:
    cikti = Path(cikti)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    fps = oran((video_akisi(probe(video)) or {}).get("avg_frame_rate")) or 30.0
    with tempfile.TemporaryDirectory() as g:
        kareler = []
        for i, t in enumerate(anlar):
            yol = Path(g) / f"{i:04d}.png"
            try:
                kare_al(video, t, yol, genislik, fps)
                kareler.append(Image.open(yol).convert("RGB"))
            except Exception:
                kareler.append(Image.new("RGB", (genislik, genislik), (60, 0, 0)))
        h = max(k.height for k in kareler)
        f = _yazi(max(12, genislik // 13))
        serit = f.size + 6 if hasattr(f, "size") else 18          # etiket şeridi karenin ALTINDA: kareyi örtmez
        satir = (len(kareler) + sutun - 1) // sutun
        sayfa = Image.new("RGB", (sutun * (genislik + 4), satir * (h + serit + 4)), "black")
        ciz = ImageDraw.Draw(sayfa)
        for i, k in enumerate(kareler):
            x, y = (i % sutun) * (genislik + 4), (i // sutun) * (h + serit + 4)
            sayfa.paste(k, (x, y))
            etiket = (etiketler[i] if etiketler else None) or f"{anlar[i]:.2f}s"
            ciz.text((x + 3, y + h + 2), etiket, font=f, fill=(255, 230, 0))
        sayfa.save(cikti)
    return cikti


def calistir_(args) -> int:
    if Path(args.video).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff"}:
        raise MedyaHatasi("medya kontak video içindir; görseller için: gorsel-uretim becerisi (scripts/kontak.py)")
    sure = float(probe(args.video)["format"]["duration"])
    if args.anlar:
        anlar = [float(x) for x in args.anlar.split(",")]
    else:
        adim = args.aralik or max(sure / 48, 0.5)
        anlar, t = [], adim / 2
        while t < sure:
            anlar.append(round(t, 3))
            t += adim
    v = video_akisi(probe(args.video)) or {}
    dikey = int(v.get("height", 1)) > int(v.get("width", 1))
    genislik = args.genislik or (160 if dikey else 260)
    sutun = args.sutun or (10 if dikey else 6)
    cikti = args.cikti or str(Path(args.video).with_suffix("")) + "-kontak.png"
    kontak_sayfasi(args.video, anlar, cikti, genislik=genislik, sutun=sutun)
    print(f"{len(anlar)} kare → {cikti}")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="zaman damgalı temas sayfası")
    p.add_argument("video")
    p.add_argument("--aralik", type=float, help="kareler arası saniye (varsayılan: süreye göre ~48 kare)")
    p.add_argument("--anlar", help="virgülle ayrılmış anlar, ör. 1.5,3,10")
    p.add_argument("--genislik", type=int, help="kare genişliği (px)")
    p.add_argument("--sutun", type=int)
    p.add_argument("--cikti", help="PNG yolu")
    p.set_defaults(islev=calistir_)
