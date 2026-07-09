#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE="${BERRYBRAIN_ENV_FILE:-.env}"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
COMPOSE_PROD="$COMPOSE_FILES --profile worker"
CERT_PATH="./data/certbot/conf/live/berrybrain"
DOMAIN="${BERRYBRAIN_DOMAIN:-berrybrain.local}"

usage() {
    echo "Usage: $0 {up|down|ssl|logs|status}"
    echo "  up      Start all services (api, web, nginx, worker)"
    echo "  down    Stop all services"
    echo "  ssl     Setup/renew Let's Encrypt certificate (DNS challenge)"
    echo "  logs    Tail logs from all services"
    echo "  status  Show service status"
    exit 1
}

init_ssl_placeholder() {
    if [ -f "$CERT_PATH/fullchain.pem" ]; then
        return 0
    fi
    echo "Generating self-signed placeholder cert so nginx can start..."
    mkdir -p "$CERT_PATH"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$CERT_PATH/privkey.pem" \
        -out "$CERT_PATH/fullchain.pem" \
        -subj "/CN=${DOMAIN}" 2>/dev/null
    cp "$CERT_PATH/fullchain.pem" "$CERT_PATH/chain.pem"
    echo "Placeholder cert created for $DOMAIN"
}

[ $# -eq 0 ] && usage

case "$1" in
    up)
        init_ssl_placeholder
        echo "Starting services..."
        docker compose $COMPOSE_PROD up -d --build
        echo ""
        echo "Access: https://${DOMAIN}  (self-signed until you run: $0 ssl)"
        echo "Or HTTP: http://localhost:${BERRYBRAIN_PROXY_HTTP:-80}"
        ;;

    down)
        docker compose $COMPOSE_PROD down
        ;;

    ssl)
        bash scripts/setup-ssl.sh
        echo "Reloading nginx..."
        docker compose $COMPOSE_FILES restart nginx
        ;;

    logs)
        docker compose $COMPOSE_FILES logs -f --tail=100
        ;;

    status)
        docker compose $COMPOSE_FILES ps
        ;;

    *)
        usage
        ;;
esac
