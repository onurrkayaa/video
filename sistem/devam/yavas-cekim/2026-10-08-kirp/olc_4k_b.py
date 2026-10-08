"""O3 4K ölçümü: kırp-önce / ara-kare-önce (ikisi de RIFE; 4K'da -u) ve 60 fps yolunun eski/yeni karşılaştırması.
Doğruluk: gerçek 60 fps kareleri (aynı kırpım/ölçek). Kareler ham çözülür, psnr süzgeci yok. Sonuç adım adım JSON'a.
Kaynaklar: tam sayı hareketli sentetik 4K60 (yuvarlama yok) ve deneme kaynağı (IMG_4021, 4096x2160 60 fps; kare açılmaz)."""
import importlib.util
import json
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np

KOK = Path("/Users/onurkaya/Projects/video")
sys.path.insert(0, str(KOK))
from medya.komutlar.yavaslat import yavaslat as yeni  # noqa: E402
from medya.ortak import ffmpeg  # noqa: E402

BURA = Path(__file__).parent
IS = Path(__import__("tempfile").gettempdir()) / "o3-is4k"   # büyük ara dosyalar depoya yazılmaz
IS.mkdir(exist_ok=True)   # sıra: olc_4k_b.py (kaynakları üretir) → tani2.py → tani3.py; eski modül: yavaslat_eski.py (O3 öncesi)
CIKTI = BURA / "olc_4k_b.json"
sonuc = json.loads(CIKTI.read_text()) if CIKTI.exists() else {}
spec = importlib.util.spec_from_file_location("medya.komutlar.yavaslat_eski", BURA / "yavaslat_eski.py")
eski_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eski_mod)
FF = ffmpeg()


def yaz():
    CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1))


def ff(*a):
    subprocess.run([FF, "-nostdin", "-v", "error", "-y", *a], check=True)


def akis(yol, vf, w, h, bas=None, n=None):
    """Gri kareleri tek tek verir (bellek dostu)."""
    k = [FF, "-nostdin", "-v", "error"] + (["-ss", str(bas)] if bas is not None else []) + ["-i", str(yol)]
    k += (["-frames:v", str(n)] if n else []) + ["-vf", f"{vf}format=gray", "-fps_mode", "passthrough", "-f", "rawvideo", "-"]
    p = subprocess.Popen(k, stdout=subprocess.PIPE)
    boy = w * h
    while True:
        b = p.stdout.read(boy)
        if len(b) < boy:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w)
    p.wait()


def psnr_dizi(a_akis, b_akis):
    out = []
    for a, b in zip(a_akis, b_akis):
        d = a.astype(np.int16) - b.astype(np.int16)
        mse = float(np.mean(d.astype(np.float32) ** 2))
        out.append(10 * np.log10(255 ** 2 / max(mse, 1e-9)))
    return out


class DiskTepe:
    def __enter__(self):
        self.bas = shutil.disk_usage(KOK).free
        self.en_az, self.dur = self.bas, False
        self.t = threading.Thread(target=self._dongu, daemon=True)
        self.t.start()
        self.t0 = time.time()
        return self

    def _dongu(self):
        while not self.dur:
            self.en_az = min(self.en_az, shutil.disk_usage(KOK).free)
            time.sleep(0.5)

    def __exit__(self, *a):
        self.dur = True
        self.t.join()
        self.sure = time.time() - self.t0
        self.tepe_gb = round((self.bas - self.en_az) / 1e9, 2)


def ozet(p, ara_idx, ozgun_idx):
    a = [p[i] for i in ara_idx if i < len(p)]
    o = [p[i] for i in ozgun_idx if i < len(p)]
    k5 = max(1, round(len(a) * 0.05))
    return dict(ara_ort=round(float(np.mean(a)), 2), ara_kotu5=round(float(np.mean(sorted(a)[:k5])), 2),
                ara_min=round(float(min(a)), 2), ozgun_ort=round(float(np.mean(o)), 2),
                ozgun_min=round(float(min(o)), 2), n=len(p))


# ---------------------------------------------------------------- kaynaklar
s60, s30 = IS / "sent4k60.mp4", IS / "sent4k30.mp4"
if not s60.exists():
    ff("-f", "lavfi", "-i", "mandelbrot=s=4480x2560:r=1", "-frames:v", "1", str(IS / "doku.png"))
    hareket = ("crop=3840:2160:x='100+360*t':y='60+120*t',drawbox=x='600+480*t':y='900+120*t':w=400:h=400:"
               "color=orange@1:t=fill,drawbox=x='3000-240*t':y='300+60*t':w=240:h=600:color=0x2040ff@1:t=fill,format=yuv420p")
    renk = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
    ff("-loop", "1", "-framerate", "60", "-t", "1", "-i", str(IS / "doku.png"), "-vf", hareket, "-r", "60",
       "-c:v", "libx264", "-crf", "0", "-preset", "veryfast", *renk, str(s60))
    (IS / "doku.png").unlink()
if not s30.exists():
    ff("-i", str(s60), "-vf", "select='not(mod(n\\,2))',setpts=N/30/TB", "-r", "30", "-c:v", "libx264", "-crf", "0",
       "-preset", "veryfast", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
       "-color_range", "tv", str(s30))
DEN = KOK / "projeler/2026-10-05-deniz-kenari-deneme/kaynak/IMG_4021.MOV"
d30 = IS / "den30_hareketli.mp4"
if not d30.exists():   # deneme en hareketli pencere (1,2333 sn = kare 74), 1 sn, çift kareler
    ff("-ss", "1.233333", "-i", str(DEN), "-frames:v", "30", "-vf", "select='not(mod(n\\,2))',setpts=N/30/TB", "-r", "30",
       "-c:v", "libx264", "-crf", "0", "-preset", "veryfast", "-colorspace", "bt709", "-color_primaries", "bt709",
       "-color_trc", "bt709", "-color_range", "tv", str(d30))

KAYNAK = {"sentetik": dict(k60=s60, k30=s30, bas=None, gw=3840, kirp="1312,0,1216,2160"),
          "deneme_hareketli": dict(k60=DEN, k30=d30, bas=1.233333, gw=4096, kirp="1440,0,1216,2160")}

# ---------------------------------------------------------------- 1) kırp-önce / ara-kare-önce, 4K
for ad, K in KAYNAK.items():
    anahtar = f"kirp_sirasi_{ad}"
    if "kirpim_1216x2160" in sonuc.get(anahtar, {}):
        continue
    x, y, w, h = (int(n) for n in K["kirp"].split(","))
    vf_k = f"crop={w}:{h}:{x}:{y}:exact=1,"
    vf_ko = vf_k + "scale=1080:1920:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv420p,"
    r = {}
    for kip, kw in (("A_kirp_once_1216x2160", dict(kirp=K["kirp"])),
                    ("A2_kirp_olcek_once_1080x1920", dict(kirp=K["kirp"], olcek="1080x1920")),
                    ("B_tam_4k", {})):
        cik = IS / f"{ad}_{kip}.mov"
        with DiskTepe() as dt:
            s = yeni(str(K["k30"]), str(cik), 0.5, yontem="rife", **kw)
        r[kip] = dict(yontem=s["yontem"], kat=s.get("kat"), hazir_fps=s.get("hazir_fps"), sure_sn=round(dt.sure, 1),
                      disk_tepe_gb=dt.tepe_gb, mb=round(cik.stat().st_size / 1e6, 1),
                      dusulen=s.get("dusulen"))
        sonuc[anahtar] = r
        yaz()
    ara_idx, ozg_idx = range(1, 58, 2), range(0, 59, 2)   # 59: RIFE'nin sağ komşusuz son karesi
    gercek = lambda vf, ww, hh: akis(K["k60"], vf, ww, hh, bas=K["bas"], n=60)
    pA = psnr_dizi(akis(IS / f"{ad}_A_kirp_once_1216x2160.mov", "", w, h), gercek(vf_k, w, h))
    pB = psnr_dizi(akis(IS / f"{ad}_B_tam_4k.mov", vf_k, w, h), gercek(vf_k, w, h))
    pA2 = psnr_dizi(akis(IS / f"{ad}_A2_kirp_olcek_once_1080x1920.mov", "", 1080, 1920), gercek(vf_ko, 1080, 1920))
    pB2 = psnr_dizi(akis(IS / f"{ad}_B_tam_4k.mov", vf_ko, 1080, 1920), gercek(vf_ko, 1080, 1920))
    kopya = []
    g = list(gercek(vf_k, w, h))
    for i in ara_idx:
        if i < len(g):
            d = g[i - 1].astype(np.float32) - g[i].astype(np.float32)
            kopya.append(10 * np.log10(255 ** 2 / max(float(np.mean(d ** 2)), 1e-9)))
    r["kirpim_1216x2160"] = dict(kirp_once=ozet(pA, ara_idx, ozg_idx), ara_kare_once=ozet(pB, ara_idx, ozg_idx),
                                 kare_kare_fark_ort=round(float(np.mean([pA[i] - pB[i] for i in ara_idx])), 2),
                                 kopya_ort=round(float(np.mean(kopya)), 2))
    r["kirpim_olcek_1080x1920"] = dict(kirp_olcek_once=ozet(pA2, ara_idx, ozg_idx), ara_kare_once=ozet(pB2, ara_idx, ozg_idx),
                                       kare_kare_fark_ort=round(float(np.mean([pA2[i] - pB2[i] for i in ara_idx])), 2))
    sonuc[anahtar] = r
    yaz()
    for f in IS.glob(f"{ad}_*.mov"):
        f.unlink()

# ---------------------------------------------------------------- 2) 60 fps yolu eski/yeni (yarı ölçekli eşdeğer):
# 30 fps kaynak (60 fps'in çift kareleri), --fps 15 --hiz 0.25 → eski: 15 fps'e iner × 4; yeni: 30 fps × 2.
# Çıktı karesi i = gerçek 60 fps karesi i. Kaynak 1080x1920'ye kırpılıp ölçeklenmiş (RIFE ilk sırada, -u yok).
for ad, K in KAYNAK.items():
    anahtar = f"gercek_kare_yolu_{ad}"
    if "yeni" in sonuc.get(anahtar, {}):
        continue
    x, y, w, h = (int(n) for n in K["kirp"].split(","))
    vf_ko = f"crop={w}:{h}:{x}:{y}:exact=1,scale=1080:1920:flags=lanczos:out_color_matrix=bt709:out_range=tv"   # ardından format=yuv420p
    g60, g30 = IS / f"{ad}_g60.mp4", IS / f"{ad}_g30.mp4"
    ff(*(["-ss", str(K["bas"])] if K["bas"] is not None else []), "-i", str(K["k60"]), "-frames:v", "60", "-vf",
       vf_ko + ",format=yuv420p", "-c:v", "libx264", "-crf", "0", "-preset", "veryfast", "-colorspace", "bt709",
       "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", str(g60))
    ff("-i", str(g60), "-vf", "select='not(mod(n\\,2))',setpts=N/30/TB", "-r", "30", "-c:v", "libx264", "-crf", "0",
       "-preset", "veryfast", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
       "-color_range", "tv", str(g30))
    r = {}
    for kip, f in (("eski", eski_mod.yavaslat), ("yeni", yeni)):
        cik = IS / f"{ad}_{kip}.mov"
        with DiskTepe() as dt:
            s = f(str(g30), str(cik), 0.25, fps=15, yontem="rife")
        p = psnr_dizi(akis(cik, "", 1080, 1920), akis(g60, "", 1080, 1920))[:57]   # 57+: eskide sağ komşusuz kuyruk
        r[kip] = dict(yontem=s["yontem"], kat=s.get("kat"), hazir_fps=s.get("hazir_fps"), sure_sn=round(dt.sure, 1),
                      n=len(p), hepsi_ort=round(float(np.mean(p)), 2),
                      cift_ort=round(float(np.mean(p[0::2])), 2), cift_min=round(float(min(p[0::2])), 2),
                      tek_ort=round(float(np.mean(p[1::2])), 2), tek_min=round(float(min(p[1::2])), 2),
                      dort_ort=round(float(np.mean(p[0::4])), 2),
                      uretilen_ort=round(float(np.mean([v for i, v in enumerate(p) if i % (4 if kip == "eski" else 2)])), 2),
                      kotu5=round(float(np.mean(sorted(p)[:max(1, round(len(p) * 0.05))])), 2))
        sonuc[anahtar] = r
        yaz()
        cik.unlink()
    g60.unlink()
    g30.unlink()
print(json.dumps(sonuc, ensure_ascii=False, indent=1))
