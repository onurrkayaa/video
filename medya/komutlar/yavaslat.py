"""medya yavaslat <video> --hiz 0.5 [--bas sn --sure sn] [--fps 30] [--yontem dogal|apple|rife|ffmpeg] [--cikti x.mov]

Ağır çekim. Yöntem kaynağa göre seçilir (biri başarısız olursa ya da asılırsa sıradakine düşülür):
  dogal   Kaynak yeterince yüksek gerçek kare hızındaysa (ör. telefonun 120/240 fps "slo-mo" çekimi) ara kare
          üretilmez; kareler yeniden zamanlanır. En temiz sonuç.
  rife    ≤ 2000 px kaynakta ilk: RIFE v4.6 (rife-ncnn-vulkan, MIT; GPU/Metal, Neural Engine'e bağlı değil). Gerçek
          kamera görüntüsünde en iyisi (el kamerası 37,7 / Apple 36,4 dB; kaydırmada en kötü %5 kare 28,8 / 26,2).
  apple   4K kaynakta ilk (hız ve disk: RIFE PNG ara kareleri GB'larca yer tutar): Apple VTFrameRateConversion.
  ffmpeg  Son yedek: minterpolate (mci, aobmc, bidir).
Ölçüm 2 (2026-10-05, yalnız üretilen ara kareler, kareler ham çözülerek; sistem/devam/yavas-cekim/): yüksek
hareket 1080p ×4: RIFE v4.6 35,2 dB, Apple 35,0, minterpolate 33,5; 540p ×4: Apple 33,8, RIFE 33,1, minterpolate
31,2; el kamerası 24 fps ×2: RIFE 37,7, minterpolate 32,6 (Apple ölçülemedi: Neural Engine takılıydı); sakin
çekimde hepsi ≈ 40,5. Apple ≈ RIFE > minterpolate; 1080p'de Apple ~2 kat hızlı.
Ölçüm (2026-10-05, gerçek 240 fps kaynaktan doğruluk sınaması, kareler doğrudan çözülerek; ffmpeg'in psnr
süzgeci zaman damgası farkında kare kaydırdığı için KULLANILMADI): büyük harekette (5→20 fps) ara kare
ortalaması Apple 43,2 dB (kodlama tavanı düşülünce ≈44,2), minterpolate 42,9, karıştırma 40,8 (en kötü 32,3:
hayalet görüntü). Apple ile minterpolate kalitede denk, Apple ~3 kat hızlı. Karıştırma (framerate) kullanılmaz.
Önce kaynak hazırlanır: HDR ise SDR'ye, değişken/yinelenen kareliyse gerçek fps'te sabit kare hızına çevrilir.
Çıktı varsayılan olarak ProRes 422 HQ .mov (ara dosya; görsel kayıpsız). Ses yazılmaz (ağır çekim sessizdir).
"""
from __future__ import annotations

import json
import math
import shutil
import tempfile
from pathlib import Path

from ..ortak import ARAC, MedyaHatasi, apple_calistir, bilgi, calistir, ffmpeg, probe
from .incele import incele_dosya

APPLE = ARAC / "medya-apple"
RIFE = ARAC / "rife" / "rife-ncnn-vulkan"
RIFE_MODEL = ARAC / "rife" / "rife-v4.6"


def _hazirla(girdi: str, hedef: Path, fps: float, bas: float | None, sure: float | None, sdr: bool) -> Path:
    """Kesit + sabit kare hızı (+ gerekirse HDR→SDR) — kayıpsıza yakın ara dosya."""
    vf = []
    if sdr:
        vf.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,"
                  "zscale=t=bt709:m=bt709:r=tv")
    vf += [f"fps={fps:g}", "setsar=1", "format=yuv420p"]
    komut = [ffmpeg(), "-nostdin", "-v", "error", "-y"]
    if bas is not None:
        komut += ["-ss", f"{bas:.4f}"]
    if sure is not None:
        komut += ["-t", f"{sure:.4f}"]
    komut += ["-i", girdi, "-an", "-vf", ",".join(vf), "-fps_mode", "cfr", "-c:v", "libx264", "-crf", "6",
              "-preset", "veryfast", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
              "-color_range", "tv", str(hedef)]
    calistir(komut, hata_mesaji="kaynak hazırlanamadı")
    return hedef


def _kodla_mov(komut_vf: str, girdi: str, cikti: str, fps: float, bas=None, sure=None) -> None:
    komut = [ffmpeg(), "-nostdin", "-v", "error", "-y"]
    if bas is not None:
        komut += ["-ss", f"{bas:.4f}"]
    if sure is not None:
        komut += ["-t", f"{sure:.4f}"]
    komut += ["-i", girdi, "-an", "-vf", komut_vf, "-r", f"{fps:g}"]
    if cikti.lower().endswith(".mov"):
        komut += ["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le"]
    else:
        komut += ["-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p"]
    komut += ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", cikti]
    calistir(komut, hata_mesaji="kodlama başarısız")


def _rife(hazir: Path, ara: Path, kat: int, taban: float) -> dict:
    """PNG kareler → RIFE → PNG kareler → ProRes (taban fps, kat kat uzun). Diskte yer yoksa denemez."""
    v = next(x for x in probe(hazir)["streams"] if x.get("codec_type") == "video")
    w, h = int(v["width"]), int(v["height"])
    K = round(float(probe(hazir)["format"]["duration"]) * taban)
    gerek = (K + K * kat) * w * h * 3 * 0.6                     # PNG ≈ ham boyutun %60'ı (doğal görüntü)
    with tempfile.TemporaryDirectory() as g:
        bos = shutil.disk_usage(g).free
        if bos - gerek < 5e9:
            raise MedyaHatasi(f"RIFE ara kareleri ~{gerek / 1e9:.1f} GB ister, disk yetmez (5 GB taban)")
        gir, cik = Path(g) / "gir", Path(g) / "cik"
        gir.mkdir(); cik.mkdir()
        calistir([ffmpeg(), "-nostdin", "-v", "error", "-i", str(hazir), "-vf",
                  "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-fps_mode", "passthrough",
                  str(gir / "%08d.png")], hata_mesaji="kareler çıkarılamadı")
        K = len(list(gir.glob("*.png")))
        komut = [str(RIFE), "-i", str(gir), "-o", str(cik), "-m", str(RIFE_MODEL), "-n", str(K * kat), "-f", "%08d.png"]
        if max(w, h) > 2000:
            komut.append("-u")                                     # 4K: UHD kipi (akış ölçeği)
        calistir(komut, zaman_asimi=180 + 2 * K * kat, hata_mesaji="RIFE ara kare üretimi")
        # ara.mov sözleşmesi (Apple ve minterpolate ile aynı): taban fps, kat kat uzun = 1/kat hızında
        calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-framerate", f"{taban:g}", "-i",
                  str(cik / "%08d.png"), "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv422p10le",
                  "-c:v", "prores_ks", "-profile:v", "3", "-colorspace", "bt709", "-color_primaries", "bt709",
                  "-color_trc", "bt709", "-color_range", "tv", str(ara)], hata_mesaji="kodlama başarısız")
    return {"kare": K * kat, "model": RIFE_MODEL.name}


def yavaslat(girdi: str, cikti: str, hiz: float, *, fps: float | None = None, bas: float | None = None,
             sure: float | None = None, yontem: str | None = None) -> dict:
    if not 0.05 <= hiz < 1:
        raise MedyaHatasi("--hiz 0,05 ile 1 arasında olmalı (0,5 = yarı hız)")
    r = incele_dosya(girdi)
    v = r.get("video") or {}
    if not v:
        raise MedyaHatasi("video akışı yok")
    gercek = v["kare_olcumu"].get("gercek_fps") or v["fps_nominal"]
    taban = fps or min(30.0, round(gercek))                     # çıktının oynatma kare hızı
    gereken = taban / hiz                                        # doğal ağır çekim için gereken kaynak fps
    sonuc = {"girdi": girdi, "cikti": cikti, "hiz": hiz, "fps": taban, "kaynak_gercek_fps": round(gercek, 2)}
    if (yontem in (None, "dogal")) and gercek >= gereken * 0.98:
        vf = f"fps={gereken:g},setpts=PTS/{hiz:g},fps={taban:g},setsar=1"
        if v.get("hdr"):
            vf = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,"
                  "zscale=t=bt709:m=bt709:r=tv," + vf)
        _kodla_mov(vf, girdi, cikti, taban, bas, sure)
        sonuc["yontem"] = "dogal"
        return sonuc
    kat = math.ceil(1 / hiz - 1e-9)
    kat = max(2, min(8, kat))
    with tempfile.TemporaryDirectory() as g:
        hazir = _hazirla(girdi, Path(g) / "hazir.mp4", taban, bas, sure, bool(v.get("hdr")))
        ara = Path(g) / "ara.mov"
        hv = next(x for x in probe(hazir)["streams"] if x.get("codec_type") == "video")
        sira = ("rife", "apple", "ffmpeg") if max(int(hv["width"]), int(hv["height"])) <= 2000 else ("apple", "rife", "ffmpeg")
        sira = [y for y in sira if y != "apple" or APPLE.exists()]
        sira = [y for y in sira if y != "rife" or (RIFE.exists() and RIFE_MODEL.exists())]
        if yontem in ("apple", "rife"):                              # zorlanan önce; başarısızsa yine sıradaki
            sira = [yontem] + [y for y in sira if y != yontem]
        elif yontem == "ffmpeg":
            sira = ["ffmpeg"]
        kullanilan = sira[0]
        for kullanilan in sira:
            try:
                if kullanilan == "apple":
                    n = float(probe(hazir)["format"]["duration"]) * taban * kat        # üretilecek kare
                    s = apple_calistir([str(APPLE), "yavaslat", str(hazir), str(ara), str(kat), "--kodek", "prores"],
                                       zaman_asimi=180 + 2 * n, hata_mesaji="Apple ara kare üretimi")
                    sonuc["apple"] = json.loads(s.stdout.decode().strip().splitlines()[-1])
                elif kullanilan == "rife":
                    sonuc["rife"] = _rife(hazir, ara, kat, taban)
                break
            except MedyaHatasi as e:
                sonuc.setdefault("dusulen", []).append(f"{kullanilan}: {str(e)[:300]}")
                bilgi(f"⚠ {kullanilan} ara kare üretimi başarısız, sıradakine düşülüyor: {str(e)[:200]}")
        if kullanilan == "ffmpeg":
            _kodla_mov(f"minterpolate=fps={taban * kat:g}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
                       f"setpts=PTS*{kat},fps={taban:g}", str(hazir), str(ara), taban)
        # ara.mov 1/kat hızında; istenen hıza (hiz) getir: hiz*kat >= 1 → kare düşürerek hızlandır
        hizlan = hiz * kat
        if abs(hizlan - 1) < 1e-6 and cikti.lower().endswith(".mov"):
            Path(ara).replace(cikti)
        else:
            _kodla_mov(f"setpts=PTS/{hizlan:g},fps={taban:g}", str(ara), cikti, taban)
        sonuc["yontem"] = kullanilan
        sonuc["kat"] = kat
    sonuc["sure"] = float(probe(cikti)["format"]["duration"])
    return sonuc


def calistir_(args) -> int:
    g = Path(args.girdi)
    cikti = args.cikti or str(g.with_name(g.stem + f"-yavas{args.hiz:g}".replace(".", "_") + ".mov"))
    r = yavaslat(args.girdi, cikti, args.hiz, fps=args.fps, bas=args.bas, sure=args.sure, yontem=args.yontem)
    print(f"{r['yontem']}: hız {r['hiz']:g}x, {r['fps']:g} fps, kaynak gerçek {r['kaynak_gercek_fps']} fps → {cikti}"
          + (f" ({r['sure']:.2f} sn)" if "sure" in r else ""))
    if r["yontem"] == "ffmpeg":
        print("  ⚠ ffmpeg ara karesi hızlı harekette kenar yırtılması yapabilir: medya kontak ile kontrol et")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="ağır çekim (doğal / Apple ML / ffmpeg)")
    p.add_argument("girdi")
    p.add_argument("--hiz", type=float, required=True, help="oynatma hızı: 0.5 = yarı hız, 0.25 = çeyrek")
    p.add_argument("--fps", type=float, help="çıktı kare hızı (varsayılan: 30 ya da kaynağın gerçek fps'i)")
    p.add_argument("--bas", type=float, help="kesit başlangıcı (sn)")
    p.add_argument("--sure", type=float, help="kesit süresi (sn, kaynak süresi)")
    p.add_argument("--yontem", choices=["dogal", "apple", "rife", "ffmpeg"],
                   help="önce bunu dene (varsayılan: dogal → ≤2000 px'te rife, 4K'da apple → diğeri → ffmpeg)")
    p.add_argument("--cikti", help="varsayılan <ad>-yavas<hız>.mov (ProRes 422 HQ)")
    p.set_defaults(islev=calistir_)
