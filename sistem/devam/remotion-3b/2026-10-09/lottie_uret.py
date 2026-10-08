"""Şablonun Lottie örneği: 512x512, 30 fps, 60 kare. Halka (trim path ile çizilir, döner) + ortada yaylanan nokta.
Elle/kodla yazıldı (2026-10-09): üçüncü taraf içerik yok, lisans sorunu yok. Çıktı: argv[1]."""
import json
import sys


def sabit(v):
    return {"a": 0, "k": v}


def anahtar(kareler):
    """[(kare, değer listesi, (ox, oy, ix, iy) ya da None)] → Lottie anahtar kare dizisi (son kare eğrisiz)."""
    k = []
    for t, s, egri in kareler:
        a = {"t": t, "s": s}
        if egri:
            ox, oy, ix, iy = egri
            n = len(s)
            a["o"] = {"x": [ox] * n, "y": [oy] * n}
            a["i"] = {"x": [ix] * n, "y": [iy] * n}
        k.append(a)
    return {"a": 1, "k": k}


def donusum():
    return {"ty": "tr", "nm": "donusum", "p": sabit([0, 0]), "a": sabit([0, 0]), "s": sabit([100, 100]),
            "r": sabit(0), "o": sabit(100), "sk": sabit(0), "sa": sabit(0)}


def katman(ind, ad, ks, ogeler):
    return {"ddd": 0, "ind": ind, "ty": 4, "nm": ad, "sr": 1, "ks": ks, "ao": 0,
            "shapes": [{"ty": "gr", "nm": ad, "it": ogeler + [donusum()]}],
            "ip": 0, "op": 60, "st": 0, "bm": 0}


def ks(r=None, s=None):
    return {"o": sabit(100), "r": r or sabit(0), "p": sabit([256, 256, 0]), "a": sabit([0, 0, 0]),
            "s": s or sabit([100, 100, 100])}


YUMUSAK = (0.6, 0, 0.2, 1)        # yavaş başlar, yumuşak oturur
halka = katman(2, "halka", ks(r=anahtar([(0, [0], (0.4, 0, 0.3, 1)), (60, [180], None)])), [
    {"ty": "el", "nm": "elips", "d": 1, "p": sabit([0, 0]), "s": sabit([320, 320])},
    {"ty": "tm", "nm": "kirp", "s": sabit(0), "e": anahtar([(0, [0], YUMUSAK), (36, [100], None)]), "o": sabit(0),
     "m": 1},
    {"ty": "st", "nm": "cizgi", "c": sabit([0.424, 0.773, 0.553, 1]), "o": sabit(100), "w": sabit(28), "lc": 2,
     "lj": 2, "bm": 0},
])
nokta = katman(1, "nokta", ks(s=anahtar([(20, [0, 0, 100], (0.5, 0, 0.3, 1)),
                                          (32, [115, 115, 100], (0.6, 0, 0.4, 1)),
                                          (42, [100, 100, 100], None)])), [
    {"ty": "el", "nm": "elips", "d": 1, "p": sabit([0, 0]), "s": sabit([120, 120])},
    {"ty": "fl", "nm": "dolgu", "c": sabit([0.949, 0.42, 0.357, 1]), "o": sabit(100), "r": 1, "bm": 0},
])
belge = {"v": "5.12.2", "fr": 30, "ip": 0, "op": 60, "w": 512, "h": 512, "nm": "ornek", "ddd": 0, "assets": [],
         "layers": [nokta, halka], "markers": []}
open(sys.argv[1], "w").write(json.dumps(belge, ensure_ascii=False, separators=(",", ":")) + "\n")
