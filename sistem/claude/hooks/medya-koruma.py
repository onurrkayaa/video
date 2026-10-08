#!/usr/bin/env python3
"""Claude Code PreToolUse (Bash) kancası — medya işlerinde kullanıcının kesin kurallarını zorlar.

Kaynak: /Users/onurkaya/Projects/video/sistem/claude/hooks/medya-koruma.py (sürümlü). ~/.claude/settings.json
içindeki PreToolUse kancası bu dosyayı çalıştırır; ana oturumda, alt ajanlarda ve iş akışı ajanlarında geçerlidir.

Engeller (çıkış kodu 2; gerekçe stderr'den Claude'a döner) — yalnız komut gerçekten ÇALIŞTIRILIYORSA:
- hyperframes cloud | lambda | cloudrun | auth | publish | usage | feedback   (ücretli/bulut/hesap/dış istek;
  feedback --file-issue projeyi GitHub'a yayımlar, --search-miss HeyGen'e rapor yollar)
- hyperframes telemetry enable                                               (analiz verisi kapalı kalmalı)
- hyperframes snapshot, '--'dan önceki her --describe değeri birebir 'false' değilse (GEMINI_API_KEY varsa kareler
  Google'a gider; CLI yalnız "false"u kapatma sayar: 0, no, False, boş değer soru olur; tekrar edende son değer geçer)
- hyperframes media-use resolve|doctor|adopt|from (grade/lut dışı)           (HeyGen hesabı/katalogu, ücretli avatar video)
- heygen …                                                                   (HeyGen bulut CLI'si: hesap/OAuth/kredi)
- remotion lambda | cloudrun | upgrade | skills, --public-license-key/--license-key (bulut çizim, sabit sürümü
  bozan yükseltme, telemetrili kurulum; lisans anahtarı 'free-license' dahil remotion.pro'ya kullanım olayı yollar)
- npx create-video / npx skills …  ve  @remotion/web-renderer|google-fonts|lambda|cloudrun|vercel|sfx|mcp kurulumu
- sessiz büyük indirmeler: hyperframes remove-background (~394 MB model), whisperx (uvx/pip/uv, 'python3 -m pip',
  sürüm sabitli 'whisperx==3.8.6' dahil, büyük/küçük harf duyarsız: PyPI adları öyle, ~2 GB) — stüdyonun
  indirmesiz/kurulu karşılıkları var; gerçekten gerekiyorsa önce boyutu söyleyip kullanıcıya sorulur
- hyperframes transcribe <ses/video> (yalnız .json/.srt/.vtt girdisi serbest; görünür girdisi olmayan çağrı da engelli:
  'xargs … transcribe' girdiyi stdin'den alır, kanca göremez), init --video/--audio/-v/-a ve kısa bayrak grupları
  (-vv.mp4; --skip-transcribe yoksa; citty parseArgs bu grupları video sayar, cli.js assertKnownFlags çalıştırmadan
  reddeder, kanca temkinli engeller), tts, models install — sormadan whisper.cpp (brew) + ggml modeli, Kokoro ya da
  Parakeet indirir
- hyperframes upgrade (--project dahil) ve skills (check dışında) — sabit sürümü ya da satıcı beceri kaynağını bozar
- tam sürüm dışı hyperframes@ (latest, next, ^, ~, aralık, etiket): npx/bunx/dlx/npm exec ile ya da -p/--package
  değeri olarak; npm/pnpm/yarn/bun i|install|add|update|up|upgrade'de sürümsüz ad da (latest kurup ^ ile kaydeder) —
  sabit sürümü bozar. Serbest: 'npm i -D -E hyperframes@x.y.z', 'npx hyperframes@x.y.z', çıplak 'npx hyperframes'
- indirme yapan satıcı betikleri: embedded-captions scripts/prepare.sh, transcribe.cjs, matte.cjs; media-use
  scripts/transcribe.mjs — bash/sh/source/node ile ya da yol vererek doğrudan çalıştırılınca. Adlar genel olduğundan
  yalnız yolda, komutta ya da çalışma klasöründe beceri adı geçiyorsa tutulur; cat/sed/grep/find ile okuma ve
  'node --check' / 'bash -n' sözdizimi denetimi serbest
Bu iki hyperframes kuralında --help/-h serbesttir (CLI o zaman komutu çalıştırmaz, yalnız kullanımı yazar).
Ayrıştırma kabuk kurallarına uyar: tek tırnak içi ve tırnaklı heredoc gövdesi VERİDİR (engellenmez); satır sonları,
; && || | & komut ayırır; ters bölü + satır sonu (satır devamı) kabuktaki gibi silinir (ön süzgeçte de);
yönlendirmeler (2>&1, >/dev/null, > x.json, < x; işleç, hedefi ve işlece bitişik fd rakamı — 'timeout 600 >x'te 600
argümandır) argüman sayılmaz, 'bash < betik' girdisi betik olarak denetlenir; $(…) ve `…` (tek tırnak dışında) ile
kabuğa giden heredoc gövdeleri ayrıca denetlenir; npx/bunx/pnpm dlx/npm exec (-p/--package değeriyle), yol önekli
ikili, `node …/hyperframes.mjs`, env/time/nohup/exec/sudo/xargs/timeout/caffeinate/nice önekleri (yol önekli
/usr/bin/env dahil; değer alan bayraklarının değeriyle, timeout'un süresiyle), ortam atamaları, `sh|bash|zsh -c "…"`
ve eval yakalanır.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

YASAK = {"cloud", "lambda", "cloudrun", "auth", "publish", "usage", "feedback"}
SESSIZ_INDIRME = {"remove-background": "arka plan için 'medya arkaplan-sil' (Apple Vision, indirme yok)"}
AYRAC = {";", "&&", "||", "|", "&", "(", ")", "|&", ";;"}
# shlex'in (punctuation_chars) verdiği yönlendirme işleçleri; hedefleri argüman değildir (işlece bitişik fd rakamını,
# 2>&1'deki 2'yi, fd_sil önceden siler)
YONLENDIRME = {">", ">>", "<", "<<", "<<<", "<>", ">|", ">&", "<&", "&>", "&>>"}
PAKET_BAYRAK = ("-p", "--package")           # npx/npm exec/dlx: çalıştırılacak paketi verir (değer alır)
# Önekler (ad ya da yolun son parçası: /usr/bin/env) → ayrık değer alan bayrakları; değer de atlanır (xargs -n 1,
# nice -n 10). Bayraklar bu Mac'in man sayfalarından; timeout GNU/FreeBSD'den (bu Mac'te yok) ve süresi de atlanır.
ONEK = {"npx": PAKET_BAYRAK, "bunx": (), "exec": (), "time": (), "nohup": (), "command": (), "sudo": (), "builtin": (),
        "then": (), "do": (), "else": (), "if": (), "while": (), "until": (), "!": (), "{": (), "}": (),
        "env": ("-u", "-C", "-P", "-S"), "xargs": ("-E", "-I", "-J", "-L", "-n", "-P", "-R", "-S", "-s"),
        "timeout": ("-s", "--signal", "-k", "--kill-after"), "caffeinate": ("-t", "-w"), "nice": ("-n",)}
PIP = ("uvx", "pip", "pip3", "uv", "pipx")
KABUK = {"sh", "bash", "zsh", "dash", "ksh"}
CALISTIRICI = {"node", "bun", "deno"}
HF = re.compile(r"^(?:.*/)?hyperframes(?:@[\w.\-]+)?(?:\.m?js)?$")
HF_PAKET = re.compile(r"^hyperframes(?:@(.*))?$")              # paket belirteci: sürümsüz ya da @sürüm/etiket/aralık
TAM_SURUM = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.\-]+)?$")  # 0.8.140, 0.9.0-beta.1; 0.8, 0.8.x, ^, latest değil
KURULUM = {"i", "install", "add", "update", "up", "upgrade"}    # npm/pnpm/yarn/bun: paket kuran ya da yükselten
RM = re.compile(r"^(?:.*/)?remotion(?:@[\w.\-]+)?$")
RM_YASAK = {"lambda", "cloudrun", "upgrade", "skills"}
RM_PAKET = re.compile(r"@remotion/(?:web-renderer|google-fonts|lambda|cloudrun|vercel|sfx|mcp|licensing)\b")
LISANS = re.compile(r"--(?:public-)?license-key\b")
ANAHTAR = ("hyperframes", "heygen", "remotion", "create-video", "skills", "whisperx", "prepare.sh", "transcribe.cjs",
           "matte.cjs", "transcribe.mjs")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
INDIRME = {"transcribe", "init", "tts", "models", "upgrade", "skills"}
YARDIM = {"--help", "-h"}                    # cli.js: argv'de varsa komut çalışmaz, yalnız kullanım yazılır
DOKUM = (".json", ".srt", ".vtt")            # transcribe bunları içe/dışa aktarır (indirmesiz)
DOKUM_DEGERLI = {"-d", "--dir", "-e", "--engine", "-m", "--model", "-l", "--language", "--to", "-o", "--output",
                 "--timeout"}                # transcribe'ın değer alan bayrakları: değerleri girdi sayılmaz
# init'in medya girdisi: --video/--audio, -v/-a ve kısa bayrak grupları (-vv.mp4, -yv x.mp4). citty parseArgs
# (util.parseArgs, strict:false) gruptaki bilinmeyen harfi boolean sayıp geçer, değer alan e/t/V kalanı kendi değeri
# olarak yutar; gerçek CLI (cli.js assertKnownFlags) bu grupları çalıştırmadan reddeder ('Unknown flag: -.'/'-y',
# ölçüldü 2026-10-08). Kanca temkinli engeller: o denetim bir sürümde gevşerse indirme yeniden açılır.
INIT_MEDYA = re.compile(r"^--(?:video|audio)(?:=|$)|^-(?!-)[^etVva]*[va]")
WHISPERX_SURUM = re.compile(r"^whisperx[=<>!~@\[]", re.I)  # sürüm/ek belirteçli paket (whisperX==3.8.6): her konumda
STUDYO_DOKUM = ("Stüdyo yolu: döküm/alt yazı 'medya yaziya-dok <dosya> --dil tr --srt' (Whisper large-v3-turbo, MLX, "
                "kurulu); HyperFrames'e indirmesiz içe aktarım 'hyperframes transcribe <x>.srt -d <proje>' (işaret "
                "düzeyinde; kelime zamanı için yaziya-dok JSON'undaki 'kelimeler'i [{text,start,end}] dizisine çevirip "
                ".json ver).")
SATICI_BETIK = {"prepare.sh": "embedded-captions", "transcribe.cjs": "embedded-captions",
                "matte.cjs": "embedded-captions", "transcribe.mjs": "media-use"}
BETIK_CALISTIRAN = KABUK | CALISTIRICI | {"source", "."}
BAGLAM = ""                                  # main(): komutun tamamı + çalışma klasörü (göreli betik yolu için)


class Engel(Exception):
    pass


def engelle(neden: str):
    raise Engel(neden)


# ------------------------------------------------------------------ kural denetimi
def alt_komut_denetle(arg: list[str]) -> None:
    """arg: hyperframes'ten sonraki argümanlar (bayraklar atlanarak ilk sözcük alt komuttur)."""
    sozcukler = [a for a in arg if not a.startswith("-")]
    if not sozcukler:
        return
    alt = sozcukler[0]
    metin = " ".join(arg)
    if alt in YASAK:
        engelle(f"'hyperframes {alt}' kullanılmaz — ücretli/bulut/hesap ya da dış istek. Kullanıcının kuralı: her şey "
                "bu bilgisayarda, yerelde çalışır; HeyGen'e geri bildirim/rapor da gönderilmez.")
    if alt == "telemetry" and len(sozcukler) > 1 and sozcukler[1] == "enable":
        engelle("HyperFrames analiz verisi kapalı kalmalı.")
    if alt == "media-use" and len(sozcukler) > 1 and sozcukler[1] in ("resolve", "doctor", "adopt", "from"):
        m = re.search(r"--type(?:=|\s+)(\S+)", metin)
        if not (sozcukler[1] == "resolve" and m and m.group(1) in ("grade", "lut")):
            engelle(f"'hyperframes media-use {sozcukler[1]}' HeyGen hesabına/çevrimiçi kataloğuna dayanır (kullanıcının "
                    "kuralı: hesap ve bulut yok). Stüdyonun yerel yollarını kullan: ses için ses-tasarimi, görsel için "
                    "gorsel-uretim becerisi (yalnız --type grade|lut yerel renk işleri serbest).")
    if alt in SESSIZ_INDIRME:
        engelle(f"'hyperframes {alt}' ilk kullanımda sormadan büyük model indirir; {SESSIZ_INDIRME[alt]}. Gerçekten "
                "gerekiyorsa boyutu söyleyip kullanıcıya sor.")
    if alt == "snapshot" and not describe_kapali(arg[arg.index(alt) + 1:]):
        engelle("'hyperframes snapshot' her zaman '--describe false' ile çalıştırılır (birebir 'false'; 0, no, False "
                "ya da boş değer Gemini'ye soru olarak gider); aksi hâlde GEMINI_API_KEY tanımlıysa kareler Google'a "
                "gönderilir.")
    if alt in INDIRME and not YARDIM & set(arg):
        indirme_denetle(alt, arg[arg.index(alt) + 1:])


def describe_kapali(kalan: list[str]) -> bool:
    """snapshot'ın Gemini açıklaması kapalı mı? CLI yalnız birebir "false"u kapatma sayar (0.8.140
    snapshot-SD5R3NWX.js:729); 0, no, False, boş değer soru olarak gider. citty 0.2.2 (node parseArgs, strict:false)
    tekrar eden bayrakta son değeri alır, '--'dan sonrasını konumsal sayar (ölçüldü 2026-10-08): '--'dan önceki her
    --describe değeri 'false' olmalı."""
    degerler = []
    for k, a in enumerate(kalan):
        if a == "--":
            break
        if a == "--describe":
            degerler.append(kalan[k + 1] if k + 1 < len(kalan) else "")
        elif a.startswith("--describe="):
            degerler.append(a.split("=", 1)[1])
    return bool(degerler) and all(d == "false" for d in degerler)


def surum_denetle(paketler: list[str], surumsuz_serbest: bool) -> None:
    """Sabit sürüm: hyperframes belirtecinde sürüm tam olmalı (x.y.z[-ön sürüm]). surumsuz_serbest: npx/dlx'te çıplak
    'hyperframes' kurulu sürümü çalıştırır; 'npm i hyperframes' ise latest kurar ve ^ ile kaydeder."""
    for p in paketler:
        m = HF_PAKET.match(p)
        if m and not (m.group(1) is None and surumsuz_serbest) and not TAM_SURUM.match(m.group(1) or ""):
            engelle(f"'{p}' sabit sürümü bozar: HyperFrames yalnız tam sürümle kurulur ya da çalıştırılır (ör. 'npm i "
                    "-D -E hyperframes@<x.y.z>'); latest, next, ^, ~, aralık ya da etiket package.json'daki sabit "
                    "sürümün yerine başkasını getirir. Stüdyoda 'npx hyperframes …' kurulu sürümü çalıştırır. "
                    "Yükseltme: arac-radari → güncelleme-ve-disk §3 (tam sürüm + sınama, kullanıcı onayıyla).")


def indirme_denetle(alt: str, kalan: list[str]) -> None:
    """Sessiz indirme ve sabit sürüm kuralları. kalan: alt komuttan sonraki argümanlar."""
    sozcukler = [a for a in kalan if not a.startswith("-")]
    if alt == "transcribe":
        girdiler, deger = [], False
        for a in kalan:
            if deger:
                deger = False
            elif a in DOKUM_DEGERLI:
                deger = True
            elif not a.startswith("-"):
                girdiler.append(a)
        if not girdiler:                             # xargs/stdin'den gelen girdi görünmez; girdisiz CLI zaten düşer
            engelle("'hyperframes transcribe' görünür girdisi yok: girdi xargs ya da stdin'den geliyor, kanca "
                    "denetleyemez (ses/video girdisinde sormadan whisper.cpp kurar ve ggml modeli indirir). Döküm "
                    f"dosyasını adıyla ver. {STUDYO_DOKUM}")
        yabanci = [g for g in girdiler if not g.lower().endswith(DOKUM)]
        if yabanci:
            engelle(f"'hyperframes transcribe' girdisi {', '.join(repr(g) for g in yabanci)} döküm dosyası "
                    "(.json/.srt/.vtt) değil: ses/video ya da değişkenli girdide sormadan whisper.cpp kurmaya ('brew "
                    "install whisper-cpp') ve ggml modeli indirmeye çalışır (small.en/small ~488 MB, large-v3 3,1 GB). "
                    f"{STUDYO_DOKUM} Gerçekten gerekiyorsa boyutu söyleyip kullanıcıya sor.")
    elif alt == "init":
        if any(INIT_MEDYA.match(a) for a in kalan) and not {"--skip-transcribe", "--skip-transcribe=true"} & set(kalan):
            engelle("'hyperframes init --video/--audio' '--skip-transcribe' olmadan dökümü aynı whisper yoluyla alır "
                    f"(sessiz 'brew install whisper-cpp' + ggml modeli). '--skip-transcribe' ekle. {STUDYO_DOKUM}")
    elif alt == "tts":
        engelle("'hyperframes tts' kokoro-onnx ve soundfile kuruluysa Kokoro modelini ve seslerini (311 + 27 MB) sormadan "
                "indirir; değilse 'pip install kokoro-onnx soundfile' ister (kurma). Türkçe yok. Dış ses: 'medya "
                "seslendir' (VoxCPM2, kurulu).")
    elif alt == "models" and sozcukler[:1] == ["install"]:
        engelle("'hyperframes models install' çalışma ortamı ve model indirir (parakeet: sherpa-onnx-node + 670 MB; "
                f"Türkçe yok). {STUDYO_DOKUM}")
    elif alt == "upgrade":
        engelle("'hyperframes upgrade' sabit sürümü bozar ('--project' hyperframes@sürüm sabitlerini en yeniye "
                "çevirir). Yükseltme: arac-radari → güncelleme-ve-disk §3 (tam sürüm + sınama, kullanıcı onayıyla).")
    elif alt == "skills" and sozcukler[:1] != ["check"]:
        engelle("'hyperframes skills' sabit olmayan GitHub HEAD'den 'npx skills add … --yes' çalıştırır (telemetri); "
                "'update' yayından kalkan becerileri siler. Yalnız 'hyperframes skills check' (salt okunur) serbest; "
                "satıcı becerileri sabit commit + SHA-256 ile (sistem/claude/satici/KAYNAKLAR.md).")


def satici_betik_denetle(yollar: list[str]) -> None:
    """Çalıştırılan dosyalar arasında indirme yapan bilinen satıcı betiği var mı? (Kanca alt süreçleri göremez.)
    Adların dördü de genel (başka projenin kendi transcribe.mjs'i olabilir; kanca bütün projelerde çalışır): yalnız
    yolda, komutta ya da çalışma klasöründe beceri adı geçiyorsa tutulur."""
    for yol in yollar:
        ad = yol.rsplit("/", 1)[-1]
        beceri = SATICI_BETIK.get(ad)
        if beceri and (beceri in yol or beceri in BAGLAM):
            engelle(f"'{ad}' ({beceri} satıcı betiği) alt süreçte sormadan indirir: transcribe.cjs 'uvx "
                    "whisperx==3.8.6', matte.cjs 'hyperframes remove-background', transcribe.mjs 'hyperframes "
                    "transcribe' (whisper.cpp + model); prepare.sh matte ile transcribe'ı birlikte çalıştırır. "
                    f"{STUDYO_DOKUM} Gerçekten gerekiyorsa boyutu söyleyip kullanıcıya sor.")


def yalniz_sozdizimi(ad: str, arg: list[str]) -> bool:
    """'node --check|-c x.js' ve 'bash|sh|zsh -n x.sh' betiği çalıştırmaz, yalnız sözdizimini denetler. Bayrak betikten
    önce gelmeli; sonra gelirse betiğin kendi argümanıdır."""
    for a in arg:
        if not a.startswith("-"):
            return False
        if (ad == "node" and a in ("--check", "-c")) or (ad in KABUK and re.match(r"^-[a-zA-Z]*n[a-zA-Z]*$", a)):
            return True
    return False


def python_modulu(arg: list[str]) -> tuple[str, list[str]]:
    """'python3 [-I] -m pip install x' ya da '-mpip install x' → ('pip', ['install', 'x']); modül yoksa ('', [])."""
    for k, a in enumerate(arg):
        if a == "-m":
            return (arg[k + 1], arg[k + 2:]) if k + 1 < len(arg) else ("", [])
        if a.startswith("-m"):
            return a[2:], arg[k + 1:]
        if not a.startswith("-"):
            break
    return "", []


def remotion_denetle(arg: list[str]) -> None:
    """arg: remotion'dan sonraki argümanlar."""
    if LISANS.search(" ".join(arg)):
        engelle("Remotion'a lisans anahtarı verilmez: 'free-license' dahil her anahtar her çizimden sonra "
                "remotion.pro'ya kullanım olayı gönderir (ölçüldü). Kişisel/≤3 kişilik işte anahtar gerekmez.")
    sozcukler = [a for a in arg if not a.startswith("-")]
    if sozcukler and sozcukler[0] in RM_YASAK:
        engelle(f"'remotion {sozcukler[0]}' kullanılmaz — bulut çizim, sabit sürümü (4.0.533) bozan yükseltme ya da "
                "telemetrili beceri kurulumu. Beceri: sistem/claude/skills/remotion-best-practices (sabit commit).")


# ------------------------------------------------------------------ kabuk ayrıştırma
def heredoc_ayikla(komut: str) -> tuple[str, list[str], list[str]]:
    """Heredoc gövdelerini komut metninden çıkarır.
    Döner: (gövdesiz komut, kabuğa giden gövdeler [tam denetlenir], ikameli gövdeler [yalnız $(…)/`…` denetlenir])."""
    satirlar = komut.split("\n")
    kalan, kabuga, ikameli = [], [], []
    i = 0
    while i < len(satirlar):
        satir = satirlar[i]
        kalan.append(satir)
        i += 1
        for tirnak, ayrac in HEREDOC.findall(satir):
            govde = []
            while i < len(satirlar) and satirlar[i].strip() != ayrac:
                govde.append(satirlar[i])
                i += 1
            i += 1                                            # bitiş satırı
            metin = "\n".join(govde)
            on = satir.split("<<", 1)[0]
            if re.search(r"(?:^|[\s;|&(])(?:\S*/)?(?:sh|bash|zsh|dash|ksh)\b[^|;&]*$", on):
                kabuga.append(metin)                          # gövde kabukta komut olarak çalışır
            elif not tirnak:
                ikameli.append(metin)                         # tırnaksız: içindeki ikameler çalışır
    return "\n".join(kalan), kabuga, ikameli


def tara(komut: str) -> tuple[str, list[str]]:
    """Tırnak durumunu izleyerek: (1) tırnak dışı satır sonlarını ';' yapar (komut ayırıcı),
    (2) tek tırnak dışındaki $(…) ve `…` ikamelerini toplar, (3) tek tırnak dışındaki satır devamını (ters bölü + satır
    sonu) siler: kabuk da siler, kalırsa shlex '\\n' jetonu verir (ikili adından sonra alt komut, girdiden sonra girdi
    sanılır)."""
    cikti, ikameler = [], []
    i, n = 0, len(komut)
    tek = cift = False
    while i < n:
        c = komut[i]
        if tek:
            if c == "'":
                tek = False
            cikti.append(c); i += 1; continue
        if c == "\\" and i + 1 < n:
            if komut[i + 1] != "\n":                         # satır devamı: ikisi de düşer
                cikti.append(komut[i:i + 2])
            i += 2; continue
        if c == "'" and not cift:
            tek = True; cikti.append(c); i += 1; continue
        if c == '"':
            cift = not cift; cikti.append(c); i += 1; continue
        if c == "$" and i + 1 < n and komut[i + 1] == "(" and not komut.startswith("$((", i):
            derinlik, j = 1, i + 2
            while j < n and derinlik:
                if komut[j] == "(":
                    derinlik += 1
                elif komut[j] == ")":
                    derinlik -= 1
                j += 1
            ikameler.append(komut[i + 2:j - 1])
            cikti.append(komut[i:j].replace("\\\n", "")); i = j; continue
        if c == "`":
            j = komut.find("`", i + 1)
            j = n if j < 0 else j
            ikameler.append(komut[i + 1:j])
            cikti.append(komut[i:j + 1].replace("\\\n", "")); i = j + 1; continue
        if c == "\n" and not cift:
            cikti.append(" ; "); i += 1; continue
        cikti.append(c); i += 1
    return "".join(cikti), ikameler


def fd_sil(komut: str) -> str:
    """Yönlendirme işlecine bitişik fd rakamını boşlukla değiştirir (2>&1 → ' >&1'). Kabukta yalnız bitişik rakam
    fd'dir: 'timeout 600 >/dev/null …'te 600 argümandır (süre); shlex boşluğu sakladığı için ayrım burada yapılır.
    Tırnak içi veridir; tırnaklar shlex'teki gibi eşlenir ($(…) içindeki tırnaklar da düz sayılır)."""
    cikti, i, n = [], 0, len(komut)
    tek = cift = False
    while i < n:
        c = komut[i]
        if tek:
            tek = c != "'"
        elif c == "\\":
            cikti.append(komut[i:i + 2]); i += 2; continue
        elif c == "'" and not cift:
            tek = True
        elif c == '"':
            cift = not cift
        elif c.isdigit() and not cift and (i == 0 or komut[i - 1] in " \t\n;&|()"):
            j = i
            while j < n and komut[j].isdigit():
                j += 1
            cikti.append(" " if j < n and komut[j] in "<>" else komut[i:j])
            i = j; continue
        cikti.append(c); i += 1
    return "".join(cikti)


def yonlendirme_ayikla(b: list[str]) -> tuple[list[str], list[str]]:
    """Bölümden yönlendirmeleri çıkarır: işleç ve hedefi (işlece bitişik fd rakamını fd_sil önceden siler).
    Döner: (kalan jetonlar, '<'/'<>' ile okunan dosyalar — 'bash < betik.sh' betiği çalıştırır)."""
    kalan, okunan = [], []
    i = 0
    while i < len(b):
        if b[i] in YONLENDIRME:
            if b[i] in ("<", "<>") and i + 1 < len(b):
                okunan.append(b[i + 1])
            i += 2
        else:
            kalan.append(b[i]); i += 1
    return kalan, okunan


def bolumleri_denetle(komut: str, derinlik: int) -> None:
    try:
        lx = shlex.shlex(fd_sil(komut), posix=True, punctuation_chars=True)
        lx.whitespace_split = True
        lx.commenters = ""
        jetonlar = list(lx)
    except ValueError:                                       # ayrıştırılamadı: temkinli düz arama
        for m in re.finditer(r"(?:^|[\s;&|(])(?:\S*/)?hyperframes(?:@[\w.\-]+)?(?:\.m?js)?\s+(\S+)([^;&|\n]*)", komut):
            alt_komut_denetle([m.group(1)] + m.group(2).split())
        if re.search(r"(?:^|[\s;&|(])(?:\S*/)?heygen(?:\s|$)", komut):
            engelle("'heygen' bulut CLI'si kullanılmaz (hesap/OAuth/kredi gerektirir).")
        for m in re.finditer(r"(?:^|[\s;&|(])(?:\S*/)?remotion(?:@[\w.\-]+)?\s+([^;&|\n]*)", komut):
            remotion_denetle(m.group(1).split())
        return
    bolum, bolumler = [], []
    for j in jetonlar:
        if j in AYRAC:
            bolumler.append(bolum); bolum = []
        else:
            bolum.append(j)
    bolumler.append(bolum)
    for b in bolumler:
        b, okunan = yonlendirme_ayikla(b)
        i, degerli, paketler = 0, (), []
        while i < len(b):
            j = b[i]
            onek = j.rsplit("/", 1)[-1]                      # /usr/bin/env → env
            if j.startswith("-"):                            # önekin bayrağı; ayrık değeri de (xargs -n 1, nice -n 10)
                if j in degerli and j in PAKET_BAYRAK and i + 1 < len(b):
                    paketler.append(b[i + 1])                # npx -p hyperframes@x hyperframes …
                elif j.startswith("--package="):
                    paketler.append(j.split("=", 1)[1])
                i += 2 if j in degerli else 1
            elif re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", j):
                i += 1                                       # ortam atamaları
            elif onek in ONEK:
                degerli, i = ONEK[onek], i + 1
                if onek == "timeout":                        # timeout [bayrak…] SÜRE komut: süre de atlanır
                    while i < len(b) and b[i].startswith("-"):
                        i += 2 if b[i] in degerli else 1
                    i += 1
            elif j in ("pnpm", "yarn") and i + 1 < len(b) and b[i + 1] in ("dlx", "exec"):
                degerli, i = (PAKET_BAYRAK if b[i + 1] == "dlx" else ()), i + 2
            elif j == "npm" and i + 1 < len(b) and b[i + 1] in ("exec", "x"):
                degerli, i = PAKET_BAYRAK, i + 2
            elif j == "--":
                i += 1
            else:
                break
        surum_denetle(paketler + b[i:i + 1], True)         # npx/dlx/npm exec hyperframes@<tam sürüm dışı>
        if i >= len(b):
            continue
        bas = b[i]
        ad = bas.rsplit("/", 1)[-1]
        if ad == "heygen" or ad.startswith("heygen@") or re.match(r"^(?:@heygen/)?heygen(?:@[\w.\-]+)?$", ad):
            engelle("'heygen' bulut CLI'si kullanılmaz (hesap/OAuth/kredi gerektirir). Kullanıcının kuralı: ücretli "
                    "hizmet ve hesap yok; her şey yerelde.")
        if ad in BETIK_CALISTIRAN:                           # bash …/prepare.sh, node …/transcribe.cjs, bash < …
            if not yalniz_sozdizimi(ad, b[i + 1:]):
                satici_betik_denetle(b[i + 1:] + okunan)
        elif "/" in bas:                                     # yol vererek doğrudan çalıştırma. Çıplak ad PATH'ten
            satici_betik_denetle([bas])                      # aranır; find \( -name x \)'te de shlex '('yi ayırır
        if ad in KABUK:                                      # sh -c "…" / bash -lc '…'
            for k in range(i + 1, len(b)):
                if re.match(r"^-[a-zA-Z]*c[a-zA-Z]*$", b[k]) and k + 1 < len(b):
                    denetle(b[k + 1], derinlik + 1)
                    break
            continue
        if ad == "eval":
            denetle(" ".join(b[i + 1:]), derinlik + 1)
            continue
        if ad == "create-video" or ad.startswith("create-video@"):
            engelle("'create-video' kullanılmaz (etkileşimli, @latest kurar). Remotion projesi: "
                    "medya proje yeni <ad> --motor remotion.")
        if ad == "skills" or ad.startswith("skills@"):
            engelle("'npx skills' kullanılmaz (telemetri, sabitsiz sürüm). Satıcı becerileri sabit commit'le "
                    "sistem/claude/satici/KAYNAKLAR.md'deki gibi kopyalanır.")
        if ad in ("npm", "pnpm", "yarn", "bun") and RM_PAKET.search(" ".join(b[i + 1:])) and \
                any(x in ("i", "install", "add") for x in b[i + 1:i + 3]):
            engelle("Bu Remotion paketi kurulmaz: web-renderer/lambda/cloudrun/vercel bulut ya da telemetri, "
                    "google-fonts dış yazı tipi, sfx lisansı belirsiz uzak ses. Yerel karşılıklar: @remotion/fonts + "
                    "public/fonts, kodla/CC0 ses.")
        if ad in ("npm", "pnpm", "yarn", "bun") and KURULUM & set(b[i + 1:]):   # npm --prefix p i hyperframes@latest
            surum_denetle([x for x in b[i + 1:] if not x.startswith("-")], False)
        paket, parg = ad.lower(), b[i + 1:]                 # PyPI adı büyük/küçük harf duyarsız (whisperX)
        if re.match(r"^python[\d.]*$", paket):              # python3 -m pip install whisperx → pip install whisperx
            paket, parg = python_modulu(parg)
            paket = paket.lower()
        if paket == "whisperx" or paket.startswith("whisperx@") or (paket in PIP and (
                "whisperx" in [x.lower() for x in parg[:3]] or any(WHISPERX_SURUM.match(x) for x in parg))):
            engelle("whisperx ~2 GB indirir (satıcı altyazı becerisi sormadan kurar). Stüdyoda kurulu karşılığı: "
                    "'medya yaziya-dok --dil tr --srt' (Whisper large-v3-turbo, MLX, kelime zamanlı).")
        if RM.match(bas):
            remotion_denetle(b[i + 1:])
            continue
        if ad in CALISTIRICI and i + 1 < len(b) and HF.match(b[i + 1]):
            alt_komut_denetle(b[i + 2:])
            continue
        if HF.match(bas):
            alt_komut_denetle(b[i + 1:])


def denetle(komut: str, derinlik: int = 0) -> None:
    kucuk = komut.replace("\\\n", "").lower()                # 'pip install whisperX' ve 'hyper\'+satır sonu+'frames'
                                                             # (kabuk satır devamını siler) de ön süzgeçten geçmeli
    if derinlik > 6 or not any(a in kucuk for a in ANAHTAR):
        return
    govdesiz, kabuga, ikameli = heredoc_ayikla(komut)
    for g in kabuga:
        denetle(g, derinlik + 1)
    for g in ikameli:
        for ic in tara(g)[1]:
            denetle(ic, derinlik + 1)
    duz, ikameler = tara(govdesiz)
    for ic in ikameler:
        denetle(ic, derinlik + 1)
    bolumleri_denetle(duz, derinlik)


def main() -> int:
    global BAGLAM
    try:
        veri = json.load(sys.stdin)
    except Exception:
        return 0
    komut = (veri.get("tool_input") or {}).get("command") or ""
    birlesik = komut.replace("\\\n", "")                     # satır devamıyla bölünmüş beceri adı da bağlamdır
    BAGLAM = f"{birlesik}\n{veri.get('cwd') or ''}"
    try:
        denetle(komut)
    except Engel as e:
        print(f"ENGELLENDİ (medya-koruma): {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
