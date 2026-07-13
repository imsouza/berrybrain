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

echo "check=note_pipeline"
if [ -n "$API_TOKEN" ]; then
  note_title="Baseline $(date -u +%Y%m%dT%H%M%SZ)"
  payload="$(printf '{"title":"%s","folder":"inbox","content":"# %s\\n\\nBaseline note for install smoke testing."}' "$note_title" "$note_title")"
  note_response="$(curl -fsS -H "Authorization: Bearer $API_TOKEN" -H "Content-Type: application/json" -d "$payload" "$API_URL/api/v1/notes")"
  note_path="$(printf '%s' "$note_response" | sed -n 's/.*"path":"\([^"]*\)".*/\1/p')"
  if [ -z "$note_path" ]; then
    echo "fail=note_pipeline reason=note_path_missing"
    exit 1
  fi
  jobs_response="$(curl -fsS -H "Authorization: Bearer $API_TOKEN" "$API_URL/api/v1/jobs")"
  if ! printf '%s' "$jobs_response" | grep -q "$note_path"; then
    echo "fail=note_pipeline reason=job_not_enqueued note_path=$note_path"
    exit 1
  fi
  echo "ok=note_pipeline note_path=$note_path"
else
  echo "skip=note_pipeline reason=BERRYBRAIN_API_TOKEN not set"
fi

echo "completed_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
