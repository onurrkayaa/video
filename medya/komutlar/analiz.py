"""medya analiz <video|resim> [--aralik 0.5] — kare kare görüntü analizi (Apple Vision, yerleşik, indirme yok).

Her örnek karede: estetik puan (-1..1; "keeper" seçimi), yüzler (kutu + yakalama kalitesi: gözler açık mı,
net mi), insanlar, dikkat çeken bölge (dikey/yatay yeniden kadrajın merkezi), sahne etiketleri, bir önceki
örneğe görsel uzaklık (neredeyse aynı kareleri ve sahne içi hareketi bulmak için).

Özet (çekim başına, --sahneler verilirse): en iyi an (estetik + yüz kalitesi), yüz sayısı, ortalama ilgi
merkezi (kadraj için), baskın etiketler. Kurgucu bu özetle çekim seçer ve sıralar.
"""
from __future__ import annotations

import statistics as st
from pathlib import Path

from ..ortak import ARAC, MedyaHatasi, apple_calistir, json_oku, json_yaz, probe

APPLE = ARAC / "medya-apple"


def kare_analizi(girdi: str, aralik: float, cikti: Path) -> dict:
    if not APPLE.exists():
        raise MedyaHatasi("arac/medya-apple yok; derle: medya kur medya-apple")
    sure = float(probe(girdi).get("format", {}).get("duration") or 0)          # resimde 0
    apple_calistir([str(APPLE), "analiz", girdi, str(cikti), "--aralik", f"{aralik:g}"],
                   zaman_asimi=180 + 3 * sure / max(aralik, 0.05), hata_mesaji="görüntü analizi başarısız")
    return json_oku(cikti)


def _puan(k: dict) -> float:
    """An puanı: estetik (-1..1) + en iyi yüz kalitesi (0..1) * 0.5; fayda (belge/ekran) karesi cezalı."""
    p = float(k.get("estetik", 0.0))
    yuzler = k.get("yuzler") or []
    if yuzler:
        p += 0.5 * max(float(y.get("kalite", 0.0)) for y in yuzler)
    if k.get("fayda"):
        p -= 0.5
    return round(p, 3)


def cekim_ozeti(analiz: dict, cekimler: list[dict]) -> list[dict]:
    kareler = analiz["kareler"]
    ozet = []
    for c in cekimler:
        icteki = [k for k in kareler if c["bas"] <= k["t"] < c["son"]]
        if not icteki:
            ozet.append({**c, "kare": 0}); continue
        en_iyi = max(icteki, key=_puan)
        merkezler = []
        for k in icteki:
            kutular = (k.get("yuzler") and [y["kutu"] for y in k["yuzler"]]) or k.get("ilgi") or []
            if kutular:
                x0 = min(b[0] for b in kutular); y0 = min(b[1] for b in kutular)
                x1 = max(b[0] + b[2] for b in kutular); y1 = max(b[1] + b[3] for b in kutular)
                merkezler.append(((x0 + x1) / 2, (y0 + y1) / 2))
        etiket = {}
        for k in icteki:
            for ad, g in k.get("etiketler", []):
                etiket[ad] = etiket.get(ad, 0) + g
        farklar = [k["fark_onceki"] for k in icteki if "fark_onceki" in k]
        ozet.append({**c, "kare": len(icteki), "en_iyi_an": en_iyi["t"], "en_iyi_puan": _puan(en_iyi),
                     "estetik_ort": round(st.mean(float(k.get("estetik", 0)) for k in icteki), 3),
                     "yuz_en_cok": max(len(k.get("yuzler") or []) for k in icteki),
                     "ilgi_merkezi": [round(st.mean(m[0] for m in merkezler), 3), round(st.mean(m[1] for m in merkezler), 3)] if merkezler else None,
                     "hareket": round(st.mean(farklar), 3) if farklar else None,
                     "etiketler": [a for a, _ in sorted(etiket.items(), key=lambda x: -x[1])[:5]]})
    return ozet


def calistir_(args) -> int:
    cikti = Path(args.cikti or str(Path(args.girdi).with_suffix("")) + "-analiz.json")
    a = kare_analizi(args.girdi, args.aralik, cikti)
    kareler = a["kareler"]
    if args.sahneler:
        a["cekim_ozeti"] = cekim_ozeti(a, json_oku(args.sahneler)["cekimler"])
        json_yaz(cikti, a)
        en_iyiler = sorted(a["cekim_ozeti"], key=lambda c: -c.get("en_iyi_puan", -9))[:8]
        print("en iyi çekimler (an puanı): " + ", ".join(f"#{c['no']}@{c.get('en_iyi_an', 0):.1f}s ({c.get('en_iyi_puan', 0):+.2f})" for c in en_iyiler))
    yuzlu = sum(1 for k in kareler if k.get("yuzler"))
    es = [float(k.get("estetik", 0)) for k in kareler]
    print(f"{len(kareler)} kare: estetik ort {st.mean(es):+.2f} (en iyi {max(es):+.2f} @ {kareler[es.index(max(es))]['t']}s), "
          f"yüzlü kare {yuzlu}" if kareler else "kare yok")
    print(f"→ {cikti}")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="kare kare görüntü analizi (Apple Vision)")
    p.add_argument("girdi")
    p.add_argument("--aralik", type=float, default=0.5, help="örnekleme aralığı (sn)")
    p.add_argument("--sahneler", help="medya sahneler çıktısı: çekim başına özet üretir")
    p.add_argument("--cikti")
    p.set_defaults(islev=calistir_)
