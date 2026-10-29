#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv-build
. .venv-build/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
python build.py
