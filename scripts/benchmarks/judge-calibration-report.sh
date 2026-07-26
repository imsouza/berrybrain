#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/apps/api/.venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="${PYTHON_BIN_FALLBACK:-python3}"
fi

cd "$ROOT_DIR"
PYTHONPATH="$ROOT_DIR/apps/api:$ROOT_DIR/apps/api/src:${PYTHONPATH:-}" \
  "$PYTHON_BIN" -m benchmarks.judge_calibration_report \
  --fixture "${JUDGE_CALIBRATION_FIXTURE:-tests/fixtures/judge_calibration_fixture.json}" \
  --output "${1:-reports/judge-calibration-report.json}"
