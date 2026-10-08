"""Deney: B kareli, uzun GOP'lu gerçek HEVC'de (yalnız sayısal: kare özetleri) ortadan -ss ile ilk kare doğru mu."""
import subprocess, sys
from fractions import Fraction
from pathlib import Path
K = Path("/Users/onurkaya/Projects/video")
FF = str(K / "arac" / "ffmpeg")
Y = K / "projeler/2026-10-05-deniz-kenari-deneme/kaynak/IMG_4021.MOV"
VF = "scale=256:136:flags=area,format=rgb24"

def satirlar(kom):
    return [l for l in subprocess.run(kom, capture_output=True, text=True, check=True).stdout.splitlines() if l and not l.startswith("#")]

r = subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(Y), "-map", "0:v:0", "-c", "copy", "-f", "framemd5", "-"],
                   capture_output=True, text=True, check=True).stdout.splitlines()
tb = Fraction(next(l for l in r if l.startswith("#tb 0:")).split(":")[1].strip())
pts = sorted(int(l.split(",")[2]) for l in r if l and not l.startswith("#"))
anahtar = sorted(int(l.split(",")[0]) for l in subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts,flags", "-of", "csv=p=0", str(Y)], capture_output=True, text=True).stdout.splitlines() if "K" in l.split(",")[1])
tam = satirlar([FF, "-nostdin", "-v", "error", "-i", str(Y), "-map", "0:v:0", "-vf", VF, "-fps_mode", "passthrough", "-f", "framemd5", "-"])
ozet = [l.split(",")[-1].strip() for l in tam]
print("kare", len(pts), "çözülen", len(ozet), "anahtar kare pts", anahtar)
ki = [pts.index(a) for a in anahtar]
adaylar = sorted(set([1, 2, 3, 100] + [i + d for i in ki for d in (-2, -1, 0, 1, 2, 3)]))
hata = 0
for i0 in adaylar:
    if not 0 < i0 < len(pts) - 6: continue
    X = Fraction(pts[i0 - 1] + pts[i0], 2) * tb
    s = satirlar([FF, "-nostdin", "-v", "error", "-ss", f"{float(X):.6f}", "-i", str(Y), "-map", "0:v:0", "-vf", VF,
                  "-frames:v", "5", "-fps_mode", "passthrough", "-f", "framemd5", "-"])
    o = [l.split(",")[-1].strip() for l in s]
    if o != ozet[i0:i0 + 5]:
        hata += 1
        print("UYUMSUZ", i0, [ozet.index(x) if x in ozet else None for x in o])
print("denenen", len([i for i in adaylar if 0 < i < len(pts) - 6]), "uyumsuz", hata)
