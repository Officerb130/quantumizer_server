#!/usr/bin/env bash
set -euo pipefail

python3 -m venv testvenv
source testvenv/bin/activate
cd /workspace/app/cmd
pip3 install --upgrade pip
pip3 install -r requirements.txt

python3 -m pytest --log-cli-level INFO --cov=. --cov-report xml:reports/coverage.xml --cov-report term  --junitxml=reports/unittest.xml -s /workspace/app/cmd/pyapp

deactivate
rm -rf testvenv
