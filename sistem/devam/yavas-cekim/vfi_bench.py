"""Ara kare doğruluk sınaması: gerçek 60 fps kareler → her N'inci kare girdi → yöntem N kat ara kare üretir →
YALNIZ üretilen ara kareler, atılan gerçek karelerle karşılaştırılır (kareler ham çözülür; ffmpeg psnr süzgeci yok).

  python vfi_bench.py <klip> <N> <yontem> [<yontem> ...]
  yontem: apple | minterp | rife-v4.6 | rife-v4.22 | rife-v4.25 | rife-v4.26 | karisim | kopya
"""
import csv, json, os, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np

KOK = Path(__file__).resolve().parent
FF = "/Users/onurkaya/Projects/video/arac/ffmpeg"
APPLE = "/Users/onurkaya/Projects/video/arac/medya-apple"
NIHUI = KOK / "nihui/rife-ncnn-vulkan-20221029-macos"
TNT = KOK / "tnt/macos"
RIFE = {
    "rife-v4.6": (NIHUI / "rife-ncnn-vulkan", NIHUI / "rife-v4.6"),
    "rife-v4.22": (TNT / "rife-ncnn-vulkan", TNT / "rife-v4.22"),
    "rife-v4.25": (TNT / "rife-ncnn-vulkan", TNT / "rife-v4.25"),
    "rife-v4.26": (TNT / "rife-ncnn-vulkan", TNT / "rife-v4.26"),
    "rife-v4.25-lite": (TNT / "rife-ncnn-vulkan", TNT / "rife-v4.25-lite"),
    "rife-v4.25-heavy": (TNT / "rife-ncnn-vulkan", TNT / "rife-v4.25-heavy"),
    "rife-v4.22-lite": (TNT / "rife-ncnn-vulkan", TNT / "rife-v4.22-lite"),
}
KLIP = {
    "gercek_sakin": dict(src="/Users/onurkaya/Projects/video/projeler/2026-10-05-deniz-kenari-deneme/kaynak/IMG_4021.MOV",
                         ss=17.0, n=240, w=1024, h=540),
    "bbb_yuksek": dict(src=str(KOK / "data/bbb_sunflower_1080p_60fps_normal.mp4"), ss=361.5, n=240, w=960, h=540),
    "bbb_yuksek_1080": dict(src=str(KOK / "data/bbb_sunflower_1080p_60fps_normal.mp4"), ss=361.5, n=120, w=1920, h=1080),
    "sentetik": dict(src="/Users/onurkaya/Projects/video/testler/veri/hareket60.mp4", ss=None, n=120, w=1280, h=720),
    # Tears of Steel (CC-BY 3.0, Blender Foundation) — gerçek kamera, 24 fps: 2x sınaması 12 → 24
    "tos_kaydirma": dict(src=str(KOK / "data/tears_of_steel_1080p.mov"), ss=258.0, n=96, w=1920, h=800, fps=24),
    "tos_elde": dict(src=str(KOK / "data/tears_of_steel_1080p.mov"), ss=159.5, n=96, w=1920, h=800, fps=24),
}
SONUC = KOK / "sonuc"
SONUC.mkdir(exist_ok=True)


def ff(*a, **kw):
    return subprocess.run([FF, "-nostdin", "-v", "error", "-y", *a], check=True, **kw)


def gt_hazirla(ad):
    c = KLIP[ad]
    d = KOK / "run" / ad / "gt"
    if d.exists() and len(list(d.glob("*.png"))) == c["n"]:
        return d
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    a = []
    if c["ss"] is not None:
        a += ["-ss", str(c["ss"])]
    a += ["-i", c["src"], "-an", "-vf",
          f"scale={c['w']}:{c['h']}:flags=area:in_color_matrix=bt709:in_range=tv,format=rgb24",
          "-fps_mode", "passthrough", "-frames:v", str(c["n"]), str(d / "%08d.png")]
    ff(*a)
    assert len(list(d.glob("*.png"))) == c["n"], "gt kare sayısı"
    return d


def girdi_hazirla(ad, N):
    """Ortak girdi = stüdyonun _hazirla biçimi: her N'inci gerçek kare → x264 crf 6, yuv420p, BT.709 (in264.mp4).
    Bütün yöntemler AYNI girdi piksellerini alır: Apple ve minterpolate bu dosyayı, RIFE bundan çözülen PNG'leri."""
    gt = sorted(gt_hazirla(ad).glob("*.png"))
    kul = ((len(gt) - 1) // N) * N + 1                  # son kullanılan gerçek kare bir girdi karesi olsun
    K = (kul - 1) // N + 1
    d = KOK / "run" / ad / f"x{N}"
    sec = d / "sec"
    if not (sec.exists() and len(list(sec.glob("*.png"))) == K):
        shutil.rmtree(sec, ignore_errors=True)
        sec.mkdir(parents=True)
        for j, i in enumerate(range(0, kul, N)):
            os.link(gt[i], sec / f"{j + 1:08d}.png")
    mov = d / "in264.mp4"
    if not mov.exists():
        ff("-framerate", f"{KLIP[ad].get('fps', 60) / N:g}", "-i", str(sec / "%08d.png"), "-vf",
           "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p", "-c:v", "libx264", "-crf", "6", "-preset",
           "veryfast", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv",
           str(mov))
    g = d / "in"
    if not (g.exists() and len(list(g.glob("*.png"))) == K):
        shutil.rmtree(g, ignore_errors=True)
        g.mkdir(parents=True)
        ff("-i", str(mov), "-vf", "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-fps_mode", "passthrough",
           str(g / "%08d.png"))
        assert len(list(g.glob("*.png"))) == K
    return d, g, mov, kul


def oku_rgb(args, w, h):
    p = subprocess.run([FF, "-nostdin", "-v", "error", *args, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w, 3)


def gt_oku(ad):
    c = KLIP[ad]
    return oku_rgb(["-i", str(gt_hazirla(ad) / "%08d.png")], c["w"], c["h"])


# --- ölçüler -------------------------------------------------------------------------------------------------
_k = np.exp(-0.5 * ((np.arange(11) - 5) / 1.5) ** 2)
_k /= _k.sum()


def _g(x):
    H, W = x.shape
    y = sum(_k[i] * x[i:H - 10 + i, :] for i in range(11))
    return sum(_k[i] * y[:, i:W - 10 + i] for i in range(11))


def luma(a):
    a = a.astype(np.float64)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def ssim(x, y):                                       # Wang 2004, Gauss 11/1.5, geçerli bölge (skimage ile aynı)
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    mx, my = _g(x), _g(y)
    sxx, syy, sxy = _g(x * x) - mx * mx, _g(y * y) - my * my, _g(x * y) - mx * my
    m = ((2 * mx * my + C1) * (2 * sxy + C2)) / ((mx * mx + my * my + C1) * (sxx + syy + C2))
    return float(m.mean())


def psnr(a, b):
    mse = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))
    return 100.0 if mse == 0 else 10 * np.log10(255.0 ** 2 / mse)


def olc(ad, N, yontem, cikti, gt, kul, sure, notlar=""):
    satir = []
    n = kul - N                                       # son aralık herkes için dışarıda (minterpolate onu üretmiyor)
    assert len(cikti) >= n, f"{yontem}: çıktı {len(cikti)} kare, beklenen ≥ {n}"
    hiza = []
    for i in range(n):
        if i % N == 0:
            yG, yC = luma(gt[i]), luma(cikti[i])
            satir.append(dict(tur="ozgun", i=i, faz=0, psnr_y=psnr(yG, yC), ssim_y=None, psnr_rgb=psnr(gt[i], cikti[i])))
            continue
        yG, yC = luma(gt[i]), luma(cikti[i])
        satir.append(dict(tur="ara", i=i, faz=(i % N) / N, psnr_y=psnr(yG, yC), ssim_y=ssim(yG, yC),
                          psnr_rgb=psnr(gt[i], cikti[i])))
        if len(hiza) < 40 and i + 1 < n:              # hizalama sağlaması: en yakın gerçek kare i olmalı
            p = [psnr(luma(gt[j]), yC) for j in (i - 1, i, i + 1)]
            hiza.append(int(np.argmax(p)) == 1)
    ara = [s for s in satir if s["tur"] == "ara"]
    oz = [s for s in satir if s["tur"] == "ozgun"]
    py = np.array([s["psnr_y"] for s in ara]); ss = np.array([s["ssim_y"] for s in ara])
    pr = np.array([s["psnr_rgb"] for s in ara])
    k5 = max(1, int(round(len(py) * 0.05)))
    ozet = dict(klip=ad, N=N, yontem=yontem, ara_kare=len(ara),
                psnr_y_ort=round(float(py.mean()), 2), psnr_y_kotu5_ort=round(float(np.sort(py)[:k5].mean()), 2),
                psnr_y_min=round(float(py.min()), 2),
                ssim_y_ort=round(float(ss.mean()), 4), ssim_y_kotu5_ort=round(float(np.sort(ss)[:k5].mean()), 4),
                ssim_y_min=round(float(ss.min()), 4),
                psnr_rgb_ort=round(float(pr.mean()), 2),
                tavan_ozgun_psnr_y=round(float(np.mean([s["psnr_y"] for s in oz])), 2),
                hizalama=f"{sum(hiza)}/{len(hiza)}" if hiza else "-",
                sure_sn=None if sure is None else round(sure, 2),
                ms_ara_kare=None if sure is None else round(1000 * sure / len(ara), 1), notlar=notlar)
    # faz bazında
    for f in sorted({s["faz"] for s in ara}):
        v = [s["psnr_y"] for s in ara if s["faz"] == f]
        ozet[f"psnr_y_faz{f:g}"] = round(float(np.mean(v)), 2)
    with open(SONUC / f"kare_{ad}_x{N}_{yontem}.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(satir[0].keys()))
        w.writeheader(); w.writerows(satir)
    with open(SONUC / "ozet.jsonl", "a") as fh:
        fh.write(json.dumps(ozet, ensure_ascii=False) + "\n")
    print(json.dumps(ozet, ensure_ascii=False))
    return ozet


def calistir(ad, N, yontem):
    c = KLIP[ad]
    d, g, mov, kul = girdi_hazirla(ad, N)
    gt = gt_oku(ad)
    K = (kul - 1) // N + 1
    out = d / f"out_{yontem}"
    shutil.rmtree(out, ignore_errors=True)
    notlar = ""
    if yontem in ("karisim", "kopya"):
        gir = oku_rgb(["-i", str(g / "%08d.png")], c["w"], c["h"])
        cik = []
        for i in range(kul):
            a, r = divmod(i, N)
            A = gir[a].astype(np.float64)
            B = gir[min(a + 1, K - 1)].astype(np.float64)
            t = r / N
            cik.append(np.clip(np.rint((1 - t) * A + t * B), 0, 255).astype(np.uint8) if yontem == "karisim"
                       else gir[a])
        return olc(ad, N, yontem, np.stack(cik), gt, kul, None)
    if yontem == "apple":
        out.mkdir(parents=True)
        t0 = time.time()
        p = subprocess.run([APPLE, "yavaslat", str(mov), str(out / "a.mov"), str(N), "--kodek", "prores"],
                           capture_output=True, text=True, check=True, timeout=float(os.environ.get("APPLE_ZA", "480")))
        sure = time.time() - t0
        notlar = p.stdout.strip().splitlines()[-1]
        cik = oku_rgb(["-i", str(out / "a.mov"), "-vf", "scale=in_color_matrix=bt709:in_range=tv,format=rgb24",
                       "-fps_mode", "passthrough"], c["w"], c["h"])
    elif yontem == "minterp":
        out.mkdir(parents=True)
        t0 = time.time()
        ff("-i", str(mov), "-vf",                       # stüdyodaki gibi yuv420p üzerinde, aynı ayarlar
           f"minterpolate=fps={c.get('fps', 60)}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
           "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-f", "rawvideo", str(out / "m.rgb"))
        sure = time.time() - t0
        cik = np.fromfile(out / "m.rgb", np.uint8).reshape(-1, c["h"], c["w"], 3)
    elif yontem in RIFE:
        b, m = RIFE[yontem]
        out.mkdir(parents=True)
        t0 = time.time()
        p = subprocess.run([str(b), "-i", str(g), "-o", str(out), "-m", str(m), "-n", str(K * N), "-f", "%08d.png"],
                           capture_output=True, text=True)
        sure = time.time() - t0
        if p.returncode != 0:
            print(p.stderr[-2000:]); raise SystemExit(f"{yontem} başarısız")
        notlar = " ".join(l for l in p.stderr.splitlines() if l.startswith("[0"))[:200]
        cik = oku_rgb(["-i", str(out / "%08d.png")], c["w"], c["h"])
    else:
        raise SystemExit(f"bilinmeyen yöntem {yontem}")
    try:
        return olc(ad, N, yontem, cik, gt, kul, sure, notlar)
    finally:
        shutil.rmtree(out, ignore_errors=True)        # büyük çıktıları hemen sil, yalnız CSV/JSON kalsın


if __name__ == "__main__":
    ad, N = sys.argv[1], int(sys.argv[2])
    for y in sys.argv[3:]:
        calistir(ad, N, y)
