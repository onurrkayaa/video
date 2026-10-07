#!/usr/bin/env python3
"""Satıcı (vendor) becerileri: sabit commit'ten indirilir, başına stüdyo ev kuralları eklenir.

Lisansı yeniden dağıtıma izin vermeyen ya da belirsiz olan satıcı içeriği depoya girmez (.gitignore); kurulumda
bu betik onu sabit commit'ten indirir (git fetch → içerik commit kimliğiyle doğrulanır), istenmeyen klasörleri siler
ve SKILL.md'nin satıcı ön bilgisini (frontmatter) stüdyonun başlığıyla değiştirir.

  python3 sistem/claude/satici/satici.py kur [--zorla]     eksik olanı kurar (--zorla: yeniden kurar)
  python3 sistem/claude/satici/satici.py dogrula           kurulu mu, başlık yerinde mi

Yeni sürüme geçmek (arac-radari): commit'i güncelle, `kur --zorla`, satıcı metnini yasaklara karşı tara
(Google Fonts, Studio'yu kendiliğinden açma, lisans anahtarı, uzak varlık, @latest), KAYNAKLAR.md'yi güncelle.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BURASI = Path(__file__).resolve().parent
BECERILER = BURASI.parent / "skills"
ISARET = "Stüdyo kuralları — önce bunlar"

SATICI = [
    {
        "ad": "remotion-best-practices",
        "depo": "https://github.com/remotion-dev/skills",
        "commit": "0b5db9daae40f42c73544d1cc0a8c733bd530eaa",   # 2026-10-05, Remotion 4.0.532 için yazılmış
        "yol": "skills/remotion-best-practices",
        "sil": ["agents"],                                       # başka istemcinin (Codex) ayarı
        "baslik": "remotion-ev-kurallari.md",
        "lisans": "depoda lisans yok (2026-10-05) → yeniden dağıtılmaz, kurulumda indirilir",
    },
]


def _git(*arg: str, cwd: Path) -> str:
    return subprocess.run(["git", *arg], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def _onbilgisiz(metin: str) -> str:
    """'---\\n…\\n---\\n' satıcı ön bilgisini atar, gövdeyi döndürür."""
    if not metin.startswith("---\n"):
        return metin
    son = metin.index("\n---\n", 4)
    return metin[son + len("\n---\n"):]


def kur(zorla: bool = False) -> int:
    hata = 0
    for s in SATICI:
        hedef = BECERILER / s["ad"]
        if not zorla and (hedef / "SKILL.md").exists() and ISARET in (hedef / "SKILL.md").read_text():
            print(f"  {s['ad']}: kurulu")
            continue
        with tempfile.TemporaryDirectory() as g:
            gd = Path(g)
            _git("init", "-q", cwd=gd)
            _git("fetch", "-q", "--depth", "1", s["depo"], s["commit"], cwd=gd)
            _git("checkout", "-q", "FETCH_HEAD", cwd=gd)
            if _git("rev-parse", "HEAD", cwd=gd) != s["commit"]:
                print(f"  ✗ {s['ad']}: commit tutmadı")
                hata += 1
                continue
            if hedef.exists():
                shutil.rmtree(hedef)
            shutil.copytree(gd / s["yol"], hedef)
        for d in s["sil"]:
            shutil.rmtree(hedef / d, ignore_errors=True)
        govde = _onbilgisiz((hedef / "SKILL.md").read_text()).lstrip("\n")
        (hedef / "SKILL.md").write_text((BURASI / s["baslik"]).read_text() + govde)
        print(f"  {s['ad']}: {s['commit'][:7]} kuruldu (+ stüdyo başlığı)")
    return 1 if hata else 0


def dogrula() -> int:
    eksik = [s["ad"] for s in SATICI
             if not (BECERILER / s["ad"] / "SKILL.md").exists()
             or ISARET not in (BECERILER / s["ad"] / "SKILL.md").read_text()]
    print("tamam" if not eksik else f"eksik/başlıksız: {eksik} → python3 {Path(__file__)} kur")
    return 1 if eksik else 0


if __name__ == "__main__":
    komut = sys.argv[1] if len(sys.argv) > 1 else "dogrula"
    sys.exit(kur("--zorla" in sys.argv) if komut == "kur" else dogrula())
