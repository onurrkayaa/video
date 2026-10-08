"""O3 ölçümü (720p sentetik): eski/yeni 60 fps yolu ve kırp-önce / ara-kare-önce. Kareler ham çözülür (psnr süzgeci yok)."""
import importlib.util
import json
import statistics as st
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

KOK = Path("/Users/onurkaya/Projects/video")
sys.path.insert(0, str(KOK))
VERI = KOK / "testler" / "veri"
from medya.komutlar.yavaslat import yavaslat as yeni  # noqa: E402
from medya.ortak import ffmpeg  # noqa: E402

spec = importlib.util.spec_from_file_location("medya.komutlar.yavaslat_eski", Path(__file__).with_name("yavaslat_eski.py"))
eski_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eski_mod)
eski = eski_mod.yavaslat


def kareler(yol, vf, w, h):
    r = subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-i", str(yol), "-vf", f"{vf}format=gray",
                        "-fps_mode", "passthrough", "-f", "rawvideo", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, h, w).astype(float)


def psnr(a, b):
    return float(10 * np.log10(255 ** 2 / max(np.mean((a - b) ** 2), 1e-9)))


sonuc = {}
with tempfile.TemporaryDirectory() as g:
    g = Path(g)
    # (1) 60 fps kaynak, 0,25x, ilk 1 sn: gerçek 120 fps karelerine karşı
    ref = kareler(VERI / "hareket120.mp4", "", 1280, 720)
    for ad, f in (("eski", eski), ("yeni", yeni)):
        t = time.time()
        r = f(str(VERI / "hareket60.mp4"), str(g / f"{ad}.mov"), 0.25, sure=1.0)
        s = time.time() - t
        y = kareler(g / f"{ad}.mov", "", 1280, 720)
        n = min(len(y), len(ref))
        p = [psnr(y[i], ref[i]) for i in range(n)]
        cift = [p[i] for i in range(0, n, 2)]       # yeni yolda gerçek 60 fps kareleri
        tek = [p[i] for i in range(1, n, 2)]
        dort = [p[i] for i in range(0, n, 4)]       # eski yolda gerçek 30 fps kareleri
        sonuc[f"60fps_0.25x_{ad}"] = dict(yontem=r["yontem"], kat=r.get("kat"), hazir_fps=r.get("hazir_fps"),
                                          kare=len(y), n=n, sure_sn=round(s, 1),
                                          cift_ort=round(st.mean(cift), 2), cift_min=round(min(cift), 2),
                                          tek_ort=round(st.mean(tek), 2), tek_min=round(min(tek), 2),
                                          dort_min=round(min(dort), 2), hepsi_ort=round(st.mean(p), 2))
    # (2) kırp-önce / ara-kare-önce (RIFE ikisinde de): 30 fps → ×2, gerçek 60 fps karelerinin aynı kırpımına karşı
    K = "crop=400:720:440:0,"
    ref60 = kareler(VERI / "hareket60.mp4", K, 400, 720)
    a = yeni(str(VERI / "hareket30.mp4"), str(g / "a.mov"), 0.5, yontem="rife", kirp="440,0,400,720")
    b = yeni(str(VERI / "hareket30.mp4"), str(g / "b.mov"), 0.5, yontem="rife")
    ya, yb = kareler(g / "a.mov", "", 400, 720), kareler(g / "b.mov", K, 400, 720)
    n = min(len(ya), len(yb), len(ref60))
    ara = lambda y: [psnr(y[i], ref60[i]) for i in range(1, n, 2)]
    ozg = lambda y: [psnr(y[i], ref60[i]) for i in range(0, n, 2)]
    kopya = [psnr(ref60[i - 1], ref60[i]) for i in range(1, n, 2)]
    pa, pb = ara(ya), ara(yb)
    k5 = max(1, round(len(pa) * 0.05))
    sonuc["kirp_once_vs_ara_kare_once_720p"] = dict(
        yontem=[a["yontem"], b["yontem"]], n=n,
        kirp_once_ara_ort=round(st.mean(pa), 2), ara_once_ara_ort=round(st.mean(pb), 2),
        kirp_once_kotu5=round(float(np.mean(sorted(pa)[:k5])), 2), ara_once_kotu5=round(float(np.mean(sorted(pb)[:k5])), 2),
        kopya_ort=round(st.mean(kopya), 2), kirp_once_ozgun_min=round(min(ozg(ya)), 2),
        ara_once_ozgun_min=round(min(ozg(yb)), 2), fark_ort=round(st.mean(pa) - st.mean(pb), 2),
        kare_kare_fark_min=round(min(x - y for x, y in zip(pa, pb)), 2))
print(json.dumps(sonuc, ensure_ascii=False, indent=1))
(Path(__file__).with_name("olc_720.json")).write_text(json.dumps(sonuc, ensure_ascii=False, indent=1))
