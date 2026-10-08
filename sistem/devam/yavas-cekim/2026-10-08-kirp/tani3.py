"""Sentetik −4,1 dB'in nedeni: aşırı ayrıntılı dokunun ölçeklemede örtüşmesi mi? Aynı hareket, bant sınırlı doku
(gblur σ=1,5): kırp+ölçek-önce (1080x1920) / tam 4K ara kare sonra kırp+ölçek, ikisi de RIFE, gerçek 60 fps karelerine karşı."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

KOK = Path("/Users/onurkaya/Projects/video")
sys.path.insert(0, str(KOK))
from medya.komutlar.yavaslat import yavaslat  # noqa: E402
from medya.ortak import ffmpeg  # noqa: E402

BURA = Path(__file__).parent
FF = ffmpeg()
VF = "crop=1216:2160:1312:0:exact=1,scale=1080:1920:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv420p,"
sonuc = {}


def ff(*a):
    subprocess.run([FF, "-nostdin", "-v", "error", "-y", *a], check=True)


def gri(yol, vf="", n=60):
    b = subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(yol), "-frames:v", str(n), "-vf", f"{vf}format=gray",
                        "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, 1920, 1080)


def psnr(a, b):
    d = a.astype(np.float32) - b.astype(np.float32)
    return float(10 * np.log10(255 ** 2 / max(float(np.mean(d * d)), 1e-9)))


with tempfile.TemporaryDirectory() as t:
    t = Path(t)
    ff("-f", "lavfi", "-i", "mandelbrot=s=4480x2560:r=1", "-frames:v", "1", "-vf", "gblur=sigma=1.5", str(t / "doku.png"))
    hareket = ("crop=3840:2160:x='100+360*t':y='60+120*t',drawbox=x='600+480*t':y='900+120*t':w=400:h=400:"
               "color=orange@1:t=fill,drawbox=x='3000-240*t':y='300+60*t':w=240:h=600:color=0x2040ff@1:t=fill,format=yuv420p")
    renk = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
    ff("-loop", "1", "-framerate", "60", "-t", "1", "-i", str(t / "doku.png"), "-vf", hareket, "-r", "60",
       "-c:v", "libx264", "-crf", "0", "-preset", "veryfast", *renk, str(t / "k60.mp4"))
    ff("-i", str(t / "k60.mp4"), "-vf", "select='not(mod(n\\,2))',setpts=N/30/TB", "-r", "30", "-c:v", "libx264",
       "-crf", "0", "-preset", "veryfast", *renk, str(t / "k30.mp4"))
    a = yavaslat(str(t / "k30.mp4"), str(t / "a.mov"), 0.5, yontem="rife", kirp="1312,0,1216,2160", olcek="1080x1920")
    b = yavaslat(str(t / "k30.mp4"), str(t / "b.mov"), 0.5, yontem="rife")
    g = gri(t / "k60.mp4", VF)
    ya, yb = gri(t / "a.mov"), gri(t / "b.mov", VF)
    ara, ozg = range(1, 58, 2), range(0, 59, 2)
    pa, pb = [psnr(ya[i], g[i]) for i in ara], [psnr(yb[i], g[i]) for i in ara]
    oa, ob = [psnr(ya[i], g[i]) for i in ozg], [psnr(yb[i], g[i]) for i in ozg]
    kopya = [psnr(g[i - 1], g[i]) for i in ara]
    sonuc["bant_sinirli_doku_1080x1920"] = dict(
        yontem=[a["yontem"], b["yontem"]], kirp_olcek_once_ara=round(float(np.mean(pa)), 2),
        ara_kare_once_ara=round(float(np.mean(pb)), 2), fark=round(float(np.mean(pa) - np.mean(pb)), 2),
        kirp_olcek_once_ozgun=round(float(np.mean(oa)), 2), ara_kare_once_ozgun=round(float(np.mean(ob)), 2),
        kopya=round(float(np.mean(kopya)), 2))
print(json.dumps(sonuc, ensure_ascii=False, indent=1))
(BURA / "tani3.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1))
