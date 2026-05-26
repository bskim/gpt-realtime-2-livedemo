#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install --upgrade pip -q
pip install -r backend/requirements.txt -q
echo "Python environment ready."
