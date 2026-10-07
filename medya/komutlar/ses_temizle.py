"""medya ses-temizle <ses|video> [--siddet 12] [--cikti x.wav|x.mp4] — konuşmadaki gürültüyü azaltır (DeepFilterNet3).

Rüzgâr, kalabalık, uğultu, oda sesi. Yerel, MIT/Apache-2.0, ~28 MB ikili (arac/deep-filter), model içinde.
Ölçüm (2026-10-05, gürültülü Türkçe konuşma + bilinen temiz kayıt):
  sınırsız bastırma  SI-SDR 1,8 → 12,5 dB ama Whisper anlaşılırlığı 12/15 → 10/15 (konuşma bozuldu)
  --siddet 12 dB     SI-SDR 1,8 → 10,1 dB ve anlaşılırlık 12/15 → 13/15  ← varsayılan
  -D olmadan çıktı 30 ms GECİKİR (dudak senkronu bozulur); bu komut -D'yi daima verir ve gecikmeyi ölçer.
Tek bir sınamadır: her klipte `--dogrula` ile Whisper anlaşılırlığını önce/sonra karşılaştır.
"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

from ..ortak import ARAC, MedyaHatasi, calistir, ffmpeg, probe, ses_gecikmesi, video_akisi

DF = ARAC / "deep-filter"
VIDEO_UZANTI = {".mp4", ".mov", ".m4v", ".mkv"}


def ses_temizle(girdi: str, cikti: str, siddet: float = 12.0) -> dict:
    if not DF.exists():
        raise MedyaHatasi("arac/deep-filter yok; kur: medya kur deepfilternet")
    with tempfile.TemporaryDirectory() as g:
        ham = Path(g) / "girdi.wav"
        calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", girdi, "-vn", "-ac", "1", "-ar", "48000",
                  "-c:a", "pcm_s16le", str(ham)], hata_mesaji="ses çözülemedi")
        calistir([str(DF), "-D", "-a", f"{siddet:g}", "-o", g + "/c", str(ham)], hata_mesaji="deep-filter başarısız")
        temiz = Path(g) / "c" / "girdi.wav"
        gecikme = ses_gecikmesi(ham, temiz, sure=min(20.0, float(probe(str(ham))["format"]["duration"])))
        hedef = Path(cikti)
        if hedef.suffix.lower() in VIDEO_UZANTI and video_akisi(probe(girdi)):
            vsure = float(probe(girdi)["format"]["duration"])      # -shortest sondan kare kesiyordu (553 → 549)
            calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", girdi, "-i", str(temiz), "-map", "0:v:0", "-map", "1:a:0",
                      "-c:v", "copy", "-af", "apad", "-c:a", "aac", "-b:a", "256k", "-t", f"{vsure:.6f}",
                      "-movflags", "+faststart", str(hedef)], hata_mesaji="video ile birleştirilemedi")
        else:
            calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", str(temiz), "-c:a", "pcm_s24le", str(hedef)])
    return {"cikti": str(hedef), "siddet_db": siddet, "gecikme": gecikme}


def anlasilirlik(yol: str) -> str:
    from .yaziya_dok import yaziya_dok
    return yaziya_dok(yol, dil="tr")["metin"]


def calistir_(args) -> int:
    g = Path(args.girdi)
    cikti = args.cikti or str(g.with_name(g.stem + "-temiz" + (g.suffix if g.suffix.lower() in VIDEO_UZANTI else ".wav")))
    if Path(cikti).resolve() == g.resolve():
        raise MedyaHatasi("çıktı girdinin üzerine yazamaz")
    r = ses_temizle(args.girdi, cikti, args.siddet)
    gk = r["gecikme"].get("gecikme_ms")
    print(f"gürültü azaltıldı (sınır {args.siddet:g} dB) → {cikti}; gecikme {gk} ms" + (" ✓" if gk is not None and abs(gk) <= 1 else " ⚠"))
    if args.dogrula:
        once, sonra = anlasilirlik(args.girdi), anlasilirlik(cikti)
        print(f"  önce : {once[:160]}\n  sonra: {sonra[:160]}")
        print("  sonrası daha kötü okunuyorsa --siddet'i düşür (ör. 8) ya da temizlemeyi atla")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="konuşmadaki gürültüyü azalt (DeepFilterNet3)")
    p.add_argument("girdi")
    p.add_argument("--siddet", type=float, default=12.0, help="en çok bastırma (dB); yüksek değer konuşmayı bozabilir")
    p.add_argument("--dogrula", action="store_true", help="Whisper ile önce/sonra anlaşılırlığı karşılaştır")
    p.add_argument("--cikti", help=".wav (yalnız ses) ya da .mp4/.mov (görüntü kopyalanır, ses değişir)")
    p.set_defaults(islev=calistir_)
