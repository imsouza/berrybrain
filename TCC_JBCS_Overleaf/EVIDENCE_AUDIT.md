# Evidence Audit

## Submission Identity

- Manuscript: BerryBrain 1.4.8 architecture and exploratory evaluation.
- First and corresponding author: Mateus Almeida de Souza.
- ORCID: `0009-0000-4701-1282`; valid ISO 7064 MOD 11-2 checksum and public-name match through the
  official ORCID Public API on August 25, 2026.
- Second author and academic supervisor: Professor Leonardo José Silvestre.
- Second-author ORCID: pending direct author supply and official-registry validation; no identifier
  was inferred.
- Student registration number: intentionally excluded because it is an internal academic identifier.
- Integrated revision: `a81c566`, dirty worktree.
- Frozen research artifact: `jbcs-artifact-2026-08-25`, preserving the source and retained evidence
  without rewriting the original run metadata.

## Traceability

| Evidence | Identifier or hash | Scope |
| --- | --- | --- |
| Integrated run | `20260825T010700Z-be80c3b51974adc5` | retrieval, backend, queue, faults, maturity |
| Integrated manifest SHA-256 | `4b1398a6b4951599a544cff2d6f48fcca10ca4e9d00555a610ce98d5052e18c1` | run provenance |
| SciFact context run | `20260814T045308Z-61842dc72de6976f` | independent BM25 context only |
| Public browser report SHA-256 | `079e0f8a3f891e7ad46957b0ce02c9a1d0003dbf77e4176f31f518b3735cee82` | 30 public-route observations |
| Synthetic 10k graph report SHA-256 | `716ca64a1d95ccd8fa586ecc962c451e898f826ea5ea058970f4951fabf9c3f0` | renderer regression |

`evidence-summary.json` consolidates the values used in the manuscript. It is a crosswalk, not raw
evidence. Repository paths and interpretation limits are documented in `REPRODUCIBILITY.md`.

## Scientific Boundaries

- Runtime support bounds are nominal empirical-Bernstein-style intervals over heterogeneous
  bounded signals, not calibrated probabilities of factual truth.
- The internal retrieval corpus is a deterministic regression fixture.
- SciFact BM25 was not compared with BerryBrain on the same corpus.
- Judge agreement uses synthetic references and contains zero human reviews.
- No participant or longitudinal field study has been completed.
- The measurements represent one ARM host and a dirty revision.

## Document Integrity

- XeLaTeX build: 11 pages, zero errors, unresolved citations/references, warnings, or overfull boxes.
- Compiled PDF SHA-256: `a7ce12afd64ee5a6d6449800c2ab714f327821a1302426354cb3231845c64215`.
- RQ1-RQ9 remain together on page 3.
- Figure 1 is on page 5, constrained to the available width, and documents runtime, authority,
  asynchronous processing, model routing, derived projections, retrieval, and feedback flow.
- Tables 1-12 appear in order on pages 3-8; Table 12 is on page 8 and References start on page 10.
- Result tables use local one-column placement so no float interrupts the Maturity paragraph.
- The final bibliography page is column-balanced; all 11 pages were visually checked for clipping,
  overlap, abnormal whitespace, and isolated floats.
- All 45 citation keys resolve to one BibTeX entry. All 28 DOI entries match Crossref or DataCite
  metadata, and all 17 non-DOI entries resolve through official or stable URLs. See
  `REFERENCE_AUDIT.md`.
- The English package contains no student registration number. The two-author record reflects the
  authorship confirmation supplied by the corresponding author.
- Eleven publication-package tests pass. They cover two-author identity and metadata, required declarations, generative-AI
  disclosure, metadata consistency, stale placeholders, citation-set equality, PDF/package
  integrity and hash agreement, the current JBCS submission policy, and institutional reviewer
  profiles. External checks use live official endpoints and no mocks.
- Generative AI assistance in software engineering and automated-test design is explicitly
  disclosed; it is not represented as independent scientific validation.

## Open Submission Blockers

The remaining non-delegable gates are the second author's verified ORCID, his explicit
author-reviewer response, both authors' signed truth declarations, independent final English
review, and a clean DOI-bearing Zenodo archive of the frozen GitHub release. The GitHub artifact is
versioned; the Zenodo deposit remains pending and no DOI is claimed.
Confirmatory external and human evidence remains required for stronger generalization claims, not
silently inferred from the exploratory results.
