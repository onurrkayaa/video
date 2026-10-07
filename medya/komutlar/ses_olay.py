"""medya ses-olay <video|ses> [--pencere 1.0] — ses olayları: kahkaha, alkış, tezahürat, konuşma, şarkı, müzik…

Apple SoundAnalysis yerleşik sınıflandırıcısı (303 sınıf; indirme yok). Duygusal anları bulmak (gülüşmeler,
alkış), konuşmalı çekimleri ayırmak (J/L kesim, müzik kısma) ve sessiz/ortam sesli bölümleri seçmek için.
Çıktı: pencere başına ilk sınıflar + ilgi çekici olayların birleşik zaman aralıkları.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from ..ortak import ARAC, MedyaHatasi, apple_calistir, calistir, ffmpeg, json_oku, json_yaz

APPLE = ARAC / "medya-apple"
ILGINC = {"laughter": "kahkaha", "giggling": "kıkırdama", "belly_laugh": "kahkaha", "baby_laughter": "bebek kahkahası",
          "applause": "alkış", "cheering": "tezahürat", "crowd": "kalabalık", "speech": "konuşma",
          "whispering": "fısıltı", "singing": "şarkı", "music": "müzik", "crying_sobbing": "ağlama",
          "kiss": "öpücük", "dog_bark": "köpek", "silence": "sessizlik", "wind": "rüzgâr", "water": "su",
          "ocean": "deniz", "fireworks": "havai fişek"}


def olaylar(pencereler: list[dict], esik: float = 0.35) -> list[dict]:
    """Aynı sınıfın ardışık pencerelerini birleştirir."""
    aktif: dict[str, dict] = {}
    sonuc = []
    for p in pencereler:
        bulunan = {ad: g for ad, g in p["siniflar"] if ad in ILGINC and g >= esik}
        for ad in list(aktif):
            if ad not in bulunan:
                sonuc.append(aktif.pop(ad))
        for ad, g in bulunan.items():
            if ad in aktif:
                aktif[ad]["son"] = p["son"]; aktif[ad]["en_yuksek"] = max(aktif[ad]["en_yuksek"], g)
            else:
                aktif[ad] = {"olay": ILGINC[ad], "sinif": ad, "bas": p["bas"], "son": p["son"], "en_yuksek": g}
    sonuc += aktif.values()
    return sorted(sonuc, key=lambda o: o["bas"])


def calistir_(args) -> int:
    if not APPLE.exists():
        raise MedyaHatasi("arac/medya-apple yok; derle: medya kur medya-apple")
    cikti = Path(args.cikti or str(Path(args.girdi).with_suffix("")) + "-ses-olay.json")
    with tempfile.TemporaryDirectory() as g:
        wav = Path(g) / "s.wav"
        calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", args.girdi, "-vn", "-ac", "1", "-ar", "16000", str(wav)],
                 hata_mesaji="ses çözülemedi")
        ham = Path(g) / "h.json"
        apple_calistir([str(APPLE), "ses-olay", str(wav), str(ham), "--pencere", f"{args.pencere:g}"],
                       zaman_asimi=180 + Path(wav).stat().st_size / 32000 / 5, hata_mesaji="ses analizi başarısız")
        veri = json_oku(ham)
    veri["kaynak"] = args.girdi
    veri["olaylar"] = olaylar(veri["pencereler"], args.esik)
    json_yaz(cikti, veri)
    ozet = {}
    for o in veri["olaylar"]:
        ozet[o["olay"]] = ozet.get(o["olay"], 0) + (o["son"] - o["bas"])
    print(f"{len(veri['pencereler'])} pencere; olaylar: " + (", ".join(f"{k} {v:.1f} sn" for k, v in sorted(ozet.items(), key=lambda x: -x[1])) or "yok"))
    for o in [o for o in veri["olaylar"] if o["sinif"] in ("laughter", "giggling", "belly_laugh", "applause", "cheering")][:10]:
        print(f"  {o['olay']}: {o['bas']:.1f}–{o['son']:.1f} sn (en yüksek {o['en_yuksek']:.2f})")
    print(f"→ {cikti}")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="ses olayları (kahkaha, alkış, konuşma, müzik…)")
    p.add_argument("girdi")
    p.add_argument("--pencere", type=float, default=1.0, help="analiz penceresi (sn)")
    p.add_argument("--esik", type=float, default=0.35, help="olay sayma güven eşiği")
    p.add_argument("--cikti")
    p.set_defaults(islev=calistir_)
