#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${BERRYBRAIN_DOMAIN:-berrybrain.local}"
EMAIL="${BERRYBRAIN_LETSENCRYPT_EMAIL:-admin@berrybrain.local}"
DNS_PROVIDER="${BERRYBRAIN_DNS_PROVIDER:-cloudflare}"
CF_CREDENTIALS="${BERRYBRAIN_CF_CREDENTIALS:-./data/certbot/cloudflare.ini}"
CERTBOT_CONF="./data/certbot/conf"
CERTBOT_WWW="./data/certbot/www"
NGINX_CONF="./nginx/nginx.conf"
PID_FILE="./data/certbot/certbot.pid"

echo "=== BerryBrain SSL Setup ==="
echo "Domain: $DOMAIN"
echo "DNS Provider: $DNS_PROVIDER"

mkdir -p "$CERTBOT_CONF" "$CERTBOT_WWW" ./data/certbot/logs

if [ -d "$CERTBOT_CONF/live/$DOMAIN" ]; then
    echo "Certificate already exists for $DOMAIN"
    echo "To renew manually: docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot renew"
    exit 0
fi

# --- DNS Challenge ---
# Cloudflare
if [ "$DNS_PROVIDER" = "cloudflare" ]; then
    if [ ! -f "$CF_CREDENTIALS" ]; then
        echo "ERROR: Cloudflare credentials not found at $CF_CREDENTIALS"
        echo "Create it with:"
        echo "  mkdir -p ./data/certbot"
        echo "  echo 'dns_cloudflare_api_token = YOUR_CLOUDFLARE_API_TOKEN' > $CF_CREDENTIALS"
        echo "  chmod 600 $CF_CREDENTIALS"
        exit 1
    fi

    docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm \
        -v "$(pwd)/$CF_CREDENTIALS:/root/.cloudflare.ini:ro" \
        certbot \
        certonly \
        --dns-cloudflare \
        --dns-cloudflare-credentials /root/.cloudflare.ini \
        --dns-cloudflare-propagation-seconds 30 \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        -d "$DOMAIN" \
        --config-dir /etc/letsencrypt \
        --work-dir /var/lib/letsencrypt \
        --logs-dir /var/log/letsencrypt

# Route53 (AWS)
elif [ "$DNS_PROVIDER" = "route53" ]; then
    if [ -z "${AWS_ACCESS_KEY_ID:-}" ] || [ -z "${AWS_SECRET_ACCESS_KEY:-}" ]; then
        echo "ERROR: Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables"
        exit 1
    fi

    docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm \
        -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
        certbot \
        certonly \
        --dns-route53 \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        -d "$DOMAIN" \
        --config-dir /etc/letsencrypt \
        --work-dir /var/lib/letsencrypt \
        --logs-dir /var/log/letsencrypt

# DigitalOcean
elif [ "$DNS_PROVIDER" = "digitalocean" ]; then
    if [ -z "${DO_AUTH_TOKEN:-}" ]; then
        echo "ERROR: Set DO_AUTH_TOKEN environment variable"
        exit 1
    fi

    docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm \
        -e DO_AUTH_TOKEN \
        certbot \
        certonly \
        --dns-digitalocean \
        --dns-digitalocean-propagation-seconds 30 \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        -d "$DOMAIN" \
        --config-dir /etc/letsencrypt \
        --work-dir /var/lib/letsencrypt \
        --logs-dir /var/log/letsencrypt

# Manual / generic
elif [ "$DNS_PROVIDER" = "manual" ]; then
    echo "Running certbot in manual DNS mode. You'll need to add a TXT record."
    docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm \
        certbot \
        certonly \
        --manual \
        --preferred-challenges dns \
        --agree-tos \
        --email "$EMAIL" \
        -d "$DOMAIN" \
        --config-dir /etc/letsencrypt \
        --work-dir /var/lib/letsencrypt \
        --logs-dir /var/log/letsencrypt

else
    echo "ERROR: Unknown DNS provider: $DNS_PROVIDER"
    echo "Supported: cloudflare, route53, digitalocean, manual"
    exit 1
fi

# Update nginx config with real domain
if [ "$DOMAIN" != "berrybrain.local" ]; then
    echo "Updating nginx config with domain: $DOMAIN"
    sed -i "s|/etc/letsencrypt/live/berrybrain/|/etc/letsencrypt/live/$DOMAIN/|g" "$NGINX_CONF"
fi

echo ""
echo "=== DONE ==="
echo "Restart nginx to pick up certs:"
echo "  docker compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx"
echo ""
echo "Setup auto-renewal (cron):"
echo "  0 3 * * 0 cd $(pwd) && docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot renew && docker compose -f docker-compose.yml -f docker-compose.prod.yml exec nginx nginx -s reload"
