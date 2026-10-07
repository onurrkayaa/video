import json, subprocess, time
import numpy as np
SRC = "data/bbb_sunflower_1080p_60fps_normal.mp4"
W, H = 192, 108
t0 = time.time()
p = subprocess.Popen(["/Users/onurkaya/Projects/video/arac/ffmpeg", "-nostdin", "-v", "error", "-hwaccel", "videotoolbox", "-i", SRC,
                      "-an", "-vf", f"scale={W}:{H}:flags=area,format=gray", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
buf = p.stdout.read()
p.wait()
f = np.frombuffer(buf, np.uint8).reshape(-1, H, W).astype(np.float32)
print("kare", len(f), "sn", round(time.time() - t0, 1))
mad1 = np.abs(f[1:] - f[:-1]).mean(axis=(1, 2))
mad4 = np.abs(f[4:] - f[:-4]).mean(axis=(1, 2))
kesim = np.where(mad1 > np.maximum(25, 6 * np.median(mad1)))[0]
print("kesim sayısı (MAD1 sıçraması)", len(kesim))
L = 240
iyi = []
for s in range(0, len(f) - L, 15):
    if ((kesim >= s - 2) & (kesim < s + L + 2)).any():
        continue
    seg1 = mad1[s:s + L - 1]; seg4 = mad4[s:s + L - 4]
    if seg1.max() > 20:        # olası yumuşak geçiş/flaş
        continue
    iyi.append((float(seg4.mean()), float(seg1.mean()), s))
iyi.sort(reverse=True)
for m4, m1, s in iyi[:12]:
    print(f"  {s/60:7.2f}-{(s+L)/60:7.2f} sn  MAD4 {m4:5.2f}  MAD1 {m1:5.2f}")
print("medyan pencere MAD4", np.median([x[0] for x in iyi]).round(2))
json.dump({"mad1": mad1.round(3).tolist(), "kesim": kesim.tolist(), "iyi": iyi[:40]}, open("data/bbb_profil.json", "w"))
