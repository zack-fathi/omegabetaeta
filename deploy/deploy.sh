#!/bin/bash
# ──────────────────────────────────────────────────────────────
# Deploy script — runs ON the server as the 'obh' user.
# Called by GitHub Actions, or manually:
#   sudo -u obh /home/obh/omegabetaeta/deploy/deploy.sh
# ──────────────────────────────────────────────────────────────

set -Eeuo pipefail

APP_DIR="/home/obh/omegabetaeta"
cd "$APP_DIR"

echo "=== Pulling latest code ==="
git fetch origin main
git reset --hard origin/main

echo "=== Installing dependencies ==="
if [[ ! -d env ]]; then
  python3 -m venv env
fi
source env/bin/activate
pip install -q -r requirements.txt

echo "=== Creating var directories ==="
mkdir -p var/uploads

echo "=== Restarting app ==="
sudo systemctl restart obhapp

echo "✅ Deployed at $(date)"
