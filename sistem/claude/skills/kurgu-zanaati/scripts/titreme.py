#!/usr/bin/env python3
"""Kamera titremesini ölçer — sabitlemeden ÖNCE (gerekli mi?) ve SONRA (işe yaradı mı?). Ölçmeden vid.stab uygulanmaz.

  $MEDYA/.venv/bin/python titreme.py <video> [--bas sn] [--sure sn] [--json]

Yöntem: ardışık gri kareler (uzun kenar 320 px) arasında faz ilintisi → küresel kayma → kamera yolu; titreme = yolun
~1 sn kayan ortalamadan sapmasının RMS'i / uzun kenar. Yavaş, bilinçli hareket (pan) ortalamada kalır; yalnız hızlı sarsıntı
sayılır. Eşik 0,004 başparmak kuralıdır (araştırma örneği); asıl ölçüt aynı çekim setinde göreli sıra ve sabitleme
sonrası en az %50 düşüş.
Sınama (2026-10-05, yapay 640x360): sabit 0,0000; düzgün pan 0,0000; 3–5 Hz sarsıntı 0,0130 → vid.stab sonrası 0,0003.
Desensiz dokuda (renk şeritleri) vid.stab işe yaramadı (0,0118 → 0,0114) ve tripod=1 kötüleştirdi (0,0498):
sabitlenmiş klibi bu ölçüm geçmeden kullanma.
Sınama 2 (2026-10-05, durağan resimden 320x240): sabit 0,0000; düzgün pan 0,0018; 4–5 Hz sarsıntı 0,0548 → vid.stab
(smoothing=15:optzoom=1) sonrası 0,0003. SINIR: kadrajın büyük kısmını kaplayan özne hareketi kamera hareketi sanılır
(sabit kamerada hareketli test deseni 0,0376 verdi) → tek başına karar değil; kontak sayfasıyla birlikte oku.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

import numpy as np

from medya.ortak import ffmpeg, oran, probe, video_akisi

GEN = 320  # analiz genişliği (px)


def kareler(video: str, bas: float | None, sure: float | None) -> tuple[np.ndarray, float]:
    v = video_akisi(probe(video)) or {}
    if not v:
        raise SystemExit(f"video akışı yok: {video}")
    w, h = int(v["width"]), int(v["height"])
    don = 0
    for sd in v.get("side_data_list") or []:
        if "rotation" in sd:
            don = int(round(float(sd["rotation"])))
    if abs(don) in (90, 270):                     # ffmpeg çözerken döndürür: görünen boyut
        w, h = h, w
    # uzun kenar GEN px: dikey ve yatay çekim aynı ölçekte karşılaştırılır
    gw, gy = (GEN, max(2, round(GEN * h / w / 2) * 2)) if w >= h else (max(2, round(GEN * w / h / 2) * 2), GEN)
    komut = [ffmpeg(), "-nostdin", "-v", "error"]
    if bas is not None:
        komut += ["-ss", f"{bas:.4f}"]
    if sure is not None:
        komut += ["-t", f"{sure:.4f}"]
    komut += ["-i", video, "-an", "-vf", f"scale={gw}:{gy},format=gray", "-f", "rawvideo", "-"]
    s = subprocess.run(komut, capture_output=True, stdin=subprocess.DEVNULL)
    if s.returncode:
        raise SystemExit(s.stderr.decode("utf-8", "replace")[-800:])
    k = np.frombuffer(s.stdout, np.uint8).reshape(-1, gy, gw).astype(np.float32)
    return k, oran(v.get("avg_frame_rate")) or 30.0


def kayma(a: np.ndarray, b: np.ndarray, pencere: np.ndarray) -> tuple[float, float]:
    """b'nin a'ya göre küresel kayması (px), alt piksel (parabol)."""
    A = np.fft.rfft2((a - a.mean()) * pencere)
    B = np.fft.rfft2((b - b.mean()) * pencere)
    R = A * np.conj(B)
    R /= np.abs(R) + 1e-9
    r = np.fft.irfft2(R, s=a.shape)
    iy, ix = np.unravel_index(np.argmax(r), r.shape)

    def alt(c0, c1, c2):
        d = c0 - 2 * c1 + c2
        return 0.0 if abs(d) < 1e-12 else 0.5 * (c0 - c2) / d

    H, W = r.shape
    dy = iy + alt(r[(iy - 1) % H, ix], r[iy, ix], r[(iy + 1) % H, ix])
    dx = ix + alt(r[iy, (ix - 1) % W], r[iy, ix], r[iy, (ix + 1) % W])
    return float(dx - W if dx > W / 2 else dx), float(dy - H if dy > H / 2 else dy)


def titreme(video: str, bas: float | None = None, sure: float | None = None) -> dict:
    k, fps = kareler(video, bas, sure)
    n = max(3, int(round(fps)) | 1)                        # ~1 sn, tek sayı
    if len(k) < n + 8:
        return {"video": video, "olculemedi": True, "neden": f"{len(k)} kare; en az {n + 8} gerekir"}
    pencere = np.outer(np.hanning(k.shape[1]), np.hanning(k.shape[2])).astype(np.float32)
    d = np.array([kayma(k[i - 1], k[i], pencere) for i in range(1, len(k))])
    yol = np.vstack([[0.0, 0.0], np.cumsum(d, axis=0)])
    duz = np.stack([np.convolve(yol[:, j], np.ones(n) / n, "valid") for j in range(2)], 1)
    sapma = yol[n // 2:len(yol) - n // 2] - duz             # yalnız pencere dolu iç kareler
    rms = float(np.sqrt((sapma ** 2).sum(1).mean()))
    return {"video": video, "kare": int(len(k)), "fps": round(fps, 3), "titreme": round(rms / GEN, 5),
            "titreme_px_320": round(rms, 2), "en_buyuk_sapma_px_320": round(float(np.abs(sapma).max()), 2),
            "esik_basparmak": 0.004}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("video")
    p.add_argument("--bas", type=float)
    p.add_argument("--sure", type=float, help="en az ~1 sn + 8 kare gerekir (30 fps: 1,3 sn; 120 fps: 1,08 sn); "
                   "kısa kesitte 'olculemedi' döner — --sure 1.5 ver")
    p.add_argument("--json", action="store_true", help="yalnız JSON yaz")
    x = p.parse_args()
    r = titreme(x.video, x.bas, x.sure)
    if x.json:
        print(json.dumps(r, ensure_ascii=False))
        return 0
    if r.get("olculemedi"):
        print(f"ölçülemedi: {r['neden']}")
        return 1
    yorum = "yüksek → sabitlemeyi düşün" if r["titreme"] >= r["esik_basparmak"] else "düşük → sabitleme gerekmez"
    print(f"titreme {r['titreme']:.4f} (uzun kenara oranla; {r['titreme_px_320']} px @320) — {yorum} [{r['kare']} kare]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
