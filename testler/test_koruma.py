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


def calis(komut: str) -> int:
    r = subprocess.run([sys.executable, str(KANCA)], input=json.dumps({"tool_name": "Bash", "tool_input": {"command": komut}}),
                       capture_output=True, text=True)
    return r.returncode


ENGELLENMELI = [
    "npx hyperframes remove-background foto.png --output kesik.png",
    "uvx whisperx ses.wav --language tr",
    "pip install whisperx",
    "whisperx ses.wav",
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
]
GECMELI = [
    "medya arkaplan-sil foto.png --cikti kesik.png",
    "grep -rn whisperx ~/.claude/skills/embedded-captions/SKILL.md",
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
]


@pytest.mark.parametrize("komut", ENGELLENMELI)
def test_engeller(komut):
    assert calis(komut) == 2, komut


@pytest.mark.parametrize("komut", GECMELI)
def test_gecirir(komut):
    assert calis(komut) == 0, komut
