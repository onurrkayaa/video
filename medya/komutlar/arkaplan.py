"""medya arkaplan-sil <resim> [--kirp] [--maske] — arka planı siler, şeffaf PNG yazar (Apple Vision ön plan maskesi).

İndirme yok, macOS'ta yerleşik. Kişi, hayvan ve belirgin nesnelerde iyi; saç teli, kürk, cam ve duman gibi zor
kenarlarda daha ağır yöntemlere bak (gorsel-uretim becerisi). Sonucu her zaman Read ile açıp kenarlara bak.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..ortak import ARAC, MedyaHatasi, apple_calistir

APPLE = ARAC / "medya-apple"


def arkaplan_sil(girdi: str, cikti: str, *, kirp: bool = False, maske: str | None = None) -> dict:
    if not APPLE.exists():
        raise MedyaHatasi("arac/medya-apple yok; derle: medya kur medya-apple")
    if not cikti.lower().endswith(".png"):
        raise MedyaHatasi("şeffaflık için çıktı .png olmalı")
    komut = [str(APPLE), "arkaplan-sil", girdi, cikti]
    if kirp:
        komut += ["--kirp", "evet"]
    if maske:
        komut += ["--maske", maske]
    s = apple_calistir(komut, zaman_asimi=180, hata_mesaji="arka plan silinemedi")
    return json.loads(s.stdout.decode().strip().splitlines()[-1])


def calistir_(args) -> int:
    g = Path(args.girdi)
    cikti = args.cikti or str(g.with_name(g.stem + "-seffaf.png"))
    maske = str(g.with_name(g.stem + "-maske.png")) if args.maske else None
    r = arkaplan_sil(args.girdi, cikti, kirp=args.kirp, maske=maske)
    print(f"{r['ornek_sayisi']} ön plan örneği, {r['boyut']} → {cikti}" + (f" (maske: {maske})" if maske else ""))
    print("  kenarları kontrol et: Read ile aç (saç/kürk/cam zor kenarlardır)")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="arka planı sil (şeffaf PNG, Apple Vision)")
    p.add_argument("girdi")
    p.add_argument("--kirp", action="store_true", help="ön planın sınırlarına kırp")
    p.add_argument("--maske", action="store_true", help="siyah-beyaz maskeyi de yaz")
    p.add_argument("--cikti", help="varsayılan <ad>-seffaf.png")
    p.set_defaults(islev=calistir_)
