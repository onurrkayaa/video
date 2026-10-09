"""medya-koruma kancasının sınamaları: engellemesi gerekenler engelleniyor, zararsızlar geçiyor mu?

Kanca kabuk kurallarına uymalı: tek tırnak ve tırnaklı heredoc içi VERİDİR; satır sonu komut ayırır; ikameler
($(…), `…`) ve kabuğa giden heredoc gövdeleri ayrıca denetlenir.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

KANCA = Path(__file__).resolve().parent.parent / "sistem" / "claude" / "hooks" / "medya-koruma.py"


def _kanca(komut: str, cwd: str = "") -> subprocess.CompletedProcess:
    girdi = {"tool_name": "Bash", "tool_input": {"command": komut}}
    if cwd:
        girdi["cwd"] = cwd
    return subprocess.run([sys.executable, str(KANCA)], input=json.dumps(girdi), capture_output=True, text=True)


def calis(komut: str, cwd: str = "") -> int:
    return _kanca(komut, cwd).returncode


ENGELLENMELI = [
    "npx hyperframes remove-background foto.png --output kesik.png",
    "uvx whisperx ses.wav --language tr",
    "pip install whisperx",
    "whisperx ses.wav",
    # sürüm sabitli whisperx (transcribe.cjs'nin kurduğu komutun aynısı dahil)
    "uvx --python 3.12 --from whisperx==3.8.6 whisperx a.wav --model large-v3",
    "uvx whisperx==3.8.6 a.wav",
    "pip install whisperx==3.8.6",
    "uv pip install whisperx==3.8.6",
    "npx remotion lambda render x",
    "cd p && $MEDYA/node_modules/.bin/remotion render src/index.ts A out.mp4 --public-license-key=free-license",
    "node_modules/.bin/remotion render src/index.ts A out.mp4 --license-key abc",
    "npx remotion upgrade",
    "npx create-video@latest",
    "npx skills add remotion-dev/skills",
    "npm i @remotion/google-fonts",
    "npm install --save-exact @remotion/web-renderer@4.0.532",
    "HYPERFRAMES_NO_TELEMETRY=1 hyperframes cloud render x",
    "cd /x && export A=1 && npx hyperframes@latest auth login",
    "node_modules/.bin/hyperframes lambda deploy",
    "pnpm dlx hyperframes publish",
    "npm exec -- hyperframes usage --json",
    "npx --yes hyperframes feedback --rating 9",
    "hyperframes feedback --search-miss 'whip pan'",
    "hyperframes snapshot deneme --at 2,3",
    "hyperframes lint a; hyperframes snapshot b --at 1",
    "hyperframes telemetry enable",
    'sh -c "hyperframes usage"',
    "bash -lc 'cd x && npx hyperframes publish'",
    "zsh -c 'hyperframes snapshot p --at 1'",
    "node node_modules/hyperframes/bin/hyperframes.mjs usage",
    "eval 'hyperframes auth status'",
    "echo $(hyperframes usage --json)",
    'echo "$(hyperframes usage --json)"',
    "x=`hyperframes cloud list`",
    # çok satırlı: yasak komut kendi satırında
    "cd /Users/x/proje\nhyperframes publish",
    "source ortam.sh\nnpx hyperframes cloud render .\necho bitti",
    # kabuğa giden heredoc gövdesi komuttur
    "bash <<'EOF'\ncd x\nhyperframes publish\nEOF",
    # tırnaksız heredoc içindeki ikame çalışır
    "cat <<EOF > a.txt\nsonuc: $(hyperframes usage --json)\nEOF",
    # HeyGen bulut CLI'si ve hesap tabanlı media-use
    "heygen auth login --oauth",
    "npx heygen tts merhaba",
    "cd x && heygen update",
    "hyperframes media-use resolve --type bgm --intent sakin --project p",
    "npx hyperframes media-use doctor",
    "hyperframes media-use resolve --type voice --intent dis-ses",
    # sessiz indirme: ses/video dökümü (whisper.cpp + ggml modeli), init'in dökümü, Kokoro, Parakeet
    "npx hyperframes transcribe ses.wav",
    "hyperframes transcribe video.mp4 --model large-v3",
    "hyperframes transcribe --model large-v3 ses.wav",
    "hyperframes transcribe -d out.srt ses.wav",
    'npx hyperframes transcribe "$WORK_DIR/audio.mp3" -d "$WORK_DIR" --json --model small.en',
    'hyperframes transcribe "$GIRDI"',
    "hyperframes init p --non-interactive --video v.mp4",
    "hyperframes init p --non-interactive --video=v.mp4 --skill=embedded-captions",
    "hyperframes init p -a ses.m4a",
    # kısa bayrak grupları: citty parseArgs video=v.mp4 / audio=a.m4a okur, cli.js assertKnownFlags bunları çalıştırmadan
    # reddeder ('Unknown flag: -.' / '-y'; ölçüldü 2026-10-08); kanca temkinli engeller
    "hyperframes init p --non-interactive -vv.mp4",
    "hyperframes init p --non-interactive -aa.m4a",
    "hyperframes init p -yv v.mp4",
    'npx hyperframes tts "merhaba"',
    "npx hyperframes models install parakeet",
    # sabit sürüm ve satıcı beceri kaynağı
    "npx hyperframes skills",
    "npx hyperframes skills update embedded-captions",
    "hyperframes upgrade -y",
    "hyperframes upgrade --project x",
    # indirme yapan satıcı betikleri (kanca alt süreçlerini göremez)
    "bash ~/.claude/skills/embedded-captions/scripts/prepare.sh p",
    "cd ~/.claude/skills/embedded-captions && bash scripts/prepare.sh p",
    "~/.claude/skills/embedded-captions/scripts/prepare.sh p",
    "node ~/.claude/skills/embedded-captions/scripts/transcribe.cjs p",
    "TRANSCRIBE_ENGINE=whisper node ~/.claude/skills/embedded-captions/scripts/matte.cjs p",
    "node ~/.claude/skills/media-use/scripts/transcribe.mjs --input ses.wav",
    'sh -c "node ~/.claude/skills/embedded-captions/scripts/transcribe.cjs ."',
    "node ~/.claude/skills/embedded-captions/scripts/transcribe.cjs --check",
    # girdisi görünmeyen transcribe: xargs girdiyi stdin'den verir (girdisiz doğrudan çağrıyı CLI zaten reddeder)
    "ls *.wav | xargs -n1 npx hyperframes transcribe",
    "find . -name '*.wav' -print0 | xargs -0 -n1 npx hyperframes transcribe",
    "ls *.wav | xargs -n 1 npx hyperframes transcribe",
    "npx hyperframes transcribe",
    # sarmalayıcı önekler, bayrak değerleri ve süreyle (eski yasaklar da: cloud render)
    "timeout 600 npx hyperframes cloud render",
    "timeout 900 npx hyperframes transcribe ses.wav",
    "timeout -s KILL 600 npx hyperframes transcribe ses.wav",
    "caffeinate -i npx hyperframes transcribe ses.wav --model large-v3",
    "caffeinate -i -t 3600 npx hyperframes cloud render",
    "nice -n 10 npx hyperframes tts merhaba",
    "/usr/bin/env HYPERFRAMES_NO_TELEMETRY=1 npx hyperframes cloud render",
    "/usr/bin/env -u GEMINI_API_KEY npx hyperframes transcribe ses.wav",
    "timeout 900 bash ~/.claude/skills/embedded-captions/scripts/prepare.sh p",
    "caffeinate -i node ~/.claude/skills/embedded-captions/scripts/transcribe.cjs p",
    "/usr/bin/env bash ~/.claude/skills/embedded-captions/scripts/prepare.sh p",
    # satır devamı ikili adından hemen sonra (shlex '\n' jetonu alt komut sanılıyordu)
    "npx hyperframes \\\n transcribe ses.wav",
    "npx hyperframes \\\n  cloud render",
    # yönlendirme argüman sayılmaz: komut başında ya da alt komuttan önce de; 'bash < betik' betiği çalıştırır
    "2>/dev/null npx hyperframes cloud render",
    "hyperframes 2>/dev/null transcribe ses.wav",
    "bash < ~/.claude/skills/embedded-captions/scripts/prepare.sh",
    # whisperx: PyPI adı büyük/küçük harf duyarsız; python -m pip
    "pip install whisperX",
    "python3 -m pip install whisperx",
    ".venv/bin/python -m pip install -U whisperX",
    # gizlilik: snapshot açıklaması yalnız birebir 'false' ile kapanır (0.8.140 snapshot-SD5R3NWX.js:729); citty'de
    # tekrar eden bayrakta son değer geçer, '--' sonrası konumsaldır (ölçüldü 2026-10-08); --no-describe: kural metni
    # '--describe false', kanca birebir onu ister
    "hyperframes snapshot p --describe 0",
    "hyperframes snapshot p --describe no",
    "hyperframes snapshot p --describe=0",
    "hyperframes snapshot p --describe=no",
    "hyperframes snapshot p --describe False --at 1",
    "hyperframes snapshot p --at 1 --describe",
    "hyperframes snapshot p --describe false --describe 'logo görünüyor mu?'",
    "hyperframes snapshot p -- --describe false",
    "hyperframes snapshot p --describe false-ish",
    "hyperframes snapshot p --no-describe",
    # sabit sürüm: tam sürüm dışı hyperframes@ (npx/dlx/npm exec, -p/--package) ve tam sürümsüz kurulum/yükseltme
    # (sürümsüz ad latest kurar, ^ ile kaydeder; son örnek oturum kayıtlarındaki bir komutun aynısı)
    "npm i -D hyperframes@latest",
    "npm install --save-dev --save-exact hyperframes@next",
    "npm i hyperframes@^0.8.140",
    "npm i -D hyperframes@~0.8.140",
    'npm i "hyperframes@>=0.8.0"',
    "npm i hyperframes@0.8",
    "npm i hyperframes@0.8.x",
    "npm i -g hyperframes",
    "npm --prefix calisma/kompozisyon install hyperframes@latest",
    "npm update hyperframes",
    "pnpm add -D hyperframes@latest",
    "yarn add hyperframes@^0.8.140",
    "bun add hyperframes@latest",
    "npx hyperframes@latest render .",
    "npx --yes hyperframes@next lint p",
    "npx hyperframes@^0.8 cloud render",
    "npx hyperframes@0.8.140+x cloud render",
    "pnpm dlx hyperframes@latest lint p",
    "npm exec hyperframes@latest -- lint p",
    "bunx hyperframes@latest lint",
    "npx -p hyperframes@latest hyperframes lint p",
    "npx --package=hyperframes@latest hyperframes lint p",
    "npx -p hyperframes hyperframes cloud render",
    "npm exec -p hyperframes@0.8.140 -- hyperframes cloud render",
    # -p/--package değeri komut sanılmaz: Remotion kuralı da aynı yoldan kaçıyordu
    "npx -p @remotion/cli remotion lambda render x",
    "npx --package @remotion/cli remotion upgrade",
    # remotion add: sabit kurulum yolunu (yetenekler.toml) atlar, eş bağımlılıkları (three, R3F, lottie-web) sabitlemez
    # (4.0.533 add.js); özgün kancada hepsi çıkış 0'dı (2026-10-09, JSON stdin)
    "npx remotion add @remotion/three",
    "npx remotion@4.0.533 add @remotion/lottie",
    "npx --yes remotion add @remotion/three",
    "npx -p @remotion/cli remotion add @remotion/three",
    "node_modules/.bin/remotion add @remotion/three",
    "cd sablonlar/remotion && $MEDYA/node_modules/.bin/remotion add @remotion/gif",
    "/Users/x/Projects/video/node_modules/.bin/remotion add @remotion/three --log=verbose",
    "npm exec remotion add @remotion/three",
    "npm exec -- remotion add @remotion/three",
    "npm x remotion add @remotion/three",
    "pnpm dlx remotion add @remotion/three",
    "pnpm exec remotion add @remotion/lottie",
    "yarn dlx remotion add @remotion/three",
    "yarn exec remotion add @remotion/three",
    "bunx remotion add @remotion/three",
    "bash -lc 'npx remotion add @remotion/three'",
    "echo @remotion/three | xargs npx remotion add",
    # bayrak araya girse de alt komut add: bunu kilitleyen sınama yoktu (sozcukler[:1] → arg[:1] mutasyonu geçiyordu)
    "npx remotion --log=verbose add @remotion/three",
    # yarn|pnpm|bun [run] <ikili>: paket yöneticisi node_modules/.bin'deki ikiliyi çalıştırır; satıcı becerisi
    # 'yarn remotion add …' öğretiyor (remotion-captions, remotion-markup/3d.md). Özgün kancada hepsi çıkış 0
    # (2026-10-09, JSON stdin); aynı açık lambda/upgrade ve hyperframes için de vardı
    "yarn remotion add @remotion/captions",
    "pnpm remotion add @remotion/three",
    "yarn run remotion add @remotion/three",
    "bun run remotion add @remotion/three",
    "cd p && yarn remotion add @remotion/media",
    "yarn remotion lambda render x",
    "pnpm remotion upgrade",
    "yarn hyperframes cloud render",
    "npm install --save-dev --no-fund --no-audit hyperframes ffmpeg-static 2>&1 | tail -5",
    # fd yalnız işlece bitişik rakamdır: boşluklu '600 >x'te 600 önekin değeridir (süre), komut ondan sonra gelir
    "timeout 600 >/dev/null hyperframes cloud render",
    "nice -n 10 >/dev/null hyperframes cloud render",
    "ls *.wav | xargs -n 1 >/dev/null hyperframes transcribe",
    # satır devamı ön süzgeçte ve beceri bağlamında da silinir (kabuk 'hyper\' + satır sonu + 'frames'i birleştirir)
    "npx hyper\\\nframes cloud render",
    "whisper\\\nx ses.wav",
    "cd /x/embedded-captions/scripts && bash prep\\\nare.sh p",
    "cd ~/.claude/skills/embedded-cap\\\ntions && bash scripts/prepare.sh p",
]
GECMELI = [
    "medya arkaplan-sil foto.png --cikti kesik.png",
    "grep -rn whisperx ~/.claude/skills/embedded-captions/SKILL.md",
    "uv run pytest -k whisperx testler/",
    "node_modules/.bin/remotion render src/index.ts Ornek out/o.mp4 --image-format=png",
    "npm install --save-dev --save-exact remotion@4.0.532 @remotion/cli@4.0.532 @remotion/fonts@4.0.532",
    "echo 'npx remotion lambda'",
    "grep -n remotion package.json",
    "$MEDYA/node_modules/.bin/remotion still src/index.ts Ornek out/k.png --frame=30",
    "ls -la",
    "npx hyperframes render deneme --output r.mp4",
    "hyperframes snapshot deneme --at 2,3 --describe false",
    "hyperframes snapshot deneme --describe=false --at 1",
    "hyperframes telemetry disable",
    "echo 'hyperframes usage docs' > notlar.txt",
    "echo '$(hyperframes usage --json)'",
    "grep -n 'hyperframes cloud' README.md",
    "hyperframes docs rendering | head",
    "hyperframes catalog --on-device crossfade --json",
    'git commit -m "hyperframes feedback kapatildi"',
    "node node_modules/hyperframes/bin/hyperframes.mjs lint proje",
    "hyperframes media-use resolve --type grade --for clip.mp4 --analyze",
    "grep -rn heygen ~/.claude/skills/media-use/SKILL.md",
    "echo 'heygen kullanılmaz' >> notlar.md",
    # tırnaklı heredoc VERİDİR (dosyaya/python'a gider, kabukta çalışmaz)
    "cat > testler/x.py <<'EOF'\nKOMUTLAR = ['hyperframes cloud list', 'x=`hyperframes publish`', 'heygen auth login']\nEOF",
    "python3 - <<'EOF'\nprint('hyperframes usage ve heygen yalnız metin')\nEOF",
    "cat <<EOF > a.txt\nhyperframes publish satırı yalnız metin (tırnaksız heredoc, ikame yok)\nEOF",
    # indirmesiz döküm içe/dışa aktarımı, dökümsüz init, salt okunur skills check, yardım
    "npx hyperframes transcribe altyazi.srt",
    "hyperframes transcribe t.json --to srt",
    "hyperframes transcribe -d proj altyazi.srt",
    "hyperframes transcribe --language tr altyazi.VTT",
    "hyperframes transcribe -o cikti.srt t.json --to=srt",
    "hyperframes transcribe --help",
    "hyperframes tts -h",
    "hyperframes init p --non-interactive --video v.mp4 --skip-transcribe",
    "HYPERFRAMES_SKIP_SKILLS=1 hyperframes init kompozisyon --non-interactive --example=blank --resolution=landscape",
    "hyperframes init p --non-interactive -eblank",
    "hyperframes skills check",
    # satıcı betiklerini okumak, find ile aramak ve yalnız sözdizimini denetlemek serbest; başka projedeki genel adlı betik
    "cat ~/.claude/skills/embedded-captions/scripts/prepare.sh",
    "sed -n 1,40p ~/.claude/skills/embedded-captions/scripts/transcribe.cjs",
    "grep -n transcribe ~/.claude/skills/talking-head-recut/SKILL.md",
    "find ~/.claude/skills -maxdepth 4 \\( -name 'transcribe.mjs' -o -name 'prepare.sh' \\) 2>/dev/null",
    "find . \\( -name matte.cjs \\) -print",
    "node --check ~/.claude/skills/embedded-captions/scripts/transcribe.cjs",
    "bash -n ~/.claude/skills/embedded-captions/scripts/prepare.sh",
    "medya yaziya-dok ses.wav --dil tr --srt",
    "bash scripts/prepare.sh",
    "node /Users/x/baska-proje/transcribe.mjs",
    # içe/dışa aktarımda yönlendirme ve satır devamı girdi sayılmaz (bu biçimler 2026-10-08 kapanış ölçümünde yanlış
    # engelleniyordu; ilk satır yönlendirmesiz karşılaştırma)
    "npx hyperframes transcribe a.srt -d komp",
    "npx hyperframes transcribe analiz/yazi/a.srt -d calisma/kompozisyon 2>&1 | tail -5",
    "npx hyperframes transcribe a.srt -d proj >/dev/null 2>&1",
    "npx hyperframes transcribe a-kelime.json -d komp 2>/dev/null",
    "hyperframes transcribe t.json --to srt --json > sonuc.json",
    "npx hyperframes transcribe a.srt \\\n -d komp",
    "cd calisma/kompozisyon && npx hyperframes transcribe ../../analiz/yazi/a.srt 2>&1 | tail -3",
    "hyperframes skills check --json 2>&1",
    "hyperframes init p --non-interactive --video v.mp4 --skip-transcribe 2>&1 | tail",
    # sarmalayıcıyla zararsız komutlar; python -m pip başka paket
    "timeout 60 npx hyperframes lint komp",
    "caffeinate -i medya test",
    "nice -n 5 medya yaziya-dok ses.wav --dil tr --srt",
    "python3 -m pip install rich",
    # snapshot: tırnaklı 'false' ve yönlendirmeli çağrı
    "hyperframes snapshot p --describe 'false' --at 1",
    "npx hyperframes snapshot calisma/kompozisyon --at 1,2 --describe false 2>&1 | tail -3",
    # sabit sürüm: tam sürümle kurulum/çalıştırma (yetenekler.toml kurulum satırı dahil), çıplak npx (kurulu sürüm),
    # salt okunur npm sorguları
    "npm i -D -E hyperframes@0.8.140",
    "npm install --save-dev --save-exact --no-audit --no-fund hyperframes@0.8.140",
    "pnpm add -E hyperframes@0.8.140",
    "npm i -D -E hyperframes@0.9.0-beta.1",
    "npx hyperframes@0.8.140 lint p",
    "npx -p hyperframes@0.8.140 hyperframes lint p",
    "npx -p @remotion/cli remotion render src/index.ts A out.mp4",
    # remotion: sürüm denetimi, stüdyonun kurulum yolu, yardım ve 'add'i yalnız metin olarak anan komutlar
    "npx remotion versions",
    "medya kur remotion --yeniden",
    "npx remotion help add",
    "grep -rn 'npx remotion add' ~/.claude/skills/remotion-best-practices",
    "echo 'npx remotion add @remotion/three'",
    'git commit -m "remotion add engeli"',
    "git add sablonlar/remotion yetenekler.toml",
    # yarn|pnpm|bun [run] remotion: yasak dışı alt komutlar ve paket yöneticisinin kendi add'i geçer
    "yarn remotion render src/index.ts A out.mp4",
    "pnpm remotion versions",
    "bun run remotion still src/index.ts A a.png --frame=10",
    "yarn add -D -E @remotion/three@4.0.533",
    "yarn hyperframes lint p",
    "npm view hyperframes version time.modified",
    "npm view hyperframes@latest version",
    "npm outdated hyperframes",
    "npm ls hyperframes",
    # bitişik fd rakamı argüman değildir, $(…) içinde de (dış geçiş 2'yi girdi sanmamalı); tırnak içi veridir
    'x=$(npx hyperframes transcribe a.srt -d komp 2>&1)',
    "npx hyperframes transcribe a.srt -d komp 2> hata.txt",
    "npx hyperframes transcribe a.srt -d komp 1>&2",
    "timeout 600 npx hyperframes lint komp >/dev/null",
    'echo "2>x" && npx hyperframes lint p',
    # tek tırnak içinde satır devamı silinmez: veri
    "echo 'hyper\\\nframes cloud'",
]
# Göreli satıcı betiği: çalışma klasörü (kancanın JSON girdisindeki cwd) beceriyi gösteriyorsa engellenir; dört ad da
# genel olduğundan başka projenin kendi betiği serbest.
CALISMA_KLASORLU = [
    ("bash scripts/prepare.sh p", "/Users/x/.claude/skills/embedded-captions", 2),
    ("./prepare.sh p", "/Users/x/.claude/skills/embedded-captions/scripts", 2),
    ("node scripts/transcribe.cjs .", "/Users/x/.claude/skills/embedded-captions", 2),
    ('sh -c "node scripts/transcribe.cjs ."', "/Users/x/.claude/skills/embedded-captions", 2),
    ("node matte.cjs p", "/Users/x/.claude/skills/embedded-captions/scripts", 2),
    ("node scripts/transcribe.mjs --input a.wav", "/Users/x/.claude/skills/media-use", 2),
    ("bash scripts/prepare.sh p", "/Users/x/Projects/baska-proje", 0),
    ("node scripts/transcribe.mjs", "/Users/x/Projects/podcast", 0),
    ("node transcribe.cjs girdi.wav", "/Users/x/Projects/baska", 0),
]
# Engel iletisi stüdyonun kurulu yolunu (ve doğru önkoşulu) söylemeli.
ILETI = [
    ("npx hyperframes transcribe ses.wav", "medya yaziya-dok"),
    ("hyperframes init p --video v.mp4", "--skip-transcribe"),
    ('npx hyperframes tts "merhaba"', "medya seslendir"),
    ('npx hyperframes tts "merhaba"', "kokoro-onnx ve soundfile kuruluysa"),
    ("node ~/.claude/skills/embedded-captions/scripts/transcribe.cjs .", "hyperframes transcribe <x>.srt"),
    ("ls *.wav | xargs -n1 npx hyperframes transcribe", "görünür girdisi yok"),
    ('hyperframes transcribe a.srt "$X"', "girdisi '$X' döküm dosyası"),
    ("hyperframes snapshot p --describe 0", "birebir 'false'"),
    ("npx hyperframes@latest render .", "tam sürümle"),
    ("npm i -D hyperframes@latest", "güncelleme-ve-disk §3"),
    ("npx remotion add @remotion/three", "medya kur remotion --yeniden"),
]
# İleti döküm dosyasını ses/video girdisi diye anmamalı (yalnız döküm dışı girdiyi adıyla söyler).
ILETI_DEGIL = [
    ('hyperframes transcribe a.srt "$X"', "'a.srt'"),
]


@pytest.mark.parametrize("komut", ENGELLENMELI)
def test_engeller(komut):
    assert calis(komut) == 2, komut


@pytest.mark.parametrize("komut", GECMELI)
def test_gecirir(komut):
    assert calis(komut) == 0, komut


@pytest.mark.parametrize("komut,cwd,beklenen", CALISMA_KLASORLU)
def test_calisma_klasoru(komut, cwd, beklenen):
    assert calis(komut, cwd) == beklenen, (komut, cwd)


@pytest.mark.parametrize("komut,beklenen", ILETI)
def test_engel_iletisi_studyo_yolu(komut, beklenen):
    r = _kanca(komut)
    assert r.returncode == 2 and beklenen in r.stderr, r.stderr


@pytest.mark.parametrize("komut,olmayan", ILETI_DEGIL)
def test_engel_iletisi_dokum_girdisini_anmaz(komut, olmayan):
    r = _kanca(komut)
    assert r.returncode == 2 and olmayan not in r.stderr, r.stderr
