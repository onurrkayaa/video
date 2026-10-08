"""HyperFrames 0.8.140 çizimde video kliplerini kareye açar (extractVideoFramesRange, chunk-TPECLKPA.js:11468):
ProRes her kipte PNG (resolveFrameFormat :11844), H.264 taslakta JPEG (-q:v 2), --video-frame-format png'de PNG
(-compression_level 1). Burada aynı ffmpeg ayarlarıyla, diske yazmadan (boru) kare başına bayt ölçülür.
Klipler: deneme A ağır çekimi (IMG_4021 --bas 14.25 --sure 2.9 --hiz 0.5, doğal yol) farklı çıktı biçimlerinde."""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

KOK = Path("/Users/onurkaya/Projects/video")
sys.path.insert(0, str(KOK))
from medya.komutlar.yavaslat import yavaslat  # noqa: E402
from medya.ortak import ffmpeg, probe, video_akisi  # noqa: E402

BURA = Path(__file__).parent
FF = ffmpeg()
DEN = KOK / "projeler/2026-10-05-deniz-kenari-deneme/kaynak/IMG_4021.MOV"
SDR = "setparams=color_primaries=bt709:color_trc=iec61966-2-1"
JPG = "scale=flags=neighbor,format=gbrp,scale=out_color_matrix=bt601:out_range=pc:flags=neighbor,format=yuv420p"


def cikar_bayt(klip, bicim):
    v = video_akisi(probe(klip))
    sure = float(probe(klip)["format"]["duration"])
    k = [FF, "-nostdin", "-v", "error"]
    if v["codec_name"] in ("prores", "vp8", "vp9"):
        k += ["-c:v", v["codec_name"]]
    k += ["-noaccurate_seek", "-ss", "0", "-i", str(klip), "-t", str(sure), "-vf",
          ",".join(["settb=intb/2", "setpts=PTS-lte(TB\\,0.001)", "fps=30:start_time=0:round=up", SDR]
                   + ([JPG] if bicim == "jpg" else []))]
    k += ["-q:v", "2" if bicim == "jpg" else "0"] + (["-compression_level", "1"] if bicim == "png" else [])
    k += ["-f", "image2pipe", "-c:v", "png" if bicim == "png" else "mjpeg", "-"]
    p = subprocess.Popen(k, stdout=subprocess.PIPE)
    toplam = 0
    while True:
        b = p.stdout.read(1 << 22)
        if not b:
            break
        toplam += len(b)
    p.wait()
    return toplam, round(sure * 30)


sonuc = {}
with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    for ad, kw, uzanti in (("ProRes 4096x2160 (bugün)", {}, ".mov"),
                           ("ProRes 1216x2160 (yalnız kırpma)", {"kirp": "1440,0,1216,2160"}, ".mov"),
                           ("ProRes 1080x1920 (kırp+ölçek)", {"kirp": "1440,0,1216,2160", "olcek": "1080x1920"}, ".mov"),
                           ("H.264 CRF 12 1216x2160 (yalnız kırpma)", {"kirp": "1440,0,1216,2160"}, ".mp4"),
                           ("H.264 CRF 12 1080x1920 (kırp+ölçek)", {"kirp": "1440,0,1216,2160", "olcek": "1080x1920"}, ".mp4")):
        klip = t / f"k{len(sonuc)}{uzanti}"
        t0 = time.time()
        r = yavaslat(str(DEN), str(klip), 0.5, bas=14.25, sure=2.9, **kw)
        s = round(time.time() - t0, 1)
        kayit = dict(yontem=r["yontem"], uretim_sn=s, dosya_mb=round(klip.stat().st_size / 1e6, 1))
        for bicim in (("png",) if uzanti == ".mov" else ("png", "jpg")):
            bayt, kare = cikar_bayt(klip, bicim)
            kayit[f"{bicim}_mb_kare"] = round(bayt / kare / 1e6, 3)
            kayit[f"{bicim}_237_kare_gb"] = round(bayt / kare * 237 / 1e9, 3)   # denemede zaman çizelgesindeki ağır çekim
            kayit["kare"] = kare
        sonuc[ad] = kayit
        print(ad, kayit, flush=True)
        (BURA / "olc_hf.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1))
        klip.unlink()
