#!/usr/bin/env bash
# Instalação do ambiente de produção (Docker Compose)
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
  ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "")
  sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env
  [ -n "$ENCRYPTION_KEY" ] && sed -i "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=${ENCRYPTION_KEY}|" .env
  echo ">> .env criado com chaves geradas. Revise as senhas do banco antes de expor publicamente."
fi

docker compose up -d --build
echo ">> Frontend: http://localhost:3000 | API: http://localhost:8000/docs"
