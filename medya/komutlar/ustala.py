"""medya ustala <girdi> [--hedef -16] [--tepe -1.5] [--cikti …] — ses düzeyini hedefe getirir.

1) EBU R128 ile ölçer (entegre LUFS, gerçek tepe dBTP). 2) Gereken kazancı uygular, alimiter ile tepeyi
sınırlar. 3) Yeniden ölçer; gerçek tepe hedefi aşıyorsa sınırı düşürüp tekrarlar (en çok 3 tur).
Videoda görüntü akışı KOPYALANIR (yeniden kodlanmaz). Asıl dosyanın üzerine yazmaz: varsayılan çıktı
<ad>-usta.<uzantı>. Sesi dinleyemeyiz; yalnız ölçüm raporlanır.

Hedefler: sosyal medya/web -14…-16 LUFS, tepe ≤ -1,0…-1,5 dBTP; yayın -23 LUFS.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..ortak import MedyaHatasi, calistir, ffmpeg, json_yaz, probe, video_akisi


def olc(yol: str | Path) -> dict:
    s = calistir([ffmpeg(), "-nostdin", "-nostats", "-i", str(yol), "-vn", "-af", "ebur128=peak=true:framelog=quiet",
                  "-f", "null", "-"])
    metin = s.stderr.decode("utf-8", "replace")
    ozet = metin[metin.rfind("Summary:"):]
    def sayi(desen):
        m = re.search(desen, ozet)
        return float(m.group(1)) if m else float("nan")
    return {"lufs": sayi(r"I:\s+(-?[\d.]+|-inf) LUFS"), "lra": sayi(r"LRA:\s+(-?[\d.]+) LU"),
            "tepe_dbtp": sayi(r"Peak:\s+(-?[\d.]+|-inf) dBFS")}


def ustala(girdi: str, cikti: str, hedef: float = -16.0, tepe: float = -1.5) -> dict:
    once = olc(girdi)
    if once["lufs"] != once["lufs"] or once["lufs"] < -70:
        raise MedyaHatasi(f"ölçülebilir ses yok ({once})")
    p = probe(girdi)
    video_var = video_akisi(p) is not None
    sure = float(p["format"]["duration"])
    wav = Path(cikti).suffix.lower() in (".wav", ".aif", ".aiff")
    if abs(hedef - once["lufs"]) <= 0.5 and once["tepe_dbtp"] <= tepe:
        # zaten hedefte: yeni bir kodlama kuşağı ekleme (uçtan uca denetim: +0,0 dB'de AAC yeniden kodlanıyordu)
        komut = [ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", girdi]
        komut += (["-map", "0:v:0", "-map", "0:a:0", "-c", "copy"] if video_var else ["-map", "0:a:0", "-c", "copy"])
        calistir(komut + ([] if wav else ["-movflags", "+faststart"]) + [cikti])
        sonra = olc(cikti)
        return {"once": once, "sonra": sonra, "kazanc_db": 0.0, "tur": 0, "kopya": True, "hedef_lufs": hedef,
                "hedef_tepe_dbtp": tepe, "gecti": True}
    sinir_db = tepe - 0.6                                   # örnek tepesi; gerçek tepe bunun biraz üstüne çıkabilir
    kazanc = hedef - once["lufs"]
    for tur in range(5):
        sinir = 10 ** (sinir_db / 20)
        af = (f"volume={kazanc:.2f}dB,alimiter=limit={sinir:.4f}:attack=4:release=60:level=disabled:asc=1:latency=1,"
              "aresample=48000")   # latency=1: sınırlayıcının ~4 ms gecikmesini telafi eder (ölçüldü)
        komut = [ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", girdi]
        if video_var:
            komut += ["-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy", "-t", f"{sure:.3f}"]
        komut += ["-af", af]
        komut += ["-c:a", "pcm_s24le"] if wav else ["-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart"]
        calistir(komut + [cikti])
        sonra = olc(cikti)
        tepe_ok = sonra["tepe_dbtp"] <= tepe + 0.05
        lufs_ok = abs(sonra["lufs"] - hedef) <= 0.5
        if tepe_ok and lufs_ok:
            break
        if not tepe_ok:                                     # gerçek tepe aşımı kadar (+0,1 pay) sınırı indir
            sinir_db -= (sonra["tepe_dbtp"] - tepe) + 0.1
        if not lufs_ok:                                     # sınırlayıcının yuttuğunu geri koy (davullu müzikte −2 LU)
            kazanc += hedef - sonra["lufs"]
    sonuc = {"once": once, "sonra": sonra, "kazanc_db": round(kazanc, 2), "tur": tur + 1, "hedef_lufs": hedef,
             "hedef_tepe_dbtp": tepe, "gecti": sonra["tepe_dbtp"] <= tepe + 0.05 and abs(sonra["lufs"] - hedef) <= 1.0}
    if video_var:
        s1, s2 = float(probe(girdi)["format"]["duration"]), float(probe(cikti)["format"]["duration"])
        sonuc["sure_farki_ms"] = round((s2 - s1) * 1000, 1)
    return sonuc


def calistir_(args) -> int:
    g = Path(args.girdi)
    cikti = args.cikti or str(g.with_name(g.stem + "-usta" + g.suffix))
    if Path(cikti).resolve() == g.resolve():
        raise MedyaHatasi("çıktı girdinin üzerine yazamaz; --cikti ile başka yol ver")
    if args.olc:
        r = olc(args.girdi)
        print(f"{r['lufs']:.1f} LUFS, tepe {r['tepe_dbtp']:.1f} dBTP, LRA {r['lra']:.1f} LU")
        return 0
    r = ustala(args.girdi, cikti, args.hedef, args.tepe)
    o, s = r["once"], r["sonra"]
    print(f"önce {o['lufs']:.1f} LUFS / {o['tepe_dbtp']:.1f} dBTP → sonra {s['lufs']:.1f} LUFS / {s['tepe_dbtp']:.1f} dBTP "
          f"(kazanç {r['kazanc_db']:+.1f} dB, {r['tur']} tur) {'✓' if r['gecti'] else '✗ hedef tutmadı'} → {cikti}")
    if args.json:
        json_yaz(args.json, r)
    return 0 if r["gecti"] else 1


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="ses düzeyi ustalığı")
    p.add_argument("girdi")
    p.add_argument("--hedef", type=float, default=-16.0, help="entegre ses yüksekliği (LUFS)")
    p.add_argument("--tepe", type=float, default=-1.5, help="gerçek tepe sınırı (dBTP)")
    p.add_argument("--cikti")
    p.add_argument("--olc", action="store_true", help="yalnız ölç, değiştirme")
    p.add_argument("--json")
    p.set_defaults(islev=calistir_)
