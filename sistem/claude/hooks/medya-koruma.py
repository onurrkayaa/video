#!/usr/bin/env python3
"""Claude Code PreToolUse (Bash) kancası — medya işlerinde kullanıcının kesin kurallarını zorlar.

Kaynak: /Users/onurkaya/Projects/video/sistem/claude/hooks/medya-koruma.py (sürümlü). ~/.claude/settings.json
içindeki PreToolUse kancası bu dosyayı çalıştırır; ana oturumda, alt ajanlarda ve iş akışı ajanlarında geçerlidir.

Engeller (çıkış kodu 2; gerekçe stderr'den Claude'a döner) — yalnız komut gerçekten ÇALIŞTIRILIYORSA:
- hyperframes cloud | lambda | cloudrun | auth | publish | usage | feedback   (ücretli/bulut/hesap/dış istek;
  feedback --file-issue projeyi GitHub'a yayımlar, --search-miss HeyGen'e rapor yollar)
- hyperframes telemetry enable                                               (analiz verisi kapalı kalmalı)
- hyperframes snapshot … '--describe false' olmadan                          (GEMINI_API_KEY varsa kareler Google'a gider)
- hyperframes media-use resolve|doctor|adopt|from (grade/lut dışı)           (HeyGen hesabı/katalogu, ücretli avatar video)
- heygen …                                                                   (HeyGen bulut CLI'si: hesap/OAuth/kredi)
- remotion lambda | cloudrun | upgrade | skills, --public-license-key/--license-key (bulut çizim, sabit sürümü
  bozan yükseltme, telemetrili kurulum; lisans anahtarı 'free-license' dahil remotion.pro'ya kullanım olayı yollar)
- npx create-video / npx skills …  ve  @remotion/web-renderer|google-fonts|lambda|cloudrun|vercel|sfx|mcp kurulumu
- sessiz büyük indirmeler: hyperframes remove-background (~394 MB model), whisperx (uvx/pip, ~2 GB) — stüdyonun
  indirmesiz/kurulu karşılıkları var; gerçekten gerekiyorsa önce boyutu söyleyip kullanıcıya sorulur
Ayrıştırma kabuk kurallarına uyar: tek tırnak içi ve tırnaklı heredoc gövdesi VERİDİR (engellenmez); satır sonları,
; && || | & komut ayırır; $(…) ve `…` (tek tırnak dışında) ile kabuğa giden heredoc gövdeleri ayrıca denetlenir;
npx/bunx/pnpm dlx/npm exec, yol önekli ikili, `node …/hyperframes.mjs`, env/time/nohup/exec/sudo önekleri,
ortam atamaları, `sh|bash|zsh -c "…"` ve eval yakalanır.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

YASAK = {"cloud", "lambda", "cloudrun", "auth", "publish", "usage", "feedback"}
SESSIZ_INDIRME = {"remove-background": "arka plan için 'medya arkaplan-sil' (Apple Vision, indirme yok)"}
AYRAC = {";", "&&", "||", "|", "&", "(", ")", "|&", ";;"}
ONEK = {"npx", "bunx", "exec", "time", "nohup", "env", "command", "sudo", "builtin", "xargs", "then", "do", "else",
        "if", "while", "until", "!", "{", "}"}
KABUK = {"sh", "bash", "zsh", "dash", "ksh"}
CALISTIRICI = {"node", "bun", "deno"}
HF = re.compile(r"^(?:.*/)?hyperframes(?:@[\w.\-]+)?(?:\.m?js)?$")
RM = re.compile(r"^(?:.*/)?remotion(?:@[\w.\-]+)?$")
RM_YASAK = {"lambda", "cloudrun", "upgrade", "skills"}
RM_PAKET = re.compile(r"@remotion/(?:web-renderer|google-fonts|lambda|cloudrun|vercel|sfx|mcp|licensing)\b")
LISANS = re.compile(r"--(?:public-)?license-key\b")
ANAHTAR = ("hyperframes", "heygen", "remotion", "create-video", "skills", "whisperx")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


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
    if alt == "snapshot" and not re.search(r"--describe(=|\s+)(false|0|no)\b", metin):
        engelle("'hyperframes snapshot' her zaman '--describe false' ile çalıştırılır; aksi hâlde GEMINI_API_KEY "
                "tanımlıysa kareler Google'a gönderilir.")


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
    (2) tek tırnak dışındaki $(…) ve `…` ikamelerini toplar."""
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
            cikti.append(komut[i:i + 2]); i += 2; continue
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
            ikameler.append(komut[i + 2:j - 1]); cikti.append(komut[i:j]); i = j; continue
        if c == "`":
            j = komut.find("`", i + 1)
            j = n if j < 0 else j
            ikameler.append(komut[i + 1:j]); cikti.append(komut[i:j + 1]); i = j + 1; continue
        if c == "\n" and not cift:
            cikti.append(" ; "); i += 1; continue
        cikti.append(c); i += 1
    return "".join(cikti), ikameler


def bolumleri_denetle(komut: str, derinlik: int) -> None:
    try:
        lx = shlex.shlex(komut, posix=True, punctuation_chars=True)
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
        i = 0
        while i < len(b):
            j = b[i]
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", j) or j in ONEK or j.startswith("-"):
                i += 1                                       # atamalar, önekler ve bayrakları
            elif j in ("pnpm", "yarn") and i + 1 < len(b) and b[i + 1] in ("dlx", "exec"):
                i += 2
            elif j == "npm" and i + 1 < len(b) and b[i + 1] in ("exec", "x"):
                i += 2
            elif j == "--":
                i += 1
            else:
                break
        if i >= len(b):
            continue
        bas = b[i]
        ad = bas.rsplit("/", 1)[-1]
        if ad == "heygen" or ad.startswith("heygen@") or re.match(r"^(?:@heygen/)?heygen(?:@[\w.\-]+)?$", ad):
            engelle("'heygen' bulut CLI'si kullanılmaz (hesap/OAuth/kredi gerektirir). Kullanıcının kuralı: ücretli "
                    "hizmet ve hesap yok; her şey yerelde.")
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
        if ad == "whisperx" or ad.startswith("whisperx@") or ("whisperx" in b[i + 1:i + 4] and
                                                            ad in ("uvx", "pip", "pip3", "uv", "pipx")):
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
    if derinlik > 6 or not any(a in komut for a in ANAHTAR):
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
    try:
        veri = json.load(sys.stdin)
    except Exception:
        return 0
    komut = (veri.get("tool_input") or {}).get("command") or ""
    try:
        denetle(komut)
    except Engel as e:
        print(f"ENGELLENDİ (medya-koruma): {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
