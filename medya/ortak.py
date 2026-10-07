"""Ortak yardımcılar: yollar, komut çalıştırma, ffprobe/ffmpeg, JSON, ses okuma."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

KOK = Path(os.environ.get("MEDYA", Path(__file__).resolve().parent.parent))
ARAC = KOK / "arac"


class MedyaHatasi(RuntimeError):
    """Kullanıcıya gösterilecek, yığın izi gerektirmeyen hata."""


def arac_yolu(ad: str) -> str:
    """Önce çalışma alanındaki arac/, sonra PATH."""
    yerel = ARAC / ad
    if yerel.exists():
        return str(yerel)
    bulunan = shutil.which(ad)
    if bulunan:
        return bulunan
    raise MedyaHatasi(f"'{ad}' bulunamadı (arac/ ya da PATH). Önce: source {KOK}/ortam.sh")


def calistir(komut: list[str], *, yakala: bool = True, girdi: bytes | None = None, zaman_asimi: float | None = None,
             hata_mesaji: str | None = None) -> subprocess.CompletedProcess:
    """Komutu stdin'i kapalı çalıştırır (ffmpeg döngülerde stdin yemesin); hata olursa anlaşılır mesaj verir."""
    try:
        sonuc = subprocess.run(komut, capture_output=yakala, input=girdi, timeout=zaman_asimi,
                               stdin=None if girdi is not None else subprocess.DEVNULL)
    except FileNotFoundError as e:
        raise MedyaHatasi(f"komut bulunamadı: {komut[0]}") from e
    if sonuc.returncode != 0:
        hata = (sonuc.stderr or b"").decode("utf-8", "replace")[-1500:] if yakala else ""
        raise MedyaHatasi((hata_mesaji or f"komut başarısız ({sonuc.returncode}): {' '.join(komut[:6])} …") + "\n" + hata)
    return sonuc


def _etime_sn(e: str) -> int:
    """ps etime ([[gg-]ss:]dd:ss) → saniye."""
    gun, _, saat = e.rpartition("-")
    p = [int(x) for x in saat.split(":")]
    while len(p) < 3:
        p.insert(0, 0)
    return (int(gun) if gun else 0) * 86400 + p[0] * 3600 + p[1] * 60 + p[2]


def ane_tikanikligi(ps_ciktisi: str | None = None) -> str | None:
    """Apple Neural Engine derleyicisi takıldıysa açıklama döndürür, yoksa None.

    2026-10-05: ANECompilerService 18 saat %100 CPU'da kaldı; Vision (medya analiz) ve kare hızı dönüşümü
    (medya yavaslat) model yüklerken aned'in arkasında sessizce, sonsuza dek bekledi (örnekleme yığını:
    _ANEDaemonConnection loadModel). Normal derleme saniyeler sürer; >10 dk ve meşgulse takılı sayılır."""
    if ps_ciktisi is None:
        try:
            ps_ciktisi = subprocess.run(["ps", "-axo", "etime=,pcpu=,comm="], capture_output=True, text=True,
                                        timeout=5).stdout
        except (OSError, subprocess.SubprocessError):
            return None
    for satir in ps_ciktisi.splitlines():
        p = satir.split(None, 2)
        if len(p) == 3 and p[2].strip().endswith("ANECompilerService"):
            sure, cpu = _etime_sn(p[0]), float(p[1])
            if cpu >= 50 and sure >= 600:
                return (f"Apple Neural Engine derleyicisi takılı (ANECompilerService {sure / 3600:.1f} saattir %{cpu:.0f} "
                        "CPU): Vision ve ağır çekim istekleri onun arkasında bekler. Çözüm (kullanıcı): Terminal'de "
                        "'sudo killall ANECompilerService' ya da Mac'i yeniden başlatmak.")
    return None


def apple_calistir(komut: list[str], zaman_asimi: float, hata_mesaji: str) -> subprocess.CompletedProcess:
    """arac/medya-apple'ı bekçiyle çalıştırır: Neural Engine takılıysa hiç başlamaz, süre aşılırsa öldürülür.
    Her iki durumda da MedyaHatasi (yedeği olan yetenek — ör. yavaslat → ffmpeg — ona düşer)."""
    tikali = ane_tikanikligi()
    if tikali:
        raise MedyaHatasi(f"{hata_mesaji}: {tikali}")
    try:
        return calistir(komut, zaman_asimi=zaman_asimi, hata_mesaji=hata_mesaji)
    except subprocess.TimeoutExpired as e:
        raise MedyaHatasi(f"{hata_mesaji}: {zaman_asimi:.0f} sn'de bitmedi, durduruldu. "
                          + (ane_tikanikligi() or "Neural Engine yanıt vermiyor olabilir; 'medya-apple yetenek' ve "
                             "Etkinlik İzleyicisi'nde ANECompilerService'e bak.")) from e


def ffmpeg() -> str:
    return arac_yolu("ffmpeg")


def ffprobe() -> str:
    return arac_yolu("ffprobe")


def probe(yol: str | Path) -> dict:
    """ffprobe çıktısı (akışlar + biçim + yan veri) sözlük olarak."""
    s = calistir([ffprobe(), "-v", "error", "-print_format", "json", "-show_format", "-show_streams",
                  str(yol)], hata_mesaji=f"okunamadı: {yol}")
    return json.loads(s.stdout)


def video_akisi(p: dict) -> dict | None:
    return next((s for s in p.get("streams", []) if s.get("codec_type") == "video"
                 and not s.get("disposition", {}).get("attached_pic")), None)


def ses_akisi(p: dict) -> dict | None:
    return next((s for s in p.get("streams", []) if s.get("codec_type") == "audio"), None)


def oran(metin: str | None) -> float:
    """'30000/1001' -> 29.97"""
    if not metin or metin in ("0/0", "N/A"):
        return 0.0
    if "/" in metin:
        a, b = metin.split("/")
        return float(a) / float(b) if float(b) else 0.0
    return float(metin)


def ses_oku(yol: str | Path, *, sr: int = 22050, kanal: int = 1, bas: float | None = None,
            sure: float | None = None, zamanli: bool = False) -> tuple[np.ndarray, int]:
    """Herhangi bir medya dosyasının sesini ffmpeg ile float32 dizisine çözer (kanal=1: mono).
    zamanli=True: oynatıcının duyduğu gibi — akışın başlangıç zaman damgası (ör. geç başlayan ses) sessizlikle
    doldurulur; yoksa ilk örnekten okunur ve kapsayıcı düzeyindeki kayma görünmez."""
    komut = [ffmpeg(), "-nostdin", "-v", "error"]
    if bas is not None:
        komut += ["-ss", f"{bas:.4f}"]
    if sure is not None:
        komut += ["-t", f"{sure:.4f}"]
    komut += ["-i", str(yol), "-vn"]
    if zamanli:
        komut += ["-af", "aresample=async=1:first_pts=0"]
    komut += ["-ac", str(kanal), "-ar", str(sr), "-f", "f32le", "-"]
    s = calistir(komut, hata_mesaji=f"ses çözülemedi: {yol}")
    x = np.frombuffer(s.stdout, dtype="<f4")
    if kanal > 1:
        x = x.reshape(-1, kanal)
    return x.copy(), sr


def json_yaz(yol: str | Path, veri) -> Path:
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2, default=_json_varsayilan) + "\n")
    return yol


def json_oku(yol: str | Path):
    return json.loads(Path(yol).read_text())


def _json_varsayilan(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(type(o))


def uyar(mesaj: str) -> None:
    print(f"⚠ {mesaj}", file=sys.stderr)


def bilgi(mesaj: str) -> None:
    print(mesaj, file=sys.stderr)


def ses_gecikmesi(a: str | Path, b: str | Path, *, sr: int = 48000, bas: float = 0.0, sure: float = 20.0,
                  ara: float = 0.25) -> dict:
    """b'nin a'ya göre gecikmesi (ms; pozitif = b geç). Örnek düzeyinde FFT çapraz ilintisi, ±ara sn arar."""
    x, _ = ses_oku(a, sr=sr, bas=bas, sure=sure)
    y, _ = ses_oku(b, sr=sr, bas=bas, sure=sure)
    n = min(len(x), len(y))
    if n < sr // 2:
        return {"olculemedi": True}
    x, y = x[:n] - x[:n].mean(), y[:n] - y[:n].mean()
    m = 1 << int(np.ceil(np.log2(2 * n)))
    c = np.fft.irfft(np.fft.rfft(y, m) * np.conj(np.fft.rfft(x, m)), m)
    k = int(ara * sr)
    aday = np.concatenate([c[-k:], c[:k + 1]])               # gecikmeler -k … +k
    j = int(np.argmax(aday)) - k
    ilinti = float(aday.max() / (np.sqrt((x ** 2).sum() * (y ** 2).sum()) + 1e-12))
    return {"gecikme_ms": round(j / sr * 1000, 3), "ilinti": round(ilinti, 4)}

