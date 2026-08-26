# Documentation Authenticity Audit

## Audit Status

| Field | Value |
| --- | --- |
| Audit date | 25 August 2026 |
| Target | BerryBrain 1.4.8 and the JBCS manuscript package |
| Revision represented by integrated evidence | `a81c566`, dirty worktree |
| Classification | Exploratory engineering evidence |
| Result | Internally traceable; not yet publication-final |

This audit checks whether active documentation, manuscript claims, source code, and retained
measurement artifacts agree. It does not turn controlled fixtures into external validation and it
does not certify a dirty worktree as a release.

## Scope And Method

The repository-wide scan covered README, thesis material, active architecture/evaluation documents,
historical plans, report indexes, and the complete Overleaf package. Historical planning files were
preserved as records; stale confidence descriptions now carry an explicit historical notice and
point to the current source of truth.

The audit used six checks:

1. **Code-to-document inspection:** runtime behavior was compared with implementation and tests,
   with special attention to confidence, data authority, ontology, lifecycle, and provider routing.
2. **Claim-to-artifact tracing:** headline values were checked against retained JSON reports,
   manifests, run identifiers, and SHA-256 hashes.
3. **Statistical terminology review:** descriptive runtime support bounds were separated from
   inferential effect intervals and from calibrated probabilities of correctness.
4. **Reference audit:** every manuscript citation was matched to a BibTeX entry; DOI resolution and
   title metadata were checked where registries exposed them.
5. **Document integrity:** relative Markdown links, English submission text, author metadata, and
   prohibited internal identifiers were scanned.
6. **Rendered-output review:** the manuscript was compiled with XeLaTeX, its log was checked, text
   locations were extracted from the PDF, and every rendered page was visually inspected.
7. **Live publication validation:** the author identity, journal policy, PDF hash, and potential
   reviewer metadata were tested against the official ORCID API, current JBCS page, local artifact,
   and current institutional profiles without mock responses.

## Corrections Applied

| Area | Previous risk | Current state |
| --- | --- | --- |
| Runtime confidence | Active documentation contained stale Wilson/Jeffreys wording | Current docs identify `empirical-bernstein-bounded-signals-v1` and its limits |
| Confidence interpretation | A 95% label could be read as truth coverage | Described as a nominal evidence-support uncertainty interval, not calibrated truth probability |
| Architecture | Relational state was described as entirely rebuildable | Canonical Markdown, authoritative control state, and rebuildable projections are separated |
| Benchmark provenance | Integrated and external-context runs could appear merged | Run IDs, revisions, dirty state, and separate SciFact context are explicit |
| Browser evidence | Headline values lacked a current retained report | Public-route and synthetic 10k reports are retained and hashed |
| Authorship | An earlier draft did not reflect the final authorship decision and printed the student number | Mateus Almeida de Souza is first and corresponding author; Leonardo José Silvestre is second author and supervisor; the student number is removed |
| Tables | Queued double-column floats interrupted Maturity and created abnormal whitespace | Tables 4 and 6-12 use local one-column placement; Maturity is uninterrupted; the bibliography is column-balanced |
| Architecture figure | Figure exceeded the text width and omitted important runtime boundaries | Figure is constrained to `0.98\textwidth` and now covers authority, jobs, agents, exclusive provider routing, projections, retrieval, and feedback |
| SUS reference | DOI identified the containing book | DOI corrected to chapter `10.1201/9781498710411-35` |
| Historical plans | Superseded confidence claims looked current | A historical-status notice points to `docs/confidence-model.md` |
| ORCID | Required identifier was absent | Mateus Almeida de Souza's checksum and public name were validated through the official ORCID Public API; Leonardo José Silvestre's author-supplied ORCID remains pending and was not inferred |
| AI-use transparency | Software-engineering test assistance was not explicit | Manuscript and package disclose code, debugging, automated-test, research-organization, and language assistance |
| Submission package | Editorial actions were implicit | Metadata, two-author checklist, cover-letter draft, coauthor/reviewer confirmation form, reviewer research, and live validation tests are included |

## Headline Claim Ledger

| Claim | Value | Evidence | Interpretation boundary |
| --- | ---: | --- | --- |
| Internal graph-hybrid Recall@10 | 1.000 | `reports/evaluation/full-evaluation.json` | Controlled 44-query fixture |
| Standard-hybrid Recall@10 | 0.500 | same integrated bundle | Same fixture only |
| Multi-hop paired difference | +1.000, bootstrap [1.000, 1.000] | integrated run, seed 20260812, 2,000 resamples | Exploratory interval; designed fixture |
| BEIR SciFact BM25 Recall@10 | 0.7816 | run `20260814T045308Z-61842dc72de6976f` | External context, not a direct BerryBrain comparison |
| API statement coverage | 82.1905% | run `20260825T010700Z-be80c3b51974adc5` | Statement coverage, not behavioral completeness |
| Worker statement coverage | 48.9407% | same integrated run | Material residual risk |
| Local HTTP throughput | 62.017 requests/s | `reports/evaluation/http-load.json` | One Raspberry Pi 4 profile |
| Synthetic 10k graph completion | 6,349.92 ms | `reports/evaluation/graph-performance-10k-v1.4.8.json` | Mocked pagination; renderer regression |
| Synthetic 10k interaction p95 | 33.50 ms | same graph report | Eight scripted interactions |
| Public-route maximum wall p95 | 2,383.16 ms | `reports/evaluation/browser-performance-public-v1.4.8.json` | Five repetitions per route/profile |
| Judge weighted kappa | 0.9801 | `reports/judge-calibration-report.json` | Synthetic references; zero human reviews |

## Retained Artifact Identity

| Artifact | SHA-256 |
| --- | --- |
| Integrated manifest | `4b1398a6b4951599a544cff2d6f48fcca10ca4e9d00555a610ce98d5052e18c1` |
| Public-route browser report | `079e0f8a3f891e7ad46957b0ce02c9a1d0003dbf77e4176f31f518b3735cee82` |
| Synthetic 10k graph report | `716ca64a1d95ccd8fa586ecc962c451e898f826ea5ea058970f4951fabf9c3f0` |
| SciFact source archive | `536e14446a0ba56ed1398ab1055f39fe852686ecad24a6306c80c490fa8e0165` |
| Current JBCS package PDF | `f16f6b336adfb621bc943cfcdc1ce701a3a4301fab236f57e206a5a2a0df0759` |
| Current Overleaf ZIP | `200a539cfcf9bc3b105e45e1de5590e9f4f0d6d9982e662e11da53b2f012c6c6` |

## Confidence Finding

The runtime does not use a frequentist confidence interval for factual truth. It aggregates distinct
bounded scored signals, computes their sample mean and Bessel-corrected sample variance, and applies
an empirical-Bernstein-style radius. With one signal it deliberately returns `[0,1]`; with no scored
signals it returns unavailable. The persisted point is the interval midpoint.

The nominal construction level is 95%, but heterogeneous heuristic, model, and user signals have
not been shown to be independent observations from one common distribution. The result therefore
must not be described as calibrated correctness probability or demonstrated 95% truth coverage.
Retrieval effect intervals are separate paired percentile bootstrap intervals.

## Bibliography And Link Findings

- All 45 manuscript citation keys have one BibTeX entry; no entry is unused.
- All 28 DOI strings resolve after decoding LaTeX escapes. Titles, years, and first-author surnames
  match structured metadata: 22 entries through Crossref and six through DataCite.
- All 17 non-DOI references returned successful responses from W3C, official software
  documentation, or the retained JSTOR stable record.
- Holm (1979) has no confirmed DOI in the retained metadata and uses its stable JSTOR record.
- The package-level `REFERENCE_AUDIT.md` records the method, all 45 keys, registries, and the sole
  registry-year note for the Efron and Tibshirani book.
- The repository-relative scan covered 136 Markdown files and 48 local links and found no broken
  target in the audited scope.

## Rendered Manuscript Findings

- Compiler: XeLaTeX under TeX Live 2026, with the template's free-font fallback enabled locally.
- Final PDF: 11 pages.
- Compiled PDF SHA-256: `a7ce12afd64ee5a6d6449800c2ab714f327821a1302426354cb3231845c64215`.
- Log: zero LaTeX errors, fatal errors, unresolved citations, unresolved references, warnings, and
  overfull boxes.
- RQ1-RQ9: page 3.
- Figure 1: page 5, inside the two-column width, with expanded runtime and data-authority detail.
- Tables 1-12: monotonic order on pages 3-8.
- Table 12: page 8; References start on page 10.
- Every page was rasterized and visually checked for clipping, overlap, isolated floats, abnormal
  column gaps, and paragraph interruption. The last bibliography page is column-balanced.
- The author page visibly contains both authors and the first author's verified ORCID link. Eleven
  publication-package tests pass, including
  live official identity, journal-policy, and institutional-profile checks and a computed PDF hash
  comparison.

## Remaining Authenticity Boundaries

The manuscript is not ready for an external validity or superiority claim. Remaining blockers are:

- a clean immutable revision and evidence archive with DOI;
- Leonardo José Silvestre's author-supplied ORCID and official-registry validation;
- Leonardo José Silvestre's explicit consent to the qualified author-reviewer commitment;
- both authors' personal originality, simultaneous-submission, funding, conflict, permission, and
  final-approval attestations;
- independent final English review;
- same-corpus execution of BerryBrain and every baseline;
- an independently annotated corpus;
- human Judge calibration;
- an approved participant study and longitudinal feedback evaluation;
- independent hardware and external-service replication.

These are reported as missing evidence, not converted into estimates or synthetic placeholders.
