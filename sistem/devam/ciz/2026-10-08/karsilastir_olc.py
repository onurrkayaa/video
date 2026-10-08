"""Kayıpsız başvuru (planın ideal çizimi: ciz'in nle_olc ile doğrulanmış kare seçimi ve erime karışımı, FFV1) + VMAF ve
Y-PSNR (kareler doğrudan çözülerek), HyperFrames çiziminin kare hizası (−1/0/+1 kayma)."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
K = Path("/Users/onurkaya/Projects/video"); sys.path.insert(0, str(K))
from medya.komutlar.ciz import plani_hazirla, egri, _gecis
FF = str(K / "arac/ffmpeg")
D = Path(sys.argv[1]); W, H = 1920, 1080
ref = D / "ref.mkv"
if not ref.exists():
    P = plani_hazirla(json.loads((D / "plan/kurgu.json").read_text()), D)
    enc = subprocess.Popen([FF, "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}",
                            "-framerate", "30", "-i", "-", "-c:v", "ffv1", "-level", "3", str(ref)], stdin=subprocess.PIPE)
    for x in P.cekimler: x.baslat()
    for n in range(P.toplam):
        e = [x for x in P.cekimler if x.bas_n <= n < x.son_n]
        if len(e) == 1: k = e[0].sonraki()
        else:
            a, b = e; w = egri(_gecis(b.c).get("egri"), (n - b.bas_n) / (a.son_n - b.bas_n))
            k = np.rint(np.frombuffer(a.sonraki(), np.uint8) * np.float32(1 - w) + np.frombuffer(b.sonraki(), np.uint8) * np.float32(w)).astype(np.uint8).tobytes()
        enc.stdin.write(k)
    enc.stdin.close(); enc.wait()
    for x in P.cekimler: x.kapat()
def y_kareler(yol):
    b = subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(yol), "-map", "0:v:0", "-fps_mode", "passthrough", "-f", "rawvideo",
                        "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, H, W)
def psnr(a, b):
    m = np.mean((a.astype(np.float64) - b) ** 2); return 99.0 if m == 0 else 10 * np.log10(255 ** 2 / m)
R = y_kareler(ref)
sonuc = {"ref_kare": len(R)}
for ad in ("ciz", "hf_png", "hf_auto"):
    yol = D / f"{ad}.mp4"
    log = D / f"vmaf-{ad}.json"
    subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(yol), "-i", str(ref), "-lavfi",
                    "[0:v]settb=1/30,setpts=N[d];[1:v]settb=1/30,setpts=N[r];[d][r]libvmaf=model=version=vmaf_v0.6.1:n_threads=8:"
                    f"log_fmt=json:log_path={log}", "-f", "null", "-"], check=True)
    v = json.loads(log.read_text())
    kv = [f["metrics"]["vmaf"] for f in v["frames"]]
    X = y_kareler(yol)
    ps = [psnr(X[i], R[i]) for i in range(min(len(X), len(R)))]
    hiza = {}
    for kay in (-1, 0, 1):          # X[n] ile R[n+kay]: en iyi 0 olmalı (kesim ve erime çevresindeki kareler)
        idx = [n for n in (70, 74, 75, 76, 80, 137, 140, 149, 150, 224, 225, 226) if 0 <= n + kay < len(R) and n < len(X)]
        hiza[kay] = round(float(np.mean([psnr(X[n], R[n + kay]) for n in idx])), 2)
    sonuc[ad] = {"kare": len(X), "vmaf_ort": round(v["pooled_metrics"]["vmaf"]["mean"], 3),
                 "vmaf_en_az": round(v["pooled_metrics"]["vmaf"]["min"], 3),
                 "vmaf_en_kotu_5": round(float(np.mean(sorted(kv)[:max(1, len(kv) // 20)])), 3),
                 "y_psnr_ort": round(float(np.mean(ps)), 3), "y_psnr_en_az": round(float(np.min(ps)), 3),
                 "kayma_psnr": hiza, "bayt": yol.stat().st_size}
    print(ad, sonuc[ad])
(D / "karsilastirma.json").write_text(json.dumps(sonuc, indent=1))
