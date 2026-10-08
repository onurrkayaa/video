"""Kadraj ve Ken Burns ölçümü: sabit işaretli (Gauss lekeleri) kaynak, ciz çizimi, leke merkezleri plana karşı."""
import json, subprocess, sys
from pathlib import Path
import numpy as np
K = Path("/Users/onurkaya/Projects/video")
sys.path.insert(0, str(K))
from medya.cli import ana
from medya.komutlar.ciz import plani_hazirla
FF = str(K / "arac/ffmpeg")
D = Path(sys.argv[1]); D.mkdir(parents=True, exist_ok=True)
Ws, Hs = 1920, 1080
LEKE = [(x, y) for x in (700.3, 1000.6, 1240.2, 1500.8) for y in (200.4, 540.1, 860.7)]
def kaynak(yol):
    yy, xx = np.mgrid[0:Hs, 0:Ws].astype(np.float32)
    Y = np.full((Hs, Ws), 40, np.float32)
    for bx, by in LEKE:
        Y += 180 * np.exp(-((xx - bx) ** 2 + (yy - by) ** 2) / (2 * 5.0 ** 2))
    kare = np.concatenate([np.clip(np.rint(Y), 0, 255).astype(np.uint8).ravel(), np.full(Ws * Hs // 2, 128, np.uint8)]).tobytes()
    subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{Ws}x{Hs}", "-r", "30",
                    "-i", "-", "-c:v", "libx264", "-qp", "0", "-preset", "veryfast", "-colorspace", "bt709", "-color_primaries", "bt709",
                    "-color_trc", "bt709", "-color_range", "tv", str(yol)], input=kare * 90, check=True)
def kareler(yol, w, h):
    b = subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(yol), "-map", "0:v:0", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, h, w).astype(np.float64)
def merkez(im, x, y, r=10):
    x0, y0 = int(round(x)) - r, int(round(y)) - r
    p = im[max(0, y0):y0 + 2 * r + 1, max(0, x0):x0 + 2 * r + 1]
    if p.shape != (2 * r + 1, 2 * r + 1): return None
    g = np.clip(p - np.median(p) - 3, 0, None)
    yy, xx = np.mgrid[0:p.shape[0], 0:p.shape[1]]
    return (x0 + (g * xx).sum() / g.sum(), y0 + (g * yy).sum() / g.sum()) if g.sum() > 0 else None
src = D / "leke.mp4"
if not src.exists(): kaynak(src)
Wc, Hc = 540, 960
sonuc = {}
for ad, cek in [("sabit", {"kadraj": {"ilgi": [0.62, 0.5]}}),
                ("kenburns_dogrusal", {"kadraj": {"ilgi": [0.62, 0.4]}, "hareket": {"tur": "kenburns", "olcek": [1.0, 1.15]}}),
                ("kenburns_sine", {"kadraj": {"ilgi": [0.62, 0.4]}, "hareket": {"tur": "kenburns", "olcek": [1.0, 1.15], "egri": "sine.inOut"}}),
                ("punch", {"hareket": {"tur": "punch", "olcek": [1.0, 1.2], "kare": 4, "egri": "expo.out"}})]:
    plan = {"ad": ad, "fps": 30, "boyut": [Wc, Hc], "cekimler": [dict({"no": 1, "kaynak": str(src), "kaynak_bas": 0.0, "cikti_bas": 0,
            "cikti_son": 2.0, "hiz": 1, "ses": "sessiz", "vurusa": False, "gecis": {"tur": "kesim", "sure_kare": 0}}, **cek)]}
    (D / "plan").mkdir(exist_ok=True)
    pj = D / "plan" / f"{ad}.json"; pj.write_text(json.dumps(plan))
    out = D / f"{ad}.mp4"; out.unlink(missing_ok=True)
    crf = sys.argv[2] if len(sys.argv) > 2 else "16"
    assert ana(["ciz", str(pj), "--cikti", str(out), "--kok", str(D), "--crf", crf]) == 0
    x = plani_hazirla(plan, D).cekimler[0]
    k = kareler(out, Wc, Hc)
    hatalar, artik = [], []
    for j, im in enumerate(k):
        L, T, Rw, Rh = x.kaynak_dikdortgeni(j)
        satir = []
        for bx, by in LEKE:
            ex = (bx + 0.5 - L) / Rw * Wc - 0.5
            ey = (by + 0.5 - T) / Rh * Hc - 0.5
            if not (12 < ex < Wc - 12 and 12 < ey < Hc - 12): satir.append(None); continue
            m = merkez(im, ex, ey)
            satir.append(None if m is None else (m[0] - ex, m[1] - ey))
        artik.append(satir)
    A = np.array([[(np.nan, np.nan) if v is None else v for v in s] for s in artik])   # kare x leke x 2
    hata = np.nanmax(np.abs(A))
    ikinci = np.abs(np.diff(A, n=2, axis=0)).reshape(-1)
    ikinci = ikinci[~np.isnan(ikinci)]
    sonuc[ad] = {"kare": len(k), "leke": int(np.sum(~np.isnan(A[..., 0]))), "en_buyuk_hata_px": round(float(hata), 3),
                 "ort_hata_px": [round(float(np.nanmean(A[..., 0])), 3), round(float(np.nanmean(A[..., 1])), 3)],
                 "artik_ikinci_fark_p95_px": round(float(np.percentile(ikinci, 95)), 4) if len(ikinci) else None,
                 "kirp": x.kirp, "pencere": [round(v, 3) for v in x.pencere]}
    print(ad, sonuc[ad])
(D / "geometri.json").write_text(json.dumps(sonuc, indent=1))
