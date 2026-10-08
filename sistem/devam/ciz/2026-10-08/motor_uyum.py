"""ciz ↔ HyperFrames aynı plandan aynı geometriyi mi çiziyor? Kare başına Y-PSNR ve faz ilintisiyle alt piksel kayma
(kare açılmaz; yalnız sayılar). Kayma ≈ 0 ise kadraj/çapa/ölçek kuralı iki motorda aynı."""
import subprocess, sys
import numpy as np
FF = "/Users/onurkaya/Projects/video/arac/ffmpeg"
a_yol, b_yol, W, H = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
def Y(yol):
    b = subprocess.run([FF, "-nostdin", "-v", "error", "-i", yol, "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, H, W).astype(np.float64)
A, B = Y(a_yol), Y(b_yol)
def kayma(a, b):
    """b'nin a'ya göre (dx, dy) alt piksel kayması: faz ilintisi tepesi + parabol."""
    w = np.outer(np.hanning(a.shape[0]), np.hanning(a.shape[1]))
    Fa, Fb = np.fft.fft2((a - a.mean()) * w), np.fft.fft2((b - b.mean()) * w)
    R = Fb * np.conj(Fa); R /= np.abs(R) + 1e-9
    r = np.fft.ifft2(R).real
    iy, ix = np.unravel_index(np.argmax(r), r.shape)
    def alt(v, i, n):
        m, p = v[(i - 1) % n], v[(i + 1) % n]; d = m - 2 * v[i] + p
        return i + (0.5 * (m - p) / d if d else 0)
    dx = alt(r[iy, :], ix, r.shape[1]); dy = alt(r[:, ix], iy, r.shape[0])
    return (dx - r.shape[1] if dx > r.shape[1] / 2 else dx), (dy - r.shape[0] if dy > r.shape[0] / 2 else dy)
print("kare", len(A), len(B))
ps = []
for n in range(min(len(A), len(B))):
    m = np.mean((A[n] - B[n]) ** 2); ps.append(99 if m == 0 else 10 * np.log10(255 ** 2 / m))
ps = np.array(ps)
print("Y-PSNR ort %.2f, en az %.2f (kare %d)" % (ps.mean(), ps.min(), ps.argmin()))
for n in [int(x) for x in sys.argv[5].split(",")]:
    # merkez 512x512 ve dört köşe yakını: ölçek farkı varsa köşelerde kayma farklı çıkar
    cy, cx = H // 2, W // 2
    parca = {"orta": (slice(cy - 256, cy + 256), slice(cx - 256, cx + 256)),
             "sol_ust": (slice(64, 576), slice(32, 544)), "sag_alt": (slice(H - 576, H - 64), slice(W - 544, W - 32))}
    print(f"kare {n}: PSNR {ps[n]:.2f} · " + " · ".join(f"{k} dx {kayma(A[n][s], B[n][s])[0]:+.3f} dy {kayma(A[n][s], B[n][s])[1]:+.3f}" for k, s in parca.items()))
