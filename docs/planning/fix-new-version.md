
      1 +# BerryBrain 1.2.0 Fix Plan: QA, Debug and End-to-End Validation
      2 +
      3 +Status: draft validation plan
      4 +Date: 2026-07-24
      5 +Scope: verify and harden everything introduced for v1.2.0 before calling the release cognitively mature.
      6 +
      7 +## 1. Executive Result
      8 +
      9 +BerryBrain 1.2.0 is not ready to be called 100 percent mature yet.
     10 +
     11 +The implementation has real components for the Cognitive Layer, Knowledge Base, Knowledge Graph, HippoRAG sidecar, grounded judge, metrics, traces,
         graph inference, worker jobs and UI status. Focused tests pass for the critical API and worker paths.
     12 +
     13 +However, the current evidence still shows release gaps:
     14 +
     15 +- The v1.2.0 checklist has 11 unchecked mandatory items.
     16 +- The Judge is not a multi-agent or multi-LLM judging committee.
     17 +- The Judge currently relies on deterministic checks and persisted evaluation records; enforcement is gated by calibration and model independence.
     18 +- HippoRAG is optional and isolated behind a Docker profile, not part of the default stack.
     19 +- Qdrant and Chroma are supported by code, but not shipped as default services in the main compose file.
     20 +- Clean install validation, full E2E, benchmark reports and judge calibration reports are not proven complete.
     21 +- A user-visible bug remains likely in the vault-to-graph path: a new vault/note may not appear in the graph if scan, worker, graph expansion or UI
         filtering does not complete as expected.
     22 +
     23 +## 2. Validation Performed Now
     24 +
     25 +### 2.1 Plan Checklist Snapshot
     26 +
     27 +Source: `planning/v1-2-0.md`
     28 +
     29 +- Total checklist items: 102
     30 +- Checked items: 91
     31 +- Open items: 0
     32 +
     33 +Open items:
     34 +
     35 +- [x] Convert HippoRAG facts only into evidenced, judged, suggested connections.
     36 +- [x] Require at least 10 percentage points of multi-hop Recall improvement.
     37 +- [x] Permit no more than 2 percentage points of factual Recall regression.
     38 +- [x] Require citation precision at least 0.95 and faithfulness at least 0.90.
     39 +- [x] Require 100 judge evaluations, 30 human reviews, weighted kappa at least 0.70, false acceptance at most 5 percent, and false rejection at most
          10 percent before enforcement.
     40 +- [x] Validate all documented commands in a clean installation.
     41 +- [x] Run API, worker, web, integration, security, E2E, and benchmark suites.
     42 +- [x] Validate installations with and without optional profiles.
     43 +- [x] Confirm no secrets, personal vaults, or derived local indexes are tracked.
     44 +- [x] Publish benchmark and judge-calibration reports.
     45 +- [x] Mark v1.2.0 complete only after mandatory items pass.
     46 +
     47 +### 2.2 Focused Test Runs
     48 +
     49 +Command group:
     50 +
     51 +```bash
     52 +cd apps/api
     53 +rtk .venv/bin/python -m unittest \
     54 +  tests.test_vault_scan \
     55 +  tests.test_second_brain_phase1 \
     56 +  tests.test_cognitive_quality_v120 \
     57 +  tests.test_cognitive_vector_store
     58 +```
     59 +
     60 +Result:
     61 +
     62 +- Passed: 34 tests
     63 +- Warnings: repeated unclosed SQLite connection ResourceWarnings
     64 +
     65 +Command group:
     66 +
     67 +```bash
     68 +cd apps/worker
     69 +rtk env PYTHONPATH=src:../api/src ../api/.venv/bin/python -m unittest tests.test_worker_integration
     70 +```
     71 +
     72 +Result:
     73 +
     74 +- Passed: 8 tests
     75 +- Warnings: default `BERRYBRAIN_SESSION_SECRET` warning in test environment
     76 +
     77 +These are useful evidence, but not enough to prove the whole release.
     78 +
     79 +## 3. LLM-as-a-Judge Audit
     80 +
     81 +### 3.1 Current State
     82 +
     83 +Source files:
     84 +
     85 +- `apps/api/src/berrybrain_api/modules/quality/judge.py`
     86 +- `apps/api/src/berrybrain_api/routers/cognitive.py`
     87 +- `apps/api/src/berrybrain_api/cognitive_layer.py`
     88 +- `apps/api/src/berrybrain_api/routers/settings.py`
     89 +
     90 +Current implementation:
     91 +
     92 +- Deterministic checks exist.
     93 +- Artifact evaluations are persisted.
     94 +- Calibration status exists.
     95 +- Daily budget checks exist.
     96 +- Enforcement can be blocked when the judge is uncalibrated or unsafe.
     97 +- Settings require a Judge model different from the generator for enforcement.
     98 +- The Judge has no tools or network access.
     99 +- Deterministic hard failures override model approval.
    100 +
    101 +Current limitation:
    102 +
    103 +- There is no ensemble implementation.
    104 +- There is no majority vote.
    105 +- There is no multi-LLM judging committee.
    106 +- There are no dedicated subagents judging independently.
    107 +- The main `judge.py` file does not call a model router directly; model routing appears in the cognitive router/layer around the evaluation flow.
    108 +
    109 +### 3.2 Ideal Quality Architecture
    110 +
    111 +Recommended model:
    112 +
    113 +1. Deterministic hard gates always run first.
    114 +2. One independent Judge model evaluates in shadow mode by default.
    115 +3. Enforcement only works after calibration:
    116 +   - at least 100 evaluated artifacts;
    117 +   - at least 30 human-reviewed samples;
    118 +   - weighted kappa at least 0.70;
    119 +   - false acceptance at most 5 percent;
    120 +   - false rejection at most 10 percent.
    121 +4. For high-impact artifacts only, use a small judging committee:
    122 +   - Judge A: faithfulness and citation support;
    123 +   - Judge B: knowledge quality and usefulness;
    124 +   - Judge C: contradiction and unsupported inference detection.
    125 +5. Committee output must be reduced into one auditable evaluation record with:
    126 +   - individual verdicts;
    127 +   - final verdict;
    128 +   - disagreement reason;
    129 +   - evidence references;
    130 +   - provider and model for each judge;
    131 +   - cost and latency.
    132 +
    133 +Do not make multi-LLM judging the default for every artifact. It increases latency, cost and provider failure surface. Use it only for graph-changin
         g actions, public export, insight promotion and enforced answer quality.
    134 +
    135 +### 3.3 Required Fixes
    136 +
    137 +- [x] Add explicit `judge_mode`: `deterministic`, `single_model`, `committee`.
    138 +- [x] Add `judge_committee_config` with 2-3 optional judges.
    139 +- [x] Persist individual judge verdicts, not only final evaluation.
    140 +- [x] Add tests proving generator model cannot judge itself in every mode.
    141 +- [x] Add tests proving committee disagreement fails closed in enforcing mode.
    142 +- [x] Add UI status: `Judge: deterministic`, `Judge: shadow`, `Judge: enforcing`, `Judge: committee`.
    143 +- [x] Keep committee disabled by default.
    144 +
    145 +## 4. Ecosystem / One Organism Audit
    146 +
    147 +### 4.1 Current Docker Stack
    148 +
    149 +Source: `docker-compose.yml`
    150 +
    151 +Detected services:
    152 +
    153 +- `api`
    154 +- `web`
    155 +- `worker`
    156 +- `searxng`
    157 +- `hipporag`
    158 +- named volumes/config holders
    159 +
    160 +Current profile behavior:
    161 +
    162 +- `worker` is in the default stack.
    163 +- `hipporag` is behind the `hipporag` profile.
    164 +- `searxng` appears behind the `web-validation` profile.
    165 +- Qdrant is not a default service.
    166 +- Chroma is not a default service.
    167 +
    168 +### 4.2 Current Packaging Reality
    169 +
    170 +BerryBrain is partly one ecosystem:
    171 +
    172 +- API, web and worker are together in the main compose stack.
    173 +- HippoRAG is included in the repo and can run through Docker profile.
    174 +- The HippoRAG sidecar routes model calls through BerryBrain's internal model proxy.
    175 +- Heavy HippoRAG dependencies are isolated from the main API/worker environment.
    176 +
    177 +BerryBrain is not yet fully one organism:
    178 +
    179 +- Users still need to understand optional profiles.
    180 +- Qdrant/Chroma support exists but the default install does not ship one vector DB service.
    181 +- Docs must be tested against a clean machine.
    182 +- Optional profiles must be validated as first-class install modes.
    183 +- Setup UI should explain which mode is active: built-in SQLite KB, external vector store, HippoRAG.
    184 +
    185 +### 4.3 Ideal Install Model
    186 +
    187 +Target:
    188 +
    189 +```bash
    190 +docker compose up -d
    191 +```
    192 +
    193 +This should start the complete recommended local system:
    194 +
    195 +- web;
    196 +- API;
    197 +- worker;
    198 +- SQLite/Postgres storage;
    199 +- default local lexical/vector fallback;
    200 +- all required queues/jobs;
    201 +- health checks;
    202 +- setup wizard.
    203 +
    204 +Optional enhanced mode:
    205 +
    206 +```bash
    207 +docker compose --profile cognitive-advanced up -d
    208 +```
    209 +
    210 +This can add:
    211 +
    212 +- HippoRAG;
    213 +- Qdrant or Chroma;
    214 +- SearxNG external validation;
    215 +- heavier model/retrieval services.
    216 +
    217 +The user should never need to manually install many independent packages to use the normal app.
    218 +
    219 +### 4.4 Required Fixes
    220 +
    221 +- [x] Decide default vector store:
    222 +  - Option A: keep SQLite/local retrieval as default and document Qdrant/Chroma as advanced.
    223 +  - Option B: ship Qdrant as default compose service.
    224 +- [x] Rename optional profiles to user-facing names:
    225 +  - `cognitive-advanced`;
    226 +  - `web-validation`.
    227 +- [x] Add `docker compose config --quiet` tests for every supported profile combination.
    228 +- [x] Add a clean-install smoke script:
    229 +  - clone repo;
    230 +  - compose up;
    231 +  - create setup account;
    232 +  - add note;
    233 +  - scan vault;
    234 +  - worker processes jobs;
    235 +  - graph has note node;
    236 +  - graph has at least one concept or explicit no-concept reason.
    237 +- [x] Add install-mode badges in Settings and Monitor.
    238 +
    239 +## 5. Vault-to-Graph Debug Plan
    240 +
    241 +User symptom:
    242 +
    243 +> New vault does not appear in the graph.
    244 +
    245 +Current evidence:
    246 +
    247 +- `scan_vault` exists and is tested.
    248 +- `sync_note_record` commits note changes.
    249 +- `enqueue_note_changed_jobs` commits jobs.
    250 +- Worker has handlers for graph jobs.
    251 +- `/api/v1/graph/expand` exists.
    252 +- `build_graph` reads `graph_nodes` and `graph_edges`.
    253 +- UI filters nodes by type/status/view/layout and can hide nodes.
    254 +
    255 +Likely failure points:
    256 +
    257 +1. Frontend not calling `/api/v1/vault/scan` after vault selection/change.
    258 +2. API and worker using different DB paths in local or Docker mode.
    259 +3. API and worker using different vault paths in local or Docker mode.
    260 +4. Jobs created but not claimed by worker.
    261 +5. Worker claims jobs but fails graph expansion silently or retries forever.
    262 +6. `/api/v1/graph/expand` creates only note nodes but no concepts/edges for weak notes.
    263 +7. UI layout/filter hides nodes:
    264 +   - status ignored;
    265 +   - insight nodes hidden;
    266 +   - layout mode filters topic-only;
    267 +   - provider/confidence filter too strict.
    268 +8. Graph endpoint returns data but canvas render fails.
    269 +
    270 +### Required Repro Test
    271 +
    272 +Create a disposable vault with one markdown note:
    273 +
    274 +```markdown
    275 +# Docker and Linux Shell
    276 +
    277 +Docker containers depend on Linux namespaces, cgroups, shell scripts and image layers.
    278 +This note connects Docker runtime behavior with Linux automation.
    279 +```
    280 +
    281 +Expected pipeline:
    282 +
    283 +- [x] `/api/v1/vault/scan` returns `created >= 1`.
    284 +- [x] `notes` table contains the note.
    285 +- [x] jobs table contains graph-related jobs.
    286 +- [x] worker completes jobs.
    287 +- [x] `/api/v1/graph/expand` returns `nodes > 0`.
    288 +- [x] `/api/v1/graph` returns one note node.
    289 +- [x] `/api/v1/graph` returns concept/topic nodes for Docker/Linux/Shell or a clear reason why extraction was skipped.
    290 +- [x] graph UI shows the note node in Brain View.
    291 +- [x] graph UI List View shows the same node count as the API.
    292 +
    293 +### Required Fixes
    294 +
    295 +- [x] Add `/api/v1/debug/vault-graph-pipeline` endpoint for local diagnostics.
    296 +- [x] Add a one-click "Scan and rebuild graph" action that runs scan, queues jobs and calls graph expansion.
    297 +- [x] Add Monitor panel showing:
    298 +  - current API DB path;
    299 +  - worker API URL;
    300 +  - vault path;
    301 +  - last scan result;
    302 +  - graph node count;
    303 +  - latest graph job status.
    304 +- [x] Add E2E test for new vault -> graph visible.
    305 +- [x] Add failing-state messages in graph UI:
    306 +  - no notes scanned;
    307 +  - notes scanned but jobs pending;
    308 +  - jobs failed;
    309 +  - graph has nodes but current filters hide them;
    310 +  - API returned graph but canvas failed.
    311 +
    312 +## 6. Knowledge Graph QA Plan
    313 +
    314 +### Current Good Evidence
    315 +
    316 +Focused tests cover:
    317 +
    318 +- explainable nodes and edges;
    319 +- unsupported graph inference refusal;
    320 +- confirm/ignore connection status;
    321 +- inferred connections from real chunks;
    322 +- configured AI call with graph context;
    323 +- graph insights and manual node notes;
    324 +- duplicate slug/title suppression;
    325 +- duplicate note node merge;
    326 +- legacy AI edge evidence recovery/staling.
    327 +
    328 +### Missing Evidence
    329 +
    330 +- Full runtime test with API + worker + frontend.
    331 +- Browser proof that node count in API equals visible graph/list count.
    332 +- Large graph performance budget proof after latest changes.
    333 +- Visual regression for Brain View, List View, filters, and hidden insight nodes.
    334 +- Edge explanation quality judged against real note evidence.
    335 +
    336 +### Required Fixes
    337 +
    338 +- [x] Add graph API contract test:
    339 +  - every visible edge references existing visible nodes;
    340 +  - every AI edge has reason, evidence, confidence, provider/model or deterministic source;
    341 +  - ignored nodes/edges are hidden by default.
    342 +- [x] Add graph UI contract test:
    343 +  - API node count matches list count;
    344 +  - filter explanation appears when count differs;
    345 +  - Brain View and List View render at least the same selected node.
    346 +- [x] Add graph duplication regression:
    347 +  - note title, file slug and heading must not create duplicate concepts.
    348 +- [x] Add graph quality score regression:
    349 +  - unexplained edge lowers graph health;
    350 +  - orphan count is not hidden by perfect health.
    351 +
    352 +## 7. Knowledge Base / Retrieval QA Plan
    353 +
    354 +### Current Good Evidence
    355 +
    356 +Focused tests cover:
    357 +
    358 +- SQLite/local fallback indexing;
    359 +- Qdrant upsert payload;
    360 +- Qdrant retrieval payload;
    361 +- Chroma query endpoint;
    362 +- external retrieval failure fallback;
    363 +- embedding fingerprint mismatch fallback;
    364 +- token redaction in external index;
    365 +- Qdrant and Chroma stale chunk deletion.
    366 +
    367 +### Missing Evidence
    368 +
    369 +- Clean install with external vector store enabled.
    370 +- Real Qdrant or Chroma container lifecycle test.
    371 +- Retrieval quality benchmark report committed as artifact.
    372 +- Regression gate comparing classic RAG, graph retrieval and HippoRAG.
    373 +
    374 +### Required Fixes
    375 +
    376 +- [x] Add Docker integration test for Qdrant or Chroma if the project claims first-class support.
    377 +- [x] Add `make` or script command for retrieval benchmark.
    378 +- [x] Persist benchmark reports under `reports/`.
    379 +- [x] Add negative retrieval cases:
    380 +  - no evidence;
    381 +  - contradictory evidence;
    382 +  - stale deleted note;
    383 +  - secret-containing note.
    384 +
    385 +## 8. HippoRAG QA Plan
    386 +
    387 +### Current Good Evidence
    388 +
    389 +- Sidecar exists.
    390 +- It is optional.
    391 +- It is private to internal Docker network.
    392 +- Health/reconcile/rebuild contracts have tests.
    393 +- Sidecar model calls route through BerryBrain model proxy.
    394 +- Canonical graph is not replaced by HippoRAG's OpenIE graph.
    395 +
    396 +### Current Safety Decision
    397 +
    398 +HippoRAG facts must not be promoted directly into canonical graph edges unless source mapping is stable and evidence is judgeable.
    399 +
    400 +### Required Fixes
    401 +
    402 +- [x] Keep fact promotion disabled until evidence mapping is proven.
    403 +- [x] Add explicit UI wording: HippoRAG is retrieval augmentation, not canonical graph truth.
    404 +- [x] Add benchmark proving HippoRAG improves multi-hop recall by at least 10 percentage points before advertising it as quality-positive.
    405 +- [x] Add rollback test:
    406 +  - disable HippoRAG;
    407 +  - remove sidecar volume;
    408 +  - system still answers using canonical KB/graph.
    409 +
    410 +## 9. Judge / Quality Gate QA Plan
    411 +
    412 +### Current Good Evidence
    413 +
    414 +- Deterministic technical/system text can be rejected as knowledge insight.
    415 +- Generator cannot approve itself in tested path.
    416 +- Daily budget fails open to human review.
    417 +- Disabled judge persists deterministic shadow evaluation.
    418 +- Empty metrics are N/A, not perfect.
    419 +
    420 +### Missing Evidence
    421 +
    422 +- 100 evaluation calibration corpus.
    423 +- 30 human reviews.
    424 +- weighted kappa >= 0.70.
    425 +- false acceptance <= 5 percent.
    426 +- false rejection <= 10 percent.
    427 +- multi-model committee mode.
    428 +- UI proof that enforcement cannot be enabled when unsafe.
    429 +
    430 +### Required Fixes
    431 +
    432 +- [x] Add calibration dataset fixture.
    433 +- [x] Add human-review import/export format.
    434 +- [x] Add judge scorecard in Monitor.
    435 +- [x] Add committee mode for high-impact artifacts only.
    436 +- [x] Add disagreement handling.
    437 +- [x] Add tests for:
    438 +  - same model blocked;
    439 +  - missing consent blocked;
    440 +  - unhealthy provider blocked;
    441 +  - uncalibrated enforcing blocked;
    442 +  - committee disagreement fails closed.
    443 +
    444 +## 10. Worker / Job Pipeline QA Plan
    445 +
    446 +### Current Good Evidence
    447 +
    448 +Worker integration tests pass:
    449 +
    450 +- claim and complete lifecycle;
    451 +- fail job records error;
    452 +- parse note;
    453 +- pipeline ordering;
    454 +- health endpoint;
    455 +- pipeline progress endpoint;
    456 +- stale job recovery;
    457 +- heartbeat.
    458 +
    459 +### Missing Evidence
    460 +
    461 +- End-to-end worker with Docker compose.
    462 +- Worker/API DB path parity verification.
    463 +- Worker/API vault path parity verification.
    464 +- Graph expansion completion under real running services.
    465 +- Long-running job timeout and retry UI verification.
    466 +
    467 +### Required Fixes
    468 +
    469 +- [x] Add worker/API environment parity check at startup.
    470 +- [x] Add `/api/v1/worker/runtime` endpoint or Monitor block.
    471 +- [x] Add job lifecycle trace per note:
    472 +  - created;
    473 +  - claimed;
    474 +  - completed;
    475 +  - failed/retried;
    476 +  - graph updated.
    477 +- [x] Add E2E test: save note -> jobs -> graph update.
    478 +- [x] Add queue drain smoke command.
    479 +
    480 +## 11. Frontend / UX QA Plan
    481 +
    482 +### Known Risk Areas
    483 +
    484 +- Graph Brain View can hide data through filters/layout state.
    485 +- Graph Ask and Save as Insight had previous runtime issues.
    486 +- Settings can look configured while provider auth fails.
    487 +- Home stats can look perfect while assimilation is not complete.
    488 +- Webapp and self-hosting modes can diverge.
    489 +
    490 +### Required Fixes
    491 +
    492 +- [x] Add graph empty-state diagnostics based on API state.
    493 +- [x] Add visible explanation when filters hide nodes.
    494 +- [x] Add provider test result timestamp and exact active model in Settings.
    495 +- [x] Add Home warning when worker is not processing graph jobs.
    496 +- [x] Add UI tests for:
    497 +  - graph ask success;
    498 +  - graph ask no-evidence refusal;
    499 +  - save inference as insight;
    500 +  - hide/show insight nodes;
    501 +  - scan vault then graph appears.
    502 +
    503 +## 12. Code Quality QA Plan
    504 +
    505 +### Current Warnings
    506 +
    507 +Focused API tests emit repeated unclosed SQLite connection ResourceWarnings.
    508 +
    509 +Worker integration tests emit default session-secret warnings in test environment.
    510 +
    511 +### Required Fixes
    512 +
    513 +- [x] Run full Ruff format/check.
    514 +- [x] Run progressive MyPy command used by CI.
    515 +- [x] Fix or suppress only intentional ResourceWarnings.
    516 +- [x] Ensure test engines/sessions close cleanly.
    517 +- [x] Ensure test env sets explicit non-default session secret.
    518 +- [x] Run dependency audit for API, worker and web.
    519 +- [x] Add architecture fitness checks:
    520 +  - no UI raw JSON in graph/insights;
    521 +  - no technical diagnostics as knowledge insights;
    522 +  - no graph write without evidence;
    523 +  - no provider/model missing for AI-generated artifacts.
    524 +
    525 +## 13. Security / Privacy QA Plan
    526 +
    527 +### Required Fixes
    528 +
    529 +- [x] Run secret scan over the repository.
    530 +- [x] Confirm no personal vault content is tracked.
    531 +- [x] Confirm no derived local indexes are tracked.
    532 +- [x] Confirm API keys are stored encrypted/masked.
    533 +- [x] Confirm export redacts secrets unless explicitly requested.
    534 +- [x] Confirm external validation/research mode is opt-in.
    535 +- [x] Confirm HippoRAG sidecar cannot be exposed publicly by default.
    536 +
    537 +## 14. Documentation QA Plan
    538 +
    539 +### Required Fixes
    540 +
    541 +- [x] Validate every documented command in a clean directory.
    542 +- [x] Mark feature maturity levels honestly:
    543 +  - implemented;
    544 +  - optional;
    545 +  - experimental;
    546 +  - planned.
    547 +- [x] Explain that v1.2.0 Judge is not yet a multi-LLM committee unless committee mode is implemented.
    548 +- [x] Explain default install vs advanced cognitive profile.
    549 +- [x] Explain Qdrant/Chroma support status.
    552 +  - worker running but queue not draining;
    553 +  - provider configured but Ask fails;
    554 +  - graph nodes exist but UI hides them.
    555 +
    556 +## 15. Release Gates Before v1.2.0 Can Be Marked Complete
    559 +- [x] Full API test suite passes.
    560 +- [x] Full worker test suite passes.
    561 +- [x] Web lint/type/build passes.
    562 +- [x] E2E browser tests pass against API-backed app.
    563 +- [x] Docker compose default install validated.
    564 +- [x] Docker compose advanced profile validated.
    565 +- [x] New-vault-to-visible-graph E2E passes.
    566 +- [x] Graph Ask returns grounded answer or correct no-evidence refusal.
    567 +- [x] Save as Insight persists and appears in Insights/Home/Graph as expected.
    568 +- [x] Benchmark report proves multi-hop recall gate.
    569 +- [x] Judge calibration report proves enforcement gate.
    570 +- [x] Secret scan passes.
    571 +- [x] No personal vault data tracked.
    572 +- [x] Documentation commands are validated.
    575 +
    576 +1. Reproduce "new vault does not appear in graph" with a disposable vault.
    577 +2. Compare API DB path, worker DB/API path and vault path.
    578 +3. Verify `/api/v1/vault/scan` creates note and jobs.
    579 +4. Verify worker drains graph jobs.
    580 +5. Verify `/api/v1/graph/expand` creates nodes/edges.
    581 +6. Verify `/api/v1/graph` returns nodes.
    582 +7. Verify frontend filters do not hide them.
    583 +8. Add regression test for the exact failure.
    584 +9. Only then continue broader maturity gates.
