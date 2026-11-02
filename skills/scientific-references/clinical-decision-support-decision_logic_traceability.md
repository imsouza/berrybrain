---
id: sciref-clinical-decision-support-decision-logic-traceability
name: "Scientific Ref: Decision-Logic Traceability"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (clinical-decision-support): Decision-Logic Traceability"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "clinical decision support decision logic traceability"
  - "clinico decision support decision logic traceability"
  - "decision-logic traceability"
keywords:
  - "clinical"
  - "decision"
  - "support"
  - "logic"
  - "traceability"
  - "clinico"
  - "specialized"
  - "scientific"
  - "reference"
---

# Decision-Logic Traceability

## Scope

“Decision logic” here means research and governance logic only:

- evidence inclusion/exclusion;
- data-quality gates;
- validation acceptance criteria;
- release holds;
- documentation completeness;
- change-control approval;
- human-review checkpoints.

Do not encode diagnostic, treatment, dosing, triage, alarm, urgency, bedside, or patient-facing logic.

## Matrix Purpose

A traceability matrix links each rule to:

- its source and rationale;
- input/precondition;
- deterministic statement;
- bounded output kind;
- verification tests;
- owner and reviewer;
- version and status;
- known limitations and change history.

The matrix documents logic. It does not execute arbitrary expressions.

## Allowed Node Types

- `input_check`
- `data_quality_gate`
- `evidence_rule`
- `validation_gate`
- `documentation_gate`
- `human_review`
- `release_gate`
- `monitoring_gate`

Allowed output kinds:

- `include_evidence`
- `exclude_evidence`
- `flag_for_review`
- `validation_status`
- `documentation_status`
- `release_hold`
- `monitoring_status`

There is deliberately no generic “action” node.

## Required Fields

### Matrix Metadata

- logic ID and title;
- version/status/owner;
- research-only intended use;
- prohibited uses;
- data level;
- source ledger;
- human-review requirement;
- change summary;
- monitoring and retirement criteria.

### Per Node

- unique node ID;
- type;
- precondition/input;
- logic statement in plain language;
- output kind;
- output value;
- source IDs;
- rationale;
- validation tests;
- owner;
- reviewer role;
- status.

## Rule-Writing Guidance

Write rules so an independent reviewer can reproduce the result without hidden knowledge.

Good:

> If an evidence record lacks a stable citation and retrieval date, set output kind `flag_for_review` with value `missing_source_provenance`.

> If external validation is absent, set `release_hold` to `true` for claims of transportability.

Unsafe and prohibited:

> If a person's score is high, trigger an urgent alert.

> If a biomarker is positive, recommend a therapy.

## Validation Tests

For each node include:

- positive case;
- negative case;
- boundary case;
- missing/invalid input;
- source/version regression;
- expected output;
- reviewer and date.

For the matrix as a whole include:

- unreachable or orphan nodes;
- conflicting outputs;
- cycles;
- missing sources;
- stale versions;
- bypass paths around human review;
- rollback and retirement behavior.

The bundled helper validates identifiers, allowed node/output types, citations, and required review fields, then emits CSV. It does not parse or execute the logic statement. Invalid matrices produce diagnostics without CSV export; `--strict` also withholds export when review warnings remain.

## Change Control

For any change:

1. state the reason;
2. link new evidence or requirement;
3. identify affected nodes and downstream artifacts;
4. update tests;
5. independently validate;
6. record approval;
7. define rollout/rollback when applicable;
8. retain the previous version;
9. update monitoring;
10. retire superseded logic explicitly.

## Script

```bash
python3 scripts/decision_logic_traceability.py \
  assets/decision_logic_traceability_template.json
```

The output is a documentation matrix, not executable clinical logic.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

