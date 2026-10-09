"""medya gorsel-uret "<istem>" --cikti x.png [--model flux2|z-image] [--boyut GxY] [--adim N] [--tohum 7]
                     [--adet 1] [--referans a.png …]

Yerel görsel üretimi ve referanslı düzenleme. İki model; ikisinin de ağırlığı Apache-2.0 (iş için uygun), mflux 0.21.0
(MLX, MIT), çevrimdışı çalışır:
- `flux2` (varsayılan): FLUX.2 [klein] 4B (Black Forest Labs), mflux-community Q4 (4,6 GB, sabit sürüm 794cd15),
  4 adım. Metinden görsel ve referanslı düzenleme. 1024² 83–107 sn (model yükleme dahil), bellek tepesi 9,0–10,8 GB
  (A/B 2026-10-08); düzenleme ~176 sn (2026-10-07).
- `z-image`: Z-Image-Turbo 6B (Tongyi-MAI), mflux-community Q4 (5,9 GB, sabit sürüm f427e25), 9 adım. Yalnız metinden
  görsel. 1024² 275–383 sn (FLUX.2'nin 3,3–3,7 katı), bellek tepesi 6,3 GB. Aynı istem ve tohumlarla A/B'de
  İngilizce afiş yazısını harfi harfine doğru yazdı (2/2; FLUX.2 0/2); fotogerçekçilik farkı ölçülmedi (görseller:
  sistem/devam/ham/gorsel-ab/, kullanıcı bakar). Görselde İngilizce yazı gerekiyorsa ya da bellek darsa seç.
--model verilmezse kayıttaki sıra (yetenekler.toml → gorsel-uret: birincil, sonra yedek); birincil kurulu değilse ya
da üretimi başarısız olursa sıradakine uyarıyla düşer (açık --adim birincilindir; yedek kendi varsayılan adımıyla
koşar). Çalışırken başka ağır iş (çizim, ML) açma: 16 GB RAM'de pay az.

--referans: verilen görsel(ler)den düzenleme/çoklu referans (ürünü yeni sahneye koy, arka planı değiştir, ışık).
Her zaman FLUX.2: Z-Image'ın düzenleme modeli yok (Z-Image-Edit yayımlanmadı; HF Tongyi-MAI, 2026-10-08).
Kişilerde kimlik korunmaz → gerçek kişilerin yüzünü değiştirme; gerçek kişiyi/markayı taklit eden görsel üretme.
İstem İngilizce en iyi çalışır. Görselde yazı istenirse metni kullanıcı verir, üretimden sonra büyütüp okunur
(model harf hatası yapar). Her çıktının yanında <ad>.json: istem, tohum, sağlayıcı, model, sürüm, lisans, süre —
yeniden üretim için. Görselin kalitesi ÖLÇÜLMEZ: Read ile açıp bak; istenirse `medya analiz` estetik puanı.
"""
from __future__ import annotations

import time
from datetime import date
from pathlib import Path

from ..kayit import yukle
from ..ortak import ARAC, KOK, MedyaHatasi, calistir, disk_bekcisi, json_yaz, uyar

_HUB = KOK / "modeller" / "hf" / "hub"
# Sağlayıcı adı (yetenekler.toml) → yerel anlık görüntü: sabit commit'le inen modelde çevrimdışı repo adı çözülmez.
MODELLER = {
    "z-image-turbo": {
        "yol": _HUB / "models--mflux-community--z-image-turbo-mflux-q4" / "snapshots"
               / "f427e257d8e6ffa03edd4d9ac554a05809da456c",
        "uret": ARAC / "mflux-generate-z-image-turbo", "taban": "z-image-turbo", "adim": 9,
        "ad": "Z-Image-Turbo 6B Q4 (mflux-community, f427e25)",
        "lisans": "Z-Image-Turbo: Apache-2.0 (Tongyi-MAI); mflux: MIT"},
    "flux2-klein": {
        "yol": _HUB / "models--mflux-community--flux2-klein-4b-mflux-q4" / "snapshots"
               / "794cd159538149ad9830848508c31f0ea7088e58",
        "uret": ARAC / "mflux-generate-flux2", "duzenle": ARAC / "mflux-generate-flux2-edit",
        "taban": "flux2-klein-4b", "adim": 4, "ad": "FLUX.2 [klein] 4B Q4 (mflux-community, 794cd15)",
        "lisans": "FLUX.2 [klein] 4B: Apache-2.0 (Qwen3-4B metin kodlayıcı dahil); mflux: MIT"},
}
KISA = {"z-image": "z-image-turbo", "flux2": "flux2-klein"}


def model_sirasi(model: str | None = None, referans: list[str] | None = None) -> list[str]:
    """Denenecek sağlayıcılar, sırayla: --referans yalnız FLUX.2; --model tek; yoksa kaydın birincili + yedekleri."""
    if model is not None and model not in KISA:
        raise MedyaHatasi(f"bilinmeyen model: {model} (z-image | flux2)")
    if referans:
        if model == "z-image":
            raise MedyaHatasi("--referans (düzenleme) yalnız FLUX.2 klein'da: Z-Image'ın düzenleme modeli yok "
                              "(Z-Image-Edit yayımlanmadı). --model flux2 ver ya da --model'i kaldır.")
        return ["flux2-klein"]
    if model:
        return [KISA[model]]
    y = yukle()[0]["gorsel-uret"]
    return [y.saglayici, *y.yedek]


def _uret(ad: str, istem: str, c: Path, g: int, y: int, adim: int | None, tohum: int, adet: int,
          referans: list[str] | None) -> list[dict]:
    m = MODELLER[ad]
    adim = adim or m["adim"]
    sonuc = []
    for i in range(adet):
        hedef = c if adet == 1 else c.with_name(f"{c.stem}-{i + 1}{c.suffix}")
        komut = [str(m["duzenle"] if referans else m["uret"]), "--model", str(m["yol"]), "--base-model", m["taban"],
                 "--prompt", istem, "--width", str(g), "--height", str(y), "--steps", str(adim),
                 "--seed", str(tohum + i), "--low-ram", "--no-exif", "--output", str(hedef)]
        if referans:
            komut += ["--image-paths", *referans]
        t = time.perf_counter()
        calistir(komut, hata_mesaji=f"görsel üretimi başarısız ({ad})")
        kayit = {"cikti": str(hedef), "istem": istem, "tohum": tohum + i, "boyut": [g, y], "adim": adim,
                 "referans": referans or [], "saglayici": ad, "model": m["ad"], "lisans": m["lisans"],
                 "sure_sn": round(time.perf_counter() - t, 1), "tarih": date.today().isoformat()}
        json_yaz(hedef.with_suffix(".json"), kayit)
        sonuc.append(kayit)
    return sonuc


def _yedek_notu(ad: str, birincil: str, adim: int | None) -> str:
    """Açık --adim birincilindir (--model'siz çağrıda kayıttaki ilk model); yedek damıtıldığı kendi adım sayısıyla
    koşar (Z-Image 9; FLUX.2'nin 4'üyle değil). Uyarıya eklenecek not; adım verilmediyse ya da ad birincilse boş."""
    if adim is None or ad == birincil:
        return ""
    return f"; --adim {adim} {birincil} içindi, {ad} kendi varsayılanı {MODELLER[ad]['adim']} adımla koşuyor"


def gorsel_uret(istem: str, cikti: str, *, model: str | None = None, boyut: str = "1024x1024",
                adim: int | None = None, tohum: int = 7, adet: int = 1,
                referans: list[str] | None = None) -> list[dict]:
    sira = model_sirasi(model, referans)
    saglayicilar = yukle()[1]
    kurulu = [a for a in sira if saglayicilar[a].etkin and saglayicilar[a].kurulu_mu()]
    if not kurulu:
        raise MedyaHatasi(f"{sira[0]} ya da mflux kurulu değil: medya kur {sira[0]}")
    if kurulu[0] != sira[0]:
        uyar(f"{sira[0]} kurulu değil; {kurulu[0]} kullanılıyor (kurmak için: medya kur {sira[0]})"
             f"{_yedek_notu(kurulu[0], sira[0], adim)}")
    disk_bekcisi(3.0, "görsel üretimi (6–11 GB bellek)")
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
    adimi = {ad: adim if ad == sira[0] else None for ad in kurulu}     # yedek: kendi varsayılan adımı (_yedek_notu)
    for ad, sonraki in zip(kurulu, kurulu[1:]):
        try:
            return _uret(ad, istem, c, g, y, adimi[ad], tohum, adet, referans)
        except MedyaHatasi as e:
            uyar(f"{ad} başarısız ({str(e).strip()[-300:]}); {sonraki} ile yeniden deneniyor"
                 f"{_yedek_notu(sonraki, sira[0], adim)}")
    return _uret(kurulu[-1], istem, c, g, y, adimi[kurulu[-1]], tohum, adet, referans)


def calistir_(args) -> int:
    for r in gorsel_uret(args.istem, args.cikti, model=args.model, boyut=args.boyut, adim=args.adim,
                         tohum=args.tohum, adet=args.adet, referans=args.referans):
        print(f"{r['cikti']}  ({r['boyut'][0]}x{r['boyut'][1]}, {r['saglayici']}, tohum {r['tohum']}, "
              f"{r['sure_sn']} sn)")
    print("  kalite ölçülmez: görsele bak (Read). Yazı istendiyse büyütüp harf harf oku.")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="metinden ya da referans görselden görsel üretir (FLUX.2 klein / Z-Image-Turbo, yerel)",
                       description=__doc__.split("\n\n")[0])
    p.add_argument("istem", help="görsel tarifi (İngilizce en iyi)")
    p.add_argument("--cikti", required=True, help="PNG yolu (yanına .json üretim kaydı)")
    p.add_argument("--model", choices=sorted(KISA), help="varsayılan: kayıttaki birincil (flux2, 1024² 83–107 sn); "
                   "z-image: İngilizce yazıda tek afiş istemi × 2 tohumda 2/2'ye 0/2 doğru, bellek 6,3 GB, "
                   "1024² 275–383 sn; --referans her zaman flux2")
    p.add_argument("--boyut", default="1024x1024", help="GxY, 16'nın katları (ör. 1080x1920 değil 1088x1920)")
    p.add_argument("--adim", type=int, help="çıkarım adımı (varsayılan: z-image 9, flux2 4 — damıtıldıkları sayı; "
                   "--model'siz verilirse birincilin, yedeğe düşülünce yedek kendi adımıyla koşar)")
    p.add_argument("--tohum", type=int, default=7, help="aynı model + tohum + istem = aynı görsel")
    p.add_argument("--adet", type=int, default=1, help="farklı tohumlarla kaç seçenek")
    p.add_argument("--referans", nargs="+", help="düzenleme/çoklu referans: kaynak görsel(ler) (yalnız flux2)")
    p.set_defaults(islev=calistir_)
