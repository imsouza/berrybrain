---
id: sci-clinical-decision-support
name: "Scientific: clinical-decision-support"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Prepares and validates research-only clinical decision-support evaluation, evidence-profile, cohort, survival, biomarker/model, privacy, and governance artifacts. Supports aggregate or synthetic research documentation and traceability, excluding patient care and live clinical ope"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "clinical decision support"
  - "clinico decision support"
  - "clinical-decision-support"
keywords:
  - "clinical"
  - "decision"
  - "support"
  - "clinico"
  - "prepares"
  - "validates"
  - "research"
  - "only"
---

# Clinical Decision-Support Research and Evaluation

## Hard Safety Boundary

This skill produces **research, evaluation, documentation, and governance artifacts only**.

Never use it to:

- diagnose or classify a person;
- recommend, select, sequence, start, stop, or modify treatment;
- calculate or communicate a patient-specific dose;
- triage, prioritize, alarm, alert, or determine urgency;
- make or automate a patient-specific clinical decision;
- support bedside, point-of-care, or live clinical operation;
- replace professional judgment or a validated, authorized clinical system;
- claim FDA authorization, regulatory conformity, HIPAA compliance, or legal compliance.

If a request could affect care for a person, stop the workflow and route the matter to a licensed healthcare professional using locally validated and appropriately authorized systems. Do not redirect to another skill for patient-specific care.

## In Scope

- Intended-use and limitation statements for research artifacts
- Aggregate cohort table shells with disclosure controls
- Statistical analysis plans and survival-analysis plan review
- Aggregate model or biomarker performance evaluation
- Transparent GRADE evidence-profile checklists
- Evidence-source and decision-logic traceability
- De-identification process checklists
- Fairness, subgroup, calibration, uncertainty, external-validation, monitoring, change-control, audit, and human-factors documentation

Outputs remain drafts until qualified humans approve them. Reporting guidance improves transparency; it does not establish study quality, clinical utility, safety, effectiveness, authorization, or compliance.

## Data Gate

Before any script:

1. Have the responsible human reviewer confirm and document that input is synthetic or aggregate. Scripts cannot establish this from field names or declared metadata.
2. Reject patient rows, records, narratives, identifiers, free text, dates tied to people, images, waveforms, or genomic sequences.
3. Keep source files local. Do not fetch URLs, call APIs, read environment variables, or send data to a model.
4. Set disclosure thresholds before producing tables.
5. Record provenance, data cut date, population, exclusions, missingness, and transformations.

The scripts cap file size, groups, rows, and text length. They reject URL-like paths and common row-level keys. These controls reduce accidental misuse; they are not a privacy determination.

## Required Artifact Header

Every artifact must visibly include:

- `artifact_type`, title, version, status, owner, date, and change summary;
- intended purpose, intended users, aggregate population scope, and decision role;
- all prohibited uses from the hard boundary;
- data level and confirmation that no PHI or raw rows were supplied;
- limitations, uncertainty, and foreseeable failure modes;
- external-validation and subgroup applicability status;
- human-review roles, completion status, and approval boundary;
- source citations with versions or dates;
- monitoring, change-control, retirement, and audit expectations;
- the statement: **Not for patient care or live clinical use.**

Start from `assets/artifact_intended_use_template.json`.

## Workflow

### 1. Frame the Research Question

- Define the estimand or evaluation target before viewing results.
- Distinguish descriptive, prognostic, predictive, diagnostic-accuracy, and causal questions.
- Pre-specify outcomes, time origin, horizon, subgroups, cut points, missing-data handling, multiplicity, and sensitivity analyses.
- Separate exploratory findings from confirmatory analyses.

### 2. Select the Artifact

| Need | Asset | Script |
|---|---|---|
| Intended-use/governance review | `assets/artifact_intended_use_template.json` | `scripts/validate_cds_artifact.py` |
| GRADE evidence profile | `assets/evidence_profile_template.json` | `scripts/evidence_profile_check.py` |
| Aggregate model/biomarker evaluation | `assets/aggregate_model_evaluation_template.json` | `scripts/model_biomarker_evaluation.py` |
| Aggregate cohort table | `assets/aggregate_cohort_table_template.json` | `scripts/cohort_table_generator.py` |
| Survival analysis plan | `assets/survival_analysis_plan_template.json` | `scripts/survival_plan_validator.py` |
| Logic traceability matrix | `assets/decision_logic_traceability_template.json` | `scripts/decision_logic_traceability.py` |
| De-identification process review | `assets/deidentification_checklist_template.json` | `scripts/deidentification_checklist.py` |

### 3. Run Locally

All helpers are dependency-free. Run the following commands from the skill directory:

```bash
python3 scripts/validate_cds_artifact.py --help
python3 scripts/evidence_profile_check.py --help
python3 scripts/model_biomarker_evaluation.py --help
python3 scripts/cohort_table_generator.py --help
python3 scripts/survival_plan_validator.py --help
python3 scripts/decision_logic_traceability.py --help
python3 scripts/deidentification_checklist.py --help
```

Write outputs only to a reviewed local directory. Never place generated reports in an EHR, alerting system, clinical portal, or device workflow.

### 4. Human Review

Require review proportionate to the artifact:

- methodologist/statistician for design and analysis;
- domain expert for clinical-scientific context;
- privacy officer or qualified expert for disclosure decisions;
- regulatory or legal counsel for jurisdiction-specific interpretations;
- human-factors specialist for user studies;
- authorized governance owner for release and change control.

Script success means only that declared fields and internal consistency checks passed.

## GRADE Evidence Profiles

Do not infer a certainty rating from article text, study design alone, p-values, or keywords. Do not use the legacy `1A/2B` shorthand as if it were universal GRADE output.

For each important outcome, a human panel must document:

- risk of bias;
- inconsistency;
- indirectness;
- imprecision;
- dissemination/publication bias;
- any applicable upgrading considerations;
- effect estimate and uncertainty;
- rationale and source IDs for every judgment;
- final certainty judgment and named review role.

The checker validates completeness and citation links only. It never calculates certainty or recommendation strength. See `references/evidence_profiles.md`.

## Aggregate Model and Biomarker Evaluation

Do not derive thresholds, assign molecular or disease classes, match therapies, or emit person-level predictions.

The e

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

