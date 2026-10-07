#!/usr/bin/env bash
# Sourced by both entry points; .env is data, never executable shell.
BERRYBRAIN_DEPLOY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$BERRYBRAIN_DEPLOY_ROOT"
export BERRYBRAIN_ENV_FILE="${BERRYBRAIN_ENV_FILE:-.env}"
[[ -f "$BERRYBRAIN_ENV_FILE" ]] || { echo "Missing environment file: $BERRYBRAIN_ENV_FILE" >&2; exit 1; }

read_deploy_setting() {
    local key="$1" line value
    [[ ! -v "$key" ]] || return 0
    while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%$'\r'}"
        [[ "$line" == "$key="* ]] || continue
        value="${line#*=}"
        if [[ "$value" == \"*\" || "$value" == \'*\' ]]; then
            value="${value:1:${#value}-2}"
        else
            value="${value%% #*}"
        fi
        export "$key=$value"
    done < "$BERRYBRAIN_ENV_FILE"
}
for deploy_key in BERRYBRAIN_DOMAIN BERRYBRAIN_LETSENCRYPT_EMAIL BERRYBRAIN_DNS_PROVIDER BERRYBRAIN_CF_CREDENTIALS BERRYBRAIN_DO_CREDENTIALS BERRYBRAIN_CERTBOT_VERSION; do
    read_deploy_setting "$deploy_key"
done
DOMAIN="${BERRYBRAIN_DOMAIN:-berrybrain.local}"
[[ "$DOMAIN" =~ ^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$ && "$DOMAIN" != *..* ]] || { echo "Invalid BERRYBRAIN_DOMAIN." >&2; exit 1; }
COMPOSE=(docker compose --env-file "$BERRYBRAIN_ENV_FILE" -f docker-compose.yml -f docker-compose.prod.yml)

configure_proxy() {
    local certificate_dir=/etc/letsencrypt/self-signed/berrybrain temporary_config
    if [[ -s ./data/certbot/conf/live/berrybrain/fullchain.pem && -s ./data/certbot/conf/live/berrybrain/privkey.pem ]]; then
        certificate_dir=/etc/letsencrypt/live/berrybrain
    fi
    mkdir -p nginx/sites-enabled
    temporary_config="$(mktemp nginx/sites-enabled/.tls.XXXXXX)"
    if ! sed -e "s|__DOMAIN__|$DOMAIN|g" -e "s|__CERT_DIR__|$certificate_dir|g" nginx/templates/tls.conf.template > "$temporary_config"; then
        rm -f "$temporary_config"
        return 1
    fi
    chmod 644 "$temporary_config"
    mv "$temporary_config" nginx/sites-enabled/tls.conf
}
