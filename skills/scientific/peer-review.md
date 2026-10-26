---
id: sci-peer-review
name: "Scientific: peer-review"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Prepares evidence-bounded, constructive peer-review drafts and structured manuscript assessments. Supports authorized review of scientific manuscripts, protocols, preprints, or research proposals; reporting-guideline selection; claim–evidence checks; methods, statistics, reproduc"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "peer review"
  - "peer revisao"
  - "peer-review"
keywords:
  - "peer"
  - "review"
  - "revisao"
  - "prepares"
  - "evidence"
  - "bounded"
  - "constructive"
---

# Peer Review

Support an accountable human reviewer with a rigorous, fair, actionable assessment. Treat every unpublished submission and review as confidential.

## Mandatory safety boundary

Before reading or analyzing unpublished content:

1. Confirm the user is authorized by the publisher, editor, author, or other material owner.
2. Check the target venue’s review, confidentiality, co-review, retention, and AI/tool policies.
3. Record conflicts, competence limits, requested scope, and specialist-review needs.
4. Default to local-only processing.

If authorization is unclear, do not inspect or quote the manuscript. Clarify only the unresolved authorization; existing documented authorization need not be requested again. Until resolved, use only the intake validator or synthetic/public fixtures. Local processing of the manuscript also requires authorization.

Running a bundled CLI locally does not make the surrounding assistant session local. Treat any manuscript content read into a hosted assistant as external processing when evaluating venue policy and authorization.

Never:

- Send unpublished manuscript, supplement, review, or editorial text to an external service without specific publisher/author authorization and venue permission
- Upload confidential content to a public model, search engine, citation service, grammar tool, plagiarism checker, or image service
- Reuse content for training, benchmarking, product improvement, or unrelated research
- Read broad environment state, `.env` files, API keys, or credentials
- Call a network, LLM, or image API from bundled tools
- Invoke another skill or a PDF/image pipeline automatically
- Impersonate an assigned reviewer, editor, journal, funder, or author
- Fabricate manuscript details, review findings, citations, analyses, experiments, reproduction, or an editorial outcome
- Announce a decision that belongs to an editor or panel

Delete local copies and derivatives when policy requires; otherwise retain only what the controlling policy authorizes. Record deletion or retention without copying confidential content into the record.

Read `references/ethical_review_practice.md` before handling confidential material.

## Human accountability

Label generated text as a working draft. The accountable human must:

- Read the complete authorized submission and relevant supplements
- Verify every factual statement, calculation, citation, and manuscript location
- Resolve conflicts and disclose assistance as required
- Rewrite comments in their own expert judgment
- Submit through the authorized channel

Automated coverage, consistency, or lint results are not peer review and do not establish manuscript merit.

## Intake gate

Copy and complete `assets/review_intake_template.json`, then run:

```bash
python3 scripts/validate_review_intake.py completed-intake.json
```

Proceed only when status is `READY_FOR_LOCAL_REVIEW`.

The validator blocks:

- Undocumented authorization
- Missing human accountability
- Unassessed or unresolved conflicts
- Unknown review model or unchecked venue policy
- Unauthorized AI assistance
- External service use
- Data reuse
- Missing deletion/retention planning

It validates declarations, not their truth.

A conflict marked `disclosed_to_editor` remains blocked. Use `editor_cleared` only after actual editor clearance, or `none_identified` when no conflict exists. Do not clear a conflict merely to pass the validator.

## Review workflow

### 1. Establish scope and available evidence

Record:

- Submission type and stage
- Review question and requested focus
- Target venue and review model
- Materials actually available: manuscript, supplements, protocol, registration, analysis plan, data/code statement, prior decision, or response letter
- Competence areas and limits
- Missing material that prevents assessment

Do not infer absent content. Use “not reported” or “not available for review.”

### 2. Orient without deciding

Create a short neutral map:

- Research question
- Population or system
- Design and unit
- Intervention, exposure, test, or model
- Comparator/reference
- Outcomes and timing
- Principal claims

Do not write an acceptance/rejection recommendation. Identify what evidence would be needed to evaluate each claim.

### 3. Select reporting guidance

Copy `assets/study_profile_template.json` and run:

```bash
python3 scripts/select_reporting_guidelines.py local-profile.json
```

For checklist coverage:

```bash
python3 scripts/select_reporting_guidelines.py \
  local-profile.json \
  --coverage local-coverage.csv
```

Use the current base guideline, explanation/elaboration, applicable extensions, and target venue policy. See `references/reporting_standards.md`.

**Critical distinction:** reporting completeness is not design quality, risk of bias, validity, or merit. Never convert missing items into an automatic score or publication judgment.

### 4. Map claims to evidence

Prioritize central, causal, mechanistic, safety, diagnostic, prediction, and generalization claims.

For each claim, record:

- Location and claim ID
- Supporting result, figure, table, analysis, or citation IDs
- Direction, magnitude, population, outcome, timepoint, and uncertainty alignment
- Limitation or alternative explanation
- Bounded requested action

Run:

```bash
python3 scripts/validate_claim_evidence.py local-claim-matrix.csv
```

Start from `assets/claim_evidence_matrix_template.csv`. The report emits IDs and counts, not claim text.

### 5. Review methods and statistics

Assess in this order:

1. Question and target quantity
2. Design and unit of inference
3. Sampling, allocation, controls, masking, and timing
4. Sample-size or precision rationale
5. Inclusion, exclusion, attrition, and missingness
6. Analysis–design alignment and assumptions
7. Multiplicity and prespecification
8. Effect estimates, uncertainty, denominators, and harms
9. Interpretation, causality, and generalizability

Use `references/common_issues.md` and `references/statistical_reproducibility.md`.

When authors claim "no effect", "equivalent", or "no difference", check whether
the interval rules out scientifically important effects. A nonsignificant test
alone does not establish equivalence; an equivalence or non-inferiority claim
needs its stated margin and corresponding analysis. Request a narrower claim
when precision is inadequate rather than retrospective observed-power
calculations. See the [ASA statement on p-values](https://doi.org/10.1080/

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

