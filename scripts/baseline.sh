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
  note_started_epoch="$(date +%s)"
  note_title="Baseline $(date -u +%Y%m%dT%H%M%SZ)"
  payload="$(printf '{"title":"%s","folder":"inbox","content":"# %s\\n\\nBaseline note for install smoke testing."}' "$note_title" "$note_title")"
  note_response="$(curl -fsS -H "Authorization: Bearer $API_TOKEN" -H "Content-Type: application/json" -d "$payload" "$API_URL/api/v1/notes")"
  echo "metric=note_create_seconds value=$(($(date +%s) - note_started_epoch))"
  note_path="$(printf '%s' "$note_response" | sed -n 's/.*"path":"\([^"]*\)".*/\1/p')"
  if [ -z "$note_path" ]; then
    echo "fail=note_pipeline reason=note_path_missing"
    exit 1
  fi
  jobs_response="$(curl -fsS -H "Authorization: Bearer $API_TOKEN" "$API_URL/api/v1/jobs?limit=200")"
  if ! printf '%s' "$jobs_response" | grep -q "$note_path"; then
    echo "fail=note_pipeline reason=job_not_enqueued note_path=$note_path"
    exit 1
  fi
  pipeline_started_epoch="$(date +%s)"
  pipeline_percent=0
  while [ "$(($(date +%s) - pipeline_started_epoch))" -lt 240 ]; do
    progress_response="$(curl -fsS -H "Authorization: Bearer $API_TOKEN" "$API_URL/api/v1/jobs/pipeline-progress")"
    pipeline_percent="$(printf '%s' "$progress_response" | python3 -c 'import json,sys; data=json.load(sys.stdin); path=sys.argv[1]; print(next((item.get("percent", 0) for item in data.get("notes", []) if item.get("notePath") == path), 0))' "$note_path")"
    [ "$pipeline_percent" -ge 100 ] && break
    sleep 2
  done
  pipeline_seconds="$(($(date +%s) - pipeline_started_epoch))"
  echo "metric=pipeline_seconds value=$pipeline_seconds percent=$pipeline_percent"
  if [ "$pipeline_percent" -lt 100 ]; then
    echo "fail=note_pipeline reason=timeout note_path=$note_path percent=$pipeline_percent"
    exit 1
  fi
  echo "ok=note_pipeline note_path=$note_path"

  search_seconds="$(curl -fsS -o /dev/null -w '%{time_total}' -G -H "Authorization: Bearer $API_TOKEN" --data-urlencode "q=$note_title" --data-urlencode "limit=10" "$API_URL/api/v1/search")"
  echo "metric=search_seconds value=$search_seconds"
else
  echo "skip=note_pipeline reason=BERRYBRAIN_API_TOKEN not set"
fi

echo "completed_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
