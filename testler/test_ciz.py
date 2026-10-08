"""`medya ciz` doğruluk sınamaları: planı HyperFrames'siz, doğrudan ffmpeg ile çizen yetenek.

Çalıştır: source ortam.sh && medya test ciz
Ölçütler (O6, 2026-10-08): kare kodlu sınama projesinde (testler/nle_sinama.py) görüntü 0 kare (her karede beklenen
kaynak karesi, 24 fps kaynak dahil), erime ağırlık rampasından plan uzunluğunda ve ortası kesimde; ses en çok yarım kare
(müzik çapraz ilintiyle ≤ 1 ms). Ken Burns/punch alt piksel: konum hatası ≤ 0,05 px (CRF 1'de ölçülen ≤ 0,02),
artığın ikinci farkı p95 ≤ 0,1 px (zoompan 0,94 px titrerdi — doğrulama ölçümü). Kapsam dışı öğe sessizce kesime dönmez, hata verir.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))
sys.path.insert(0, str(KOK / "testler"))
FF = str(KOK / "arac" / "ffmpeg")


@pytest.fixture(scope="module")
def sinama(tmp_path_factory):
    """Kare kodlu sınama projesi (A/B 30, C 60, D 24 fps; 12 karelik erime; B'nin kendi sesi; müzik bas 0,5)."""
    p = tmp_path_factory.mktemp("ciz") / "sinama"
    subprocess.run([sys.executable, str(KOK / "testler" / "nle_sinama.py"), str(p)], check=True, capture_output=True)
    return p


def test_ciz_kare_kodlu_plan_kare_kesin_ses_yarim_kare(sinama):
    """Kesim 0 kare, kaynak karesi her karede tam (zamanı ≤ t olan son kare; Resolve 24 fps'te 24 kareyi 1 erken
    veriyordu), erime 12 kare ve ortası kesimde, erimeden sonraki kesim kaymıyor (elle kurulan concat → xfade → concat
    zinciri +1 kare kaydırmıştı — gelistirme.md), ses yarım kareden az."""
    from medya.cli import ana
    from nle_olc import goruntu_olc, ses_olc
    cikti = sinama / "cikti" / "ciz.mp4"
    assert ana(["ciz", str(sinama / "plan" / "kurgu.json"), "--cikti", str(cikti)]) == 0
    g, s = goruntu_olc(sinama, cikti), ses_olc(sinama, cikti)
    assert not g["hatalar"] and not s["hatalar"], (g["hatalar"][:10], s["hatalar"])
    assert g["kare"] == 228
    assert {h: c["sapma"] for h, c in g["cekimler"].items()} == {"A": {"0": 60}, "B": {"0": 48}, "C": {"0": 48},
                                                                "D": {"0": 60}}
    assert [g["cekimler"][h]["ilk_kare"] for h in "ABD"] == [0, 60, 168]
    r = g["erimeler"][0]["rampa"]
    assert abs(r["kare"] - 12) <= 0.25 and abs(r["orta"] - r["kesim"]) <= 0.1, r
    yarim = 1000 / 30 / 2
    assert all(abs(o["sapma_ms"]) <= yarim for o in s["muzik"] + s["cekim_sesi"]), (s["muzik"], s["cekim_sesi"])
    assert abs(s["ses_hizasi"]["gecikme_ms"]) <= 1.0 and s["ses_hizasi"]["ilinti"] > 0.8, s["ses_hizasi"]
    assert [o["kaynak_sn"] for o in s["cekim_sesi"]] == [1, 2]


def _leke_kaynagi(yol: Path, W: int = 1280, H: int = 720) -> list[tuple[float, float]]:
    """Durağan Gauss lekeli kayıpsız kaynak (x264 qp 0): çıktıda leke kayarsa yalnız geometri kaydırmıştır."""
    lekeler = [(x, y) for x in (470.3, 640.6, 790.2, 905.8, 1020.4, 1180.7) for y in (150.4, 360.1, 560.7)]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    Y = np.full((H, W), 40, np.float32)
    for bx, by in lekeler:
        Y += 180 * np.exp(-((xx - bx) ** 2 + (yy - by) ** 2) / (2 * 4.0 ** 2))
    kare = np.concatenate([np.clip(np.rint(Y), 0, 255).astype(np.uint8).ravel(),
                           np.full(W * H // 2, 128, np.uint8)]).tobytes()
    subprocess.run([FF, "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}",
                    "-r", "30", "-i", "-", "-c:v", "libx264", "-qp", "0", "-preset", "veryfast", "-colorspace", "bt709",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv", str(yol)],
                   input=kare * 75, check=True)
    return lekeler


def _beklenen(Ws, Hs, Wc, Hc, ilgi, hareket, j, n):
    """Sözleşmeden (plan-semasi.md, kompozisyon.md): cover + object-position P = clamp((x·Wö − Wç/2)/(Wö − Wç)); ölçek
    çapası ilginin ekrandaki yeri (yoksa orta); kenburns olcek[0] ilk karede, olcek[1] son karede; punch `kare` karede."""
    from medya.komutlar.ciz import egri
    k = max(Wc / Ws, Hc / Hs)
    ww, wh = Wc / k, Hc / k
    ix, iy = ilgi or (0.5, 0.5)
    P = lambda i, S, C: min(1.0, max(0.0, (i * S * k - C / 2) / (S * k - C))) if S * k - C > 1e-9 else 0.5
    X0, Y0 = (Ws - ww) * P(ix, Ws, Wc), (Hs - wh) * P(iy, Hs, Hc)
    if not hareket:
        return X0, Y0, ww, wh
    ax, ay = ((ix * Ws - X0) / ww, (iy * Hs - Y0) / wh) if ilgi else (0.5, 0.5)
    a, b = hareket["olcek"]
    p = j / (n - 1) if hareket["tur"] == "kenburns" else (min(1.0, j / hareket["kare"]) if hareket.get("kare") else 1.0)
    z = a + (b - a) * egri(hareket.get("egri"), p)
    return X0 + ax * ww * (1 - 1 / z), Y0 + ay * wh * (1 - 1 / z), ww / z, wh / z


def test_ciz_kadraj_ve_ken_burns_alt_piksel(tmp_path):
    from medya.cli import ana
    kaynak = tmp_path / "leke.mp4"
    lekeler = _leke_kaynagi(kaynak)
    Wc, Hc, n = 360, 640, 60
    durumlar = {"sabit": ({"ilgi": [0.62, 0.5]}, None, 0.75),
                "kenburns": ({"ilgi": [0.62, 0.4]}, {"tur": "kenburns", "olcek": [1.0, 1.15]}, 0.05),
                "kenburns_sine": ({"ilgi": [0.62, 0.4]}, {"tur": "kenburns", "olcek": [1.0, 1.15], "egri": "sine.inOut"},
                                  0.05),
                "kenburns_kenarda": ({"ilgi": [0.92, 0.3]}, {"tur": "kenburns", "olcek": [1.05, 1.0]}, 0.05),
                "punch": (None, {"tur": "punch", "olcek": [1.0, 1.2], "kare": 4, "egri": "expo.out"}, 0.05)}
    for ad, (kadraj, hareket, sinir) in durumlar.items():
        c = {"no": 1, "kaynak": str(kaynak), "kaynak_bas": 0.0, "cikti_bas": 0, "cikti_son": n / 30, "hiz": 1,
             "ses": "sessiz", "vurusa": False, "gecis": {"tur": "kesim", "sure_kare": 0}}
        if kadraj:
            c["kadraj"] = kadraj
        if hareket:
            c["hareket"] = hareket
        plan = tmp_path / f"{ad}.json"
        plan.write_text(json.dumps({"fps": 30, "boyut": [Wc, Hc], "cekimler": [c]}))
        cikti = tmp_path / f"{ad}.mp4"
        assert ana(["ciz", str(plan), "--cikti", str(cikti), "--kok", str(tmp_path), "--crf", "1"]) == 0
        b = subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(cikti), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                           capture_output=True, check=True).stdout
        kareler = np.frombuffer(b, np.uint8).reshape(-1, Hc, Wc).astype(np.float64)
        assert len(kareler) == n
        artik = np.full((n, len(lekeler), 2), np.nan)
        for j, im in enumerate(kareler):
            L, T, Rw, Rh = _beklenen(1280, 720, Wc, Hc, (kadraj or {}).get("ilgi"), hareket, j, n)
            for i, (bx, by) in enumerate(lekeler):
                ex, ey = (bx + 0.5 - L) / Rw * Wc - 0.5, (by + 0.5 - T) / Rh * Hc - 0.5   # piksel merkezi kuralı
                if not (10 < ex < Wc - 10 and 10 < ey < Hc - 10):
                    continue
                x0, y0 = int(round(ex)) - 8, int(round(ey)) - 8
                p = im[y0:y0 + 17, x0:x0 + 17]
                w = np.clip(p - np.median(p) - 3, 0, None)
                yy, xx = np.mgrid[0:17, 0:17]
                artik[j, i] = ((w * xx).sum() / w.sum() + x0 - ex, (w * yy).sum() / w.sum() + y0 - ey)
        assert np.sum(~np.isnan(artik[..., 0])) >= n * 4, ad
        assert np.nanmax(np.abs(artik)) <= sinir, (ad, float(np.nanmax(np.abs(artik))))
        ikinci = np.abs(np.diff(artik, n=2, axis=0)).ravel()
        assert np.percentile(ikinci[~np.isnan(ikinci)], 95) <= 0.1, (ad, "titreme")


def test_ciz_egriler_gsap_ve_ffmpeg_ifadesi_ayni():
    """Eğriler GSAP 3 formülleriyle (gsap-core _insertEase) aynı; perspective'e giden ffmpeg ifadesi Python'la aynı sayıyı
    verir (aevalsrc ile hesaplatılır)."""
    from medya.komutlar.ciz import egri, egri_gecerli, egri_ifadesi
    bilinen = {("none", 0.3): 0.3, ("sine.inOut", 0.25): (1 - np.cos(np.pi / 4)) / 2, ("expo.out", 0.3): 0.875,
               ("power2.inOut", 0.7): 1 - 0.6 ** 3 / 2, ("power1", 0.25): 0.4375, ("sine.in", 1.0): 1.0,
               ("expo.in", 0.0): 0.0, ("circ.out", 0.5): np.sqrt(0.75)}
    for (ad, p), v in bilinen.items():
        assert abs(egri(ad, p) - v) < 1e-12, (ad, p)
    assert not egri_gecerli("bounce.out") and not egri_gecerli("elastic") and not egri_gecerli(3)
    for ad in ("none", "sine.inOut", "sine.out", "expo.out", "expo.inOut", "power2.inOut", "power3.in", "circ.inOut"):
        r = subprocess.run([FF, "-nostdin", "-v", "error", "-f", "lavfi", "-i",
                            f"aevalsrc=exprs='{egri_ifadesi(ad, 't')}':s=100:d=1.005", "-f", "f64le", "-"],
                           capture_output=True, check=True)
        x = np.frombuffer(r.stdout, "<f8")
        assert len(x) >= 101, ad
        assert max(abs(x[k] - egri(ad, k / 100)) for k in range(101)) < 1e-9, ad


def test_ciz_kapsam_disi_sessizce_cevirmez(tmp_path, capsys):
    from medya.cli import ana
    kaynak = tmp_path / "leke.mp4"
    _leke_kaynagi(kaynak, 320, 180)
    c = lambda no, b, s, **k: dict({"no": no, "kaynak": str(kaynak), "kaynak_bas": 0.0, "cikti_bas": b, "cikti_son": s,
                                    "hiz": 1, "ses": "sessiz", "vurusa": False,
                                    "gecis": {"tur": "kesim", "sure_kare": 0}}, **k)
    plan = {"fps": 30, "boyut": [180, 320], "cekimler": [
        c(1, 0, 0.5, gecis={"tur": "siyah-dip", "sure_kare": 12}),
        c(2, 0.5, 1.0, gecis={"tur": "savurma", "sure_kare": 8}, kadraj={"olcek": 1.2}),
        c(3, 1.0, 1.5, gecis={"tur": "j-kesim", "sure_kare": 6}, hareket={"tur": "paralaks", "olcek": [1.0, 1.05]}),
        c(4, 1.5, 2.0, kadraj={"mod": "takip"}, hareket={"tur": "kenburns", "olcek": [1.0, 1.1], "egri": "bounce"}),
        c(5, 2.0, 2.5, hiz=0.5)]}
    (tmp_path / "plan.json").write_text(json.dumps(plan))
    cikti = tmp_path / "x.mp4"
    assert ana(["ciz", str(tmp_path / "plan.json"), "--cikti", str(cikti), "--kok", str(tmp_path)]) == 1
    hata = capsys.readouterr().err
    for parca in ("'siyah-dip'", "'savurma'", "kadraj.olcek", "'j-kesim'", "'paralaks'", "kadraj.mod 'takip'",
                  "'bounce'", "hiz 0.5", "HyperFrames"):
        assert parca in hata, (parca, hata)
    assert not cikti.exists()
    duz = dict(plan, cekimler=[c(1, 0, 1.0)])                       # çizilebilir plan; çıktı varsa üzerine yazılmaz
    (tmp_path / "duz.json").write_text(json.dumps(duz))
    cikti.write_bytes(b"kullanicinin")
    assert ana(["ciz", str(tmp_path / "duz.json"), "--cikti", str(cikti), "--kok", str(tmp_path)]) == 1
    assert cikti.read_bytes() == b"kullanicinin" and "üzerine yazılmaz" in capsys.readouterr().err


def test_ciz_dikey_teslim_uygunlugu(tmp_path, sinama):
    """1080x1920 çıktı teslim kapısından geçer: H.264 High seviye ≤ 4.2 (HyperFrames delivery 5.0 verip kalmıştı),
    bt709 etiketleri, faststart, AAC LC 48 kHz stereo, A/V başlangıcı aynı, üst veri yok."""
    from medya.cli import ana
    kaynak = tmp_path / "leke.mp4"
    _leke_kaynagi(kaynak)
    k = lambda no, b, s, kb, **x: dict({"no": no, "kaynak": str(kaynak), "kaynak_bas": kb, "cikti_bas": b,
                                        "cikti_son": s, "hiz": 1, "ses": "muzik", "vurusa": False,
                                        "gecis": {"tur": "kesim", "sure_kare": 0}}, **x)
    plan = {"fps": 30, "boyut": [1080, 1920], "muzik": {"dosya": str(sinama / "kaynak" / "muzik.wav"), "bas": 0},
            "cekimler": [k(1, 0, 1.5, 0.0, kadraj={"ilgi": [0.3, 0.5]}),
                         k(2, 1.1, 2.5, 0.5, gecis={"tur": "erime", "sure_kare": 12}, kadraj={"ilgi": [0.7, 0.5]},
                           hareket={"tur": "kenburns", "olcek": [1.0, 1.1]})]}
    (tmp_path / "plan.json").write_text(json.dumps(plan))
    cikti = tmp_path / "dikey.mp4"
    assert ana(["ciz", str(tmp_path / "plan.json"), "--cikti", str(cikti), "--kok", str(tmp_path)]) == 0
    r = subprocess.run([sys.executable, str(KOK / "sistem/claude/skills/teslim-denetimi/scripts/teslim.py"), "uygunluk",
                        str(cikti), "--hedef", "dikey", "--json", str(tmp_path / "u.json")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:]
    d = {b["ad"]: b["durum"] for b in json.loads((tmp_path / "u.json").read_text())["denetimler"]}
    assert all(d[a] == "gecti" for a in ("seviye", "renk", "faststart", "ses_bicimi", "av_baslangic", "ust_veri")), d


def _ton_tepesi(x: np.ndarray, t: float, hz: float, sr: int = 48000) -> float:
    from nle_olc import _zarf
    parca = x[int((t - 0.01) * sr):int((t + 0.04) * sr)]
    return float(_zarf(parca, hz)[1].max())


def test_ciz_konusma_katmani_kisma_ve_miks(tmp_path, sinama):
    """Kısma yolu (ciz kendi kısma mantığını yazmaz): --yalniz-konusma → ses-tasarimi kisma.py → kısılmış WAV
    muzik.dosya olur → ciz. Müzik tonları konuşma aralığında ≈ −12 dB, dışında değişmez; çekim sesi yerinde."""
    from medya.cli import ana
    from medya.ortak import ses_oku
    py = KOK / "ortamlar" / "ses" / "bin" / "python"
    if not py.exists():
        pytest.skip("ses ortamı yok (kisma.py): medya kur ses-ortami")
    plan = json.loads((sinama / "plan" / "kurgu.json").read_text())
    plan["muzik"]["bas"] = 0                                        # önerilen tek saat (plan-semasi: muzik.bas 0)
    p0 = sinama / "plan" / "kisma-oncesi.json"
    p0.write_text(json.dumps(plan))
    konusma = tmp_path / "konusma.wav"
    assert ana(["ciz", str(p0), "--yalniz-konusma", str(konusma)]) == 0
    k, sr = ses_oku(konusma, sr=48000, kanal=1)
    assert abs(len(k) / sr - 7.6) < 1e-6
    disari = np.concatenate([k[:int(1.999 * sr)], k[int(4.001 * sr):]])
    assert np.abs(disari).max() < 1e-6 and np.abs(k[int(2 * sr):int(4 * sr)]).max() > 0.1   # yalnız B, 2,0–4,0 sn
    (tmp_path / "aralik.json").write_text("[[2.0, 4.0]]")
    kisik = tmp_path / "muzik-kisik.wav"
    subprocess.run([str(py), str(KOK / "sistem/claude/skills/ses-tasarimi/scripts/kisma.py"), "--yatak",
                    str(sinama / "kaynak" / "muzik.wav"), "--konusma", str(konusma), "--araliklar",
                    str(tmp_path / "aralik.json"), "--bas", "0", "--cikti", str(kisik)], capture_output=True)
    assert kisik.exists()
    plan["muzik"]["dosya"] = str(kisik)
    p1 = sinama / "plan" / "kisma-sonrasi.json"
    p1.write_text(json.dumps(plan))
    cikti = tmp_path / "kisik.mp4"
    assert ana(["ciz", str(p1), "--cikti", str(cikti)]) == 0
    x, _ = ses_oku(cikti, sr=48000, kanal=1)
    ton = lambda kk: _ton_tepesi(x.astype(np.float64), kk * 0.5, 1500 + 100 * kk)    # k. ton videoda k·0,5 sn'de
    dis = [ton(kk) for kk in (1, 2, 3, 10, 11, 12)]
    ic = [ton(kk) for kk in (4, 5, 6, 7)]                           # 2,0–3,5 sn: tam kısılmış bölge
    fark = 20 * np.log10(np.mean(ic) / np.mean(dis))
    assert abs(fark + 12) < 1.5 and max(dis) / min(dis) < 1.2, (fark, dis, ic)
    from nle_olc import ses_olc
    s = ses_olc(_proje_kopya(sinama, plan, tmp_path), cikti)
    assert [o["kaynak_sn"] for o in s["cekim_sesi"]] == [1, 2] and all(abs(o["sapma_ms"]) <= 1000 / 60
                                                                       for o in s["cekim_sesi"])


def _proje_kopya(sinama: Path, plan: dict, hedef: Path) -> Path:
    """nle_olc planı proje/plan/kurgu.json'dan okur: kısma sonrası planla ölçmek için yalnız planın kopyası."""
    p = hedef / "proje"
    (p / "plan").mkdir(parents=True, exist_ok=True)
    (p / "plan" / "kurgu.json").write_text(json.dumps(plan))
    if not (p / "kaynak").exists():
        os.symlink(sinama / "kaynak", p / "kaynak")
    return p


def test_plan_denetle_egri_adini_denetler(tmp_path):
    """plan_denetle tanınmayan gecis.egri / hareket.egri için ✗ verir (iki motor aynı eğriyi çizmeli)."""
    import importlib.util
    yol = KOK / "sistem/claude/skills/kurgu-zanaati/scripts/plan_denetle.py"
    spec = importlib.util.spec_from_file_location("plan_denetle", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    c = {"no": 1, "kaynak": "kaynak/a.mp4", "kaynak_bas": 0, "cikti_bas": 0, "cikti_son": 2, "hiz": 1, "ses": "muzik",
         "vurusa": False, "gecis": {"tur": "kesim", "sure_kare": 0}}
    iyi = {"fps": 30, "boyut": [1080, 1920], "cekimler": [
        dict(c), dict(c, no=2, cikti_bas=1.6, cikti_son=4, gecis={"tur": "erime", "sure_kare": 12, "egri": "sine.inOut"},
                      hareket={"tur": "kenburns", "olcek": [1.0, 1.05], "egri": "none"})]}
    R = m.Rapor()
    assert m.sema(iyi, R) and not R.hatalar
    kotu = json.loads(json.dumps(iyi))
    kotu["cekimler"][1]["gecis"]["egri"] = "bounce.out"
    kotu["cekimler"][1]["hareket"]["egri"] = "Sine.InOut"
    R = m.Rapor()
    assert not m.sema(kotu, R) and sum("egri" in h for h in R.hatalar) == 2, R.hatalar


def test_ciz_hiz_klip_ve_donuk_kaynak(tmp_path, sinama):
    """Pişmemiş hızlandırma (hiz 2 → her 2. kaynak karesi), klip/klip_bas (görüntü klipten, `ses: kendi` asıl kaynaktan:
    medya nle ve denetle --plan gibi) ve 90° döndürülmüş kaynak (kadraj görünen boyutta: 1280x720 → döndürülünce
    720x1280, kırpma yok; kareler ffmpeg'in döndürdüğüyle aynı)."""
    from medya.cli import ana
    from nle_olc import _zarf
    from nle_sinama import kod_oku
    from medya.ortak import ses_oku
    k = sinama / "kaynak"
    c = lambda no, b, s, **x: dict({"no": no, "cikti_bas": b, "cikti_son": s, "hiz": 1, "ses": "sessiz", "vurusa": False,
                                    "gecis": {"tur": "kesim", "sure_kare": 0}}, **x)
    plan = {"fps": 30, "boyut": [1280, 720], "cekimler": [
        c(1, 0, 1.0, kaynak=str(k / "A.mov"), kaynak_bas=0.5, hiz=2),
        c(2, 1.0, 2.0, kaynak=str(k / "B.mov"), kaynak_bas=1.0, klip=str(k / "D.mov"), klip_bas=0.25, ses="kendi")]}
    (tmp_path / "p.json").write_text(json.dumps(plan))
    cikti = tmp_path / "hk.mp4"
    assert ana(["ciz", str(tmp_path / "p.json"), "--cikti", str(cikti), "--kok", str(tmp_path)]) == 0
    b = subprocess.run([FF, "-nostdin", "-v", "error", "-i", str(cikti), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, check=True).stdout
    kod = [kod_oku(x) for x in np.frombuffer(b, np.uint8).reshape(-1, 720, 1280, 3)]
    assert kod == [("A", 15 + 2 * j) for j in range(30)] + [("D", int((0.25 + j / 30) * 24 + 1e-9)) for j in range(30)]
    x, _ = ses_oku(cikti, sr=48000, kanal=1)
    tepe = lambda hz, a, s: float(_zarf(x[int(a * 48000):int(s * 48000)].astype(np.float64), hz, 0.04, 0.002, True)[1].max())
    # B'nin sesi var, D'nin (klibin) yok; eşik nle_olc'nin sızıntı eşiği 0,05 (660 Hz bip'lerin 550 Hz'e taşması ~0,04)
    assert tepe(660, 1.0, 2.0) > 0.1 and tepe(550, 1.0, 2.0) < 0.05 and tepe(660, 0.0, 0.95) < 0.05
    don = tmp_path / "A90.mov"
    subprocess.run([FF, "-nostdin", "-v", "error", "-display_rotation", "90", "-i", str(k / "A.mov"), "-c", "copy",
                    str(don)], check=True)
    plan = {"fps": 30, "boyut": [720, 1280], "cekimler": [c(1, 0, 0.5, kaynak=str(don), kaynak_bas=0.5)]}
    (tmp_path / "d.json").write_text(json.dumps(plan))
    cikti = tmp_path / "don.mp4"
    assert ana(["ciz", str(tmp_path / "d.json"), "--cikti", str(cikti), "--kok", str(tmp_path)]) == 0
    oku = lambda y, ek: np.frombuffer(subprocess.run([FF, "-nostdin", "-v", "error", *ek, "-i", str(y), "-frames:v", "15",
                                                      "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True,
                                                     check=True).stdout, np.uint8).reshape(-1, 1280, 720).astype(float)
    a, r = oku(cikti, []), oku(don, ["-ss", "0.5"])
    psnr = 10 * np.log10(255 ** 2 / np.mean((a - r) ** 2))
    assert a.shape == (15, 1280, 720) and psnr > 40, psnr
