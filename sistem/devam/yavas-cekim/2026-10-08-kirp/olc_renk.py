"""--olcek renk matrisi (2026-10-08 düzeltme turu). Bulgu: etiketsiz (matris 'unknown') HD SDR kaynakta --olcek renkleri
sessizce kaydırıyordu; scale'in giriş matrisi 'auto' kalınca ffmpeg 6.0 etiketsiz kareyi BT.601 okuyup BT.709'a
çeviriyor. Ayrıca HDR yolundaki ölçek renk ayarının (out_color_matrix/out_range + setparams) kanıtı.

SDR: smptehdbars 60 fps 0,5 sn, libx264 CRF 10. Kaynaklar: 1280x720 etiketsiz (h264_metadata matrix_coefficients,
colour_primaries, transfer_characteristics = 2), bt709, smpte170m; 640x360 etiketsiz. yavaslat --hiz 0.5 (doğal yol,
.mp4) üç biçimde: ölçeksiz (O3 öncesi yol), --olcek yarı boyut O3 ilk hâli (giriş matrisi verilmez = 'auto'), --olcek
bugünkü kod.
  psnr_duz / psnr_601_709: çıktının Y/U/V'si (ham yuv420p, en kötü kare) iki başvuruya karşı: matris çevirmeyen düz
  ölçek / BT.601→709 çevrilmiş ölçek.
  hf_*: HyperFrames'in göreceği renk. Çıktı ve kaynak, etiketlerine göre RGB'ye çözülür; etiketsizse önce HyperFrames'in
  tahmini uygulanır (chromeGuessForUntaggedMatrix, 0.8.140 chunk-TPECLKPA.js:11413: ≥ 720 satır → bt709, değilse
  smpte170m). hf_cubuk: 7 renk çubuğunun ortası; hf_fark: bütün karede |çıktı − kaynak| ortalaması ve en çoğu.
HDR: testler/veri/hdr_hlg.mp4 (HLG, bt2020nc), --kirp 160,0,320,360 --olcek 160x180, doğal (--fps 15) ve ara kare
(--yontem ffmpeg) yolu. scale ayarsız (O3 ilk taslağı) / out_color_matrix=bt709:out_range=tv ama setparams yok / bugünkü
kod. Başvuru sınamadaki zincir: ton eşleme → yuv420p → kırp → ölçek. Y/U/V PSNR (ortalama, en kötü kare), sınamanın
kendi ölçütü (gri, en kötü kare) ve çıktının matris etiketi. Ara yolda çift kareler kaynağın kareleri, son kare hariç.
Sentetik kaynaklar; kişisel görüntü yok.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

KOK = Path("/Users/onurkaya/Projects/video")
sys.path.insert(0, str(KOK))
import medya.komutlar.yavaslat as Y  # noqa: E402
from medya.ortak import ffmpeg, probe, video_akisi  # noqa: E402

BURA = Path(__file__).parent
FF = ffmpeg()
ASIL = Y._kirp_olcek
CUBUK = ["beyaz75", "sari", "camgobegi", "yesil", "eflatun", "kirmizi", "mavi"]
ETIKETSIZ = ["-bsf:v", "h264_metadata=matrix_coefficients=2:colour_primaries=2:transfer_characteristics=2"]


def ff(*a):
    subprocess.run([FF, "-nostdin", "-v", "error", "-y", *a], check=True)


def duzlemler(yol, w, h, vf=None):
    """Bütün kareler, ham yuv420p: [(Y, U, V), …]."""
    k = [FF, "-nostdin", "-v", "error", "-i", str(yol)] + (["-vf", vf] if vf else [])
    b = subprocess.run(k + ["-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], capture_output=True, check=True).stdout
    b = np.frombuffer(b, np.uint8).astype(float)
    n, y, c = w * h * 3 // 2, w * h, w * h // 4
    return [(b[i:i + y], b[i + y:i + y + c], b[i + y + c:i + n]) for i in range(0, len(b), n)]


def gri(yol, w, h, on=""):
    """Sınamadaki _kareler: scale=w:h:flags=area,format=gray."""
    r = subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(yol), "-vf", f"{on}scale={w}:{h}:flags=area,format=gray",
                        "-fps_mode", "passthrough", "-f", "rawvideo", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, h, w).astype(float)


def psnr(a, b):
    return float(10 * np.log10(255 ** 2 / max(np.mean((a - b) ** 2), 1e-9)))


def karsilastir(cikti, ref, ciftler):
    s = {}
    for j, d in enumerate("YUV"):
        p = [psnr(cikti[i][j], ref[k][j]) for i, k in ciftler]
        s[d] = {"ort": round(float(np.mean(p)), 2), "en_kotu": round(min(p), 2)}
    return s


def hf_rgb(yol, w, h):
    """İlk kare, HyperFrames'in göreceği RGB (h x w x 3)."""
    v = video_akisi(probe(yol))
    m, on = v.get("color_space"), ""
    if not m or m == "unknown":
        hd = int(v["height"]) >= 720 and v["codec_name"] not in ("vp9", "av1")
        on = f"setparams=colorspace={'bt709' if hd else 'smpte170m'},"
    b = subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(yol), "-vf", f"{on}scale={w}:{h}:flags=area,format=rgb24",
                        "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(b, np.uint8).reshape(h, w, 3).astype(float)


def cubuklar(rgb):
    """smptehdbars üst bölümündeki 7 çubuğun ortası (1280 genişlikte çubuk 138 px, ilk çubuk x=160'ta)."""
    h, w, _ = rgb.shape
    s = {}
    for i, ad in enumerate(CUBUK):
        x, y = round((229 + 138 * i) / 1280 * w), round(210 / 720 * h)
        dx, dy = max(1, round(30 / 1280 * w)), max(1, round(80 / 720 * h))
        s[ad] = [round(float(c)) for c in rgb[y - dy:y + dy, x - dx:x + dx].reshape(-1, 3).mean(0)]
    return s


def eski(kirp, olcek, gorunen, *_):
    """O3 ilk hâli: scale'in giriş matrisi verilmez ('auto')."""
    return [re.sub(r":in_color_matrix=\w+", "", f) for f in ASIL(kirp, olcek, gorunen)]


def sdr(t):
    kaynaklar = {
        "etiketsiz_1280x720": ("1280x720", ETIKETSIZ),
        "bt709_1280x720": ("1280x720", ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]),
        "smpte170m_1280x720": ("1280x720", ["-colorspace", "smpte170m", "-color_primaries", "smpte170m",
                                            "-color_trc", "smpte170m"]),
        "etiketsiz_640x360": ("640x360", ETIKETSIZ),
    }
    sonuc = {}
    for ad, (boyut, etiket) in kaynaklar.items():
        w, h = (int(n) for n in boyut.split("x"))
        k = t / f"{ad}.mp4"
        ff("-f", "lavfi", "-i", f"smptehdbars=s={boyut}:r=60:d=0.5", "-c:v", "libx264", "-crf", "10", "-preset",
           "ultrafast", "-pix_fmt", "yuv420p", *etiket, str(k))
        hk = hf_rgb(k, w // 2, h // 2)
        kayit = {"kaynak_matris": video_akisi(probe(k)).get("color_space") or "yok",
                 "giris_matrisi_bugun": Y._giris_matrisi(Y.incele_dosya(str(k))["video"]),
                 "hf_cubuk_kaynak": cubuklar(hk)}
        for varyant, olcek in (("olceksiz", None), ("olcek_eski", f"{w // 2}x{h // 2}"),
                               ("olcek_bugun", f"{w // 2}x{h // 2}")):
            Y._kirp_olcek = eski if varyant == "olcek_eski" else ASIL
            try:
                c = t / f"{ad}_{varyant}.mp4"
                r = Y.yavaslat(str(k), str(c), 0.5, olcek=olcek)
            finally:
                Y._kirp_olcek = ASIL
            ow, oh = (w, h) if olcek is None else (w // 2, h // 2)
            cik = duzlemler(c, ow, oh)
            duz = duzlemler(k, ow, oh, f"scale={ow}:{oh}:flags=lanczos")
            cev = duzlemler(k, ow, oh, f"scale={ow}:{oh}:flags=lanczos:in_color_matrix=bt601:out_color_matrix=bt709:"
                                       "out_range=tv")
            ciftler = [(i, i) for i in range(min(len(cik), len(duz)))]
            hc = hf_rgb(c, w // 2, h // 2)
            fark = np.abs(hc - hk)
            kayit[varyant] = {"yontem": r["yontem"], "kare": len(cik), "cikti_matris": video_akisi(probe(c)).get("color_space"),
                              "psnr_duz": karsilastir(cik, duz, ciftler), "psnr_601_709": karsilastir(cik, cev, ciftler),
                              "hf_fark_ort": round(float(fark.mean()), 2), "hf_fark_en_cok": int(fark.max()),
                              "hf_cubuk": cubuklar(hc)}
        sonuc[ad] = kayit
        print(ad, json.dumps(kayit, ensure_ascii=False), flush=True)
    return sonuc


def hdr(t):
    src = KOK / "testler/veri/hdr_hlg.mp4"
    ton = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv,format=yuv420p,crop=320:360:160:0,scale=160:180:flags=lanczos")
    ref, ref_gri = duzlemler(src, 160, 180, ton), gri(src, 160, 180, ton + ",")
    ayar = r"(:in_color_matrix=\w+)?:out_color_matrix=bt709:out_range=tv"
    varyantlar = {
        "ayarsiz": lambda f: re.sub(ayar + r",setparams=colorspace=bt709:range=tv", "", f),
        "ayarli_setparams_yok": lambda f: re.sub(r":in_color_matrix=\w+", "", f).replace(
            ",setparams=colorspace=bt709:range=tv", ""),
        "bugun": lambda f: f,
    }
    sonuc = {}
    for yol, kw in (("dogal", {"fps": 15}), ("ara", {"yontem": "ffmpeg"})):
        for ad, donustur in varyantlar.items():
            Y._kirp_olcek = lambda *a, _d=donustur: [_d(f) for f in ASIL(*a)]
            try:
                c = t / f"hdr_{yol}_{ad}.mov"
                r = Y.yavaslat(str(src), str(c), 0.5, kirp="160,0,320,360", olcek="160x180", **kw)
            finally:
                Y._kirp_olcek = ASIL
            cik, cik_gri = duzlemler(c, 160, 180), gri(c, 160, 180)
            adim = 1 if yol == "dogal" else 2
            ciftler = [(adim * j, j) for j in range(len(ref) - (adim - 1)) if adim * j < len(cik)]
            sonuc[f"{yol}_{ad}"] = {
                "yontem": r["yontem"], "kare": len(cik), "cikti_matris": video_akisi(probe(c)).get("color_space"),
                "psnr": karsilastir(cik, ref, ciftler),
                "sinama_olcutu_gri_en_kotu": round(min(psnr(cik_gri[i], ref_gri[k]) for i, k in ciftler), 2)}
            print(yol, ad, json.dumps(sonuc[f"{yol}_{ad}"], ensure_ascii=False), flush=True)
    return sonuc


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        sonuc = {"ffmpeg": subprocess.run([FF, "-version"], capture_output=True, text=True).stdout.split("\n")[0],
                 "sdr": sdr(t), "hdr": hdr(t)}
    (BURA / "olc_renk.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1))
