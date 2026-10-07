"""Müzik analizi işçisi — ortamlar/ses Python'unda çalışır (torch, beat_this, essentia, librosa, mir_eval).

  ortamlar/ses/bin/python medya/isciler/muzik_isci.py <master.wav> <cikti.json> [--hizli]

KOMİTE: Beat This! (final0, final1, final2 — ISMIR 2024, MIT) + Essentia RhythmExtractor2013 multifeature
(AGPL, kendi güven puanıyla) + librosa (zayıf üye). Her üye önce aynı metrik düzeye getirilir (yarım/çift tempo
ve ara vuruş fazı), sonra ikili uyum ölçülür (mir_eval F ±70 ms, Information Gain bit). Yalnız uyum yüksekse
"yuksek" güven verilir; yoksa vuruşa dayalı kesim önerilmez. Neden: tek bir izleyici "kendinden emin ama
yanlış" olabilir; 2026-10-04'te sabit ızgara yumuşak bir şarkıda ±300 ms kaydı.
"""
from __future__ import annotations

import json
import sys
import warnings

import numpy as np

warnings.filterwarnings("ignore")


def _f(a, b):
    import mir_eval
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return 0.0
    return float(mir_eval.beat.f_measure(a, b, f_measure_threshold=0.07))


def _ig(a, b):
    import mir_eval
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 3 or len(b) < 3:
        return 0.0
    return float(mir_eval.beat.information_gain(a, b))


def _ibi(b):
    b = np.asarray(b)
    return float(np.median(np.diff(b))) if len(b) > 2 else float("nan")


def duzeye_getir(uye, ref):
    """Üyeyi ref'in metrik düzeyine taşır: çift tempoysa uygun yarısını seç, yarı tempoysa araya vuruş ekle.
    Döner: (düzeltilmiş vuruşlar, işlem adı)."""
    u = np.asarray(uye, float)
    r = _ibi(u) / _ibi(ref)
    if 1.7 < r < 2.3:                                   # üye yarı hızda → ara noktaları ekle
        ara = (u[:-1] + u[1:]) / 2
        return np.sort(np.concatenate([u, ara])), "yari-tempo→ara-eklendi"
    if 0.43 < r < 0.59:                                 # üye çift hızda → ref'le en uyumlu yarıyı seç
        a, b = u[0::2], u[1::2]
        return (a, "cift-tempo→tekler") if _f(ref, a) >= _f(ref, b) else (b, "cift-tempo→ciftler")
    return u, "ayni"


def ritim_komitesi(wav: str, hizli: bool = False) -> dict:
    import essentia.standard as es
    import librosa
    from beat_this.inference import File2Beats

    uyeler = {}
    for ck in (["final0"] if hizli else ["final0", "final1", "final2"]):
        b, d = File2Beats(checkpoint_path=ck, device="cpu", dbn=False)(wav)
        uyeler[f"beat_this:{ck}"] = {"vuruslar": np.asarray(b, float), "olcu": np.asarray(d, float)}
    ses = es.MonoLoader(filename=wav, sampleRate=44100)()
    bpm, eb, guven_es, _, _ = es.RhythmExtractor2013(method="multifeature")(ses)
    uyeler["essentia"] = {"vuruslar": np.asarray(eb, float), "bpm": float(bpm), "guven": float(guven_es)}
    y, sr = librosa.load(wav, sr=22050, mono=True)
    oe = librosa.onset.onset_strength(y=y, sr=sr, hop_length=256, lag=2, max_size=3)
    _, lb = librosa.beat.beat_track(onset_envelope=oe, sr=sr, hop_length=256, units="time", trim=False)
    uyeler["librosa"] = {"vuruslar": np.asarray(lb, float)}

    ref = uyeler["beat_this:final0"]["vuruslar"]
    olcu = uyeler["beat_this:final0"]["olcu"]
    # Beat This! çift tempoya kaçtıysa (ölçü başı aralığı ≈ 8 vuruş) ref'i yarıya indir — ölçü başlarını içeren yarı
    if len(olcu) > 2 and len(ref) > 4:
        vurus_per_olcu = _ibi(olcu) / _ibi(ref)
        if 7.0 < vurus_per_olcu < 9.0:
            a, b = ref[0::2], ref[1::2]
            ref = a if _f(olcu, a) >= _f(olcu, b) else b
    duz = {}
    for ad, u in uyeler.items():
        v, islem = duzeye_getir(u["vuruslar"], ref) if not ad.startswith("beat_this:final0") else (ref, "ref")
        duz[ad] = {"vuruslar": v, "islem": islem}

    # bağımsız kanıt: vuruşlar nota başlangıçlarıyla örtüşüyor mu? (Beat This! kontrol noktaları aynı mimari ve
    # eğitimden geldiği için birbirleriyle uyumları bağımsız kanıt değildir; sentetik yumuşak parçada üçü birlikte yanıldı)
    y22, _ = librosa.load(wav, sr=22050, mono=True)
    hop = 128
    oe = librosa.onset.onset_strength(y=y22, sr=22050, hop_length=hop, lag=2, max_size=3)
    oe = oe / (np.percentile(oe, 99) + 1e-9)
    ofps = 22050 / hop

    def baslangic_skoru(v):
        if len(v) == 0:
            return 0.0
        w = int(0.035 * ofps)
        tepe = [oe[max(0, int(t * ofps) - w): int(t * ofps) + w + 1].max(initial=0) for t in v]
        return float(np.mean(np.clip(tepe, 0, 1)))

    cekirdek = [a for a in duz if a != "librosa"]          # librosa sabit ~30 ms geç ve zayıf; yalnız bilgi
    adlar = list(duz)
    ikili = {}
    for i, a in enumerate(adlar):
        for b in adlar[i + 1:]:
            ikili[f"{a}|{b}"] = {"F": _f(duz[a]["vuruslar"], duz[b]["vuruslar"]),
                                 "IG": _ig(duz[a]["vuruslar"], duz[b]["vuruslar"])}
    def uyum(a):
        return float(np.mean([v["F"] for k, v in ikili.items() if a in k.split("|") and all(x in cekirdek for x in k.split("|"))]))
    skor = {a: {"uyum": uyum(a), "baslangic": baslangic_skoru(duz[a]["vuruslar"])} for a in cekirdek}

    def F_(a, b):
        return ikili.get(f"{a}|{b}", ikili.get(f"{b}|{a}", {"F": 0.0}))["F"]
    # seçim: bağımsız aileyle (essentia) en çok uyuşan Beat This! kontrol noktası; uyum zayıfsa ve essentia nota
    # başlangıçlarıyla belirgin daha iyi örtüşüyorsa essentia.
    bt = [a for a in cekirdek if a.startswith("beat_this")]
    en_iyi_bt = max(bt, key=lambda a: (round(F_(a, "essentia"), 3), skor[a]["baslangic"]))
    secilen = en_iyi_bt
    if F_(en_iyi_bt, "essentia") < 0.6 and (guven_es > 1.5 or
                                           skor["essentia"]["baslangic"] > skor[en_iyi_bt]["baslangic"] + 0.05):
        secilen = "essentia"   # sinir ağı ile sinyal işleme ayrıştı, essentia kendinden emin: o seçilir (güven yine düşük)
    karsi = "essentia" if secilen != "essentia" else en_iyi_bt
    F_karsi = F_(secilen, karsi)
    mma = float(np.mean([v["IG"] for v in ikili.values()]))              # bilgi amaçlı (kısa kliplerde düşük çıkar)
    ck_uyum = [v["F"] for k, v in ikili.items() if k.count("beat_this") == 2]
    ck_min = min(ck_uyum) if ck_uyum else 1.0

    # kayma: yalnız EŞLEŞEN vuruş çiftlerinin farkı (|d| < 70 ms), sabit sapma çıkarılır, 8 eşleşmelik yuvarlanan
    # medyanın en büyük sapması. Ölçülen şey zamanla değişen kaymadır, sabit eğilim değil.
    s_ = duz[secilen]["vuruslar"]; e_ = duz[karsi]["vuruslar"]
    fark = np.array([(e_ - t)[np.argmin(np.abs(e_ - t))] for t in s_]) * 1000 if len(e_) and len(s_) else np.array([])
    eslesen = fark[np.abs(fark) < 70]
    if len(eslesen) >= 8:
        sabit = float(np.median(eslesen))
        yuv = np.array([np.median(eslesen[i:i + 8]) for i in range(len(eslesen) - 7)]) - sabit
        faz_kayma = float(np.max(np.abs(yuv)))
    else:
        sabit, faz_kayma = float(np.median(eslesen)) if len(eslesen) else 0.0, 999.0
    bas_skor = skor[secilen]["baslangic"]

    kosullar = {"aile_uyumu_F>=0.85": F_karsi >= 0.85, "essentia_guveni>1.5": guven_es > 1.5,
                "kontrol_noktalari_F>=0.9": ck_min >= 0.9, "kayma<=25ms": faz_kayma <= 25,
                "baslangic_skoru>=0.5": bas_skor >= 0.5}
    if all(kosullar.values()):
        seviye, guven = "yuksek", 0.9
    elif F_karsi >= 0.6 and guven_es > 1.0:
        seviye, guven = "orta", 0.45
    else:
        seviye, guven = "dusuk", 0.2
    vuruslar = duz[secilen]["vuruslar"]
    olcu_b = olcu if len(olcu) else vuruslar[::4]
    # ölçü başları seçilen vuruşlara oturtulur (en yakın vuruş)
    if len(vuruslar):
        olcu_b = np.array([vuruslar[np.argmin(np.abs(vuruslar - t))] for t in olcu_b])
    yerel_bpm = (60 / np.diff(vuruslar)).tolist() if len(vuruslar) > 1 else []
    return {
        "vuruslar": [round(float(t), 4) for t in vuruslar],
        "olcu_baslari": [round(float(t), 4) for t in np.unique(olcu_b)],
        "bpm_medyan": float(60 / _ibi(vuruslar)) if len(vuruslar) > 2 else None,
        "bpm_yerel": [round(x, 2) for x in yerel_bpm],
        "guven": guven, "guven_seviye": seviye,
        "komite": {"secilen": secilen, "karsi_aile": karsi, "F_aile": round(F_karsi, 3), "mma_bit_bilgi": round(mma, 3),
                   "F_kontrol_noktalari_min": round(ck_min, 3), "essentia_guven": round(float(guven_es), 3),
                   "essentia_bpm": round(float(bpm), 2), "faz_kayma_ms": round(faz_kayma, 1),
                   "sabit_sapma_ms": round(sabit, 1), "baslangic_skoru": round(bas_skor, 3),
                   "kosullar": kosullar, "skorlar": {a: {k: round(v, 3) for k, v in d.items()} for a, d in skor.items()},
                   "uyeler": {a: {"islem": duz[a]["islem"], "sayi": len(duz[a]["vuruslar"])} for a in duz},
                   "ikili": {k: {"F": round(v["F"], 3), "IG": round(v["IG"], 3)} for k, v in ikili.items()}},
        "uye_vuruslari": {a: [round(float(t), 4) for t in duz[a]["vuruslar"]] for a in duz},
    }


def bolumler(wav: str) -> list[dict]:
    """Etiketsiz bölüm sınırları (öz-benzerlik + Laplacian) ve bölüm başına enerji."""
    import librosa
    y, sr = librosa.load(wav, sr=22050, mono=True)
    hop = 512
    C = librosa.amplitude_to_db(np.abs(librosa.cqt(y=y, sr=sr, hop_length=hop, n_bins=72, bins_per_octave=12)), ref=np.max)
    sinir = librosa.segment.agglomerative(C, k=max(2, min(12, int(len(y) / sr / 20))))
    t = librosa.frames_to_time(sinir, sr=sr, hop_length=hop).tolist() + [len(y) / sr]
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    out = []
    for a, b in zip(t, t[1:]):
        i0, i1 = int(a * sr / hop), max(int(a * sr / hop) + 1, int(b * sr / hop))
        out.append({"bas": round(a, 3), "son": round(b, 3), "enerji_db": round(float(20 * np.log10(rms[i0:i1].mean() + 1e-9)), 1)})
    return out


if __name__ == "__main__":
    wav, cikti = sys.argv[1], sys.argv[2]
    hizli = "--hizli" in sys.argv
    sonuc = ritim_komitesi(wav, hizli)
    try:
        sonuc["bolumler"] = bolumler(wav)
    except Exception as e:                                   # bölümleme isteğe bağlı
        sonuc["bolumler"] = []
        sonuc["bolum_hatasi"] = str(e)
    with open(cikti, "w") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=1)
