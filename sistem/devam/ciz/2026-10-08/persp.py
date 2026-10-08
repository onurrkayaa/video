"""Deney: perspective süzgecinin koordinat kuralı (piksel dizini mi, merkez mi) ve eval=frame'de 'in' sayacı."""
import subprocess
import numpy as np
FF = "/Users/onurkaya/Projects/video/arac/ffmpeg"
W, H = 128, 72
def blob(cx, cy, s=2.0):
    y, x = np.mgrid[0:H, 0:W]
    return (16 + 200 * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * s * s))).astype(np.float64)
def merkez(im):
    g = np.clip(im.astype(float) - 16, 0, None)
    y, x = np.mgrid[0:im.shape[0], 0:im.shape[1]]
    return (g * x).sum() / g.sum(), (g * y).sum() / g.sum()
def calis(kareler, vf):
    girdi = b"".join(np.concatenate([np.rint(k).astype(np.uint8).ravel(), np.full(W * H // 2, 128, np.uint8)]).tobytes() for k in kareler)
    r = subprocess.run([FF, "-nostdin", "-v", "error", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                        "-vf", vf, "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], input=girdi, capture_output=True, check=True)
    n = W * H * 3 // 2
    return [np.frombuffer(r.stdout[i * n:i * n + W * H], np.uint8).reshape(H, W) for i in range(len(r.stdout) // n)]
k = blob(40.0, 20.0)
print("girdi merkez", merkez(k))
# 2x yakınlaştırma: kaynak dikdörtgen (a,b)-(a+64,b+36) tam kareye
a, b = 20.0, 10.0
for interp in ("linear", "cubic"):
    o = calis([k], f"perspective=x0={a}:y0={b}:x1={a+64}:y1={b}:x2={a}:y2={b+36}:x3={a+64}:y3={b+36}:interpolation={interp}:sense=source")
    print(interp, "çıktı merkez", merkez(o[0]), "dizin kuralı bekler", ((40 - a) * 2, (20 - b) * 2), "merkez kuralı bekler", ((40.5 - a) * 2 - 0.5, (20.5 - b) * 2 - 0.5))
# in sayacı: x0 = in (her karede 1 px kayma) — ilk karede kayma kaç?
o = calis([k] * 4, "perspective=x0=in:y0=0:x1=in+128:y1=0:x2=in:y2=72:x3=in+128:y3=72:interpolation=cubic:sense=source:eval=frame")
print("eval=frame 'in' ile kaymalar:", [round(40 - merkez(x)[0], 3) for x in o])
o = calis([k] * 4, "perspective=x0=on:y0=0:x1=on+128:y1=0:x2=on:y2=72:x3=on+128:y3=72:interpolation=cubic:sense=source:eval=frame")
print("eval=frame 'on' ile kaymalar:", [round(40 - merkez(x)[0], 3) for x in o])
