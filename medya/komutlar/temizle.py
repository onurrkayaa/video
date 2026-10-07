"""medya temizle [--uygula] — disk bütçesi: stüdyonun yeniden üretilebilir önbelleklerini raporlar / temizler.

Yalnız stüdyonun KENDİ ürettiği ve yeniden üretilebilir şeyler: HyperFrames kare önbelleği (`hyperframes clean`),
uv önbelleği, test geçici klasörü, projelerin `calisma/` klasörleri (yalnız --calisma ile; ara dosyalardır ama
silmeden önce kullanıcıya sor). Kullanıcı dosyalarına (kaynak/, cikti/, İndirilenler…) ve modellere dokunmaz.
Varsayılan kuru çalıştırmadır; silmek için --uygula.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..ortak import KOK, MedyaHatasi


def _boyut(yol: Path) -> int:
    if not yol.exists():
        return 0
    if yol.is_file():
        return yol.stat().st_size
    toplam = 0
    for p in yol.rglob("*"):
        try:
            if p.is_file() and not p.is_symlink():
                toplam += p.stat().st_size
        except OSError:
            pass
    return toplam


def _gb(b: int) -> str:
    return f"{b / 1e9:.2f} GB" if b >= 1e8 else f"{b / 1e6:.0f} MB"


def calistir_(args) -> int:
    hedefler: list[tuple[str, Path, str]] = [
        ("uv önbelleği", KOK / ".uv" / "cache", "uv"),
        ("test geçici klasörü", KOK / "testler" / ".gecici", "sil"),
    ]
    if args.calisma:
        for p in sorted((KOK / "projeler").glob("*/calisma")):
            hedefler.append((f"proje ara dosyaları ({p.parent.name})", p, "sil-icerik"))
    bos = shutil.disk_usage(KOK).free
    print(f"boş disk: {_gb(bos)}")
    toplam = 0
    for ad, yol, _ in hedefler:
        b = _boyut(yol)
        toplam += b
        print(f"  {ad:<40} {_gb(b):>9}  {yol}")
    hf = subprocess.run([str(KOK / "node_modules" / ".bin" / "hyperframes"), "clean", "--dry-run"],
                        capture_output=True, text=True, stdin=subprocess.DEVNULL, cwd=KOK)
    hf_satir = next((s.strip() for s in hf.stdout.splitlines() if "Would remove" in s or "Nothing" in s), "bilinmiyor")
    print(f"  {'HyperFrames kare önbelleği':<40} {hf_satir}")
    modeller = _boyut(KOK / "modeller")
    print(f"  (dokunulmaz) modeller/: {_gb(modeller)} — gerekmeyen modeli elle ve sorarak sil")
    if not args.uygula:
        print(f"kuru çalıştırma: ~{_gb(toplam)} + HyperFrames önbelleği boşaltılabilir. Silmek için: medya temizle --uygula")
        return 0
    for ad, yol, tur in hedefler:
        if not yol.exists():
            continue
        if not str(yol.resolve()).startswith(str(KOK.resolve())):
            raise MedyaHatasi(f"stüdyo dışı yol reddedildi: {yol}")
        if tur == "uv":
            subprocess.run([str(KOK / "arac" / "uv"), "cache", "clean"], check=False, cwd=KOK)
        elif tur == "sil":
            shutil.rmtree(yol)
        elif tur == "sil-icerik":
            for p in yol.iterdir():
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    subprocess.run([str(KOK / "node_modules" / ".bin" / "hyperframes"), "clean"], check=False, cwd=KOK,
                   stdin=subprocess.DEVNULL, capture_output=True)
    print(f"temizlendi. boş disk: {_gb(shutil.disk_usage(KOK).free)}")
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="önbellekleri raporla/temizle (disk bütçesi)")
    p.add_argument("--uygula", action="store_true", help="gerçekten sil (varsayılan: yalnız rapor)")
    p.add_argument("--calisma", action="store_true", help="projelerin calisma/ ara dosyalarını da dahil et (önce sor)")
    p.set_defaults(islev=calistir_)
