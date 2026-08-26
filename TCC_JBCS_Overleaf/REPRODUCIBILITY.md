# Reproducibility Protocol

## Identification

| Field | Value |
| --- | --- |
| System | BerryBrain 1.4.8 |
| Integrated-run revision | a81c566 (`v1.4.8`) |
| State | dirty worktree, recorded as a limitation |
| Local date | August 24, 2026 |
| UTC artifact date | August 25, 2026 |
| Integrated profile | S, exploratory |
| Seed | 20260812 |
| Hardware | Raspberry Pi 4, 4x Cortex-A72, up to 1.8 GHz |
| Memory | 7.6 GiB |
| OS | Debian aarch64, Linux 6.12.62 |
| Host Python | 3.11.2 |
| Integrated benchmark Python | 3.13.13 |
| Node.js | 20.20.2 |
| Docker | 29.3.1 |

## Recommended order

Frozen research artifact: <https://github.com/imsouza/berrybrain/releases/tag/jbcs-artifact-2026-08-25>

The release preserves the evaluated inputs and retained evidence. The run table below retains each
execution's original revision and dirty-state metadata rather than relabeling historical runs.

1. Create a clean clone at the recorded revision.
2. Install dependencies from repository lockfiles.
3. Confirm that no production vault is mounted into benchmark jobs.
4. Run tests before benchmarks.
5. Separate cold and warm cache measurements.
6. Preserve stdout, JSON, hashes, non-secret configuration, and Git state.

## Publication-package tests

From `TCC_JBCS_Overleaf`:

    node --test tests/submission-package.test.mjs

The eleven tests read the real manuscript, bibliography, declarations, metadata documents, and
compiled PDF. Three test groups call external authoritative services over HTTPS:

1. the ORCID Public API, to validate the first author's checksum and public-name agreement with the
   author block; and
2. the current JBCS submission page, to detect drift in template, compiler, review-model,
   declaration, cover-letter, and author-reviewer requirements; and
3. the institutional profiles recorded for potential reviewers, to verify names, institutional
   email addresses, and reported doctoral qualifications.

No local mock server, fabricated response, or static pass file is used. A network or upstream
failure fails the integration test instead of being converted into success.

## Reference commands

API:

    cd apps/api
    PYTHONPATH=src:. uv run pytest -p no:cacheprovider
    uvx ruff check --no-cache src tests benchmarks

Worker:

    cd apps/worker
    PYTHONPATH=src:../api/src:. ../api/.venv/bin/pytest -p no:cacheprovider
    uvx ruff check --no-cache src tests

Frontend:

    cd apps/web
    npm run lint
    npm run typecheck
    npm run build
    npm run test:e2e

Benchmarks:

    cd apps/api
    python -m benchmarks.retrieval_quality_benchmark --evidence-root reports/evidence
    python -m benchmarks.graph_performance_benchmark --on-disk --evidence-root reports/evidence
    python -m benchmarks.worker_queue_benchmark --jobs 100 --evidence-root reports/evidence
    python -m benchmarks.http_load_benchmark --base-url http://127.0.0.1:8000 --path /health
    python -m benchmarks.full_evaluation --repository-root ../.. --output-root ../../reports/evaluation

## Interpretation rules

- Fixture metrics are regression evidence, not generalization evidence.
- A model judge evaluated against synthetic references is not human-calibrated.
- SciFact BM25 cannot be compared directly with BerryBrain results from a different corpus.
- Test suite counts overlap and must not be added.
- The exploratory bootstrap used 2,000 resamples; confirmation requires at least 10,000.
- Runtime graph support uses a separate nominal empirical-Bernstein-style bounded-signal interval.
  It is not a calibrated probability or a demonstrated 95% truth-coverage interval.
- Every new run should record a clean commit, temperature, load, cache state, model, and provider.

## Evidence map

| Evidence | Run or artifact | Revision | Scope |
| --- | --- | --- | --- |
| Integrated profile S | `20260825T010700Z-be80c3b51974adc5` | `a81c566`, dirty | retrieval, backend, queue, faults, maturity |
| SciFact BM25 context | `20260814T045308Z-61842dc72de6976f` | `c297558`, dirty | independent lexical implementation check only |
| Judge regression | `reports/judge-calibration-report.json` | repository artifact | synthetic references; zero human reviews |
| Public browser | `reports/evaluation/browser-performance-public-v1.4.8.json` | `a81c566`, dirty | 30 public-route observations; SHA-256 `079e0f8a...cee82` |
| Synthetic 10k graph | `reports/evaluation/graph-performance-10k-v1.4.8.json` | `a81c566`, dirty | mocked-pagination renderer regression only; not live-backend or real-user evidence; SHA-256 `716ca64a...c3f0` |
| Consolidated claims | `evidence-summary.json` | mixed, explicitly identified | publication crosswalk; not raw evidence |

The SciFact run is intentionally not merged into the integrated profile. It uses a public corpus
and an earlier revision, so it can validate the external BM25 path but cannot support a direct
BerryBrain comparison. The referenced runs are preserved in the immutable GitHub artifact. Before
submission, archive that exact release in Zenodo and publish its checksums and DOI.

## Generative AI Transparency

Generative AI assisted software engineering, code review and debugging, automated-test design,
research organization, manuscript structure, and language revision. The first author executed the
test suites, inspected retained outputs, and verified evidence and references. Both authors remain
responsible for the work. `AI_USE_DISCLOSURE.md` records the scope and prohibited representations. AI assistance is
not treated as independent validation, human peer review, authorship, or an experimental result.

## Public corpus integrity

Source: <https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip>

SHA-256:
536e14446a0ba56ed1398ab1055f39fe852686ecad24a6306c80c490fa8e0165.
