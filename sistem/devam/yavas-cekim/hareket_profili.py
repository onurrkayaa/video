"""IMG_4021.MOV hareket profili: düşük çözünürlükte gri kareler; ardışık kare MAD + faz korelasyonu kayması."""
import json, subprocess, sys, time
import numpy as np
SRC = "/Users/onurkaya/Projects/video/projeler/2026-10-05-deniz-kenari-deneme/kaynak/IMG_4021.MOV"
W, H = 256, 135
t0 = time.time()
p = subprocess.run(["/Users/onurkaya/Projects/video/arac/ffmpeg", "-nostdin", "-v", "error", "-hwaccel", "videotoolbox", "-i", SRC,
                    "-vf", f"scale={W}:{H}:flags=area,format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True)
f = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W).astype(np.float32)
print("kare", len(f), "çözme sn", round(time.time() - t0, 1))
mad = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
win = np.hanning(H)[:, None] * np.hanning(W)[None, :]
def kayma(a, b):
    A = np.fft.fft2((a - a.mean()) * win); B = np.fft.fft2((b - b.mean()) * win)
    R = A * np.conj(B); R /= np.abs(R) + 1e-9
    r = np.fft.ifft2(R).real
    y, x = np.unravel_index(np.argmax(r), r.shape)
    if y > H // 2: y -= H
    if x > W // 2: x -= W
    return x, y
# 4 karelik aralıkla (15 fps eşdeğeri) kayma, 1024 genişliğe ölçekli
sh = []
for i in range(0, len(f) - 4, 4):
    x, y = kayma(f[i + 4], f[i])
    sh.append((i, x * 4, y * 4))
sh = np.array(sh)
mag = np.hypot(sh[:, 1], sh[:, 2])
print("MAD/kare (0-255) yüzdelikler p10/p50/p90/max:", np.percentile(mad, [10, 50, 90, 100]).round(2))
print("4 karelik kayma (1024px ölçeğinde) p10/p50/p90/max:", np.percentile(mag, [10, 50, 90, 100]).round(1))
# 4 sn (240 kare) pencereler: ortalama MAD
L = 240
cs = np.concatenate([[0], np.cumsum(mad)])
ort = [(s, (cs[s + L - 1] - cs[s]) / (L - 1)) for s in range(0, len(f) - L + 1, 30)]
for s, m in ort:
    k = (sh[:, 0] >= s) & (sh[:, 0] < s + L)
    print(f"  pencere {s/60:5.1f}-{(s+L)/60:5.1f} sn  MAD {m:5.2f}  kayma medyan {np.median(mag[k]):5.1f} px  max {mag[k].max():5.1f}")
json.dump({"mad": mad.round(3).tolist(), "kayma4": sh.tolist()}, open("data/hareket_profili.json", "w"))
