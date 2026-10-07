"""medya denetle <video> [--plan p.json] [--muzik m.json] [--hedef web|sosyal|youtube|arsiv] — teslim öncesi kalite denetimi.

Ölçülebilir her şeyi ölçer, geçti/kaldı der; görsel kontrol için temas sayfası üretir. Denetimler:
  teknik    akışlar, çözünürlük/fps/codec/piksel biçimi, renk etiketleri (SDR bt709), süre, moov başta mı
  siyah     istenmeyen siyah kareler (blackdetect; baştaki/sondaki kararmalar ayrı raporlanır)
  donma     donmuş görüntü (freezedetect; bilinçli duraklama olabilir → uyarı)
  flas      1–2 karelik "flaş" çekimler (kare kare fark + renk histogramı; ffmpeg sahne puanı bunu göremez)
  ses       entegre LUFS, gerçek tepe, LRA, kırpılma, uzun sessizlik, kesimlerde tık
  senkron   (müzik analizi varsa) vuruşa işaretli kesimlerin vuruşa uzaklığı
  av        (planda "ses": "kendi" çekimler varsa) çekim sesi kaynağıyla hizalı mı (ms)
  meta      konum/GPS ve kişisel üst veri
Çıktı: <video>-denetim.json + <video>-denetim-kontak.png. Çıkış kodu 0 = geçti.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from ..ortak import MedyaHatasi, calistir, ffmpeg, json_oku, json_yaz, oran, probe, ses_akisi, ses_oku, video_akisi
from .incele import GPS_ETIKET
from .ustala import olc

HEDEFLER = {   # entegre LUFS aralığı, gerçek tepe üst sınırı
    "web": {"lufs": (-17.0, -15.0), "tepe": -1.0},
    "sosyal": {"lufs": (-15.0, -13.0), "tepe": -1.0},
    "youtube": {"lufs": (-15.0, -13.0), "tepe": -1.0},
    "arsiv": {"lufs": (-24.0, -12.0), "tepe": -1.0},
}


def _goruntu_gecisi(video: str, fps: float) -> dict:
    """ffmpeg geçişi: siyah ve donma. (Sahne puanı burada kullanılmaz: ffmpeg'in 'scene' puanı bir önceki
    değişime göre hesaplanır ve art arda iki büyük değişimin ikincisini bastırır — flaş kareyi göremez.)"""
    s = calistir([ffmpeg(), "-nostdin", "-hide_banner", "-i", video, "-an", "-vf",
                  "scale=320:-2,blackdetect=d=0.03:pix_th=0.10:pic_th=0.98,freezedetect=n=0.003:d=0.6",
                  "-f", "null", "-"])
    m = s.stderr.decode("utf-8", "replace")
    siyah = [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", m)]
    donma_bas = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", m)]
    donma_son = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", m)]
    donma = list(zip(donma_bas, donma_son + [float("nan")] * (len(donma_bas) - len(donma_son))))
    return {"siyah": siyah, "donma": donma}


def kare_farklari(video: str, gen: int = 96) -> dict:
    """Bütün kareleri küçük çözüp kare kare fark ve histogram uzaklığı hesaplar (kesim ve flaş için)."""
    v = video_akisi(probe(video)) or {}
    w, h = int(v.get("width", 16)), int(v.get("height", 9))
    yuk = max(2, round(gen * h / w / 2) * 2)
    s = calistir([ffmpeg(), "-nostdin", "-v", "error", "-i", video, "-an", "-vf", f"scale={gen}:{yuk}",
                  "-pix_fmt", "rgb24", "-f", "rawvideo", "-"])
    f = np.frombuffer(s.stdout, np.uint8).reshape(-1, yuk, gen, 3).astype(np.int16)
    n = len(f)
    hist = np.stack([np.concatenate([np.bincount(k[..., c].ravel() >> 4, minlength=16) for c in range(3)])
                     for k in f]).astype(float)
    hist /= hist.sum(1, keepdims=True)
    mad = np.zeros(n); hd = np.zeros(n)
    mad[1:] = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2, 3)) / 255.0
    hd[1:] = 0.5 * np.abs(np.diff(hist, axis=0)).sum(1)
    return {"mad": mad, "hd": hd, "hist": hist, "fps": oran(v.get("avg_frame_rate")) or 30.0, "n": n}


def kesim_kareleri(k: dict, esik_hd: float = 0.25, esik_mad: float = 0.12) -> np.ndarray:
    """Kesim: histogram ya da piksel farkı yüksek VE çevresindeki hareketin belirgin üstünde (uyarlamalı)."""
    mad, hd = k["mad"], k["hd"]
    yerel = np.array([np.median(mad[max(1, i - 15):i + 16]) for i in range(len(mad))])
    aday = ((hd > esik_hd) | (mad > esik_mad)) & (mad > 2.5 * yerel + 0.01)
    aday[0] = False
    return np.flatnonzero(aday)


def _flas_kareler(k: dict) -> list[float]:
    """Flaş kare: 1–2 karelik bir parça; renk dağılımı hem önceki hem sonraki kareden belirgin farklı
    (araya düşmüş siyah/yabancı kare, kesimde artık kalmış kare). Kesimden sonra hızla değişen hareket
    (aynı renk dağılımı) sayılmaz."""
    H, fps = k["hist"], k["fps"]
    kes = kesim_kareleri(k)
    flas = []
    for i, j in zip(kes, kes[1:]):
        L = j - i                                   # kısa parçanın kare sayısı
        if L > 2 or i < 1 or j >= len(H):
            continue
        parca = H[i:j].mean(0)
        d_once = 0.5 * np.abs(parca - H[i - 1]).sum()
        d_sonra = 0.5 * np.abs(parca - H[j]).sum()
        if d_once > 0.35 and d_sonra > 0.35:
            flas.append(round(float(i) / fps, 3))
    return flas


def _tiklar(video: str, kesimler: list[float]) -> list[dict]:
    """Kesim anında sesin ani sıçraması (tık/pat): ±6 ms içindeki fark tepesi, çevre 200 ms'nin medyanına oranla."""
    if not kesimler:
        return []
    x, sr = ses_oku(video, sr=48000)
    dx = np.abs(np.diff(x))
    supheli = []
    for t in kesimler:
        i = int(t * sr)
        if i < sr // 5 or i > len(dx) - sr // 5:
            continue
        w = int(0.006 * sr)
        pencere = dx[i - w: i + w]
        j = int(np.argmax(pencere))
        cevre = np.concatenate([dx[i - sr // 5: i - int(0.02 * sr)], dx[i + int(0.02 * sr): i + sr // 5]])
        taban = np.percentile(cevre, 99) + 1e-6
        r = float(pencere[j] / taban)
        # yalıtılmışlık: tık tek örneklik bir sıçramadır; davul/hi-hat ise milisaniyelerce süren enerji yığınıdır
        komsu = np.concatenate([pencere[max(0, j - w // 2): max(0, j - 3)], pencere[j + 4: j + w // 2]])
        yalitik = float(pencere[j] / (np.percentile(komsu, 90) + 1e-6)) if len(komsu) else 0.0
        if r > 4.0 and yalitik > 4.0:
            supheli.append({"t": round(float(t), 3), "oran": round(r, 1), "yalitiklik": round(yalitik, 1)})
    return supheli


def _av_hizasi(cikti: str, kaynak: str, c0: float, c1: float, k0: float, hiz: float = 1.0) -> dict:
    """Çıktıdaki [c0,c1] sesi ile kaynaktaki [k0, …] sesinin gecikmesi (ms). Pozitif: çıktıdaki ses geç."""
    sr = 8000
    sure = min(c1 - c0, 8.0)
    a, _ = ses_oku(cikti, sr=sr, bas=c0, sure=sure)
    on = min(0.5, k0)                                        # kaynakta k0'dan önce okunan pay (k0 < 0,5'te kırpılır)
    b, _ = ses_oku(kaynak, sr=sr, bas=k0 - on, sure=(sure * hiz) + 1.0)
    if hiz != 1.0 or len(a) < sr or len(b) < len(a):
        return {"olculemedi": True}
    a = a - a.mean(); b = b - b.mean()
    c = np.correlate(b, a, "valid")
    enerji = np.sqrt(np.convolve(b ** 2, np.ones(len(a)), "valid") * (a ** 2).sum()) + 1e-9
    nc = c / enerji
    j = int(np.argmax(nc))
    return {"gecikme_ms": round((on - j / sr) * 1000, 1), "ilinti": round(float(nc[j]), 3)}


GORSEL_UZANTI = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff", ".gif", ".bmp"}
PLANLI_DIP = {"siyah-dip", "beyaz-dip", "flas"}


def _planli_gecisler(plan: dict | None, fps: float) -> list[tuple[float, float]]:
    """Plandaki dip/flaş geçişlerinin zaman pencereleri (kesimin iki yanı, geçiş süresi + 1 kare pay)."""
    out = []
    for c in (plan or {}).get("cekimler") or []:
        g = c.get("gecis") or {}
        g = {"tur": g} if isinstance(g, str) else g
        if str(g.get("tur", "")).lower() in PLANLI_DIP:
            yari = (int(g.get("sure_kare") or 6) + 1) / fps
            out.append((c["cikti_bas"] - yari, c["cikti_bas"] + yari))
    return out


def _icinde(a: float, b: float, pencereler: list[tuple[float, float]]) -> bool:
    return any(p0 <= a and b <= p1 for p0, p1 in pencereler)


def denetle(video: str, plan: dict | None = None, muzik: dict | None = None, hedef: str = "web",
            beklenen: dict | None = None, sessiz: bool = False) -> dict:
    p = probe(video)
    v, a = video_akisi(p), ses_akisi(p)
    sure = float(p["format"]["duration"])
    fps = oran(v.get("avg_frame_rate")) if v else 30.0
    D: dict = {"video": video, "sure": sure, "hedef": hedef, "denetimler": {}}
    K = D["denetimler"]

    # teknik
    t = {"gecti": True, "bulgular": []}
    if not v:
        t["gecti"] = False; t["bulgular"].append("video akışı yok")
    else:
        t["ozet"] = {"boyut": f"{v.get('width')}x{v.get('height')}", "fps": round(fps, 3), "codec": v.get("codec_name"),
                     "pix_fmt": v.get("pix_fmt"), "aktarim": v.get("color_transfer"), "birincil": v.get("color_primaries")}
        if v.get("pix_fmt") not in ("yuv420p", "yuvj420p"):
            t["bulgular"].append(f"piksel biçimi {v.get('pix_fmt')} (telefon/web uyumu için yuv420p önerilir)")
        if v.get("color_transfer") in ("smpte2084", "arib-std-b67"):
            t["bulgular"].append("çıktı HDR etiketli; SDR teslimde yanlış renk görünür"); t["gecti"] = False
        if beklenen:
            if beklenen.get("boyut") and t["ozet"]["boyut"] != beklenen["boyut"]:
                t["gecti"] = False; t["bulgular"].append(f"boyut {t['ozet']['boyut']} ≠ beklenen {beklenen['boyut']}")
            if beklenen.get("fps") and abs(fps - beklenen["fps"]) > 0.01:
                t["gecti"] = False; t["bulgular"].append(f"fps {fps:.3f} ≠ beklenen {beklenen['fps']}")
            if beklenen.get("sure") and abs(sure - beklenen["sure"]) > 0.1:
                t["gecti"] = False; t["bulgular"].append(f"süre {sure:.2f} ≠ beklenen {beklenen['sure']}")
    with open(video, "rb") as fh:
        bas = fh.read(4 * 1024 * 1024)
    moov, mdat = bas.find(b"moov"), bas.find(b"mdat")
    if mdat >= 0 and (moov < 0 or moov > mdat):                 # moov ilk 4 MB'ta yok ya da mdat'tan sonra
        t["bulgular"].append("moov sonda (web'de hızlı başlatma yok): ffmpeg -c copy -movflags +faststart ile düzelt")
        if hedef in ("web", "sosyal", "youtube"):
            t["gecti"] = False
    if v and (v.get("color_primaries") in (None, "unknown") or v.get("color_transfer") in (None, "unknown")):
        t["bulgular"].append("renk etiketleri boş (primaries/transfer bilinmiyor): oynatıcılar farklı yorumlayabilir; "
                             "SDR teslimde -colorspace bt709 -color_primaries bt709 -color_trc bt709 ile etiketle")
    K["teknik"] = t

    # görüntü: siyah, donma, flaş
    if v:
        g = _goruntu_gecisi(video, fps)
        uc = 0.6
        ic_siyah = [(a_, b_) for a_, b_ in g["siyah"] if a_ > uc and b_ < sure - uc]
        pencere = _planli_gecisler(plan, fps)             # planlı siyaha/beyaza dip ve flaş kusur sayılmaz
        planli = [(a_, b_) for a_, b_ in ic_siyah if _icinde(a_, b_, pencere)]
        ic_siyah = [x for x in ic_siyah if x not in planli]
        K["siyah"] = {"gecti": not ic_siyah, "ic": ic_siyah, "planli": planli,
                      "bas_son": [(a_, b_) for a_, b_ in g["siyah"] if (a_, b_) not in ic_siyah + planli]}
        K["donma"] = {"gecti": True, "uyari": [(a_, b_) for a_, b_ in g["donma"]]}
        kf = kare_farklari(video)
        flas = _flas_kareler(kf)
        planli_flas = [t_ for t_ in flas if _icinde(t_, t_, pencere)]
        flas = [t_ for t_ in flas if t_ not in planli_flas]
        K["flas"] = {"gecti": not flas, "anlar": flas, "planli": planli_flas}
        kesimler = [round(float(i) / kf["fps"], 3) for i in kesim_kareleri(kf)]
        K["kesimler"] = {"gecti": True, "sayi": len(kesimler), "anlar": kesimler[:200]}
    else:
        kesimler = []
    if plan and plan.get("cekimler"):
        kesimler = [c["cikti_bas"] for c in plan["cekimler"][1:]]

    # ses
    if a:
        o = olc(video)
        alt_, ust = HEDEFLER[hedef]["lufs"]
        s = {"olcum": o, "bulgular": []}
        s["gecti"] = alt_ <= o["lufs"] <= ust and o["tepe_dbtp"] <= HEDEFLER[hedef]["tepe"]
        if not alt_ <= o["lufs"] <= ust:
            s["bulgular"].append(f"ses yüksekliği {o['lufs']:.1f} LUFS, hedef {alt_}…{ust} → medya ustala")
        if o["tepe_dbtp"] > HEDEFLER[hedef]["tepe"]:
            s["bulgular"].append(f"gerçek tepe {o['tepe_dbtp']:.1f} dBTP > {HEDEFLER[hedef]['tepe']} → medya ustala")
        m = calistir([ffmpeg(), "-nostdin", "-hide_banner", "-i", video, "-vn", "-af",
                      "silencedetect=n=-50dB:d=1.5,astats=metadata=0:measure_perchannel=none", "-f", "null", "-"]
                     ).stderr.decode("utf-8", "replace")
        sessiz = [(float(a_), float(b_)) for a_, b_ in re.findall(r"silence_start: ([\d.]+)[\s\S]*?silence_end: ([\d.]+)", m)]
        ic_sessiz = [x for x in sessiz if x[0] > 1.0 and x[1] < sure - 1.0]
        if ic_sessiz:
            s["bulgular"].append(f"videonun içinde {len(ic_sessiz)} uzun sessizlik (≥1,5 sn): {ic_sessiz[:3]}")
        xs, _ = ses_oku(video, sr=48000, kanal=2)
        kirpik = int(np.sum(np.abs(xs) >= 0.999))
        s["kirpik_ornek"] = kirpik
        if kirpik > 10:
            s["bulgular"].append(f"{kirpik} örnek kırpılmış (|x| ≥ 0,999) → kazancı düşür / sınırlayıcı")
            s["gecti"] = False
        tik = _tiklar(video, kesimler)
        if tik:
            s["bulgular"].append(f"{len(tik)} kesimde olası tık/pat (ses kesiminde mikro geçiş yok?): {tik[:5]}")
        s["tik"] = tik
        K["ses"] = s
    else:
        K["ses"] = ({"gecti": True, "bulgular": ["sessiz teslim (beklenen): ses akışı yok"]} if sessiz
                    else {"gecti": False, "bulgular": ["ses akışı yok"]})

    # senkron
    if muzik:
        from .senkron import senkron
        r = senkron(video, muzik, plan)
        K["senkron"] = {"gecti": r.get("karar") == "vurusta", **{k: r[k] for k in r if k != "kesimler"}}

    # çekim sesi hizası
    if plan and plan.get("cekimler"):
        av = []
        for c in plan["cekimler"]:
            if c.get("ses") == "kendi" and c.get("kaynak"):
                h = _av_hizasi(video, c["kaynak"], c["cikti_bas"] + 0.1, c["cikti_son"] - 0.1, c["kaynak_bas"] + 0.1,
                               float(c.get("hiz", 1.0)))
                av.append({"no": c.get("no"), **h})
        if av:
            kotu = [x for x in av if not x.get("olculemedi") and (abs(x["gecikme_ms"]) > 45 or x["ilinti"] < 0.5)]
            K["av"] = {"gecti": not kotu, "olcumler": av, "kotu": kotu}

    # meta
    etiket = {**(p.get("format", {}).get("tags") or {}), **((v or {}).get("tags") or {})}
    konum = [k for k in GPS_ETIKET if k in etiket]
    K["meta"] = {"gecti": not konum, "konum_etiketleri": konum,
                 "not": "paylaşmadan önce: medya meta-temizle" if konum else ""}

    D["gecti"] = all(x.get("gecti", True) for x in K.values())
    return D


def calistir_(args) -> int:
    plan = json_oku(args.plan) if args.plan else None
    muzik = json_oku(args.muzik) if args.muzik else None
    beklenen = {}
    if args.boyut:
        beklenen["boyut"] = args.boyut
    if args.fps:
        beklenen["fps"] = args.fps
    if args.sure:
        beklenen["sure"] = args.sure
    if Path(args.video).suffix.lower() in GORSEL_UZANTI:
        raise MedyaHatasi("medya denetle video içindir; durağan görsel teslim denetimi: gorsel-uretim becerisi "
                          "(scripts/olc.py --teslim)")
    r = denetle(args.video, plan, muzik, args.hedef, beklenen or None, sessiz=args.sessiz)
    taban = Path(args.json or str(Path(args.video).with_suffix("")) + "-denetim.json")
    json_yaz(taban, r)
    for ad, d in r["denetimler"].items():
        isaret = "✓" if d.get("gecti", True) else "✗"
        ayrinti = "; ".join(d.get("bulgular", []))
        if ad == "siyah" and d.get("ic"):
            ayrinti = f"içeride siyah: {d['ic'][:4]}"
        if ad == "flas" and d.get("anlar"):
            ayrinti = f"flaş kare: {d['anlar'][:6]}"
        if ad == "donma" and d.get("uyari"):
            ayrinti = f"donma (bilinçli mi?): {d['uyari'][:4]}"
        if ad == "ses" and d.get("olcum"):
            o = d["olcum"]
            ayrinti = f"{o['lufs']:.1f} LUFS, tepe {o['tepe_dbtp']:.1f} dBTP, LRA {o['lra']:.1f}" + (f" — {ayrinti}" if ayrinti else "")
        if ad == "meta" and d.get("konum_etiketleri"):
            ayrinti = f"konum üst verisi: {', '.join(d['konum_etiketleri'])} → {d['not']}"
        if ad == "senkron":
            ayrinti = f"{d.get('karar')}: p90 {d.get('p90_ms', float('nan')):.0f} ms, en büyük {d.get('en_buyuk_ms', float('nan')):.0f} ms"
        print(f"{isaret} {ad:<8} {ayrinti}")
    print(("GEÇTİ" if r["gecti"] else "KALDI") + f" → {taban}")
    if not args.kontaksiz:
        from .kontak import kontak_sayfasi
        sure = r["sure"]
        anlar = list(np.linspace(0.25, max(0.3, sure - 0.1), 40))
        k = kontak_sayfasi(args.video, anlar, taban.with_name(taban.stem + "-kontak.png"), genislik=150, sutun=10)
        print(f"görsel kontrol → {k}")
    return 0 if r["gecti"] else 1


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="teslim öncesi kalite denetimi")
    p.add_argument("video")
    p.add_argument("--plan", help="kurgu planı JSON (kesimler, çekim sesleri)")
    p.add_argument("--muzik", help="medya muzik çıktısı JSON (vuruş senkronu için)")
    p.add_argument("--hedef", default="web", choices=list(HEDEFLER))
    p.add_argument("--boyut", help="beklenen boyut, ör. 1080x1920")
    p.add_argument("--fps", type=float)
    p.add_argument("--sure", type=float)
    p.add_argument("--json")
    p.add_argument("--kontaksiz", action="store_true", help="temas sayfası üretme")
    p.add_argument("--sessiz", action="store_true",
                   help="bilerek sessiz teslim (GIF/döngü/yükleniyor animasyonu): ses akışı yokluğu kusur sayılmaz")
    p.set_defaults(islev=calistir_)
