#!/usr/bin/env bash
set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " YouTubeKit Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1) Create venv
if [ ! -d ".venv" ]; then
  echo "[1/5] Creating virtualenv (.venv)"
  python3 -m venv .venv
fi

# 2) Activate
echo "[2/5] Activating .venv"
source .venv/bin/activate
python --version

# 3) Upgrade pip
echo "[3/5] Upgrading pip"
python -m pip install --upgrade pip >/dev/null

# 4) Install package
echo "[4/5] Installing youtubekit (editable)"
pip install -e . || {
  echo "⚠️  Editable install failed. Trying standard install...";
  pip install .;
}

# 5) Ensure .env
if [ ! -f ".env" ]; then
  echo "[5/5] Creating .env"
  cat > .env <<'EOF'
OPENAI_API_KEY=
YOUTUBE_API_KEY=
# Optional flags
YT_OFFLINE_MODE=1
EOF
  echo "⚠️  Fill OPENAI_API_KEY and YOUTUBE_API_KEY in .env."
else
  echo "[5/5] .env already exists"
fi

echo "✅ Setup complete. Run tests: python test_youtube.py"
