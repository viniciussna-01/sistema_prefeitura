#!/usr/bin/env bash
# Ambiente de desenvolvimento: backend (SQLite) + frontend, sem Docker
set -euo pipefail
cd "$(dirname "$0")/.."

(cd backend \
  && python3 -m venv .venv 2>/dev/null || true \
  && .venv/bin/pip install -q -r requirements.txt \
  && .venv/bin/uvicorn app.main:app --reload --port 8000) &

(cd frontend && npm install --no-audit --no-fund && npm run dev) &

wait
