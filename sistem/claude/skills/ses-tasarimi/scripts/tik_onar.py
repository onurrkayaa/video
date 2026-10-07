"""Kısa tık/pat onarımı (PCM'de, ustalıktan ÖNCE): verilen anların ±10 ms çevresindeki yalıtık sıçramayı bulur, bozuk
örnekleri iki yanındaki sağlam örnekler arasında doğrusal aradeğerler. Dosyanın geri kalanı bit bit aynı kalır.

  PY=$MEDYA/ortamlar/ses/bin/python; B=$MEDYA/sistem/claude/skills/ses-tasarimi/scripts
  $PY $B/tik_onar.py --girdi calisma/ses/miks.wav --anlar 8.9,12.3 --cikti calisma/ses/miks-onarili.wav --json analiz/tik.json

Anlar: medya denetle çıktısındaki ses.tik[].t (çıktı zamanı) ya da elle. Önce kaynağı düşün: tık bizim ses ekimizden
(kesimde mikro geçiş yok) geliyorsa sesi YENİDEN ÜRET (5–10 ms afade / data-fade-in/out); bu betik ek yeri olmayan
kısa bozulmalar içindir. Bulma: örnek farkı |x[n]−x[n−1]| çevredeki ±200 ms'nin (±20 ms hariç) 99. yüzdeliğinin 4
katını aşan örnekler (medya denetle'nin ölçütü). Bozuk aralık 5 ms'den uzunsa (gerçek vuruş/davul olabilir) dokunmaz.
Neden: sınırlayıcı (medya ustala) 0,5 ms'lik tam ölçek bir tıkı yalnız ~4,7 dB bastırır, tık duyulur kalır ve kazanç
çöker (denetim dersi 2026-10-05); ffmpeg adeclick ise bu tıkı gidermedi ve dosyanın her yerini değiştirdi (ölçüldü).
Çıkış kodu: 0 hepsi onarıldı, 1 en az biri bulunamadı/reddedildi (dosya yine yazılır), 2 kullanım hatası.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

import sesortak as so

ARA = 0.010         # aranan pencere ± sn
CEVRE = 0.200       # taban için çevre ± sn
BOSLUK = 0.020      # tabandan çıkarılan iç kısım ± sn
ORAN = 4.0          # medya denetle eşiği
EN_UZUN = 0.005     # sn


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--girdi", required=True, help="PCM WAV (miks ya da kaynak sesi)")
    p.add_argument("--anlar", required=True, help="virgülle ayrılmış sn, ör. 8.9,12.3")
    p.add_argument("--cikti", required=True)
    p.add_argument("--json")
    a = p.parse_args()
    if Path(a.cikti).resolve() == Path(a.girdi).resolve():
        so.hata("çıktı girdinin üzerine yazamaz")
    x, sr = so.oku(a.girdi)
    y = x.copy()
    d = np.concatenate([[0.0], np.abs(np.diff(x, axis=1)).max(axis=0)])      # d[n] = |x[n] − x[n−1]| (kanal en büyüğü)
    sonuc, hepsi = [], True
    for t in [float(s) for s in a.anlar.split(",") if s.strip()]:
        i0, i1 = int((t - ARA) * sr), int((t + ARA) * sr)
        c0, c1 = int((t - CEVRE) * sr), int((t + CEVRE) * sr)
        b0, b1 = int((t - BOSLUK) * sr), int((t + BOSLUK) * sr)
        if c0 < 1 or c1 > x.shape[1]:
            sonuc.append({"t": t, "durum": "kenar", "not": "dosya başına/sonuna 0,2 sn'den yakın"}); hepsi = False
            continue
        taban = float(np.percentile(np.concatenate([d[c0:b0], d[b1:c1]]), 99)) + 1e-9
        aday = np.flatnonzero(d[i0:i1] > ORAN * taban) + i0
        if len(aday) == 0:
            sonuc.append({"t": t, "durum": "bulunamadi", "en_buyuk_oran": round(float(d[i0:i1].max() / taban), 2)})
            hepsi = False
            continue
        s, e = int(aday[0]), int(aday[-1])            # bozuk örnekler: s … e−1 (tek örneklik sıçramada s … s)
        e = max(e, s + 1)
        if (e - s) / sr > EN_UZUN:
            sonuc.append({"t": t, "durum": "reddedildi", "uzunluk_ms": round((e - s) / sr * 1000, 2),
                          "not": "5 ms'den uzun: gerçek vuruş olabilir; sesi yeniden üret"}); hepsi = False
            continue
        cizgi = np.stack([np.linspace(x[k, s - 1], x[k, e], e - s + 2)[1:-1] for k in range(x.shape[0])])
        sapma = float(np.abs(x[:, s:e] - cizgi).max())
        sicrama = float(np.abs(x[:, e] - x[:, s - 1]).max())
        if sapma <= sicrama:                          # iki yanı farklı düzeyde: darbe değil basamak (ek yeri)
            sonuc.append({"t": t, "durum": "reddedildi", "not": "basamak (dalga biçimi sıçraması): ek yerinde mikro geçişle "
                          "sesi yeniden üret"}); hepsi = False
            continue
        once_tepe = float(np.abs(x[:, i0:i1]).max())
        y[:, s:e] = cizgi
        sonuc.append({"t": t, "durum": "onarildi", "bas_sn": round(s / sr, 6), "uzunluk_ms": round((e - s) / sr * 1000, 3),
                      "ornek": e - s, "tepe_once": round(once_tepe, 4), "tepe_sonra": round(float(np.abs(y[:, i0:i1]).max()), 4),
                      "oran": round(float(d[s:e + 1].max() / taban), 1)})
    so.yaz(a.cikti, y, sr)
    degisen = int(np.count_nonzero(np.any(y != x, axis=0)))
    rapor = {"girdi": a.girdi, "cikti": a.cikti, "anlar": sonuc, "degisen_ornek_toplam": degisen, "gecti": hepsi}
    if a.json:
        so.json_yaz(a.json, rapor)
    for r in sonuc:
        if r["durum"] == "onarildi":
            print(f"✓ {r['t']:.3f} sn: {r['ornek']} örnek ({r['uzunluk_ms']} ms) @ {r['bas_sn']:.4f} sn aradeğerlendi; "
                  f"çevre tepesi {r['tepe_once']:.3f} → {r['tepe_sonra']:.3f}")
        else:
            print(f"✗ {r['t']:.3f} sn: {r['durum']} {r.get('not', '')}{' (en büyük oran ' + str(r['en_buyuk_oran']) + ')' if 'en_buyuk_oran' in r else ''}")
    print(f"  toplam değişen örnek: {degisen} → {a.cikti}")
    return 0 if hepsi else 1


if __name__ == "__main__":
    raise SystemExit(main())
