#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

uvx mypy \
  apps/api/src/berrybrain_api/ai_gateway.py \
  apps/api/src/berrybrain_api/settings_store.py \
  apps/api/src/berrybrain_api/routers/judge.py \
  apps/api/src/berrybrain_api/routers/settings.py \
  apps/api/benchmarks/retrieval_quality_benchmark.py \
  apps/api/benchmarks/judge_calibration_report.py \
  --ignore-missing-imports \
  --follow-imports=skip
