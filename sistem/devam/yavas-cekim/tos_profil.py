import json, subprocess, time
import numpy as np
SRC = "data/tears_of_steel_1080p.mov"
W, H = 192, 80
t0 = time.time()
p = subprocess.run(["/Users/onurkaya/Projects/video/arac/ffmpeg", "-nostdin", "-v", "error", "-hwaccel", "videotoolbox", "-i", SRC,
                    "-an", "-vf", f"scale={W}:{H}:flags=area,format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True)
f = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W).astype(np.float32)
print("kare", len(f), "sn", round(time.time() - t0, 1))
mad1 = np.abs(f[1:] - f[:-1]).mean(axis=(1, 2))
mad2 = np.abs(f[2:] - f[:-2]).mean(axis=(1, 2))
med = np.median(mad1)
# kesim: komşularına göre sıçrama
kesim = [i for i in range(2, len(mad1) - 2) if mad1[i] > 12 and mad1[i] > 3 * max(np.median(mad1[i-2:i]), np.median(mad1[i+1:i+3]), 1)]
kesim = np.array(kesim)
print("kesim", len(kesim), "medyan MAD1", round(float(med), 2))
L = 96
rows = []
for s in range(0, min(len(f) - L, int(620 * 24)), 6):       # jenerik dışı
    if len(kesim) and ((kesim >= s - 2) & (kesim < s + L + 2)).any():
        continue
    seg = mad1[s:s + L - 1]
    if seg.max() > 25 or f[s:s+L].mean() < 20:              # flaş / karanlık sahne değil
        continue
    rows.append((float(mad2[s:s + L - 2].mean()), float(seg.mean()), s))
m = np.array([r[0] for r in rows])
print("pencere", len(rows), "MAD2 p50/p90/max", np.percentile(m, [50, 90, 100]).round(2))
rows.sort(reverse=True)
last = []
for v2, v1, s in rows:
    if all(abs(s - x) > 240 for x in last):
        print(f"  {s/24:7.2f}-{(s+L)/24:7.2f} sn MAD2 {v2:5.2f} MAD1 {v1:5.2f} parlaklık {f[s:s+L].mean():5.1f}"); last.append(s)
    if len(last) >= 10: break
json.dump({"mad1": mad1.round(3).tolist(), "kesim": kesim.tolist()}, open("data/tos_profil.json", "w"))
