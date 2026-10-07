"""medya gorsel-uret "<istem>" --cikti x.png [--boyut 1024x1024] [--adim 4] [--tohum 7] [--adet 1] [--referans a.png …]

Yerel görsel üretimi ve referanslı düzenleme: FLUX.2 [klein] 4B (Black Forest Labs; ağırlık Apache-2.0 — iş için
uygun), mflux-community Q4 (4,6 GB, sabit sürüm 794cd15), mflux 0.21.0 (MLX, MIT). Çevrimdışı çalışır.
Ölçüm (2026-10-07, bu Mac): 1024×1024, 4 adım ~84 sn (model yükleme dahil), bellek tepesi 8,8 GB; referanslı
düzenleme ~176 sn, 8,9 GB. Çalışırken başka ağır iş (çizim, ML) açma: 16 GB RAM'de pay az.

--referans: verilen görsel(ler)den düzenleme/çoklu referans (ürünü yeni sahneye koy, arka planı değiştir, ışık).
Kişilerde kimlik korunmaz → gerçek kişilerin yüzünü değiştirme; gerçek kişiyi/markayı taklit eden görsel üretme.
İstem İngilizce en iyi çalışır. Görselde yazı istenirse metni kullanıcı verir, üretimden sonra büyütüp okunur
(model harf hatası yapar). Her çıktının yanında <ad>.json: istem, tohum, model, sürüm, lisans, süre — yeniden üretim
için. Görselin kalitesi ÖLÇÜLMEZ: Read ile açıp bak; istenirse `medya analiz` estetik puanı.
"""
from __future__ import annotations

import time
from datetime import date
from pathlib import Path

from ..ortak import ARAC, KOK, MedyaHatasi, calistir, disk_bekcisi, json_yaz

MODEL = (KOK / "modeller" / "hf" / "hub" / "models--mflux-community--flux2-klein-4b-mflux-q4" / "snapshots"
         / "794cd159538149ad9830848508c31f0ea7088e58")
URET, DUZENLE = ARAC / "mflux-generate-flux2", ARAC / "mflux-generate-flux2-edit"
LISANS = "FLUX.2 [klein] 4B: Apache-2.0 (Qwen3-4B metin kodlayıcı dahil); mflux: MIT"


def gorsel_uret(istem: str, cikti: str, *, boyut: str = "1024x1024", adim: int = 4, tohum: int = 7,
                adet: int = 1, referans: list[str] | None = None) -> list[dict]:
    if not MODEL.exists() or not URET.exists():
        raise MedyaHatasi("FLUX.2 klein ya da mflux yok: medya kur flux2-klein")
    disk_bekcisi(3.0, "görsel üretimi (FLUX.2 ~9 GB bellek)")
    try:
        g, y = (int(v) for v in boyut.lower().split("x"))
    except ValueError as e:
        raise MedyaHatasi("--boyut GxY olmalı, ör. 1024x1024 (16'nın katları)") from e
    if g % 16 or y % 16:
        raise MedyaHatasi("genişlik ve yükseklik 16'nın katı olmalı")
    for r in referans or []:
        if not Path(r).exists():
            raise MedyaHatasi(f"referans yok: {r}")
    c = Path(cikti)
    c.parent.mkdir(parents=True, exist_ok=True)
    sonuc = []
    for i in range(adet):
        hedef = c if adet == 1 else c.with_name(f"{c.stem}-{i + 1}{c.suffix}")
        komut = [str(DUZENLE if referans else URET), "--model", str(MODEL), "--base-model", "flux2-klein-4b",
                 "--prompt", istem, "--width", str(g), "--height", str(y), "--steps", str(adim),
                 "--seed", str(tohum + i), "--low-ram", "--no-exif", "--output", str(hedef)]
        if referans:
            komut += ["--image-paths", *referans]
        t = time.perf_counter()
        calistir(komut, hata_mesaji="görsel üretimi başarısız")
        kayit = {"cikti": str(hedef), "istem": istem, "tohum": tohum + i, "boyut": [g, y], "adim": adim,
                 "referans": referans or [], "model": "FLUX.2 [klein] 4B Q4 (mflux-community, 794cd15)",
                 "lisans": LISANS, "sure_sn": round(time.perf_counter() - t, 1), "tarih": date.today().isoformat()}
        json_yaz(hedef.with_suffix(".json"), kayit)
        sonuc.append(kayit)
    return sonuc


def calistir_(args) -> int:
    for r in gorsel_uret(args.istem, args.cikti, boyut=args.boyut, adim=args.adim, tohum=args.tohum,
                         adet=args.adet, referans=args.referans):
        print(f"{r['cikti']}  ({r['boyut'][0]}x{r['boyut'][1]}, tohum {r['tohum']}, {r['sure_sn']} sn)")
    print("  kalite ölçülmez: görsele bak (Read). Yazı istendiyse büyütüp harf harf oku.")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="metinden ya da referans görselden görsel üretir (FLUX.2 klein 4B, yerel)",
                       description=__doc__.split("\n\n")[0])
    p.add_argument("istem", help="görsel tarifi (İngilizce en iyi)")
    p.add_argument("--cikti", required=True, help="PNG yolu (yanına .json üretim kaydı)")
    p.add_argument("--boyut", default="1024x1024", help="GxY, 16'nın katları (ör. 1080x1920 değil 1088x1920)")
    p.add_argument("--adim", type=int, default=4, help="çıkarım adımı (klein 4 adımda damıtılmış)")
    p.add_argument("--tohum", type=int, default=7, help="aynı tohum + istem = aynı görsel")
    p.add_argument("--adet", type=int, default=1, help="farklı tohumlarla kaç seçenek")
    p.add_argument("--referans", nargs="+", help="düzenleme/çoklu referans: kaynak görsel(ler)")
    p.set_defaults(islev=calistir_)
