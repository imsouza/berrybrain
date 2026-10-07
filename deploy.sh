#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/scripts/deploy-common.sh"

init_ssl_placeholder() {
    local cert_path=./data/certbot/conf/self-signed/berrybrain previous_umask
    if [[ -f ./data/certbot/conf/live/berrybrain/fullchain.pem && -f ./data/certbot/conf/live/berrybrain/privkey.pem ]]; then
        return
    fi
    if [[ -f "$cert_path/fullchain.pem" && -f "$cert_path/privkey.pem" ]]; then
        return
    fi
    previous_umask="$(umask)"
    umask 077
    mkdir -p "$cert_path"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$cert_path/privkey.pem" -out "$cert_path/fullchain.pem" \
        -subj "/CN=${DOMAIN}" -addext "subjectAltName=DNS:${DOMAIN}"
    umask "$previous_umask"
}

case "${1:-}" in
    up)
        init_ssl_placeholder
        configure_proxy
        "${COMPOSE[@]}" up -d --build
        echo "Access: https://${DOMAIN} (self-signed until deploy.sh ssl succeeds)."
        ;;
    down) "${COMPOSE[@]}" down ;;
    ssl)
        bash scripts/setup-ssl.sh "${2:-issue}"
        "${COMPOSE[@]}" exec -T nginx nginx -t
        "${COMPOSE[@]}" exec -T nginx nginx -s reload
        ;;
    logs) "${COMPOSE[@]}" logs -f --tail=100 ;;
    status) "${COMPOSE[@]}" ps ;;
    *) echo "Usage: $0 {up|down|ssl [issue|renew]|logs|status}" >&2; exit 1 ;;
esac
