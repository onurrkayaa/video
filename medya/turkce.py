"""Türkçe'ye duyarlı metin karşılaştırma: normalleştirme, CER/WER — dış ses (TTS) kabulü ve anlaşılırlık ölçümü.

Yalnız standart kitaplık + numpy: hem .venv'de (medya) hem ortamlar/ses işçilerinde içe aktarılır.
Normalleştirme (iki tarafa da): İ→i, I→ı, sonra küçük harf (Python lower() 'İ'yi 'i̇' yapar → sahte hata);
â/î/û → a/i/u; rakamlar Türkçe sözcüğe (Whisper "dokuzda"yı "9'da" yazar → "dokuzda"; %50 → "yüzde elli";
1.500 → "bin beş yüz"; 3,5 → "üç virgül beş"; 10:30 → "on otuz"); kesme işareti silinir; noktalama boşluk olur.
"""
from __future__ import annotations

import re
import unicodedata

import numpy as np

BIRLER = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
ONLAR = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
BUYUK = [(10 ** 12, "trilyon"), (10 ** 9, "milyar"), (10 ** 6, "milyon"), (10 ** 3, "bin")]
SAYI = re.compile(r"(%\s*)?(\d{1,3}(?:\.\d{3})+(?!\d)|\d+)(?:([,:])(\d+))?(?:['’ʼ]([a-zçğıöşü]+))?")


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


def karsilastir(basvuru: str, deneme: str) -> dict:
    """Normalleştirilmiş CER ve WER (+ kelime işlemleri). Başvuru boşsa CER/WER 1 sayılır."""
    rw, hw = normallestir(basvuru).split(), normallestir(deneme).split()
    ref, hyp = " ".join(rw), " ".join(hw)
    if not rw:
        return {"cer": 1.0, "wer": 1.0, "kelime_islemleri": {"mesafe": len(hw), "degisen": [], "dusen": [], "eklenen": hw}}
    ops = islemler(rw, hw)
    return {"cer": round(mesafe(ref, hyp) / len(ref), 4), "wer": round(ops["mesafe"] / len(rw), 4), "kelime_islemleri": ops}
