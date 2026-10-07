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
def _kareler(yol, w=640, h=360):
    """Videonun bütün karelerini gri ve küçültülmüş olarak doğrudan çözer (sıra = kare sırası).
    ffmpeg'in psnr süzgeci zaman damgası farklı akışlarda kare kaydırabildiği için kullanılmaz."""
    import subprocess
    import numpy as np
    from medya.ortak import ffmpeg
    r = subprocess.run([ffmpeg(), "-nostdin", "-v", "error", "-i", str(yol), "-vf", f"scale={w}:{h}:flags=area,format=gray",
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
    from medya.komutlar.yavaslat import RIFE, yavaslat
    if not RIFE.exists():
        pytest.skip("RIFE kurulu değil: medya kur rife")
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
