---
id: sciref-peer-review-tool-reference
name: "Scientific Ref: Local Tool Contracts"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (peer-review): Local Tool Contracts"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "peer review tool reference"
  - "peer revisao tool reference"
  - "local tool contracts"
keywords:
  - "peer"
  - "review"
  - "tool"
  - "reference"
  - "revisao"
  - "specialized"
  - "scientific"
  - "local"
---

# Local Tool Contracts

All bundled tools are deterministic Python 3.11+ standard-library CLIs. They make no network, model, image, subprocess, environment-variable, dynamic-code, or pickle calls.

## Shared safety behavior

- Inputs: local JSON, CSV, or Markdown only
- Maximum input size: 4 MiB
- Maximum CSV rows: 5,000
- UTF-8 only; NUL bytes rejected
- Symlink inputs and outputs rejected
- Duplicate JSON keys and CSV headers rejected
- Unknown schema fields rejected by JSON validators
- Existing outputs are not replaced unless `--force` is explicit
- JSON and Markdown outputs are written atomically with owner-only permissions where supported
- Reports contain IDs, counts, rule codes, and line numbers—not raw manuscript, review, claim, title, author, or reference prose

Exit codes:

- `0`: structurally valid or completed
- `1`: a validly parsed audit is blocked or has rule errors
- `2`: malformed input, unsafe path, unsupported field, or CLI validation error

Run tools from the skill directory or use absolute script paths.

## Intake validator

```bash
python3 scripts/validate_review_intake.py \
  assets/review_intake_template.json
```

Purpose:

- Confirm documented authorization and human accountability
- Record role, competence areas and limits, conflicts, target-venue policy, and review model
- Enforce local-only processing, no external service use, no data reuse, and a deletion/retention record
- Gate approved AI assistance on venue policy, permission, and disclosure

The bundled template is intentionally blocked until the human completes the controls.

Top-level JSON fields:

- `schema_version`: `2.0`
- `review_id`: safe local identifier, not a manuscript title
- `material`: status and sensitive-data flag
- `authorization`: basis and documented permissions
- `reviewer`: capacity, accountability, competence, and conflicts
- `venue_policy`: checked status, review model, confidential-note channel
- `ai_use`: policy, plan, permission, disclosure
- `handling`: local-only, external-service, reuse, retention controls
- `scope`: manuscript type, requested focus, limits, specialist needs

The report validates declarations, not their truth.

`reviewer.conflict_status` accepts `not_assessed`, `none_identified`, `disclosed_to_editor`, `editor_cleared`, or `unresolved`. Disclosure alone does not clear a conflict: `disclosed_to_editor` blocks until an editor actually clears participation. The validator cannot verify that clearance.

## Reporting-guideline selector and coverage audit

Selection only:

```bash
python3 scripts/select_reporting_guidelines.py \
  assets/study_profile_template.json
```

Selection plus coverage:

```bash
python3 scripts/select_reporting_guidelines.py \
  assets/study_profile_template.json \
  --coverage assets/reporting_checklist_template.csv
```

Profile fields:

- `schema_version`: `2.0`
- `profile_id`
- `study_types`: identifiers such as `randomized_trial`
- `report_kind`: `results`, `protocol`, `abstract`, or `data_release`
- `features`: for example `ai_based`, `ai_intervention`, `large_language_model`
- `domains`: for example `health`, `genomics`, `proteomics`

Coverage columns:

- `guideline_id`
- `item_id`: aggregate main item number for guidelines with a known main count
- `status`: `reported`, `partly_reported`, `not_reported`, `not_applicable`, `not_assessed`
- `location`: required for reported or partly reported items
- `rationale`: required for not-applicable items

The catalog is `assets/reporting_guidelines.json`, reviewed on the date embedded in that file; source-specific verification limits are in `assets/source_ledger.csv`. It does not fetch live updates. The output deliberately has no percentage or quality score.

For an AI trial protocol use `study_types: ["randomized_trial"]`, `report_kind: "protocol"`, `features: ["ai_intervention"]`, and `domains: ["health"]`; this selects SPIRIT 2025 and SPIRIT-AI 2020. For an LLM development, tuning, prompt-engineering, or evaluation study use `study_types: ["llm_study"]`, `report_kind: "results"`, `features: ["large_language_model"]`, and `domains: ["health"]`. Add `prediction_model` only if that design also applies. Abstracts have different checklists; the bundled catalog has no abstract checklist and a no-match result does not mean no guideline exists.

Main-item rows are an aggregate navigation record. `coverage_record_complete` means those row IDs are present, even if all are `not_assessed`; it does not certify coverage of subitems or a completed review.

## Claim–evidence matrix validator

```bash
python3 scripts/validate_claim_evidence.py \
  assets/claim_evidence_matrix_template.csv
```

Columns:

- `claim_id`
- `location`
- `claim_type`
- `claim_summary`: input-only; never echoed
- `evidence_ids`: semicolon-delimited local IDs
- `support_level`: `supported`, `partly_supported`, `unsupported`, `not_assessed`
- `alignment_issue`: direction, magnitude, population, outcome, timepoint, causal language, scope, uncertainty, selective reporting, other, or none
- `limitation`: input-only; never echoed
- `requested_action`: input-only; never echoed

Rules include:

- Supported claims need evidence IDs and no declared alignment issue.
- Partly supported claims require evidence and an issue code; a missing requested action is a warning that still needs human resolution.
- Unsupported claims need an issue code.
- Claim IDs must be unique.

The tool does not determine whether evidence is true or sufficient.

## Statistics and reproducibility checklist

```bash
python3 scripts/audit_statistics_reproducibility.py \
  assets/statistical_reproducibility_template.json
```

The JSON contains:

- Checklist and study-design IDs
- Specialist-review declaration
- Core item records with category, applicability, status, evidence locations, note, and requested action

Core areas:

- Question/estimand alignment
- Unit, independence, sample size, allocation, and blinding
- Inclusion/exclusion, missing data, and data handling
- Prespecification, method alignment, assumptions, multiplicity, and dependence
- Effect estimates, uncertainty, denominators, outcomes, and harms
- Data/material access, code/environment, and provenance
- Ethics/governance, claim interpretation, and selective reporting

The tool requires the core item IDs but permits additional safe IDs. It reports gaps and specialist-review triggers without a score.

## Citation/reference consistency audit

The Markdown must use Pandoc-style citation keys:

```mar

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

