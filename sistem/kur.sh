#!/bin/zsh
# Medya stüdyosu kurulum / onarım betiği — tekrar çalıştırılabilir (eksik olanı kurar, var olanı korur).
#   zsh sistem/kur.sh            her şey
#   zsh sistem/kur.sh --bagla    yalnız beceri ve ajan bağlantıları (~/.claude/skills, ~/.claude/agents)
#   zsh sistem/kur.sh --modeller büyük üretici modeller (~8,6 GB, diske bak): FLUX.2 klein, VoxCPM2
# Homebrew gerekmez (Xcode lisansı kabul edilmemiş makinede de çalışır). Ücretli/hesaplı hiçbir şey kurmaz.
set -e
KOK="$(cd "$(dirname "$0")/.." && pwd)"
cd "$KOK"

bagla() {
  echo "== beceri ve ajan bağlantıları"
  mkdir -p "$HOME/.claude/skills" "$HOME/.claude/agents"
  for d in "$KOK"/sistem/claude/skills/*/; do
    ad="$(basename "$d")"
    hedef="$HOME/.claude/skills/$ad"
    if [ -e "$hedef" ] && [ ! -L "$hedef" ]; then echo "  ⚠ $hedef gerçek klasör; atlandı (eski satıcı kopyasıysa: python3 $KOK/sistem/claude/satici/satici.py bagla)"; continue; fi
    ln -sfn "${d%/}" "$hedef" && echo "  beceri: $ad"
  done
  for f in "$KOK"/sistem/claude/agents/*.md; do
    ad="$(basename "$f")"
    hedef="$HOME/.claude/agents/$ad"
    if [ -e "$hedef" ] && [ ! -L "$hedef" ]; then echo "  ⚠ $hedef gerçek dosya; atlandı"; continue; fi
    ln -sf "$f" "$hedef" && echo "  ajan: ${ad%.md}"
  done
  if ! grep -q "medya-koruma.py" "$HOME/.claude/settings.json" 2>/dev/null; then
    echo "  ⚠ ~/.claude/settings.json'da medya-koruma kancası yok. Ekle (hooks.PreToolUse, matcher Bash):"
    echo "    $KOK/sistem/claude/hooks/medya-koruma.py"
  fi
}

if [ "$1" = "--bagla" ]; then bagla; exit 0; fi
if [ "$1" = "--modeller" ]; then          # büyük üretici modeller (~8,6 GB): görsel (FLUX.2 klein), dış ses (VoxCPM2)
  source "$KOK/ortam.sh"
  medya kur flux2-klein && medya kur voxcpm2
  exit $?
fi

echo "== npm bağımlılıkları (HyperFrames, Remotion, GSAP, ffmpeg-static, ffprobe, yazı tipleri — sürümler sabit)"
npm install --no-audit --no-fund
npm install-scripts approve ffmpeg-static esbuild @ffprobe-installer/darwin-arm64 >/dev/null 2>&1 || true
npm rebuild ffmpeg-static esbuild >/dev/null 2>&1 || true
chmod u+x node_modules/@ffprobe-installer/darwin-arm64/ffprobe
mkdir -p arac
ln -sf ../node_modules/ffmpeg-static/ffmpeg arac/ffmpeg
ln -sf ../node_modules/@ffprobe-installer/darwin-arm64/ffprobe arac/ffprobe

if [ ! -x arac/uv ]; then
  echo "== uv (resmî sürüm, sağlama toplamı denetimli)"
  surum=$(curl -fsSL https://api.github.com/repos/astral-sh/uv/releases/latest | python3 -c "import json,sys; print(json.load(sys.stdin)['tag_name'])")
  gecici=$(mktemp -d)
  curl -fsSL -o "$gecici/uv.tar.gz" "https://github.com/astral-sh/uv/releases/download/$surum/uv-aarch64-apple-darwin.tar.gz"
  curl -fsSL -o "$gecici/uv.sha256" "https://github.com/astral-sh/uv/releases/download/$surum/uv-aarch64-apple-darwin.tar.gz.sha256"
  [ "$(cut -d' ' -f1 "$gecici/uv.sha256")" = "$(shasum -a 256 "$gecici/uv.tar.gz" | cut -d' ' -f1)" ] || { echo "uv sağlama toplamı tutmadı"; exit 1; }
  tar -xzf "$gecici/uv.tar.gz" -C "$gecici"
  cp "$gecici"/uv-aarch64-apple-darwin/uv "$gecici"/uv-aarch64-apple-darwin/uvx arac/
  rm -rf "$gecici"
fi

source "$KOK/ortam.sh"
echo "== Python 3.12 + medya paketi"
arac/uv python install 3.12
arac/uv sync --all-extras

echo "== sağlayıcılar (kayıt defterinden)"
medya kur ses-ortami
medya kur medya-apple
medya kur exiftool
medya kur deepfilternet
medya kur rife

echo "== satıcı içeriği (sabit commit: remotion-best-practices, HyperFrames becerileri; depoda tutulmaz)"
python3 "$KOK/sistem/claude/satici/satici.py" kur
mkdir -p varliklar/js testler/hyperframes-baslik/vendor
cp node_modules/gsap/dist/gsap.min.js varliklar/js/gsap.min.js
cp node_modules/gsap/dist/gsap.min.js testler/hyperframes-baslik/vendor/gsap.min.js

bagla

echo "== sınamalar"
medya test
echo "Kurulum tamam. Yetenekler: medya yetenekler --saglayicilar"
