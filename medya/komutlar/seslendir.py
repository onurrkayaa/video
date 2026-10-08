"""medya seslendir "<metin>"|metin.txt --cikti dis-ses.wav [--kimlik ses/anlatici] [--tarif "…"] [--referans kayit.wav --rizali]

Dış ses (TTS): VoxCPM2 (OpenBMB; kod ve ağırlık Apache-2.0, 30 dil, Türkçe dahil), mlx-community 8-bit (3,2 GB),
mlx-audio ile yerelde ve çevrimdışı. Ölçüm (2026-10-08, bu Mac; 4-bit'le aynı kimlik ve tohumla A/B, 40'ar Türkçe
cümle, yeniden üretimsiz): Whisper dökümüyle CER %0,74 (4-bit %0,97; İ/ı/ç/ğ/ş, sayılar dahil); 1 sn ses ~2,5 sn'de.

SES KİMLİĞİ (tutarlılık): VoxCPM2 aynı tarifle her çağrıda BAŞKA bir ses üretir — ayrı üretilen cümleler arası
konuşmacı benzerliği ortalama 0,29 ölçüldü. Bu yüzden ses bir kez "kimlik" olarak üretilir (ya da senin kaydından
alınır) ve bütün cümleler ondan üretilir: kimliğe benzerlik varsayılan "devam" kipinde (kimliğin metniyle birlikte)
ort. 0,82 (en düşük 0,73; 8-bit, 40 cümle); "klon" kipi 8-bit'te ölçülmedi (4-bit, 5 cümle: ort. 0,73, en düşük 0,67).
Kimlik <önek>.wav + <önek>.json olarak saklanır;
aynı projede sonraki dış sesler --kimlik ile aynı sesi kullanır.
  --tarif "A calm, warm male voice in his thirties"  yeni kimlik için ses tarifi (İngilizce tarif)
  --referans kayit.wav --rizali                    kendi sesinden (5–15 sn temiz kayıt) kimlik; YALNIZ kendi sesin ya da
                                                    açık rızası olan birinin sesi (gerçek bir kişiyi taklit etmek yok)
DOĞRULAMA (varsayılan): her cümle Whisper ile yazıya dökülür (Türkçe normalleştirilmiş CER) ve kimliğe konuşmacı
benzerliği ölçülür (SpeechBrain ECAPA). Kapı: toplam CER ≤ %3, cümle CER ≤ %8, benzerlik ≥ 0,5; kalan cümle en çok
--deneme kez yeniden üretilir. Konuşma hızı 10–18 karakter/sn dışındaysa uyarılır. Sesin doğallığı ÖLÇÜLEMEZ:
kullanıcı dinler. Çıktı: 48 kHz mono 24-bit WAV + <cikti>.json (cümle zamanları, ölçümler). Ses düzeyi: sonra
`medya ustala` (miksin içinde).
"""
from __future__ import annotations

import json
import re
import tempfile
from datetime import date
from pathlib import Path

import numpy as np

from ..ortak import KOK, MedyaHatasi, bilgi, calistir, disk_bekcisi, ffmpeg, json_oku, json_yaz, ses_oku, uyar

MLX_PY = KOK / ".uv" / "tools" / "mlx-audio" / "bin" / "python"
SES_PY = KOK / "ortamlar" / "ses" / "bin" / "python"
URET = KOK / "medya" / "isciler" / "ses_uret_isci.py"
DOGRULA = KOK / "medya" / "isciler" / "ses_dogrula_isci.py"
HUB = KOK / "modeller" / "hf" / "hub"
MODEL = HUB / "models--mlx-community--VoxCPM2-8bit" / "snapshots" / "d52725898a0675703f7f9ddc5a4d1a3cdbb99032"
ECAPA = HUB / "models--speechbrain--spkrec-ecapa-voxceleb" / "snapshots" / "0f99f2d0ebe89ac095bcc5903c4dd8f72b367286"
WHISPER = "mlx-community/whisper-large-v3-turbo"
SR = 48000
ANKRAJ = "Merhaba, bu videonun anlatıcısıyım. Sakin, net ve sıcak bir sesle konuşuyorum."
VARSAYILAN_TARIF = "A clear, warm, natural adult narrator voice, speaking calmly"
KAPI = {"toplam_cer": 0.03, "cumle_cer": 0.08, "benzerlik": 0.5}


def cumlelere_bol(metin: str) -> list[tuple[str, bool]]:
    """→ [(cümle, paragraf_sonu)]. Cümle sonu: . ! ? … ardından boşluk ve büyük harf/rakam/tırnak."""
    out: list[tuple[str, bool]] = []
    for p in [p for p in re.split(r"\n\s*\n", metin.strip()) if p.strip()]:
        p = " ".join(p.split())
        parca = re.split(r"(?<=[.!?…])\s+(?=[A-ZÇĞİÖŞÜ0-9\"'“‘(])", p)
        birlesik: list[str] = []
        for s in parca:
            if birlesik and len(birlesik[-1]) < 20:            # çok kısa parça ("Evet.") tek başına üretilmez
                birlesik[-1] += " " + s
            else:
                birlesik.append(s)
        out += [(s, i == len(birlesik) - 1) for i, s in enumerate(birlesik)]
    return out


def _isci(py: Path, betik: Path, is_: dict, g: Path, ad: str) -> dict:
    if not py.exists():
        raise MedyaHatasi(f"ortam yok: {py} — medya kur voxcpm2 / medya kur ses-ortami")
    (g / f"{ad}-is.json").write_text(json.dumps(is_, ensure_ascii=False))
    calistir([str(py), str(betik), str(g / f"{ad}-is.json"), str(g / f"{ad}-sonuc.json")],
             hata_mesaji=f"{ad} işçisi başarısız")
    return json_oku(g / f"{ad}-sonuc.json")


def _kirp(x: np.ndarray, esik_db: float = -45.0, pay: float = 0.03) -> np.ndarray:
    """Baştaki/sondaki sessizliği kırp (20 ms pencere RMS), 30 ms pay bırak."""
    w = int(0.02 * SR)
    if len(x) < 2 * w:
        return x
    n = len(x) // w
    rms = np.sqrt((x[:n * w].reshape(n, w) ** 2).mean(1) + 1e-12)
    ses = np.where(20 * np.log10(rms) > esik_db)[0]
    if not len(ses):
        return x
    a = max(0, ses[0] * w - int(pay * SR))
    b = min(len(x), (ses[-1] + 1) * w + int(pay * SR))
    return x[a:b]


def kimlik_hazirla(onek: Path, *, tarif: str | None, referans: str | None, referans_metin: str | None,
                   yeni: bool, g: Path) -> dict:
    wav, js = onek.with_suffix(".wav"), onek.with_suffix(".json")
    if referans:
        calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", referans, "-t", "15", "-vn", "-ac", "1", "-ar",
                  str(SR), "-c:a", "pcm_s16le", str(wav)], hata_mesaji="referans ses çözülemedi")
        if not referans_metin:
            from .yaziya_dok import yaziya_dok
            referans_metin = yaziya_dok(str(wav), dil="tr")["metin"]
        k = {"kaynak": "referans (kullanıcı rızalı kayıt)", "dosya": Path(referans).name, "metin": referans_metin,
             "tarih": date.today().isoformat()}
        json_yaz(js, k)
        return {**k, "wav": str(wav)}
    if wav.exists() and js.exists() and not yeni:
        return {**json_oku(js), "wav": str(wav)}
    t = tarif or VARSAYILAN_TARIF
    r = _isci(MLX_PY, URET, {"model": str(MODEL), "klasor": str(g / "kimlik"), "tarif": t, "kimlik": None,
                             "cumleler": [{"ad": "kimlik", "metin": ANKRAJ}]}, g, "kimlik")
    onek.parent.mkdir(parents=True, exist_ok=True)
    x, _ = ses_oku(r["cumleler"][0]["wav"], sr=SR)
    _yaz_wav(_kirp(x), wav)
    k = {"kaynak": "tarif", "tarif": t, "metin": ANKRAJ, "model": "VoxCPM2 8-bit (d527258)",
         "tarih": date.today().isoformat()}
    json_yaz(js, k)
    return {**k, "wav": str(wav)}


def _yaz_wav(x: np.ndarray, hedef: Path, hiz: float = 1.0) -> None:
    komut = [ffmpeg(), "-nostdin", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-"]
    if abs(hiz - 1.0) > 1e-3:
        komut += ["-af", f"atempo={hiz:g}"]
    calistir(komut + ["-c:a", "pcm_s24le", str(hedef)], girdi=np.asarray(x, "<f4").tobytes(),
             hata_mesaji="WAV yazılamadı")


def seslendir(metin: str, cikti: str, *, kimlik: str | None = None, tarif: str | None = None,
              referans: str | None = None, referans_metin: str | None = None, rizali: bool = False,
              yeni_kimlik: bool = False, duraklama: float = 0.35, hiz: float = 1.0, dogrula: bool = True,
              deneme: int = 2, kip: str = "devam") -> dict:
    if referans and not rizali:
        raise MedyaHatasi("referans ses yalnız KENDİ sesin ya da açık rızası olan birinin sesi olabilir; "
                          "onaylıyorsan --rizali ekle (gerçek bir kişiyi taklit etmek yasak)")
    if not MODEL.exists():
        raise MedyaHatasi("VoxCPM2 modeli yok: medya kur voxcpm2")
    disk_bekcisi(2.5, "seslendirme (VoxCPM2 bellek tepesi 7–14 GB)")
    cumleler = cumlelere_bol(metin)
    if not cumleler:
        raise MedyaHatasi("metin boş")
    cikti_p = Path(cikti)
    onek = Path(kimlik) if kimlik else cikti_p.with_name(cikti_p.stem + "-kimlik")
    with tempfile.TemporaryDirectory() as gd:
        g = Path(gd)
        k = kimlik_hazirla(onek, tarif=tarif, referans=referans, referans_metin=referans_metin,
                           yeni=yeni_kimlik, g=g)
        kimlik_is = {"wav": k["wav"], "metin": k.get("metin")}
        bekleyen = [{"ad": f"{i:03d}", "metin": c} for i, (c, _) in enumerate(cumleler)]
        uretim, olcum = {}, {}
        for tur in range(1 + (deneme if dogrula else 0)):
            r = _isci(MLX_PY, URET, {"model": str(MODEL), "klasor": str(g / f"tur{tur}"), "kimlik": kimlik_is,
                                     "kip": kip, "cumleler": bekleyen}, g, f"uret{tur}")
            for c in r["cumleler"]:
                uretim[c["ad"]] = c
            if not dogrula:
                break
            d = _isci(SES_PY, DOGRULA, {"whisper": WHISPER, "ecapa": str(ECAPA) if ECAPA.exists() else None,
                                        "dil": "tr", "kimlik_wav": k["wav"],
                                        "cumleler": [{**b, "wav": uretim[b["ad"]]["wav"]} for b in bekleyen]},
                      g, f"dogrula{tur}")
            for x in d["cumleler"]:
                olcum[x["ad"]] = {**x, "tur": tur}
            bekleyen = [b for b in bekleyen if olcum[b["ad"]]["cer"] > KAPI["cumle_cer"]
                        or olcum[b["ad"]].get("benzerlik", 1.0) < KAPI["benzerlik"]]
            if not bekleyen:
                break
            if tur < deneme:
                bilgi(f"  {len(bekleyen)} cümle kapıdan kaldı, yeniden üretiliyor ({tur + 1}/{deneme})")
        # birleştir: kırpılmış cümleler + duraklamalar (paragraf sonunda iki kat)
        parca, zaman, t = [], [], 0.0
        for i, (c, paragraf_sonu) in enumerate(cumleler):
            x, _ = ses_oku(uretim[f"{i:03d}"]["wav"], sr=SR)
            x = _kirp(x)
            parca.append(x)
            zaman.append({"no": i + 1, "metin": c, "bas": round(t / hiz, 3), "son": round((t + len(x) / SR) / hiz, 3)})
            t += len(x) / SR
            if i < len(cumleler) - 1:
                bosluk = duraklama * (2 if paragraf_sonu else 1)
                parca.append(np.zeros(int(bosluk * SR), np.float32))
                t += bosluk
        cikti_p.parent.mkdir(parents=True, exist_ok=True)
        _yaz_wav(np.concatenate(parca), cikti_p, hiz)
    rapor = {"cikti": str(cikti_p), "sure": round(t / hiz, 3), "kimlik": {kk: v for kk, v in k.items()},
             "model": "VoxCPM2 8-bit (mlx-community, d527258) — Apache-2.0", "kip": kip, "hiz": hiz,
             "cumleler": [{**z, **{a: olcum.get(f"{z['no'] - 1:03d}", {}).get(a) for a in
                                   ("cer", "benzerlik", "karakter_sn", "dokum", "degisen", "dusen", "eklenen", "tur")}}
                          for z in zaman]}
    if dogrula:
        n = sum(len(c) for c, _ in cumleler)
        toplam = sum((olcum[f"{i:03d}"]["cer"] * len(c)) for i, (c, _) in enumerate(cumleler)) / max(n, 1)
        benz = [o.get("benzerlik") for o in olcum.values() if o.get("benzerlik") is not None]
        kalan = [z["no"] for z in rapor["cumleler"] if (z["cer"] or 0) > KAPI["cumle_cer"]
                 or (z["benzerlik"] is not None and z["benzerlik"] < KAPI["benzerlik"])]
        hizli = [z["no"] for z in rapor["cumleler"] if z["karakter_sn"] and not 10 <= z["karakter_sn"] <= 18]
        rapor["dogrulama"] = {"toplam_cer": round(toplam, 4), "benzerlik_min": min(benz) if benz else None,
                              "benzerlik_ort": round(float(np.mean(benz)), 3) if benz else None,
                              "kalan_cumleler": kalan, "hiz_disi_cumleler": hizli, "kapi": KAPI,
                              "gecti": toplam <= KAPI["toplam_cer"] and not kalan}
    json_yaz(cikti_p.with_suffix(".json"), rapor)
    return rapor


def calistir_(args) -> int:
    p = Path(args.metin)
    metin = p.read_text(encoding="utf-8") if p.suffix.lower() == ".txt" and p.exists() else args.metin
    r = seslendir(metin, args.cikti, kimlik=args.kimlik, tarif=args.tarif, referans=args.referans,
                  referans_metin=args.referans_metin, rizali=args.rizali, yeni_kimlik=args.yeni_kimlik,
                  duraklama=args.duraklama, hiz=args.hiz, dogrula=not args.dogrulamasiz, deneme=args.deneme,
                  kip=args.kip)
    print(f"{r['cikti']}  ({r['sure']:.1f} sn, {len(r['cumleler'])} cümle; kimlik: {r['kimlik']['wav']})")
    d = r.get("dogrulama")
    if d:
        print(f"  {'✓' if d['gecti'] else '✗'} CER %{100 * d['toplam_cer']:.1f} · konuşmacı benzerliği ort "
              f"{d['benzerlik_ort']} / en düşük {d['benzerlik_min']}"
              + (f" · kapıdan kalan cümle: {d['kalan_cumleler']}" if d["kalan_cumleler"] else ""))
        if d["hiz_disi_cumleler"]:
            uyar(f"konuşma hızı 10–18 karakter/sn dışında: cümle {d['hiz_disi_cumleler']} (gerekirse --hiz)")
        print("  doğallık ölçülemez: dinle. Aynı sesle devam için: --kimlik " + str(Path(r["kimlik"]["wav"]).with_suffix("")))
        return 0 if d["gecti"] else 1
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="metinden dış ses (Türkçe dahil): VoxCPM2, tutarlı ses kimliği, ölçülü doğrulama",
                       description=__doc__.split("\n\n")[0])
    p.add_argument("metin", help="metnin kendisi ya da .txt dosyası (boş satır = paragraf, uzun duraklama)")
    p.add_argument("--cikti", required=True, help="çıktı WAV (yanına aynı adla .json rapor)")
    p.add_argument("--kimlik", help="ses kimliği öneki (<önek>.wav/.json); yoksa üretilir. Varsayılan: <cikti>-kimlik")
    p.add_argument("--tarif", help=f"yeni kimlik için ses tarifi, İngilizce (varsayılan: '{VARSAYILAN_TARIF}')")
    p.add_argument("--yeni-kimlik", action="store_true", help="kimlik varsa da yeniden üret (başka bir ses)")
    p.add_argument("--referans", help="kimlik bu kayıttan (5–15 sn temiz konuşma) — --rizali gerekir")
    p.add_argument("--referans-metin", help="referans kaydın metni (yoksa Whisper ile çıkarılır)")
    p.add_argument("--rizali", action="store_true", help="referans ses benim sesim ya da sahibinin açık rızası var")
    p.add_argument("--duraklama", type=float, default=0.35, help="cümleler arası sessizlik, sn (paragrafta 2 katı)")
    p.add_argument("--hiz", type=float, default=1.0, help="konuşma hızı çarpanı (0,8–1,2; perde korunur)")
    p.add_argument("--deneme", type=int, default=2, help="kapıdan kalan cümle için yeniden üretim hakkı")
    p.add_argument("--dogrulamasiz", action="store_true", help="Whisper/ECAPA doğrulamasını atla (hızlı taslak)")
    p.add_argument("--kip", choices=["klon", "devam"], default="devam",
                   help="klonlama kipi: klon (yalnız kimlik sesi) ya da devam (kimliğin metniyle birlikte)")
    p.set_defaults(islev=calistir_)
