"""Deney: -ss X (iki kare zamanının ortası) ile çözücünün ilk karesi tam istenen kare mi? Kare kodlu medya + gerçek HEVC."""
import subprocess, sys, json
from fractions import Fraction
from pathlib import Path
import numpy as np
K = Path("/Users/onurkaya/Projects/video")
sys.path.insert(0, str(K / "testler"))
from nle_sinama import kod_oku
FF = str(K / "arac" / "ffmpeg")

def pts_listesi(yol):
    r = subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(yol), "-map", "0:v:0", "-c", "copy", "-f", "framemd5", "-"],
                       capture_output=True, text=True, check=True).stdout.splitlines()
    tb = next(l for l in r if l.startswith("#tb 0:")).split(":")[1].strip()
    tb = Fraction(tb)
    pts = sorted(int(l.split(",")[2]) for l in r if l and not l.startswith("#"))
    return tb, pts

def coz(yol, X, k, w, h):
    kom = [FF, "-nostdin", "-v", "error"] + (["-ss", f"{float(X):.6f}"] if X is not None else []) + [
        "-i", str(yol), "-map", "0:v:0", "-frames:v", str(k), "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    b = subprocess.run(kom, capture_output=True, check=True).stdout
    n = len(b) // (w * h * 3)
    return [np.frombuffer(b[i*w*h*3:(i+1)*w*h*3], np.uint8).reshape(h, w, 3) for i in range(n)]

P = K / "projeler/2026-10-08-nle-sinama/kaynak"
hata = 0
for harf in "ABCD":
    tb, pts = pts_listesi(P / f"{harf}.mov")
    for i0 in (0, 1, 7, 15, 30, 31, 47, 59, 61):
        if i0 >= len(pts): continue
        X = None if i0 == 0 else (Fraction(pts[i0 - 1] + pts[i0], 2) * tb)
        kare = coz(P / f"{harf}.mov", X, 5, 1280, 720)
        kod = [kod_oku(k) for k in kare]
        bek = [(harf, i0 + j) for j in range(5)]
        if kod != bek[:len(kod)] or len(kod) != 5:
            hata += 1
            print("UYUMSUZ", harf, i0, kod)
    print(harf, "tb", tb, "kare", len(pts), "ilk pts", pts[:3])
print("kare kodlu medya uyumsuz:", hata)
