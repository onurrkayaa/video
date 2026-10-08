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
    # kısa bayrak grupları: CLI'nin kendi parseArgs'ı video=v.mp4 / audio=a.m4a okuyor (ölçüldü)
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
