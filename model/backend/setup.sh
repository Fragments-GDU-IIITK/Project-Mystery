#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 -m venv "${ROOT_DIR}/venv"
source "${ROOT_DIR}/venv/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r "${ROOT_DIR}/requirements.txt"

mkdir -p "${ROOT_DIR}/adapters/tara/"
mkdir -p "${ROOT_DIR}/adapters/leo/"
mkdir -p "${ROOT_DIR}/training/"

echo "Setup complete. Run training with: python training/train_tara.py && python training/train_leo.py"
echo "Then start server with: python serve.py"
