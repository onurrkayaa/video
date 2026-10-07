"""Yetenek kayıt defteri: yetenekler.toml'u okur, sağlayıcıların kurulu olup olmadığını denetler.

Yetenek = ne yapılacağı (vuruş bul, yazıya dök, ağır çekim…); sağlayıcı = bunu yapan araç.
Beceriler ve ajanlar yeteneği çağırır; aracı değiştirmek için yalnız kayıt ve uyarlayıcı değişir.
"""
from __future__ import annotations

import shlex
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .ortak import KOK, MedyaHatasi

KAYIT = KOK / "yetenekler.toml"


@dataclass
class Saglayici:
    ad: str
    tur: str                      # ikili | python-arac | python-paket | node | uygulama (GUI, kullanıcı kurar) | bulut-ucretli
    lisans: str = "?"
    ticari: str = "?"             # evet | hayir | kosullu | ?
    kurulum: str = ""
    kontrol: str = ""
    boyut_mb: float = 0
    etkin: bool = True            # bulut-ucretli sağlayıcılar varsayılan olarak kapalı
    onay: str = ""                # etkinleştirmek için gereken kullanıcı onayı (ör. "ücretli hesap")
    not_: str = ""

    def kurulu_mu(self) -> bool:
        if not self.kontrol:
            return False
        try:
            r = subprocess.run(shlex.split(self.kontrol), capture_output=True, stdin=subprocess.DEVNULL, timeout=60,
                               cwd=KOK)
            return r.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False


@dataclass
class Yetenek:
    ad: str
    komut: str
    aciklama: str
    saglayici: str
    yedek: list[str] = field(default_factory=list)   # birincil yoksa sırayla denenenler
    alan: str = ""


def yukle() -> tuple[dict[str, Yetenek], dict[str, Saglayici]]:
    if not KAYIT.exists():
        raise MedyaHatasi(f"kayıt defteri yok: {KAYIT}")
    veri = tomllib.loads(KAYIT.read_text())
    saglayicilar = {}
    for s in veri.get("saglayici", []):
        not_ = s.pop("not", "")
        saglayicilar[s["ad"]] = Saglayici(**s, not_=not_)
    yetenekler = {y["ad"]: Yetenek(**y) for y in veri.get("yetenek", [])}
    for y in yetenekler.values():
        for ad in [y.saglayici, *y.yedek]:
            if ad not in saglayicilar:
                raise MedyaHatasi(f"yetenek '{y.ad}' bilinmeyen sağlayıcıya bağlı: {ad}")
    return yetenekler, saglayicilar


def saglayici_sec(yetenek_adi: str) -> Saglayici:
    """Yetenek için kurulu ve etkin ilk sağlayıcı (birincil, sonra yedekler)."""
    yetenekler, saglayicilar = yukle()
    if yetenek_adi not in yetenekler:
        raise MedyaHatasi(f"bilinmeyen yetenek: {yetenek_adi}")
    y = yetenekler[yetenek_adi]
    adaylar = [saglayicilar[a] for a in [y.saglayici, *y.yedek]]
    for s in adaylar:
        if s.etkin and s.kurulu_mu():
            return s
    ilk = adaylar[0]
    raise MedyaHatasi(f"'{yetenek_adi}' için kurulu sağlayıcı yok. Birincil: {ilk.ad} "
                      f"({ilk.lisans}, ~{ilk.boyut_mb:.0f} MB). Kurmak için: medya kur {ilk.ad}")
