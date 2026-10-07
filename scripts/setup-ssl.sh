#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/deploy-common.sh"

EMAIL="${BERRYBRAIN_LETSENCRYPT_EMAIL:-}"
DNS_PROVIDER="${BERRYBRAIN_DNS_PROVIDER:-cloudflare}"
if [[ "$DOMAIN" != *.* || "$DOMAIN" == *.local || -z "$EMAIL" ]]; then
    echo "Set a public BERRYBRAIN_DOMAIN and BERRYBRAIN_LETSENCRYPT_EMAIL." >&2
    exit 1
fi

run_options=()
plugin_options=()
case "$DNS_PROVIDER" in
    cloudflare|digitalocean)
        if [[ "$DNS_PROVIDER" == cloudflare ]]; then
            credentials="${BERRYBRAIN_CF_CREDENTIALS:-./data/certbot/cloudflare.ini}"
        else
            credentials="${BERRYBRAIN_DO_CREDENTIALS:-./data/certbot/digitalocean.ini}"
        fi
        [[ -f "$credentials" ]] || { echo "Missing DNS credentials file: $credentials" >&2; exit 1; }
        credentials="$(realpath "$credentials")"
        run_options+=(-v "$credentials:/root/.$DNS_PROVIDER.ini:ro")
        plugin_options+=("--dns-$DNS_PROVIDER" "--dns-$DNS_PROVIDER-credentials" "/root/.$DNS_PROVIDER.ini")
        export BERRYBRAIN_CERTBOT_IMAGE="certbot/dns-$DNS_PROVIDER:${BERRYBRAIN_CERTBOT_VERSION:-latest}"
        ;;
    route53)
        : "${AWS_ACCESS_KEY_ID:?Set AWS_ACCESS_KEY_ID}"
        : "${AWS_SECRET_ACCESS_KEY:?Set AWS_SECRET_ACCESS_KEY}"
        run_options+=(-e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY)
        [[ -z "${AWS_SESSION_TOKEN:-}" ]] || run_options+=(-e AWS_SESSION_TOKEN)
        plugin_options+=(--dns-route53)
        export BERRYBRAIN_CERTBOT_IMAGE="certbot/dns-route53:${BERRYBRAIN_CERTBOT_VERSION:-latest}"
        ;;
    manual)
        plugin_options+=(--manual --preferred-challenges dns)
        export BERRYBRAIN_CERTBOT_IMAGE="certbot/certbot:${BERRYBRAIN_CERTBOT_VERSION:-latest}"
        ;;
    *) echo "Unsupported DNS provider: $DNS_PROVIDER" >&2; exit 1 ;;
esac

mkdir -p ./data/certbot/conf ./data/certbot/www ./data/certbot/logs
case "${1:-issue}" in
    issue)
        issue_options=(certonly --cert-name berrybrain --keep-until-expiring
            --agree-tos --email "$EMAIL" -d "$DOMAIN")
        [[ "$DNS_PROVIDER" == manual ]] || issue_options+=(--non-interactive)
        "${COMPOSE[@]}" run --rm --no-deps "${run_options[@]}" certbot \
            "${issue_options[@]}" "${plugin_options[@]}"
        ;;
    renew)
        [[ "$DNS_PROVIDER" != manual ]] || { echo "Manual DNS requires interactive issuance; unattended renewal is unavailable." >&2; exit 1; }
        "${COMPOSE[@]}" run --rm --no-deps "${run_options[@]}" certbot \
            renew --cert-name berrybrain --non-interactive "${plugin_options[@]}"
        ;;
    *) echo "Usage: $0 [issue|renew]" >&2; exit 1 ;;
esac

[[ -s ./data/certbot/conf/live/berrybrain/privkey.pem ]]
openssl x509 -in ./data/certbot/conf/live/berrybrain/fullchain.pem -noout -checkend 0 >/dev/null
configure_proxy
echo "Certificate checked. Use deploy.sh ssl [issue|renew] to validate and reload nginx."
