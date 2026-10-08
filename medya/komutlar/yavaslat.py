"""medya yavaslat <video> --hiz 0.5 [--bas sn --sure sn] [--fps 30] [--kirp x,y,gen,yük] [--olcek GxY]
                [--yontem dogal|apple|rife|ffmpeg] [--cikti x.mov|x.mp4]

Ağır çekim. Yöntem kaynağa göre seçilir (biri başarısız olursa ya da asılırsa sıradakine düşülür):
  dogal   Kaynak yeterince yüksek gerçek kare hızındaysa (ör. telefonun 120/240 fps "slo-mo" çekimi) ara kare
          üretilmez; kareler yeniden zamanlanır. En temiz sonuç.
  rife    Hazır kare ≤ 2000 px ise ilk: RIFE v4.6 (rife-ncnn-vulkan, MIT; GPU/Metal, Neural Engine'e bağlı değil).
          Gerçek kamera görüntüsünde en iyisi (1920x800 ×2: el kamerası 37,7 / Apple 36,4 dB; kaydırmada 31,6 / 31,0,
          en kötü %5 karenin ortalaması 27,3 / 26,2 — sistem/devam/yavas-cekim/ozet.jsonl).
  apple   Hazır kare > 2000 px ise ilk (hız ve disk: RIFE PNG ara kareleri GB'larca yer tutar): Apple VTFrameRateConversion.
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
Ara kare yolunda hazırlık hızı, kat 2–8 arası tam sayı olacak biçimde kaynağın tam böleni olan en yüksek hızdır: çıktı
ızgarasına düşen gerçek kareler korunur. Kat kaynak hızında tam sayıysa bu bütün gerçek karelerdir (60 fps 0,25x → 60 fps
× 2; eskiden 30 fps'e inip × 4, yarısı atılıyordu); değilse ızgaraya düşmeyenler atılır (60 fps 0,2x → 30 fps × 5: tek
kareler). Uygun bölen yoksa eski yol: 30 fps, × ⌈1/hız⌉ (ör. 50 fps 0,5x: saniyede 50 karenin 20'si atılır).
--kirp/--olcek: görünen yöndeki piksellerle (döndürmeli klipte `medya incele` → gorunen), HDR ton eşlemesinden sonra,
ara kare üretiminden önce (doğal yolda da). Yöntem sırası, RIFE disk tahmini ve UHD kipi hazır kareye bakar: dikey
1080x1920 çıktıda RIFE önce. Kırpma klibe pişer.
Çıktı varsayılan olarak ProRes 422 HQ .mov (NLE devri için ara dosya; görsel kayıpsız). HyperFrames'e girecek klipte
--cikti x.mp4 (H.264 CRF 12): HyperFrames ProRes'i her kipte 16 bit PNG kareye açar (4096x2160'ta ~33 MB/kare).
Ses yazılmaz (ağır çekim sessizdir).
"""
from __future__ import annotations

import json
import math
import shutil
import tempfile
from pathlib import Path

from ..ortak import ARAC, MedyaHatasi, apple_calistir, bilgi, calistir, ffmpeg, probe, video_akisi
from .incele import incele_dosya

APPLE = ARAC / "medya-apple"
RIFE = ARAC / "rife" / "rife-ncnn-vulkan"
RIFE_MODEL = ARAC / "rife" / "rife-v4.6"


def _giris_matrisi(v: dict) -> str:
    """SDR kaynağın renk matrisi (scale in_color_matrix). Etiketliyse etiket okunur ('auto'); etiketsizse HyperFrames'in
    1x çekimlere uyguladığı tahmin (chromeGuessForUntaggedMatrix, 0.8.140 chunk-TPECLKPA.js:11413): ≥ 720 satır ve
    vp9/av1 değilse BT.709, değilse BT.601. Ağır çekim aynı kameranın 1x çekimleriyle aynı renkte görünür."""
    m = v["renk"]["matris"]
    if m and m != "unknown":
        return "auto"
    return "bt709" if v["yukseklik"] >= 720 and v["codec"] not in ("vp9", "av1") else "bt601"


def _kirp_olcek(kirp: str | None, olcek: str | None, gorunen: str, giris: str = "auto") -> list[str]:
    """--kirp x,y,gen,yük ve --olcek GxY → süzgeçler. Değerler görünen yönde: ffmpeg kareyi süzgeçten önce döndürür
    (ölçüldü 2026-10-08, 90° döndürmeli klip). Çift sayı şartı 4:2:0 renk örneklemesi içindir. giris: _giris_matrisi."""
    gw, gh = (int(n) for n in gorunen.split("x"))
    vf, kg, ky = [], gw, gh
    if kirp:
        try:
            x, y, kg, ky = (int(n) for n in kirp.split(","))
        except ValueError:
            raise MedyaHatasi(f"--kirp x,y,genişlik,yükseklik biçiminde tam sayılar olmalı: {kirp!r}") from None
        if min(x, y) < 0 or min(kg, ky) <= 0 or x + kg > gw or y + ky > gh:
            raise MedyaHatasi(f"--kirp {kirp} görünen karenin ({gorunen}) dışına taşıyor")
        if any(n % 2 for n in (x, y, kg, ky)):
            raise MedyaHatasi(f"--kirp {kirp}: değerler çift sayı olmalı (4:2:0 renk örneklemesi)")
        vf.append(f"crop={kg}:{ky}:{x}:{y}:exact=1")
    if olcek:
        try:
            ow, oh = (int(n) for n in olcek.lower().split("x"))
        except ValueError:
            raise MedyaHatasi(f"--olcek GxY biçiminde olmalı (ör. 1080x1920): {olcek!r}") from None
        if min(ow, oh) <= 0 or ow % 2 or oh % 2:
            raise MedyaHatasi(f"--olcek {olcek}: genişlik ve yükseklik pozitif çift sayı olmalı")
        if abs(kg * oh / (ky * ow) - 1) > 0.01:
            raise MedyaHatasi(f"--olcek {olcek} en-boy oranı {kg}x{ky} karesinden %1'den çok farklı: görüntü basılır. "
                              "Önce --kirp ile aynı orana kırp")
        # Renk ayarı ve etiketi şart: HDR yolunda ölçek ton eşlenmiş RGB'yi YUV'ye çevirir; ayarsız yanlış matris/aralık
        # kullanır, setparams'sız doğal yol ProRes'inde matris "unknown" kalır. SDR'de (YUV girdi) giriş matrisi açık
        # verilir: 'auto' etiketsiz kareyi BT.601 okuyup BT.709'a çevirir, renk kayar. Etiketli bt709'da piksel değişmez,
        # bt601 BT.709'a çevrilir (ölçümler: sistem/devam/yavas-cekim/2026-10-08-kirp/olc_renk.json).
        vf.append(f"scale={ow}:{oh}:flags=lanczos:in_color_matrix={giris}:out_color_matrix=bt709:out_range=tv,"
                  "setparams=colorspace=bt709:range=tv")
    return vf


def _hazir_fps(gercek: float, taban: float, gereken: float) -> tuple[float, int]:
    """Ara kare yolunda hazırlık kare hızı ve kat. Gerçek kareleri atmamak için kaynağın tam böleni olan en yüksek hız
    (≥ taban), öyle ki kat = gereken / hız tam sayı (2–8) olsun. Yoksa eski yol: taban fps, kat = ⌈gereken / taban⌉."""
    kaynak, m = round(gercek), 1
    while kaynak / m >= taban - 1e-6:
        kat = gereken * m / kaynak
        if abs(kat - round(kat)) < 1e-6 and 2 <= round(kat) <= 8:
            return kaynak / m, round(kat)
        m += 1
    return taban, max(2, min(8, math.ceil(gereken / taban - 1e-9)))


def _hazirla(girdi: str, hedef: Path, fps: float, bas: float | None, sure: float | None, sdr: bool,
             kirp_vf: list[str]) -> Path:
    """Kesit + sabit kare hızı (+ gerekirse HDR→SDR, kırpma/ölçek) — kayıpsıza yakın ara dosya."""
    vf = []
    if sdr:
        vf.append("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,"
                  "zscale=t=bt709:m=bt709:r=tv")
    vf += [*kirp_vf, f"fps={fps:g}", "setsar=1", "format=yuv420p"]
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


def _rife(hazir: Path, ara: Path, kat: int, hfps: float) -> dict:
    """PNG kareler → RIFE → PNG kareler → ProRes (hazır dosyanın fps'i, kat kat uzun). Diskte yer yoksa denemez."""
    v = next(x for x in probe(hazir)["streams"] if x.get("codec_type") == "video")
    w, h = int(v["width"]), int(v["height"])
    K = round(float(probe(hazir)["format"]["duration"]) * hfps)
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
        # ara.mov sözleşmesi (Apple ve minterpolate ile aynı): hazır dosyanın fps'i, kat kat uzun = 1/kat hızında
        calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-framerate", f"{hfps:g}", "-i",
                  str(cik / "%08d.png"), "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv422p10le",
                  "-c:v", "prores_ks", "-profile:v", "3", "-colorspace", "bt709", "-color_primaries", "bt709",
                  "-color_trc", "bt709", "-color_range", "tv", str(ara)], hata_mesaji="kodlama başarısız")
    return {"kare": K * kat, "model": RIFE_MODEL.name}


def yavaslat(girdi: str, cikti: str, hiz: float, *, fps: float | None = None, bas: float | None = None,
             sure: float | None = None, yontem: str | None = None, kirp: str | None = None,
             olcek: str | None = None) -> dict:
    if not 0.05 <= hiz < 1:
        raise MedyaHatasi("--hiz 0,05 ile 1 arasında olmalı (0,5 = yarı hız)")
    r = incele_dosya(girdi)
    v = r.get("video") or {}
    if not v:
        raise MedyaHatasi("video akışı yok")
    kirp_vf = _kirp_olcek(kirp, olcek, v["gorunen"], _giris_matrisi(v))
    gercek = v["kare_olcumu"].get("gercek_fps") or v["fps_nominal"]
    taban = fps or min(30.0, round(gercek))                     # çıktının oynatma kare hızı
    gereken = taban / hiz                                        # doğal ağır çekim için gereken kaynak fps
    sonuc = {"girdi": girdi, "cikti": cikti, "hiz": hiz, "fps": taban, "kaynak_gercek_fps": round(gercek, 2)}
    if (yontem in (None, "dogal")) and gercek >= gereken * 0.98:
        vf = ",".join([*kirp_vf, f"fps={gereken:g},setpts=PTS/{hiz:g},fps={taban:g},setsar=1"])
        if v.get("hdr"):
            vf = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,"
                  "zscale=t=bt709:m=bt709:r=tv," + vf)
        _kodla_mov(vf, girdi, cikti, taban, bas, sure)
        sonuc["yontem"] = "dogal"
        return sonuc
    hfps, kat = _hazir_fps(gercek, taban, gereken)
    with tempfile.TemporaryDirectory() as g:
        hazir = _hazirla(girdi, Path(g) / "hazir.mp4", hfps, bas, sure, bool(v.get("hdr")), kirp_vf)
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
                    n = float(probe(hazir)["format"]["duration"]) * hfps * kat         # üretilecek kare
                    s = apple_calistir([str(APPLE), "yavaslat", str(hazir), str(ara), str(kat), "--kodek", "prores"],
                                       zaman_asimi=180 + 2 * n, hata_mesaji="Apple ara kare üretimi")
                    sonuc["apple"] = json.loads(s.stdout.decode().strip().splitlines()[-1])
                elif kullanilan == "rife":
                    sonuc["rife"] = _rife(hazir, ara, kat, hfps)
                break
            except MedyaHatasi as e:
                sonuc.setdefault("dusulen", []).append(f"{kullanilan}: {str(e)[:300]}")
                bilgi(f"⚠ {kullanilan} ara kare üretimi başarısız, sıradakine düşülüyor: {str(e)[:200]}")
        if kullanilan == "ffmpeg":
            _kodla_mov(f"minterpolate=fps={hfps * kat:g}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
                       f"setpts=PTS*{kat},fps={hfps:g}", str(hazir), str(ara), hfps)
        # ara.mov hazır fps'te, kat kat uzun; istenen hıza (hiz) ve taban fps'e getir. hfps·kat·hiz = taban ise her
        # ara kare tam bir çıktı karesi (60 fps × 2 → 0,25x); eski yolda hiz·kat > 1 ise kare düşürerek hızlandırır.
        hizlan = hiz * kat
        if abs(hizlan - 1) < 1e-6 and cikti.lower().endswith(".mov"):
            Path(ara).replace(cikti)
        else:
            _kodla_mov(f"setpts=PTS/{hizlan:g},fps={taban:g}", str(ara), cikti, taban)
        sonuc["yontem"] = kullanilan
        sonuc["kat"] = kat
        sonuc["hazir_fps"] = hfps
    sonuc["sure"] = float(probe(cikti)["format"]["duration"])
    return sonuc


def calistir_(args) -> int:
    g = Path(args.girdi)
    cikti = args.cikti or str(g.with_name(g.stem + f"-yavas{args.hiz:g}".replace(".", "_") + ".mov"))
    r = yavaslat(args.girdi, cikti, args.hiz, fps=args.fps, bas=args.bas, sure=args.sure, yontem=args.yontem,
                 kirp=args.kirp, olcek=args.olcek)
    v = video_akisi(probe(cikti))
    print(f"{r['yontem']}: hız {r['hiz']:g}x, {r['fps']:g} fps, {v['width']}x{v['height']}, kaynak gerçek "
          f"{r['kaynak_gercek_fps']} fps → {cikti}" + (f" ({r['sure']:.2f} sn)" if "sure" in r else ""))
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
    p.add_argument("--kirp", help="x,y,genişlik,yükseklik: ara kareden önce kırp (görünen yönde, çift sayılar), "
                                  "ör. 4K'dan dikey 1312,0,1216,2160")
    p.add_argument("--olcek", help="GxY: kırpımdan sonra bu boyuta ölçekle (çift; en-boy kırpımla aynı), ör. 1080x1920")
    p.add_argument("--yontem", choices=["dogal", "apple", "rife", "ffmpeg"],
                   help="önce bunu dene (varsayılan: dogal → hazır kare ≤2000 px'te rife, üstünde apple → diğeri → ffmpeg)")
    p.add_argument("--cikti", help="varsayılan <ad>-yavas<hız>.mov (ProRes 422 HQ, NLE devri); HyperFrames'e girecekse "
                                   ".mp4 (H.264 CRF 12; ProRes'i HyperFrames 16 bit PNG'ye açar)")
    p.set_defaults(islev=calistir_)
