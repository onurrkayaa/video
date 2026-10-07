#!/usr/bin/env python3
"""SessionStart kancası: stüdyonun kısa durumunu oturumun başında Claude'a bağlam olarak verir.

Baş ajanın (medya-yonetici) gözü: yarım iş var mı, son yönetici incelemesinden kaç gün geçti (30+ gün → kullanıcıya
inceleme öner), kullanıcı kararını bekleyen kaç madde var, disk durumu (ağır ML öncesi), git'te kayıtsız/gönderilmemiş
iş. Hızlıdır (< 1 sn), hiçbir durumda oturumu engellemez (her hata yutulur, çıkış 0).
"""
from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
INCELEME_GUN = 30


def _durum() -> tuple[str, int]:
    d = KOK / "sistem" / "DURUM.md"
    if not d.exists():
        return "bilinmiyor", 0
    s = d.read_text(encoding="utf-8")
    m = re.search(r"\*\*([^*]+)\*\*", s)
    baslik = m.group(1).strip() if m else "?"
    bolum = s.split("## Kullanıcının kararını bekleyenler", 1)
    bekleyen = 0
    if len(bolum) == 2:
        govde = bolum[1].split("\n## ", 1)[0]
        bekleyen = sum(1 for l in govde.splitlines() if l.startswith("- "))
    return baslik, bekleyen


def _son_inceleme() -> tuple[str | None, int | None]:
    tarihler = []
    for kl in ("yonetim", "radar"):
        for f in (KOK / "sistem" / kl).glob("20??-??-??-*.md"):
            try:
                tarihler.append(dt.date.fromisoformat(f.name[:10]))
            except ValueError:
                pass
    if not tarihler:
        return None, None
    son = max(tarihler)
    return son.isoformat(), (dt.date.today() - son).days


def _git() -> str:
    try:
        degisen = subprocess.run(["git", "-C", str(KOK), "status", "--porcelain"], capture_output=True, text=True,
                                 timeout=3).stdout.strip().splitlines()
        ileri = subprocess.run(["git", "-C", str(KOK), "rev-list", "--count", "@{u}..HEAD"], capture_output=True,
                               text=True, timeout=3).stdout.strip() or "?"
        return f"{len(degisen)} kayıtsız değişiklik, {ileri} gönderilmemiş commit"
    except Exception:
        return "bilinmiyor"


def main() -> int:
    try:
        baslik, bekleyen = _durum()
        son, gun = _son_inceleme()
        bos = shutil.disk_usage(KOK).free / 1e9
        satirlar = [f"STÜDYO ÖZETİ (otomatik, oturum başı): durum: {baslik}"]
        if "DURAKLATILDI" in baslik.upper():
            satirlar.append("→ yarım iş var: önce sistem/DURUM.md'yi oku, kullanıcıya hatırlat ve sor.")
        if son is None:
            satirlar.append("son yönetici incelemesi: yok → uygun anda kullanıcıya `medya-yonetim` incelemesi öner.")
        else:
            satirlar.append(f"son yönetici incelemesi/radar: {son} ({gun} gün önce)"
                            + (f" → {INCELEME_GUN} günü geçti: kullanıcıya inceleme öner (medya-yonetim, radar: true)."
                               if gun >= INCELEME_GUN else "."))
        if bekleyen:
            satirlar.append(f"kullanıcı kararını bekleyen madde: {bekleyen} (sistem/DURUM.md) — ilgili iş gelince hatırlat.")
        disk = f"boş disk: {bos:.1f} GB (taban 5 GB"
        if bos < 5:
            disk += "; DÜŞÜK → ağır ML/çizimden önce kullanıcıya söyle: yeniden başlatma takası boşaltır, yer aç"
        satirlar.append(disk + ").")
        satirlar.append(f"git: {_git()}.")
        cikti = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n".join(satirlar)}}
        print(json.dumps(cikti, ensure_ascii=False))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
