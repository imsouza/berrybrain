# BerryBrain 1.4.8 Release Validation

## Release Identity

| Field | Value |
| --- | --- |
| Target | `v1.4.8` |
| Validation date | 14 August 2026 |
| Baseline | `c297558` / `v1.4.7` plus v1.4.8 worktree |
| Evidence class | Local release-candidate engineering evidence |
| Maturity | `incomplete-evidence`, minimum Level 0, median Level 2 |

## Functional Gates

| Gate | Result |
| --- | --- |
| API unit/integration | 459 passed, 1 skipped in 260.116 s |
| API branch coverage | 79%; required 78.5%; critical coverage passed |
| API Ruff | Check and format passed on 204 files |
| API MyPy | 13 progressive-contract modules passed |
| Worker | 55 passed; Ruff check and format passed |
| Multi-hop sidecar | 8 passed; Ruff check and format passed |
| Web | ESLint, TypeScript, and production build passed; 23 routes generated |
| Browser | 50/50 Chromium tests passed with retries disabled in 2.9 min |
| Accessibility | Landing/login automated WCAG A/AA scan passed; focus/reduced-motion test passed |
| Visual audit | Home and Ask inspected at 1440x1000 and 390x844; overlay and mobile Ask layout repaired |

## Performance Evidence

| Workload | Result |
| --- | --- |
| HTTP | 100/100 successful; 76.12 requests/s; p50/p95/p99 119.26/224.55/257.96 ms |
| Worker | 100/100 complete; 11.92 jobs/s drain; p95 8,060.36 ms; zero duplicate claims |
| S graph | 500 nodes/1,000 edges; p95 222.63 ms; 864,092 B payload |
| Release graph | 5,000 nodes/20,000 edges; p95 2,824.20 ms; 14,153,919 B payload |
| Browser graph | 10,000 nodes; 1,745.35 ms cold first visual; 4,443.49 ms complete; 33.60 ms interaction p95; 23.10 MB heap |
| Instrumentation | 0.003884 ms/op absolute overhead; 95% bootstrap CI [0.003526, 0.004281] |

## Retrieval And Judge Evidence

| Evaluation | Result |
| --- | --- |
| Internal graph hybrid | 44 queries; Recall@10 1.000; MRR 0.750; NDCG@10 0.815 |
| Internal multi-hop gain | +1.000; 95% bootstrap CI [1.000, 1.000]; no factual recall regression |
| BEIR SciFact BM25 context | 5,183 documents; 300 queries; Recall@10 0.7816; MRR 0.6386; NDCG@10 0.6644 |
| Judge synthetic regression | 100 evaluations; 30 synthetic labels; 29/30 match; kappa 0.9801; zero human reviews; not calibrated |

The internal fixture and SciFact baseline are not directly comparable because they use different
corpora and tasks. No competitive-superiority or human-calibration claim is made.

## Security And Supply Chain

| Gate | Result |
| --- | --- |
| Authentication/maintenance tests | 17 passed |
| Python locked dependency audit | No known vulnerabilities |
| Node production dependency audit | 0 vulnerabilities |
| Gitleaks | 107 commits, approximately 8.20 MB; no leaks after exact path/value fixture allowlists |
| Compose | Configuration valid |
| Container build | API, Worker, Web, and optional multi-hop sidecar images built with `--pull` |
| Trivy | API, Worker, Web, and sidecar each report 0 High/0 Critical |
| CycloneDX SBOM | API 232 components; Worker 105; Web 51; sidecar 120 |

## Evidence Boundary

This report supports a local engineering release. It does not establish production capacity,
independent replication, long-term feedback-learning benefit, human Judge calibration, confidence
calibration, or superiority over another RAG system. Those gates remain open in
`docs/planning/v1-4-8.md`.
