# Human-Supervised Validation Runner

## Purpose

This runner converts BerryBrain's twelve manual acceptance scenarios into a prospective,
checksummed evidence session. A human operates the real interface while the runner records explicit
observations, before/after screenshots, sanitized browser telemetry, optional cloud-provider route
evidence, durations, rationales, and attachments.

The runner never invents a result. An operator must assign `passed`, `failed`, or `blocked` to every
scenario. A contradictory structured observation forces `failed`; missing required evidence forces
`blocked`, even if the operator selected `passed`.

## Evidence Classification

The output is **author-supervised acceptance validation**. It can support claims that a recorded
workflow passed on one revision, environment, corpus, and session. It is not:

- an independent or blinded review;
- a participant usability study;
- a same-corpus comparative benchmark;
- evidence of population-level satisfaction;
- proof of Judge accuracy or longitudinal learning.

Use `docs/human-evaluation-protocol.md` for the independent confirmatory study.

## Prerequisites

- Run the BerryBrain Web, API, and Worker services.
- Use a dedicated sanitized vault. Do not use personal notes or participant data.
- Install Web dependencies and the Playwright Chromium browser.
- Configure the cloud provider through BerryBrain Settings. Never enter credentials in the runner.
- Run the command from an interactive terminal with access to the graphical browser session.

```bash
npm --prefix apps/web ci
npm --prefix apps/web exec -- playwright install chromium
```

## Start A Session

The minimum command is:

```bash
npm --prefix apps/web run validate:supervised -- \
  --base-url http://localhost:3000/berrybrain
```

Metadata can be supplied in advance without placing a secret on the command line:

```bash
npm --prefix apps/web run validate:supervised -- \
  --base-url https://berrybrain.example/berrybrain \
  --provider cloud-provider-label \
  --model cloud-model-label \
  --operator-id operator-01 \
  --corpus-id sanitized-vault-2026-08-27
```

The provider and model values are descriptive labels. API keys remain exclusively in BerryBrain
Settings or its secret store.

## Optional Backend Evidence

Browser telemetry cannot prove which server-side model route executed. Add one of these optional
sources when route-level evidence is required:

```bash
npm --prefix apps/web run validate:supervised -- \
  --base-url http://localhost:3000/berrybrain \
  --docker-container berrybrain-api-1
```

```bash
npm --prefix apps/web run validate:supervised -- \
  --base-url http://localhost:3000/berrybrain \
  --backend-log /tmp/berrybrain-api-validation.log
```

The runner does not retain the raw backend log. It records only redacted, truncated lines that
mention the configured cloud provider or model. If no backend source is supplied, the report labels
route evidence as operator attestation.

## Supervised Flow

For each browser scenario the runner:

1. prints the objective, actions, and pass criteria;
2. waits while the operator navigates to the initial state;
3. records a before screenshot and starts the evidence window;
4. waits while the operator performs the real actions;
5. records the resulting screenshot and sanitized telemetry;
6. asks structured factual questions;
7. requests an explicit status and evidence-based rationale;
8. optionally copies additional evidence files;
9. writes an incremental report before continuing.

Before any operational scenario begins, the runner requires `/api/v1/auth/me` to return HTTP 200.
An unauthenticated landing or login screen cannot be used as workflow evidence.

Version 2 also applies prospective-evidence guards:

- the default action window is at least 10 seconds per case;
- state-changing cases require the expected browser response and mutation activity;
- screenshots must show at least two distinct visual states;
- HTTP 401/403 responses force failure;
- unexpected HTTP 5xx responses force failure;
- copied rationales create an evidence gap;
- semantic inspection requires at least five nodes and five edges.

These are minimum sanity checks, not proof that the human interpretation is correct. Perform each
action after the before screenshot and do not preload answers into the terminal. The minimum action
window can be changed with `--minimum-action-seconds`, but a lower value weakens the resulting
evidence and must be justified in the report.

For accessibility, the operator performs keyboard, browser-zoom, and screen-reader checks. The
runner additionally provides a `390x844` mobile viewport and a recorded throttled profile of 300 ms,
1,500 kbps download, and 750 kbps upload. These parameters can be changed with command options.

The final scenario requires the operator to review the complete draft, verify every decision, and
attest that the bundle contains no credentials or personal vault content.

## Output

The default directory is:

```text
reports/evaluation/human-supervised/<run-id>/
```

Each completed run contains:

| Artifact | Purpose |
| --- | --- |
| `report.md` | Human-readable results and interpretation boundary |
| `results.json` | Structured observations, statuses, environment, and timings |
| `network-events.json` | Sanitized URL, status, type, and duration records; no bodies or headers |
| `browser-events.json` | Redacted browser warnings and errors |
| `evidence/` | Checksummed screenshots and operator-selected attachments |
| `manifest.json` | File sizes and SHA-256 values |
| `checksums.sha256` | Portable integrity verification |

Unless `--no-archive` is supplied, the runner also writes `<run-id>.tar.gz` beside the run
directory and prints its SHA-256 value. The output directory is ignored by Git because screenshots
and operator evidence can still be sensitive even when a sanitized vault is used.

## Resume An Interrupted Run

Every completed scenario is written immediately. Resume an interrupted session with the exact path
printed by the runner:

```bash
npm --prefix apps/web run validate:supervised -- \
  --resume reports/evaluation/human-supervised/<run-id>
```

Pass the backend evidence option again when resuming if it was used in the original process. A
resumed run skips completed operational scenarios and requires a new final evidence review.

## Safe Interpretation

- `passed`: operator decision agrees with all required structured observations.
- `failed`: the operator reported failure or a structured observation contradicts a pass criterion.
- `blocked`: required observation or evidence is unavailable.

A run is `passed` only when all twelve effective statuses pass. Preserve failed and blocked runs;
never delete an unfavorable session or overwrite it with a rerun. Use a new run ID for remediation
verification.

## Audited Runs

The first submitted version-1 bundle from August 27, 2026, was cryptographically valid but rejected
as prospective execution evidence. Its declared statuses are retained only as retrospective author
attestation. See `docs/reports/human-supervised-evidence-audit-2026-08-27.md`.
