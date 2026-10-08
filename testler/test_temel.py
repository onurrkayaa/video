"""Temel yeteneklerin doğruluk sınamaları — doğru cevabı bilinen sentetik medyayla (testler/uretec.py).

Çalıştır:  source ortam.sh && medya test   (ya da: .venv/bin/python -m pytest -q testler)
Her sınama, geçmişte yaşanmış ya da yaşanabilecek bir hatayı kilitler (ör. vuruş ızgarası kayması).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parent.parent
VERI = KOK / "testler" / "veri"
sys.path.insert(0, str(KOK))


@pytest.fixture(scope="session", autouse=True)
def veri():
    if not (VERI / "gercek.json").exists():
        subprocess.run([sys.executable, str(KOK / "testler" / "uretec.py")], check=True)
    return json.loads((VERI / "gercek.json").read_text())


@pytest.fixture
def agir():
    """Üretici modeller (FLUX.2 9–11 GB, Z-Image 6,3 GB, VoxCPM2 7–14 GB bellek): 16 GB'lık Mac'te takası GB'larca
    büyütür (2026-10-07'de 6 GB takas dosyası diski 1,4 GB'a düşürdü). Yalnız istenince: medya test --agir
    (MEDYA_AGIR_TEST=1)."""
    import os
    if os.environ.get("MEDYA_AGIR_TEST") != "1":
        pytest.skip("ağır üretici model sınaması: medya test --agir")


@pytest.fixture
def apple_ml():
    """Neural Engine derleyicisi takılıysa (sistem sorunu) Apple ML sınamalarını açık nedenle atla — asılmasınlar."""
    from medya.ortak import ane_tikanikligi
    neden = ane_tikanikligi()
    if neden:
        pytest.skip(neden)


def test_incele_hdr_vfr_gps():
    from medya.komutlar.incele import incele_dosya
    assert incele_dosya(VERI / "hdr_hlg.mp4")["video"]["hdr_turu"] == "HLG"
    assert any("VFR" in u for u in incele_dosya(VERI / "vfr.mp4")["uyarilar"])
    r = incele_dosya(VERI / "kusurlu.mp4")
    assert r["etiketler"]["konum_var"] and any("GPS" in u for u in r["uyarilar"])
    assert not incele_dosya(VERI / "kesimli.mp4")["video"]["hdr"]


def test_sahneler_bilinen_kesimler(veri):
    from medya.komutlar.sahneler import kesimleri_bul
    bulunan, _ = kesimleri_bul(str(VERI / "kesimli.mp4"))
    gercek = veri["kesimli"]["kesimler"]
    assert len(bulunan) == len(gercek)
    assert max(abs(a - b) for a, b in zip(bulunan, gercek)) <= 1 / 30 + 1e-6


def test_ses_turu_muzik_ve_karisik():
    from medya.komutlar.ses_turu import ses_turu
    assert ses_turu(str(VERI / "kesimli.mp4"))["karar"].startswith("yalniz-muzik")
    assert ses_turu(str(VERI / "karisik_ses.mp4"))["karar"] == "karisik"


def test_senkron_dogru_ve_kayik_izgara(veri):
    """Bugünkü hatanın kilidi: 200 ms kaymış ızgara 'kayik' denmeli, doğru ızgara 'vurusta'."""
    from medya.komutlar.senkron import senkron
    g = veri["muzik_davullu"]
    dogru = {"vuruslar": g["vuruslar"], "olcu_baslari": g["olcu_baslari"], "guven": 0.95}
    kayik = {"vuruslar": [t + 0.2 for t in g["vuruslar"]], "olcu_baslari": [], "guven": 0.95}
    assert senkron(str(VERI / "kesimli.mp4"), dogru)["karar"] == "vurusta"
    r = senkron(str(VERI / "kesimli.mp4"), kayik)
    assert r["karar"] == "kayik" and r["medyan_ms"] > 150
    dusuk = {**dogru, "guven": 0.3}
    assert senkron(str(VERI / "kesimli.mp4"), dusuk)["karar"] == "guvenilmez"


def test_denetle_kusurlari_bulur_temizi_gecirir():
    from medya.komutlar.denetle import denetle
    k = denetle(str(VERI / "kusurlu.mp4"))["denetimler"]
    assert not k["siyah"]["gecti"] and any(abs(a - 8.0) < 0.05 for a, _ in k["siyah"]["ic"])
    assert not k["flas"]["gecti"] and any(abs(t - 8.0) < 0.05 for t in k["flas"]["anlar"])
    assert len(k["ses"]["tik"]) == 1                      # yalnız gerçek tık; hi-hat sayılmaz
    assert not k["meta"]["gecti"]
    t = denetle(str(VERI / "kesimli.mp4"))["denetimler"]
    assert t["siyah"]["gecti"] and t["flas"]["gecti"] and t["meta"]["gecti"] and not t["ses"]["tik"]


def test_ustala_hedefe_getirir(tmp_path):
    from medya.komutlar.ustala import olc, ustala
    r = ustala(str(VERI / "kusurlu.mp4"), str(tmp_path / "u.mp4"), -16.0, -1.5)
    assert r["gecti"]
    o = olc(tmp_path / "u.mp4")
    assert abs(o["lufs"] + 16) <= 1.0 and o["tepe_dbtp"] <= -1.45
    from medya.ortak import ses_gecikmesi
    g = ses_gecikmesi(VERI / "kusurlu.mp4", tmp_path / "u.mp4")       # ustalık sesi kaydırmamalı (≤1 ms)
    assert abs(g["gecikme_ms"]) <= 1.0 and g["ilinti"] > 0.9, g


def test_donusturmeler(tmp_path):
    from medya.cli import ana
    from medya.komutlar.incele import incele_dosya
    assert ana(["sdr", str(VERI / "hdr_hlg.mp4"), "--cikti", str(tmp_path / "s.mp4")]) == 0
    assert not incele_dosya(tmp_path / "s.mp4")["video"]["hdr"]
    assert ana(["meta-temizle", str(VERI / "kusurlu.mp4"), "--cikti", str(tmp_path / "m.mp4")]) == 0
    assert not incele_dosya(tmp_path / "m.mp4")["etiketler"]["konum_var"]
    assert ana(["cfr", str(VERI / "vfr.mp4"), "--cikti", str(tmp_path / "c.mp4")]) == 0
    assert not any("VFR" in u for u in incele_dosya(tmp_path / "c.mp4")["uyarilar"])


def test_kayit_defteri_tutarli():
    from medya.kayit import yukle
    yetenekler, saglayicilar = yukle()
    assert "denetle" in yetenekler and "ffmpeg" in saglayicilar
    for s in saglayicilar.values():
        if s.tur == "bulut-ucretli":
            assert not s.etkin, f"{s.ad}: ücretli/bulut sağlayıcı varsayılan olarak kapalı olmalı"


# ------------------------------------------------------------------ müzik komitesi (ses ortamı gerekir, ~1 dk)
def _muzik(ad, tmp_path):
    from medya.komutlar.muzik import ana_wav, analiz
    if not (KOK / "ortamlar" / "ses" / "bin" / "python").exists():
        pytest.skip("ses ortamı kurulu değil")
    return analiz(ana_wav(str(VERI / f"{ad}.wav"), tmp_path / f"{ad}.wav"))


def _hata_ms(tahmin, gercek):
    import numpy as np
    t, g = np.asarray(tahmin), np.asarray(gercek)
    e = np.array([(t - r)[np.argmin(np.abs(t - r))] for r in g]) * 1000
    return e


@pytest.mark.parametrize("ad", ["muzik_net", "muzik_kayan"])
def test_muzik_net_ve_kayan_tempo_yuksek_guven(ad, veri, tmp_path):
    """Net ritim ve CANLI GİBİ KAYAN tempo: komite yüksek güven vermeli ve her vuruş ≤40 ms isabetli olmalı."""
    import numpy as np
    r = _muzik(ad, tmp_path)
    assert r["guven_seviye"] == "yuksek", r["komite"]["kosullar"]
    e = _hata_ms(r["vuruslar"], veri[ad]["vuruslar"])
    assert np.mean(np.abs(e) <= 40) >= 0.97 and np.percentile(np.abs(e), 90) <= 30


def test_muzik_belirsizse_yuksek_demez(veri, tmp_path):
    """Hi-hat tuzağı (metrik düzey belirsiz) ve davulsuz yumuşak parça: 'yuksek' denmemeli (dürüstlük)."""
    for ad in ["muzik_davullu", "muzik_yumusak"]:
        r = _muzik(ad, tmp_path)
        assert r["guven_seviye"] != "yuksek", ad


def test_sabit_izgara_kayan_tempoda_basarisiz(veri):
    """2026-10-04 hatasının türü: sabit BPM ızgarası kayan tempoda yüzlerce ms sapar."""
    import numpy as np
    g = np.asarray(veri["muzik_kayan"]["vuruslar"])
    izgara = g[0] + np.median(np.diff(g[:8])) * np.arange(len(g))
    assert np.max(np.abs(izgara - g)) > 0.5


# ------------------------------------------------------------------ yeni yetenekler (Apple çerçeveleri, Whisper, Demucs)
def _kareler(yol, w=640, h=360, on=""):
    """Videonun bütün karelerini gri ve küçültülmüş olarak doğrudan çözer (sıra = kare sırası); `on`: önce uygulanacak
    süzgeç (ör. başvuru kırpımı, virgülle biter). ffmpeg'in psnr süzgeci zaman damgası farklı akışlarda kare
    kaydırabildiği için kullanılmaz."""
    import subprocess
    import numpy as np
    from medya.ortak import ffmpeg
    r = subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-i", str(yol), "-vf",
                        f"{on}scale={w}:{h}:flags=area,format=gray",
                        "-fps_mode", "passthrough", "-f", "rawvideo", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, h, w).astype(float)


def _psnr(a, b):
    import numpy as np
    return float(10 * np.log10(255 ** 2 / max(np.mean((a - b) ** 2), 1e-9)))


def _apple_gerek():
    if not (KOK / "arac" / "medya-apple").exists():
        pytest.skip("arac/medya-apple derlenmemiş")


def test_yavaslat_apple_ara_kareler_kopyadan_iyi(tmp_path, apple_ml):
    """30 fps'ten 2x: her kare beklenen sırada; üretilen ara kareler gerçek 60 fps karelerine, önceki kareyi
    tekrar etmekten belirgin yakın olmalı."""
    _apple_gerek()
    import statistics as st
    from medya.komutlar.yavaslat import yavaslat
    r = yavaslat(str(VERI / "hareket30.mp4"), str(tmp_path / "y.mov"), 0.5, yontem="apple")
    assert r["yontem"] == "apple" and r["kat"] == 2
    y, ref = _kareler(tmp_path / "y.mov"), _kareler(VERI / "hareket60.mp4")
    n = min(len(y), len(ref))
    assert n >= 110
    ara = [_psnr(y[i], ref[i]) for i in range(1, n, 2)]
    kopya = [_psnr(ref[i - 1], ref[i]) for i in range(1, n, 2)]             # ara kare yerine önceki kare
    ozgun = [_psnr(y[i], ref[i]) for i in range(0, n, 2)]
    assert min(ozgun) > 40                                                  # özgün kareler doğru yerde
    assert st.mean(ara) > st.mean(kopya) + 3.0, (st.mean(ara), st.mean(kopya))


def test_yavaslat_rife_yedegi(tmp_path):
    """RIFE yedeği (Neural Engine'den bağımsız): Apple ile aynı sözleşme — doğru sırada özgün kareler, kopyadan
    belirgin iyi ara kareler, doğru süre. 2026-10-05: Apple FRC Neural Engine takılınca asıldı; yedek bu."""
    import statistics as st
    import shutil
    from medya.komutlar.yavaslat import RIFE, yavaslat
    if not RIFE.exists():
        pytest.skip("RIFE kurulu değil: medya kur rife")
    if shutil.disk_usage(KOK).free / 1e9 < 5.5:          # RIFE ara kareleri disk tabanı altında bilerek reddedilir
        pytest.skip("boş disk 5 GB tabanına yakın: RIFE bilerek çalışmaz (yedeğe düşer) — önce yer aç")
    r = yavaslat(str(VERI / "hareket30.mp4"), str(tmp_path / "y.mov"), 0.5, yontem="rife")
    assert r["yontem"] == "rife" and r["kat"] == 2 and abs(r["sure"] - 4.0) < 0.05
    y, ref = _kareler(tmp_path / "y.mov"), _kareler(VERI / "hareket60.mp4")
    n = min(len(y), len(ref))
    assert n >= 110
    ara = [_psnr(y[i], ref[i]) for i in range(1, n, 2)]
    kopya = [_psnr(ref[i - 1], ref[i]) for i in range(1, n, 2)]
    ozgun = [_psnr(y[i], ref[i]) for i in range(0, n, 2)]
    assert min(ozgun) > 40
    assert st.mean(ara) > st.mean(kopya) + 3.0, (st.mean(ara), st.mean(kopya))


def test_yavaslat_dogal_yol(tmp_path):
    """120 fps kaynak, 0.25x, 30 fps çıktı: ara kare üretilmeden yeniden zamanlanmalı."""
    from medya.komutlar.yavaslat import yavaslat
    from medya.ortak import probe
    r = yavaslat(str(VERI / "hareket120.mp4"), str(tmp_path / "d.mov"), 0.25)
    assert r["yontem"] == "dogal"
    assert abs(float(probe(tmp_path / "d.mov")["format"]["duration"]) - 4.0) < 0.1


# ---- yavaslat --kirp/--olcek (O3, 2026-10-08): 4K kaynaktan teslim boyutunda ağır çekim
KIRP_4K, VF_4K = "1312,0,1216,2160", "crop=1216:2160:1312:0,scale=1080:1920:flags=lanczos,"


@pytest.fixture(scope="module")
def kaynak_4k(tmp_path_factory):
    """3840x2160 testsrc2, 60 fps 0,5 sn ve onun çift kareleri (30 fps): tek kez üretilir."""
    from medya.ortak import ffmpeg
    d = tmp_path_factory.mktemp("kaynak4k")
    renk = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
    kod = ["-c:v", "libx264", "-crf", "10", "-preset", "ultrafast", "-pix_fmt", "yuv420p", *renk]
    ff = lambda *a: subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-y", *a], check=True)
    ff("-f", "lavfi", "-i", "testsrc2=s=3840x2160:r=60:d=0.5", *kod, str(d / "k60.mp4"))
    ff("-i", str(d / "k60.mp4"), "-vf", "select='not(mod(n\\,2))',setpts=N/30/TB", "-r", "30", *kod, str(d / "k30.mp4"))
    return d / "k60.mp4", d / "k30.mp4"


def _teslim_klibi(yol, w, h, fps, kare):
    """Boyut, sabit kare hızı, kare sayısı ve bt709 etiketleri."""
    from medya.komutlar.incele import incele_dosya
    from medya.ortak import probe, video_akisi
    v = video_akisi(probe(yol))
    assert (int(v["width"]), int(v["height"])) == (w, h)
    assert v["r_frame_rate"] == f"{fps}/1" and v["avg_frame_rate"] == f"{fps}/1" and int(v["nb_frames"]) == kare, v
    assert (v.get("color_space"), v.get("color_transfer"), v.get("color_primaries")) == ("bt709",) * 3
    assert not any("VFR" in u for u in incele_dosya(yol)["uyarilar"])


def test_yavaslat_kirp_olcek_dogal_yol_4k(tmp_path, kaynak_4k):
    """4K60 → 0,5x, --kirp --olcek 1080x1920: doğal yol (ara kare yok) doğrudan teslim boyutunda; her çıktı karesi
    kaynağın aynı karesinin kırpılıp ölçeklenmiş hâli. Doğal yol eskiden kırpmayı hiç görmezdi (deneme projesi)."""
    from medya.komutlar.yavaslat import yavaslat
    k60, _ = kaynak_4k
    r = yavaslat(str(k60), str(tmp_path / "d.mov"), 0.5, kirp=KIRP_4K, olcek="1080x1920")
    assert r["yontem"] == "dogal"
    _teslim_klibi(tmp_path / "d.mov", 1080, 1920, 30, 30)
    y, ref = _kareler(tmp_path / "d.mov", 540, 960), _kareler(k60, 540, 960, VF_4K)
    yanlis = _kareler(k60, 540, 960, VF_4K.replace(":1312:", ":1112:"))      # 200 px kaymış kırpım
    assert len(y) == len(ref) == 30
    assert min(_psnr(a, b) for a, b in zip(y, ref)) > 40
    assert max(_psnr(a, b) for a, b in zip(y, yanlis)) < 25                 # kırpımın yeri gerçekten denetleniyor


def test_yavaslat_kirp_olcek_ara_kare_yolu_4k(tmp_path, kaynak_4k):
    """4K30 → 0,5x aynı kırp/ölçek, .mp4 (HyperFrames'e girecek biçim): ara kareler kırpılmış 1080x1920 karede
    üretilir, bu yüzden RIFE ilk sırada (yöntem sırası hazır kareye bakar); çift kareler kaynağın kırpılmış kareleri."""
    import shutil
    from medya.komutlar.yavaslat import RIFE, RIFE_MODEL, yavaslat
    _, k30 = kaynak_4k
    r = yavaslat(str(k30), str(tmp_path / "a.mp4"), 0.5, kirp=KIRP_4K, olcek="1080x1920")
    assert r["kat"] == 2 and r["hazir_fps"] == 30
    if RIFE.exists() and RIFE_MODEL.exists() and shutil.disk_usage(KOK).free / 1e9 >= 5.5:
        assert r["yontem"] == "rife", r
    _teslim_klibi(tmp_path / "a.mp4", 1080, 1920, 30, 30)
    y, ref = _kareler(tmp_path / "a.mp4", 540, 960), _kareler(k30, 540, 960, VF_4K)
    assert min(_psnr(y[2 * j], ref[j]) for j in range(len(ref))) > 38


@pytest.mark.parametrize("yol", ["dogal", "ara"])
def test_yavaslat_hdr_ton_esleme_sonra_kirp_olcek(tmp_path, yol):
    """HLG kaynak: ton eşleme kırpma/ölçekten önce, ölçek renk matrisini ve etiketini bozmaz. Başvuru: bugünkü ton
    eşleme → yuv420p → kırp/ölçek. Renk ayarsız scale RGB'yi yanlış matris/aralıkla YUV'ye çeviriyordu (Y 24 dB);
    etiketsiz doğal yol ProRes'inde matris "unknown" kalıyordu (ikisi de 2026-10-08)."""
    from medya.komutlar.incele import incele_dosya
    from medya.komutlar.yavaslat import yavaslat
    kw = {"fps": 15} if yol == "dogal" else {"yontem": "ffmpeg"}
    r = yavaslat(str(VERI / "hdr_hlg.mp4"), str(tmp_path / "h.mov"), 0.5, kirp="160,0,320,360", olcek="160x180", **kw)
    assert r["yontem"] == ("dogal" if yol == "dogal" else "ffmpeg")
    _teslim_klibi(tmp_path / "h.mov", 160, 180, 15 if yol == "dogal" else 30, 90 if yol == "dogal" else 180)
    assert not incele_dosya(tmp_path / "h.mov")["video"]["hdr"]
    ton = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=mobius:desat=0,"
           "zscale=t=bt709:m=bt709:r=tv,format=yuv420p,crop=320:360:160:0,scale=160:180:flags=lanczos,")
    y, ref = _kareler(tmp_path / "h.mov", 160, 180), _kareler(VERI / "hdr_hlg.mp4", 160, 180, ton)
    adim = 1 if yol == "dogal" else 2                       # ara yolda çift kareler kaynağın kareleri
    son = len(ref) - (adim - 1)                             # ara yolun son karesi sağ komşusuz (önceki kare)
    assert min(_psnr(y[adim * j], ref[j]) for j in range(son)) > 40


@pytest.mark.parametrize("boyut,etiket,yol,beklenen", [("1280x720", "yok", "dogal", "duz"),
                                                       ("1280x720", "yok", "ara", "duz"),
                                                       ("1280x720", "smpte170m", "dogal", "601_709"),
                                                       ("640x360", "yok", "dogal", "601_709")])
def test_yavaslat_olcek_sdr_renk_matrisi(tmp_path, boyut, etiket, yol, beklenen):
    """--olcek SDR kaynağın renk matrisini HyperFrames'in 1x çekimi okuduğu gibi okur. Etiketsiz (matris 'unknown') HD
    kaynakta scale'in giriş matrisi 'auto' kalınca kare BT.601 okunup BT.709'a çevriliyordu: kırmızı çubuk 189 → 168,
    Y/U/V düz ölçeğe 31/36/35 dB (2026-10-08 doğrulamasında bulundu; olc_renk.json). HyperFrames etiketsiz ≥ 720p'yi
    BT.709, altını BT.601 sayar (chromeGuessForUntaggedMatrix); BT.601 etiketli kaynak BT.709'a çevrilir. Çıktının
    Y/U/V'si (ham yuv420p) beklenen başvuruya > 45 dB, ötekine < 40 dB (sınama iki durumu gerçekten ayırıyor)."""
    import numpy as np
    from medya.komutlar.incele import incele_dosya
    from medya.komutlar.yavaslat import yavaslat
    from medya.ortak import ffmpeg
    w, h = (int(n) for n in boyut.split("x"))
    ow, oh, k = w // 2, h // 2, tmp_path / "k.mp4"
    renk = (["-bsf:v", "h264_metadata=matrix_coefficients=2:colour_primaries=2:transfer_characteristics=2"]
            if etiket == "yok" else ["-colorspace", etiket, "-color_primaries", etiket, "-color_trc", etiket])
    subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i", f"smptehdbars=s={boyut}:r=60:d=0.5",
                    "-c:v", "libx264", "-crf", "10", "-preset", "ultrafast", "-pix_fmt", "yuv420p", *renk, str(k)],
                   check=True)
    assert (incele_dosya(k)["video"]["renk"]["matris"] or "yok") in ((etiket,) if etiket != "yok" else ("yok", "unknown"))
    kw = {"yontem": "ffmpeg"} if yol == "ara" else {}
    r = yavaslat(str(k), str(tmp_path / "y.mp4"), 0.25 if yol == "ara" else 0.5, olcek=f"{ow}x{oh}", **kw)
    assert r["yontem"] == ("ffmpeg" if yol == "ara" else "dogal")

    def yuv(dosya, vf=None):
        a = subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-i", str(dosya), *(["-vf", vf] if vf else []), "-f",
                            "rawvideo", "-pix_fmt", "yuv420p", "-"], capture_output=True, check=True).stdout
        a, n = np.frombuffer(a, np.uint8).astype(float).reshape(-1, ow * oh * 3 // 2), ow * oh
        return a[:, :n], a[:, n:n * 5 // 4], a[:, n * 5 // 4:]

    cikti = yuv(tmp_path / "y.mp4")
    duz = yuv(k, f"scale={ow}:{oh}:flags=lanczos")                     # matris çevirmez
    cevir = yuv(k, f"scale={ow}:{oh}:flags=lanczos:in_color_matrix=bt601:out_color_matrix=bt709:out_range=tv")
    iyi, kotu = (duz, cevir) if beklenen == "duz" else (cevir, duz)
    for d in range(3):                                                  # Y, U, V; çubuklar durağan: başvurunun ilk karesi
        assert min(_psnr(c, iyi[d][0]) for c in cikti[d]) > 45, ("YUV"[d], beklenen)
        assert max(_psnr(c, kotu[d][0]) for c in cikti[d]) < 40, ("YUV"[d], beklenen)


def test_yavaslat_kirp_hatalari_ve_donuk_kaynak(tmp_path):
    """Kırpma görünen yönde: 90° döndürmeli 640x360 klip 360x640 görünür. Kodlanmış yöne göre geçerli ama görünen
    karenin dışındaki kırpım, tek sayı, bozuk biçim ve en-boy uyuşmazlığı işe başlamadan açık hatayla durur; görünen
    yöndeki kırpım ekranda görünen bölgeyi verir (ffmpeg kareyi süzgeçten önce döndürür: üst yarı mavi)."""
    import numpy as np
    from medya.komutlar.incele import incele_dosya
    from medya.komutlar.yavaslat import yavaslat
    from medya.ortak import MedyaHatasi, ffmpeg
    duz, donuk = tmp_path / "duz.mp4", tmp_path / "donuk.mp4"
    ff = lambda *a: subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-y", *a], check=True)
    ff("-f", "lavfi", "-i", "color=red:s=320x360:r=30:d=1", "-f", "lavfi", "-i", "color=blue:s=320x360:r=30:d=1",
       "-filter_complex", "[0][1]hstack", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(duz))
    ff("-display_rotation:v:0", "90", "-i", str(duz), "-c", "copy", str(donuk))
    assert incele_dosya(donuk)["video"]["gorunen"] == "360x640"
    for kirp, olcek, mesaj in [("0,0,640,360", None, "dışına taşıyor"), ("0,0,360,642", None, "dışına taşıyor"),
                               ("0,0,359,320", None, "çift sayı"), ("1,0,358,320", None, "çift sayı"),
                               ("0,0,360,320", "181x160", "çift sayı"), ("1,2,3", None, "biçiminde"),
                               (None, "1080", "biçiminde"), ("0,0,360,320", "320x320", "en-boy")]:
        with pytest.raises(MedyaHatasi, match=mesaj):
            yavaslat(str(donuk), str(tmp_path / "x.mov"), 0.5, fps=15, kirp=kirp, olcek=olcek)
    assert not (tmp_path / "x.mov").exists()
    r = yavaslat(str(donuk), str(tmp_path / "u.mp4"), 0.5, fps=15, kirp="0,0,360,320")
    assert r["yontem"] == "dogal"
    b = subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-i", str(tmp_path / "u.mp4"), "-frames:v", "1", "-f",
                        "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    ort = np.frombuffer(b, np.uint8).reshape(320, 360, 3).reshape(-1, 3).mean(0)
    assert ort[2] > 200 and ort[0] < 30, ort                # tek renk (mavi): kodlanmış yönde kırpılsa kırmızı+mavi


def test_yavaslat_60fps_kaynakta_gercek_kareleri_atmaz(tmp_path):
    """Ara kare yolunda 60 fps kaynak 0,25x: hazırlık 60 fps × 2. Eskiden 30 fps'e inip × 4 üretiyordu, gerçek
    karelerin yarısı atılıyordu (2026-10-08 doğrulamasında bulundu). Her çift çıktı karesi gerçek bir 60 fps karesi."""
    from medya.komutlar.yavaslat import _hazir_fps, yavaslat
    assert _hazir_fps(60, 30, 120) == (60, 2)              # 0,25x
    assert _hazir_fps(59.94, 30, 120) == (60, 2)
    assert _hazir_fps(60, 30, 300) == (60, 5)              # 0,1x (eskiden 30 fps × 10 → 8'e kırpılıp kare yineliyordu)
    assert _hazir_fps(60, 30, 30 / 0.2) == (30, 5)         # 60'ta kat 2,5 → 30 fps × 5
    assert _hazir_fps(120, 30, 300) == (60, 5)             # 120'de kat 2,5 → 60 × 5 (eskiden 30 × 8)
    assert _hazir_fps(50, 30, 60) == (30, 2)               # uygun bölen yok → eski yol
    assert _hazir_fps(30, 30, 60) == (30, 2) and _hazir_fps(24, 24, 48) == (24, 2)
    r = yavaslat(str(VERI / "hareket60.mp4"), str(tmp_path / "y.mov"), 0.25, sure=0.5)
    assert r["hazir_fps"] == 60 and r["kat"] == 2 and abs(r["sure"] - 2.0) < 0.05
    y, ref = _kareler(tmp_path / "y.mov"), _kareler(VERI / "hareket60.mp4")
    assert len(y) == 60
    assert min(_psnr(y[2 * j], ref[j]) for j in range(30)) > 40


def test_yavaslat_kirp_once_ara_kare_kalitesi(tmp_path):
    """Kırpınca kenarda bağlam azalır; ara kare kalitesi düşmemeli. Aynı yöntemle (RIFE) önce kırpıp × 2 üretmek, tam
    kareyi × 2 üretip sonra kırpmaya karşı, gerçek 60 fps karelerinin aynı kırpımıyla ölçülür (2026-10-08: 720p'de
    fark −0,03 dB; 4K ve gerçek çekim ölçümü sistem/dersler.md)."""
    import shutil
    import statistics as st
    from medya.komutlar.yavaslat import RIFE, yavaslat
    if not RIFE.exists():
        pytest.skip("RIFE kurulu değil: medya kur rife")
    if shutil.disk_usage(KOK).free / 1e9 < 5.5:
        pytest.skip("boş disk 5 GB tabanına yakın: RIFE bilerek çalışmaz (yedeğe düşer) — önce yer aç")
    K = "crop=400:720:440:0,"
    a = yavaslat(str(VERI / "hareket30.mp4"), str(tmp_path / "a.mov"), 0.5, yontem="rife", kirp="440,0,400,720")
    b = yavaslat(str(VERI / "hareket30.mp4"), str(tmp_path / "b.mov"), 0.5, yontem="rife")
    assert a["yontem"] == b["yontem"] == "rife"
    ya, yb = _kareler(tmp_path / "a.mov", 400, 720), _kareler(tmp_path / "b.mov", 400, 720, K)
    ref = _kareler(VERI / "hareket60.mp4", 400, 720, K)
    n = min(len(ya), len(yb), len(ref))
    assert n >= 110
    ara = range(1, n - 1, 2)                               # son kare: RIFE'nin sağ komşusuz kopyası
    pa, pb = [_psnr(ya[i], ref[i]) for i in ara], [_psnr(yb[i], ref[i]) for i in ara]
    kopya = [_psnr(ref[i - 1], ref[i]) for i in ara]
    assert st.mean(pa) >= st.mean(pb) - 0.5, (st.mean(pa), st.mean(pb))
    assert st.mean(pa) > st.mean(kopya) + 2.5, (st.mean(pa), st.mean(kopya))


def test_analiz_ve_ses_olay(tmp_path, apple_ml):
    _apple_gerek()
    from medya.cli import ana
    from medya.ortak import json_oku
    assert ana(["analiz", str(VERI / "kesimli.mp4"), "--aralik", "2", "--cikti", str(tmp_path / "a.json")]) == 0
    k = json_oku(tmp_path / "a.json")["kareler"]
    assert len(k) >= 9 and all(-1.0 <= x.get("estetik", 0) <= 1.0 for x in k) and any(x.get("etiketler") for x in k)
    if not (VERI / "karma.wav").exists():
        pytest.skip("konuşma fikstürü yok")
    assert ana(["ses-olay", str(VERI / "karma.wav"), "--cikti", str(tmp_path / "o.json")]) == 0
    olaylar = json_oku(tmp_path / "o.json")["olaylar"]
    konusma = [o for o in olaylar if o["sinif"] == "speech"]
    assert konusma and any(o["bas"] < 16 < o["son"] for o in konusma)          # konuşma 12–20 sn'de
    assert any(o["sinif"] == "music" for o in olaylar)


def test_yaziya_dok_turkce(veri, tmp_path):
    if "konusma_tr" not in veri or not (KOK / "ortamlar" / "ses" / "bin" / "python").exists():
        pytest.skip("konuşma fikstürü ya da ses ortamı yok")
    import re
    from medya.komutlar.yaziya_dok import yaziya_dok
    r = yaziya_dok(str(VERI / "konusma_tr.wav"), dil="tr")
    norm = lambda m: re.findall(r"[a-zçğıöşü]+", m.replace("İ", "i").replace("I", "ı").lower())
    beklenen = [w for w in norm(veri["konusma_tr"]["metin"]) if w != "dokuzda"]   # "9'da" yazılabilir
    bulunan = set(norm(r["metin"]))
    assert sum(w in bulunan for w in beklenen) / len(beklenen) >= 0.9, r["metin"]
    assert r["dil"] == "tr" and r["kelimeler"] and r["kelimeler"][0]["bas"] < 1.0


def test_ayir_konusmayi_vokale_ayirir(veri, tmp_path):
    if not (VERI / "karma.wav").exists() or not (KOK / "ortamlar" / "ses" / "bin" / "python").exists():
        pytest.skip("fikstür ya da ses ortamı yok")
    import numpy as np
    from medya.cli import ana
    from medya.ortak import ses_oku
    assert ana(["ayir", str(VERI / "karma.wav"), "--cikti", str(tmp_path / "k")]) == 0
    v, sr = ses_oku(tmp_path / "k" / "vocals.wav", sr=16000)
    db = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
    assert db(v[12 * sr:20 * sr]) - db(v[2 * sr:10 * sr]) > 20                  # konuşma vokal katmanında


def test_exif_gps_ve_kayipsiz_temizlik(tmp_path):
    """Görselde GPS/tarih okunur; meta-temizle pikselleri değiştirmeden (yeniden kodlamadan) siler, yönü korur."""
    if not (KOK / "arac" / "exiftool").exists():
        pytest.skip("exiftool kurulu değil")
    import subprocess
    import numpy as np
    from PIL import Image
    from medya.cli import ana
    from medya.komutlar.incele import incele_dosya
    from medya.ortak import ffmpeg
    f = tmp_path / "f.jpg"
    subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=320x240", "-frames:v", "1", str(f)], check=True)
    subprocess.run([str(KOK / "arac" / "exiftool"), "-q", "-overwrite_original", "-GPSLatitude=41.0", "-GPSLatitudeRef=N",
                    "-GPSLongitude=29.0", "-GPSLongitudeRef=E", "-DateTimeOriginal=2026:05:01 14:30:00", "-Orientation#=6", str(f)], check=True)
    r = incele_dosya(f)
    assert r["etiketler"]["konum_var"] and r["exif"]["tarih"].startswith("2026:05:01")
    assert ana(["meta-temizle", str(f), "--cikti", str(tmp_path / "t.jpg")]) == 0
    t = incele_dosya(tmp_path / "t.jpg")
    assert not t["etiketler"]["konum_var"] and not t["exif"].get("tarih")
    assert np.array_equal(np.asarray(Image.open(f)), np.asarray(Image.open(tmp_path / "t.jpg")))
    assert t["exif"].get("yon") == 6


def test_arkaplan_sil_kutu(tmp_path, apple_ml):
    _apple_gerek()
    import subprocess
    import numpy as np
    from PIL import Image
    from medya.komutlar.arkaplan import arkaplan_sil
    from medya.ortak import ffmpeg
    f = tmp_path / "k.png"
    subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=800x600", "-vf",
                    "drawbox=x=250:y=150:w=300:h=300:color=red@1:t=fill", "-frames:v", "1", str(f)], check=True)
    arkaplan_sil(str(f), str(tmp_path / "s.png"))
    al = np.asarray(Image.open(tmp_path / "s.png"))[..., 3]
    assert np.mean(al[160:440, 260:540] > 200) > 0.95 and np.mean(al[:140] < 30) > 0.95


def test_zamankodu_taslagi(tmp_path):
    from medya.cli import ana
    from medya.ortak import probe
    assert ana(["zamankodu", str(VERI / "kesimli.mp4"), "--cikti", str(tmp_path / "z.mp4")]) == 0
    p = probe(tmp_path / "z.mp4")
    assert abs(float(p["format"]["duration"]) - 20.0) < 0.2


def test_ses_temizle_gecikmesiz_ve_anlasilir(veri, tmp_path):
    """Gürültülü konuşma: SI-SDR artmalı, çıktı gecikmemeli (≤1 ms), Whisper anlaşılırlığı düşmemeli."""
    if not (KOK / "arac" / "deep-filter").exists() or "konusma_tr" not in veri:
        pytest.skip("deep-filter ya da konuşma fikstürü yok")
    import subprocess
    import numpy as np
    from medya.komutlar.ses_temizle import ses_temizle
    from medya.ortak import ffmpeg, ses_oku
    temiz, gurultulu = tmp_path / "t.wav", tmp_path / "g.wav"
    subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-i", str(VERI / "konusma_tr.wav"), "-ar", "48000", "-ac", "1", str(temiz)], check=True)
    subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-i", str(temiz), "-f", "lavfi", "-i", "anoisesrc=color=brown:amplitude=0.5:r=48000:seed=7",
                    "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:normalize=0[a]", "-map", "[a]", "-ac", "1", str(gurultulu)], check=True)
    r = ses_temizle(str(gurultulu), str(tmp_path / "c.wav"))
    assert abs(r["gecikme"]["gecikme_ms"]) <= 1.0
    c, _ = ses_oku(temiz, sr=48000); n, _ = ses_oku(gurultulu, sr=48000); e, _ = ses_oku(tmp_path / "c.wav", sr=48000)
    m = min(len(c), len(n), len(e))
    def sisdr(x, ref):
        a = np.dot(x[:m], ref[:m]) / np.dot(ref[:m], ref[:m]); s = a * ref[:m]
        return 10 * np.log10(np.sum(s ** 2) / np.sum((x[:m] - s) ** 2))
    assert sisdr(e, c) > sisdr(n, c) + 5


def test_kontak_ekrandaki_kareyi_alir(tmp_path):
    """Bir karenin süresi İÇİNDEKİ an istendiğinde o kare gelmeli (ffmpeg -ss sonrakini verir; düzeltildi)."""
    import numpy as np
    from PIL import Image
    from medya.komutlar.kontak import kare_al
    for t in (8.0, 8.0 + 1 / 60, 8.0 + 1 / 31):                 # siyah kare 240: [8,000, 8,033)
        kare_al(str(VERI / "kusurlu.mp4"), t, tmp_path / "k.png", 160)
        assert np.asarray(Image.open(tmp_path / "k.png").convert("L")).mean() < 10, t
    kare_al(str(VERI / "kusurlu.mp4"), 7.99, tmp_path / "k.png", 160)       # önceki kare siyah değil
    assert np.asarray(Image.open(tmp_path / "k.png").convert("L")).mean() > 10


def test_denetle_web_hizli_baslatma():
    from medya.komutlar.denetle import denetle
    t = denetle(str(VERI / "kusurlu.mp4"), hedef="web")["denetimler"]["teknik"]
    assert not t["gecti"] and any("faststart" in b for b in t["bulgular"])


def test_proje_yeni_sablon_ve_salt_okunur_kopya(tmp_path):
    import os
    import shutil
    from medya.cli import ana
    kaynak = tmp_path / "asil.mp4"
    shutil.copy2(VERI / "vfr.mp4", kaynak)
    ad = "pytest gecici proje"
    hedef = KOK / "projeler" / f"{__import__('datetime').date.today().isoformat()}-pytest-gecici-proje"
    try:
        assert ana(["proje", "yeni", ad, "--tur", "video", "--kaynak", str(kaynak)]) == 0
        brief = (hedef / "BRIEF.md").read_text()
        assert "Ekranda yazı: YOK" in brief and "Gizlilik" in brief and ad in brief
        kopya = hedef / "kaynak" / "asil.mp4"
        assert kopya.exists() and not os.access(kopya, os.W_OK)          # salt okunur kopya
        assert os.access(kaynak, os.W_OK)                                 # asıl dosyaya dokunulmadı
    finally:
        if hedef.exists():
            (hedef / "kaynak" / "asil.mp4").chmod(0o644)
            shutil.rmtree(hedef)


def test_nle_otio_edl_erime_ve_sesler(tmp_path):
    """Plan → .otio/.edl: örtüşen erime kesim+geçişe döner, kaynak kareleri ve süre korunur, geri okunur."""
    import opentimelineio as otio
    from medya.komutlar.nle import zaman_cizelgesi
    k = str(VERI / "kesimli.mp4")
    plan = {"fps": 30, "muzik": {"dosya": str(VERI / "muzik_net.wav"), "bas": 1.0}, "cekimler": [
        {"no": 1, "kaynak": k, "kaynak_bas": 0.0, "cikti_bas": 0.0, "cikti_son": 3.3, "ses": "muzik", "gecis": "kesim"},
        {"no": 2, "kaynak": k, "kaynak_bas": 3.0, "cikti_bas": 2.9, "cikti_son": 5.0, "ses": "kendi",
         "gecis": {"tur": "erime", "sure_kare": 12}},                                  # 12 kare örtüşme
        {"no": 3, "kaynak": str(VERI / "hareket30.mp4"), "klip": str(VERI / "hareket60.mp4"), "klip_bas": 0.0,
         "kaynak_bas": 0.0, "cikti_bas": 5.0, "cikti_son": 6.5, "hiz": 0.5, "ses": "muzik", "gecis": "savurma"},
        {"no": 4, "kaynak": k, "kaynak_bas": 10.0, "cikti_bas": 6.5, "cikti_son": 8.5, "ses": "kendi",
         "gecis": {"tur": "erime", "sure_kare": 10}},                                  # örtüşmesiz: tutamaçtan
        {"no": 5, "kaynak": k, "kaynak_bas": 15.0, "cikti_bas": 9.0, "cikti_son": 10.0, "hiz": 2, "ses": "muzik"},
    ]}
    tl, uyarilar = zaman_cizelgesi(plan, tmp_path)
    V = tl.tracks[0]
    oge = [(type(x).__name__, x.in_offset.value, x.out_offset.value) if isinstance(x, otio.schema.Transition)
           else (type(x).__name__, x.source_range.start_time.to_seconds(), round(x.duration().to_seconds() * 30))
           for x in V]
    assert oge == [("Clip", 0.0, 93), ("Transition", 6, 6), ("Clip", 3.2, 57), ("Clip", 0.0, 45),
                   ("Transition", 5, 5), ("Clip", 10.0, 60), ("Gap", 0.0, 15), ("Clip", 15.0, 30)]
    assert round(V.duration().rescaled_to(30).value) == 300
    muzik, ses = tl.tracks[1], tl.tracks[2]
    assert muzik[0].source_range.start_time.to_seconds() == 1.0 and round(muzik.duration().to_seconds(), 3) == 10.0
    assert [round(ses.range_of_child_at_index(i).start_time.to_seconds(), 3) for i in (1, 3)] == [2.9, 6.5]
    assert any("2x" in u for u in uyarilar) and any("savurma" in u for u in uyarilar)
    otio.adapters.write_to_file(tl, str(tmp_path / "k.otio"))
    geri = otio.adapters.read_from_file(str(tmp_path / "k.otio"))
    assert len(list(geri.find_clips())) == len(list(tl.find_clips()))
    # uyum: düz mutlak yol (Resolve file:// reddetti), işaret metni comment'ta (Kdenlive), makara = kaynak dosya
    klipler = list(V.find_clips())
    assert all(not c.media_reference.target_url.startswith("file:") for c in klipler)
    assert all(m.comment for c in klipler for m in c.markers)
    assert [c.metadata["cmx_3600"]["reel"] for c in klipler] == ["A001", "A001", "A002", "A001", "A001"]


def test_nle_komutu_edl_ascii_ve_ndf(tmp_path):
    """Komut uçtan uca: .otio + .edl yazar ve geri okur; EDL ASCII, NON-DROP başlıklı, makaralar kaynak başına."""
    from medya.cli import ana
    plan = {"ad": "çekim şöleni", "fps": 30, "cekimler": [
        {"no": 1, "kaynak": str(VERI / "kesimli.mp4"), "kaynak_bas": 0.0, "cikti_bas": 0.0, "cikti_son": 2.0,
         "gecis": "kesim", "kadraj": {"olcek": 1.2}},
        {"no": 2, "kaynak": str(VERI / "kesimli.mp4"), "kaynak_bas": 5.0, "cikti_bas": 2.0, "cikti_son": 4.0,
         "gecis": "savurma"}]}
    (tmp_path / "plan").mkdir()
    (tmp_path / "plan" / "kurgu.json").write_text(json.dumps(plan, ensure_ascii=False))
    assert ana(["nle", str(tmp_path / "plan" / "kurgu.json"), "--bicim", "hepsi"]) == 0
    edl = (tmp_path / "cikti" / "nle" / "kurgu.edl").read_text()
    assert edl.isascii() and "FCM: NON-DROP FRAME" in edl and ";" not in edl.split("FCM", 1)[1].replace("*", "")
    assert "A001" in edl and "SAVURMA" in edl
    assert (tmp_path / "cikti" / "nle" / "kurgu-kdenlive.otio").exists()


def test_nle_kdenlive_uyarlamasi(tmp_path):
    """Kdenlive 26.08 OTIO içe aktarımının ölçülen iki hatasına karşı (2026-10-08, testler/nle_olc.py): zaman çizelgesi
    hızı tek (proje fps'i duration().rate'ten), erime yok (kesim + işaret), her izin sonunda 1 karelik 'SON — sil'
    klibi (son klibin giriş noktası kaybolmasın). Kesim yerleri ve Kdenlive'ın hesaplayacağı kaydırma Resolve
    sürümüyle aynı olmalı."""
    import opentimelineio as otio
    from medya.komutlar.nle import zaman_cizelgesi
    k = str(VERI / "kesimli.mp4")
    plan = {"fps": 30, "muzik": {"dosya": str(VERI / "muzik_net.wav"), "bas": 1.0}, "cekimler": [
        {"no": 1, "kaynak": k, "kaynak_bas": 0.5, "cikti_bas": 0.0, "cikti_son": 3.3, "ses": "muzik"},
        {"no": 2, "kaynak": k, "kaynak_bas": 3.0, "cikti_bas": 2.9, "cikti_son": 5.0, "ses": "kendi",
         "gecis": {"tur": "erime", "sure_kare": 12}},
        {"no": 3, "kaynak": str(VERI / "hareket60.mp4"), "kaynak_bas": 0.25, "cikti_bas": 5.0, "cikti_son": 6.5,
         "ses": "muzik"}]}
    tl, _ = zaman_cizelgesi(plan, tmp_path)
    tk, uyarilar = zaman_cizelgesi(plan, tmp_path, kdenlive=True)
    assert tl.duration().rate == 60 and tk.duration().rate == 30        # karışık hız Kdenlive'da 60 fps proje açar
    assert not any(isinstance(x, otio.schema.Transition) for iz in tk.tracks for x in iz)
    toplam = round(tl.tracks[0].duration().rescaled_to(30).value)
    for iz in tk.tracks:
        son = iz[-1]
        assert son.name == "SON — sil" and son.source_range.duration.value == 1
        assert round(iz.range_of_child_at_index(len(iz) - 1).start_time.rescaled_to(30).value) == toplam
        for c in iz.find_clips():
            assert c.source_range.start_time.rate == 30 and c.source_range.duration.rate == 30
    gercek = lambda t: [c for iz in t.tracks for c in iz.find_clips() if c.name != "SON — sil"]
    for a, b in zip(gercek(tl), gercek(tk)):                          # aynı kesim yerleri, aynı kaydırma
        assert round(a.range_in_parent().start_time.rescaled_to(30).value) == \
            round(b.range_in_parent().start_time.rescaled_to(30).value)
        assert round(a.source_range.start_time.to_seconds() * 30) == b.source_range.start_time.value
    gelen = gercek(tk)[1]
    assert any("erime 12 kare" in m.name for m in gelen.markers)
    assert any("SON — sil" in u for u in uyarilar) and any("erime" in u for u in uyarilar)


def test_nle_kdenlive_isaret_klibin_basinda(tmp_path):
    """Klip notu işareti klibin ilk karesine düşmeli. OTIO'da işaret klibin kaynak saatindedir (düz .otio böyle yazar);
    Kdenlive 26.08 kırpılmış başlangıcı yeniden ekliyor (otioimport.cpp: pos = start + işaret, kaydırma = start − TC):
    2026-10-08 kaydedilen projede giriş 21 → işaret 42 ölçüldü. Zaman kodlu medyada TC de düşülmeli. Ölçü başı
    kılavuzları zaman çizelgesi hızında olmalı (Kdenlive onları yeniden ölçeklemeden okuyor)."""
    import subprocess
    from medya.komutlar.nle import zaman_cizelgesi
    tc = tmp_path / "tc.mov"                                            # başlangıç zaman kodu 10 sn = 300 kare
    subprocess.run([str(KOK / "arac" / "ffmpeg"), "-nostdin", "-v", "error", "-i", str(VERI / "kesimli.mp4"),
                    "-c", "copy", "-timecode", "00:00:10:00", str(tc)], check=True)
    plan = {"fps": 30, "muzik": {"dosya": str(VERI / "muzik_net.wav"), "bas": 1.0}, "cekimler": [
        {"no": 1, "kaynak": str(VERI / "kesimli.mp4"), "kaynak_bas": 2.0, "cikti_bas": 0.0, "cikti_son": 2.0,
         "kadraj": {"olcek": 1.2}},
        {"no": 2, "kaynak": str(VERI / "hareket60.mp4"), "kaynak_bas": 0.5, "cikti_bas": 1.8, "cikti_son": 3.5,
         "gecis": {"tur": "erime", "sure_kare": 6}},
        {"no": 3, "kaynak": str(tc), "kaynak_bas": 1.0, "cikti_bas": 3.5, "cikti_son": 5.0, "hareket": {"tur": "kenburns"}}]}
    muzik = {"olcu_baslari": [1.0, 2.5, 4.0], "guven_seviye": "yuksek"}
    tl, _ = zaman_cizelgesi(plan, tmp_path, muzik)
    tk, _ = zaman_cizelgesi(plan, tmp_path, muzik, kdenlive=True)
    duz = list(tl.tracks[0].find_clips())                             # düz .otio: OTIO anlamı (kaynak saati)
    assert [len(c.markers) for c in duz] == [1, 0, 1]                  # erime orada gerçek geçiş, notu yok
    assert all(m.marked_range.start_time == c.source_range.start_time for c in duz for m in c.markers)
    r = tk.duration().rate
    klipler = [c for c in tk.tracks[0].find_clips() if c.name != "SON — sil"]
    assert round(klipler[2].source_range.start_time.value) == 330       # TC 300 + 1 sn
    for c, tc_kare in zip(klipler, (0, 0, 300)):
        start = round(c.source_range.start_time.rescaled_to(r).value)   # Kdenlive'ın kırpılmış başlangıcı
        assert len(c.markers) == 1
        assert start + round(c.markers[0].marked_range.start_time.rescaled_to(r).value) == start - tc_kare
    assert [(m.marked_range.start_time.value, m.marked_range.start_time.rate) for m in tk.tracks.markers] == \
        [(0, r), (45, r), (90, r)]


def test_nle_olc_erime_rampasi():
    """testler/nle_olc.py erimeyi ağırlık rampasından ölçer (karışık kare saymak, ilk karesinde ağırlığı 0 olan programda
    1 kare eksik verir). Bilinen cevaplı yapay kod blokları: 12 karelik erime kare merkezinde (Resolve 21.1 böyle: orta
    113,5) ve kare başında (MLT: 114) örneklenince uygun; 11 kare ve 1 kare geç/erken erime uygun değil."""
    import numpy as np
    from nle_olc import _rampa
    a, b = {"harf": "B", "bas_n": 60, "son_n": 120}, {"harf": "C", "bas_n": 108, "son_n": 168}   # örtüşme 108–119
    kimlik = lambda h: np.array([255.0 * (((ord(h) - 64) >> (3 - j)) & 1) for j in range(4)] + [0.0] * 12)
    olc = lambda f: _rampa([kimlik("B") * (1 - w) + kimlik("C") * w
                            for w in (min(1.0, max(0.0, f(n))) for n in range(170))], a, b)
    r = olc(lambda n: (n + 0.5 - 108) / 12)
    assert r["uygun"] and abs(r["kare"] - 12) < 0.05 and abs(r["orta"] - 113.5) < 0.05
    assert olc(lambda n: (n - 108) / 12)["uygun"]
    for kotu in (lambda n: (n + 0.5 - 108) / 11, lambda n: (n - 0.5 - 108) / 12, lambda n: (n + 1.5 - 108) / 12):
        assert not olc(kotu)["uygun"]


def test_ane_tikanikligi_teshisi():
    """2026-10-05: takılı ANECompilerService Vision/FRC'yi sessizce asmıştı — bekçi bunu tanımalı, normali değil."""
    from medya.ortak import ane_tikanikligi, _etime_sn
    assert _etime_sn("18:11:07") == 65467 and _etime_sn("03-18:08:28") == 324508 and _etime_sn("02:22") == 142
    takili = "  18:11:07  99.8 /System/Library/PrivateFrameworks/AppleNeuralEngine.framework/XPCServices/ANECompilerService.xpc/Contents/MacOS/ANECompilerService\n"
    assert "sudo killall ANECompilerService" in ane_tikanikligi(takili)
    assert ane_tikanikligi("     00:12  97.0 /x/ANECompilerService\n") is None        # yeni başlamış derleme: normal
    assert ane_tikanikligi("  05:00:00   0.0 /x/ANECompilerService\n") is None        # boşta bekleyen servis


def test_remotion_sablonu_cizer_ve_lisanssiz(tmp_path):
    """Remotion şablonu: stüdyo kökünün node_modules'uyla çizer (yerel Chrome, bt709 etiketli), lisans anahtarı yok."""
    import shutil
    rm = KOK / "node_modules" / ".bin" / "remotion"
    if not rm.exists():
        pytest.skip("Remotion kurulu değil: medya kur remotion")
    ayar = (KOK / "sablonlar" / "remotion" / "remotion.config.ts").read_text()
    assert "LicenseKey(" not in ayar and "setBrowserExecutable" in ayar and "bt709" in ayar
    hedef = KOK / "testler" / ".gecici" / "remotion-sinama"      # modüller stüdyo kökünden çözülsün diye ağaç içinde
    shutil.rmtree(hedef, ignore_errors=True)
    shutil.copytree(KOK / "sablonlar" / "remotion", hedef)
    try:
        r = subprocess.run([str(rm), "render", "src/index.ts", "Ornek", "out/o.mp4", "--scale=0.25", "--log=error"],
                           cwd=hedef, capture_output=True, text=True, timeout=300)
        assert r.returncode == 0, r.stderr[-1500:]
        from medya.ortak import probe
        v = next(s for s in probe(hedef / "out" / "o.mp4")["streams"] if s["codec_type"] == "video")
        assert (v["width"], v["height"]) == (270, 480)
        assert v.get("color_space") == "bt709" and v.get("color_range") == "tv"
        assert abs(float(probe(hedef / "out" / "o.mp4")["format"]["duration"]) - 4.0) < 0.05   # 60+50+35-15-10 kare
    finally:
        shutil.rmtree(hedef, ignore_errors=True)


# Sayfanın WebGL sürücü adını PNG'nin ilk satırına karakter kodu olarak yazar (console.log çizim günlüğünde görünmedi).
REMOTION_GL_BILGI = """import {useEffect, useRef, useState} from 'react';
import {AbsoluteFill, Composition, continueRender, delayRender, registerRoot} from 'remotion';

const GlBilgi: React.FC = () => {
	const tuval = useRef<HTMLCanvasElement>(null);
	const [bekle] = useState(() => delayRender('gl'));
	useEffect(() => {
		const gl = document.createElement('canvas').getContext('webgl2');
		const ext = gl?.getExtension('WEBGL_debug_renderer_info');
		const metin = gl && ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : 'webgl-yok';
		const ctx = tuval.current!.getContext('2d')!;
		const img = ctx.createImageData(256, 1);
		for (let i = 0; i < Math.min(metin.length, 255); i++) img.data.set([metin.charCodeAt(i) & 255, 0, 0, 255], i * 4);
		ctx.putImageData(img, 0, 0);
		continueRender(bekle);
	}, [bekle]);
	return <AbsoluteFill style={{background: 'black'}}><canvas ref={tuval} width={256} height={2} /></AbsoluteFill>;
};
registerRoot(() => <Composition id="GlBilgi" component={GlBilgi} durationInFrames={1} fps={30} width={256} height={2} />);
"""


def _remotion_kopyasi(ad, paket):
    """Şablonun ağaç içi kopyası (modüller stüdyo kökünden çözülsün) ve çizici; Remotion ya da ek paketi yoksa atla."""
    import shutil
    rm = KOK / "node_modules" / ".bin" / "remotion"
    if not rm.exists() or not (KOK / "node_modules" / paket).exists():
        pytest.skip(f"{paket} kurulu değil: medya kur remotion --yeniden")
    hedef = KOK / "testler" / ".gecici" / ad
    shutil.rmtree(hedef, ignore_errors=True)
    shutil.copytree(KOK / "sablonlar" / "remotion", hedef)
    return lambda *arg: _remotion_calistir(rm, hedef, arg), hedef


def _remotion_calistir(rm, hedef, arg):
    r = subprocess.run([str(rm), *arg, "--log=error"], cwd=hedef, capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr[-1500:]


def _remotion_videosu(yol, kare, w, h):
    """Çizimin akış ölçüleri (30 fps, kare sayısı, bt709 tv) ve RGB kareleri."""
    import numpy as np
    from medya.ortak import ffmpeg, probe
    p = probe(yol)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    assert (v["width"], v["height"], v["r_frame_rate"], int(v["nb_frames"])) == (w, h, "30/1", kare)
    assert abs(float(p["format"]["duration"]) - kare / 30) < 0.05
    assert v.get("color_space") == "bt709" and v.get("color_range") == "tv"
    r = subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-i", str(yol), "-pix_fmt", "rgb24", "-fps_mode",
                        "passthrough", "-f", "rawvideo", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, h, w, 3).astype(float)


def test_remotion_3b_ornegi_gpu_da_cizer():
    """@remotion/three şablon örneği (Ornek3B). remotion.config.ts'deki gl 'angle' sayfanın WebGL'ini Apple GPU'suna
    bağlar (ANGLE Metal). Ayarsız Remotion 4.0.533 SwiftShader'a (CPU) düşüyor; swiftshader, egl, vulkan ve angle-egl
    seçeneklerinde WebGL hiç yok (2026-10-09, sistem/devam/remotion-3b/2026-10-09/). Çizim 270x480, 30 fps, 90 kare,
    bt709. Düğüm 0. karede yok (yay girişi), sonra görünür ve ışıklı: kırmızı baskın piksel var, ışıksız malzeme siyah
    kalırdı. Kareyle döner; tuval saydam (köşede CSS arka planı)."""
    import shutil
    import numpy as np
    from PIL import Image
    ayar = (KOK / "sablonlar" / "remotion" / "remotion.config.ts").read_text()
    assert "Config.setChromiumOpenGlRenderer('angle')" in ayar
    ciz, hedef = _remotion_kopyasi("remotion-3b-sinama", "@remotion/three")
    try:
        (hedef / "src" / "gl-bilgi.tsx").write_text(REMOTION_GL_BILGI)
        ciz("still", "src/gl-bilgi.tsx", "GlBilgi", "out/gl.png")
        satir = np.asarray(Image.open(hedef / "out" / "gl.png").convert("RGB"))[0, :, 0]
        metin = "".join(map(chr, satir[:int(np.argmax(satir == 0))]))
        assert "ANGLE Metal Renderer" in metin, f"3B çizim GPU'da değil: {metin!r} (gl ayarı ya da Chrome değişti mi?)"
        ciz("render", "src/index.ts", "Ornek3B", "out/u.mp4", "--scale=0.25")
        k = _remotion_videosu(hedef / "out" / "u.mp4", 90, 270, 480)
        dugum = [float(((x[..., 0] - x[..., 2]) > 30).mean()) for x in k]      # kırmızı baskın = ışıklı düğüm
        assert dugum[0] < 0.002 and min(dugum[45], dugum[89]) > 0.05, dugum[::15]
        assert np.abs(k[30] - k[60]).mean() > 3                                 # döndü
        assert k[45][2, 2, 2] - k[45][2, 2, 0] > 20                              # köşede mavi CSS arka planı
    finally:
        shutil.rmtree(hedef, ignore_errors=True)


def test_remotion_lottie_ornegi_yerel_ve_olcusu_dogru():
    """@remotion/lottie şablon örneği (OrnekLottie): public/lottie/ornek.json, stüdyoda kodla yazıldı; uzak adres yok.
    Çizim 270x480, 30 fps, 60 kare, bt709; halka trim path ile çizilir (alanı 10 → 20 → 36. karede artar). Bilinen
    cevap (59. kare, PNG, --scale=0.5): 512'lik Lottie 900 px'lik kutuya ölçeklenir, s = 900/512 × 0,5. Halka
    (yarıçap 160, çizgi 28) π((174·s)² − (146·s)²), nokta (çap 120) π(60·s)². Kenar yumuşatması kapsama oranıyla
    sayılır."""
    import math
    import shutil
    import numpy as np
    from PIL import Image
    ciz, hedef = _remotion_kopyasi("remotion-lottie-sinama", "@remotion/lottie")
    try:
        assert "staticFile('lottie/ornek.json')" in (hedef / "src" / "OrnekLottie.tsx").read_text()
        ciz("render", "src/index.ts", "OrnekLottie", "out/l.mp4", "--scale=0.25")
        k = _remotion_videosu(hedef / "out" / "l.mp4", 60, 270, 480)
        yy, xx = np.mgrid[0:480, 0:270]
        halka = [float(np.clip((k[i][..., 1] - 42) / 155, 0, 1)[np.hypot(xx - 135, yy - 240) > 45].sum())
                 for i in (10, 20, 36)]
        assert halka[0] < halka[1] < halka[2], halka
        ciz("still", "src/index.ts", "OrnekLottie", "out/l59.png", "--frame=59", "--scale=0.5")
        x = np.asarray(Image.open(hedef / "out" / "l59.png").convert("RGB")).astype(float)
        assert x.shape == (960, 540, 3) and tuple(x[5, 5]) == (14, 42, 31)        # arka plan #0e2a1f
        yy, xx = np.mgrid[0:960, 0:540]
        r = np.hypot(xx + 0.5 - 270, yy + 0.5 - 480)
        s = 900 / 512 * 0.5
        halka_alan = float(np.clip((x[..., 1] - 42) / (197 - 42), 0, 1)[r >= 90].sum())     # G: halka #6cc58d
        nokta_alan = float(np.clip((x[..., 0] - 14) / (242 - 14), 0, 1)[r < 90].sum())      # R: nokta #f26b5b
        assert abs(halka_alan / (math.pi * ((174 * s) ** 2 - (146 * s) ** 2)) - 1) < 0.02, halka_alan
        assert abs(nokta_alan / (math.pi * (60 * s) ** 2) - 1) < 0.02, nokta_alan
    finally:
        shutil.rmtree(hedef, ignore_errors=True)


HF_FIKSTUR = KOK / "testler" / "hyperframes-baslik"
HF_BASVURU = KOK / "testler" / "hyperframes-baslik-basvuru.json"


def _ses_baslangici(karisim, kaynak, sr, tahmin, ara=0.25):
    """Kaynak sesin karışımdaki başlangıcı (sn, örnek kesinliği): tahmin ± ara içinde çapraz ilinti tepesi."""
    import numpy as np
    bas = max(0, int((tahmin - ara) * sr))
    parca = karisim[bas:int((tahmin + ara) * sr) + len(kaynak)]
    n = 1 << int(np.ceil(np.log2(len(parca) + len(kaynak))))
    ilinti = np.fft.irfft(np.fft.rfft(parca, n) * np.conj(np.fft.rfft(kaynak, n)), n)[:len(parca) - len(kaynak) + 1]
    return (bas + int(np.argmax(ilinti))) / sr


def _hf_ozet(yol, sesler):
    """Çizimin özeti: akış ölçüleri, kaynak seslerin karışımdaki başlangıcı, kare başına 16x9 hücre ortalaması (gri,
    0-255, onaltılık). Başvuru JSON'u da budur (mp4 depoya girmez)."""
    import numpy as np
    from medya.ortak import ffmpeg, probe
    p = probe(yol)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    a = next(s for s in p["streams"] if s["codec_type"] == "audio")

    def pcm(dosya):
        r = subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-i", str(dosya), "-vn", "-ac", "1", "-ar", "48000",
                            "-f", "f32le", "-"], capture_output=True, check=True)
        return np.frombuffer(r.stdout, np.float32).astype(float)

    karisim, k = pcm(yol), _kareler(yol, 64, 36)
    hucre = np.rint(k.reshape(len(k), 9, 4, 16, 4).mean(axis=(2, 4))).astype(np.uint8)
    return {"genislik": v["width"], "yukseklik": v["height"], "fps": v["r_frame_rate"], "kare": int(v["nb_frames"]),
            "sure": float(v["duration"]), "ses_kodek": a["codec_name"],
            "ses_baslangic": {ad: _ses_baslangici(karisim, pcm(HF_FIKSTUR / src), 48000, t)
                              for ad, (src, t) in sesler.items()},
            "kareler": [h.tobytes().hex() for h in hucre]}


def test_kompozisyon_hyperframes_cizimi_izgarada_ve_basvuruyla_ayni(tmp_path):
    """Varsayılan motorun çizimi: fikstür lint'ten 0 hatayla geçer; taslak çizim 1920x1080, 30 fps, 150 kare, 5 sn;
    sesler bildirilen anda ve kare ızgarasında başlar (çapraz ilinti, örnek kesinliği; ızgara dışı zamanda görüntü
    sesten 1 kareye kadar kayar); kareler sabit sürümün başvurusuyla aynı (16x9 hücre, en çok 3 düzey fark — duyarlılık
    2026-10-08'de ölçüldü: başlık Inter'e çevrilince 134/150, 1 kare kayma 23/149 karede yakalanır). Telemetri ve güncelleme
    denetimi kapalı. Yükseltmede fark çıkarsa sürüm notuyla açıklanır; çizim kabul edilirse başvuru yeniden yazılır:
    MEDYA_HF_BASVURU=yaz medya test kompozisyon."""
    import datetime
    import hashlib
    import os
    import re
    import numpy as np
    hf = KOK / "node_modules" / ".bin" / "hyperframes"
    if not hf.exists():
        pytest.skip("HyperFrames kurulu değil: medya kur hyperframes")
    if not (HF_FIKSTUR / "vendor" / "gsap.min.js").exists():
        pytest.skip("testler/hyperframes-baslik/vendor/gsap.min.js yok (depoda tutulmaz): zsh sistem/kur.sh kopyalar")
    if not list((Path.home() / ".cache" / "hyperframes" / "chrome").glob("chrome-headless-shell/mac_arm-*")):
        pytest.skip("HyperFrames'in Chrome'u yok: ilk çizim ~190 MB indirir (hyperframes browser ensure; sorarak)")
    if not all((HF_FIKSTUR / "ses" / f).exists() for f in ("cin.wav", "hisirti.wav")):    # *.wav depoda tutulmaz
        subprocess.run([sys.executable, str(HF_FIKSTUR / "ses" / "efekt.py")], check=True)  # sabit tohum: aynı dosya
    ortam = {**os.environ, "HYPERFRAMES_NO_TELEMETRY": "1", "HYPERFRAMES_NO_UPDATE_CHECK": "1",
             "HYPERFRAMES_NO_AUTO_INSTALL": "1", "HYPERFRAMES_SKIP_SKILLS": "1", "DO_NOT_TRACK": "1"}
    surum = subprocess.run([str(hf), "--version"], capture_output=True, text=True, env=ortam).stdout.strip()
    r = subprocess.run([str(hf), "lint", str(HF_FIKSTUR), "--json"], capture_output=True, text=True, env=ortam,
                       timeout=120)
    assert r.returncode == 0 and json.loads(r.stdout)["errorCount"] == 0, r.stdout[-1500:]
    cikti = tmp_path / "baslik.mp4"
    r = subprocess.run([str(hf), "render", str(HF_FIKSTUR), "--quality", "draft", "-o", str(cikti)],
                       capture_output=True, text=True, env=ortam, timeout=300)
    assert r.returncode == 0, (r.stdout + r.stderr)[-1500:]

    html = (HF_FIKSTUR / "index.html").read_text()
    sesler = {m["id"]: (m["src"], float(m["bas"])) for m in re.finditer(
        r'<audio id="(?P<id>[\w-]+)" src="(?P<src>[^"]+)" data-start="(?P<bas>[\d.]+)"', html)}
    assert len(sesler) == 2, sesler
    o = _hf_ozet(cikti, sesler)
    assert (o["genislik"], o["yukseklik"], o["fps"], o["kare"], o["ses_kodek"]) == (1920, 1080, "30/1", 150, "aac")
    assert abs(o["sure"] - 5.0) < 1 / 30
    for ad, (_, bas) in sesler.items():
        t = o["ses_baslangic"][ad]
        assert abs(t - bas) < 0.001, (ad, t, bas)                      # bildirilen anda
        assert abs(t * 30 - round(t * 30)) < 0.03, (ad, t * 30)        # kare ızgarasında (k/30)

    imza = hashlib.sha256(html.encode()).hexdigest()
    if os.environ.get("MEDYA_HF_BASVURU") == "yaz":
        HF_BASVURU.write_text(json.dumps({
            "aciklama": "testler/hyperframes-baslik taslak çiziminin başvurusu (test_temel.py _hf_ozet). Yeniden yaz: "
                        "MEDYA_HF_BASVURU=yaz medya test kompozisyon",
            "hyperframes": surum, "tarih": datetime.date.today().isoformat(), "fikstur_sha256": imza, **o},
            ensure_ascii=False, indent=1) + "\n")
        pytest.skip(f"başvuru yazıldı: HyperFrames {surum}")
    b = json.loads(HF_BASVURU.read_text())
    assert b["fikstur_sha256"] == imza, ("fikstür (index.html) başvurudan sonra değişti: sabit sürümle yeniden yaz "
                                          "(MEDYA_HF_BASVURU=yaz medya test kompozisyon)")
    assert len(o["kareler"]) == len(b["kareler"])
    fark = [int(np.abs(np.frombuffer(bytes.fromhex(x), np.uint8).astype(int) -
                       np.frombuffer(bytes.fromhex(y), np.uint8)).max()) for x, y in zip(o["kareler"], b["kareler"])]
    farkli = [i for i, f in enumerate(fark) if f > 3]
    assert not farkli, (f"HyperFrames {surum} çizimi başvurudan ({b['hyperframes']}) farklı: {len(farkli)} kare "
                        f"(ilkleri {farkli[:10]}), en büyük fark {max(fark)} düzey")


def test_satici_bagla_eski_kopyayi_yedekleyip_baglar(tmp_path, monkeypatch):
    """~/.claude/skills'te aynı adlı eski gerçek kopya (npx skills --copy) dururken sabit commit'ten kurulan kopya
    sessizce devre dışı kalır (kur.sh bagla gerçek klasörü atlar). satici.py: dogrula bunu söyler; bagla --uygula olmadan
    dokunmaz; --uygula önce yedekler ve arşivi sayar, sonra kaldırır ve bağlar (~/.agents/skills'te eski kopyası olanlar
    oraya da bağlanır); listede olmayana dokunmaz; içerik özeti elle düzenlemeyi yakalar. Sahte ev klasöründe, ağsız."""
    import importlib.util
    import tarfile
    spec = importlib.util.spec_from_file_location("satici", KOK / "sistem" / "claude" / "satici" / "satici.py")
    satici = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(satici)
    ev, bec = tmp_path / "ev", tmp_path / "beceriler"
    monkeypatch.setenv("HOME", str(ev))
    monkeypatch.setattr(satici, "BECERILER", bec)
    monkeypatch.setattr(satici, "YEDEK", tmp_path / "yedek")
    for ad in ("a", "b"):
        (bec / ad).mkdir(parents=True)
        (bec / ad / "SKILL.md").write_text(f"---\nname: {ad}\n---\nsabit\n")
    s = {"ad": "deneme", "commit": "0" * 40, "yollar": ["skills/a", "skills/b"], "sil": [], "baslik": None}
    s["ozet"] = satici._kurulu_ozet(s)
    monkeypatch.setattr(satici, "SATICI", [s])
    for k in (".claude/skills", ".agents/skills"):
        (ev / k / "a").mkdir(parents=True)
        (ev / k / "a" / "SKILL.md").write_text("eski\n")
    (ev / ".claude" / "skills" / "kendi").mkdir()                     # satıcı listesinde yok: dokunulmaz
    assert satici.dogrula() == 1
    assert satici.bagla() == 0 and (ev / ".claude" / "skills" / "a" / "SKILL.md").read_text() == "eski\n"
    assert satici.bagla(uygula=True) == 0
    for ad in ("a", "b"):
        assert (ev / ".claude" / "skills" / ad).is_symlink()
        assert (ev / ".claude" / "skills" / ad / "SKILL.md").read_text().endswith("sabit\n")
    ajan = ev / ".agents" / "skills" / "a"                            # başka ajanlar beceriyi kaybetmez: sabit kopyaya bağ
    assert ajan.is_symlink() and (ajan / "SKILL.md").read_text().endswith("sabit\n")
    assert not (ev / ".agents" / "skills" / "b").exists() and (ev / ".claude" / "skills" / "kendi").is_dir()
    arsiv, = (tmp_path / "yedek").glob("satici-yedek-*.tar.gz")
    with tarfile.open(arsiv) as t:
        assert sorted(m.name for m in t.getmembers() if m.isfile()) == [".agents/skills/a/SKILL.md",
                                                                        ".claude/skills/a/SKILL.md"]
    assert satici.dogrula() == 0
    (bec / "b" / "SKILL.md").write_text("elle düzenlendi\n")
    assert satici.dogrula() == 1


def test_satici_bagla_geri_alir(tmp_path, monkeypatch, capsys):
    """bagla --uygula'nın yazdırdığı geri alma komutu çalışır. Eski ileti (`tar -xzf <arşiv> -C ~`) çalışmıyordu:
    ~/.claude/skills/<ad> artık bağlantı; bsdtar 3.5.3 içine açmaz (çıkış 1, yalnız ~/.agents geri gelir), bağlantıyı
    izleyen açıcı (tarfile) eski içeriği sabit kopyanın üzerine yazar, çünkü sistem/claude/skills ev klasörünün içinde
    (2026-10-08 ölçüldü). geri: kuru çalıştırma dokunmaz; --uygula yalnız sabit kopyayı gösteren bağlantıyı kaldırır,
    kopyaları kipleriyle geri koyar, sabit kopyaya ve yerinde kalan kayıt dosyasına dokunmaz; yerde gerçek klasör varsa
    hiçbir şeyi değiştirmez. Sahte ev klasöründe (beceriler gerçek düzendeki gibi ev içinde), ağsız."""
    import importlib.util
    import os
    import re
    betik = KOK / "sistem" / "claude" / "satici" / "satici.py"
    spec = importlib.util.spec_from_file_location("satici", betik)
    satici = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(satici)
    ev = tmp_path / "ev"
    bec = ev / "Projects" / "video" / "sistem" / "claude" / "skills"
    monkeypatch.setenv("HOME", str(ev))
    monkeypatch.setattr(satici, "BECERILER", bec)
    monkeypatch.setattr(satici, "YEDEK", tmp_path / "yedek")
    (bec / "a").mkdir(parents=True)
    (bec / "a" / "SKILL.md").write_text("sabit\n")
    s = {"ad": "deneme", "commit": "0" * 40, "yollar": ["skills/a"], "sil": [], "baslik": None}
    s["ozet"] = satici._kurulu_ozet(s)
    monkeypatch.setattr(satici, "SATICI", [s])
    for k in (".claude/skills", ".agents/skills"):
        (ev / k / "a" / "scripts").mkdir(parents=True)
        (ev / k / "a" / "SKILL.md").write_text("eski\n")
        (ev / k / "a" / "scripts" / "x.sh").write_text("echo\n")
        (ev / k / "a" / "scripts" / "x.sh").chmod(0o755)
    kilit = ev / ".agents" / ".skill-lock.json"
    kilit.write_text('{"v": 1}\n')
    assert satici.bagla(uygula=True) == 0
    arsiv = Path(re.search(r"geri almak: python3 \S+ bagla --geri (\S+) --uygula\)", capsys.readouterr().out)[1])
    kilit.write_text('{"v": 2}\n')                                     # bagla'dan sonra değişen kayıt korunur
    assert satici.geri(arsiv) == 0 and (ev / ".claude" / "skills" / "a").is_symlink()     # kuru: dokunmaz
    assert satici.geri(arsiv, uygula=True) == 0
    for k in (".claude/skills", ".agents/skills"):
        assert not (ev / k / "a").is_symlink() and (ev / k / "a" / "SKILL.md").read_text() == "eski\n"
        assert (ev / k / "a" / "scripts" / "x.sh").stat().st_mode & 0o777 == 0o755
    assert (bec / "a" / "SKILL.md").read_text() == "sabit\n" and kilit.read_text() == '{"v": 2}\n'
    assert satici.dogrula() == 1                                       # eski kopya yine etkin
    (ev / ".claude" / "skills" / "a" / "SKILL.md").write_text("kullanıcı\n")
    assert satici.geri(arsiv, uygula=True) == 1                        # yerde gerçek klasör: üzerine yazılmaz
    assert (ev / ".claude" / "skills" / "a" / "SKILL.md").read_text() == "kullanıcı\n"
    ev2 = tmp_path / "ev2"                                             # yazdırılan komut biçimi (CLI), boş evde
    r = subprocess.run([sys.executable, str(betik), "bagla", "--geri", str(arsiv), "--uygula"],
                       capture_output=True, text=True, env={**os.environ, "HOME": str(ev2)})
    assert r.returncode == 0, r.stdout + r.stderr
    assert (ev2 / ".claude" / "skills" / "a" / "SKILL.md").read_text() == "eski\n"


def test_senkron_plan_sozlesmesi_ve_cizimden_olcum(veri):
    """muzik.bas = müzik dosyasında videonun 0. sn'sine denk gelen an (video vuruşu = müzik vuruşu − bas; medya nle
    ile aynı). Plan verilse de kesimler ÇİZİMDEN ölçülür; çizimde olmayan planlı kesim 'olculemedi' olur."""
    from medya.komutlar.senkron import senkron
    g = veri["muzik_davullu"]
    kaymis = {"vuruslar": [t + 1.0 for t in g["vuruslar"]], "olcu_baslari": [], "guven": 0.95}   # şarkının 1. sn'si = video 0
    kesim = veri["kesimli"]["kesimler"]
    plan = {"fps": 30, "muzik": {"bas": 1.0}, "cekimler": [{"cikti_bas": 0.0}] +
            [{"cikti_bas": t, "vurusa": True} for t in kesim]}
    r = senkron(str(VERI / "kesimli.mp4"), kaymis, plan)
    assert r["karar"] == "vurusta" and not r["olculemedi"], r
    yanlis = {**plan, "cekimler": [{"cikti_bas": 0.0}] + [{"cikti_bas": t + 0.5, "vurusa": True} for t in kesim]}
    r = senkron(str(VERI / "kesimli.mp4"), kaymis, yanlis)                 # plan çizimle uyuşmuyor
    assert len(r["olculemedi"]) == len(kesim) and r["karar"] != "vurusta"


def test_denetle_planli_siyah_dip_kusur_sayilmaz():
    from medya.komutlar.denetle import denetle
    plan = {"fps": 30, "cekimler": [{"no": 1, "cikti_bas": 0.0, "cikti_son": 8.0, "ses": "muzik"},
                                    {"no": 2, "cikti_bas": 8.0, "cikti_son": 20.0, "ses": "muzik",
                                     "gecis": {"tur": "siyah-dip", "sure_kare": 2}}]}
    k = denetle(str(VERI / "kusurlu.mp4"), plan=plan, hedef="arsiv")["denetimler"]
    assert k["siyah"]["gecti"] and k["siyah"]["planli"] and k["flas"]["gecti"] and k["flas"]["planli"]
    k = denetle(str(VERI / "kusurlu.mp4"), hedef="arsiv")["denetimler"]   # plansız: aynı kare kusurdur
    assert not k["siyah"]["gecti"] and not k["flas"]["gecti"]


def test_inceleme_bulgulari_cli_hatalari(tmp_path, capsys):
    """Beceri inceleyicilerinin bulduğu CLI hataları (2026-10-05): av hizası kaynak_bas<0,5'te 500 ms yanlış; renk
    etiketi yanlış alandan okunuyordu; kontak/denetle görselde anlaşılmaz çöküyordu."""
    from medya.cli import ana
    from medya.komutlar.denetle import _av_hizasi, denetle
    v = str(VERI / "karisik_ses.mp4")
    h = _av_hizasi(v, v, 0.0, 5.0, 0.0)                                   # kendisiyle, baştan: gecikme 0
    assert not h.get("olculemedi") and abs(h["gecikme_ms"]) < 2, h
    etiketli = tmp_path / "e.mp4"
    subprocess.run([str(KOK / "arac" / "ffmpeg"), "-nostdin", "-v", "error", "-y", "-i", str(VERI / "kesimli.mp4"),
                    "-t", "2", "-c:v", "libx264", "-colorspace", "bt709", "-color_primaries", "bt709",
                    "-color_trc", "bt709", "-c:a", "aac", str(etiketli)], check=True)
    t = denetle(str(etiketli), hedef="arsiv")["denetimler"]["teknik"]
    assert not any("renk etiketleri boş" in b for b in t["bulgular"]), t["bulgular"]
    from PIL import Image
    Image.new("RGB", (64, 48), (200, 50, 50)).save(tmp_path / "g.png")
    for komut in (["kontak", str(tmp_path / "g.png")], ["denetle", str(tmp_path / "g.png")]):
        assert ana(komut) != 0
        cikti = capsys.readouterr()
        assert "video içindir" in cikti.err + cikti.out


def test_ses_temizle_videoda_kare_kaybetmez(tmp_path):
    """-shortest sondan kare kesiyordu (553 → 549): temizlenmiş ses videoya eklenince kare sayısı korunmalı."""
    from medya.komutlar.ses_temizle import ses_temizle
    from medya.komutlar.ses_temizle import DF
    if not Path(DF).exists():
        pytest.skip("DeepFilterNet yok")
    girdi = VERI / "karisik_ses.mp4"
    ses_temizle(str(girdi), str(tmp_path / "t.mp4"))
    say = lambda f: int(subprocess.run([str(KOK / "arac" / "ffprobe"), "-v", "error", "-count_frames", "-select_streams",
                                        "v:0", "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(f)],
                                       capture_output=True, text=True).stdout.strip())
    assert say(tmp_path / "t.mp4") == say(girdi)


def test_kayit_birincil_saglayicilar_kurulu():
    """Sessiz yedeğe düşmeyi yakalar: 2026-10-05'te cv2 silinmişti, 'medya sahneler' fark edilmeden ffmpeg yedeğiyle
    çalışıyordu (sınama yedekle de geçiyordu). Her yeteneğin birincil (etkin) sağlayıcısı kurulu olmalı."""
    from medya.kayit import yukle
    yetenekler, saglayicilar = yukle()
    eksik = [f"{y.ad}: {y.saglayici}" for y in yetenekler.values()
             if saglayicilar[y.saglayici].etkin and not saglayicilar[y.saglayici].kurulu_mu()]
    assert not eksik, f"birincil sağlayıcı kurulu değil: {eksik}"


def test_python_ortamlari_studyonun_yorumlayicisinda():
    """2026-10-08'e dek mflux ortamı stüdyo dışındaki python.org 3.13.1'e bağlıydı (sistem `python3` 3.14'e geçmişti):
    o kaldırılınca `gorsel-uret` bozulur, `ls` denetimi kopuk bağı görmezdi. Her ortam .uv/python altındaki uv
    Python'unu kullanmalı (yeniden kurulum: --managed-python)."""
    yonetilen = (KOK / ".uv" / "python").resolve()
    sorunlu = []
    for o in [KOK / ".venv", *(KOK / "ortamlar").glob("*"), *(KOK / ".uv" / "tools").glob("*")]:
        if (o / "pyvenv.cfg").exists():
            py = (o / "bin" / "python").resolve()
            if not (py.is_relative_to(yonetilen) and py.exists()):
                sorunlu.append(f"{o.relative_to(KOK)} → {py}")
    assert not sorunlu, f"stüdyo dışı ya da kopuk yorumlayıcı: {sorunlu}"


def test_gorsel_ortami_kisit_dosyasina_esit():
    """Yeni makinede ve onarımda aynı paketler kurulur: kayıt komutu depodaki kısıt dosyasını kullanıyor ve kurulu
    ortam onunla birebir aynı (paket kayması = aynı tohumda başka görsel; `uv tool upgrade` bunu sessizce yapar)."""
    from medya.kayit import yukle
    kisit = KOK / "sistem" / "kisitlar" / "mflux-0.21.0.txt"
    s = yukle()[1]["flux2-klein"]
    assert "--managed-python" in s.kurulum and f"-c {kisit.relative_to(KOK)} " in s.kurulum and kisit.exists()
    py = KOK / ".uv" / "tools" / "mflux" / "bin" / "python"
    if not py.exists():
        pytest.skip("flux2-klein kurulu değil: medya kur flux2-klein")
    kurulu = subprocess.run([str(KOK / "arac" / "uv"), "pip", "freeze", "--python", str(py)], capture_output=True,
                            text=True, check=True).stdout.splitlines()
    assert kurulu == [satir for satir in kisit.read_text().splitlines() if satir.strip() and not satir.startswith("#")]


def test_senkron_cizimdeki_ses_kaymasini_yakalar(veri, tmp_path):
    """Kesimler vuruşta ama çizimin sesi 40 ms kaymışsa 'vurusta' DENMEZ (2026-10-04 'sesler kaymış'ın ikinci yolu)."""
    from medya.komutlar.senkron import senkron
    g = veri["muzik_davullu"]
    wav = VERI / "muzik_davullu.wav"
    muzik = {"vuruslar": g["vuruslar"], "olcu_baslari": g["olcu_baslari"], "guven": 0.95, "ana_wav": str(wav)}
    ff = str(KOK / "arac" / "ffmpeg")
    for ad, kayma in (("hizali", "0"), ("kaymis", "0.040")):
        subprocess.run([ff, "-nostdin", "-v", "error", "-y", "-i", str(VERI / "kesimli.mp4"), "-itsoffset", kayma,
                        "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "pcm_s16le", "-shortest",
                        str(tmp_path / f"{ad}.mov")], check=True)
    r = senkron(str(tmp_path / "hizali.mov"), muzik)
    assert r["karar"] == "vurusta" and abs(r["ses_hizasi"]["gecikme_ms"]) <= 2, r.get("ses_hizasi")
    r = senkron(str(tmp_path / "kaymis.mov"), muzik)
    assert r["karar"] == "kayik" and 35 <= r["ses_hizasi"]["gecikme_ms"] <= 45, r.get("ses_hizasi")


def test_ustala_davullu_hedefe_yaklasir_ve_hedefteyse_kopyalar(tmp_path):
    """Uçtan uca deneme: davul ağırlıklı müzikte ustala −14'e ulaşamıyordu (kazanç her turda baştan hesaplanıyor,
    sınırlayıcının yuttuğu geri konmuyordu) ve kazanç 0 iken de sesi yeniden kodluyordu."""
    from medya.komutlar.ustala import ustala
    r = ustala(str(VERI / "muzik_davullu.wav"), str(tmp_path / "y.wav"), hedef=-12.0, tepe=-1.5)    # 5,3 dB yukarı
    assert abs(r["sonra"]["lufs"] + 12.0) <= 0.5 and r["sonra"]["tepe_dbtp"] <= -1.45, r
    r2 = ustala(str(tmp_path / "y.wav"), str(tmp_path / "z.wav"), hedef=-12.0, tepe=-1.5)
    assert r2.get("kopya") and r2["gecti"]


def test_turkce_normallestirme_ve_cer():
    """Ortak Türkçe metin modülü (TTS kabulü): İ/ı büyük-küçük, sayılar yazıyla, kesme işareti, noktalama."""
    from medya.turkce import karsilastir, normallestir, sayi_yaziya
    assert normallestir("İZMİR'de 9'da %50 indirim, 1.500 TL; saat 10:30!") == \
        "izmirde dokuzda yüzde elli indirim bin beş yüz tl saat on otuz"
    assert sayi_yaziya(250) == "iki yüz elli" and sayi_yaziya(1000) == "bin" and sayi_yaziya(2026) == "iki bin yirmi altı"
    assert karsilastir("Işıklı Çarşı'da 3 saat", "ışıklı çarşıda üç saat")["cer"] == 0.0
    assert karsilastir("kayıt düğmesi", "kayıt dügmesi")["cer"] > 0


def test_seslendir_cumle_bolme_ve_riza_kapisi():
    from medya.komutlar.seslendir import cumlelere_bol, seslendir
    from medya.ortak import MedyaHatasi
    assert cumlelere_bol("Merhaba. Bugün güzel bir gün! Saat 10:30'da başlıyoruz.\n\nİkinci paragraf geliyor.") == [
        ("Merhaba. Bugün güzel bir gün!", False), ("Saat 10:30'da başlıyoruz.", True), ("İkinci paragraf geliyor.", True)]
    with pytest.raises(MedyaHatasi, match="rıza"):
        seslendir("Deneme cümlesi.", "/tmp/x.wav", referans="/tmp/yok.wav")     # --rizali olmadan klon yok


def test_seslendir_modeli_kayittaki_8bit():
    """2026-10-08: varsayılan VoxCPM2 8-bit oldu, 4-bit silindi. Kod başka bir modele bakarsa ağır sınama "kurulu değil"
    diye ATLANIR (sessiz): kodun modeli, kaydın kurduğu ve denetlediği anlık görüntü olmalı; kuruluysa 8 bit."""
    from medya.kayit import yukle
    from medya.komutlar.seslendir import MODEL
    s = yukle()[1]["voxcpm2"]
    assert MODEL.parent.parent.name == "models--mlx-community--VoxCPM2-8bit"
    assert f"s('mlx-community/VoxCPM2-8bit', revision='{MODEL.name}')" in s.kurulum
    assert f"{MODEL.relative_to(KOK)}/" in s.kontrol
    if MODEL.exists():
        assert json.loads((MODEL / "config.json").read_text())["quantization"]["bits"] == 8


def test_seslendir_turkce_anlasilir_ve_tutarli(tmp_path, agir):
    """Uçtan uca: kimlik üret → iki cümle → Whisper CER ve ECAPA benzerliği kapıdan geçer, zaman çizelgesi sıralı."""
    from medya.komutlar.seslendir import MODEL, seslendir
    from medya.ortak import probe
    if not MODEL.exists():
        pytest.skip("VoxCPM2 kurulu değil: medya kur voxcpm2")
    r = seslendir("Bugün yeni özelliğimizi tanıtıyoruz. Kayıt düğmesine iki saniye basılı tutun.",
                  str(tmp_path / "vo.wav"), deneme=1)
    d = r["dogrulama"]
    assert d["gecti"] and d["toplam_cer"] <= 0.03 and d["benzerlik_min"] >= 0.5, d
    s = next(x for x in probe(tmp_path / "vo.wav")["streams"] if x["codec_type"] == "audio")
    assert s["sample_rate"] == "48000" and s["channels"] == 1
    z = r["cumleler"]
    assert len(z) == 2 and 0 <= z[0]["bas"] < z[0]["son"] < z[1]["bas"] < z[1]["son"] <= r["sure"] + 0.01
    assert (tmp_path / "vo-kimlik.wav").exists() and (tmp_path / "vo-kimlik.json").exists()


def test_gorsel_uret_modelleri_kayitla_ayni():
    """Kodun baktığı anlık görüntü, kaydın kurduğu (repo + commit) ve denetlediği yol olmalı; yoksa ağır sınama "kurulu
    değil" diye sessizce ATLANIR (E1'deki VoxCPM2 dersi). İki model de gorsel-uret yeteneğine bağlı (birincil +
    yedek)."""
    from medya.kayit import yukle
    from medya.komutlar.gorsel_uret import MODELLER
    yetenekler, saglayicilar = yukle()
    y = yetenekler["gorsel-uret"]
    assert sorted([y.saglayici, *y.yedek]) == sorted(MODELLER)
    for ad, m in MODELLER.items():
        s = saglayicilar[ad]
        repo = m["yol"].parent.parent.name.removeprefix("models--").replace("--", "/")
        assert f"s('{repo}', revision='{m['yol'].name}')" in s.kurulum, ad
        assert f"{m['yol'].relative_to(KOK)}/" in s.kontrol and f"arac/{m['uret'].name} " in s.kontrol, ad


def test_gorsel_uret_referans_yalniz_flux2():
    """Z-Image'ın düzenleme modeli yok (Z-Image-Edit yayımlanmadı, 2026-10-08): --referans her zaman FLUX.2'ye gider,
    `--model z-image --referans` model çalışmadan hata verir. --model'siz sıra kayıttan (birincil, sonra yedek)."""
    from medya.kayit import yukle
    from medya.komutlar.gorsel_uret import gorsel_uret, model_sirasi
    from medya.ortak import MedyaHatasi
    assert model_sirasi(referans=["a.png"]) == model_sirasi("flux2", ["a.png"]) == ["flux2-klein"]
    assert model_sirasi("z-image") == ["z-image-turbo"] and model_sirasi("flux2") == ["flux2-klein"]
    y = yukle()[0]["gorsel-uret"]
    assert model_sirasi() == [y.saglayici, *y.yedek]
    with pytest.raises(MedyaHatasi, match="Z-Image"):
        gorsel_uret("x", "/tmp/x.png", model="z-image", referans=["/tmp/yok.png"])
    with pytest.raises(MedyaHatasi, match="bilinmeyen model"):
        model_sirasi("flux1")


def test_gorsel_uret_birincil_basarisizsa_yedege_duser(tmp_path, monkeypatch, capsys):
    """--model'siz çağrıda birincilin üretimi hata verirse (ör. bellek) kayıttaki yedekle uyarıyla yeniden denenir;
    --model verilince başka modele geçilmez. Model çalıştırılmaz (üretim sahte)."""
    import medya.komutlar.gorsel_uret as G
    from medya.kayit import Saglayici, yukle
    from medya.ortak import MedyaHatasi
    y = yukle()[0]["gorsel-uret"]
    denenen = []

    def sahte(ad, *a, **k):
        denenen.append(ad)
        if ad == y.saglayici:
            raise MedyaHatasi(f"görsel üretimi başarısız ({ad})")
        return [{"saglayici": ad}]

    monkeypatch.setattr(G, "_uret", sahte)
    monkeypatch.setattr(G, "disk_bekcisi", lambda *a: None)
    monkeypatch.setattr(Saglayici, "kurulu_mu", lambda self: True)
    assert G.gorsel_uret("x", str(tmp_path / "a.png"))[0]["saglayici"] == y.yedek[0]
    assert denenen == [y.saglayici, *y.yedek] and "yeniden deneniyor" in capsys.readouterr().err
    denenen.clear()
    with pytest.raises(MedyaHatasi):
        G.gorsel_uret("x", str(tmp_path / "b.png"), model={v: k for k, v in G.KISA.items()}[y.saglayici])
    assert denenen == [y.saglayici]


@pytest.mark.parametrize("model", ["flux2", "z-image"])
def test_gorsel_uret_tohumla_ayni_ve_lisans_kaydi(tmp_path, agir, model):
    """Her model: aynı istem + tohum = piksel piksel aynı görsel (FLUX.2 2026-10-07, Z-Image 2026-10-08 ölçüldü);
    üretim kaydında sağlayıcı, lisans ve tohum."""
    import numpy as np
    from PIL import Image
    from medya.komutlar.gorsel_uret import KISA, MODELLER, gorsel_uret
    ad = KISA[model]
    if not MODELLER[ad]["yol"].exists():
        pytest.skip(f"{ad} kurulu değil: medya kur {ad}")
    for f in ("a.png", "b.png"):
        k = gorsel_uret("A red bicycle leaning on a blue wall", str(tmp_path / f), model=model, boyut="256x256",
                        adim=2, tohum=3)[0]
        assert k["saglayici"] == ad and "Apache-2.0" in k["lisans"] and k["tohum"] == 3 and k["adim"] == 2
    x, y = (np.asarray(Image.open(tmp_path / f).convert("RGB"), dtype=np.int16) for f in ("a.png", "b.png"))
    assert x.shape == (256, 256, 3) and x.std() > 10 and int(np.abs(x - y).max()) == 0
