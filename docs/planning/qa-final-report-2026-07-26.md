# BerryBrain QA Final Report

Date: 2026-07-26T06:53:19-03:00
Scope: full BerryBrain validation, `docs/planning/v-1-2-0.md`, `docs/planning/fix-new-version.md`, AI setup, graph consistency, UX/settings/sidebar, security, architecture and release gates.

## Result

Status: approved for the validated v1.2.0 scope.

- `v-1-2-0.md`: 244/244 checked before this pass.
- `fix-new-version.md`: 98/98 checked after this pass.
- Runtime stack: API, web and worker healthy through Docker Compose.
- Main user-facing regressions fixed: AI setup provider/model loading, graph scan/rebuild visibility, Graph Ask HTTP 500 path, graph/list parity, settings usability, HippoRAG default safety, Save as Insight.

## Main Fixes

- Added shared cloud provider presets and model normalization in web setup/settings.
- Fixed provider model-list parsing for OpenAI-compatible schemas.
- Added encrypted-at-rest storage for AI API keys and preserved masked API responses.
- Fixed Judge scorecard math: quadratic weighted kappa plus correct false-acceptance/false-rejection denominators.
- Replaced machine-specific hardcoded prompt path with `PROJECT_ROOT`.
- Added Qdrant and Chroma optional Docker profiles plus contract tests.
- Added retrieval benchmark, judge calibration fixture/report, security audit and architecture fitness gates.
- Set HippoRAG off by default and clarified UI wording: retrieval augmentation, not canonical graph truth.
- Added rollback test proving standard retrieval remains active when HippoRAG is disabled.
- Reduced Docker build context by ignoring `.venv`, caches and reports.
- Updated web dependency overrides so production `npm audit --omit=dev` is clean.

## Validation Evidence

- API tests: `210 passed, 1 warning, 4 subtests passed`.
- Worker tests: `34 passed`.
- Web lint: passed.
- Web typecheck: passed.
- Web build: passed on Next.js `15.5.22`.
- Docker build: API and web images built; web rebuilt after dependency override.
- Docker runtime: `berrybrain-api-1`, `berrybrain-web-1`, `berrybrain-worker-1` healthy.
- E2E: `29 passed`.
- Retrieval benchmark: pass, multi-hop recall gain `0.25`.
- Judge calibration: calibrated, weighted kappa `0.9801`.
- Security audit: pass, `0` failures.
- Architecture fitness: pass, `0` failures.
- Python progressive mypy: pass.
- Python focused Ruff format/check: pass.
- Web production dependency audit: `0` high/critical vulnerabilities.
- Python dependency audit: `0` known vulnerabilities.

## Generated Reports

- `reports/retrieval-benchmark.json`
- `reports/judge-calibration-report.json`
- `reports/security-audit.json`
- `reports/architecture-fitness.json`
- `reports/npm-audit-web-prod.json`
- `reports/pip-audit-api-worker.json`

## Residual Notes

- FastAPI TestClient emits a `StarletteDeprecationWarning` from dependency internals. It is not a BerryBrain runtime failure.
- Web dev-only `npm audit` still reports ESLint/minimatch advisory paths requiring breaking toolchain upgrades. Runtime/production audit is clean.
- Full-repository legacy Ruff/Mypy debt exists outside the progressive gate. Touched release-gate files pass Ruff and progressive Mypy.
