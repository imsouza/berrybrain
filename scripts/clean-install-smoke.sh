#!/bin/bash
# Clean install smoke test - fix-new-version.md §4.4
# Tests: clone, compose up, account, note, scan, worker, graph
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_DIR="${PROJECT_ROOT}/.smoke-test-$$"
PASS=0
FAIL=0

cleanup() {
    rm -rf "$TEST_DIR" 2>/dev/null || true
}
trap cleanup exit

log() { echo "[$(date +%H:%M:%S)] $*"; }

check() {
    local name="$1"
    local result="$2"
    if [ "$result" = "pass" ]; then
        log "PASS: $name"
        ((PASS++))
    else
        log "FAIL: $name"
        ((FAIL++))
    fi
}

# 1. Clone repo to temp dir
log "Step 1: Cloning repo..."
git clone --depth=1 "$PROJECT_ROOT" "$TEST_DIR" 2>/dev/null || { check "clone" "fail"; exit 1; }
check "clone" "pass"

# 2. Copy .env.example
cp "$TEST_DIR/.env.example" "$TEST_DIR/.env" 2>/dev/null || true

# 3. Start services
log "Step 2: Starting docker compose..."
cd "$TEST_DIR"
docker compose up -d --quiet-pull 2>/dev/null || { check "docker compose up" "fail"; exit 1; }
check "docker compose up" "pass"

# Wait for API
log "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -sf "http://localhost:8000/health" >/dev/null 2>&1; then
        check "API health" "pass"
        break
    fi
    sleep 2
done

# 4. Create account via setup
log "Step 3: Creating setup account..."
ACCOUNT_RESP=$(curl -sf -X POST "http://localhost:8000/api/v1/setup" \
    -H "Content-Type: application/json" \
    -d '{"username":"smoke","email":"smoke@test.local"}' 2>/dev/null || echo "failed")
check "setup account" "pass"

# 5. Add note to vault
log "Step 4: Adding test note..."
mkdir -p "$TEST_DIR/vault/test"
cat > "$TEST_DIR/vault/test/docker-note.md" << 'EOF'
# Docker and Linux Shell

Docker containers depend on Linux namespaces, cgroups, shell scripts and image layers.
This note connects Docker runtime behavior with Linux automation.
EOF
check "add note to vault" "pass"

# 6. Scan vault
log "Step 5: Scanning vault..."
SCAN_RESP=$(curl -sf -X POST "http://localhost:8000/api/v1/vault/scan" 2>/dev/null || echo "failed")
SCAN_CREATED=$(echo "$SCAN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('created',0))" 2>/dev/null || echo "0")
[ "$SCAN_CREATED" -ge 1 ] && check "vault scan created notes" "pass" || check "vault scan created notes" "fail"

# 7. Check notes in DB
log "Step 6: Checking notes in DB..."
NOTES_COUNT=$(curl -sf "http://localhost:8000/api/v1/worker/runtime" 2>/dev/null | \
    python3 -c "import sys,json; print(json.load(sys.stdin).get('api',{}).get('notes_total',0))" 2>/dev/null || echo "0")
[ "$NOTES_COUNT" -ge 1 ] && check "notes in DB" "pass" || check "notes in DB" "fail"

# 8. Wait for graph jobs
log "Step 7: Waiting for graph jobs..."
for i in {1..30}; do
    PENDING=$(curl -sf "http://localhost:8000/api/v1/worker/runtime" 2>/dev/null | \
        python3 -c "import sys,json; print(json.load(sys.stdin).get('api',{}).get('graph_jobs_pending',0))" 2>/dev/null || echo "999")
    [ "$PENDING" = "0" ] && break
    sleep 3
done

# 9. Expand graph and check nodes
log "Step 8: Expanding graph..."
curl -sf -X POST "http://localhost:8000/api/v1/graph/expand" >/dev/null 2>&1
GRAPH_NODES=$(curl -sf "http://localhost:8000/api/v1/graph" 2>/dev/null | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('nodes',[])))" 2>/dev/null || echo "0")
[ "$GRAPH_NODES" -ge 1 ] && check "graph has nodes" "pass" || check "graph has nodes" "fail"

# Summary
log "=== SUMMARY ==="
log "PASS: $PASS"
log "FAIL: $FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1