#!/usr/bin/env sh
set -eu

service="${1:-app}"
env_name="${BERRYBRAIN_ENV:-local}"

required_vars="
BERRYBRAIN_API_TOKEN
BERRYBRAIN_SESSION_SECRET
BERRYBRAIN_DATABASE_URL
BERRYBRAIN_VAULT_PATH
"

missing=""
for name in $required_vars; do
  value="$(printenv "$name" 2>/dev/null || true)"
  if [ -z "$value" ]; then
    missing="$missing $name"
  fi
done

if [ -n "$missing" ]; then
  echo "BerryBrain $service startup failed: missing required env vars:$missing" >&2
  exit 1
fi

max_request_body_bytes="${BERRYBRAIN_MAX_REQUEST_BODY_BYTES:-26214400}"
case "$max_request_body_bytes" in
  ''|*[!0-9]*)
    echo "BerryBrain $service startup failed: BERRYBRAIN_MAX_REQUEST_BODY_BYTES must be an integer" >&2
    exit 1
    ;;
esac

case "$env_name" in
  prod|production)
    if [ "$BERRYBRAIN_SESSION_SECRET" = "dev-change-me" ] || [ "$BERRYBRAIN_SESSION_SECRET" = "change-me-with-32-plus-random-bytes" ]; then
      echo "BerryBrain $service startup failed: production requires a strong BERRYBRAIN_SESSION_SECRET" >&2
      exit 1
    fi
    if [ "$BERRYBRAIN_API_TOKEN" = "change-me-generate-a-random-api-token" ]; then
      echo "BerryBrain $service startup failed: production requires a real BERRYBRAIN_API_TOKEN" >&2
      exit 1
    fi
    if [ "${BERRYBRAIN_SESSION_SECURE_COOKIE:-false}" != "true" ]; then
      echo "BerryBrain $service startup failed: production requires BERRYBRAIN_SESSION_SECURE_COOKIE=true" >&2
      exit 1
    fi
    ;;
esac

echo "BerryBrain $service env validation ok"
