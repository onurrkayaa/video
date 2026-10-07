"""Konuşma temizliğinin önce/sonra ölçümü — karşılaştırmalı (tek bir sesin mutlak tayfı yorumlanmaz).

  PY=$MEDYA/ortamlar/ses/bin/python; B=$MEDYA/sistem/claude/skills/ses-tasarimi/scripts
  $PY $B/temizlik_olc.py --once calisma/ses/konusma-ham.wav --sonra calisma/ses/konusma.wav \
      --yazi analiz/konusma-ham-yazi.json --json analiz/temizlik.json

--once: medya ses-temizle'ye giren WAV; --sonra: çıkan WAV; --yazi: 'once' dosyasının medya yaziya-dok JSON'u
(kelime zamanları → konuşma ve durak bölgeleri; gürültülü dosyada enerji kapısı güvenilmez).
Ölçer: (1) hizalama: örnek düzeyinde çapraz ilinti (ilk 60 sn), |gecikme| ≤ 1 ms; (2) uzunluk: DeepFilterNet -D
gecikmeyi baştan telafi eder ve çıktı SONDA ~30 ms kısalır (ölçüldü) → 0…−40 ms kabul, ötesi kaldı;
(3) duraklarda (kelime arası ≥0,3 sn) gürültü: 50 ms blok güçlerinin MEDYANI (Whisper sınır hatasıyla durağa düşen
konuşma bloklarına dayanıklı), geniş bant ve <150 Hz (rüzgâr); ayrıca bütün dosyanın %10'luk blok gücü (dökümden
bağımsız gürültü tabanı); (4) konuşmada 1–4 kHz bant düzeyi değişimi, durak gürültüsü çıkarılarak (gürültü telafili);
(5) kırpılma (|x| ≥ 0,999).
Kapı (araştırma 2026-10-05): duraklarda gürültü düşer; 1–4 kHz konuşma bandı ±2 dB; hizalama ≤ 1 ms; kırpılma artmaz.
Anlaşılırlık ayrı: medya ses-temizle --dogrula (Whisper önce/sonra). Ölçülemeyen: metalik/'su altı' yan ürünü,
doğallık → kullanıcıya düzeyi eşitlenmiş A/B dinletisi. Çıkış kodu: 0 geçti, 1 kaldı, 2 kullanım hatası.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

import sesortak as so

DURAK_EN_KISA = 0.3      # sn
DURAK_PAY = 0.05         # kelime sınırlarından içeri pay (Whisper sınırları yaklaşık)
BLOK = 0.05              # sn
BANT_KAPI_DB = 2.0       # araştırma: 1–4 kHz konuşma bandı ±2 dB
GECIKME_KAPI_MS = 1.0
KISALMA_MS = (-40.0, 0.0)


def db(p: float) -> float:
    return 10 * math.log10(p) if p and p > 0 else float("-inf")


def bloklar(x: np.ndarray, sr: int, araliklar) -> np.ndarray:
    """Aralıkların içine tam sığan 50 ms blokların ortalama güçleri."""
    n = int(BLOK * sr)
    g = []
    for a, b in araliklar:
        i = int(math.ceil(a * sr))
        while i + n <= min(int(b * sr), len(x)):
            g.append(float(np.mean(x[i:i + n] ** 2)))
            i += n
    return np.asarray(g)


def gecikme(a: np.ndarray, b: np.ndarray, sr: int, en_cok: float = 0.05, sure: float = 60.0) -> tuple[int, float]:
    """b'nin a'ya göre gecikmesi (örnek; + = b geç) ve normalize ilinti."""
    n = min(len(a), len(b), int(sure * sr))
    x, y = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    m = 1 << int(math.ceil(math.log2(2 * n)))
    c = np.fft.irfft(np.fft.rfft(y, m) * np.conj(np.fft.rfft(x, m)), m)
    k = int(en_cok * sr)
    aday = np.concatenate([c[-k:], c[: k + 1]])
    j = int(np.argmax(aday)) - k
    return j, float(aday.max() / (math.sqrt(float((x ** 2).sum() * (y ** 2).sum())) + 1e-12))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--once", required=True)
    p.add_argument("--sonra", required=True)
    p.add_argument("--yazi", required=True, help="'once' dosyasının medya yaziya-dok JSON'u")
    p.add_argument("--json")
    a = p.parse_args()

    x0, sr = so.oku(a.once)
    x1, sr1 = so.oku(a.sonra)
    if sr != sr1 or x0.shape[0] != x1.shape[0]:
        so.hata(f"biçim farklı: {sr} Hz/{x0.shape[0]} kanal ↔ {sr1} Hz/{x1.shape[0]} kanal (aynı biçimde karşılaştır)")
    bulgular, gecti = [], True
    fark_ms = (x1.shape[1] - x0.shape[1]) / sr * 1000
    if not KISALMA_MS[0] <= fark_ms <= KISALMA_MS[1]:
        gecti = False
        bulgular.append(f"uzunluk farkı {fark_ms:+.1f} ms (beklenen 0…−40 ms; DeepFilterNet -D sonda ~30 ms kısaltır)")
    n = min(x0.shape[1], x1.shape[1])
    m0, m1 = x0[:, :n].mean(axis=0).astype(np.float64), x1[:, :n].mean(axis=0).astype(np.float64)
    sure = n / sr

    gec, ilinti = gecikme(m0, m1, sr)
    gec_ms = gec / sr * 1000
    if abs(gec_ms) > GECIKME_KAPI_MS:
        gecti = False
        bulgular.append(f"gecikme {gec_ms:+.2f} ms ({gec:+d} örnek): deep-filter -D (gecikme telafisi) kullanıldı mı?")

    kel = json.loads(Path(a.yazi).read_text(encoding="utf-8")).get("kelimeler", [])
    konusma = so.birlestir([(float(w["bas"]), float(w["son"])) for w in kel if float(w["son"]) > float(w["bas"])], 0.0)
    if not konusma:
        so.hata(f"{a.yazi} içinde kelime yok (medya yaziya-dok çıktısı mı?)")
    duraklar, onceki = [], 0.0
    for b0, b1 in konusma + [(sure, sure)]:
        if b0 - onceki >= DURAK_EN_KISA:
            duraklar.append((onceki + DURAK_PAY, min(b0, sure) - DURAK_PAY))
        onceki = max(onceki, b1)
    mk = so.maske(konusma, sr, n)

    bant = butter(4, [1000, 4000], btype="bandpass", fs=sr, output="sos")
    alcak = butter(4, 150, btype="lowpass", fs=sr, output="sos")
    b0_, b1_ = sosfilt(bant, m0), sosfilt(bant, m1)
    l0, l1 = sosfilt(alcak, m0), sosfilt(alcak, m1)
    d0, d1 = bloklar(m0, sr, duraklar), bloklar(m1, sr, duraklar)
    tum0, tum1 = bloklar(m0, sr, [(0, sure)]), bloklar(m1, sr, [(0, sure)])

    olcum = {"gecikme_ms": round(gec_ms, 3), "ilinti": round(ilinti, 4), "uzunluk_farki_ms": round(fark_ms, 1),
             "durak_blok": int(len(d0)), "konusma_sn": round(float(mk.sum()) / sr, 2),
             "taban_yuzde10_db": {"once": round(db(float(np.percentile(tum0, 10))), 2),
                                  "sonra": round(db(float(np.percentile(tum1, 10))), 2)}}
    pd0 = pd1 = None
    if len(d0) < 10:
        bulgular.append(f"duraklar yetersiz ({len(d0)} blok × 50 ms): durak gürültüsü ölçülemedi (belirsiz); "
                        "%10'luk taban yalnız bilgi")
        olcum["durak"] = None
    else:
        r0, r1 = bloklar(l0, sr, duraklar), bloklar(l1, sr, duraklar)
        g0, g1 = db(float(np.median(d0))), db(float(np.median(d1)))
        olcum["durak"] = {"genis_once_db": round(g0, 2), "genis_sonra_db": round(g1, 2), "genis_dusus_db": round(g0 - g1, 2),
                          "ruzgar_once_db": round(db(float(np.median(r0))), 2),
                          "ruzgar_sonra_db": round(db(float(np.median(r1))), 2)}
        if not g0 - g1 > 0:
            gecti = False
            bulgular.append("duraklarda gürültü düşmedi")
        pd0, pd1 = float(np.median(bloklar(b0_, sr, duraklar))), float(np.median(bloklar(b1_, sr, duraklar)))

    pk0, pk1 = float(np.mean(b0_[mk] ** 2)), float(np.mean(b1_[mk] ** 2))
    ham_degisim = db(pk1) - db(pk0)
    telafili = db(pk1 - pd1) - db(pk0 - pd0) if pd0 is not None and pk0 > pd0 and pk1 > pd1 else None
    degisim = telafili if telafili is not None else ham_degisim
    olcum["bant_1_4khz"] = {"ham_degisim_db": round(ham_degisim, 2),
                            "gurultu_telafili_degisim_db": None if telafili is None else round(telafili, 2),
                            "kapida_kullanilan": "telafili" if telafili is not None else "ham"}
    if abs(degisim) > BANT_KAPI_DB:
        gecti = False
        bulgular.append(f"konuşma bandı (1–4 kHz) {degisim:+.1f} dB değişti (kapı ±{BANT_KAPI_DB:g} dB): temizlik konuşmayı "
                        "da yiyor olabilir → medya ses-temizle --siddet'i düşür (ör. 8)"
                        + ("" if telafili is not None else "; ham ölçüm gürültüyü de içerir, durak yetersiz"))
    k0, k1 = int(np.sum(np.abs(x0) >= 0.999)), int(np.sum(np.abs(x1) >= 0.999))
    olcum["kirpik_ornek"] = {"once": k0, "sonra": k1}
    if k1 > k0:
        gecti = False
        bulgular.append(f"kırpılma arttı: {k0} → {k1} örnek")

    rapor = {"once": a.once, "sonra": a.sonra, "yazi": a.yazi, "olcum": olcum, "bulgular": bulgular,
             "kapi": {"bant_db": BANT_KAPI_DB, "gecikme_ms": GECIKME_KAPI_MS, "uzunluk_ms": KISALMA_MS, "durak": "düşmeli"},
             "olculemeyen": "metalik/su altı yan ürünü, doğallık: düzeyi eşitlenmiş A/B dinletisiyle kullanıcı karar verir",
             "gecti": bool(gecti)}
    if a.json:
        so.json_yaz(a.json, rapor)
    d = olcum["durak"]
    print(f"{'✓' if gecti else '✗'} temizlik ölçümü ({a.yazi})")
    print(f"  hizalama {gec_ms:+.3f} ms, ilinti {ilinti:.3f}; uzunluk farkı {fark_ms:+.1f} ms")
    if d:
        print(f"  duraklar ({len(d0)} blok): geniş bant {d['genis_once_db']:.1f} → {d['genis_sonra_db']:.1f} dB "
              f"(düşüş {d['genis_dusus_db']:.1f}); <150 Hz {d['ruzgar_once_db']:.1f} → {d['ruzgar_sonra_db']:.1f} dB")
    t = olcum["taban_yuzde10_db"]
    print(f"  gürültü tabanı (%10): {t['once']:.1f} → {t['sonra']:.1f} dB")
    print(f"  1–4 kHz konuşma bandı: {degisim:+.2f} dB ({olcum['bant_1_4khz']['kapida_kullanilan']}; ham {ham_degisim:+.2f})")
    for b in bulgular:
        print(f"  ⚠ {b}")
    if a.json:
        print(f"→ {a.json}")
    return 0 if gecti else 1


if __name__ == "__main__":
    raise SystemExit(main())
