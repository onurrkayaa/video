"""medya yetenekler | kur <sağlayıcı> | test [yetenek] — kayıt defteri ve kurulum.

`kur` sağlayıcının kayıttaki kurulum komutunu çalıştırır; önce lisansı, ticari kullanım durumunu ve disk
boyutunu gösterir. Ücretli/bulut sağlayıcılar (etkin=false) kullanıcının açık onayı olmadan kurulmaz.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

from ..kayit import yukle
from ..ortak import KOK, MedyaHatasi


def yetenekler_(args) -> int:
    yetenekler, saglayicilar = yukle()
    durum = {}
    alan = None
    for y in sorted(yetenekler.values(), key=lambda y: (y.alan, y.ad)):
        if y.alan != alan:
            alan = y.alan
            print(f"\n[{alan or 'genel'}]")
        isaret = []
        for ad in [y.saglayici, *y.yedek]:
            s = saglayicilar[ad]
            if ad not in durum:
                durum[ad] = s.kurulu_mu() if s.etkin else None
            d = durum[ad]
            isaret.append(f"{ad}{'✓' if d else ('·kapalı' if d is None else '✗')}")
        print(f"  {y.komut:<22} {y.aciklama}\n  {'':<22} sağlayıcı: {', '.join(isaret)}")
    if args.saglayicilar:
        print("\nSağlayıcılar:")
        for s in saglayicilar.values():
            d = durum.get(s.ad, s.kurulu_mu() if s.etkin else None)
            print(f"  {s.ad:<22} {('kurulu' if d else ('KAPALI: ' + s.onay if d is None else 'kurulu değil')):<28} "
                  f"lisans: {s.lisans}; ticari: {s.ticari}; ~{s.boyut_mb:.0f} MB")
    return 0


def kur_(args) -> int:
    _, saglayicilar = yukle()
    if args.saglayici not in saglayicilar:
        raise MedyaHatasi(f"bilinmeyen sağlayıcı: {args.saglayici}. Liste: medya yetenekler --saglayicilar")
    s = saglayicilar[args.saglayici]
    if not s.etkin:
        raise MedyaHatasi(f"{s.ad} kapalı ({s.onay}). Kullanıcının açık onayı olmadan kurulmaz; onay verirse "
                          "yetenekler.toml içinde etkin = true yapılır.")
    print(f"{s.ad}: lisans {s.lisans}; ticari kullanım: {s.ticari}; yaklaşık {s.boyut_mb:.0f} MB")
    if s.not_:
        print(f"  not: {s.not_}")
    if s.kurulu_mu() and not args.yeniden:
        print("zaten kurulu.")
        return 0
    if not s.kurulum:
        raise MedyaHatasi(f"{s.ad} için kurulum komutu yok; elle kurulur.")
    bos = shutil.disk_usage(KOK).free / 1e9
    if s.boyut_mb / 1000 > bos - 5:
        raise MedyaHatasi(f"diskte {bos:.1f} GB boş; {s.ad} (~{s.boyut_mb / 1000:.1f} GB) sonrası 5 GB'tan az kalır.")
    print(f"$ {s.kurulum}")
    r = subprocess.run(s.kurulum, shell=True, cwd=KOK)
    if r.returncode:
        raise MedyaHatasi(f"kurulum başarısız ({r.returncode})")
    print("kurulu ✓" if s.kurulu_mu() else "⚠ kurulum bitti ama kontrol komutu başarısız: " + s.kontrol)
    return 0


def test_(args) -> int:
    komut = [sys.executable, "-m", "pytest", "-q", str(KOK / "testler")]
    if args.yetenek:
        komut += ["-k", args.yetenek]
    ortam = dict(os.environ)
    if args.agir:                       # 7–9 GB bellek isteyen üretici modeller (FLUX.2, VoxCPM2): yalnız istenince
        ortam["MEDYA_AGIR_TEST"] = "1"
    return subprocess.run(komut, cwd=KOK, env=ortam).returncode


def kaydet(alt, ad):
    if ad == "yetenekler":
        p = alt.add_parser(ad, help="yetenekleri ve sağlayıcıları listeler")
        p.add_argument("--saglayicilar", action="store_true", help="sağlayıcı lisans/boyut tablosunu da göster")
        p.set_defaults(islev=yetenekler_)
    elif ad == "kur":
        p = alt.add_parser(ad, help="sağlayıcı kurar")
        p.add_argument("saglayici")
        p.add_argument("--yeniden", action="store_true")
        p.set_defaults(islev=kur_)
    elif ad == "test":
        p = alt.add_parser(ad, help="doğruluk sınamaları")
        p.add_argument("yetenek", nargs="?")
        p.add_argument("--agir", action="store_true",
                       help="ağır üretici model sınamalarını da koş (FLUX.2 9–11 GB, Z-Image 6,3 GB, VoxCPM2 "
                            "7–14 GB bellek; takas büyütür)")
        p.set_defaults(islev=test_)
