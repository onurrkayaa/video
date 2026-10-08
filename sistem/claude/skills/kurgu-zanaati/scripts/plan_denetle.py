#!/usr/bin/env python3
"""Kurgu planı denetimi: plan/kurgu.json sözleşmeye uyuyor mu; müzik analizi, kompozisyon (HTML) ve çizimin
denetim raporu planla tutarlı mı? Sözleşme: references/plan-semasi.md.

  $MEDYA/.venv/bin/python plan_denetle.py plan/kurgu.json [--muzik analiz/muzik.json]
        [--html calisma/kompozisyon/index.html] [--denetim cikti/<ad>-denetim.json] [--kok <proje>]

Göreli yollar proje köküne göredir (varsayılan: planın iki üstü — medya nle gibi). --muzik verilmezse planın
muzik.analiz alanı kullanılır. ✗ = hata (çıkış 1: düzeltmeden çizme/teslim etme). ⚠ = bak; bilinçliyse
KARARLAR.md'ye gerekçesiyle yaz.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, os.environ.get("MEDYA", "/Users/onurkaya/Projects/video"))
from medya.komutlar.ciz import egri_gecerli  # noqa: E402  (eğri adları: medya ciz ve HyperFrames aynı GSAP adını çizer)

GECISLER = {"kesim", "erime", "j-kesim", "l-kesim", "eslesme", "savurma", "yakinlasma", "isik", "siyah-dip",
            "beyaz-dip", "flas"}
SADE = {"kesim", "j-kesim", "l-kesim", "eslesme"}          # görünür efekt değil: "süslü geçiş" sayılmaz
PARLAK = {"flas", "beyaz-dip", "isik"}
SESLER = {"kendi", "muzik", "sessiz"}
GORSEL = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff"}
ZORUNLU = ("no", "kaynak", "kaynak_bas", "cikti_bas", "cikti_son", "hiz", "ses", "vurusa", "gecis")
SECIMLIK = {"klip", "klip_bas", "kadraj", "hareket"}          # gerekçe/not KARARLAR.md'ye
UST = {"ad", "fps", "boyut", "sure", "muzik", "cekimler"}
MUZIK = {"dosya", "bas", "analiz"}
HDR = {"arib-std-b67", "smpte2084"}                          # HLG, PQ
ZOOM_SINIR = 1.15                                            # çıktı pikseli / kaynak pikseli
EPS = 1e-6


class Rapor:
    def __init__(self):
        self.hatalar, self.uyarilar = [], []

    def hata(self, m):
        self.hatalar.append(m)
        print(f"✗ {m}")

    def uyari(self, m):
        self.uyarilar.append(m)
        print(f"⚠ {m}")


def ffprobe():
    y = Path(os.environ.get("MEDYA", "/Users/onurkaya/Projects/video")) / "arac" / "ffprobe"
    return str(y) if y.exists() else (shutil.which("ffprobe") or "ffprobe")


def bilgi(yol: Path) -> tuple[float | None, bool]:
    """(süre sn | None, ses akışı var mı)"""
    s = subprocess.run([ffprobe(), "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json",
                        str(yol)], capture_output=True, stdin=subprocess.DEVNULL)
    if s.returncode:
        return None, False
    d = json.loads(s.stdout or b"{}")
    sure = d.get("format", {}).get("duration")
    return (float(sure) if sure not in (None, "N/A") else None), any(
        x.get("codec_type") == "audio" for x in d.get("streams", []))


def goruntu(yol: Path) -> tuple[int, int, str] | None:
    """(genişlik, yükseklik — döndürme uygulanmış, color_transfer) | None"""
    s = subprocess.run([ffprobe(), "-v", "error", "-select_streams", "v:0", "-show_streams", "-of", "json", str(yol)],
                       capture_output=True, stdin=subprocess.DEVNULL)
    if s.returncode:
        return None
    st = (json.loads(s.stdout or b"{}").get("streams") or [{}])[0]
    if not st.get("width"):
        return None
    w, h = int(st["width"]), int(st["height"])
    don = [x.get("rotation") for x in st.get("side_data_list", []) if "rotation" in x] or [st.get("tags", {}).get("rotate", 0)]
    if abs(int(float(don[0] or 0))) % 180 == 90:
        w, h = h, w
    return w, h, st.get("color_transfer") or ""


def izgarada(t: float, fps: float) -> bool:
    k = t * fps
    return abs(k - round(k)) <= 2e-3                         # 4+ ondalıkla yazılmış k/fps kabul


def kare(t: float, fps: float) -> int:
    return round(t * fps)


def yol(kok: Path, y: str) -> Path:
    p = Path(y).expanduser()
    return (p if p.is_absolute() else kok / p).resolve()


def medya_bas(c: dict) -> float:
    """Kompozisyonun kullandığı ortam girişi: klip varsa klip_bas, yoksa kaynak_bas."""
    return float(c.get("klip_bas", 0.0)) if c.get("klip") else float(c["kaynak_bas"])


def gorsel_mi(c: dict) -> bool:
    return Path(c.get("klip") or c["kaynak"]).suffix.lower() in GORSEL


# ---------------------------------------------------------------- şema
def sema(p: dict, R: Rapor) -> bool:
    n0 = len(R.hatalar)
    fps = p.get("fps")
    if not isinstance(fps, (int, float)) or isinstance(fps, bool) or fps <= 0:
        R.hata("fps eksik ya da geçersiz")
    b = p.get("boyut")
    if not (isinstance(b, list) and len(b) == 2 and all(isinstance(x, int) and x > 0 for x in b)):
        R.hata("boyut [genişlik, yükseklik] (tamsayı) olmalı")
    elif any(x % 2 for x in b):
        R.hata(f"boyut {b}: çift sayı olmalı (yuv420p kodlama)")
    if "sure" in p and not isinstance(p["sure"], (int, float)):
        R.hata("sure sayı olmalı")
    for a in sorted(set(p) - UST):
        R.uyari(f"üst düzeyde sözleşmede olmayan alan '{a}' (araçlar okumaz; boyut/fps/sure kullan)")
    mz = p.get("muzik")
    if isinstance(mz, dict):
        for a in sorted(set(mz) - MUZIK):
            R.uyari(f"muzik altında sözleşmede olmayan alan '{a}' (araçlar okumaz)")
    if mz is not None:
        if not isinstance(mz, dict) or "dosya" not in mz or not isinstance(mz.get("bas", 0), (int, float)):
            R.hata("muzik {dosya, bas, analiz?} olmalı")
        elif float(mz.get("bas", 0)) < 0:
            R.hata("muzik.bas ≥ 0 olmalı (müzik dosyasının t=0'a denk gelen saniyesi)")
    C = p.get("cekimler")
    if not isinstance(C, list) or not C:
        R.hata("cekimler boş")
        return False
    for i, c in enumerate(C):
        ad = c.get("no", f"#{i + 1}")
        eksik = [a for a in ZORUNLU if a not in c]
        if eksik:
            R.hata(f"çekim {ad}: eksik alan {eksik}")
        fazla = sorted(set(c) - set(ZORUNLU) - SECIMLIK)
        if fazla:
            R.uyari(f"çekim {ad}: sözleşmede olmayan alan {fazla} — yazım hatası mı? (araçlar okumaz)")
        g = c.get("gecis")
        if "gecis" in c and not (isinstance(g, dict) and g.get("tur") in GECISLER
                                 and isinstance(g.get("sure_kare"), int) and g["sure_kare"] >= 0):
            R.hata(f"çekim {ad}: gecis {{tur: {'|'.join(sorted(GECISLER))}, sure_kare: tamsayı ≥ 0}} olmalı; plan: {g}")
        for alan in ("gecis", "hareket"):
            d = c.get(alan)
            if isinstance(d, dict) and "egri" in d and not egri_gecerli(d["egri"]):
                R.hata(f"çekim {ad}: {alan}.egri '{d['egri']}' tanınmıyor (GSAP adı: none, sine.inOut, power2.out, "
                       "expo.out…; yoksa doğrusal) — iki motor aynı eğriyi çizsin")
        if "ses" in c and c["ses"] not in SESLER:
            R.hata(f"çekim {ad}: ses kendi|muzik|sessiz olmalı; plan: {c['ses']}")
        if "vurusa" in c and not isinstance(c["vurusa"], bool):
            R.hata(f"çekim {ad}: vurusa true/false olmalı")
        if "hiz" in c and (not isinstance(c["hiz"], (int, float)) or isinstance(c["hiz"], bool) or c["hiz"] <= 0):
            R.hata(f"çekim {ad}: hiz > 0 sayı olmalı")
        for a in ("kaynak_bas", "cikti_bas", "cikti_son", "klip_bas"):
            if a in c and (not isinstance(c[a], (int, float)) or isinstance(c[a], bool) or c[a] < 0):
                R.hata(f"çekim {ad}: {a} ≥ 0 sayı olmalı")
        for a in ("kadraj", "hareket"):
            if a in c and not isinstance(c[a], dict):
                R.hata(f"çekim {ad}: {a} nesne olmalı")
        if "klip_bas" in c and not c.get("klip"):
            R.uyari(f"çekim {ad}: klip_bas var ama klip yok (kaynak_bas kullanılır)")
    tekrar = [n for n, k in Counter(c.get("no") for c in C).items() if k > 1]
    if tekrar:
        R.hata(f"aynı no birden çok çekimde: {tekrar}")
    return len(R.hatalar) == n0


def olcek_denetle(p: dict, c: dict, g: tuple | None, R: Rapor) -> None:
    """Etkin ölçek = cover ölçeği × hareket.olcek ≤ 1,15 (çıktı pikseli / kaynak pikseli)."""
    if not g:
        return
    W, H = p["boyut"]
    cover = max(W / g[0], H / g[1])
    o = (c.get("hareket") or {}).get("olcek") or [1]
    try:
        punch = max(float(x) for x in o) if isinstance(o, list) else float(o)
    except (TypeError, ValueError):
        return
    if cover * punch > ZOOM_SINIR + EPS:
        ne = (f"punch ≤ {ZOOM_SINIR / cover:.2f}" if cover <= ZOOM_SINIR else
              f"kaynak bu boyutta zaten {cover:.2f}x büyütülüyor: punch koyma, yumuşak görüneceğini kullanıcıya söyle")
        R.uyari(f"çekim {c['no']}: etkin ölçek {cover * punch:.2f} (cover {cover:.2f} × hareket {punch:g}) > "
                f"{ZOOM_SINIR} ({g[0]}x{g[1]} → {W}x{H}) → {ne} (sabitleme zoom'u da çarpılır)")


# ---------------------------------------------------------------- zaman ve süreklilik
def zaman(p: dict, R: Rapor) -> None:
    fps, C = p["fps"], p["cekimler"]
    if any(b["cikti_bas"] < a["cikti_bas"] for a, b in zip(C, C[1:])):
        R.hata("cekimler cikti_bas sırasında değil (medya senkron/denetle liste sırasını kullanır: ilk çekimi atlar)")
        return
    for c in C:
        alanlar = ["cikti_bas", "cikti_son"] + ([] if gorsel_mi(c) else ["klip_bas" if c.get("klip") else "kaynak_bas"])
        for a in alanlar:
            t = float(c.get(a, 0.0))
            if not izgarada(t, fps):
                k = int(t * fps + EPS)
                R.hata(f"çekim {c['no']}: {a}={t} kare ızgarasında değil → {k}/{fps} = {k / fps:.6f} "
                       "(görüntü sesten 1 kareye kadar kayar)")
    if "sure" in p and not izgarada(float(p["sure"]), fps):
        R.hata(f"sure={p['sure']} kare ızgarasında değil")
    if abs(C[0]["cikti_bas"]) > EPS:
        R.hata(f"ilk çekim 0'da başlamıyor ({C[0]['cikti_bas']}): baştaki boşluk siyah kare olur")
    if C[0]["gecis"]["tur"] == "erime":
        R.hata("ilk çekime erime olmaz (önceki çekim yok); siyahtan açılış için siyah-dip")
    for o, c in zip(C, C[1:]):
        tur, n = c["gecis"]["tur"], c["gecis"]["sure_kare"]
        if tur == "erime":
            beklenen = o["cikti_son"] - n / fps
            if n < 1:
                R.hata(f"çekim {c['no']}: erimede sure_kare ≥ 1 olmalı")
            elif abs(c["cikti_bas"] - beklenen) > 1e-4:
                R.hata(f"çekim {c['no']}: erime örtüşmedir → cikti_bas = önceki cikti_son − {n}/{fps} = {beklenen:.6f}; "
                       f"plan {c['cikti_bas']}")
            elif n >= kare(o["cikti_son"] - o["cikti_bas"], fps) or n >= kare(c["cikti_son"] - c["cikti_bas"], fps):
                R.hata(f"çekim {c['no']}: {n} karelik erime çekimlerden birinden uzun")
        elif c["cikti_bas"] > o["cikti_son"] + 1e-4:
            R.hata(f"çekimler {o['no']}→{c['no']}: {(c['cikti_bas'] - o['cikti_son']) * 1000:.0f} ms boşluk (siyah kare)")
        elif c["cikti_bas"] < o["cikti_son"] - 1e-4:
            R.hata(f"çekimler {o['no']}→{c['no']}: '{tur}' ama {kare(o['cikti_son'] - c['cikti_bas'], fps)} kare örtüşüyor "
                   "(yalnız erime örtüşür)")
    if "sure" in p and abs(C[-1]["cikti_son"] - p["sure"]) > 1e-4:
        R.hata(f"son çekim {C[-1]['cikti_son']} sn'de bitiyor, plan süresi {p['sure']}")
    for c in C:
        d = c["cikti_son"] - c["cikti_bas"]
        if d < 3 / fps - EPS:
            R.hata(f"çekim {c['no']}: {kare(d, fps)} kare — flaş kare olur (denetle 'flas'); kısa vurgu için ≥ 3 kare")
        elif d < 0.5:
            R.uyari(f"çekim {c['no']}: {d:.2f} sn çok kısa; bilinçli bir patlama mı?")


# ---------------------------------------------------------------- kaynaklar, hız, ses
def kaynaklar(p: dict, kok: Path, R: Rapor) -> None:
    fps = p["fps"]
    for c in p["cekimler"]:
        no, hiz, d = c["no"], float(c["hiz"]), c["cikti_son"] - c["cikti_bas"]
        ky = yol(kok, c["kaynak"])
        if not ky.exists():
            R.hata(f"çekim {no}: kaynak yok: {c['kaynak']}")
            continue
        if not ky.is_relative_to((kok / "kaynak").resolve()):
            R.hata(f"çekim {no}: kaynak proje kaynak/ altında değil ({c['kaynak']}): asıl yerine salt okunur kopya kullan")
        kp = yol(kok, c["klip"]) if c.get("klip") else None
        if kp is not None:
            if not kp.exists():
                R.hata(f"çekim {no}: klip yok: {c['klip']}")
                continue
            if not kp.is_relative_to((kok / "calisma" / "klipler").resolve()):
                R.uyari(f"çekim {no}: klip calisma/klipler/ altında değil ({c['klip']})")
        ortam = kp or ky
        if ortam.suffix.lower() in (".heic", ".heif"):
            R.hata(f"çekim {no}: HEIC tarayıcıda ve ffmpeg 6.0'da açılmaz → sips -s format jpeg <heic> --out "
                   "calisma/klipler/<ad>.jpg ve klip olarak ver")
        if hiz < 1 and (kp is None or kp == ky):
            R.hata(f"çekim {no}: hiz {hiz:g} ama hazır klip yok. Ağır çekim önce medya yavaslat ile üretilir "
                   "(kompozisyonda data-playback-rate < 1 kare tekrarlar)")
        if ortam.suffix.lower() in GORSEL:
            olcek_denetle(p, c, goruntu(ortam), R)
            if c["ses"] == "kendi":
                R.hata(f"çekim {no}: görselin sesi olmaz (ses: muzik|sessiz)")
            if abs(hiz - 1) > EPS:
                R.uyari(f"çekim {no}: görselde hiz {hiz:g} anlamsız")
            continue
        g = goruntu(ortam)
        if g and g[2] in HDR:
            R.hata(f"çekim {no}: HDR ({g[2]}) {'klip' if kp is not None else 'asıl'} kompozisyona giriyor (--sdr hable "
                   "uygular) → medya sdr --cikti calisma/klipler/<ad>-sdr.mp4 ile klip üret")
        olcek_denetle(p, c, g, R)
        sure, _ = bilgi(ortam)
        gerek = medya_bas(c) + (d if (kp is not None and hiz < 1) else d * hiz)
        if sure is not None and gerek > sure + 1 / fps:
            R.hata(f"çekim {no}: {'klip' if kp is not None else 'kaynak'} {sure:.3f} sn ama plan {gerek:.3f} sn'ye kadar "
                   "okuyor (son kare donar/siyah)")
        if c["ses"] == "kendi":
            if abs(hiz - 1) > EPS:
                R.hata(f"çekim {no}: ses 'kendi' yalnız hiz 1'de (hızı değişen çekim sesi kullanılmaz)")
            if not bilgi(ky)[1]:
                R.hata(f"çekim {no}: ses 'kendi' ama kaynakta ses akışı yok")


# ---------------------------------------------------------------- müzik
def muzik(p: dict, m: dict | None, R: Rapor) -> None:
    fps, C = p["fps"], p["cekimler"]
    mz = p.get("muzik") or {}
    bas = float(mz.get("bas", 0.0))
    vurusa = [c for c in C[1:] if c["vurusa"]]
    if C[0]["vurusa"]:
        R.uyari("ilk çekimde vurusa: true ölçülmez (senkron ilk çekimi atlar)")
    for c in vurusa:
        if c["gecis"]["tur"] == "erime":
            R.hata(f"çekim {c['no']}: erimeye vurusa: true verilmez (senkron örtüşmenin BAŞINI ölçer). vurusa: false; "
                   "erimenin ORTASINI ölçü başına koy")
    # medya senkron/denetle/nle aynı sözleşmeyi okur (video vuruşu = müzik vuruşu − bas; senkron 2026-10-05'te
    # düzeltildi). Yine de tek saat en temizi: kullanılan bölüm ayrı WAV + kendi analizi + bas 0.
    if abs(bas) > EPS:
        R.uyari(f"muzik.bas = {bas}: geçerli, ama önerilen kullanılan bölümü calisma/ses/muzik.wav olarak kesip onu "
                "medya muzik ile analiz etmek ve bas: 0 (tek saat, tek analiz)")
    if not vurusa:
        return
    if m is None:
        R.hata("vuruşa işaretli kesim var ama müzik analizi yok (--muzik ya da plan muzik.analiz)")
        return
    seviye = m.get("guven_seviye")
    if seviye != "yuksek":
        R.hata(f"müzik güveni '{seviye}': vuruşa sert kesim yasak (yalnız 'yuksek'). Bölüm/cümle sınırı + erime "
               "kullan, vurusa: false yaz; vuruş iddiası yapma")
        return
    v = sorted(t - bas for t in m.get("vuruslar", []))
    if not v:
        R.hata("müzik analizinde vuruş yok")
        return
    for c in vurusa:
        b = min(v, key=lambda x: abs(x - c["cikti_bas"]))
        fark = c["cikti_bas"] - b
        if not (-1 / fps + EPS < fark <= EPS):
            k = int(b * fps + EPS)
            R.hata(f"çekim {c['no']}: kesim {c['cikti_bas']:.4f}, vuruş {b:.4f} ({fark * 1000:+.0f} ms) → cikti_bas = "
                   f"floor(vuruş·fps)/fps = {k}/{fps} = {k / fps:.6f} (görüntü 0–1 kare ÖNCE)")


def muzik_ek(p: dict, m: dict | None, R: Rapor) -> None:
    """Güven yüksekken erime ortası ve ölçü başı sağlığı (uyarı)."""
    if not m or m.get("guven_seviye") != "yuksek":
        if m:
            print(f"  müzik güveni '{m.get('guven_seviye')}': vuruş iddiası yok; kullanıcıya tık dinletisi öner")
        return
    fps, C = p["fps"], p["cekimler"]
    bas = float((p.get("muzik") or {}).get("bas", 0.0))
    v = sorted(t - bas for t in m.get("vuruslar", []))
    olcu = sorted(t - bas for t in m.get("olcu_baslari", []))
    saglam = True
    if len(v) > 8 and len(olcu) > 2:
        ara = sorted(sum(1 for x in v if a - 1e-3 <= x < b - 1e-3) for a, b in zip(olcu, olcu[1:]))
        med, oran = ara[len(ara) // 2], len(olcu) / len(v)
        if med not in (3, 4) or oran > 0.4:
            saglam = False
            R.uyari(f"ölçü başları şüpheli (ölçü başına medyan {med} vuruş, oran {oran:.2f}): ölçü başına dayanma; "
                    "bölüm sınırı + başlangıç zarfı PNG'si ile karar ver")
    hedef = olcu if (saglam and olcu) else v
    for o, c in zip(C, C[1:]):
        if c["gecis"]["tur"] == "erime" and hedef:
            orta = (c["cikti_bas"] + o["cikti_son"]) / 2
            b = min(hedef, key=lambda x: abs(x - orta))
            if abs(orta - b) > 1 / fps + EPS:
                R.uyari(f"çekim {c['no']}: erime ortası {orta:.3f}, en yakın {'ölçü başı' if hedef is olcu else 'vuruş'} "
                        f"{b:.3f} ({(orta - b) * 1000:+.0f} ms)")


# ---------------------------------------------------------------- zanaat (amatör izleri)
def zanaat(p: dict, R: Rapor) -> None:
    fps, C = p["fps"], p["cekimler"]
    sure = C[-1]["cikti_son"]
    dk = sure / 60
    turler = Counter(c["gecis"]["tur"] for c in C[1:])
    suslu = {t: n for t, n in turler.items() if t not in SADE}
    toplam = sum(suslu.values())
    print(f"  {len(C)} çekim, ort. {sure / len(C):.2f} sn; geçişler: {dict(turler)}")
    if len(suslu) > 3:
        R.uyari(f"{len(suslu)} farklı süslü geçiş türü {suslu}: bir ana tür + en çok 2 vurgu")
    if toplam >= 3 and max(suslu.values()) / toplam < 0.6:
        R.uyari(f"ana geçiş payı %{100 * max(suslu.values()) / toplam:.0f} (< %60): her kesimde başka geçiş amatör durur")
    if dk > 0 and toplam / dk > 6:
        R.uyari(f"dakikada {toplam / dk:.1f} süslü geçiş (sakin işte ≤ 4–6)")
    yavas = sum(1 for c in C if float(c["hiz"]) < 1)
    if dk > 0 and yavas / dk > 3:
        R.uyari(f"dakikada {yavas / dk:.1f} ağır çekim (≤ 3; yalnız duygu doruklarında)")
    parlak = sorted(c["cikti_bas"] for c in C if c["gecis"]["tur"] in PARLAK)
    if any(sum(1 for t in parlak if a <= t < a + 1) > 3 for a in parlak):
        R.uyari("1 sn içinde 3'ten çok flaş/beyaz geçiş (WCAG 2.3.1 ışığa duyarlılık sınırı)")
    uz = [kare(c["cikti_son"] - c["cikti_bas"], fps) for c in C]
    seri = en = 1
    for a, b in zip(uz, uz[1:]):
        seri = seri + 1 if a == b else 1
        en = max(en, seri)
    if en > 3:
        R.uyari(f"{en} çekim üst üste aynı uzunlukta: metronom gibi; uzunlukları değiştir")
    if len(uz) >= 5 and Counter(uz).most_common(1)[0][1] / len(uz) > 0.6:
        R.uyari("çekimlerin %60'ından fazlası aynı uzunlukta")


# ---------------------------------------------------------------- kompozisyon (HTML)
class _Html(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ogeler, self.betikler, self.yazilar, self._yigin = [], [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("video", "audio", "img"):
            self.ogeler.append((tag, a))
        if tag == "script" and a.get("src"):
            self.betikler.append(a["src"])
        if tag in ("script", "style", "title"):
            self._yigin.append(tag)

    def handle_endtag(self, tag):
        if self._yigin and self._yigin[-1] == tag:
            self._yigin.pop()

    def handle_data(self, data):
        if not self._yigin and data.strip():
            self.yazilar.append(data.strip())


def html_denetle(p: dict, html_yol: str, R: Rapor) -> None:
    fps, C = p["fps"], p["cekimler"]
    h = _Html()
    h.feed(Path(html_yol).read_text(encoding="utf-8"))
    kimlik = {a.get("id"): (t, a) for t, a in h.ogeler}
    for s in h.betikler:
        if s.startswith(("http:", "https:", "//")):
            R.hata(f"HTML ağdan betik yüklüyor ({s}): GSAP'ı yerel kopyadan yükle ($MEDYA/varliklar/js/gsap.min.js)")
    if h.yazilar:
        R.uyari(f"kompozisyonda ekran yazısı var {h.yazilar[:3]}: kullanıcı istedi mi? (BRIEF; istenmedikçe yazı yok)")
    for t, a in h.ogeler:
        src = a.get("src", "")
        if src.startswith(("../", "/", "http:", "https:", "file:")):
            R.hata(f"#{a.get('id')}: src '{src}' kompozisyon klasörünün dışını gösteriyor (lint hatası; çizim görüntüyü "
                   "sessizce atlar) → kompozisyon klasörüne bağlantı (ln -s ../klipler klipler) ve 'klipler/…'")
        r = a.get("data-playback-rate")
        if r is not None and float(r) < 1:
            R.hata(f"#{a.get('id')}: data-playback-rate {r} < 1 kare tekrarlar → medya yavaslat ile önceden üret")
        for k in ("data-start", "data-duration", "data-media-start"):
            if k in a and not izgarada(float(a[k]), fps):
                R.hata(f"#{a.get('id')}: {k}={a[k]} kare ızgarasında değil")
    for c in C:
        oge = kimlik.get(f"c{c['no']}")
        if not oge:
            R.hata(f"çekim {c['no']}: HTML'de id=\"c{c['no']}\" öğesi yok (zamanlı <video>/<img>)")
            continue
        t, a = oge
        d = c["cikti_son"] - c["cikti_bas"]
        for k, beklenen in (("data-start", c["cikti_bas"]), ("data-duration", d)):
            if abs(float(a.get(k, "nan")) - beklenen) > 1e-4:
                R.hata(f"#c{c['no']}: {k}={a.get(k)} ama plan {beklenen:.6f}")
        if Path(a.get("src", "")).name != Path(c.get("klip") or c["kaynak"]).name:
            R.hata(f"#c{c['no']}: src {a.get('src')} ≠ plan {c.get('klip') or c['kaynak']}")
        if t != "video":
            continue
        if abs(float(a.get("data-media-start", "0")) - medya_bas(c)) > 1e-4:
            R.hata(f"#c{c['no']}: data-media-start={a.get('data-media-start')} ama plan {medya_bas(c)}")
        sessiz = "muted" in a
        if c["ses"] == "kendi" and (sessiz or a.get("data-has-audio") != "true"):
            R.hata(f"#c{c['no']}: ses 'kendi' → muted yok, data-has-audio=\"true\" olmalı")
        if c["ses"] != "kendi" and not sessiz:
            R.hata(f"#c{c['no']}: ses '{c['ses']}' → <video> muted olmalı")
        hiz = float(c["hiz"])
        r = float(a.get("data-playback-rate", 1))
        if not c.get("klip") and hiz > 1 and abs(r - hiz) > 1e-6:
            R.hata(f"#c{c['no']}: hızlandırma {hiz:g} → data-playback-rate=\"{hiz:g}\" olmalı (şimdi {r:g})")
        if c.get("klip") and abs(r - 1) > 1e-6 and hiz < 1:
            R.hata(f"#c{c['no']}: pişmiş ağır çekim klibi 1x oynar; data-playback-rate kaldır")
    mz = p.get("muzik")
    if mz:
        oge = kimlik.get("muzik")
        if not oge or oge[0] != "audio":
            R.hata("HTML'de id=\"muzik\" <audio> yok")
            return
        a = oge[1]
        if abs(float(a.get("data-start", 0))) > EPS or abs(float(a.get("data-media-start", 0)) - float(mz.get("bas", 0))) > 1e-4:
            R.hata(f"müzik: data-start=\"0\" ve data-media-start=\"{mz.get('bas', 0)}\" (muzik.bas) olmalı; HTML "
                   f"{a.get('data-start')} / {a.get('data-media-start')}")
        if Path(a.get("src", "")).name != Path(mz["dosya"]).name:
            R.hata(f"müzik src {a.get('src')} ≠ plan {mz['dosya']} (analiz edilen dosyanın aynısı çalmalı)")


# ---------------------------------------------------------------- çizim (medya denetle raporu)
def pencereler(p: dict) -> list[tuple[float, float, str]]:
    """Planlı geçişlerin kapladığı aralıklar: buradaki kesim/flaş/siyah bulguları beklenir."""
    fps, C = p["fps"], p["cekimler"]
    P = []
    for i, c in enumerate(C):
        tur, n = c["gecis"]["tur"], c["gecis"]["sure_kare"]
        if tur == "erime" and i:
            P.append((c["cikti_bas"] - 1 / fps, C[i - 1]["cikti_son"] + 1 / fps, tur))
        elif tur not in SADE and tur != "erime":
            P.append((c["cikti_bas"] - (n + 1) / fps, c["cikti_bas"] + (n + 1) / fps, tur))
    return P


def cizim_denetle(p: dict, yol_: str, R: Rapor) -> None:
    fps, C = p["fps"], p["cekimler"]
    K = json.loads(Path(yol_).read_text()).get("denetimler", {})
    bulunan = K.get("kesimler", {}).get("anlar", [])
    P = pencereler(p)
    icinde = lambda t: next((tur for x, z, tur in P if x <= t <= z), None)
    # siyah/beyaz dipte kesim tam siyahın/beyazın altında olur: kare farkıyla görülmez
    sert = [c["cikti_bas"] for c in C[1:] if c["gecis"]["tur"] not in ("erime", "siyah-dip", "beyaz-dip")]
    tol = 1 / fps + EPS
    eksik = [t for t in sert if not any(abs(b - t) <= tol for b in bulunan)]
    fazla = [b for b in bulunan if not any(abs(b - t) <= tol for t in sert) and not icinde(b)]
    print(f"  çizim: {len(sert)} planlı sert kesimin {len(sert) - len(eksik)}'i ±1 karede bulundu")
    if eksik:
        R.uyari(f"çizimde bulunamayan planlı kesimler {eksik}: o anlara medya kontak --anlar ile bak "
                "(benzer iki çekim algılanmayabilir)")
    if fazla:
        R.uyari(f"planda olmayan kesimler {fazla[:10]}: flaş kare / yanlış klip mi? medya kontak --anlar ile bak")
    flas = K.get("flas", {}).get("anlar", [])
    beklenen = [(t, icinde(t)) for t in flas if icinde(t)]
    if beklenen:
        print(f"  not: 'flas' bulguları planlı geçiş içinde {beklenen} — beklenir; medya kontak --anlar ile doğrula")
    if [t for t in flas if not icinde(t)]:
        R.uyari(f"planlı geçiş dışında flaş kare: {[t for t in flas if not icinde(t)]} "
                "(silme: önceki karenin kopyasıyla değiştir)")
    for a, b in K.get("siyah", {}).get("ic", []):
        tur = icinde((a + b) / 2)
        if tur == "siyah-dip":
            print(f"  not: iç siyah {a:.2f}–{b:.2f} planlı siyah-dip — denetle KALDI der ama beklenir; raporda belirt")
        else:
            R.uyari(f"planlanmamış iç siyah {a:.2f}–{b:.2f}: boşluk/eksik klip mi?")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--muzik", help="medya muzik JSON'u (varsayılan: plan muzik.analiz)")
    ap.add_argument("--html", help="kompozisyon index.html")
    ap.add_argument("--denetim", help="medya denetle JSON raporu (çizimden sonra)")
    ap.add_argument("--kok", help="göreli yolların kökü (varsayılan: planın iki üstü)")
    x = ap.parse_args()
    plan_yolu = Path(x.plan).resolve()
    kok = Path(x.kok).resolve() if x.kok else plan_yolu.parent.parent
    p = json.loads(plan_yolu.read_text())
    R = Rapor()
    if sema(p, R):
        zaman(p, R)
        kaynaklar(p, kok, R)
        my = x.muzik or (p.get("muzik") or {}).get("analiz")
        m = json.loads(yol(kok, my).read_text()) if my else None
        muzik(p, m, R)
        muzik_ek(p, m, R)
        zanaat(p, R)
        if x.html:
            html_denetle(p, x.html, R)
        if x.denetim:
            cizim_denetle(p, x.denetim, R)
    print(f"{'KALDI' if R.hatalar else 'GEÇTİ'}: {len(R.hatalar)} hata, {len(R.uyarilar)} uyarı")
    return 1 if R.hatalar else 0


if __name__ == "__main__":
    raise SystemExit(main())
