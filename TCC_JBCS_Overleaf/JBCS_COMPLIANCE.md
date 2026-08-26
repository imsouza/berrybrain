# JBCS Compliance Report

Checked on August 25, 2026 against the official submission page of the *Journal of the Brazilian
Computer Society* (JBCS) and the journal-provided template.

## Result

The project uses the official sbc2023 class, the apalike-sol bibliography style, XeLaTeX, and an
English manuscript. It is structurally aligned with the JBCS template. The first author's ORCID,
the two-author CRediT statement, target area, AI-use disclosure, submission metadata, and draft
correspondence are recorded. It is **not authorized for submission** until the non-delegable gates
below are resolved.

## Submission blockers

1. **Second-author ORCID:** JBCS requires an ORCID for every author. Leonardo Jose Silvestre's
   identifier was not found reliably and must be supplied and verified; no identifier is inferred.
2. **Author-reviewer consent:** JBCS asks one author to review up to two papers and expects the
   volunteer to hold a PhD or equivalent degree. Leonardo Jose Silvestre has a relevant PhD, but
   must explicitly accept the commitment before it is entered in OJS.
3. **Author-only attestations:** originality, absence of simultaneous submission, complete funding
   and conflict disclosure, permissions, contributions, reviewer conflicts, and approval must be
   personally confirmed by both authors in `AUTHOR_CONFIRMATION_CHECKLIST.md`.
4. **DOI-bearing deposit:** the exact GitHub research artifact is versioned, but that release must
   still be deposited in Zenodo. No DOI is claimed until the public record exists and is verified.
5. **Independent language review:** automated checks do not constitute independent human or
   professional English review. Complete a final read-through after all substantive edits.

Current results remain exploratory. This does not make them fabricated, but it limits the claims:
general superiority requires same-corpus baselines, human judge calibration, and longitudinal user
evidence.

## Editorial checklist

| Current rule | Status | Evidence or action |
| --- | --- | --- |
| PDF uses the JBCS template | Met | main.tex uses sbc2023 |
| Template header conditional | Corrected | supplied class omitted the false branch of ifdefempty |
| Keyword rule scope | Corrected | supplied class leaked right skip into the full-width rule |
| XeLaTeX compilation | Met | process documented in README_OVERLEAF.md |
| Manuscript in English | Met | English-only audit passed for title, abstract, body, tables, declarations, and package documentation |
| Single-blind review | Met | authors and affiliations are visible |
| ORCID for each author | **Blocked** | Mateus's ORCID is verified and linked; Leonardo's author-supplied ORCID remains pending |
| Authorship | Corrected | Mateus Almeida de Souza is first and corresponding author; Leonardo Jose Silvestre is second author and supervisor |
| Internal student identifier | Met | registration number is excluded from the article package |
| Original and not simultaneously submitted | Declaration pending | confirm in the portal |
| DOI supplied when available | Met for cited set | 28 DOI entries match Crossref/DataCite; 17 official or stable URLs resolve; see `REFERENCE_AUDIT.md` |
| Ethics addressed | Met | ethics scope and absence of participants stated |
| Author contributions | Drafted, approval pending | two-author CRediT role statement included; both authors must confirm it |
| Competing interests | Met | explicit declaration included |
| Acknowledgements | Met | explicit declaration included |
| Funding | Author attestation pending | manuscript reports no specific external funding; both authors must personally confirm completeness |
| Data and materials | Partial | immutable GitHub artifact identified; DOI-bearing Zenodo archive remains pending |
| Generative AI disclosure | Met | software engineering, automated-test design, research and writing assistance, verification, and responsibility are disclosed |
| Reproducible code and data | Met with stated limits | public GitHub snapshot contains scripts, fixtures, protocols, and retained evidence; personal vault data are excluded |
| Cover letter | Prepared, not authorized | `COVER_LETTER_DRAFT.md`; both authors' attestations, ORCID completion, and reviewer consent remain required |
| JBCS area | Met | Information Retrieval, matching the current OJS category list |
| Suggested reviewers | Researched, not nominated | two real institutional profiles recorded; author conflict checks remain required |
| Author-reviewer commitment | Pending explicit consent | Leonardo holds a relevant PhD and may be entered only after he agrees to review up to two papers |
| Submission metadata | Met | `SUBMISSION_METADATA.md` |
| Live package tests | Met | eleven tests pass, including two-author metadata, official ORCID API, current JBCS policy, PDF hash, and institutional-profile checks |
| Float order | Met | Tables 1-12 are monotonic; result tables remain beside their analyses; Maturity is uninterrupted; Table 12 precedes References |

## Length

The current official instructions reviewed do not publish an explicit page or word limit for
regular articles. No limit was invented. The validated English PDF contains **11 pages**. Lack of
a formal limit does not remove the requirement for concise, coherent, and scientifically useful
writing.

## Review and submission rules

- Submission is a PDF in the mandatory JBCS template; off-template manuscripts may be desk rejected.
- JBCS articles must be written in English and are reviewed single-blind.
- The journal assesses scientific validity, coherence, and a useful computing contribution.
- The process generally involves three reviewers.
- The manuscript must not be published or under simultaneous evaluation elsewhere.
- A conference extension must add non-trivial conceptual material. The official guidance uses
  approximately 30% as a practical reference and requires an explanation in the cover letter.
- At least one author commits to reviewing up to two papers. A suggested reviewer should have a
  PhD or equivalent qualification, full name, expertise, institutional email, and affiliation.
- The cover letter should explain JBCS fit, area, policy issues, conflicts, special issue status,
  relationship to earlier work, and reviewer suggestions.
- Accepted manuscripts require LaTeX source files.
- JBCS is diamond open access: no author or reader fee, under CC BY 4.0.

## Required work before publication

1. Run BM25, dense, hybrid, vanilla RAG, GraphRAG, and BerryBrain on the same corpus and qrels.
2. Add a blinded annotated corpus rather than relying only on deterministic fixtures.
3. Calibrate model judges against human reviewers and report kappa and critical error rates.
4. Run user studies only under the applicable ethics protocol.
5. Repeat performance on reference hardware with separate cold and warm cache results.
6. Preregister power, hypotheses, exclusions, and non-inferiority margin.
7. Perform an independent final English review.
8. Freeze and deposit the exact release, then add its DOI without changing the archived evidence.
9. Obtain and verify Leonardo Jose Silvestre's ORCID.
10. Obtain Leonardo's explicit consent to the author-reviewer commitment.
11. Both authors complete and approve `AUTHOR_CONFIRMATION_CHECKLIST.md`.

## Completed Publication Procedures

- The first author's ORCID checksum and public identity were validated through the official ORCID
  Public API and linked in the manuscript.
- The CRediT statement uses recognized role names and identifies both confirmed authors.
- The generative-AI disclosure explicitly includes software engineering and automated-test design.
- Submission metadata, the JBCS area, a bounded cover-letter draft, an author-only checklist, and
  author-reviewer consent guidance are included.
- Potential reviewer research uses current institutional profiles and does not claim nomination or
  absence of conflicts.
- `tests/submission-package.test.mjs` validates the actual manuscript, bibliography, declarations,
  PDF and hash, ORCID record, live JBCS policy page, and institutional reviewer profiles. It uses no
  mock server, fabricated registry response, or hardcoded pass result.

## Official sources

- Submissions: <https://journals-sol.sbc.org.br/index.php/jbcs/about/submissions>
- Journal portal: <https://journals-sol.sbc.org.br/index.php/jbcs/>
- Official template: <https://www.overleaf.com/read/sgfkmgfqzbdz>
- SBC publication conduct code:
  <https://www.sbc.org.br/wp-content/uploads/2024/07/Codigo_Conduta_para_Publicacoes_da_SBC.pdf>
- JBCS 2025 report:
  <https://www.sbc.org.br/jbcs-tem-recorde-de-submissoes-e-publicacoes-em-2025/>
- UFES Department of Computing and Electronics staff directory:
  <https://computacao.saomateus.ufes.br/docente>
