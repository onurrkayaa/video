#!/usr/bin/env python3
"""Hız rampası: 1x → yavaş → tutma → 1x, yalnız GERÇEK yüksek kare hızlı kaynakta (ara kare üretmez; her çıktı
karesi gerçek bir kaynak karesidir). Sabit hızlı ağır çekim için bu değil `medya yavaslat` kullanılır.

  $MEDYA/.venv/bin/python rampa.py <girdi> --cikti calisma/klipler/<ad>-rampa.mp4 \\
        --hiz 0.25 --a 0.8 --b 1.0 --c 1.6 --d 1.8 [--bas S --sure L] [--fps 30]

Zamanlar KESİTİN (--bas'tan sonraki) kaynak saniyeleridir:
  [0,a) 1x · [a,b) 1x→hiz (hız kaynak zamanında doğrusal) · [b,c) hiz'de tutma · [c,d) hiz→1x · [d,…) 1x
Kapalı biçim: rampa t = ln(1+kΔ)/k, tutma Δ/hiz (setpts). Kaynak gerçek fps ≥ fps/hiz olmalı (240 fps → 0,125x;
120 → 0,25x; 60 → 0,5x); değilse kare yinelenir → durur. HDR kaynak mobius ile SDR'ye çevrilir (medya sdr gibi).
Çıktı sessizdir; .mov → ProRes 422 HQ, diğerleri H.264 CRF 12 (bt709). Sonda kare sayısı tahminle karşılaştırılır.
Sınama (2026-10-05): 120 fps kare-numaralı kaynakta 154/154 kare, 0 yinelenen, tutmada her çıktı karesi = 1 kaynak karesi.
"""
from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

from medya.komutlar.incele import incele_dosya
from medya.ortak import MedyaHatasi, calistir, ffmpeg, probe

TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv,")


def zaman(T: float, a: float, b: float, c: float, d: float, r: float) -> float:
    """Kesit içi kaynak zamanı T → çıktı zamanı (sn)."""
    k1, k2 = (r - 1) / (b - a), (1 - r) / (d - c)
    tb = a + math.log(1 + k1 * (b - a)) / k1
    tc = tb + (c - b) / r
    td = tc + math.log((r + k2 * (d - c)) / r) / k2
    if T < a:
        return T
    if T < b:
        return a + math.log(1 + k1 * (T - a)) / k1
    if T < c:
        return tb + (T - b) / r
    if T < d:
        return tc + math.log((r + k2 * (T - c)) / r) / k2
    return td + (T - d)


def ifade(a: float, b: float, c: float, d: float, r: float) -> str:
    k1, k2 = (r - 1) / (b - a), (1 - r) / (d - c)
    tb = a + math.log(1 + k1 * (b - a)) / k1
    tc = tb + (c - b) / r
    td = tc + math.log((r + k2 * (d - c)) / r) / k2
    g = lambda x: f"{x:.9g}"
    return (f"if(lt(T,{g(a)}),T,"
            f"if(lt(T,{g(b)}),{g(a)}+log(1+({g(k1)})*(T-{g(a)}))/({g(k1)}),"
            f"if(lt(T,{g(c)}),{g(tb)}+(T-{g(b)})/{g(r)},"
            f"if(lt(T,{g(d)}),{g(tc)}+log(({g(r)}+({g(k2)})*(T-{g(c)}))/{g(r)})/({g(k2)}),"
            f"{g(td)}+(T-{g(d)})))))")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("girdi")
    p.add_argument("--cikti", required=True, help="calisma/klipler/<ad>-rampa.mp4 (.mov → ProRes)")
    p.add_argument("--hiz", type=float, required=True, help="en yavaş oynatma hızı, ör. 0.25")
    for ad in "abcd":
        p.add_argument(f"--{ad}", type=float, required=True)
    p.add_argument("--bas", type=float, help="kesit başlangıcı (kaynak sn)")
    p.add_argument("--sure", type=float, help="kesit süresi (kaynak sn)")
    p.add_argument("--fps", type=float, default=30.0, help="çıktı kare hızı (kompozisyonun fps'i)")
    x = p.parse_args()
    a, b, c, d, r = x.a, x.b, x.c, x.d, x.hiz
    if not (0 < r < 1 and 0 <= a < b <= c < d):
        print("HATA: 0 < hiz < 1 ve 0 ≤ a < b ≤ c < d olmalı", file=sys.stderr)
        return 2
    if Path(x.cikti).resolve() == Path(x.girdi).resolve():
        print("HATA: çıktı girdinin üzerine yazamaz", file=sys.stderr)
        return 2
    v = incele_dosya(x.girdi).get("video") or {}
    if not v:
        print("HATA: video akışı yok", file=sys.stderr)
        return 2
    kfps = v["kare_olcumu"].get("gercek_fps") or v["fps_nominal"]
    if kfps < x.fps / r * 0.98:
        print(f"HATA: kaynağın gerçek kare hızı {kfps:.1f}; {r:g}x için en az {x.fps / r:g} fps gerekir (kare yinelenir). "
              "Sabit ağır çekim: medya yavaslat; geçişi hız kesmesiyle (1x çekim → yavaş klip, vuruşta kesme) yap.",
              file=sys.stderr)
        return 2
    kesit = x.sure if x.sure is not None else float(probe(x.girdi)["format"]["duration"]) - (x.bas or 0.0)
    if kesit <= d:
        print(f"HATA: kesit {kesit:.3f} sn; rampa sonu d={d:g} kesitin içinde olmalı", file=sys.stderr)
        return 2
    beklenen = round(zaman(kesit, a, b, c, d, r) * x.fps)
    # yarım kaynak karesi kaydırma: fps süzgecinin eşit uzaklıkta kararsız seçimini (1x bölümde sıçrama) önler
    vf = (TONEMAP if v.get("hdr") else "") + \
        f"setpts='({ifade(a, b, c, d, r)})/TB+{0.5 / kfps:.9g}/TB',fps=fps={x.fps:g},setsar=1"
    komut = [ffmpeg(), "-nostdin", "-v", "error", "-y"]
    if x.bas is not None:
        komut += ["-ss", f"{x.bas:.4f}"]
    komut += ["-t", f"{kesit:.4f}", "-i", x.girdi, "-an"]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(vf)
    komut += ["-filter_script:v", f.name, "-frames:v", str(beklenen + 5)]          # kaçak akışa sigorta
    if x.cikti.lower().endswith(".mov"):
        komut += ["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le"]
    else:
        komut += ["-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p"]
    komut += ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", x.cikti]
    try:
        calistir(komut, hata_mesaji="rampa kodlanamadı")
    except MedyaHatasi as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1
    finally:
        Path(f.name).unlink(missing_ok=True)
    s = next(s for s in probe(x.cikti)["streams"] if s.get("codec_type") == "video")
    n = int(s.get("nb_frames") or 0)
    print(f"rampa: kaynak {kfps:.1f} fps, en yavaş {r:g}x → {x.cikti} ({n} kare, beklenen {beklenen})")
    for ad, T in (("rampa başı a", a), ("en yavaş b", b), ("tutma sonu c", c), ("rampa sonu d", d)):
        print(f"  {ad}: kaynak {T:g} sn → klipte {zaman(T, a, b, c, d, r):.3f} sn")
    print("  planda: klip = bu dosya, klip_bas 0, hiz = en yavaş hız; en yavaş anı (b–c) vuruş/doruk üstüne koy")
    if abs(n - beklenen) > 1:
        print(f"⚠ kare sayısı tahminden {n - beklenen:+d} sapıyor: medya kontak ile bak", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
