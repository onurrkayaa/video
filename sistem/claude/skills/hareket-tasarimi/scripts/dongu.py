"""dongu.py — döngülü hareketli görsel denetimi (GIF / animasyonlu WebP / APNG).

Çalıştır: source /Users/onurkaya/Projects/video/ortam.sh && $MEDYA/.venv/bin/python <beceri>/scripts/dongu.py X.gif [--kb 3000] [--fps 20] [--opak] [--tek-sefer]
Ölçer: bayt, boyut, kare sayısı, kare gecikmeleri, döngü sayısı (0 = sonsuz), alfa,
dikiş (döngüde): son→ilk kare farkı ile ardışık karelerin ortanca farkı. Çıkış 0 = geçti, 1 = kaldı.
Gecikme: kodlayıcılar aynı ardışık kareleri birleştirir (bekleme), agg değişken gecikme yazar; bu yüzden eşitlik
değil, her gecikmenin taban gecikmenin (en küçüğü ya da 1000/--fps) tam katı olması denetlenir.
"""
import argparse, os, statistics, sys
from PIL import Image, ImageChops, ImageSequence, ImageStat


def fark(a, b):
    """Ortalama mutlak fark (0–255); saydam pikseller sabit bir zemine bindirilerek karşılaştırılır."""
    def zemin(k):
        z = Image.new("RGBA", k.size, (255, 0, 255, 255))
        z.alpha_composite(k)
        return z.convert("RGB")
    return sum(ImageStat.Stat(ImageChops.difference(zemin(a), zemin(b))).mean) / 3


ap = argparse.ArgumentParser()
ap.add_argument("dosya")
ap.add_argument("--kb", type=float, help="bayt bütçesi (KB); aşılırsa KALDI")
ap.add_argument("--fps", type=float, help="beklenen fps: taban gecikme 1000/fps")
ap.add_argument("--opak", action="store_true", help="saydam piksel varsa KALDI (README GIF'i gibi)")
ap.add_argument("--tek-sefer", action="store_true", help="döngü değil (ör. sonda tutulan terminal demosu): dikiş ölçülmez")
a = ap.parse_args()

im = Image.open(a.dosya)
kareler, gecikme = [], []
for k in ImageSequence.Iterator(im):
    kareler.append(k.convert("RGBA"))  # önce çöz: WebP gecikmeyi çözünce yazar
    gecikme.append(k.info.get("duration"))
dongu = im.info.get("loop")
alfa = any(k.getextrema()[3][0] < 255 for k in kareler)
adim = [fark(kareler[i], kareler[i + 1]) for i in range(len(kareler) - 1)]
dikis = fark(kareler[-1], kareler[0]) if len(kareler) > 1 else 0.0
ortanca = statistics.median(adim) if adim else 0.0
kb = os.path.getsize(a.dosya) / 1024

sorun, bilgi = [], []
if None in gecikme or not gecikme or min(gecikme) <= 0:
    sorun.append(f"gecikme okunamadı ya da 0: {gecikme[:5]}…")
else:
    taban = 1000 / a.fps if a.fps else min(gecikme)
    if im.format == "GIF" and round(taban) % 10:
        sorun.append(f"taban gecikme {taban:g} ms: GIF 10 ms birimlidir → 10/20/25/50 fps")
    kat = [d / taban for d in gecikme]
    if any(abs(k - round(k)) > 0.02 or round(k) < 1 for k in kat):
        sorun.append(f"gecikmeler taban {taban:g} ms'nin tam katı değil {sorted(set(gecikme))} ms (ör. 15 fps → 60/70 karışık)")
    bek = [d for d in gecikme if d > taban * 1.02]
    if bek:
        bilgi.append(f"{len(bek)} bekleme, toplam {sum(bek) / 1000:.2f} sn (birleşmiş aynı kareler)")
if dongu not in (0, None) or (dongu is None and im.format == "GIF"):
    sorun.append(f"sonsuz döngü değil (loop={dongu})")
if a.opak and alfa:
    sorun.append("saydam piksel var: arka planı #root'a ver (body arka planı saydam çıkar)")
if a.tek_sefer:
    pass
elif len(kareler) > 1 and dikis <= 0.1 * ortanca:
    if (gecikme[0] > min(gecikme) * 1.02 or gecikme[-1] > min(gecikme) * 1.02):
        bilgi.append("son kare ≈ ilk kare, ama dikişte bekleme var: bilinçli dinlenme pozuysa sorun değil, izleyerek doğrula")
    else:
        sorun.append("son kare = ilk kare: döngüde 1 kare takılır (süre tam bir periyot, son kare T-1/fps olmalı)")
elif ortanca > 0 and dikis > 2 * ortanca:
    sorun.append(f"dikiş sıçraması: son→ilk {dikis:.2f} > 2 × ortanca adım {ortanca:.2f}")
if a.kb and kb > a.kb:
    sorun.append(f"bütçe aşıldı: {kb:.0f} KB > {a.kb:.0f} KB")

print(f"{a.dosya}: {im.format} {im.size[0]}x{im.size[1]}, {len(kareler)} kare, gecikme {sorted(set(gecikme))} ms, "
      f"loop={dongu}, alfa={'var' if alfa else 'yok'}, {kb:.1f} KB, dikiş {dikis:.2f} / ortanca adım {ortanca:.2f}")
for b in bilgi:
    print("·", b)
for s in sorun:
    print("✗", s)
print("KALDI" if sorun else "GEÇTİ")
sys.exit(1 if sorun else 0)
