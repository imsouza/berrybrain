#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"
node scripts/lint/architecture-fitness.js | tee "${1:-reports/architecture-fitness.json}"
