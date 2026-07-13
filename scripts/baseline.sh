#!/usr/bin/env sh
set -eu

WEB_URL="${BERRYBRAIN_BASELINE_WEB_URL:-http://127.0.0.1:3000/berrybrain}"
API_URL="${BERRYBRAIN_BASELINE_API_URL:-http://127.0.0.1:8000}"
API_TOKEN="${BERRYBRAIN_API_TOKEN:-}"
if [ -z "$API_TOKEN" ] && [ -f ".env" ]; then
  API_TOKEN="$(sed -n 's/^BERRYBRAIN_API_TOKEN=//p' .env | tail -1)"
fi

started_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

echo "BerryBrain baseline"
echo "started_at=$started_at"
echo "web_url=$WEB_URL"
echo "api_url=$API_URL"

echo "check=docker_compose_services"
docker compose config --services

echo "check=api_health"
curl -fsS "$API_URL/health" >/dev/null
echo "ok=api_health"

echo "check=web_landing"
curl -fsS "$WEB_URL" >/dev/null
echo "ok=web_landing"

echo "check=worker_status"
if [ -n "$API_TOKEN" ]; then
  curl -fsS -H "Authorization: Bearer $API_TOKEN" "$API_URL/api/v1/worker/status"
else
  echo "skip=worker_status reason=BERRYBRAIN_API_TOKEN not set"
fi

echo "completed_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
