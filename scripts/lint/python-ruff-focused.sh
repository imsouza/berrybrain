#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"
export RUFF_CACHE_DIR="${RUFF_CACHE_DIR:-/tmp/berrybrain-ruff-cache}"

uvx ruff format --check \
  apps/api/src/berrybrain_api/ai_gateway.py \
  apps/api/src/berrybrain_api/settings_store.py \
  apps/api/src/berrybrain_api/routers/judge.py \
  apps/api/src/berrybrain_api/routers/settings.py \
  apps/api/benchmarks/retrieval_quality_benchmark.py \
  apps/api/benchmarks/judge_calibration_report.py \
  apps/api/tests/test_settings.py \
  apps/api/tests/test_judge_committee.py \
  apps/api/tests/test_retrieval_quality_benchmark.py \
  apps/api/tests/test_judge_calibration_report.py \
  apps/api/tests/test_vector_store_docker_profiles.py \
  apps/api/tests/test_hipporag_defaults.py \
  apps/api/tests/test_cognitive_query_resilience.py

uvx ruff check \
  apps/api/src/berrybrain_api/ai_gateway.py \
  apps/api/src/berrybrain_api/settings_store.py \
  apps/api/src/berrybrain_api/routers/judge.py \
  apps/api/src/berrybrain_api/routers/settings.py \
  apps/api/benchmarks/retrieval_quality_benchmark.py \
  apps/api/benchmarks/judge_calibration_report.py \
  apps/api/tests/test_settings.py \
  apps/api/tests/test_judge_committee.py \
  apps/api/tests/test_retrieval_quality_benchmark.py \
  apps/api/tests/test_judge_calibration_report.py \
  apps/api/tests/test_vector_store_docker_profiles.py \
  apps/api/tests/test_hipporag_defaults.py \
  apps/api/tests/test_cognitive_query_resilience.py
