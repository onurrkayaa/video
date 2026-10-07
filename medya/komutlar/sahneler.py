"""medya sahneler <video> — çekim sınırları.

Sağlayıcı kayıt defterinden seçilir: PySceneDetect (AdaptiveDetector; kurulu ise) ya da ffmpeg sahne
puanı (her zaman var). Çıktı: {"kesimler": [t…], "cekimler": [{bas, son, sure}…]}; --kontak ile her
çekimin ortasından bir kare içeren etiketli temas sayfası.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..kayit import saglayici_sec
from ..ortak import calistir, ffmpeg, json_yaz, probe, uyar


def _ffmpeg_kesimler(video: str, esik: float) -> list[float]:
    s = calistir([ffmpeg(), "-nostdin", "-hide_banner", "-i", video, "-an", "-vf",
                  f"scale=240:-2,select='gt(scene,{esik})',showinfo", "-f", "null", "-"])
    return [float(x) for x in re.findall(r"pts_time:([0-9.]+)", s.stderr.decode("utf-8", "replace"))]


def _pyscenedetect_kesimler(video: str, esik: float) -> list[float]:
    from scenedetect import AdaptiveDetector, detect          # noqa: PLC0415 (isteğe bağlı bağımlılık)
    # varsayılan 3,0 düşük kontrastlı kesimleri kaçırıyor (sentetik sınamada 5 kesimin 1'i); 2,0 hepsini buldu
    sahne = detect(video, AdaptiveDetector(adaptive_threshold=2.0 * esik / 0.25), show_progress=False)
    return [b.seconds for b, _ in sahne[1:]]


def kesimleri_bul(video: str, *, esik: float = 0.25, en_kisa: float = 0.5) -> tuple[list[float], str]:
    try:
        s = saglayici_sec("sahneler")
        ad = s.ad
    except Exception:
        ad = "ffmpeg"
    try:
        ham = _pyscenedetect_kesimler(video, esik) if ad == "pyscenedetect" else _ffmpeg_kesimler(video, esik)
    except Exception as e:                                   # sağlayıcı bozuksa ffmpeg'e düş
        if ad != "ffmpeg":
            uyar(f"{ad} başarısız ({e}); ffmpeg sahne puanına düşüldü")
        ad, ham = "ffmpeg", _ffmpeg_kesimler(video, esik)
    kesimler: list[float] = []
    for t in sorted(ham):                                     # birbirine çok yakın (flaş/titreşim) kesimleri birleştir
        if not kesimler or t - kesimler[-1] >= en_kisa:
            kesimler.append(round(t, 3))
    return kesimler, ad


def calistir_(args) -> int:
    sure = float(probe(args.video)["format"]["duration"])
    kesimler, ad = kesimleri_bul(args.video, esik=args.esik, en_kisa=args.en_kisa)
    sinir = [0.0, *kesimler, sure]
    cekimler = [{"no": i, "bas": a, "son": b, "sure": round(b - a, 3)} for i, (a, b) in enumerate(zip(sinir, sinir[1:]))]
    veri = {"video": args.video, "saglayici": ad, "esik": args.esik, "kesimler": kesimler, "cekimler": cekimler}
    cikti = args.json or str(Path(args.video).with_suffix("")) + "-sahneler.json"
    json_yaz(cikti, veri)
    print(f"{len(cekimler)} çekim ({ad}) → {cikti}")
    if args.kontak:
        from .kontak import kontak_sayfasi
        anlar = [(c["bas"] + c["son"]) / 2 for c in cekimler]
        etiket = [f"#{c['no']} {c['bas']:.1f}-{c['son']:.1f}" for c in cekimler]
        yol = kontak_sayfasi(args.video, anlar, str(Path(cikti).with_suffix("")) + "-kontak.png", genislik=150,
                             sutun=12, etiketler=etiket)
        print(f"temas sayfası → {yol}")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="çekim sınırları")
    p.add_argument("video")
    p.add_argument("--esik", type=float, default=0.25, help="ffmpeg sahne puanı eşiği (0-1)")
    p.add_argument("--en-kisa", type=float, default=0.5, help="bundan kısa aralıklı kesimleri birleştir (sn)")
    p.add_argument("--json")
    p.add_argument("--kontak", action="store_true", help="çekim başına bir kare içeren temas sayfası üret")
    p.set_defaults(islev=calistir_)
