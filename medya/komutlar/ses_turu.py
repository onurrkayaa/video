"""medya ses-turu <video> — ses yalnız müzik mi, yoksa çekimlerin kendi sesi (konuşma, gülüş) karışık mı?

Sahneleri yeniden sıralamadan ÖNCE çalıştırılır. Çekim sesi karışıksa, sıralama değiştiğinde sesler yanlış
görüntülerin altına düşer: o durumda ses katmanlara ayrılmalı (medya ayir) ya da her çekim kendi sesiyle
taşınmalıdır.

Yöntem: görüntü kesim noktalarında sesin tayfı, rastgele anlara göre belirgin biçimde değişiyorsa çekim
sesi vardır (müzik kesimlerden habersiz akar). Kesimlerin ne kadarının rastgele anların 95. yüzdeliğini
aştığına bakılır.
"""
from __future__ import annotations

import numpy as np

from ..ortak import json_yaz, probe, ses_akisi, ses_oku
from .sahneler import kesimleri_bul


def _tayf(x: np.ndarray, sr: int, n: int = 2048, h: int = 512) -> tuple[np.ndarray, float]:
    kare = (len(x) - n) // h
    if kare <= 0:
        return np.zeros((0, n // 2 + 1)), sr / h
    idx = np.arange(n)[None, :] + h * np.arange(kare)[:, None]
    S = np.abs(np.fft.rfft(x[idx] * np.hanning(n), axis=1)).astype(np.float32)
    return np.log(S + 1e-5), sr / h


def degisim(L: np.ndarray, fps: float, t: float, w: float = 0.25) -> float:
    i, k = int(t * fps), max(1, int(w * fps))
    if i - k < 0 or i + 1 + k > len(L):
        return float("nan")
    return float(np.abs(L[i - k:i].mean(0) - L[i + 1:i + 1 + k].mean(0)).mean())


def ses_turu(video: str) -> dict:
    p = probe(video)
    if not ses_akisi(p):
        return {"karar": "ses-yok"}
    x, sr = ses_oku(video, sr=22050)
    if np.sqrt(np.mean(x ** 2)) < 1e-4:
        return {"karar": "sessiz"}
    L, fps = _tayf(x, sr)
    sure = len(x) / sr
    kesimler, _ = kesimleri_bul(video)
    kesimler = [t for t in kesimler if 0.5 < t < sure - 0.5]
    if len(kesimler) < 4:
        return {"karar": "belirsiz", "neden": f"yalnız {len(kesimler)} kesim var; ölçüm için az", "kesim_sayisi": len(kesimler)}
    rng = np.random.default_rng(7)
    rast = [t for t in rng.uniform(0.5, sure - 0.5, 400) if min(abs(t - c) for c in kesimler) > 1.0]
    dk = np.array([degisim(L, fps, t) for t in kesimler]); dk = dk[~np.isnan(dk)]
    dr = np.array([degisim(L, fps, t) for t in rast]); dr = dr[~np.isnan(dr)]
    p95 = float(np.percentile(dr, 95))
    asan = float(np.mean(dk > p95))
    oran_ = float(np.median(dk) / np.median(dr))
    if asan >= 0.30 or oran_ >= 1.5:
        karar = "karisik"
    elif asan <= 0.12 and oran_ <= 1.15:
        karar = "yalniz-muzik-ya-da-surekli-ses"
    else:
        karar = "belirsiz"
    return {"karar": karar, "kesim_sayisi": len(dk), "kesimde_degisim_medyan": float(np.median(dk)),
            "rastgele_degisim_medyan": float(np.median(dr)), "rastgele_p95": p95,
            "p95_asan_kesim_orani": asan, "medyan_orani": oran_,
            "yorum": {"karisik": "Çekim sesi var: sıralama değişirse ses katmanlara ayrılmalı ya da çekimle taşınmalı.",
                      "yalniz-muzik-ya-da-surekli-ses": "Ses kesimlerden bağımsız akıyor (büyük olasılıkla yalnız müzik). "
                                                         "Sıralama sesi bozmaz; ama müzikle eşleşen anlar kaybolabilir.",
                      "belirsiz": "Kesin değil: konuşma tespiti (medya yaziya-dok) ve katman ayırma ile doğrula."}[karar]}


def calistir_(args) -> int:
    r = ses_turu(args.video)
    print(f"karar: {r['karar']}")
    for k, v in r.items():
        if k != "karar":
            print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")
    if args.json:
        json_yaz(args.json, r)
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="ses türü (müzik / karışık)")
    p.add_argument("video")
    p.add_argument("--json")
    p.set_defaults(islev=calistir_)
