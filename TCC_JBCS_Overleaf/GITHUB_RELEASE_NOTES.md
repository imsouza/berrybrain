# BerryBrain JBCS Research Artifact - 25 August 2026

## Scope

This release freezes the BerryBrain 1.4.8 research artifact used by the JBCS manuscript. It
preserves source code, lockfiles, benchmark programs, synthetic fixtures, retained evidence,
evaluation protocols, manuscript sources, and the compiled PDF.

The release does not relabel historical benchmark provenance. Retained runs continue to identify
their original commit and dirty-worktree state. The release is a preservation snapshot, not a claim
that every benchmark was rerun on the release commit.

## Validation Gates

- API: 465 tests and 59 subtests passed.
- Worker and API integration: 55 tests passed.
- Web: TypeScript typecheck, ESLint, and Next.js production build passed.
- Browser: 56 Playwright scenarios passed against the local full stack.
- Publication package: 11 live and local validation tests passed.
- Manuscript: XeLaTeX produced 11 pages with zero errors, warnings, unresolved references,
  unresolved citations, or overfull boxes.
- Citation metadata: `CITATION.cff` passed the Citation File Format 1.2.0 schema validator.

## Evidence Boundaries

No personal vault content, credentials, environment files, or secrets are distributed. Controlled
fixtures and mocked renderer measurements remain labeled and do not constitute real-user evidence.
The study does not claim human calibration, longitudinal adaptation, or universal superiority.

## Persistent Identifier

The GitHub release is immutable by tag. A Zenodo DOI has not yet been created and is not claimed by
this release. The DOI must be added to the manuscript only after the exact release is deposited and
the public Zenodo record is independently verified.
