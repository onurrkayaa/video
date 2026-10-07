"""Müziği (yatağı) konuşmanın altında kısar — belirlenimci, ileri bakışlı zarf — ve kabul kapısını ölçer.

  PY=$MEDYA/ortamlar/ses/bin/python; B=$MEDYA/sistem/claude/skills/ses-tasarimi/scripts
  $PY $B/kisma.py --yatak calisma/ses/muzik-ana.wav --konusma calisma/ses/konusma.wav \
      --araliklar analiz/konusma-yazi.json [analiz/dis-ses-yazi.json …] [--bas <plan muzik.bas>] \
      --cikti calisma/ses/muzik-kisik.wav --json analiz/kisma.json --png analiz/kisma.png \
      [--derinlik -12] [--kazanc 0] [--on 0.12] [--atak 0.08] [--birak 0.45] [--hf calisma/ses/kisma-hf.json --medya-bas 0]

Zamanlar:
  --yatak     kompozisyonda çalınacak müzik dosyası (ana WAV). Çıktı aynı dosya zamanındadır, aynı örnek sayısı:
              ana WAV'ın yerine AYNI data-start/data-media-start ile konur (vuruş zamanları geçerli kalır).
  --bas       yatağın 0. sn'si çıktı videoda kaçıncı sn (plan muzik.bas = data-start − data-media-start).
  --konusma   çıktı zaman çizelgesindeki konuşma/dış ses katmanı (0. sn = videonun 0. sn'si), miksteki seviyesiyle.
  --araliklar çıktı zamanında: medya yaziya-dok JSON'u (kelimeler), medya ses-olay JSON'u (konuşma/kahkaha) ya da
              [[bas, son], …]; birden çok dosya birleşir. Verilmezse konuşma katmanının enerjisinden (RMS kapısı).
--kazanc     yatağa zarftan önce uygulanan genel kazanç dB (≤ 0); -15 dB kısma kapıyı geçirmezse öneri bunu verir.
Zarf (araştırma 2026-10-05): kısma konuşmadan 'on' sn önce başlar, 'atak' sn'de 'derinlik' dB'e iner (dB'de kosinüs),
konuşma bitince 'birak' sn'de çıkar. Aradaki boşluk on+birak'tan kısaysa yatak inik kalır (pompalama yok).
Kapı (araştırma): kısma bölgelerinde 3 sn'lik kayan pencerelerde (bölge kısaysa bütün bölge) konuşma − yatak ≥ 10 LU;
kısma dışında yatak ±0,5 LU. Ölçüm BS.1770 K-ağırlıklı, kapısız; kanal güçleri toplanır. Mono konuşma ffmpeg/HyperFrames
stereo miksine kanal başına −3 dB girer, ses yüksekliği değişmez (ölçüldü) → mono katmanı olduğu gibi ver.
--hf: aynı zarfın HyperFrames data-automation 'volume' şeridi (klibe göre sn = dosya zamanı − --medya-bas; rampalar
7 noktayla). Ölçülen şey kısılmış WAV'dır; kompozisyonda tercihen o dosyayı kullan.
Çıkış kodu: 0 kapı geçti, 1 kaldı (dosyalar yine yazılır), 2 kullanım hatası.
"""
from __future__ import annotations

import argparse
import math

import numpy as np

import sesortak as so

KONTROL_HZ = 1000          # zarf 1 ms çözünürlükte kurulur, örneklere doğrusal aradeğerlenir
KAPI_LU = 10.0             # konuşma − yatak (araştırma: ≥10 LU)
DIS_LU = 0.5               # kısma dışında yatak değişimi (araştırma: ±0,5 LU)
PENCERE = 3.0              # kısa süreli ses yüksekliği penceresi (BS.1770 short-term)
ADIM = 0.1
EN_KISA = 0.4              # bundan kısa tam-kısma aralığı ölçülmez (bir anlık blok)
RAMPA_NOKTA = 7


def zarf_db(birlesik, sure: float, derinlik: float, on: float, atak: float, birak: float) -> np.ndarray:
    """KONTROL_HZ çözünürlükte kazanç (dB); her bölge için rampa-tepe-rampa, en derin olan geçerli."""
    t = np.arange(int(math.ceil(sure * KONTROL_HZ)) + 1) / KONTROL_HZ
    g = np.zeros_like(t)
    for a, b in birlesik:
        t0, t1, t3 = a - on, a - on + atak, b + birak
        h = np.zeros_like(t)
        h[(t >= t1) & (t <= b)] = 1.0
        inis = (t >= t0) & (t < t1)
        h[inis] = 0.5 - 0.5 * np.cos(np.pi * (t[inis] - t0) / atak)
        cikis = (t > b) & (t < t3)
        h[cikis] = 0.5 + 0.5 * np.cos(np.pi * (t[cikis] - b) / birak)
        g = np.minimum(g, derinlik * h)
    return g


def hf_seridi(g_db, birlesik, sure, on, atak, birak, medya_bas) -> list[dict]:
    """Zarfı kırılma noktalarına indirger (rampalar RAMPA_NOKTA noktayla); t = dosya zamanı − medya_bas."""
    anlar = {0.0, sure}
    for a, b in birlesik:
        anlar.update(np.linspace(a - on, a - on + atak, RAMPA_NOKTA).tolist())
        anlar.update(np.linspace(b, b + birak, RAMPA_NOKTA).tolist())
    tk = np.arange(len(g_db)) / KONTROL_HZ
    noktalar = []
    for t in sorted(x for x in anlar if medya_bas <= x <= sure):
        v = round(float(10 ** (np.interp(t, tk, g_db) / 20)), 4)
        if len(noktalar) >= 2 and noktalar[-1]["v"] == v and noktalar[-2]["v"] == v:
            noktalar[-1]["t"] = round(t - medya_bas, 4)          # düz bölümün ara noktalarını at
        else:
            noktalar.append({"t": round(t - medya_bas, 4), "v": v})
    if noktalar and noktalar[0]["t"] > 0:
        noktalar.insert(0, {"t": 0.0, "v": round(float(10 ** (np.interp(medya_bas, tk, g_db) / 20)), 4)})
    return noktalar


def guc_birikimli(xk: np.ndarray) -> np.ndarray:
    """K-ağırlıklı sinyalin kanal güçleri toplamının birikimli toplamı (pencere ortalamaları için)."""
    return np.concatenate([[0.0], np.cumsum(np.sum(xk ** 2, axis=0))])


def pencere_lufs(c: np.ndarray, i: int, j: int) -> float:
    ms = (c[j] - c[i]) / max(j - i, 1)
    return -0.691 + 10 * math.log10(ms) if ms > 0 else float("-inf")


def ciz(yol, x_konusma, x_once, x_sonra, sr, bas, g_db, birlesik, en_kotu, baslik):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def rms_db(x, pencere=0.1):
        m = x.mean(axis=0).astype(np.float64)
        n = max(1, int(pencere * sr))
        k = len(m) // n
        return 10 * np.log10((m[: k * n].reshape(k, n) ** 2).mean(axis=1) + 1e-12), np.arange(k) * pencere + bas

    fig, (u, a) = plt.subplots(2, 1, figsize=(16, 5.5), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    for x, renk, ad in ((x_once, "0.6", "yatak (önce)"), (x_sonra, "tab:orange", "yatak (sonra)"),
                        (x_konusma, "tab:blue", "konuşma")):
        d, t = rms_db(x)
        u.plot(t, d, color=renk, lw=1.1, label=ad)
    for b0, b1 in birlesik:
        u.axvspan(b0 + bas, b1 + bas, color="tab:blue", alpha=0.08)
    if en_kotu is not None:
        u.axvspan(en_kotu[0] + bas, en_kotu[1] + bas, color="tab:red", alpha=0.15, label="en düşük pencere")
    u.set_ylim(-80, 0)
    u.set_ylabel("RMS dBFS (100 ms)")
    u.legend(loc="lower right")
    u.set_title(baslik)
    a.plot(np.arange(len(g_db)) / KONTROL_HZ + bas, g_db, color="tab:orange")
    a.set_ylabel("kazanç dB")
    a.set_xlabel("çıktı videosunda sn")
    fig.tight_layout()
    fig.savefig(yol, dpi=90)
    plt.close(fig)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--yatak", required=True, help="müzik yatağı WAV (kompozisyonda çalınacak dosya)")
    p.add_argument("--konusma", required=True, help="konuşma/dış ses katmanı WAV (çıktı zaman çizelgesi)")
    p.add_argument("--cikti", required=True, help="kısılmış yatak WAV (32 bit kayan, yatakla aynı uzunluk)")
    p.add_argument("--araliklar", nargs="+", help="yaziya-dok / ses-olay JSON'ları ya da [[bas, son], …] (çıktı zamanı)")
    p.add_argument("--bas", type=float, default=0.0, help="yatağın 0. sn'si çıktıda kaçıncı sn (plan muzik.bas)")
    p.add_argument("--derinlik", type=float, default=-12.0, help="dB (araştırma: -8…-15)")
    p.add_argument("--kazanc", type=float, default=0.0, help="yatağa genel kazanç dB (≤ 0; zarftan önce)")
    p.add_argument("--on", type=float, default=0.12, help="konuşmadan önce başlama (sn)")
    p.add_argument("--atak", type=float, default=0.08, help="iniş süresi (sn)")
    p.add_argument("--birak", type=float, default=0.45, help="çıkış süresi (sn)")
    p.add_argument("--hf", help="HyperFrames data-automation JSON çıktısı")
    p.add_argument("--medya-bas", type=float, default=0.0, help="yatak öğesinin data-media-start'ı (yalnız --hf için)")
    p.add_argument("--json", help="ölçüm raporu")
    p.add_argument("--png", help="seviye + zarf görseli (Read ile bak)")
    a = p.parse_args()
    if not (a.derinlik < 0 and a.kazanc <= 0 and a.on >= 0 and a.atak > 0 and a.birak > 0):
        so.hata("derinlik < 0, kazanc ≤ 0, on ≥ 0, atak > 0, birak > 0 olmalı")

    yatak, sr = so.oku(a.yatak)
    yatak = yatak * (10 ** (a.kazanc / 20))
    konusma_cikti, sr2 = so.oku(a.konusma)
    if sr != sr2:
        so.hata(f"örnekleme hızları farklı ({sr} / {sr2}); önce aynı hıza getir: "
                f"arac/ffmpeg -nostdin -i <dosya> -ar {sr} <yeni>.wav")
    n = yatak.shape[1]
    sure = n / sr
    # konuşma katmanını yatak dosyasının zamanına taşı: yatak örneği k ↔ çıktı zamanı k/sr + bas
    kay = int(round(a.bas * sr))
    konusma = konusma_cikti[:, kay:] if kay >= 0 else np.pad(konusma_cikti, ((0, 0), (-kay, 0)))
    konusma = np.pad(konusma, ((0, 0), (0, max(0, n - konusma.shape[1]))))[:, :n]

    if a.araliklar:
        ham = sorted(x for yol in a.araliklar for x in so.araliklar_oku(yol, -a.bas))
        kaynak = " + ".join(a.araliklar)
    else:
        ham = so.rms_kapisi(konusma, sr)
        kaynak = "rms-kapisi (konuşma katmanı)"
    ham = [(max(0.0, x), min(sure, y)) for x, y in ham if y > 0 and x < sure]
    if not ham:
        so.hata("yatak süresi içinde konuşma bölgesi yok (katman sessiz mi, --bas doğru mu? --araliklar ver)")
    birlesik = so.birlestir(ham, a.on + a.birak)
    uyari = []
    kapsam = sum(y - x for x, y in birlesik) / sure
    if not a.araliklar and kapsam > 0.9:
        uyari.append(f"kısma bölgeleri sürenin %{100 * kapsam:.0f}'i: enerji kapısı ortam sesini konuşma sanmış "
                     "olabilir → --araliklar ile Whisper kelimelerini ver")

    g = zarf_db(birlesik, sure, a.derinlik, a.on, a.atak, a.birak)
    tk = np.arange(len(g)) / KONTROL_HZ
    g_ornek = np.interp(np.arange(n) / sr, tk, g)
    cikti = (yatak * (10 ** (g_ornek / 20))).astype(np.float32)
    so.yaz(a.cikti, cikti, sr)

    # ---- ölçüm: kısa süreli pencereler (yalnız tam kısılmış aralıklarda)
    kk, yk_once, yk_sonra = so.k_agirlikla(konusma, sr), so.k_agirlikla(yatak, sr), so.k_agirlikla(cikti, sr)
    ck, cs = guc_birikimli(kk), guc_birikimli(yk_sonra)
    pencereler, olculmeyen = [], []
    for x, y in birlesik:
        p0, p1 = max(0.0, x - a.on + a.atak), min(sure, y)
        if p1 - p0 < EN_KISA:
            olculmeyen.append([round(p0 + a.bas, 3), round(p1 + a.bas, 3)])
            continue
        w = min(PENCERE, p1 - p0)
        for s in np.arange(p0, p1 - w + 1e-9, ADIM):
            i, j = int(s * sr), int((s + w) * sr)
            fark = pencere_lufs(ck, i, j) - pencere_lufs(cs, i, j)
            pencereler.append((float(s), float(s + w), fark))
    if not pencereler:
        so.hata("ölçülebilir kısma aralığı yok (hepsi 0,4 sn'den kısa)")
    en_kotu = min(pencereler, key=lambda q: q[2])
    m_k = so.maske(ham, sr, n)
    fark_toplam = so.yukseklik(kk, m_k) - so.yukseklik(yk_sonra, m_k)
    m_dis = g_ornek == 0.0
    dis_degisim = (so.yukseklik(yk_sonra, m_dis) - so.yukseklik(yk_once, m_dis)) if m_dis.any() else 0.0
    gercek_kisma = so.yukseklik(yk_once, m_k) - so.yukseklik(yk_sonra, m_k)
    kotu = [q for q in pencereler if q[2] < KAPI_LU]
    gecti = en_kotu[2] >= KAPI_LU and abs(dis_degisim) <= DIS_LU
    oneri = None
    if en_kotu[2] < KAPI_LU:
        gereken = a.derinlik - (KAPI_LU - en_kotu[2]) - 1.0          # 1 LU pay
        oneri = (f"--derinlik {math.floor(gereken):.0f}" if gereken >= -15 else
                 f"--derinlik -15 --kazanc {a.kazanc - math.ceil(-15 - gereken):.0f} (yatağı genel indir; ya da konuşmayı "
                 "yükselt); araştırmanın kısma aralığı -8…-15 dB")

    def cikti_zamani(q):
        return [round(q[0] + a.bas, 2), round(q[1] + a.bas, 2), round(q[2], 2)]

    rapor = {"yatak": a.yatak, "konusma": a.konusma, "cikti": a.cikti, "aralik_kaynagi": kaynak, "bas_sn": a.bas,
             "parametreler": {"derinlik_db": a.derinlik, "kazanc_db": a.kazanc, "on_sn": a.on, "atak_sn": a.atak, "birak_sn": a.birak},
             "sure_sn": round(sure, 3), "kisma_bolgeleri_cikti_sn": [[round(x + a.bas, 3), round(y + a.bas, 3)] for x, y in birlesik],
             "olcum": {"pencere_sn": PENCERE, "pencere_sayisi": len(pencereler),
                       "en_dusuk_pencere_cikti_sn_lu": cikti_zamani(en_kotu),
                       "kapi_alti_pencereler_cikti_sn_lu": [cikti_zamani(q) for q in kotu[:30]],
                       "olculmeyen_kisa_bolgeler_cikti_sn": olculmeyen,
                       "konusma_eksi_yatak_lu_tum_konusma": round(fark_toplam, 2),
                       "kisma_disi_yatak_degisimi_lu": round(dis_degisim, 3), "olculen_kisma_lu": round(gercek_kisma, 2)},
             "kapi": {"konusma_eksi_yatak_lu_en_az": KAPI_LU, "kisma_disi_en_cok_lu": DIS_LU},
             "gecti": bool(gecti), "oneri": oneri, "uyarilar": uyari}
    if a.hf:
        noktalar = hf_seridi(g, birlesik, sure, a.on, a.atak, a.birak, a.medya_bas)
        if len(noktalar) > 512:
            uyari.append(f"HyperFrames şeridi {len(noktalar)} nokta (>512): yazılmadı; kısılmış WAV'ı kullan")
        else:
            so.json_yaz(a.hf, {"version": 1, "lanes": [{"target": "volume", "points": noktalar}]})
            rapor["hf"] = {"yol": a.hf, "nokta": len(noktalar), "medya_bas": a.medya_bas}
    if a.png:
        ciz(a.png, konusma, yatak, cikti, sr, a.bas, g, birlesik, en_kotu,
            f"kısma {a.derinlik:g} dB · en düşük 3 sn pencere {en_kotu[2]:.1f} LU (kapı ≥{KAPI_LU:g}) · "
            f"kısma dışı değişim {dis_degisim:+.2f} LU")
        rapor["png"] = a.png
    if a.json:
        so.json_yaz(a.json, rapor)

    print(f"{'✓' if gecti else '✗'} kısma {a.derinlik:g} dB, {len(birlesik)} bölge ({len(ham)} konuşma parçası; {kaynak})")
    print(f"  konuşma − yatak: en düşük 3 sn pencere {en_kotu[2]:.1f} LU @ {en_kotu[0] + a.bas:.1f}–{en_kotu[1] + a.bas:.1f} sn "
          f"(kapı ≥ {KAPI_LU:g}); tüm konuşmada {fark_toplam:.1f} LU; ölçülen kısma {gercek_kisma:.1f} LU; "
          f"kısma dışı yatak {dis_degisim:+.2f} LU")
    if olculmeyen:
        print(f"  ölçülmeyen kısa bölgeler (<{EN_KISA} sn): {olculmeyen[:5]}")
    if oneri:
        print(f"  öneri: {oneri}")
    for u in uyari:
        print(f"  ⚠ {u}")
    print(f"→ {a.cikti}" + (f"\n→ {a.hf}" if rapor.get("hf") else "") + (f"\n→ {a.png}" if a.png else "")
          + (f"\n→ {a.json}" if a.json else ""))
    return 0 if gecti else 1


if __name__ == "__main__":
    raise SystemExit(main())
