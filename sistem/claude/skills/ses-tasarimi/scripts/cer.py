"""Türkçe'ye duyarlı CER/WER + Whisper güveni — dış ses (TTS) kabulü, temizlik ve 'müzik altında anlaşılırlık'.

  PY=$MEDYA/ortamlar/ses/bin/python; B=$MEDYA/sistem/claude/skills/ses-tasarimi/scripts
  # dış ses: onaylı metin ↔ alınan sesin dökümü (medya yaziya-dok vo-1.wav --dil tr --cikti analiz/vo-1-yazi.json)
  $PY $B/cer.py --metin plan/dis-ses.txt --yazi analiz/vo-1-yazi.json --kapi tts --json analiz/vo-1-cer.json
  # temizlik: temizlenmemiş dökümü ↔ temizlenmiş döküm
  $PY $B/cer.py --metin analiz/konusma-ham-yazi.json --yazi analiz/konusma-yazi.json --kapi temizlik
  # miks: yalnız konuşma katmanının dökümü ↔ son videonun dökümü [--dogru plan/metin.txt: doğru metin biliniyorsa]
  $PY $B/cer.py --metin analiz/konusma-yazi.json --yazi analiz/final-yazi.json --kapi miks

--metin (başvuru) ve --yazi (denenen): medya yaziya-dok JSON'u, .txt dosyası ya da metnin kendisi.
Normalleştirme (iki tarafa da): İ→i, I→ı, sonra küçük harf (Python lower() 'İ'yi 'i̇' yapar → sahte hata);
â/î/û → a/i/u; rakamlar Türkçe sözcüğe (Whisper "dokuzda"yı "9'da" yazar → "dokuzda"; %50 → "yüzde elli";
1.500 → "bin beş yüz"; 3,5 → "üç virgül beş"; 10:30 → "on otuz"); kesme işareti silinir; noktalama boşluk olur.
Değişen/eklenen kelimeler --yazi JSON'undaki zamanlarıyla yazılır: kullanıcıya dinletilecek anlar.
Kapılar:
  tts       --metin = onaylı metin: CER ≤ %3, WER ≤ %8, eklenen/düşen kelime yok, 10–18 karakter/sn (araştırma 2026-10-05)
  temizlik, miks  iki döküm karşılaştırılır (doğru metin çoğu zaman yoktur): düşük güvenli (<0,5) kelime artmaz ve
            ortalama olasılık en çok 0,02 düşer. Mühendislik eşiği, fikstürde sınandı: kahverengi gürültüde sınırsız
            bastırma 0 → 2 düşük güvenli kelime, ortalama 0,951 → 0,847; 12 dB sınır 0 → 0, 0,951 → 0,959. İki döküm
            arasındaki WER kapı değildir: Whisper temiz kayıtta da kelime oynatır (fikstürde "kaydıdır"/"kaygıdır").
            --dogru verilirse araştırma kapısı da eklenir: WER(yazi) ≤ WER(metin) + 0,02 (doğru metne göre).
Çıkış kodu: 0 geçti (ya da kapı yok), 1 kaldı, 2 kullanım hatası.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np

BIRLER = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
ONLAR = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
BUYUK = [(10 ** 12, "trilyon"), (10 ** 9, "milyar"), (10 ** 6, "milyon"), (10 ** 3, "bin")]
SAYI = re.compile(r"(%\s*)?(\d{1,3}(?:\.\d{3})+(?!\d)|\d+)(?:([,:])(\d+))?(?:['’ʼ]([a-zçğıöşü]+))?")
DUSUK = 0.5


def hata(mesaj: str):
    print(f"HATA: {mesaj}", file=sys.stderr)
    raise SystemExit(2)


def _yuzler(n: int) -> list[str]:
    y, r = divmod(n, 100)
    o, b = divmod(r, 10)
    s = ([BIRLER[y]] if y > 1 else []) + (["yüz"] if y else [])
    return s + ([ONLAR[o]] if o else []) + ([BIRLER[b]] if b else [])


def sayi_yaziya(n: int) -> str:
    if n == 0:
        return "sıfır"
    if n >= 10 ** 15:
        return str(n)
    s = []
    for deger, ad in BUYUK:
        q, n = divmod(n, deger)
        if q:
            s += ([] if (q == 1 and ad == "bin") else _yuzler(q)) + [ad]
    return " ".join(s + _yuzler(n))


def _sayi_degistir(m: re.Match) -> str:
    yuzde, ana, ayrac, kesir, ek = m.groups()
    s = sayi_yaziya(int(ana.replace(".", "")))
    if ayrac == ",":
        s += " virgül " + sayi_yaziya(int(kesir))
    elif ayrac == ":":
        s += " " + sayi_yaziya(int(kesir))
    if yuzde:
        s = "yüzde " + s
    return " " + s + (ek or "") + " "


def normallestir(metin: str) -> str:
    s = unicodedata.normalize("NFC", metin).replace("İ", "i").replace("I", "ı").lower()
    s = s.replace("̇", "").translate(str.maketrans("âîû", "aiu"))
    s = SAYI.sub(_sayi_degistir, s)
    s = re.sub(r"['’ʼ`´]", "", s)
    s = re.sub(r"[^\w\s]|_", " ", s)
    return " ".join(s.split())


def oku(arg: str) -> tuple[str, list[dict] | None]:
    """→ (metin, kelimeler|None). JSON: medya yaziya-dok çıktısı; .txt; yoksa metnin kendisi."""
    p = Path(arg)
    if p.suffix.lower() in (".json", ".txt") or p.exists():
        if not p.exists():
            hata(f"dosya yok: {arg}")
        if p.suffix.lower() == ".json":
            v = json.loads(p.read_text(encoding="utf-8"))
            return str(v.get("metin", "")), v.get("kelimeler")
        return p.read_text(encoding="utf-8"), None
    return arg, None


def jetonlar(metin: str, kelimeler: list[dict] | None) -> tuple[list[str], list[tuple[float, float]] | None]:
    """Normalleştirilmiş kelimeler; Whisper kelimeleri varsa her jetona kendi zamanı."""
    if not kelimeler:
        return normallestir(metin).split(), None
    tok, zaman = [], []
    for w in kelimeler:
        for t in normallestir(str(w["k"])).split():
            tok.append(t)
            zaman.append((float(w["bas"]), float(w["son"])))
    return tok, zaman


def _satir(onceki: np.ndarray, a_i: int, b: np.ndarray, i: int) -> np.ndarray:
    """Levenshtein DP'nin bir satırı, numpy ile (ekleme zinciri birikimli en küçükle çözülür)."""
    j = np.arange(len(b) + 1)
    kismi = np.empty(len(b) + 1, dtype=np.int64)
    kismi[0] = i
    kismi[1:] = np.minimum(onceki[:-1] + (b != a_i), onceki[1:] + 1)
    return np.minimum.accumulate(kismi - j) + j


def _kodla(a, b):
    sozluk: dict = {}
    return (np.array([sozluk.setdefault(t, len(sozluk)) for t in a], dtype=np.int64),
            np.array([sozluk.setdefault(t, len(sozluk)) for t in b], dtype=np.int64))


def mesafe(a, b) -> int:
    if not a or not b:
        return max(len(a), len(b))
    A, B = _kodla(a, b)
    d = np.arange(len(B) + 1)
    for i in range(1, len(A) + 1):
        d = _satir(d, A[i - 1], B, i)
    return int(d[-1])


def islemler(a: list[str], b: list[str], za=None, zb=None) -> dict:
    """Kelime düzeyi: değişen / düşen (başvuruda var, denemede yok) / eklenen; zaman varsa 'sn' alanıyla."""
    A, B = _kodla(a, b)
    D = np.zeros((len(A) + 1, len(B) + 1), dtype=np.int64)
    D[0] = np.arange(len(B) + 1)
    for i in range(1, len(A) + 1):
        D[i] = _satir(D[i - 1], A[i - 1], B, i)
    i, j, deg, dus, ekl = len(A), len(B), [], [], []
    sn = lambda z, k: None if z is None else round(z[k][0], 2)
    while i > 0 or j > 0:
        if i > 0 and j > 0 and D[i, j] == D[i - 1, j - 1] + (A[i - 1] != B[j - 1]):
            if A[i - 1] != B[j - 1]:
                deg.append({"once": a[i - 1], "sonra": b[j - 1], "sn": sn(zb, j - 1)})
            i, j = i - 1, j - 1
        elif i > 0 and D[i, j] == D[i - 1, j] + 1:
            dus.append({"kelime": a[i - 1], "sn": sn(za, i - 1)})
            i -= 1
        else:
            ekl.append({"kelime": b[j - 1], "sn": sn(zb, j - 1)})
            j -= 1
    return {"mesafe": int(D[-1, -1]), "degisen": deg[::-1], "dusen": dus[::-1], "eklenen": ekl[::-1]}


def guven(kelimeler: list[dict] | None) -> dict | None:
    if not kelimeler:
        return None
    o = [float(w.get("olasilik", 0.0)) for w in kelimeler]
    return {"dusuk_guvenli": int(sum(x < DUSUK for x in o)), "ortalama_olasilik": round(float(np.mean(o)), 3)}


def _yaz(x: dict) -> str:
    z = f" @{x['sn']:.2f} sn" if x.get("sn") is not None else ""
    return (f"{x['once']} → {x['sonra']}" if "once" in x else x["kelime"]) + z


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--metin", required=True, help="başvuru: yaziya-dok JSON, .txt ya da metin")
    p.add_argument("--yazi", required=True, help="denenen: yaziya-dok JSON, .txt ya da metin")
    p.add_argument("--kapi", choices=["tts", "miks", "temizlik"], help="uygulanacak kabul kapısı")
    p.add_argument("--dogru", help="miks/temizlik: doğru metin biliniyorsa (.txt ya da metin) — araştırma kapısı eklenir")
    p.add_argument("--json")
    a = p.parse_args()
    ref_ham, ref_k = oku(a.metin)
    hyp_ham, hyp_k = oku(a.yazi)
    rw, rz = jetonlar(ref_ham, ref_k)
    hw, hz = jetonlar(hyp_ham, hyp_k)
    if not rw:
        hata("başvuru metni boş")
    ref, hyp = " ".join(rw), " ".join(hw)
    cer = mesafe(ref, hyp) / len(ref)
    ops = islemler(rw, hw, rz, hz)
    wer = ops["mesafe"] / len(rw)
    hiz = None
    if hyp_k:
        sure = float(hyp_k[-1]["son"]) - float(hyp_k[0]["bas"])
        hiz = len(ref) / sure if sure > 0 else None
    g_ref, g_hyp = guven(ref_k), guven(hyp_k)
    kosullar, dogru_wer = {}, None
    if a.kapi == "tts":
        kosullar = {"CER<=0.03": cer <= 0.03, "WER<=0.08": wer <= 0.08,
                    "eklenen_dusen_yok": not ops["eklenen"] and not ops["dusen"]}
        if hiz is not None:
            kosullar["10<=karakter_sn<=18"] = 10 <= hiz <= 18
    elif a.kapi in ("miks", "temizlik"):
        if not (g_ref and g_hyp):
            hata(f"{a.kapi} kapısı iki medya yaziya-dok JSON'u ister (kelime olasılıkları)")
        kosullar = {"dusuk_guvenli_artmadi": g_hyp["dusuk_guvenli"] <= g_ref["dusuk_guvenli"],
                    "ortalama_olasilik_dusus<=0.02": g_hyp["ortalama_olasilik"] >= g_ref["ortalama_olasilik"] - 0.02}
        if a.dogru:
            dw = normallestir(oku(a.dogru)[0]).split()
            wer_ref, wer_hyp = islemler(dw, rw)["mesafe"] / len(dw), islemler(dw, hw)["mesafe"] / len(dw)
            dogru_wer = {"basvuru": round(wer_ref, 4), "deneme": round(wer_hyp, 4)}
            kosullar["WER_dogruya_gore_en_cok_+0.02"] = wer_hyp <= wer_ref + 0.02
    gecti = all(kosullar.values()) if kosullar else True
    rapor = {"metin": a.metin, "yazi": a.yazi, "cer": round(cer, 4), "wer": round(wer, 4),
             "karakter_sn": None if hiz is None else round(hiz, 2), "guven": {"basvuru": g_ref, "deneme": g_hyp},
             "dogru_metne_gore_wer": dogru_wer, "kelime_islemleri": ops, "normal_basvuru": ref, "normal_deneme": hyp, "kapi": a.kapi,
             "kosullar": kosullar, "gecti": gecti}
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(rapor, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    isaret = "" if not a.kapi else ("✓ " if gecti else "✗ ")
    print(f"{isaret}CER %{100 * cer:.1f} · WER %{100 * wer:.1f} ({len(rw)} kelime)"
          + (f" · {hiz:.1f} karakter/sn" if hiz is not None else ""))
    if g_ref and g_hyp:
        print(f"  düşük güvenli kelime {g_ref['dusuk_guvenli']} → {g_hyp['dusuk_guvenli']}, ortalama olasılık "
              f"{g_ref['ortalama_olasilik']:.3f} → {g_hyp['ortalama_olasilik']:.3f}")
    elif g_hyp:
        print(f"  düşük güvenli kelime {g_hyp['dusuk_guvenli']}, ortalama olasılık {g_hyp['ortalama_olasilik']:.3f}")
    if dogru_wer:
        print(f"  doğru metne göre WER: başvuru %{100 * dogru_wer['basvuru']:.1f} → deneme %{100 * dogru_wer['deneme']:.1f}")
    for ad in ("degisen", "dusen", "eklenen"):
        if ops[ad]:
            print(f"  {ad}: {', '.join(_yaz(x) for x in ops[ad][:12])}{' …' if len(ops[ad]) > 12 else ''}")
    for k, v in kosullar.items():
        if not v:
            print(f"  ✗ {k}")
    if a.json:
        print(f"→ {a.json}")
    return 0 if gecti else 1


if __name__ == "__main__":
    raise SystemExit(main())
