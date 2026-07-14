#!/usr/bin/env bash
set -euo pipefail

repo="${BERRYBRAIN_GITHUB_REPO:-imsouza/berrybrain}"
branch="${BERRYBRAIN_DEFAULT_BRANCH:-main}"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI is required: https://cli.github.com/"
  exit 1
fi

gh auth status >/dev/null

ensure_label() {
  local name="$1"
  local color="$2"
  local description="$3"
  gh label create "$name" --repo "$repo" --color "$color" --description "$description" --force >/dev/null
}

ensure_epic() {
  local title="$1"
  local outcome="$2"
  if gh issue list --repo "$repo" --state all --search "in:title \"$title\"" --json title --jq '.[].title' | grep -Fxq "$title"; then
    return
  fi
  gh issue create \
    --repo "$repo" \
    --title "$title" \
    --label epic \
    --assignee imsouza \
    --body "Owner: @imsouza

Outcome:
$outcome

Acceptance criteria:
- [ ] Scope is implemented with persisted, non-mock data where applicable.
- [ ] Success, empty, degraded, and failure states are covered.
- [ ] Automated tests and documentation are updated.
- [ ] Evidence is attached before closure." >/dev/null
}

ensure_label epic 8250df "Product, architecture, quality, or release objective"
ensure_label security d73a4a "Security and privacy"
ensure_label release 0e8a16 "Release readiness and delivery"

ensure_epic "[Epic] Cognitive knowledge pipeline" "Keep note ingestion, semantic memory, graph expansion, insights, and review evidence-backed and observable."
ensure_epic "[Epic] Graph quality and inference" "Maintain useful nodes and explainable edges, grounded inference, graph integrity, and reversible actions."
ensure_epic "[Epic] Attachments and cognitive sources" "Process supported documents, images, audio, and video safely with provenance and resource limits."
ensure_epic "[Epic] Reliability and recovery" "Protect jobs, backups, restores, migrations, and degraded operation from silent data loss."
ensure_epic "[Epic] Security and privacy" "Maintain owner authentication, secret handling, local-first controls, and secure external-provider consent."
ensure_epic "[Epic] Release 1.0" "Complete consecutive green runs, immutable images, signatures, SBOM publication, and the final release audit."

protection_payload="$(mktemp)"
trap 'rm -f "$protection_payload"' EXIT
cat >"$protection_payload" <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "backend",
      "worker",
      "web",
      "compose",
      "security",
      "CodeQL",
      "Analyze (python)",
      "Analyze (javascript-typescript)"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "repos/$repo/branches/$branch/protection" \
  --input "$protection_payload" >/dev/null

echo "GitHub governance configured for $repo:$branch"
