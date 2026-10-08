"""1x 4K HEVC çekimin HyperFrames çiziminde kare başına geçici alanı (2026-10-08 düzeltme turu: dersler.md'deki
"1x 4K HEVC PNG'de 11,82 MB/kare" sayısının betiği ve JSON'u yoktu).

Kaynak: deneme IMG_4021.MOV (4096x2160 HEVC Main 8 bit, bt709, 60 fps, 24 sn). HyperFrames 0.8.140'ın çıkarma ayarları
(extractVideoFramesRange, chunk-TPECLKPA.js:11468; olc_hf.py ile aynı) diske yazmadan borudan: -noaccurate_seek -ss -t,
30 fps, SDR geçiş süzgeci; PNG -compression_level 1 (son çizim, --video-frame-format png) ve JPEG -q:v 2 (taslak,
bt601 tam aralık süzgeciyle). HEVC alfa kodeği sayılmaz, biçim isteğe göre (resolveFrameFormat :11844). Bütün klip 3 sn'lik
8 kesitte; kare sayısı akıştaki PNG/JPEG imzalarından sayılır. Gerçek HyperFrames çizimi yapılmadı. Kareler açılmadı
(yalnız bayt sayıldı)."""
import json
import subprocess
import sys
from pathlib import Path

KOK = Path("/Users/onurkaya/Projects/video")
sys.path.insert(0, str(KOK))
from medya.ortak import ffmpeg  # noqa: E402

BURA = Path(__file__).parent
FF = ffmpeg()
DEN = KOK / "projeler/2026-10-05-deniz-kenari-deneme/kaynak/IMG_4021.MOV"
SDR = "setparams=color_primaries=bt709:color_trc=iec61966-2-1"
JPG = "scale=flags=neighbor,format=gbrp,scale=out_color_matrix=bt601:out_range=pc:flags=neighbor,format=yuv420p"
IMZA = {"png": b"\x89PNG\r\n\x1a\n", "jpg": b"\xff\xd8\xff"}


def cikar(bas, sure, bicim):
    k = [FF, "-nostdin", "-v", "error", "-noaccurate_seek", "-ss", str(bas), "-i", str(DEN), "-t", str(sure), "-vf",
         ",".join(["settb=intb/2", "setpts=PTS-lte(TB\\,0.001)", "fps=30:start_time=0:round=up", SDR]
                  + ([JPG] if bicim == "jpg" else []))]
    k += ["-q:v", "2" if bicim == "jpg" else "0"] + (["-compression_level", "1"] if bicim == "png" else [])
    k += ["-f", "image2pipe", "-c:v", "png" if bicim == "png" else "mjpeg", "-"]
    p = subprocess.Popen(k, stdout=subprocess.PIPE)
    toplam, kare, kuyruk, imza = 0, 0, b"", IMZA[bicim]
    while True:
        b = p.stdout.read(1 << 22)
        if not b:
            break
        toplam += len(b)
        parca = kuyruk + b
        kare += parca.count(imza)
        kuyruk = parca[-(len(imza) - 1):]
    if p.wait():
        raise SystemExit(f"ffmpeg hata verdi: {bas} sn, {bicim}")
    return toplam, kare


sonuc = {"kaynak": "IMG_4021.MOV 4096x2160 HEVC 8 bit bt709 60 fps", "kesitler": []}
for bas in range(0, 24, 3):
    kayit = {"bas_sn": bas, "sure_sn": 3}
    for bicim in ("png", "jpg"):
        bayt, kare = cikar(bas, 3, bicim)
        kayit[f"{bicim}_kare"] = kare
        kayit[f"{bicim}_mb_kare"] = round(bayt / kare / 1e6, 3)
    sonuc["kesitler"].append(kayit)
    print(kayit, flush=True)
for bicim in ("png", "jpg"):
    d = [k[f"{bicim}_mb_kare"] for k in sonuc["kesitler"]]
    n = [k[f"{bicim}_kare"] for k in sonuc["kesitler"]]
    ort = sum(a * b for a, b in zip(d, n)) / sum(n)
    sonuc[bicim] = {"mb_kare_en_az": min(d), "mb_kare_en_cok": max(d), "mb_kare_ort": round(ort, 3),
                    "237_kare_gb_ort": round(ort * 237 / 1e3, 2)}   # denemede zaman çizelgesindeki ağır çekim karesi
(BURA / "olc_1x4k.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1))
print(json.dumps({b: sonuc[b] for b in ("png", "jpg")}, ensure_ascii=False))
