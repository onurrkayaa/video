"""(1) RIFE'nin kendi çıktısı (PNG, ProRes'ten önce): kırp-önce / ara-kare-önce, gerçek 60 fps karelerine karşı (RGB).
(2) Aynı PNG'ler ProRes HQ'ya (yavaslat'ın ayarı) kodlanınca ne kadar kayıp: kırpılmış kare / tam kare.
(3) Deneme kaynağında en hareketli 1 sn'lik pencere (önceki kare kopyasının PSNR'ı en düşük; kare açılmaz)."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

KOK = Path("/Users/onurkaya/Projects/video")
sys.path.insert(0, str(KOK))
from medya.komutlar.yavaslat import RIFE, RIFE_MODEL, _hazirla  # noqa: E402
from medya.ortak import ffmpeg  # noqa: E402

BURA = Path(__file__).parent
IS = Path(__import__("tempfile").gettempdir()) / "o3-is4k"   # büyük ara dosyalar depoya yazılmaz
FF = ffmpeg()
sonuc = {}


def rgb_dizin(d, W, H, x=0, n=None):
    out = []
    for p in sorted(d.glob("*.png"))[:n]:
        b = subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(p), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           capture_output=True, check=True).stdout
        a = np.frombuffer(b, np.uint8).reshape(-1, W, 3)
        out.append(a[:, x:x + 1216].copy())
    return out


def rgb_akis(yol, vf, w, h, bas=None, n=60):
    k = [FF, "-nostdin", "-v", "error"] + (["-ss", str(bas)] if bas is not None else []) + ["-i", str(yol), "-frames:v", str(n),
         "-vf", vf + "scale=in_color_matrix=bt709:in_range=tv,format=rgb24", "-f", "rawvideo", "-"]
    b = subprocess.run(k, capture_output=True, check=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, h, w, 3)


def psnr(a, b):
    d = a.astype(np.float32) - b.astype(np.float32)
    return float(10 * np.log10(255 ** 2 / max(float(np.mean(d * d)), 1e-9)))


def rife(hazir, d, u):
    gir, cik = d / "gir", d / "cik"
    gir.mkdir(); cik.mkdir()
    subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(hazir), "-vf", "scale=in_color_matrix=bt709:in_range=tv,format=rgb24",
                    "-fps_mode", "passthrough", str(gir / "%08d.png")], check=True)
    n = len(list(gir.glob("*.png")))
    subprocess.run([str(RIFE), "-i", str(gir), "-o", str(cik), "-m", str(RIFE_MODEL), "-n", str(2 * n), "-f", "%08d.png",
                    *(["-u"] if u else [])], check=True, capture_output=True)
    return cik


def prores_kaybi(cik, W, H, x):
    """PNG → ProRes HQ (yavaslat ayarı) → geri çöz; kırpım bölgesinde PSNR."""
    with tempfile.TemporaryDirectory() as g:
        m = Path(g) / "p.mov"
        subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-framerate", "30", "-i", str(cik / "%08d.png"), "-frames:v", "20",
                        "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv422p10le", "-c:v", "prores_ks",
                        "-profile:v", "3", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                        "-color_range", "tv", str(m)], check=True)
        geri = rgb_akis(m, "", W, H, n=20)[:, :, x:x + 1216]
        png = np.stack(rgb_dizin(cik, W, H, x, 20))
        return round(float(np.mean([psnr(a, b) for a, b in zip(geri, png)])), 2)


# (3) deneme: en hareketli pencere
DEN = KOK / "projeler/2026-10-05-deniz-kenari-deneme/kaynak/IMG_4021.MOV"
b = subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(DEN), "-vf", "crop=1216:2160:1440:0,scale=152:270:flags=area,format=gray",
                    "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
g = np.frombuffer(b, np.uint8).reshape(-1, 270, 152).astype(np.float32)
kp = np.array([psnr(g[i - 1], g[i]) for i in range(1, len(g))])
pencere = np.convolve(kp, np.ones(60) / 60, "valid")
i0 = int(np.argmin(pencere))
sonuc["deneme_hareket"] = dict(en_hareketli_bas_sn=round(i0 / 60, 3), kopya_psnr_160px=round(float(pencere[i0]), 2),
                               a_penceresi_14_25=round(float(pencere[855]), 2), ortanca=round(float(np.median(pencere)), 2))
print(sonuc["deneme_hareket"])

# (1)+(2) sentetik ve deneme (en hareketli pencere)
kaynaklar = {"sentetik": (IS / "sent4k30.mp4", IS / "sent4k60.mp4", None, 3840, 1312)}
d30h = IS / "den30_hareketli.mp4"
bas = round(i0 / 60, 4)
subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-ss", str(bas), "-i", str(DEN), "-frames:v", "30", "-vf",
                "select='not(mod(n\\,2))',setpts=N/30/TB", "-r", "30", "-c:v", "libx264", "-crf", "0", "-preset", "veryfast",
                "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", str(d30h)],
               check=True)
kaynaklar["deneme_hareketli"] = (d30h, DEN, bas, 4096, 1440)
for ad, (k30, k60, kbas, GW, X) in kaynaklar.items():
    gercek = rgb_akis(k60, f"crop=1216:2160:{X}:0:exact=1,", 1216, 2160, bas=kbas, n=58)
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "a").mkdir(); (t / "b").mkdir()
        ha = _hazirla(str(k30), t / "ha.mp4", 30, None, None, False, [f"crop=1216:2160:{X}:0:exact=1"])
        hb = _hazirla(str(k30), t / "hb.mp4", 30, None, None, False, [])
        ca, cb = rife(ha, t / "a", True), rife(hb, t / "b", True)
        pa, pb = rgb_dizin(ca, 1216, 2160, 0, 58), rgb_dizin(cb, GW, 2160, X, 58)
        ara = range(1, 57, 2)
        A = [psnr(pa[i], gercek[i]) for i in ara]
        B = [psnr(pb[i], gercek[i]) for i in ara]
        kopya = [psnr(gercek[i - 1], gercek[i]) for i in ara]
        k5 = max(1, round(len(A) * 0.05))
        sonuc[ad] = dict(rife_png_kirp_once=round(float(np.mean(A)), 2), rife_png_ara_kare_once=round(float(np.mean(B)), 2),
                         kare_kare_fark_ort=round(float(np.mean(np.array(A) - np.array(B))), 2),
                         kotu5_kirp_once=round(float(np.mean(sorted(A)[:k5])), 2),
                         kotu5_ara_kare_once=round(float(np.mean(sorted(B)[:k5])), 2), kopya_ort=round(float(np.mean(kopya)), 2),
                         prores_kaybi_kirpik_kare=prores_kaybi(ca, 1216, 2160, 0),
                         prores_kaybi_tam_kare_kirpim_bolgesi=prores_kaybi(cb, GW, 2160, X))
        print(ad, sonuc[ad])
(BURA / "tani2.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1))
