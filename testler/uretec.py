"""Doğru cevabı bilinen sentetik test medyası üretir (testler/veri/, yeniden üretilebilir, git dışı).

  .venv/bin/python testler/uretec.py

- muzik_davullu.wav   100 BPM, 4/4, davul + akor; vuruşlar 0,5 sn'de başlar (bilinen ızgara)
- muzik_yumusak.wav   76 BPM, davulsuz yumuşak pad + yumuşak tınılar (bugünkü hatanın türü)
- kesimli.mp4         6 sahne, kesimler bilinen anlarda, ses = muzik_davullu (kesimler vuruşta)
- kusurlu.mp4         kesimli.mp4 + 1 karelik siyah flaş + kesimde tık + GPS etiketi
- karisik_ses.mp4     her sahnenin kendi sesi var (çekim sesi) → ses-turu "karisik" demeli
- hdr_hlg.mp4         HLG etiketli 10 bit HEVC → incele HDR demeli, sdr çevirmeli
- vfr.mp4             değişken kare hızı → incele VFR uyarmalı
Gerçek değerler veri/gercek.json'a yazılır.
"""
from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parent.parent
VERI = Path(__file__).resolve().parent / "veri"
FF = str(KOK / "arac" / "ffmpeg")
SR = 44100
rng = np.random.default_rng(20261005)


def wav_yaz(yol: Path, x: np.ndarray) -> None:
    x = x / (np.abs(x).max() + 1e-9) * 0.7
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    with wave.open(str(yol), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def ff(*arg: str) -> None:
    subprocess.run([FF, "-nostdin", "-v", "error", "-y", *arg], check=True)


def davullu(sure=24.0, bpm=100.0, ilk=0.5):
    n = int(sure * SR); t = np.arange(n) / SR; x = np.zeros(n)
    T = 60 / bpm
    vur = np.arange(ilk, sure - 0.2, T)
    for i, b in enumerate(vur):
        k = int(b * SR); L = int(0.25 * SR); tt = np.arange(L) / SR
        f = 55 + 70 * np.exp(-tt * 30)
        kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) * (1.0 if i % 4 == 0 else 0.75)
        x[k:k + L] += kick[: n - k]
        h = int((b + T / 2) * SR); Lh = int(0.05 * SR)
        if h + Lh < n:
            x[h:h + Lh] += rng.standard_normal(Lh) * np.exp(-np.arange(Lh) / SR * 80) * 0.15
    akorlar = [(220, 277.2, 329.6), (196, 246.9, 293.7), (174.6, 220, 261.6), (196, 246.9, 293.7)]
    for j, b in enumerate(vur[::4]):
        k0, k1 = int(b * SR), min(n, int((b + 4 * T) * SR))
        tt = np.arange(k1 - k0) / SR
        for f in akorlar[j % 4]:
            x[k0:k1] += 0.08 * np.sin(2 * np.pi * f * tt) * np.minimum(1, tt / 0.02) * np.exp(-tt * 0.6)
    return x, vur.tolist(), vur[::4].tolist()


def yumusak(sure=24.0, bpm=76.0, ilk=0.79):
    """Davul yok: pad akorlar ölçü başında yavaş atakla, vuruşlarda yumuşak tınılar (yavaş atak, alçak geçiren)."""
    n = int(sure * SR); x = np.zeros(n)
    T = 60 / bpm
    vur = np.arange(ilk, sure - 0.3, T)
    akorlar = [(174.6, 220, 261.6), (146.8, 174.6, 220), (116.5, 146.8, 174.6), (130.8, 164.8, 196)]
    for j, b in enumerate(vur[::4]):
        k0, k1 = int(b * SR), min(n, int((b + 4 * T + 0.3) * SR))
        tt = np.arange(k1 - k0) / SR
        zarf = np.minimum(1, tt / 0.35) * np.exp(-tt * 0.25)
        for f in akorlar[j % 4]:
            x[k0:k1] += 0.10 * zarf * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt))
    for i, b in enumerate(vur):
        k = int(b * SR); L = int(0.6 * SR); tt = np.arange(L) / SR
        f = [523.3, 659.3, 587.3, 698.5][i % 4]
        tini = np.sin(2 * np.pi * f * tt) * np.minimum(1, tt / 0.04) * np.exp(-tt * 3.5) * 0.12
        x[k:k + L] += tini[: n - k]
    x += 0.004 * rng.standard_normal(n)
    return x, vur.tolist(), vur[::4].tolist()


def _davul(x, t, guc=1.0, tur="kick"):
    k = int(t * SR)
    if tur == "kick":
        L = int(0.25 * SR); tt = np.arange(L) / SR
        f = 55 + 70 * np.exp(-tt * 30)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) * guc
    else:                                                     # trampet: gürültü + ton
        L = int(0.18 * SR); tt = np.arange(L) / SR
        s = (0.6 * rng.standard_normal(L) + 0.5 * np.sin(2 * np.pi * 190 * tt)) * np.exp(-tt * 22) * guc
    x[k:k + L] += s[: max(0, len(x) - k)]


def net_ritim(sure=24.0, bpm=96.0, ilk=0.4):
    """Belirsizliği olmayan ritim: 1 ve 3'te kick, 2 ve 4'te trampet, ara vuruş yok + bas notası."""
    n = int(sure * SR); x = np.zeros(n); T = 60 / bpm
    vur = np.arange(ilk, sure - 0.3, T)
    for i, b in enumerate(vur):
        _davul(x, b, 1.0 if i % 4 == 0 else 0.85, "kick" if i % 2 == 0 else "trampet")
        k0, k1 = int(b * SR), min(n, int((b + T * 0.9) * SR)); tt = np.arange(k1 - k0) / SR
        x[k0:k1] += 0.15 * np.sin(2 * np.pi * [55, 55, 49, 41.2][(i // 4) % 4] * tt) * np.exp(-tt * 3)
    return x, vur.tolist(), vur[::4].tolist()


def kayan_tempo(sure=30.0, bpm0=84.0, bpm1=96.0, ilk=0.4):
    """Canlı davulcu gibi tempo yavaşça kayar (84 → 96 BPM). Sabit ızgara burada yüzlerce ms sapar."""
    n = int(sure * SR); x = np.zeros(n)
    vur, t, i = [], ilk, 0
    while t < sure - 0.3:
        vur.append(t)
        _davul(x, t, 1.0 if i % 4 == 0 else 0.85, "kick" if i % 2 == 0 else "trampet")
        bpm = bpm0 + (bpm1 - bpm0) * t / sure
        t += 60 / bpm; i += 1
    return x, vur, vur[::4]


def video_sahneler(cikti: Path, kesimler: list[float], sure: float, ses: Path | None, ek: list[str] | None = None):
    kaynaklar = ["testsrc2=s=640x360:r=30", "mandelbrot=s=640x360:r=30", "smptehdbars=s=640x360:r=30",
                 "cellauto=s=640x360:r=30:rule=110", "testsrc2=s=640x360:r=30,hue=h=140",
                 "rgbtestsrc=s=640x360:r=30", "testsrc=s=640x360:r=30"]
    sinir = [0.0, *kesimler, sure]
    girdiler, filtre = [], []
    for i, (a, b) in enumerate(zip(sinir, sinir[1:])):
        girdiler += ["-f", "lavfi", "-t", f"{b - a:.4f}", "-i", kaynaklar[i % len(kaynaklar)]]
        filtre.append(f"[{i}:v]format=yuv420p,setsar=1,fps=30[v{i}]")
    n = len(sinir) - 1
    filtre.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]")
    komut = girdiler + (["-i", str(ses)] if ses else []) + ["-filter_complex", ";".join(filtre), "-map", "[v]"]
    if ses:
        komut += ["-map", f"{n}:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    komut += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", *(ek or []), str(cikti)]
    ff(*komut)


def main():
    VERI.mkdir(exist_ok=True)
    gercek = {}
    x, vur, olcu = davullu()
    wav_yaz(VERI / "muzik_davullu.wav", x)
    gercek["muzik_davullu"] = {"bpm": 100.0, "vuruslar": vur, "olcu_baslari": olcu}
    y, vur2, olcu2 = yumusak()
    wav_yaz(VERI / "muzik_yumusak.wav", y)
    gercek["muzik_yumusak"] = {"bpm": 76.0, "vuruslar": vur2, "olcu_baslari": olcu2}

    z, vur3, olcu3 = net_ritim()
    wav_yaz(VERI / "muzik_net.wav", z)
    gercek["muzik_net"] = {"bpm": 96.0, "vuruslar": vur3, "olcu_baslari": olcu3}
    w, vur4, olcu4 = kayan_tempo()
    wav_yaz(VERI / "muzik_kayan.wav", w)
    gercek["muzik_kayan"] = {"bpm": "84→96", "vuruslar": vur4, "olcu_baslari": olcu4}

    kesimler = [round(vur[k], 4) for k in (4, 8, 14, 20, 28)]          # hepsi vuruşta
    video_sahneler(VERI / "kesimli.mp4", kesimler, 20.0, VERI / "muzik_davullu.wav")
    gercek["kesimli"] = {"kesimler": kesimler, "sure": 20.0}

    # kusurlu: 1 karelik siyah (8,0 sn'de), kesimde tık (kesimler[2]), sahte GPS
    ff("-i", str(VERI / "kesimli.mp4"), "-vf", "drawbox=enable='between(n,240,240)':x=0:y=0:w=iw:h=ih:color=black:t=fill",
       "-af", f"aeval='val(0)+if(between(t,{kesimler[2]},{kesimler[2] + 0.0005}),0.9,0)':c=same",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
       "-metadata", "location=+41.0000+029.0000/", "-metadata", "location-eng=+41.0000+029.0000/",
       str(VERI / "kusurlu.mp4"))
    gercek["kusurlu"] = {"siyah_kare": 8.0, "tik": kesimler[2]}

    # karışık ses: her sahnenin kendi tonu + gürültü rengi (çekim sesi gibi)
    sinir = [0.0, *kesimler, 20.0]
    z = np.zeros(int(20.0 * SR))
    for i, (a, b) in enumerate(zip(sinir, sinir[1:])):
        k0, k1 = int(a * SR), int(b * SR)
        tt = np.arange(k1 - k0) / SR
        g = rng.standard_normal(k1 - k0)
        g = np.convolve(g, np.ones(2 + 6 * i) / (2 + 6 * i), "same")
        z[k0:k1] = 0.3 * g + 0.2 * np.sin(2 * np.pi * (180 + 90 * i) * tt) * (1 + 0.5 * np.sin(2 * np.pi * 3 * tt))
    wav_yaz(VERI / "karisik.wav", z)
    video_sahneler(VERI / "karisik_ses.mp4", kesimler, 20.0, VERI / "karisik.wav")

    # HDR (HLG etiketli 10 bit HEVC)
    ff("-f", "lavfi", "-t", "3", "-i", "testsrc2=s=640x360:r=30", "-vf", "format=yuv420p10le", "-c:v", "libx265",
       "-x265-params", "log-level=error:colorprim=bt2020:transfer=arib-std-b67:colormatrix=bt2020nc",
       "-color_primaries", "bt2020", "-color_trc", "arib-std-b67", "-colorspace", "bt2020nc", "-tag:v", "hvc1",
       str(VERI / "hdr_hlg.mp4"))

    # VFR: zaman damgaları düzensiz
    ff("-f", "lavfi", "-t", "4", "-i", "testsrc2=s=320x240:r=30", "-vf", "setpts='N/30/TB+0.012*sin(N)/TB'",
       "-fps_mode", "passthrough", "-c:v", "libx264", "-preset", "veryfast", str(VERI / "vfr.mp4"))

    # ağır çekim doğruluk sınaması: dokulu arka plan + kayan kadraj + hareketli kutu; 60 fps gerçek,
    # 30 fps girdi (çift kareler), 120 fps kaynak (doğal ağır çekim yolu için)
    ff("-f", "lavfi", "-i", "mandelbrot=s=2560x1440:r=1", "-frames:v", "1", str(VERI / "_doku.png"))
    hareket = ("crop=1280:720:x='120+t*300':y='80+t*90',drawbox=x='100+t*350':y='300+40*sin(t*3)':w=160:h=160:"
               "color=orange@1:t=fill,format=yuv420p")
    renk = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
    ff("-loop", "1", "-framerate", "60", "-t", "2", "-i", str(VERI / "_doku.png"), "-vf", hareket, "-r", "60",
       "-c:v", "libx264", "-crf", "0", "-preset", "veryfast", *renk, str(VERI / "hareket60.mp4"))
    ff("-i", str(VERI / "hareket60.mp4"), "-vf", "select='not(mod(n\\,2))',setpts=N/30/TB", "-r", "30",
       "-c:v", "libx264", "-crf", "0", "-preset", "veryfast", *renk, str(VERI / "hareket30.mp4"))
    ff("-loop", "1", "-framerate", "120", "-t", "1", "-i", str(VERI / "_doku.png"), "-vf", hareket, "-r", "120",
       "-c:v", "libx264", "-crf", "10", "-preset", "veryfast", *renk, str(VERI / "hareket120.mp4"))
    (VERI / "_doku.png").unlink()

    # Türkçe konuşma (macOS yerleşik Yelda sesi) ve müzik + konuşma karışımı
    metin = "Merhaba, bu bir deneme kaydıdır. Bugün hava güzel ve kahvemi içiyorum. Yarın sabah dokuzda toplantımız var."
    try:
        subprocess.run(["say", "-v", "Yelda", "-o", str(VERI / "_konusma.aiff"), metin], check=True)
        ff("-i", str(VERI / "_konusma.aiff"), "-ar", "16000", "-ac", "1", str(VERI / "konusma_tr.wav"))
        (VERI / "_konusma.aiff").unlink()
        ff("-i", str(VERI / "muzik_net.wav"), "-i", str(VERI / "konusma_tr.wav"), "-filter_complex",
           "[1:a]adelay=12000|12000,apad[k];[0:a][k]amix=inputs=2:duration=first[a]", "-map", "[a]", str(VERI / "karma.wav"))
        gercek["konusma_tr"] = {"metin": metin, "karma_konusma": [12.0, 20.0]}
    except (OSError, subprocess.CalledProcessError):
        print("⚠ 'say -v Yelda' yok: konuşma fikstürü atlandı")

    (VERI / "gercek.json").write_text(json.dumps(gercek, indent=1))
    print("üretildi:", ", ".join(sorted(p.name for p in VERI.iterdir())))


if __name__ == "__main__":
    main()
