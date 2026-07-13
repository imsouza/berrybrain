#!/usr/bin/env sh
set -eu

vault_path="${BERRYBRAIN_VAULT_PATH:-/app/vault}"
data_path="/app/data"

mkdir -p \
  "$vault_path" \
  "$data_path/sqlite" \
  "$data_path/jobs" \
  "$data_path/logs" \
  "$data_path/backups"

chmod 775 \
  "$vault_path" \
  "$data_path" \
  "$data_path/sqlite" \
  "$data_path/jobs" \
  "$data_path/logs" \
  "$data_path/backups"

echo "BerryBrain runtime directories ready"
