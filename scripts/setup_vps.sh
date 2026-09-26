#!/usr/bin/env bash
# One-time setup for a fresh Ubuntu 22.04/24.04 VPS (e.g. Hetzner CX33: 4 vCPU, 8 GB).
# Usage: git clone <this repo> && cd make-money- && bash scripts/setup_vps.sh
set -euo pipefail

sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip ffmpeg fonts-dejavu-core fonts-noto-color-emoji curl unzip git

# yt-dlp needs a JavaScript runtime (Deno) to download from YouTube.
if ! command -v deno >/dev/null 2>&1 && [ ! -x "$HOME/.deno/bin/deno" ]; then
  curl -fsSL https://deno.land/install.sh | sh -s -- -y
fi
grep -q '.deno/bin' "$HOME/.bashrc" || echo 'export PATH="$HOME/.deno/bin:$PATH"' >> "$HOME/.bashrc"

# 4 GB swap so whisper "medium" never gets killed on an 8 GB box.
if ! swapon --show | grep -q .; then
  sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile
  sudo mkswap /swapfile && sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
[ -f .env ] || cp .env.example .env

# Pre-download the default whisper model so the first job starts fast.
.venv/bin/python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"

echo
echo "Done. Next:"
echo "  1. nano .env            # paste your free GEMINI_API_KEY"
echo "  2. source .venv/bin/activate && export PATH=\"\$HOME/.deno/bin:\$PATH\""
echo "  3. python -m moneymaker clip 'https://www.youtube.com/watch?v=...'"
