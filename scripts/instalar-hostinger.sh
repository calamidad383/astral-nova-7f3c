#!/usr/bin/env bash
# Instalación automática de la plataforma en un VPS (Hostinger u otro Ubuntu 24.04).
# Uso: bash scripts/instalar-hostinger.sh [dominio-opcional]
set -euo pipefail

cd "$(dirname "$0")/.."
DOMINIO="${1:-}"

echo "== 1/6 Docker =="
if ! command -v docker >/dev/null; then
    curl -fsSL https://get.docker.com | sh
fi
docker compose version >/dev/null 2>&1 || { echo "docker compose no disponible"; exit 1; }

echo "== 2/6 Firewall =="
if command -v ufw >/dev/null; then
    ufw allow OpenSSH >/dev/null 2>&1 || true
    ufw allow 80/tcp  >/dev/null 2>&1 || true
    ufw allow 443/tcp >/dev/null 2>&1 || true
    ufw allow 8000/tcp >/dev/null 2>&1 || true
    yes | ufw enable >/dev/null 2>&1 || true
fi

echo "== 3/6 Credenciales =="
if [ ! -f .env ]; then
    cp .env.example .env
    echo "AVISO: se creó .env desde .env.example. Súbelo con scp desde tu PC y reinicia."
fi

echo "== 4/6 Configuración de Caddy =="
if [ -n "$DOMINIO" ]; then
    sed "s/:80/${DOMINIO}/" docker/Caddyfile.example > docker/Caddyfile
    echo "Dominio: ${DOMINIO} (HTTPS automático)"
else
    cp docker/Caddyfile.example docker/Caddyfile
    echo "Sin dominio: se sirve por HTTP en el puerto 8000."
fi

echo "== 5/6 Construcción y arranque =="
cd docker
docker compose up -d --build

echo "== 6/6 Estado =="
sleep 5
docker compose ps
echo ""
echo "Listo. Panel: http://localhost:8000/app/ (desde el servidor)"
[ -n "$DOMINIO" ] && echo "Panel público: https://${DOMINIO}/app/" || echo "Panel público: http://IP_DEL_VPS:8000/app/"
echo "Logs: docker compose logs -f"
