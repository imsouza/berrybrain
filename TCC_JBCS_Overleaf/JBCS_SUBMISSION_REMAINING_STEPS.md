# JBCS Submission Remaining Steps

## Status

- Assessment date: August 25, 2026
- Manuscript stage: pre-submission; not submitted
- Article DOI: not assigned
- Software and evidence archive DOI: not yet created
- Repository release: <https://github.com/imsouza/berrybrain/releases/tag/jbcs-artifact-2026-08-25>

The DOI is not the only remaining item and is not the principal blocker for initial submission.

## The Two Different DOIs

### Article DOI

The journal assigns the article DOI after acceptance. The author must not create, predict, or place
a provisional journal DOI in the manuscript.

### Software And Evidence DOI

The frozen GitHub artifact records the source revision, evidence, prompts, lockfiles, non-secret
configuration, and reproduction instructions. Deposit that exact release through Zenodo.
This archive strengthens reproducibility but does not replace the journal's DOI. It can be added
during revision and must exist before the manuscript claims that it exists.

## Completed Requirements

- The manuscript is written in English.
- The official JBCS class and XeLaTeX workflow are used.
- The validated PDF contains 11 pages.
- The first author's ORCID checksum and public identity were verified through the official ORCID
  Public API and linked in the author block.
- Leonardo Jose Silvestre is recorded as second author and academic supervisor; his institutional
  identity, email, expertise, and doctoral qualification are documented.
- The manuscript contains CRediT contribution, competing-interest, funding, acknowledgement,
  data-and-materials, ethics, and generative-AI declarations.
- Generative-AI assistance in software engineering, debugging, automated-test design, research
  organization, structure, and language revision is explicitly disclosed.
- All citation keys resolve to bibliography entries, and the reference authenticity audit is
  included.
- The target JBCS category and area are `Information Retrieval`, matching the current OJS list.
- Submission metadata and a bounded cover-letter draft are included.
- Potential reviewer research uses real institutional profiles and does not claim nomination or
  absence of conflicts.
- The publication package has live validation tests for ORCID, current JBCS policy, institutional
  profiles, declarations, bibliography consistency, PDF integrity, and SHA-256 agreement.

## Mandatory Actions Before Initial Submission

### 1. Complete The Second Author's Identity

Obtain Leonardo Jose Silvestre's ORCID directly from him and validate its checksum and public-name
agreement through the official ORCID Public API. JBCS requires an ORCID for every author. No
identifier may be inferred from a name search.

### 2. Resolve The Author-Reviewer Requirement

The current JBCS instructions ask at least one author from each submitted paper to commit to
reviewing up to two papers. They state that volunteer reviewers are expected to hold a PhD or
equivalent degree in Computer Science or a closely related field.

Leonardo is the second author and has a relevant doctoral qualification. Obtain his explicit
agreement using `COAUTHOR_REVIEWER_CONFIRMATION.md`. Do not treat coauthorship as consent and do not
enter him as the committed reviewer unless he accepts.

### 3. Complete The Author-Only Attestations

Both authors must personally complete and approve `AUTHOR_CONFIRMATION_CHECKLIST.md`. An automated
system cannot truthfully confirm:

- originality;
- absence of simultaneous submission;
- complete funding disclosure;
- complete competing-interest disclosure;
- authorship eligibility;
- permissions and licensing;
- reviewer conflicts;
- accuracy of the final package; or
- authorization to submit.

### 4. Complete Independent English Review

Automated language checks and generative-AI revision do not constitute independent human or
professional language review. The final PDF must receive an independent English read-through after
the final technical edit.

### 5. Finalize Reviewer Suggestions

Before entering a potential reviewer in the journal portal, the authors must verify current
institutional contact details and check recent coauthorship, institutional ties, advisor or student
relationships, active collaboration, personal or financial conflicts, and journal-specific
exclusion periods. `POTENTIAL_REVIEWERS.md` contains research candidates only.

### 6. Finalize The Cover Letter

`COVER_LETTER_DRAFT.md` must not be sent until both authors approve it, Leonardo's ORCID is
verified, and his reviewer-commitment response is recorded. The final correspondence must
accurately state:

- why the manuscript fits JBCS;
- the selected JBCS area;
- relevant policy issues;
- competing interests;
- special-issue status, if applicable;
- relationships to earlier publications, if applicable;
- verified reviewer suggestions; and
- verified committed author-reviewer details, only if Leonardo accepts.

### 7. Complete The OJS Submission

After the preceding gates are satisfied, the corresponding author must:

1. create or verify both author records and ORCID associations;
2. choose the `Articles` section;
3. enter the title, abstract, keywords, author identity, affiliation, and declarations;
4. enter `Information Retrieval` in Comments to the Editor;
5. upload the validated PDF and required correspondence;
6. verify the generated submission summary; and
7. obtain both authors' final approval and personally authorize submission.

## Actions Before Final Revision Or Publication

1. Freeze a clean Git revision.
2. Run the essential software, benchmark, document, and package tests against that exact revision.
3. Preserve command outputs, versions, hashes, prompts, providers, and non-secret configuration.
4. Verify the published GitHub artifact and its checksums.
5. Deposit that exact release and evidence in an immutable Zenodo archive.
6. Record the real archive DOI in the data-and-materials statement.
7. Recompile and inspect the final PDF.
8. Submit the LaTeX sources if requested after acceptance.
9. Complete the journal's copyright and open-access licensing workflow.

No DOI, release, submission, acceptance, reviewer appointment, or editorial exception may be
claimed before it actually exists.

## Scientific Risks Rather Than Procedural Blockers

The following limitations do not automatically prevent initial submission because the manuscript
states them explicitly, but reviewers may require stronger evidence:

- the principal internal retrieval comparison uses a controlled regression fixture;
- no longitudinal user study has demonstrated improvement from feedback over time;
- model Judges have not been calibrated against independent human reviewers;
- BerryBrain and every baseline have not yet been executed on the same independent corpus and
  qrels;
- external service and hardware replication remains limited; and
- the evaluated worktree was not a clean frozen release.

The manuscript must retain bounded claims. It may present a functional, auditable research artifact
and exploratory evaluation, but must not claim universal superiority, calibrated factual
probability, autonomous model-weight learning, or field-proven longitudinal adaptation.

## Recommended Execution Order

1. Obtain and verify Leonardo Jose Silvestre's ORCID.
2. Obtain both authors' approval of authorship and CRediT roles.
3. Record Leonardo's explicit reviewer-commitment response.
4. Complete independent English review.
5. Verify reviewer conflicts and finalize the cover letter.
6. Both authors complete and approve `AUTHOR_CONFIRMATION_CHECKLIST.md`.
7. Freeze a clean revision and rerun essential validation.
8. Submit through OJS.
9. Create the software/evidence release and DOI before the final publication version claims it.

## Package References

- `AUTHOR_CONFIRMATION_CHECKLIST.md`
- `COVER_LETTER_DRAFT.md`
- `COAUTHOR_REVIEWER_CONFIRMATION.md`
- `JBCS_COMPLIANCE.md`
- `POTENTIAL_REVIEWERS.md`
- `SUBMISSION_METADATA.md`
- `AI_USE_DISCLOSURE.md`
- `EVIDENCE_AUDIT.md`
- `REFERENCE_AUDIT.md`
- `REPRODUCIBILITY.md`

## Official Sources

- JBCS submission instructions:
  <https://journals-sol.sbc.org.br/index.php/jbcs/about/submissions>
- JBCS editorial team and areas:
  <https://journals-sol.sbc.org.br/index.php/jbcs/about/editorialTeam>
- Author ORCID:
  <https://orcid.org/0009-0000-4701-1282>
