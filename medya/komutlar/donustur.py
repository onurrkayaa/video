"""medya sdr | cfr | meta-temizle — teslim ve kurgu öncesi dönüştürmeler.

sdr          HDR (HLG / PQ / Dolby Vision tabanı) → SDR bt709. Ton eşlemesiz çevrilen iPhone HDR çekimi soluk ve
             gri görünür; burada doğrusal ışığa açılıp tonemap (varsayılan mobius) ile sıkıştırılır.
cfr          Değişken kare hızını (telefon VFR) sabite çevirir; kurgu ve ses hizası için şart.
meta-temizle Konum/GPS, cihaz ve tarih üst verisini siler (paylaşılacak çıktılar için). Görüntü/ses yeniden
             kodlanmaz (video: akış kopyası; görsel: exiftool ile, yön ve renk profili korunarak).
Asıl dosyanın üzerine asla yazmaz; varsayılan çıktı <ad>-sdr / -cfr / -temiz.
"""
from __future__ import annotations

from pathlib import Path

from ..ortak import MedyaHatasi, calistir, ffmpeg, oran, probe, video_akisi

GORSEL = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".tif", ".tiff"}


def _cikti(girdi: str, ek: str, cikti: str | None, uzanti: str | None = None) -> str:
    g = Path(girdi)
    c = cikti or str(g.with_name(g.stem + ek + (uzanti or g.suffix)))
    if Path(c).resolve() == g.resolve():
        raise MedyaHatasi("çıktı girdinin üzerine yazamaz")
    return c


def sdr_(args) -> int:
    p = probe(args.girdi)
    v = video_akisi(p) or {}
    trc = v.get("color_transfer")
    if trc not in ("smpte2084", "arib-std-b67") and not args.zorla:
        print(f"HDR değil (aktarım: {trc}); dönüştürme gerekmiyor. Yine de: --zorla")
        return 0
    tin = trc or "arib-std-b67"
    vf = (f"zscale=tin={tin}:pin=bt2020:min=bt2020nc:t=linear:npl={args.npl},format=gbrpf32le,"
          f"zscale=p=bt709,tonemap=tonemap={args.yontem}:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    c = _cikti(args.girdi, "-sdr", args.cikti, ".mp4")
    calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", args.girdi, "-map", "0:v:0", "-map", "0:a?",
              "-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf), "-pix_fmt", "yuv420p",
              "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
              "-c:a", "copy", "-movflags", "+faststart", c])
    print(f"SDR ({args.yontem}, npl {args.npl}) → {c}\n  kontrol: medya kontak {c}  (soluk/aşırı karanlık mı bak)")
    return 0


def cfr_(args) -> int:
    v = video_akisi(probe(args.girdi)) or {}
    hedef = args.fps or round(oran(v.get("r_frame_rate")) or 30)
    c = _cikti(args.girdi, "-cfr", args.cikti, ".mp4")
    calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", args.girdi, "-map", "0:v:0", "-map", "0:a?",
              "-vf", f"fps={hedef}", "-fps_mode", "cfr", "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf),
              "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", c])
    print(f"{hedef} fps sabit → {c}")
    return 0


def meta_temizle_(args) -> int:
    g = Path(args.girdi)
    if g.suffix.lower() in GORSEL:
        from ..ortak import ARAC
        c = _cikti(args.girdi, "-temiz", args.cikti)
        if (ARAC / "exiftool").exists():
            # yeniden kodlama yok: bütün üst veri silinir, yalnız yön ve renk profili geri yazılır
            calistir([str(ARAC / "exiftool"), "-q", "-all=", "-tagsFromFile", "@", "-Orientation", "-ICC_Profile",
                      "-ColorSpaceTags", "-o", c, str(g)], hata_mesaji="exiftool üst veriyi silemedi")
        else:
            from PIL import Image, ImageOps
            im = ImageOps.exif_transpose(Image.open(g))        # yedek: yönü uygula, EXIF'siz yeniden kaydet (kayıplı)
            im.save(c, **({"quality": 95} if Path(c).suffix.lower() in (".jpg", ".jpeg") else {}))
    else:
        c = _cikti(args.girdi, "-temiz", args.cikti)
        calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", args.girdi, "-map", "0", "-map_metadata", "-1",
                  "-map_metadata:s", "-1", "-map_chapters", "-1", "-c", "copy", "-movflags", "+faststart", c])
    print(f"üst veri temizlendi → {c}")
    return 0


def kaydet(alt, ad):
    if ad == "sdr":
        p = alt.add_parser(ad, help="HDR → SDR (bt709)")
        p.add_argument("girdi")
        p.add_argument("--yontem", default="mobius", choices=["mobius", "hable", "reinhard", "clip"],
                       help="ton eşleme (varsayılan mobius: referans beyazı korur; hable ölçümde Y 182'ye düşürdü, mobius 218)")
        p.add_argument("--npl", type=int, default=100, help="nominal tepe parlaklık (nit); HLG için 100–203 dene")
        p.add_argument("--crf", type=int, default=16)
        p.add_argument("--zorla", action="store_true")
        p.add_argument("--cikti")
        p.set_defaults(islev=sdr_)
    elif ad == "cfr":
        p = alt.add_parser(ad, help="VFR → CFR")
        p.add_argument("girdi")
        p.add_argument("--fps", type=float)
        p.add_argument("--crf", type=int, default=16)
        p.add_argument("--cikti")
        p.set_defaults(islev=cfr_)
    elif ad == "meta-temizle":
        p = alt.add_parser(ad, help="konum/kişisel üst veriyi sil")
        p.add_argument("girdi")
        p.add_argument("--cikti")
        p.set_defaults(islev=meta_temizle_)
