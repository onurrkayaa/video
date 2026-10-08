#!/usr/bin/env python3
"""Kurgu programına devir ölçümü: kare kodlu sınama projesinin (testler/nle_sinama.py) bir NLE'deki çizimini plana karşı ölçer.

  .venv/bin/python testler/nle_olc.py <proje_klasoru> [<cizim.mov|mp4>] [--kdenlive-xml proje.kdenlive] [--json sonuc.json]
                                      [--erime-kesim] [--son-tolerans N]

Görüntü: her çıktı karesinin kod şeridi okunur (nle_sinama.kod_oku). Beklenti plandan hesaplanır: çıktı karesi n (çizim
fps'i F) → çekim kaynağı karesi floor((kaynak_bas + (n − bas_n)/F) × kaynak_fps); en yakın kare de kabul (MLT/Kdenlive
yuvarlıyor, Resolve alt sınır alıyor). Kesim: çekimin ilk göründüğü kare = bas_n (0 kare). Erime: iki çekimin örtüştüğü
aralıkta karışık (okunamayan) kareler olmalı; uzunluk ve yer ağırlık rampasından ölçülür (karışık kare saymak, ilk
karesinde ağırlığı 0 olan programda 1 karelik sahte sapma verir): ±0,5 kare. Kaynak fps'i çizim fps'ine tam bölünmüyorsa
(24 → 30) ±1 kaynak karesi kabul.
Ses (mutlak konum, periyot belirsizliği yok): müzikte k. tonun frekansı k'yı, çekim sesinde bip sayısı kaynak saniyesini
verir; ikisi de beklenen ana göre ms cinsinden ölçülür (eşik yarım zaman çizelgesi karesi). Ayrıca müzik, stüdyonun
`medya senkron` ses hizasıyla (çapraz ilinti) ölçülür: |gecikme| ≤ 5 ms. Sesi alınmayan kliplerin frekansı duyulmamalı.
--kdenlive-xml: kaydedilen .kdenlive projesi (birincil denetim; çizimin göremediklerini de görür): profil, her klibin
konumu/giriş noktası/uzunluğu, klip işaretlerinin klibin ilk karesinde olması, beklenmeyen klip.
--erime-kesim: erimesiz devir (Kdenlive OTIO'su): örtüşmenin ortasında kesim beklenir. --son-tolerans N: plan sonundan
sonraki N kare/ses olayı bulgu sayılmaz (Kdenlive 'SON — sil' klibi, melt'in kapsayan son karesi).
Çıkış kodu: 0 geçti, 1 bulgu var.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nle_sinama import (BIP_ARA, BIP_SURE, FF, KLIPLER, SR, TIK_ADIM, TIK_ARALIK, TIK_HZ0, TIK_SURE,  # noqa: E402
                        bloklar, kod_oku)

FFPROBE = str(Path(FF).with_name("ffprobe"))


def _akis(yol: Path) -> tuple[int, int, float]:
    o = json.loads(subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height,r_frame_rate", "-of", "json", str(yol)],
                                  capture_output=True, text=True, check=True).stdout)["streams"][0]
    p, q = o["r_frame_rate"].split("/")
    return int(o["width"]), int(o["height"]), int(p) / int(q)


def _kareler(yol: Path, w: int, h: int):
    p = subprocess.Popen([FF, "-nostdin", "-v", "error", "-i", str(yol), "-map", "0:v:0", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    boy = w * h * 3
    while True:
        b = p.stdout.read(boy)
        if len(b) < boy:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
    p.wait()


def _cekimler(plan: dict, F: float) -> list[dict]:
    out = []
    for c in plan["cekimler"]:
        harf = Path(c["kaynak"]).stem
        out.append({"no": c["no"], "harf": harf, "fps": KLIPLER[harf][0], "kaynak_bas": c["kaynak_bas"],
                    "bas_n": round(c["cikti_bas"] * F), "son_n": round(c["cikti_son"] * F),
                    "ses": c.get("ses"), "cikti_bas": c["cikti_bas"], "cikti_son": c["cikti_son"]})
    return out


def _beklenen_kare(c: dict, n: int, F: float, yuvarla: bool = False) -> int:
    """Çıktı karesi n'de çekimin kaynak karesi: alt sınır (Resolve) ya da en yakın kare (MLT/Kdenlive)."""
    return math.floor((c["kaynak_bas"] + (n - c["bas_n"]) / F) * c["fps"] + (0.5 if yuvarla else 0) + 1e-6)


def _kesimler(plan: dict, cek: list[dict], F: float) -> dict[int, int]:
    """Erimesiz devirde örtüşen çekim çiftinin kesim karesi (medya nle: örtüşmenin ortası, plan fps'inde)."""
    fps = float(plan["fps"])
    out = {}
    for i in range(1, len(cek)):
        a, b = cek[i - 1], cek[i]
        L = round((a["cikti_son"] - b["cikti_bas"]) * fps)
        if L > 0:
            out[i] = round((b["cikti_bas"] + (L // 2) / fps) * F)
    return out


def _rampa(Y: list, a: dict, b: dict) -> dict | None:
    """Erimede gelen çekimin ağırlığı w(n): iki klibin 4 bitlik kimliğinde farklı olan bloklar, erimeden önceki ve
    sonraki saf karelere göre ölçeklenir (kare numarası bitleri gerekmez). Doğrusal kısma oturtulan doğrudan uzunluk
    (1/eğim) ve orta (w = 0,5, kare dizini). Uygun: uzunluk plandan ±0,5 kare; orta kesimden −0,75…+0,25 kare (kare
    merkezinde örnekleyen program −0,5 verir — Resolve; kare başında örnekleyen 0 — MLT)."""
    ka, kb = ord(a["harf"]) - 64, ord(b["harf"]) - 64
    fark = [j for j in range(4) if ((ka >> (3 - j)) & 1) != ((kb >> (3 - j)) & 1)]
    na, nb = max(a["bas_n"], b["bas_n"] - 3), min(b["son_n"] - 1, a["son_n"] + 2, len(Y) - 1)
    ya, yb = Y[na][fark], Y[nb][fark]
    if np.abs(yb - ya).min() < 100:                  # saf kareler beklenen klipleri göstermiyor
        return None
    w = [(n, float(np.median((Y[n][fark] - ya) / (yb - ya)))) for n in range(na, nb + 1)]
    ic = [(n, v) for n, v in w if 0.03 < v < 0.97]
    if len(ic) < 3:
        return None
    egim, kesisim = np.polyfit([n for n, _ in ic], [v for _, v in ic], 1)
    kare, orta = 1 / egim, (0.5 - kesisim) / egim
    L, kesim = a["son_n"] - b["bas_n"], (a["son_n"] + b["bas_n"]) / 2
    return {"kare": round(kare, 2), "orta": round(orta, 2), "bas": round(-kesisim / egim, 2), "plan_kare": L,
            "kesim": kesim, "uygun": bool(abs(kare - L) <= 0.5 and -0.75 <= orta - kesim <= 0.25),
            "agirlik": [[n, round(v, 3)] for n, v in w]}


def goruntu_olc(proje: Path, cizim: Path, erime_kesim: bool = False, son_tolerans: int = 0) -> dict:
    plan = json.loads((proje / "plan" / "kurgu.json").read_text())
    w, h, F = _akis(cizim)
    cek = _cekimler(plan, F)
    kesim = _kesimler(plan, cek, F) if erime_kesim else {}
    okunan, Y = [], []
    for k in _kareler(cizim, w, h):
        okunan.append(kod_oku(k))
        Y.append(bloklar(k))
    beklenen_n = max(c["son_n"] for c in cek)
    sonuc = {"fps": F, "boyut": [w, h], "kare": len(okunan), "beklenen_kare": beklenen_n, "hatalar": [],
             "cekimler": {}, "erimeler": [], "son_fazla": []}
    hatalar = sonuc["hatalar"]
    for c in cek:
        tol = 0 if (c["fps"] % F == 0 or F % c["fps"] == 0) else 1
        sonuc["cekimler"][c["harf"]] = {"ilk_kare": None, "bas_n": c["bas_n"], "sapma": {}, "tolerans": tol}
    for n, r in enumerate(okunan):
        etkin = [c for c in cek if c["bas_n"] <= n < c["son_n"]]
        if len(etkin) == 2 and kesim:
            i = cek.index(etkin[1])
            etkin = [etkin[0]] if n < kesim[i] else [etkin[1]]
        if not etkin:
            if n >= beklenen_n and n < beklenen_n + son_tolerans:
                sonuc["son_fazla"].append([n, r])
            elif r is not None:
                hatalar.append(f"kare {n}: plan dışı ama {r} görünüyor")
            continue
        if r is not None and r[0] in sonuc["cekimler"] and sonuc["cekimler"][r[0]]["ilk_kare"] is None:
            sonuc["cekimler"][r[0]]["ilk_kare"] = n
        if len(etkin) == 1:
            c = etkin[0]
            if r is None:
                hatalar.append(f"kare {n}: kod okunamadı (beklenen {c['harf']})")
                continue
            if r[0] != c["harf"]:
                hatalar.append(f"kare {n}: {r[0]} görünüyor, beklenen {c['harf']}")
                continue
            alt, yakin = _beklenen_kare(c, n, F), _beklenen_kare(c, n, F, yuvarla=True)
            anahtar = "0" if r[1] == alt else "yuvarlama" if r[1] == yakin else str(r[1] - alt)
            s = sonuc["cekimler"][c["harf"]]
            s["sapma"][anahtar] = s["sapma"].get(anahtar, 0) + 1
            if r[1] not in (alt, yakin) and abs(r[1] - alt) > s["tolerans"]:
                hatalar.append(f"kare {n}: {c['harf']} kaynak karesi {r[1]}, beklenen {alt}")
        else:
            if r is not None and not any(r[0] == c["harf"] and abs(r[1] - _beklenen_kare(c, n, F)) <= 1
                                         for c in etkin):
                hatalar.append(f"kare {n}: erimede {r} iki çekime de uymuyor")
    for i in range(1, len(cek)):                     # örtüşen ardışık çekimler = erime
        a, b = cek[i - 1], cek[i]
        if b["bas_n"] < a["son_n"]:
            aralik = list(range(b["bas_n"], a["son_n"]))
            karisik = [n for n in aralik if n < len(okunan) and okunan[n] is None]
            e = {"cekimler": f"{a['harf']}→{b['harf']}", "aralik": [aralik[0], aralik[-1]],
                 "kare": len(aralik), "karisik_kare": len(karisik), "kesim": kesim.get(i),
                 "karisik_ilk_son": [karisik[0], karisik[-1]] if karisik else None}
            sonuc["erimeler"].append(e)
            if not karisik and not erime_kesim:
                hatalar.append(f"erime {a['harf']}→{b['harf']}: karışık kare yok — erime kesime dönmüş")
            elif not erime_kesim:                    # uzunluk ve yer ağırlık rampasından (_rampa)
                r = e["rampa"] = _rampa(Y, a, b)
                if r is None:
                    hatalar.append(f"erime {e['cekimler']}: ağırlık rampası ölçülemedi")
                elif not r["uygun"]:
                    hatalar.append(f"erime {e['cekimler']}: rampadan {r['kare']:g} kare, orta {r['orta']:g} "
                                   f"(plan {r['plan_kare']} kare, kesim {r['kesim']:g})")
    for i, c in enumerate(cek):                      # kesim: erimeyle başlamayan çekim tam bas_n'de görünmeli
        bas = kesim.get(i, c["bas_n"])
        if i and c["bas_n"] < cek[i - 1]["son_n"] and i not in kesim:
            continue
        ilk = sonuc["cekimler"][c["harf"]]["ilk_kare"]
        if ilk != bas:
            hatalar.append(f"kesim: {c['harf']} ilk kez {ilk}. karede, beklenen {bas}")
    if not beklenen_n <= len(okunan) <= beklenen_n + son_tolerans:
        hatalar.append(f"kare sayısı {len(okunan)}, beklenen {beklenen_n}"
                       + (f" (+{son_tolerans} kabul)" if son_tolerans else ""))
    return sonuc


def _ses(cizim: Path) -> np.ndarray:
    b = subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(cizim), "-map", "0:a:0", "-ac", "1", "-ar", str(SR),
                        "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(b, "<f4")


def _zarf(x: np.ndarray, hz: float, pencere: float = 0.004, adim: float = 0.0005,
          hann: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Verilen frekanstaki genlik zarfı (karmaşık çarpımla dar bant), adım aralıklı. Kısa dikdörtgen pencere zamanlama
    içindir (bant geniş); sızıntı denetimi için uzun Hann penceresi (komşu frekanslar karışmaz)."""
    n = np.arange(len(x)) / SR
    z = x * np.exp(-2j * np.pi * hz * n)
    L = int(pencere * SR)
    k = np.hanning(L) if hann else np.ones(L)
    k = k / k.sum()
    zarf = np.abs(np.convolve(z, k, mode="same")) * 2
    s = int(adim * SR)
    return n[::s], zarf[::s]


def _bant(x: np.ndarray, alt: float, ust: float) -> np.ndarray:
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < alt) | (f > ust)] = 0
    return np.fft.irfft(X, len(x))


def _baslangiclar(t: np.ndarray, z: np.ndarray, esik: float, bekleme: float) -> list[float]:
    ust = z >= esik
    out, son = [], -1e9
    for i in np.flatnonzero(ust[1:] & ~ust[:-1]) + 1:
        if t[i] - son > bekleme:
            out.append(float(t[i]))
            son = t[i]
    return out


def _tepe_frekans(x: np.ndarray, t0: float) -> float:
    a, b = int((t0 + 0.002) * SR), int((t0 + TIK_SURE - 0.002) * SR)
    p = x[a:b] * np.hanning(b - a)
    X = np.abs(np.fft.rfft(p, 1 << 16))
    return float(np.fft.rfftfreq(1 << 16, 1 / SR)[int(X.argmax())])


def ses_olc(proje: Path, cizim: Path, son_tolerans: int = 0) -> dict:
    plan = json.loads((proje / "plan" / "kurgu.json").read_text())
    fps = float(plan["fps"])
    x = _ses(cizim).astype(np.float64)
    son = max(c["cikti_son"] for c in plan["cekimler"])
    son_kabul = son + son_tolerans / fps
    esik_ms = 1000 / fps / 2
    sonuc = {"sure_sn": round(len(x) / SR, 3), "muzik": [], "cekim_sesi": [], "sizinti": [], "hatalar": []}
    hatalar = sonuc["hatalar"]

    m = plan.get("muzik")
    if m:                                            # k. ton: müzik dosyasında k·0,5 sn → videoda k·0,5 − bas
        bp = _bant(x, TIK_HZ0 - 300, 8000)
        t = np.arange(len(bp)) / SR
        L = int(0.004 * SR)
        zarf = np.convolve(np.abs(bp), np.ones(L) / L, mode="same")
        tepe = float(zarf.max()) if len(zarf) else 0.0
        bulunan = _baslangiclar(t, zarf, tepe * 0.5, 0.2) if tepe > 1e-3 else []
        beklenen_k = [k for k in range(200) if 0 <= k * TIK_ARALIK - m["bas"] < son - 1e-6]
        gorulen = set()
        for t0 in bulunan:
            k = round((_tepe_frekans(bp, t0) - TIK_HZ0) / TIK_ADIM)
            sapma = round((t0 - (k * TIK_ARALIK - m["bas"])) * 1000, 1)
            sonuc["muzik"].append({"t": round(t0, 4), "k": k, "sapma_ms": sapma})
            if t0 >= son - 1e-6:
                if t0 >= son_kabul:
                    hatalar.append(f"müzik: plan sonundan sonra ton (t={t0:.3f}, k={k})")
                continue
            gorulen.add(k)
            if abs(sapma) > esik_ms:
                hatalar.append(f"müzik: t={t0:.3f} sn'deki ton k={k} → {sapma:+.1f} ms kaymış (eşik ±{esik_ms:.1f})")
        eksik = sorted(set(beklenen_k) - gorulen)
        if eksik:
            hatalar.append(f"müzik: beklenen tonlar yok: k={eksik}")
        from medya.komutlar.senkron import ses_hizasi     # stüdyonun ölçütü (medya senkron): |gecikme| ≤ 5 ms
        hiza = sonuc["ses_hizasi"] = ses_hizasi(str(cizim), {"ana_wav": str(proje / m["dosya"])}, plan)
        if hiza and not hiza.get("olculemedi") and hiza["ilinti"] >= 0.5 and abs(hiza["gecikme_ms"]) > 5:
            hatalar.append(f"müzik: medya senkron ses hizası {hiza['gecikme_ms']:+.1f} ms "
                           f"(ilinti {hiza['ilinti']:.2f}; eşik ±5 ms)")
    for c in plan["cekimler"]:
        harf = Path(c["kaynak"]).stem
        hz = KLIPLER[harf][3]
        if c.get("ses") == "kendi":                  # s. kaynak saniyesinde s+1 bip → videoda cikti_bas + s − kaynak_bas
            t, z = _zarf(x, hz)
            tepe = float(z.max())
            bas_list = _baslangiclar(t, z, tepe * 0.5, BIP_SURE + BIP_ARA * 0.5) if tepe > 1e-3 else []
            gruplar: list[list[float]] = []
            for t0 in bas_list:
                if gruplar and t0 - gruplar[-1][0] < 0.5:
                    gruplar[-1].append(t0)
                else:
                    gruplar.append([t0])
            sure = c["cikti_son"] - c["cikti_bas"]
            beklenen_s = [s for s in range(100) if c["kaynak_bas"] - 1e-6 <= s < c["kaynak_bas"] + sure - 1e-6]
            gorulen = set()
            for g in gruplar:
                s = len(g) - 1
                bekl = c["cikti_bas"] + (s - c["kaynak_bas"])
                sapma = round((g[0] - bekl) * 1000, 1)
                sonuc["cekim_sesi"].append({"harf": harf, "t": round(g[0], 4), "kaynak_sn": s, "sapma_ms": sapma})
                if g[0] >= son - 1e-6 and g[0] < son_kabul:
                    continue
                gorulen.add(s)
                if not c["cikti_bas"] - 0.05 <= g[0] < c["cikti_son"]:
                    hatalar.append(f"{harf} çekim sesi plan aralığı dışında: t={g[0]:.3f} (kaynak {s}. sn)")
                elif abs(sapma) > esik_ms:
                    hatalar.append(f"{harf} çekim sesi: kaynak {s}. sn videoda {g[0]:.3f} sn → {sapma:+.1f} ms kaymış")
            eksik = sorted(set(beklenen_s) - gorulen)
            if eksik:
                hatalar.append(f"{harf} çekim sesi: beklenen kaynak saniyeleri duyulmuyor: {eksik}")
        else:
            t, z = _zarf(x, hz, pencere=0.04, adim=0.002, hann=True)
            if son_tolerans:
                z = z[t < son - 1e-6]
            tepe = float(z.max()) if len(z) else 0.0
            sonuc["sizinti"].append({"harf": harf, "hz": hz, "tepe": round(tepe, 4)})
            if tepe > 0.05:
                hatalar.append(f"{harf} çekiminin sesi duyuluyor (tepe {tepe:.3f}); planda 'ses: muzik'")
    return sonuc


def _mlt_kare(s: str | None, fps: float) -> int:
    """MLT zaman değeri → kare: tamsayı ya da saat 'SS:DD:SS.mmm' (Kdenlive 26.08 böyle yazıyor)."""
    if not s or ":" not in s:
        return int(s or 0)
    sa, dk, sn = s.split(":")
    return round((int(sa) * 3600 + int(dk) * 60 + float(sn)) * fps)


def kdenlive_xml_olc(proje: Path, xml: Path) -> dict:
    """Kaydedilen .kdenlive projesi (içe aktarılmış -kdenlive.otio) plana karşı — birincil denetim: profil (fps, boyut),
    her izdeki klibin konumu, giriş noktası ve uzunluğu (erime yerine örtüşmenin ortasında kesim), notlu çekimin işareti
    klibin ilk karesinde mi (Kdenlive işareti kutudaki klibe yazar: işaretin kaynak karesi = giriş noktası), beklenmeyen
    klip (ör. görüntü izinde klibin sesi). İz sonlarındaki 1 karelik 'SON — sil' klipleri kabul."""
    import xml.etree.ElementTree as ET
    plan = json.loads((proje / "plan" / "kurgu.json").read_text())
    kok = ET.parse(xml).getroot()
    pr = kok.find("profile")
    F = int(pr.get("frame_rate_num")) / int(pr.get("frame_rate_den"))
    fps = float(plan["fps"])
    sonuc = {"dosya": str(xml), "profil": {"ad": pr.get("description"), "fps": F,
                                           "boyut": [int(pr.get("width")), int(pr.get("height"))]},
             "klipler": [], "isaretler": [], "son_sil": 0, "hatalar": []}
    hatalar = sonuc["hatalar"]
    if abs(F - fps) > 1e-6:
        hatalar.append(f"profil {F:g} fps, plan {fps:g}")
    if plan.get("boyut") and sonuc["profil"]["boyut"] != list(plan["boyut"]):
        hatalar.append(f"profil boyutu {sonuc['profil']['boyut']}, plan {plan['boyut']}")
    cek = _cekimler(plan, fps)                       # beklenen: medya nle Kdenlive kipi (plan fps'inde, erime → kesim)
    kesim = _kesimler(plan, cek, fps)
    goruntu, ses = [], []                            # (medya, konum, giriş, uzunluk, etiket)
    for i, (c, pc) in enumerate(zip(cek, plan["cekimler"])):
        ad, bas, son = Path(pc["kaynak"]).name, kesim.get(i, c["bas_n"]), kesim.get(i + 1, c["son_n"])
        goruntu.append((ad, bas, round((c["kaynak_bas"] + (bas - c["bas_n"]) / fps) * fps), son - bas,
                        f"{c['harf']} görüntü"))
        if c["ses"] == "kendi":
            ses.append((ad, c["bas_n"], round(c["kaynak_bas"] * fps), c["son_n"] - c["bas_n"], f"{c['harf']} sesi"))
    toplam = max(x[1] + x[3] for x in goruntu)
    if plan.get("muzik"):
        ses.append((Path(plan["muzik"]["dosya"]).name, 0, round(plan["muzik"]["bas"] * fps), toplam, "müzik"))
    kaynaklar, isaretler = {}, {}                    # üretici → medya adı; medya adı → işaretlerin kaynak kareleri
    for el in kok.iter():
        if el.tag in ("producer", "chain"):
            oz = {p.get("name"): p.text or "" for p in el.findall("property")}
            ad = kaynaklar[el.get("id")] = Path(oz.get("resource", "")).name
            for mk in json.loads(oz.get("kdenlive:markers") or "[]"):
                isaretler.setdefault(ad, set()).add(mk["pos"])
    girisler = []                                    # projedeki her iz öğesi: (medya, konum, giriş, uzunluk)
    for pl in kok.iter("playlist"):
        if pl.get("id") == "main_bin":
            continue
        konum = 0
        for e in pl:
            if e.tag == "blank":
                konum += _mlt_kare(e.get("length"), F)
            elif e.tag == "entry":
                g, c = _mlt_kare(e.get("in"), F), _mlt_kare(e.get("out"), F)
                girisler.append((kaynaklar.get(e.get("producer"), e.get("producer")), konum, g, c - g + 1))
                konum += c - g + 1
    kalan = list(girisler)
    for ad, konum, giris, uzunluk, etiket in goruntu + ses:
        if (ad, konum, giris, uzunluk) in kalan:
            kalan.remove((ad, konum, giris, uzunluk))
            sonuc["klipler"].append(etiket)
        else:
            benzer = [f"{x[1]}/{x[2]}/{x[3]}" for x in kalan if x[0] == ad]
            hatalar.append(f"{etiket}: beklenen konum/giriş/uzunluk {konum}/{giris}/{uzunluk}, projede {benzer or 'yok'}")
    for x in kalan:
        if x[3] == 1 and x[1] >= toplam:
            sonuc["son_sil"] += 1
        else:
            hatalar.append(f"beklenmeyen klip: {x[0]} konum/giriş/uzunluk {x[1]}/{x[2]}/{x[3]}")
    for i, (pc, (ad, konum, giris, uzunluk, _)) in enumerate(zip(plan["cekimler"], goruntu)):
        if not (i in kesim or pc.get("kadraj") or pc.get("hareket") or abs(float(pc.get("hiz", 1)) - 1) > 1e-9):
            continue                                 # medya nle yalnız notlu çekime işaret koyar
        bulunan = sorted(isaretler.get(ad, ()))
        icinde = [konum + p - giris for p in bulunan if giris <= p < giris + uzunluk]
        sonuc["isaretler"].append({"cekim": pc["no"], "giris": giris, "kaynak_kareleri": bulunan,
                                   "zaman_cizelgesi": icinde, "beklenen": konum})
        if giris not in bulunan:
            hatalar.append(f"çekim {pc['no']} işareti klibin ilk karesinde değil: giriş {giris}, işaret kaynak karesi "
                           f"{bulunan or 'yok'} → zaman çizelgesinde {icinde or 'görünmüyor'}, beklenen {konum}")
    return sonuc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("proje", type=Path)
    ap.add_argument("cizim", type=Path, nargs="?")
    ap.add_argument("--kdenlive-xml", type=Path, help="kaydedilen .kdenlive projesi (profil, konumlar, işaretler)")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--erime-kesim", action="store_true", help="erimeler örtüşmenin ortasında kesim olarak beklenir")
    ap.add_argument("--son-tolerans", type=int, default=0, help="plan sonundan sonra bulgu sayılmayan kare sayısı")
    a = ap.parse_args()
    if not a.cizim and not a.kdenlive_xml:
        ap.error("çizim ya da --kdenlive-xml gerekli")
    sonuc, hata = {"cizim": str(a.cizim) if a.cizim else None}, []
    if a.kdenlive_xml:
        x = sonuc["kdenlive_xml"] = kdenlive_xml_olc(a.proje, a.kdenlive_xml)
        p = x["profil"]
        print(f"kdenlive projesi: profil '{p['ad']}' {p['fps']:g} fps {p['boyut'][0]}x{p['boyut'][1]}; "
              f"{len(x['klipler'])} klip yerinde ({', '.join(x['klipler'])}), {x['son_sil']} 'SON — sil'")
        for o in x["isaretler"]:
            print(f"  işaret çekim {o['cekim']}: giriş {o['giris']}, kaynak kareleri {o['kaynak_kareleri']} → zaman "
                  f"çizelgesinde {o['zaman_cizelgesi']} (beklenen {o['beklenen']})")
        for hat in x["hatalar"]:
            print("  BULGU:", hat)
        hata += x["hatalar"]
    if not a.cizim:
        sonuc["gecti"] = not hata
        if a.json:
            a.json.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1))
        print("GEÇTİ" if sonuc["gecti"] else "BULGU VAR")
        return 0 if sonuc["gecti"] else 1
    g = goruntu_olc(a.proje, a.cizim, a.erime_kesim, a.son_tolerans)
    s = ses_olc(a.proje, a.cizim, a.son_tolerans)
    sonuc.update(goruntu=g, ses=s, gecti=not hata and not g["hatalar"] and not s["hatalar"])
    if a.json:
        a.json.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1))
    print(f"görüntü: {g['kare']} kare @ {g['fps']:g} fps {g['boyut'][0]}x{g['boyut'][1]} (beklenen {g['beklenen_kare']})")
    for harf, c in g["cekimler"].items():
        print(f"  {harf}: ilk kare {c['ilk_kare']} (plan {c['bas_n']}), kaynak sapması {c['sapma']}")
    for e in g["erimeler"]:
        print(f"  erime {e['cekimler']}: {e['kare']} kare aralık {e['aralik']}, karışık {e['karisik_kare']} "
              f"{e['karisik_ilk_son']}" + (f", kesim {e['kesim']}" if e["kesim"] is not None else "")
              + (f", rampadan {e['rampa']['kare']:g} kare, orta {e['rampa']['orta']:g}" if e.get("rampa") else ""))
    if g["son_fazla"]:
        print(f"  plan sonrası (kabul): {g['son_fazla']}")
    mz = s["muzik"]
    if mz:
        print(f"  müzik: {len(mz)} ton, k {[o['k'] for o in mz]}, sapma ms {[o['sapma_ms'] for o in mz]}")
    if s.get("ses_hizasi"):
        print(f"  müzik, medya senkron ses hizası: {s['ses_hizasi']}")
    for o in s["cekim_sesi"]:
        print(f"  çekim sesi {o['harf']}: t={o['t']} kaynak {o['kaynak_sn']}. sn, sapma {o['sapma_ms']} ms")
    for z in s["sizinti"]:
        print(f"  sızıntı {z['harf']} ({z['hz']} Hz): tepe {z['tepe']}")
    for hat in g["hatalar"][:15] + s["hatalar"]:
        print("  BULGU:", hat)
    if len(g["hatalar"]) > 15:
        print(f"  … {len(g['hatalar']) - 15} görüntü bulgusu daha")
    print("GEÇTİ" if sonuc["gecti"] else "BULGU VAR")
    return 0 if sonuc["gecti"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
