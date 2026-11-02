---
id: sciref-hypothesis-generation-tool-reference
name: "Scientific Ref: Local Tool Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (hypothesis-generation): Local Tool Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "hypothesis generation tool reference"
  - "hipotese generation tool reference"
  - "local tool reference"
keywords:
  - "hypothesis"
  - "generation"
  - "tool"
  - "reference"
  - "hipotese"
  - "specialized"
  - "scientific"
  - "local"
---

# Local Tool Reference

## Runtime and safety model

All bundled CLIs:

- require Python 3.11+ standard library only;
- read explicit local JSON, CSV, or Markdown paths;
- reject URL-like paths, symlinks, wrong suffixes, oversized inputs, invalid UTF-8, and NUL bytes;
- cap inputs at 2 MiB, CSV data at 1,000 rows, cells/Markdown lines at 8,000 characters, and JSON collections at bounded sizes;
- reject duplicate JSON keys, nonstandard `NaN`/`Infinity` constants, and JSON nesting beyond 64 container levels; require exact ordered CSV headers;
- require full dates in `YYYY-MM-DD` calendar form; Python's accepted compact and ISO-week forms are not accepted by this schema;
- make no network, model, image, subprocess, credential, or environment-variable calls;
- write only to an explicit existing local directory;
- refuse implicit overwrite unless `--force` is given;
- use private mode (`0600`) and atomic replacement for generated output.

Reports contain identifiers, counts, rule codes, and line numbers rather than copying scientific prose where practical.

## Exit codes

- `0`: input was structurally valid; warnings or human-review gaps may remain.
- `1`: input was parsed, but consistency or required-control errors were found.
- `2`: malformed, unsafe, missing, oversized, or wrong-type input.

No exit code means a hypothesis is true, novel, ethical, safe, feasible, supported, or selected.

## 1. Hypothesis schema validator

Asset: `assets/hypothesis_record_template.json`

```bash
python3 scripts/validate_hypothesis_schema.py local-record.json
python3 scripts/validate_hypothesis_schema.py \
  local-record.json -o local-validation.json
```

The exact top-level objects are:

- observation;
- research question;
- hypotheses;
- causal estimands;
- predictions;
- alternative explanations;
- null hypotheses;
- negative controls;
- operationalizations;
- analysis plan;
- evidence/search link;
- causal-bias risk register;
- ethics/feasibility gates;
- AI-use record.

All hypothesis statuses must be `candidate`. Causal questions require at least one estimand. Cross-links among candidate, prediction, rival, measurement, analysis, control, and source IDs are checked.

The validator does not read the evidence ledger, test measurements, appraise sources, or interpret results.

## 2. Operationalization and measurement checklist

Asset: `assets/operationalization_template.json`

```bash
python3 scripts/check_operationalization.py local-operationalization.json
```

Each measurement item records:

- construct, operational definition, population/system, unit/categories, timing, and method completion;
- variable role;
- validity source IDs and applicability review;
- reliability/repeatability;
- calibration/quality control;
- invariance/comparability;
- masking;
- missingness;
- threshold/cut-point status;
- limitations and human review.

`planned`, `unresolved`, and `pending` states are reported as gaps, not converted to scores. A checklist cannot establish measurement validity.

## 3. Prediction/rival matrix validator

Asset: `assets/prediction_rival_matrix_template.csv`

Exact header:

```text
prediction_id,hypothesis_id,rival_hypothesis_ids,conditions,observable,expected_if_focal,expected_if_rivals,falsifier,indeterminate_result,boundary_conditions,measurement_ids,negative_control_ids,analysis_ids,uncertainty
```

Use semicolons inside ID-list cells:

```bash
python3 scripts/validate_prediction_matrix.py local-matrix.csv
python3 scripts/validate_prediction_matrix.py \
  local-matrix.csv --record local-record.json
```

Checks include:

- unique prediction IDs;
- focal candidate not listed as its own rival;
- declared focal and rival expectations are not lexically identical;
- required falsifier, indeterminate result, boundary, measurement, control, analysis, and uncertainty fields;
- optional cross-links to the hypothesis record.

The validator cannot determine whether two predictions are scientifically distinguishable.

## 4. Causal-versus-associational Markdown lint

```bash
python3 scripts/lint_causal_claims.py local-draft.md
```

Use one claim per annotated line:

```markdown
[claim:associational] Exposure X was associated with outcome Y in the observed sample.

[claim:causal][estimand:E1][identification:observational_assumption_dependent][confounding:unresolved][selection:assessed][collider:assessed][reverse-causation:assessed] Under the stated assumptions, intervention X would reduce outcome Y.
```

Claim types:

- `causal`
- `associational`
- `descriptive`
- `predictive`
- `mechanistic`

Identification values:

- `randomized`
- `quasi_experimental`
- `observational_assumption_dependent`
- `mechanistic_experiment`
- `other_assumption_dependent`

Risk values:

- `assessed`
- `unresolved`
- `not_applicable`

The linter flags a bounded causal lexicon and annotation consistency. It is not a semantic classifier and will have false positives and false negatives.

## 5. Falsification and negative-control checklist

Asset: `assets/falsification_controls_template.json`

```bash
python3 scripts/check_falsification_controls.py local-controls.json
python3 scripts/check_falsification_controls.py \
  local-controls.json --record local-record.json
```

For each candidate it requires:

- assumptions and boundary conditions;
- a prediction-linked falsifier and assumption-failure checks;
- at least one discriminating test with focal, rival, and indeterminate outcomes;
- a linked null and interpretation limit;
- controls including at least one negative-control type;
- outcome paths for consistency, challenge, and neither/mixed;
- human-review status.

The checker does not validate that a negative control is biologically or causally appropriate.

## 6. Evidence ledger and search-boundary audit

Assets:

- `assets/evidence_ledger_template.csv`
- `assets/search_boundary_template.json`

Exact evidence-ledger header:

```text
source_id,claim_ids,title,authors_or_organization,publication_date,source_type,identifier,url,accessed_on,relation,study_design_or_document_type,limitations,notes
```

```bash
python3 scripts/audit_evidence_ledger.py \
  local-evidence.csv local-search-boundary.json

python3 scripts/audit_evidence_ledger.py \
  local-evidence.csv local-search-boundary.json \
  --record local-record.json
```

The audit checks:

- exact schema and date/HTTPS/identifier formats;
- unique source IDs;
- source-to-claim links;
- source-type and relation declarations;
- dated search boundary, queries, limits, stop rul

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

