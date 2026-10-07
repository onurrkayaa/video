"""Müziği ölçü/bölüm başlarında kısaltır (çoklu ek) ve ek kapılarını ölçer.

  PY=$MEDYA/ortamlar/ses/bin/python; B=$MEDYA/sistem/claude/skills/ses-tasarimi/scripts
  $PY $B/kisalt.py yap --ana analiz/muzik-ana.wav --parcalar 0-7.7 12.5-40.1 98.3-176.0 [--gecis 0.03] \
      [--sonum 2] [--esle 101.2] --cikti calisma/ses/muzik-ana.wav --harita analiz/kisalt.json
  medya muzik "$PWD/calisma/ses/muzik-ana.wav" --cikti "$PWD/analiz/muzik-kisa.json" --ana "$PWD/calisma/ses/muzik-ana.wav"
  $PY $B/kisalt.py olc --harita analiz/kisalt.json --ozgun analiz/muzik.json --kisa analiz/muzik-kisa.json [--fps 30] [--sure 75]

yap: --parcalar kaynak zamanında tutulan parçalar (bas-son, sn). Her ek: önceki parça 'son'da biter, sonraki parça
     bas−gecis'ten başlar, eşit güçlü acrossfade (qsin) ek anında biter → kaynaktaki 'bas' çıktıda tam ek anına oturur
     (ölçüldü: ek sonrası 0,0 ms; araştırmadaki atrim=bas biçimi 30 ms erken). gecis: vuruşa ek 0,02–0,08 sn; güven
     düşükken bölüm/cümle sınırında 0,5–1,5 sn. --sonum: qsin sönüm, dosya bitiminden 0,1 sn önce sessizliğe iner. --esle: kaynak anlarının
     çıktıdaki yeri (ör. doruğa gelecek söz). Harita JSON'u: parçalar, ek anları (çıktı sn), eşlemeler.
olc: (1) ek başına vuruş aralığı komşuların ortancasından ±10 ms (yalnız güven yuksek iken anlamlı);
     (2) yeni vuruşlar ile eklenmiş özgün liste F ≥ 0,95 (±70 ms, mir_eval); (3) ses yüksekliği, tutulan parçaların
     sert birleşimine göre ±0,5 LU (geçişin ek yaptığı düzey sıçraması); (4) son 50 ms tepe < −60 dBFS;
     --fps ile her ek en yakın yeni ölçü başına ±1 kare; --sure ile çıktı süresi ±1 kare. Eşikler: music-sync.md
     "Music edits on downbeats", audio-production.md "Fit the music bed".
Çıkış kodu: 0 geçti, 1 kaldı (yap: dosya yazıldı), 2 kullanım hatası.
"""
from __future__ import annotations

import argparse
import json
import subprocess

import numpy as np

import sesortak as so


def parcalar_oku(metin: list[str]) -> list[tuple[float, float]]:
    try:
        p = [tuple(float(v) for v in m.split("-")) for m in metin]
    except ValueError:
        so.hata("--parcalar biçimi bas-son, ör. 0-7.7 12.5-40.1")
    if any(len(q) != 2 or q[1] <= q[0] for q in p):
        so.hata("her parça bas-son, son > bas")
    return p


def cikti_zamani(parcalar, t: float) -> float | None:
    o = 0.0
    for b, s in parcalar:
        if b <= t < s:
            return o + t - b
        o += s - b
    return None


def yap(a) -> int:
    p = parcalar_oku(a.parcalar)
    d = a.gecis
    for i, (b, s) in enumerate(p):
        if i and (b - d < 0 or s - b < 2 * d or p[i - 1][1] - p[i - 1][0] < 2 * d):
            so.hata(f"{i + 1}. parça geçişe ({d} sn) yetmiyor")
    girdiler, zincir, onceki = [], [], "p0"
    for i, (b, s) in enumerate(p):
        bas = b - d if i else b
        girdiler.append(f"[0]atrim=start={bas:.6f}:end={s:.6f},asetpts=PTS-STARTPTS[p{i}]")
        if i:
            zincir.append(f"[{onceki}][p{i}]acrossfade=d={d}:c1=qsin:c2=qsin[x{i}]")
            onceki = f"x{i}"
    sure = sum(s - b for b, s in p)
    son = f"[{onceki}]" + (f"afade=t=out:st={sure - a.sonum - 0.1:.6f}:d={a.sonum}:curve=qsin" if a.sonum else "anull") + "[o]"
    grafik = ";".join(girdiler + zincir + [son])
    r = subprocess.run([so.FFMPEG, "-nostdin", "-v", "error", "-y", "-i", a.ana, "-filter_complex", grafik,
                        "-map", "[o]", "-c:a", "pcm_s24le", a.cikti], capture_output=True, text=True)
    if r.returncode:
        so.hata(r.stderr.strip()[-400:])
    ekler, o = [], 0.0
    for b, s in p[:-1]:
        o += s - b
        ekler.append(round(o, 6))
    esle = {str(t): (round(cikti_zamani(p, t), 4) if cikti_zamani(p, t) is not None else None) for t in a.esle or []}
    so.json_yaz(a.harita, {"ana": a.ana, "cikti": a.cikti, "parcalar": p, "gecis_sn": d, "sonum_sn": a.sonum,
                           "ekler_cikti_sn": ekler, "beklenen_sure_sn": round(sure, 6), "esle_kaynak_cikti": esle})
    print(f"{len(p)} parça, {len(ekler)} ek @ {ekler} sn; süre {sure:.3f} sn → {a.cikti}")
    for k, v in esle.items():
        print(f"  kaynak {k} sn → çıktı {v} sn" if v is not None else f"  kaynak {k} sn atılan bölümde")
    return 0


def olc(a) -> int:
    h = json.load(open(a.harita))
    p, ekler = [tuple(q) for q in h["parcalar"]], h["ekler_cikti_sn"]
    oz, ks = json.load(open(a.ozgun)), json.load(open(a.kisa))
    yeni = np.array(ks["vuruslar"])
    beklenen = np.array(sorted(x for x in (cikti_zamani(p, t) for t in oz["vuruslar"]) if x is not None))
    import mir_eval
    f = float(mir_eval.beat.f_measure(beklenen, yeni, f_measure_threshold=0.07))
    sonuc, gecti = {"guven_ozgun": oz.get("guven_seviye"), "guven_kisa": ks.get("guven_seviye"), "f_olcu": round(f, 3)}, f >= 0.95
    ek_olc = []
    for e in ekler:
        i = int(np.argmin(np.abs(yeni - e)))
        ara = np.diff(yeni[max(0, i - 4):i + 5]) * 1000
        sap = float(np.max(np.abs(ara - np.median(ara)))) if len(ara) > 2 else float("nan")
        kayit = {"ek_sn": e, "vurus_araliklari_ms": [round(x) for x in ara], "en_buyuk_sapma_ms": round(sap, 1)}
        gecti &= sap <= 10
        if a.fps:
            ob = np.array(ks["olcu_baslari"])
            uz = float(np.min(np.abs(ob - e))) if len(ob) else float("inf")
            kayit["en_yakin_olcu_basi_ms"] = round(uz * 1000, 1)
            gecti &= uz <= 1 / a.fps
        ek_olc.append(kayit)
    x, sr = so.oku(h["cikti"])
    ham, _ = so.oku(h["ana"])
    sert = np.concatenate([ham[:, int(round(b * sr)):int(round(s * sr))] for b, s in p], axis=1)
    lu = so.yukseklik(so.k_agirlikla(x, sr)) - so.yukseklik(so.k_agirlikla(sert, sr))
    kuyruk = 20 * np.log10(np.max(np.abs(x[:, -int(0.05 * sr):])) + 1e-12)
    sonuc.update({"ekler": ek_olc, "duzey_farki_lu": round(lu, 2), "son_50ms_tepe_dbfs": round(float(kuyruk), 1),
                  "sure_sn": round(x.shape[1] / sr, 4)})
    gecti &= abs(lu) <= 0.5 and kuyruk < -60
    if a.sure is not None:
        sonuc["beklenen_sure_sn"] = a.sure
        gecti &= abs(x.shape[1] / sr - a.sure) <= 1 / (a.fps or 30)
    sonuc["gecti"] = bool(gecti)
    if a.json:
        so.json_yaz(a.json, sonuc)
    print(json.dumps(sonuc, ensure_ascii=False))
    print("✓ ek kapıları geçti" if gecti else "✗ ek kapısı kaldı")
    return 0 if gecti else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = p.add_subparsers(dest="komut", required=True)
    y = alt.add_parser("yap")
    y.add_argument("--ana", required=True, help="medya muzik'in ana WAV'ı (kaynak saati)")
    y.add_argument("--parcalar", nargs="+", required=True, help="tutulan parçalar bas-son (kaynak sn)")
    y.add_argument("--gecis", type=float, default=0.03, help="acrossfade sn")
    y.add_argument("--sonum", type=float, default=0.0, help="sonda qsin sönüm sn (gerçek sonla bitiyorsa 0)")
    y.add_argument("--esle", type=float, nargs="*", help="çıktıdaki yeri yazılacak kaynak anları")
    y.add_argument("--cikti", required=True)
    y.add_argument("--harita", required=True)
    o = alt.add_parser("olc")
    o.add_argument("--harita", required=True)
    o.add_argument("--ozgun", required=True, help="özgün medya muzik JSON'u")
    o.add_argument("--kisa", required=True, help="kısaltılmış dosyanın medya muzik JSON'u")
    o.add_argument("--fps", type=float)
    o.add_argument("--sure", type=float, help="beklenen video süresi sn")
    o.add_argument("--json")
    a = p.parse_args()
    return yap(a) if a.komut == "yap" else olc(a)


if __name__ == "__main__":
    raise SystemExit(main())
