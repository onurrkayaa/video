"""ciz'in çözücüsü gerçek açık GOP'lu HEVC'de (B kare, 4 sn GOP) tam kareyi mi veriyor? Tam çözümün kare özetleriyle
karşılaştırma (yalnız sayısal; kare açılmaz). Anahtar kareden hemen önceki kareler (248, 249, …) dahil."""
import hashlib, subprocess, sys
from pathlib import Path
K = Path("/Users/onurkaya/Projects/video")
sys.path.insert(0, str(K))
from medya.komutlar.ciz import plani_hazirla
Y = K / "projeler/2026-10-05-deniz-kenari-deneme/kaynak/IMG_4021.MOV"
tam = [l.split(",")[-1].strip() for l in subprocess.run(
    [str(K / "arac/ffmpeg"), "-nostdin", "-v", "error", "-i", str(Y), "-map", "0:v:0", "-pix_fmt", "yuv420p",
     "-fps_mode", "passthrough", "-f", "framemd5", "-"], capture_output=True, text=True, check=True).stdout.splitlines()
       if l and not l.startswith("#")]
print("tam çözüm kare:", len(tam))
hata = 0
for i0 in (0, 1, 100, 247, 248, 249, 250, 251, 498, 499, 500, 997, 998, 999, 1000, 1247, 1248, 1249, 1430):
    plan = {"fps": 60, "boyut": [4096, 2160], "cekimler": [
        {"no": 1, "kaynak": str(Y), "kaynak_bas": i0 / 60, "cikti_bas": 0, "cikti_son": 5 / 60, "hiz": 1, "ses": "sessiz"}]}
    P = plani_hazirla(plan, K)
    x = P.cekimler[0]
    x.baslat()
    oz = [hashlib.md5(x.sonraki()).hexdigest() for _ in range(5)]
    x.kapat()
    bek = tam[i0:i0 + 5]
    if oz != bek:
        hata += 1
        print("UYUMSUZ", i0, [tam.index(o) if o in tam else None for o in oz])
print("uyumsuz:", hata)
