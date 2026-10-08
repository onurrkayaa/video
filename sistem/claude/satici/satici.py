#!/usr/bin/env python3
"""Satıcı (vendor) becerileri: sabit commit'ten indirilir, doğrulanır, sistem/claude/skills/ altına kurulur.

Satıcı içeriği depoya girmez (.gitignore): lisansı yeniden dağıtıma izin vermiyor ya da belirsiz (Remotion) ya da
stüdyonun kuralı onu kurulumda üretmek (HyperFrames). Kurulum: seyrek git fetch (yalnız gereken klasörler,
--filter=blob:none) → HEAD commit kimliğiyle aynı mı → her dosyanın git blob SHA'sı commit ağacıyla aynı mı (satır
sonu ya da LFS süzgeci içeriği bozmasın) → içerik özeti (SHA-256) kayıttakiyle aynı mı → kopya. İstenirse istenmeyen
klasörler silinir ve SKILL.md'nin satıcı ön bilgisi (frontmatter) stüdyonun başlığıyla değiştirilir.

  python3 sistem/claude/satici/satici.py kur [--zorla]     eksik olanı kurar (--zorla: yeniden kurar)
  python3 sistem/claude/satici/satici.py dogrula           kurulu mu, başlık ve özet tutuyor mu, ~/.claude/skills bağlı mı
  python3 sistem/claude/satici/satici.py bagla [--uygula]  ~/.claude/skills/<ad> → sistem/claude/skills/<ad>; aynı adlı
        eski gerçek kopyalar (npx skills --copy: ~/.claude/skills, ~/.agents/skills) önce sistem/devam/ham/'a yedeklenir,
        arşiv sayılır, sonra kaldırılır. --uygula olmadan yalnız planı yazar (kullanıcının dosyası: önce sor).
  python3 sistem/claude/satici/satici.py bagla --geri <arşiv> [--uygula]   bagla'yı geri alır: arşivdeki kopyaların
        yerindeki bağlantıyı kaldırır, kopyaları geri koyar. `tar -xzf` bunu yapamaz (bsdtar bağlantının içine açmaz).

Yeni sürüme geçmek (arac-radari → güncelleme-ve-disk §3): commit'i değiştir, 'ozet'i boşalt (""), `kur --zorla`,
satıcı metnini yasaklara karşı tara (Google Fonts, Studio'yu kendiliğinden açma, lisans anahtarı, uzak varlık,
@latest, feedback/usage), yazdırılan özeti kayda geçir, KAYNAKLAR.md'yi güncelle.
"""
from __future__ import annotations

import datetime
import hashlib
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

BURASI = Path(__file__).resolve().parent
BECERILER = BURASI.parent / "skills"
YEDEK = BURASI.parent.parent / "devam" / "ham"
ISARET = "Stüdyo kuralları — önce bunlar"
HF_BECERILERI = ("embedded-captions", "faceless-explainer", "figma", "general-video", "hyperframes",
                 "hyperframes-animation", "hyperframes-audio", "hyperframes-cli", "hyperframes-core",
                 "hyperframes-creative", "hyperframes-keyframes", "hyperframes-registry", "hyperframes-studio",
                 "media-use", "motion-graphics", "music-to-video", "pr-to-video", "product-launch-video",
                 "remotion-to-hyperframes", "slideshow", "talking-head-recut")

SATICI = [
    {
        "ad": "remotion-best-practices",
        "depo": "https://github.com/remotion-dev/skills",
        "commit": "0b5db9daae40f42c73544d1cc0a8c733bd530eaa",   # 2026-10-01, Remotion 4.0.532 için yazılmış
        "yollar": ["skills/remotion-best-practices"],
        "sil": ["agents"],                                       # başka istemcinin (Codex) ayarı
        "baslik": "remotion-ev-kurallari.md",
        "lisans": "depoda lisans yok (2026-10-05) → yeniden dağıtılmaz, kurulumda indirilir",
    },
    {
        "ad": "hyperframes",
        "depo": "https://github.com/heygen-com/hyperframes",
        "commit": "5c7f6316d3646477a0f725176c00335cb8575560",   # v0.8.140 etiketi (2026-10-07) = package.json CLI'si
        "yollar": [f"skills/{b}" for b in HF_BECERILERI],         # 2026-10-08'de kurulu 21 beceri = etiketteki hepsi
        "sil": [],
        "baslik": None,                                          # satıcı ön bilgisi korunur; kurallar kanca + medya-studyo
        "ozet": "ba8fbc0afab7540c72694b16c0c8ac1d308b36ace7fdebf4b4af2041107c118e",   # 931 dosya
        "lisans": "Apache-2.0 (kod, metin); media-use sfx/*.mp3 Pixabay Content License, yazı tipleri OFL, "
                  "talking-head-recut MIT uyarlaması — ticari serbest; depoya alınmaz, kurulumda üretilir",
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


def _blob(dosya: Path) -> str:
    """Dosyanın git blob SHA-1'i (git hash-object ile aynı)."""
    veri = dosya.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(veri) + veri).hexdigest()


def _ozet(satirlar) -> str:
    """İçerik özeti: sıralı 'kip blob beceri/yol' satırlarının SHA-256'sı."""
    return hashlib.sha256("".join(f"{s}\n" for s in sorted(satirlar)).encode()).hexdigest()


def _kurulu_ozet(s: dict) -> str:
    satirlar = []
    for yol in s["yollar"]:
        kok = BECERILER / Path(yol).name
        for f in kok.rglob("*"):
            if f.is_file() and f.name != ".DS_Store" and "__pycache__" not in f.parts:
                kip = "100755" if f.stat().st_mode & 0o100 else "100644"
                satirlar.append(f"{kip} {_blob(f)} {Path(yol).name}/{f.relative_to(kok).as_posix()}")
    return _ozet(satirlar)


def _kurulu_mu(s: dict, ad: str) -> bool:
    skill = BECERILER / ad / "SKILL.md"
    return skill.exists() and (not s["baslik"] or ISARET in skill.read_text())


def _bagli_mi(ad: str) -> bool:
    return (Path.home() / ".claude" / "skills" / ad).resolve() == (BECERILER / ad).resolve()


def kur(zorla: bool = False) -> int:
    hata = 0
    for s in SATICI:
        adlar = [Path(y).name for y in s["yollar"]]
        if not zorla and all(_kurulu_mu(s, ad) for ad in adlar):
            print(f"  {s['ad']}: kurulu")
            continue
        with tempfile.TemporaryDirectory() as g:
            gd = Path(g)
            _git("init", "-q", cwd=gd)
            _git("remote", "add", "origin", s["depo"], cwd=gd)
            _git("sparse-checkout", "set", "--no-cone", *[f"/{y}/" for y in s["yollar"]], cwd=gd)
            _git("fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", s["commit"], cwd=gd)
            _git("checkout", "-q", "FETCH_HEAD", cwd=gd)
            if _git("rev-parse", "HEAD", cwd=gd) != s["commit"]:
                print(f"  ✗ {s['ad']}: commit tutmadı")
                hata += 1
                continue
            agac = []                                            # (kip, blob, beceri/yol, çekilen dosya)
            for satir in _git("ls-tree", "-r", "HEAD", "--", *s["yollar"], cwd=gd).splitlines():
                meta, yol = satir.split("\t", 1)
                kip, _, blob = meta.split()
                kaynak = next(y for y in s["yollar"] if yol.startswith(y + "/"))
                agac.append((kip, blob, Path(kaynak).name + yol[len(kaynak):], gd / yol))
            eksik = [y for y in s["yollar"] if not (gd / y / "SKILL.md").exists()]
            bozuk = [g for _, blob, g, f in agac if _blob(f) != blob]
            ozet = _ozet(f"{k} {b} {g}" for k, b, g, _ in agac)
            if eksik or bozuk or (s.get("ozet") and ozet != s["ozet"]):
                print(f"  ✗ {s['ad']}: commit'te olmayan beceri {eksik}, blob SHA'sı tutmayan {bozuk[:3]}, "
                      f"özet {ozet} (kayıtta {s.get('ozet')}) — hiçbir şey kurulmadı")
                hata += 1
                continue
            for y in s["yollar"]:
                hedef = BECERILER / Path(y).name
                if hedef.exists():
                    shutil.rmtree(hedef)
                shutil.copytree(gd / y, hedef)
                for d in s["sil"]:
                    shutil.rmtree(hedef / d, ignore_errors=True)
                if s["baslik"]:
                    govde = _onbilgisiz((hedef / "SKILL.md").read_text()).lstrip("\n")
                    (hedef / "SKILL.md").write_text((BURASI / s["baslik"]).read_text() + govde)
        if s.get("ozet") and _kurulu_ozet(s) != s["ozet"]:
            print(f"  ✗ {s['ad']}: kopyalanan içerik özetle tutmuyor")
            hata += 1
            continue
        print(f"  {s['ad']}: {s['commit'][:7]} kuruldu ({len(adlar)} beceri, {len(agac)} dosya; blob SHA'ları commit "
              f"ağacıyla aynı{', özet tuttu' if s.get('ozet') else ''}{'; + stüdyo başlığı' if s['baslik'] else ''})")
        if "ozet" in s and not s["ozet"]:                        # yeni commit: içeriği inceledikten sonra kayda yaz
            print(f"    özet {ozet} → satici.py'de 'ozet' alanına yaz")
    return 1 if hata else 0


def dogrula() -> int:
    sorun = []
    for s in SATICI:
        adlar = [Path(y).name for y in s["yollar"]]
        eksik = [ad for ad in adlar if not _kurulu_mu(s, ad)]
        if eksik:
            sorun.append(f"{s['ad']}: kurulu değil ya da başlıksız {eksik} → python3 {Path(__file__)} kur")
            continue
        if s.get("ozet") and _kurulu_ozet(s) != s["ozet"]:
            sorun.append(f"{s['ad']}: içerik {s['commit'][:7]} ile aynı değil (elle düzenleme ya da eski kurulum) → "
                         f"python3 {Path(__file__)} kur --zorla")
        bagsiz = [ad for ad in adlar if not _bagli_mi(ad)]
        if bagsiz:
            eski = [ad for ad in bagsiz if (Path.home() / ".claude" / "skills" / ad).is_dir()
                    and not (Path.home() / ".claude" / "skills" / ad).is_symlink()]
            sorun.append(f"{s['ad']}: {len(bagsiz)} beceri ~/.claude/skills'e bağlı değil, {len(eski)} tanesinde eski "
                         f"gerçek kopya etkin (sabit kopya devrede değil) → python3 {Path(__file__)} bagla --uygula")
    print("tamam" if not sorun else "\n".join(sorun))
    return 1 if sorun else 0


def bagla(uygula: bool = False) -> int:
    ev = Path.home()
    adlar = [Path(y).name for s in SATICI for y in s["yollar"]]
    eksik = [ad for ad in adlar if not (BECERILER / ad / "SKILL.md").exists()]
    if eksik:
        print(f"önce kur: {eksik} → python3 {Path(__file__)} kur")
        return 1
    eski = [ev / k / ad for k in (".claude/skills", ".agents/skills") for ad in adlar
            if (ev / k / ad).is_dir() and not (ev / k / ad).is_symlink()]
    baglanacak = [ad for ad in adlar if not _bagli_mi(ad)]
    dosyalar = [f for p in eski for f in p.rglob("*") if f.is_file()]
    print(f"eski gerçek kopya: {len(eski)} klasör ({len(dosyalar)} dosya, "
          f"{sum(f.stat().st_size for f in dosyalar) / 1e6:.1f} MB); bağlanacak: {len(baglanacak)} beceri")
    if not uygula:
        if eski or baglanacak:
            print(f"kuru çalıştırma — uygulamak için: python3 {Path(__file__)} bagla --uygula")
        return 0
    if eski:
        YEDEK.mkdir(parents=True, exist_ok=True)
        gun, n = datetime.date.today().isoformat(), 1
        arsiv = YEDEK / f"satici-yedek-{gun}.tar.gz"
        while arsiv.exists():                                    # eski yedeğin üzerine yazılmaz
            n += 1
            arsiv = YEDEK / f"satici-yedek-{gun}-{n}.tar.gz"
        kilit = ev / ".agents" / ".skill-lock.json"              # npx skills kaydı: yedeğe girer, yerinde kalır
        ekler = [kilit] if kilit.is_file() else []
        with tarfile.open(arsiv, "w:gz") as t:
            for p in eski + ekler:
                t.add(p, arcname=str(p.relative_to(ev)))
        with tarfile.open(arsiv) as t:
            arsivde = sum(1 for m in t.getmembers() if m.isfile())
        if arsivde != len(dosyalar) + len(ekler):
            print(f"✗ yedek eksik ({arsivde}/{len(dosyalar) + len(ekler)} dosya): hiçbir şey kaldırılmadı")
            return 1
        for p in eski:
            shutil.rmtree(p)
        print(f"  yedek: {arsiv} ({arsivde} dosya); {len(eski)} eski kopya kaldırıldı "
              f"(geri almak: python3 {Path(__file__)} bagla --geri {arsiv} --uygula)")
        ajanlar = [p.name for p in eski if p.parent == ev / ".agents" / "skills"]
        for ad in ajanlar:                                       # ~/.agents/skills'i okuyan başka ajanlar kaybetmesin
            (ev / ".agents" / "skills" / ad).symlink_to(BECERILER / ad)
        if ajanlar:
            print(f"  {len(ajanlar)} bağlantı: ~/.agents/skills/<ad> → {BECERILER}/<ad> (eski kopyanın yerine)")
    for ad in baglanacak:
        hedef = ev / ".claude" / "skills" / ad
        if hedef.is_symlink():
            hedef.unlink()
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.symlink_to(BECERILER / ad)
    print(f"  {len(baglanacak)} bağlantı: ~/.claude/skills/<ad> → {BECERILER}/<ad>")
    return 0


def geri(arsiv: Path, uygula: bool = False) -> int:
    """bagla --uygula'yı geri alır. Önce arşivdeki kopyaların yerindeki bağlantı (yalnız sistem/claude/skills/<ad>'ı
    gösteren) kaldırılır: bsdtar bağlantının içine açmaz ("Cannot extract through symlink"), bağlantıyı izleyen açıcı
    (tarfile, tar -P) eski içeriği sabit kopyanın üzerine yazar (2026-10-08, sahte ev klasöründe ölçüldü). Yerde gerçek
    klasör ya da başka yeri gösteren bağlantı varsa hiçbir şeye dokunmaz; bagla'nın yerinde bıraktığı kayıt dosyası korunur."""
    ev, kilit = Path.home(), Path(".agents") / ".skill-lock.json"
    if not arsiv.is_file():
        print(f"✗ arşiv yok: {arsiv}")
        return 1
    with tarfile.open(arsiv) as t:
        kokler = {}                                              # geri konacak yer (ev'e göre) → arşiv üyeleri
        for m in t.getmembers():
            p = Path(m.name).parts
            if len(p) >= 3 and p[1] == "skills" and p[0] in (".claude", ".agents") and ".." not in p \
                    and (m.isfile() or m.isdir()):
                kokler.setdefault(Path(*p[:3]), []).append(m)
            elif Path(m.name) == kilit and m.isfile():
                kokler.setdefault(kilit, []).append(m)
            else:
                print(f"✗ {arsiv}: beklenmeyen üye {m.name} (bagla'nın yedeği değil): hiçbir şey değişmedi")
                return 1
        baglar, yerinde, cakisan = [], [], []
        for k in kokler:
            yer = ev / k
            if yer.is_symlink() and yer.resolve() == (BECERILER / yer.name).resolve():
                baglar.append(yer)
            elif k == kilit and yer.is_file() and not yer.is_symlink():
                yerinde.append(k)                                # bagla kaldırmadı: güncel olan kalır
            elif yer.exists() or yer.is_symlink():
                cakisan.append(yer)
        if cakisan:
            print(f"✗ geri alınamaz, hiçbir şey değişmedi: {len(cakisan)} yerde gerçek klasör ya da başka yeri gösteren "
                  f"bağlantı var (ör. {cakisan[0]})")
            return 1
        secilen = [m for k, ms in kokler.items() if k not in yerinde for m in ms]
        dosya = sum(1 for m in secilen if m.isfile())
        print(f"geri alma: {len(baglar)} bağlantı kaldırılacak, {len(kokler) - len(yerinde)} yer ({dosya} dosya) "
              f"arşivden geri konacak" + (f"; yerinde kalan: {', '.join(map(str, yerinde))}" if yerinde else ""))
        if not uygula:
            print(f"kuru çalıştırma — uygulamak için: python3 {Path(__file__)} bagla --geri {arsiv} --uygula")
            return 0
        for yer in baglar:
            yer.unlink()                                         # yalnız bağlantı; gösterdiği sabit kopya yerinde kalır
        t.extractall(ev, members=secilen, **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
    gelen = sum(1 for k in kokler if k not in yerinde
                for f in ([ev / k] if (ev / k).is_file() else (ev / k).rglob("*")) if f.is_file())
    if gelen != dosya:
        print(f"✗ geri konan dosya sayısı tutmuyor ({gelen}/{dosya}); arşiv yerinde: {arsiv}")
        return 1
    print(f"  {len(baglar)} bağlantı kaldırıldı, {dosya} dosya geri kondu: eski kopyalar yine etkin (dogrula söyler)")
    return 0


if __name__ == "__main__":
    komut = sys.argv[1] if len(sys.argv) > 1 else "dogrula"
    if komut == "kur":
        sys.exit(kur("--zorla" in sys.argv))
    if komut == "bagla" and "--geri" in sys.argv:
        yol = [a for a in sys.argv[2:] if not a.startswith("--")]
        if len(yol) != 1:
            sys.exit(f"kullanım: python3 {Path(__file__)} bagla --geri <arşiv.tar.gz> [--uygula]")
        sys.exit(geri(Path(yol[0]).expanduser(), "--uygula" in sys.argv))
    sys.exit(bagla("--uygula" in sys.argv) if komut == "bagla" else dogrula())
