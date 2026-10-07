#!/usr/bin/env python3
"""Ağır çekimde yinelenen kare oranı: ardışık kare farkı (tblend difference, YAVG) iki komşusunun küçüğünün yarısından
azsa o kare "yinelenen" sayılır (gerçek akışta fark düzgün değişir; yinelenen karede çukur yapar, kayıplı kodlamada bile).

  $MEDYA/.venv/bin/python yinelenen.py <video> [--bas sn --sure sn]

Yalnız ağır çekim aralığını ver (geçiş/erime dışında). Geçer: %0–3. HyperFrames data-playback-rate 0.5 ≈ %50.
Sınama (2026-10-05, 320x240 fikstür): HyperFrames data-playback-rate 0.5 taslağı %48,3; 15→30 fps yinelenmiş kaynak
%48,3; rampa.py çıktısı (120 fps kaynak, 0,25x) %0; düz 30 fps %0; çift piksele yuvarlanan yavaş kırpma-pan %40,7 (gerçek
tekrar). mpdecimate varsayılanı yavaş harekette yanılır (yinelenmeyen rampada 78/127 "drop").
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys

from medya.ortak import ffmpeg


def farklar(video: str, bas: float | None, sure: float | None) -> list[float]:
    k = [ffmpeg(), "-nostdin", "-v", "error"]
    if bas is not None:
        k += ["-ss", f"{bas:.4f}"]
    if sure is not None:
        k += ["-t", f"{sure:.4f}"]
    k += ["-i", video, "-an", "-vf",
          "tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"]
    s = subprocess.run(k, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if s.returncode:
        raise SystemExit(s.stderr[-800:])
    return [float(x) for x in re.findall(r"YAVG=([0-9.]+)", s.stdout)][1:]   # ilk değer kendisiyle fark (0)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("video")
    p.add_argument("--bas", type=float)
    p.add_argument("--sure", type=float)
    x = p.parse_args()
    d = farklar(x.video, x.bas, x.sure)
    if len(d) < 5:
        print("ölçülemedi: kare az")
        return 1
    cukur = [i + 1 for i in range(1, len(d) - 1) if d[i] < 0.5 * min(d[i - 1], d[i + 1])]
    oran = len(cukur) / len(d)
    print(f"yinelenen kare: {len(cukur)}/{len(d)} (%{100 * oran:.1f}) — {'GEÇTİ' if oran <= 0.03 else 'KALDI: kare tekrarı'}")
    return 0 if oran <= 0.03 else 1


if __name__ == "__main__":
    sys.exit(main())
