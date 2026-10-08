# Medya çalışma alanı ortamı — her komuttan önce:  source /Users/onurkaya/Projects/video/ortam.sh
# Araçlar, önbellekler ve modeller bu klasörde kalır (kolay bulunur, kolay temizlenir); analiz verisi kapalı.
MEDYA="/Users/onurkaya/Projects/video"
export MEDYA
export PATH="$MEDYA/arac:$MEDYA/.venv/bin:$MEDYA/node_modules/.bin:$PATH"

# analiz verisi / telemetri kapalı
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1  # SKIP_SKILLS: init GitHub'a beceri denetimi yapmasın
export HF_HUB_DISABLE_TELEMETRY=1 GRADIO_ANALYTICS_ENABLED=False
export HOMEBREW_NO_ANALYTICS=1

# Python (uv) ve model önbellekleri çalışma alanında
export UV_PYTHON_INSTALL_DIR="$MEDYA/.uv/python" UV_CACHE_DIR="$MEDYA/.uv/cache"
export UV_PYTHON_INSTALL_BIN=0                                     # ~/.local/bin içine python bağlantısı koymasın
export UV_MANAGED_PYTHON=1                                         # uv yalnız stüdyonun Python'unu kullansın
export UV_TOOL_DIR="$MEDYA/.uv/tools" UV_TOOL_BIN_DIR="$MEDYA/arac"   # uv tool kurulumları da stüdyoda
export HF_HOME="$MEDYA/modeller/hf" TORCH_HOME="$MEDYA/modeller/torch"
