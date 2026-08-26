# BerryBrain JBCS Overleaf Project

## Main file

Select main.tex as the main document. The included `latexmkrc` redirects Overleaf's default
pdfLaTeX command to XeLaTeX, which the official JBCS template requires. Selecting XeLaTeX in
Overleaf's project settings remains recommended and makes the engine choice explicit.

## Local compilation

    xelatex -interaction=nonstopmode -halt-on-error main.tex
    bibtex main
    xelatex -interaction=nonstopmode -halt-on-error main.tex
    xelatex -interaction=nonstopmode -halt-on-error main.tex

## Publication-package validation

Run the package tests from this directory:

    node --test tests/submission-package.test.mjs

The suite validates the actual manuscript and compiled PDF. It also performs live HTTPS checks
against the official ORCID Public API and the current JBCS submission page. It does not use a mock
registry, a mock journal page, fabricated responses, or a hardcoded passing result. Network access
is therefore required.

## Contents

- main.tex: complete English thesis/article in the JBCS layout.
- latexmkrc: forces XeLaTeX when an imported Overleaf project initially selects pdfLaTeX.
- refs.bib: cited academic, standards, and software references.
- REFERENCE_AUDIT.md: per-registry authenticity check covering all 45 cited entries.
- sbc2023.cls, styles, font, and image: official template assets.
- JBCS_COMPLIANCE.md: current editorial-rule audit and submission blockers.
- JBCS_SUBMISSION_REMAINING_STEPS.md: ordered distinction between initial-submission requirements,
  publication-stage DOI work, author-only attestations, and scientific review risks.
- OJS_SUBMISSION_FIELD_GUIDE.md: exact current section/category choices, acknowledgement boundaries,
  editor-comments content, and the reviewer-commitment stop condition.
- REPRODUCIBILITY.md: environment, commands, metrics, and interpretation limits.
- EVIDENCE_AUDIT.md: claim provenance, document integrity, and authenticity boundaries.
- evidence-summary.json: machine-readable consolidated evidence.
- SUBMISSION_METADATA.md: exact journal, section, area, author identity, and declaration state.
- AUTHOR_CONFIRMATION_CHECKLIST.md: unsigned declarations that only the author can make.
- COVER_LETTER_DRAFT.md: bounded pre-submission draft; not authorized for sending.
- COAUTHOR_REVIEWER_CONFIRMATION.md: verified second-author metadata and pending explicit consent
  to review up to two papers.
- POTENTIAL_REVIEWERS.md: real institutional candidates, pending author conflict checks.
- AI_USE_DISCLOSURE.md: detailed software-engineering, test-design, and writing-assistance record.
- tests/submission-package.test.mjs: manuscript, PDF, bibliography, ORCID, and journal-policy tests.

## Notes

- JBCS requires English and an ORCID for every author. The manuscript is English; Mateus Almeida de
  Souza's ORCID has a valid checksum, resolves through the official registry, and is linked in the
  author block. Leonardo Jose Silvestre's author-supplied ORCID remains pending.
- Do not replace pending results with estimates. Human studies, judge calibration, and same-corpus
  comparison remain confirmatory work.
- Controlled fixtures and the mocked-pagination renderer measurement remain explicitly labeled.
  They support regression or renderer claims only and are never represented as real-user evidence.
- The immutable GitHub artifact is available at
  <https://github.com/imsouza/berrybrain/releases/tag/jbcs-artifact-2026-08-25>. Its Zenodo deposit
  remains pending, and no DOI is claimed.
- Leonardo Jose Silvestre has a relevant PhD and may satisfy the author-reviewer expectation, but
  his explicit consent to review up to two papers remains mandatory.
- Originality, simultaneous-submission status, funding completeness, conflicts, permissions, and
  final approval require the author's personal attestation.
- Current instructions publish no explicit page limit. The valid count is the compiled PDF count.
- The validated build contains 11 pages. Its current SHA-256 is recorded in `EVIDENCE_AUDIT.md`.
- The class keeps Times New Roman when available and falls back to TeX Gyre Termes when the
  proprietary font is absent.
- The JBCSForceFreeFont macro selects the free fallback directly in CI.
