"""medya proje yeni <ad> [--tur ...] — her üretim kendi klasöründe, aynı düzende.

projeler/YYYY-AA-GG-<ad>/
  BRIEF.md     ne isteniyor (amaç, izleyici, paylaşım yeri, süre, en-boy, yazı, gizlilik) — sablonlar/BRIEF.md
  KARARLAR.md  kurgu/tasarım kararları ve gerekçeleri (tarihli) — sablonlar/KARARLAR.md
  kaynak/      kullanıcının dosyalarının SALT OKUNUR kopyaları (asıllara dokunulmaz)
  analiz/      medya incele/sahneler/muzik/... çıktıları, temas sayfaları
  plan/        kurgu planı (EDL), storyboard
  calisma/     ara dosyalar (parçalar, kompozisyon, ses katmanları) — yeniden üretilebilir
               --motor remotion: calisma/remotion/ (sablonlar/remotion: config, tsconfig, yerel yazı tipleri)
  cikti/       teslim dosyaları + denetim raporları
"""
from __future__ import annotations

import datetime as dt
import re
import shutil
import stat
import subprocess
from pathlib import Path

from ..ortak import KOK, MedyaHatasi

SABLON = KOK / "sablonlar"


def _sablon(dosya: str, **alanlar) -> str:
    return (SABLON / dosya).read_text().format(**alanlar)


def _klonla(kaynak: Path, hedef: Path) -> None:
    """APFS klonu (cp -c: aynı diskte yer kaplamaz, asıl değişmez); olmazsa tam kopya. Kopya sonra salt okunur yapılır."""
    if kaynak.is_file() and subprocess.run(["cp", "-c", "-p", str(kaynak), str(hedef)],
                                           capture_output=True).returncode == 0:
        return
    shutil.copy2(kaynak, hedef)


def yeni_(args) -> int:
    temiz = re.sub(r"[^a-z0-9ğüşıöç\-]+", "-", args.ad.lower()).strip("-")
    if not temiz:
        raise MedyaHatasi("geçerli bir proje adı ver")
    tarih = dt.date.today().isoformat()
    kok = KOK / "projeler" / f"{tarih}-{temiz}"
    if kok.exists():
        raise MedyaHatasi(f"zaten var: {kok}")
    for d in ("kaynak", "analiz", "plan", "calisma", "cikti"):
        (kok / d).mkdir(parents=True)
    (kok / "BRIEF.md").write_text(_sablon("BRIEF.md", ad=args.ad, tur=args.tur, tarih=tarih, motor=args.motor))
    (kok / "KARARLAR.md").write_text(_sablon("KARARLAR.md", ad=args.ad))
    if args.motor == "remotion":                                   # lisans kapısı BRIEF'te; şablon yerel ve sabit
        shutil.copytree(SABLON / "remotion", kok / "calisma" / "remotion")
    for kaynak in args.kaynak or []:
        k = Path(kaynak).expanduser()
        if not k.exists():
            raise MedyaHatasi(f"kaynak yok: {k}")
        hedef = kok / "kaynak" / k.name
        _klonla(k, hedef)                                        # asıl dosyaya dokunulmaz
        hedef.chmod(hedef.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    print(kok)
    return 0


def kaydet(alt, ad):
    p = alt.add_parser(ad, help="üretim klasörü")
    a = p.add_subparsers(dest="eylem", required=True)
    y = a.add_parser("yeni", help="yeni proje klasörü aç")
    y.add_argument("ad")
    y.add_argument("--tur", default="video", choices=["video", "animasyon", "gorsel", "ses", "karma"])
    y.add_argument("--kaynak", nargs="*", help="kaynak/ altına salt okunur kopyalanacak dosyalar")
    y.add_argument("--motor", default="hyperframes", choices=["hyperframes", "remotion"],
                   help="kompozisyon motoru (remotion yalnız lisans kapısı geçerse: kişisel / ≤3 kişi / yalnız dosya teslimi)")
    y.set_defaults(islev=yeni_)
