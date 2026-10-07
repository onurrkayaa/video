"""medya incele <dosya...> — dosya künyesi ve tuzak uyarıları.

Telefon çekimlerinde sorunların çoğu burada başlar: HDR (HLG/PQ, Dolby Vision) yanlış çevrilince soluk
görünür; değişken kare hızı (VFR) kurguda kaymaya yol açar; döndürme üst verisi kırpmayı şaşırtır;
konum (GPS) üst verisi paylaşımda gizliliği bozar. Hepsini tek bakışta raporlar.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..ortak import calistir, ffprobe, json_yaz, oran, probe, ses_akisi, video_akisi

HDR_AKTARIM = {"smpte2084": "PQ (HDR10/Dolby Vision)", "arib-std-b67": "HLG"}
GPS_ETIKET = ("location", "location-eng", "com.apple.quicktime.location.ISO6709", "com.apple.quicktime.location.name")


def _donus(v: dict) -> int:
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            return int(round(float(sd["rotation"])))
    r = (v.get("tags") or {}).get("rotate")
    return int(r) if r else 0


def _vfr_olc(yol: str, saniye: float = 20.0) -> dict:
    """İlk ~20 sn'nin kare zaman damgalarından gerçek kare aralıklarını ölçer."""
    s = calistir([ffprobe(), "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time",
                  "-read_intervals", f"%+{saniye}", "-of", "csv=p=0", yol])
    t = np.array(sorted(float(x) for x in s.stdout.decode().split() if x not in ("", "N/A")))
    if len(t) < 10:
        return {"olculen_kare": int(len(t))}
    d = np.diff(t)
    d = d[d > 0]
    med = float(np.median(d))
    sapma = float(np.mean(np.abs(d - med) > 0.25 * med))   # medyandan %25'ten fazla sapan aralık oranı
    return {"olculen_kare": int(len(t)), "medyan_aralik_ms": med * 1000, "gercek_fps": 1 / med if med else 0,
            "duzensiz_aralik_orani": sapma}


def exif_oku(yol: str) -> dict:
    """ExifTool (varsa): çekim zamanı (saat dilimiyle), cihaz, konum, Live Photo eşleme kimliği."""
    from ..ortak import ARAC
    et = ARAC / "exiftool"
    if not et.exists():
        return {}
    try:
        s = calistir([str(et), "-j", "-n", "-api", "QuickTimeUTC", "-DateTimeOriginal", "-CreateDate",
                      "-OffsetTimeOriginal", "-CreationDate", "-Make", "-Model", "-GPSLatitude", "-GPSLongitude",
                      "-ContentIdentifier", "-MediaGroupUUID", "-ImageWidth", "-ImageHeight", "-Orientation", yol])
        d = json.loads(s.stdout.decode())[0]
    except Exception:
        return {}
    gecerli = lambda t: t if isinstance(t, str) and not t.startswith("0000") else None   # QuickTime boş tarihi
    tarih = gecerli(d.get("DateTimeOriginal")) or gecerli(d.get("CreationDate")) or gecerli(d.get("CreateDate"))
    return {"tarih": tarih, "saat_dilimi": d.get("OffsetTimeOriginal"),
            "cihaz": " ".join(str(x) for x in (d.get("Make"), d.get("Model")) if x) or None,
            "gps": [d["GPSLatitude"], d["GPSLongitude"]] if "GPSLatitude" in d and "GPSLongitude" in d else None,
            "live_photo_id": d.get("ContentIdentifier") or d.get("MediaGroupUUID"),
            "yon": d.get("Orientation")}


GORSEL_UZANTI = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tif", ".tiff", ".webp", ".dng"}


def incele_gorsel(yol: str) -> dict:
    from PIL import Image
    rapor: dict = {"dosya": yol, "tur": "gorsel", "boyut_mb": round(Path(yol).stat().st_size / 1e6, 2), "uyarilar": []}
    try:
        with Image.open(yol) as im:
            rapor["gorsel"] = {"genislik": im.width, "yukseklik": im.height, "mod": im.mode}
    except Exception:
        rapor["gorsel"] = {}
    ex = exif_oku(yol)
    rapor["exif"] = ex
    rapor["etiketler"] = {"olusturma": ex.get("tarih"), "cihaz": ex.get("cihaz"), "konum_var": bool(ex.get("gps"))}
    if ex.get("gps"):
        rapor["uyarilar"].append("Konum (GPS) üst verisi var. Paylaşılacak çıktıya geçmesin: medya meta-temizle <dosya>")
    return rapor


def incele_dosya(yol: str | Path) -> dict:
    yol = str(yol)
    if Path(yol).suffix.lower() in GORSEL_UZANTI:
        return incele_gorsel(yol)
    p = probe(yol)
    f = p.get("format", {})
    v, a = video_akisi(p), ses_akisi(p)
    rapor: dict = {"dosya": yol, "boyut_mb": round(int(f.get("size", 0)) / 1e6, 2),
                   "sure": float(f.get("duration", 0) or 0), "kapsayici": f.get("format_name"),
                   "uyarilar": []}
    U = rapor["uyarilar"]
    etiket = {**(f.get("tags") or {})}
    if v:
        etiket.update({k: x for k, x in (v.get("tags") or {}).items() if k not in etiket})
        don = _donus(v)
        w, h = int(v.get("width", 0)), int(v.get("height", 0))
        gw, gh = (h, w) if abs(don) in (90, 270) else (w, h)
        aktarim = v.get("color_transfer") or "?"
        dovi = any("dv_profile" in sd or "DOVI" in json.dumps(sd) for sd in (v.get("side_data_list") or []))
        fps_n, fps_o = oran(v.get("r_frame_rate")), oran(v.get("avg_frame_rate"))
        vfr = _vfr_olc(yol)
        pix = v.get("pix_fmt", "?")
        rapor["video"] = {
            "codec": v.get("codec_name"), "profil": v.get("profile"), "genislik": w, "yukseklik": h,
            "donus": don, "gorunen": f"{gw}x{gh}", "yon": "dikey" if gh > gw else ("kare" if gh == gw else "yatay"),
            "fps_nominal": round(fps_n, 3), "fps_ortalama": round(fps_o, 3), "kare_olcumu": vfr,
            "pix_fmt": pix, "bit": 10 if ("10" in pix or "p010" in pix) else 8,
            "renk": {"aktarim": aktarim, "birincil": v.get("color_primaries"), "matris": v.get("color_space"),
                     "aralik": v.get("color_range")},
            "hdr": aktarim in HDR_AKTARIM or dovi, "hdr_turu": HDR_AKTARIM.get(aktarim, "Dolby Vision" if dovi else None),
            "kare_sayisi": int(v["nb_frames"]) if str(v.get("nb_frames", "")).isdigit() else None,
        }
        rv = rapor["video"]
        if rv["hdr"]:
            U.append(f"HDR çekim ({rv['hdr_turu']}). SDR çıktıda soluk/yanlış renk olmasın diye önce: medya sdr {yol}")
        if vfr.get("duzensiz_aralik_orani", 0) > 0.02 or (fps_o and abs(fps_n - fps_o) / fps_n > 0.01):
            U.append(f"Değişken kare hızı (VFR) belirtisi (nominal {fps_n:.2f}, ortalama {fps_o:.2f}, düzensiz aralık "
                     f"%{100 * vfr.get('duzensiz_aralik_orani', 0):.1f}). Kurgudan önce: medya cfr {yol}")
        gercek = vfr.get("gercek_fps", 0)
        if gercek and fps_n and gercek < fps_n * 0.75:
            U.append(f"Kap {fps_n:.0f} fps ama içerik ~{gercek:.0f} fps (yinelenen kareler). Ağır çekimde ara kare "
                     "üretimi gerekir: medya yavaslat")
        if don:
            U.append(f"Döndürme üst verisi {don}°: görünen boyut {gw}x{gh}. Kırpma/yerleşimde görünen boyutu kullan.")
        if rv["bit"] == 10 and not rv["hdr"]:
            U.append("10 bit SDR: 8 bit teslimde bantlaşmayı önlemek için hafif gren/titreşim (dither) düşün.")
    else:
        U.append("Video akışı yok.")
    if a:
        rapor["ses"] = {"codec": a.get("codec_name"), "ornekleme": int(a.get("sample_rate", 0)),
                        "kanal": a.get("channels"), "sure": float(a.get("duration", 0) or 0)}
        if v and abs(rapor["ses"]["sure"] - rapor["sure"]) > 0.5:
            U.append(f"Ses ({rapor['ses']['sure']:.2f} sn) ile kap süresi ({rapor['sure']:.2f} sn) farklı.")
    else:
        U.append("Ses akışı yok.")
    konum = {k: etiket[k] for k in GPS_ETIKET if k in etiket}
    ex = exif_oku(yol)
    rapor["exif"] = ex
    rapor["etiketler"] = {"olusturma": ex.get("tarih") or etiket.get("com.apple.quicktime.creationdate") or etiket.get("creation_time"),
                          "cihaz": ex.get("cihaz") or etiket.get("com.apple.quicktime.model") or etiket.get("model"),
                          "konum_var": bool(konum) or bool(ex.get("gps"))}
    if ex.get("gps") and not konum:
        konum = {"exif": ex["gps"]}
    if konum:
        U.append("Konum (GPS) üst verisi var. Paylaşılacak çıktıya geçmesin: medya meta-temizle <çıktı>")
    return rapor


def calistir_(args) -> int:
    raporlar = [incele_dosya(y) for y in args.dosyalar]
    for r in raporlar:
        if r.get("tur") == "gorsel":
            g = r.get("gorsel", {})
            print(f"{Path(r['dosya']).name}: görsel {g.get('genislik')}x{g.get('yukseklik')}, çekim {r['exif'].get('tarih') or '?'}"
                  + (f", {r['exif']['cihaz']}" if r['exif'].get('cihaz') else ""))
            for u in r["uyarilar"]:
                print(f"  ⚠ {u}")
            continue
        v = r.get("video", {})
        satir = f"{Path(r['dosya']).name}: {r['sure']:.2f} sn"
        if v:
            satir += (f", {v['gorunen']} {v['yon']}, {v['fps_nominal']:g} fps, {v['codec']}, {v['bit']} bit"
                      f"{', ' + v['hdr_turu'] if v['hdr'] else ', SDR'}")
        if r.get("ses"):
            satir += f", ses {r['ses']['codec']} {r['ses']['ornekleme']} Hz"
        if r.get("etiketler", {}).get("olusturma"):
            satir += f", çekim {r['etiketler']['olusturma']}"
        print(satir)
        for u in r["uyarilar"]:
            print(f"  ⚠ {u}")
    if args.json:
        json_yaz(args.json, raporlar if len(raporlar) > 1 else raporlar[0])
        print(f"→ {args.json}")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="dosya künyesi ve tuzak uyarıları")
    p.add_argument("dosyalar", nargs="+")
    p.add_argument("--json", help="raporu bu JSON dosyasına yaz")
    p.set_defaults(islev=calistir_)
