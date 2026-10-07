"""medya senkron <video> --muzik analiz/muzik.json [--plan plan.json] — kesimler vuruşa ne kadar yakın?

"Vuruşta kestim" demeden önce ÖLÇÜLÜR. Kesimler HER ZAMAN çizilmiş videodan bulunur; plan verilirse yalnız
"vurusa" işaretli planlı kesimler (±3 kare içindeki) videodaki kesimle eşlenir ve ölçülen o olur — plandaki
zaman değil (2026-10-05: eskiden plan zamanı ölçülüyordu; çizim plandan saptıysa görünmezdi). Videoda
bulunamayan planlı kesim "olculemedi" listesine girer. Plan sözleşmesi: muzik.bas = müzik dosyasında videonun
0. saniyesine denk gelen an → videodaki vuruş = müzikteki vuruş − bas (medya nle ile aynı). Ayrıca sesin başlangıç zarfı, vuruşlar ve kesimler tek bir görselde
çizilir (Claude sesi duyamaz; görsel ve sayıyla doğrular).

Kabul ölçütü (varsayılan): vuruşa işaretli kesimlerin p90 |sapma| ≤ 40 ms ve en büyük ≤ 70 ms; müzik
analizinin güveni düşükse karar "güvenilmez" olur — o durumda vuruş iddiasında bulunulmaz.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ..ortak import MedyaHatasi, json_oku, json_yaz, oran, probe, ses_oku
from .kontak import YAZI


def baslangic_zarfi(x: np.ndarray, sr: int, h: int = 256) -> tuple[np.ndarray, float]:
    """Tayfsal akı (log-büyüklük artışlarının toplamı), yerel ortalaması çıkarılmış."""
    n = 1024
    kare = (len(x) - n) // h
    idx = np.arange(n)[None, :] + h * np.arange(max(kare, 0))[:, None]
    S = np.log1p(100 * np.abs(np.fft.rfft(x[idx] * np.hanning(n), axis=1)))
    aki = np.concatenate([[0], np.maximum(0, np.diff(S, axis=0)).sum(1)])
    fps = sr / h
    w = max(1, int(0.4 * fps))
    aki = np.maximum(aki - np.convolve(aki, np.ones(w) / w, "same"), 0)
    return aki / (aki.max() + 1e-9), fps


def sapmalar(kesimler: list[float], vuruslar: list[float]) -> np.ndarray:
    v = np.asarray(sorted(vuruslar))
    if len(v) == 0:
        raise MedyaHatasi("vuruş listesi boş")
    k = np.asarray(kesimler)
    i = np.clip(np.searchsorted(v, k), 1, len(v) - 1)
    sol, sag = v[i - 1], v[i]
    yakin = np.where(np.abs(k - sol) <= np.abs(k - sag), sol, sag)
    return (k - yakin) * 1000.0


def ciz(video: str, kesimler, vuruslar, olcu, cikti: Path, satir_sn: float = 30.0) -> Path:
    x, sr = ses_oku(video, sr=22050)
    zarf, fps = baslangic_zarfi(x, sr)
    sure = len(x) / sr
    satir = int(np.ceil(sure / satir_sn))
    W, H = 1800, 110
    im = Image.new("RGB", (W, satir * H + 20), (16, 16, 20))
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype(YAZI, 12)
    except OSError:
        f = ImageFont.load_default()
    px = lambda t: int((t % satir_sn) / satir_sn * (W - 60)) + 50
    for r in range(satir):
        y0 = 10 + r * H
        a, b = r * satir_sn, min((r + 1) * satir_sn, sure)
        d.text((4, y0 + 40), f"{a:.0f}s", font=f, fill=(150, 150, 150))
        i0, i1 = int(a * fps), int(b * fps)
        seg = zarf[i0:i1]
        for j in range(0, len(seg), 2):
            t = a + j / fps
            h = int(seg[j] * (H - 30))
            d.line([(px(t), y0 + H - 15), (px(t), y0 + H - 15 - h)], fill=(90, 140, 200))
        for t in vuruslar:
            if a <= t < b:
                d.line([(px(t), y0 + 5), (px(t), y0 + H - 15)], fill=(70, 70, 80))
        for t in olcu:
            if a <= t < b:
                d.line([(px(t), y0 + 5), (px(t), y0 + H - 15)], fill=(200, 200, 90), width=2)
        for t in kesimler:
            if a <= t < b:
                d.line([(px(t), y0), (px(t), y0 + H - 10)], fill=(240, 60, 60), width=2)
    d.text((50, satir * H + 4), "mavi: başlangıç zarfı · gri: vuruş · sarı: ölçü başı · kırmızı: kesim", font=f,
           fill=(200, 200, 200))
    im.save(cikti)
    return cikti


def senkron(video: str, muzik: dict, plan: dict | None = None, *, esik_p90: float = 40, esik_max: float = 70) -> dict:
    vuruslar = muzik.get("vuruslar") or []
    olcu = muzik.get("olcu_baslari") or []
    kaydirma = muzik_kaymasi(plan)
    vuruslar = [t - kaydirma for t in vuruslar]
    olcu = [t - kaydirma for t in olcu]
    from .sahneler import kesimleri_bul
    p = probe(video)
    sure = float(p["format"]["duration"])
    v = next((x for x in p.get("streams", []) if x.get("codec_type") == "video"), {})
    fps = oran(v.get("r_frame_rate")) or 30.0
    bulunan, _ = kesimleri_bul(video, esik=0.2, en_kisa=0.3)
    olculemedi = []
    if plan and plan.get("cekimler"):
        kesimler = []
        for t in [c["cikti_bas"] for c in plan["cekimler"][1:] if c.get("vurusa", True)]:
            yakin = min(bulunan, key=lambda b: abs(b - t)) if bulunan else None
            if yakin is not None and abs(yakin - t) <= 3 / fps:
                kesimler.append(yakin)
            else:
                olculemedi.append(round(t, 3))
        kaynak = "video (plandaki vurusa kesimlerine eşlendi)"
    else:
        kesimler, kaynak = bulunan, "video"
    kesimler = [t for t in kesimler if 0 < t < sure]
    if not kesimler:
        return {"karar": "kesim-yok", "olculemedi": olculemedi}
    s = sapmalar(kesimler, vuruslar)
    a = np.abs(s)
    sonuc = {"kesim_kaynagi": kaynak, "kesim_sayisi": len(kesimler), "medyan_ms": float(np.median(a)),
             "p90_ms": float(np.percentile(a, 90)), "en_buyuk_ms": float(a.max()),
             "isaretli_ortalama_ms": float(np.mean(s)), "kare_ici_oran": float(np.mean(a <= 1000 / 30)),
             "muzik_guveni": muzik.get("guven"), "saglayici": muzik.get("saglayici"),
             "kesimler": [{"t": round(t, 3), "sapma_ms": round(float(x), 1)} for t, x in zip(kesimler, s)],
             "olculemedi": olculemedi}
    if olcu:
        so = np.abs(sapmalar(kesimler, olcu))
        sonuc["olcu_basina_kare_ici_oran"] = float(np.mean(so <= 1000 / 30))
    guven = muzik.get("guven")
    if guven is not None and guven < 0.5:
        sonuc["karar"] = "guvenilmez"
        sonuc["neden"] = f"müzik analizi güveni düşük ({guven:.2f}); vuruşa oturduğu iddia edilemez"
    else:
        sonuc["karar"] = "vurusta" if sonuc["p90_ms"] <= esik_p90 and sonuc["en_buyuk_ms"] <= esik_max else "kayik"
        h = ses_hizasi(video, muzik, plan)
        sonuc["ses_hizasi"] = h
        if h and not h.get("olculemedi") and h["ilinti"] >= 0.5 and abs(h["gecikme_ms"]) > 5:
            sonuc["karar"] = "kayik"
            sonuc["neden"] = (f"çizimdeki ses müziğe göre {h['gecikme_ms']:+.1f} ms kaymış (ilinti {h['ilinti']:.2f}): "
                              "kesimler vuruşta olsa da duyulan vuruş görüntüden kayık")
        elif h and (h.get("olculemedi") or h["ilinti"] < 0.5):
            sonuc.setdefault("uyari", []).append("ses hizası ölçülemedi (miks müzikten çok farklı ya da kısa)")
        if olculemedi and sonuc["karar"] == "vurusta":
            sonuc["karar"] = "kismi"
            sonuc["neden"] = (f"{len(olculemedi)} planlı vuruş kesimi videoda bulunamadı (ölçülemedi): "
                              f"{olculemedi[:5]} — bu anları temas sayfasıyla kontrol et")
    return sonuc


def ses_hizasi(video: str, muzik: dict, plan: dict | None, *, sr: int = 16000, sure: float = 20.0,
               ara: float = 0.25) -> dict | None:
    """Çizimdeki sesin analiz edilen müzik WAV'ına göre kayması (ms; + = çizimdeki ses geç). Kesimler vuruşa denk
    gelse bile ses kaydıysa "vurusta" yanıltır — 2026-10-04 "sesler kaymış" türü hata (uçtan uca denetimin önerisi)."""
    wav = muzik.get("ana_wav")
    if not wav or not Path(wav).exists():
        return None
    x, _ = ses_oku(wav, sr=sr, bas=max(0.0, muzik_kaymasi(plan)), sure=sure)      # müzik, videonun 0. sn'sinden
    y, _ = ses_oku(video, sr=sr, bas=0.0, sure=sure, zamanli=True)                # çizimin sesi, oynatıcı gibi
    n = min(len(x), len(y))
    if n < sr:
        return {"olculemedi": True}
    x, y = x[:n] - x[:n].mean(), y[:n] - y[:n].mean()
    m = 1 << int(np.ceil(np.log2(2 * n)))
    c = np.fft.irfft(np.fft.rfft(y, m) * np.conj(np.fft.rfft(x, m)), m)
    k = int(ara * sr)
    aday = np.concatenate([c[-k:], c[:k + 1]])
    j = int(np.argmax(aday)) - k
    ilinti = float(aday.max() / (np.sqrt((x ** 2).sum() * (y ** 2).sum()) + 1e-12))
    return {"gecikme_ms": round(j / sr * 1000, 2), "ilinti": round(ilinti, 3)}


def muzik_kaymasi(plan: dict | None) -> float:
    """Plan sözleşmesi: muzik.bas = müzik dosyasında videonun 0. saniyesine denk gelen an (sn)."""
    return float(((plan or {}).get("muzik") or {}).get("bas", 0.0))


def calistir_(args) -> int:
    muzik = json_oku(args.muzik)
    plan = json_oku(args.plan) if args.plan else None
    r = senkron(args.video, muzik, plan)
    if r.get("karar") == "kesim-yok":
        print("kesim bulunamadı")
        return 1
    print(f"karar: {r['karar']} — {r['kesim_sayisi']} kesim ({r['kesim_kaynagi']}), medyan {r['medyan_ms']:.0f} ms, "
          f"p90 {r['p90_ms']:.0f} ms, en büyük {r['en_buyuk_ms']:.0f} ms, kare içi %{100 * r['kare_ici_oran']:.0f}")
    if r.get("neden"):
        print(f"  ⚠ {r['neden']}")
    kotu = sorted(r["kesimler"], key=lambda k: -abs(k["sapma_ms"]))[:5]
    print("  en kayık kesimler: " + ", ".join(f"{k['t']:.2f}s ({k['sapma_ms']:+.0f} ms)" for k in kotu))
    taban = Path(args.json or str(Path(args.video).with_suffix("")) + "-senkron.json")
    json_yaz(taban, r)
    k = muzik_kaymasi(plan)
    g = ciz(args.video, [x["t"] for x in r.get("kesimler", [])], [t - k for t in muzik.get("vuruslar", [])],
            [t - k for t in muzik.get("olcu_baslari", [])], taban.with_suffix(".png"))
    print(f"→ {taban}\n→ {g} (görsel kontrol)")
    return 0 if r["karar"] == "vurusta" else 1


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="kesim–vuruş senkron ölçümü")
    p.add_argument("video")
    p.add_argument("--muzik", required=True, help="medya muzik çıktısı (JSON)")
    p.add_argument("--plan", help="kurgu planı (JSON); yoksa kesimler videodan bulunur")
    p.add_argument("--json")
    p.set_defaults(islev=calistir_)
