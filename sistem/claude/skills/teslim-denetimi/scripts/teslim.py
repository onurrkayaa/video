#!/usr/bin/env python3
"""teslim.py — platform teslim kodlaması ve uygunluk denetimi (teslim-denetimi becerisi).

Çalıştır:  source /Users/onurkaya/Projects/video/ortam.sh && $MEDYA/.venv/bin/python <beceri>/scripts/teslim.py …

  kodla <usta> --hedef dikey|youtube|whatsapp|kucuk|apple --cikti X.mp4 [--ses usta.wav] [--mb N] [--boyut GxY]
      Ustadan platform dosyası (ön ayarlar: delivery-qa.md T5), ardından kendiliğinden `uygunluk --usta`.
      Üst veriyi siler ve moov'u başa alır (bitexact + faststart): kodlanan teslimin SON yazma adımıdır.
      kucuk = boyut sınırlı iş/e-posta kopyası (1080p, ustanın fps'i, iki geçiş, --mb zorunlu). Sınır aşılırsa
      bir kez daha düşük bit hızıyla kodlar.
  uygunluk <dosya> --hedef dikey|youtube|whatsapp|kucuk|apple|hdr [--usta U] [--mb N] [--boyut GxY] [--vmaf]
      `medya denetle`nin bakmadıkları: akışlar, kodek/profil/seviye/etiket, SAR, CFR, renk etiketleri, dönüş,
      ses biçimi, A/V başlangıç/süre, GOP, moov, boyut sınırı, üst veri (etiket + bayt + exiftool), çözme
      hatası, parlaklık kırpılması. --usta: ses kayması (ms), kare sayısı, kare kayması; --vmaf (hizalıysa).
  guvenli <dikey.mp4> --cikti sayfa.png [--analiz medya-analiz.json]
      9:16 güvenli alan temas sayfası; --analiz ile yüz merkezlerinin güvenli kutudaki oranı (kare açmadan).

Durum: gecti | kaldi | inceleme (eşik sezgisel ya da öneri) | olculemedi. Çıkış: 0 geçti, 1 kaldı, 2 girdi hatası.
Teslim dosyasının üzerine yazmaz. Rapor: <dosyanın klasörü>/denetim/<ad>-uygunluk.json.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, os.environ.get("MEDYA", "/Users/onurkaya/Projects/video"))
from medya.ortak import (ARAC, MedyaHatasi, calistir, ffmpeg, ffprobe, oran, probe,  # noqa: E402
                         ses_akisi, ses_gecikmesi, video_akisi)

SDR = ("bt709", "bt709", "bt709", "tv")
HDR = ("bt2020", "arib-std-b67", "bt2020nc", "tv")
ON = {  # delivery-qa.md T5; seviye 1080p sınıfı için taban, büyük karede seviye_sec yükseltir
    "dikey": dict(boyut=(1080, 1920), kodek="h264", profil="High", seviye=42, crf=17, gop=0.5, ses=("aac_at", "320k")),
    "youtube": dict(boyut=(1920, 1080), kodek="h264", profil="High", seviye=42, crf=16, gop=0.5, ses=("aac", "384k")),
    "whatsapp": dict(boyut=(720, 1280), kodek="h264", profil="High", seviye=40, gop=2.0, ses=("aac_at", "128k")),
    "kucuk": dict(boyut=(1080, 1920), kodek="h264", profil="High", seviye=42, gop=2.0, ses=("aac_at", "128k")),
    "apple": dict(boyut=None, kodek="hevc", profil="Main", etiket="hvc1", gop=2.0, ses=("aac_at", "320k")),
    "hdr": dict(boyut=None, kodek="hevc", profil="Main 10", etiket="hvc1", gop=2.0, pix="yuv420p10le", renk=HDR),
}
SEVIYE = ((40, 8192, 245760), (41, 8192, 245760), (42, 8704, 522240), (50, 22080, 589824),
          (51, 36864, 983040), (52, 36864, 2073600))           # H.264 Tablo A-1: (seviye, MaxFS, MaxMBPS)
IZINLI = {"major_brand", "minor_version", "compatible_brands", "language", "handler_name", "vendor_id"}
FFMPEG_SURUMU = re.compile(r"Lav[fc][\d.]*( [\w-]+)?")       # encoder=Lavf60.3.100: kişisel değil
KISISEL = re.compile(r"gps|location|make|model|software|serial|lens|comment|title|artist|author", re.I)
IZLER = (b"ISO6709", b"com.apple.quicktime", b"hyperframes")  # konum, iPhone, HyperFrames kaynak etiketi


def calis(komut: list[str]) -> subprocess.CompletedProcess:
    """Hata saymadan çalıştırır (çözme hatası ve exiftool çıktısı okunur)."""
    return subprocess.run(komut, capture_output=True, stdin=subprocess.DEVNULL)


def seviye_sec(taban: int, w: int, h: int, fps: float) -> int:
    mb = -(-w // 16) * -(-h // 16)
    for s, fs, mbps in SEVIYE:
        if s >= taban and mb <= fs and mb * fps <= mbps:
            return s
    raise MedyaHatasi(f"{w}x{h}@{fps:g} H.264 seviye 5.2'yi aşıyor")


def donus(v: dict) -> int:
    for sd in v.get("side_data_list") or []:
        if "rotation" in sd:
            return int(round(float(sd["rotation"])))
    return int((v.get("tags") or {}).get("rotate", 0) or 0)


def kutular(yol: str) -> list[str]:
    """MP4/MOV üst düzey kutu sırası (faststart: moov, mdat'tan önce)."""
    sira = []
    with open(yol, "rb") as f:
        while len(h := f.read(8)) == 8:
            boy, tip = struct.unpack(">I4s", h)
            sira.append(tip.decode("latin-1"))
            if boy == 1:
                f.seek(struct.unpack(">Q", f.read(8))[0] - 16, 1)
            elif boy == 0:
                break
            else:
                f.seek(boy - 8, 1)
    return sira


def anahtar_kareler(yol: str) -> list[float]:
    s = calis([ffprobe(), "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,flags",
               "-of", "csv=p=0", yol])
    return sorted(float(t) for t, _, b in (x.partition(",") for x in s.stdout.decode().split())
                  if "K" in b and t not in ("", "N/A"))


def luma_dizisi(yol: str) -> np.ndarray:
    """Kare sırasıyla 32x32 gri ortalama (zaman damgasına göre kare atılmaz/çoğaltılmaz)."""
    s = calis([ffmpeg(), "-nostdin", "-v", "error", "-i", yol, "-an", "-vf", "scale=32:32,format=gray",
               "-fps_mode", "passthrough", "-f", "rawvideo", "-"])
    return np.frombuffer(s.stdout, np.uint8).reshape(-1, 32 * 32).mean(1)


def kare_kaymasi(ref: np.ndarray, x: np.ndarray, en_cok: int = 15) -> tuple[int, float]:
    """x'in ref'e göre kaç kare geç olduğu (pozitif = geç) ve normalize ilinti."""
    n = min(len(ref), len(x))
    ref, x = ref[:n] - ref[:n].mean(), x[:n] - x[:n].mean()
    m = 1 << int(np.ceil(np.log2(2 * n)))
    c = np.fft.irfft(np.fft.rfft(x, m) * np.conj(np.fft.rfft(ref, m)), m)
    aday = np.concatenate([c[-en_cok:], c[:en_cok + 1]])
    j = int(np.argmax(aday))
    return j - en_cok, float(aday[j] / (np.sqrt((ref ** 2).sum() * (x ** 2).sum()) + 1e-12))


def cozme_ve_luma(yol: str, sdr: bool) -> tuple[list[str], dict | None]:
    """Tek tam çözme: bütün akışların çözme hataları + (SDR'de) kırpılma. YHIGH/YLOW 90./10. yüzdeliktir:
    YHIGH ≥ 234 → karenin ≥ %10'u beyazda kırpık; YLOW ≤ 17 → ≥ %10'u ezik siyah; YMIN < 16 ya da YMAX > 235 →
    yasal aralık dışı kare (delivery-qa QC5; 480 px'e küçültülmüş karede ölçülür)."""
    komut = [ffmpeg(), "-nostdin", "-v", "error", "-i", yol, "-map", "0"]
    if sdr:
        komut += ["-vf", "scale=480:-2:flags=area,signalstats,metadata=mode=print:file=-"]
    s = calis(komut + ["-f", "null", "-"])
    hata = s.stderr.decode("utf-8", "replace").strip().splitlines()
    if not sdr:
        return hata, None
    d = {k: [float(x) for x in re.findall(rf"lavfi\.signalstats\.{k}=([\d.]+)", s.stdout.decode())]
         for k in ("YHIGH", "YLOW", "YAVG", "YMIN", "YMAX")}
    n = max(1, len(d["YAVG"]))
    return hata, {"beyaz": sum(x >= 234 for x in d["YHIGH"]) / n, "siyah": sum(x <= 17 for x in d["YLOW"]) / n,
                  "yavg": float(np.mean(d["YAVG"] or [0])),
                  "aralik": sum(a < 16 or b > 235 for a, b in zip(d["YMIN"], d["YMAX"])) / n}


def ust_veri(yol: str, p: dict) -> list[str]:
    fazla = [f"{k}={x}" for s in [p["format"], *p["streams"]] for k, x in (s.get("tags") or {}).items()
             if k not in IZINLI and not (k == "encoder" and FFMPEG_SURUMU.fullmatch(str(x)))]
    izler, onceki = set(IZLER), b""
    with open(yol, "rb") as f:                   # parça parça: çok GB'lık dosya belleğe alınmaz
        while parca := f.read(16 << 20):
            pencere = onceki + parca
            bulunan = {iz for iz in izler if iz in pencere}
            fazla += [f"bayt:{iz.decode()}" for iz in sorted(bulunan)]
            izler -= bulunan
            onceki = parca[-32:]
    if (ARAC / "exiftool").exists():
        for satir in calis([str(ARAC / "exiftool"), "-a", "-G1", "-s", "-ee", yol]).stdout.decode("utf-8", "replace").splitlines():
            m = re.match(r"\[(\w+)\]\s+(\S+)\s+: (.*)", satir)
            if m and m[1] not in ("System", "File", "ExifTool") and (
                    KISISEL.search(m[2]) or ("Date" in m[2] and not m[3].startswith("0000:00:00"))):
                fazla.append(f"{m[1]}:{m[2]}={m[3][:40]}")
    return fazla


def uygunluk(yol: str, hedef: str, usta: str | None = None, mb: float | None = None, vmaf: bool = False,
             boyut: tuple[int, int] | None = None) -> dict:
    on, p = ON[hedef], probe(yol)
    v, a = video_akisi(p), ses_akisi(p)
    if not v:
        raise MedyaHatasi("video akışı yok")
    B: list[dict] = []

    def ekle(ad: str, durum: str, ayrinti: str = "") -> None:
        B.append({"ad": ad, "durum": durum, "ayrinti": ayrinti})

    def kosul(ad: str, ok: bool, ayrinti: str = "") -> None:
        ekle(ad, "gecti" if ok else "kaldi", ayrinti)

    turler = [s.get("codec_type") for s in p["streams"]]
    kosul("akislar", turler.count("video") == 1 and len(turler) == 1 + turler.count("audio") <= 2,
          f"{turler} (fazlası mebx/APAC/veri izi olabilir)")
    if not a:
        ekle("ses", "inceleme", "ses akışı yok — sessiz teslim bilinçli mi?")
    r_fps, fps = oran(v.get("r_frame_rate")), oran(v.get("avg_frame_rate")) or 30.0
    w, h = int(v["width"]), int(v["height"])
    kosul("kodek", v.get("codec_name") == on["kodek"] and v.get("profile") == on["profil"]
          and ("etiket" not in on or v.get("codec_tag_string") == on["etiket"]),
          f"{v.get('codec_name')} {v.get('profile')} {v.get('codec_tag_string')}")
    if on["kodek"] == "h264":
        sev = seviye_sec(on["seviye"], w, h, fps)
        kosul("seviye", int(v.get("level") or 99) <= sev, f"{v.get('level')} (en çok {sev})")
    kosul("pix_fmt", v.get("pix_fmt") == on.get("pix", "yuv420p"), str(v.get("pix_fmt")))
    beklenen = boyut or on["boyut"]
    if not boyut and hedef == "youtube" and (w, h) == (3840, 2160):
        beklenen = (3840, 2160)
    if not boyut and hedef in ("whatsapp", "kucuk") and w > h:
        beklenen = on["boyut"][::-1]
    if beklenen is None and usta:
        uv = video_akisi(probe(usta)) or {}
        beklenen = (int(uv.get("width", 0)), int(uv.get("height", 0)))
    if beklenen:
        kosul("boyut", (w, h) == tuple(beklenen), f"{w}x{h} (beklenen {beklenen[0]}x{beklenen[1]})")
    kosul("sar", v.get("sample_aspect_ratio") in (None, "1:1", "0:1"),
          f"{v.get('sample_aspect_ratio')} (16:9→9:16 doğrudan ölçek 256:81 yapar)")
    kosul("cfr", abs(r_fps - fps) <= 0.01, f"r={v.get('r_frame_rate')} avg={v.get('avg_frame_rate')}")
    renk = (v.get("color_primaries"), v.get("color_transfer"), v.get("color_space"), v.get("color_range"))
    kosul("renk", renk == on.get("renk", SDR), "/".join(map(str, renk)))
    kosul("donus", donus(v) == 0, f"{donus(v)}° (teslim yeniden kodlanır; akış kopyasında matrisi sıfırlama: yan oynar)")
    kosul("alan", v.get("field_order") in (None, "progressive", "unknown"), str(v.get("field_order")))
    if a:
        ok = (a.get("codec_name"), a.get("profile"), a.get("channels")) == ("aac", "LC", 2)
        ekle("ses_bicimi", "kaldi" if not ok else ("gecti" if a.get("sample_rate") == "48000" else "inceleme"),
             f"{a.get('codec_name')} {a.get('profile')} {a.get('sample_rate')} Hz {a.get('channels')} kanal")
        bv, ba = float(v.get("start_time") or 0), float(a.get("start_time") or 0)
        kosul("av_baslangic", abs(bv - ba) <= 1 / fps + 1e-6, f"video {bv:.3f} / ses {ba:.3f} sn (sınır 1 kare)")
        dv, da = float(v.get("duration") or 0), float(a.get("duration") or 0)
        kosul("av_sure", abs(dv - da) <= 0.050, f"video {dv:.3f} / ses {da:.3f} sn (sınır 50 ms)")
    kk = anahtar_kareler(yol)
    # son anahtar kareden dosya sonuna kadarki GOP da sayılır (uçtan uca denetim: 3,73 yazıyordu, gerçek 7,50 sn)
    bosluk = float(np.max(np.diff(np.append(kk, float(p["format"]["duration"]))))) if len(kk) else float(p["format"]["duration"])
    ekle("gop", "gecti" if bosluk <= on["gop"] + 0.5 / fps else "inceleme",
         f"en büyük anahtar kare aralığı {bosluk:.2f} sn (ön ayar {on['gop']})")
    sira = kutular(yol)
    kosul("faststart", "moov" in sira and "mdat" in sira and sira.index("moov") < sira.index("mdat"), " ".join(sira))
    boy_mb = int(p["format"].get("size", 0)) / 1e6
    if mb:
        kosul("dosya_boyutu", boy_mb <= mb, f"{boy_mb:.2f} MB (sınır {mb} MB)")
    fazla = ust_veri(yol, p)
    kosul("ust_veri", not fazla, "; ".join(fazla[:8]) or "yalnız zararsız etiketler")
    hata, L = cozme_ve_luma(yol, on.get("renk", SDR) == SDR)
    kosul("cozme", not hata, f"{len(hata)} hata satırı" + (f": {hata[0][:120]}" if hata else ""))
    if L:
        ekle("luma", "gecti" if L["beyaz"] <= 0.02 and L["siyah"] <= 0.05 and L["aralik"] <= 0.01 else "inceleme",
             f"beyaz kırpık kare %{100 * L['beyaz']:.1f} (≤2), ezik siyah kare %{100 * L['siyah']:.1f} "
             f"(≤5; gece/bilinçli beyaz olabilir), aralık dışı (Y<16/>235) kare %{100 * L['aralik']:.1f} (≤1), "
             f"YAVG ort {L['yavg']:.1f}")
    if usta:
        ustaya_gore(yol, usta, hedef, fps, a, vmaf, ekle, kosul)
    return {"dosya": yol, "hedef": hedef, "boyut_mb": round(boy_mb, 2), "sure": float(p["format"]["duration"]),
            "denetimler": B, "gecti": all(b["durum"] != "kaldi" for b in B)}


def ustaya_gore(yol, usta, hedef, fps, a, vmaf, ekle, kosul) -> None:
    """Teslim ustayla aynı kurgu mu: ses kayması (3 pencere), kare sayısı, kare kayması; hizalıysa VMAF."""
    up = probe(usta)
    uv, ua = video_akisi(up), ses_akisi(up)
    if a and ua:
        sure = min(float(probe(yol)["format"]["duration"]), float(up["format"]["duration"]))
        pen = min(4.0, sure / 4)
        olcum = [ses_gecikmesi(usta, yol, sr=16000, bas=max(0.0, k * sure - pen / 2), sure=pen)
                 for k in (0.1, 0.5, 0.9)]
        gecerli = [o["gecikme_ms"] for o in olcum if o.get("ilinti", 0) >= 0.5]
        ayrinti = f"pencereler (ms, ilinti) {[(o.get('gecikme_ms'), o.get('ilinti')) for o in olcum]}"
        if len(gecerli) < 2:
            ekle("ses_kaymasi", "olculemedi", ayrinti + " — ilinti düşük (ses farklı mı?)")
        else:
            kosul("ses_kaymasi", max(map(abs, gecerli)) <= 5 and max(gecerli) - min(gecerli) <= 2,
                  ayrinti + "; sınır |gecikme| ≤ 5 ms, yayılım ≤ 2 ms")
    ufps = oran(uv.get("avg_frame_rate")) if uv else 0
    if not uv or abs(ufps - fps) > 0.01:
        ekle("kare_kaymasi", "olculemedi", f"fps farklı ({fps:g} / {ufps:g})")
        return
    x, y = luma_dizisi(usta), luma_dizisi(yol)
    kosul("kare_sayisi", len(x) == len(y), f"teslim {len(y)} / usta {len(x)} kare")
    if np.std(x) < 0.5:
        ekle("kare_kaymasi", "olculemedi", "görüntü neredeyse durağan")
        hizali = len(x) == len(y)
    else:
        g, r = kare_kaymasi(x, y)
        kosul("kare_kaymasi", g == 0 and r >= 0.9, f"{g} kare (ilinti {r:.3f})")
        hizali = len(x) == len(y) and g == 0
    if vmaf:
        if hizali:
            ekle(**vmaf_olc(yol, usta, uv, hedef))
        else:
            ekle("vmaf", "olculemedi", "kareler hizasız: VMAF anlamsız")


def vmaf_olc(yol: str, usta: str, uv: dict, hedef: str) -> dict:
    """delivery-qa QC10: teslim ustanın çözünürlüğüne büyütülür; zaman damgası kare sırasından (settb+setpts=N),
    böylece süzgeç kareleri kaydıramaz. WhatsApp: telefon modeli. Eşikler sezgisel → altı 'inceleme'."""
    W, H = int(uv["width"]), int(uv["height"])
    pay, _, payda = (uv.get("avg_frame_rate") or "30/1").partition("/")
    tb = f"settb={payda or 1}/{pay},setpts=N"
    model = "version=vmaf_v0.6.1" + ("\\:enable_transform=true" if hedef == "whatsapp" else "")
    with tempfile.TemporaryDirectory() as g:
        log = Path(g) / "vmaf.json"
        s = calis([ffmpeg(), "-nostdin", "-v", "error", "-i", yol, "-i", usta, "-lavfi",
                   f"[0:v]{tb},scale={W}:{H}:flags=bicubic[d];[1:v]{tb}[r];"
                   f"[d][r]libvmaf=model={model}:n_threads=8:log_fmt=json:log_path={log}", "-f", "null", "-"])
        if s.returncode or not log.exists():
            return {"ad": "vmaf", "durum": "olculemedi", "ayrinti": s.stderr.decode()[-200:]}
        pm = json.loads(log.read_text())["pooled_metrics"]["vmaf"]
    ort, en_az = pm["mean"], pm["min"]
    ok = ort >= 80 if hedef == "whatsapp" else (ort >= 93 and en_az >= 85)
    esik = "telefon modeli ort ≥ 80" if hedef == "whatsapp" else "ort ≥ 93, en az ≥ 85"
    return {"ad": "vmaf", "durum": "gecti" if ok else "inceleme",
            "ayrinti": f"ort {ort:.1f}, en az {en_az:.1f} (sezgisel eşik: {esik})"}


def boyut_oku(metin: str | None) -> tuple[int, int] | None:
    if not metin:
        return None
    m = re.fullmatch(r"(\d+)x(\d+)", metin)
    if not m or int(m[1]) % 2 or int(m[2]) % 2:
        raise MedyaHatasi(f"--boyut GxY biçiminde ve çift sayılı olmalı: {metin}")
    return int(m[1]), int(m[2])


def kodla(a) -> dict:
    on, p = ON[a.hedef], probe(a.usta)
    v = video_akisi(p)
    if not v:
        raise MedyaHatasi("ustada video yok")
    if abs(oran(v.get("r_frame_rate")) - oran(v.get("avg_frame_rate"))) > 0.01:
        raise MedyaHatasi("usta VFR (r_frame_rate ≠ avg_frame_rate) → önce: medya cfr <usta> --fps <hedef>")
    if v.get("color_transfer") in ("arib-std-b67", "smpte2084"):
        raise MedyaHatasi("usta HDR etiketli → SDR teslim için önce: medya sdr <usta> (ya da hyperframes render --sdr)")
    w, h = int(v["width"]), int(v["height"])
    if abs(donus(v)) in (90, 270):
        w, h = h, w
    W, H = boyut_oku(a.boyut) or on["boyut"] or (w, h)
    if not a.boyut and a.hedef == "youtube" and (w, h) == (3840, 2160):
        W, H = w, h
    if not a.boyut and a.hedef in ("whatsapp", "kucuk") and w > h:
        W, H = H, W
    if abs(w / h - W / H) > 0.01:
        raise MedyaHatasi(f"usta {w}x{h}, hedef {W}x{H}: en-boy farklı. Doğrudan ölçek SAR bozar (256:81 ölçüldü) → "
                          "önce kurguda yeniden kadrajla (kurgu-zanaati)")
    cikti = Path(a.cikti)
    if cikti.exists():
        raise MedyaHatasi(f"{cikti} var; üzerine yazılmaz — yeni ad ver")
    if a.hedef in ("whatsapp", "kucuk") and not a.mb:
        raise MedyaHatasi("boyut sınırı (WhatsApp sohbet, e-posta eki) doğrulanmadı: --mb ile kullanıcının/uygulamanın "
                          "verdiği sınırı yaz ya da dosyayı Belge/bağlantı olarak gönder (dikey/youtube dosyası)")
    fps = oran(v["avg_frame_rate"])
    fps_ifade = "30" if a.hedef == "whatsapp" and fps > 30.01 else v["avg_frame_rate"]   # boyut sınırında 30 fps
    fps_cikti = oran(fps_ifade)
    gop = max(1, round(fps_cikti * on["gop"]))
    vf = f"scale={W}:{H}:flags=lanczos,setsar=1,fps={fps_ifade},format=yuv420p"
    var_ses = a.ses or ses_akisi(p) is not None
    girdi = ["-i", a.usta] + (["-i", a.ses] if a.ses else [])
    harita = ["-map", "0:v:0"] + (["-map", "1:a:0" if a.ses else "0:a:0"] if var_ses else [])
    ses = ["-c:a", on["ses"][0], "-b:a", on["ses"][1], "-ar", "48000", "-ac", "2"] if var_ses else []
    kuyruk = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
              "-map_metadata", "-1", "-map_metadata:s", "-1", "-map_chapters", "-1", "-fflags", "+bitexact",
              "-flags:v", "+bitexact", "-flags:a", "+bitexact", "-movflags", "+faststart"]
    bas = [ffmpeg(), "-nostdin", "-v", "error"]
    if on["kodek"] == "hevc":
        kod = ["-c:v", "hevc_videotoolbox", "-q:v", "65", "-tag:v", "hvc1", "-profile:v", "main", "-g", str(gop)]
    else:
        sev = seviye_sec(on["seviye"], W, H, fps_cikti)
        kod = ["-c:v", "libx264", "-preset", "slow", "-profile:v", "high", "-level:v", f"{sev / 10:.1f}",
               "-g", str(gop), "-bf", "2"]
    with tempfile.TemporaryDirectory() as g:
        if a.hedef in ("whatsapp", "kucuk"):
            vk = int(a.mb * 8000 * 0.97 / float(p["format"]["duration"]) - 128)
            for deneme in range(2):   # kısa klipte iki geçiş hedefi aşabilir (1 sn 4K→1080p: 1,06 / 1 MB ölçüldü)
                if vk < 300:
                    raise MedyaHatasi(f"{a.mb} MB için video bit hızı {vk} kb/s: anlamsız düşük → Belge yolu")
                ortak = ["-vf", vf] + kod + ["-b:v", f"{vk}k", "-passlogfile", str(Path(g) / "wa")]
                calistir(bas + ["-y", "-i", a.usta, "-map", "0:v:0"] + ortak + ["-pass", "1", "-an", "-f", "null",
                                                                              "/dev/null"])
                calistir(bas + ["-n"] + girdi + harita + ortak + ["-maxrate", f"{vk * 3 // 2}k", "-bufsize",
                                                                  f"{vk * 2}k", "-pass", "2"] + ses + kuyruk
                         + [str(cikti)], hata_mesaji=f"kodlama başarısız: {cikti}")
                gercek = cikti.stat().st_size / 1e6
                if gercek <= a.mb or deneme:
                    break
                print(f"  ! {gercek:.2f} MB > {a.mb} MB: bit hızı {vk} → ", end="")
                vk = int(vk * a.mb / gercek * 0.98)
                print(f"{vk} kb/s ile yeniden kodlanıyor")
                cikti.unlink()   # bu çağrının kendi yazdığı dosya
            komut = None
        elif on["kodek"] == "hevc":
            komut = bas + ["-n"] + girdi + harita + ["-vf", vf] + kod + ses + kuyruk
        else:
            tavan = ("60M", "120M") if W * H > 1920 * 1088 else ("20M", "40M")
            komut = bas + ["-n"] + girdi + harita + ["-vf", vf] + kod + ["-crf", str(on["crf"]), "-maxrate", tavan[0],
                                                                         "-bufsize", tavan[1]] + ses + kuyruk
        if komut:
            calistir(komut + [str(cikti)], hata_mesaji=f"kodlama başarısız: {cikti}")
    if var_ses and not a.ses:
        print("  ! ses ustadan yeniden kodlandı (ek AAC kuşağı); tercih: --ses <medya ustala ile ustalanmış WAV>")
    print(f"→ {cikti} ({cikti.stat().st_size / 1e6:.2f} MB)")
    return uygunluk(str(cikti), a.hedef, a.usta, a.mb, boyut=(W, H))


def guvenli(a) -> int:
    p = probe(a.video)
    v = video_akisi(p) or {}
    if abs(int(v.get("width", 0)) / max(1, int(v.get("height", 1))) - 9 / 16) > 0.01:
        raise MedyaHatasi("güvenli alan sayfası 9:16 dikey teslim içindir (Reels/TikTok/Shorts arayüzü)")
    sure = float(p["format"]["duration"])
    # kırmızı: Meta Reels reklam rehberi (doğrulandı) üst %14, alt %35, yanlar %6 · sarı çerçeve: muhafazakâr birleşim
    vf = (f"fps=18/{sure:.3f},drawbox=x=0:y=0:w=iw:h=ih*0.14:color=red@0.35:t=fill,"
          "drawbox=x=0:y=ih*0.65:w=iw:h=ih*0.35:color=red@0.35:t=fill,"
          "drawbox=x=0:y=0:w=iw*0.06:h=ih:color=red@0.35:t=fill,drawbox=x=iw*0.94:y=0:w=iw*0.06:h=ih:color=red@0.35:t=fill,"
          "drawbox=x=iw*0.111:y=ih*0.148:w=iw*0.778:h=ih*0.502:color=yellow:t=6,scale=216:-2,tile=6x3")
    Path(a.cikti).parent.mkdir(parents=True, exist_ok=True)
    calistir([ffmpeg(), "-nostdin", "-v", "error", "-y", "-i", a.video, "-an", "-vf", vf, "-frames:v", "1", a.cikti])
    print(f"güvenli alan sayfası (18 kare, eşit aralık) → {a.cikti}  — açmadan önce gizlilik onayı; yüz/eylem kırmızıda mı?")
    if not a.analiz:
        return 0
    kareler = json.loads(Path(a.analiz).read_text()).get("kareler", [])
    ici = toplam = 0
    seri = en_uzun = 0.0
    onceki_t, onceki_alt = None, False
    for k in kareler:
        merkez = [(y["kutu"][0] + y["kutu"][2] / 2, y["kutu"][1] + y["kutu"][3] / 2) for y in k.get("yuzler") or []]
        toplam += len(merkez)
        ici += sum(1 for x, y in merkez if 0.111 <= x <= 0.889 and 0.148 <= y <= 0.65)
        alt = any(y > 0.65 for _, y in merkez)
        seri = seri + (k["t"] - onceki_t) if alt and onceki_alt and onceki_t is not None else 0.0
        en_uzun, onceki_t, onceki_alt = max(en_uzun, seri), k["t"], alt
    if not toplam:
        print("yüz bulunmadı: otomatik ölçüm yok (yalnız sayfa incelemesi)")
        return 0
    ok = ici / toplam >= 0.95 and en_uzun <= 1.0
    print(f"{'✓' if ok else '✗'} yüz merkezlerinin %{100 * ici / toplam:.0f}'i güvenli kutuda (sınır %95); "
          f"alt %35'te en uzun süre {en_uzun:.1f} sn (sınır 1 sn)")
    return 0 if ok else 1


def yaz(s: dict, json_yol: str | None) -> int:
    isaret = {"gecti": "✓", "kaldi": "✗", "inceleme": "!", "olculemedi": "?"}
    print(f"  {s['dosya']}: {s['boyut_mb']} MB, {s['sure']:.3f} sn")
    for b in s["denetimler"]:
        print(f"{isaret[b['durum']]} {b['ad']:<14} {b['ayrinti']}")
    d = Path(s["dosya"])
    yol = Path(json_yol or d.parent / "denetim" / f"{d.stem}-uygunluk.json")
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n")
    print(("GEÇTİ" if s["gecti"] else "KALDI") + f" (uygunluk, {s['hedef']}) → {yol}")
    return 0 if s["gecti"] else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = ap.add_subparsers(dest="komut", required=True)
    k = alt.add_parser("kodla", help="usta → platform dosyası + uygunluk")
    k.add_argument("usta")
    k.add_argument("--hedef", required=True, choices=["dikey", "youtube", "whatsapp", "kucuk", "apple"])
    k.add_argument("--cikti", required=True)
    k.add_argument("--ses", help="ustalanmış PCM WAV (medya ustala ses.wav --cikti ses-usta.wav)")
    k.add_argument("--mb", type=float, help="boyut sınırı (MB); whatsapp ve kucuk için zorunlu")
    k.add_argument("--boyut", help="ön ayar boyutu yerine GxY (ör. 4:5 akış 1080x1350); usta aynı en-boyda olmalı")
    u = alt.add_parser("uygunluk", help="teslim dosyasının uygunluk denetimi")
    u.add_argument("dosya")
    u.add_argument("--hedef", required=True, choices=list(ON))
    u.add_argument("--usta", help="karşılaştırma için usta (ses/kare kayması, kare sayısı, VMAF)")
    u.add_argument("--mb", type=float)
    u.add_argument("--boyut", help="beklenen GxY (kodla --boyut ile üretildiyse)")
    u.add_argument("--vmaf", action="store_true", help="VMAF (usta ile aynı fps ve hizalı kareler gerekir)")
    u.add_argument("--json")
    g = alt.add_parser("guvenli", help="dikey güvenli alan sayfası (+ yüz oranı)")
    g.add_argument("video")
    g.add_argument("--cikti", required=True, help="PNG yolu")
    g.add_argument("--analiz", help="medya analiz <video> çıktısı JSON (yüz kutuları)")
    a = ap.parse_args()
    try:
        if a.komut == "kodla":
            return yaz(kodla(a), None)
        if a.komut == "uygunluk":
            return yaz(uygunluk(a.dosya, a.hedef, a.usta, a.mb, a.vmaf, boyut_oku(a.boyut)), a.json)
        return guvenli(a)
    except MedyaHatasi as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
