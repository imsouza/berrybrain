---
id: sciref-treatment-plans-documentation-workflow
name: "Scientific Ref: Documentation Package Workflow"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (treatment-plans): Documentation Package Workflow"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "treatment plans documentation workflow"
  - "documentation package workflow"
keywords:
  - "treatment"
  - "plans"
  - "documentation"
  - "workflow"
  - "specialized"
  - "scientific"
  - "reference"
---

# Documentation Package Workflow

Last reviewed: **2026-10-01**

## Package contract

A complete package contains exactly one JSON object for each document type:

- `source_fact_manifest`
- `clinician_authored_intervention_record`
- `goals_monitoring_checkpoint_record`
- `informed_preference_shared_decision_record`
- `transition_reconciliation_record`
- `intended_use_handoff_record`

All six must use schema version `2.0` and the same `subject_ref`, `data_classification`, draft status, and notice.

## 1. Intended-use gate

Complete the intended-use/handoff record first:

- purpose and authorized users;
- local setting and accountable roles;
- prohibited-use list;
- privacy and processing attestations;
- local policy, retention, change-control, and reporting routes;
- local emergency-process reference;
- handoff sender, recipient, and acknowledgment;
- clinician sign-off and documentation-handoff release gate.

Do not remove prohibited uses. The generator restores the complete list in every new package.

## 2. Source-fact manifest

Every clinical or process statement used elsewhere must have a source fact. A fact records:

- a stable fact ID;
- fact kind;
- the exact bounded statement supplied;
- source type, title, local locator, and version/date;
- verification status, verifier role, and time;
- applicability status when an official source or policy is involved.

Allowed source categories distinguish signed local records, authorized EHR records, current FDA labeling, current REMS materials, current official guidance, and local policy.

The manifest does not decide which source applies. An authorized professional must confirm applicability.

## 3. Clinician-authored interventions

Each intervention record must:

- state that the decision was supplied and verified by an authorized licensed professional;
- preserve the clinician-authored action without rewriting it into a recommendation;
- link to at least one verified source fact;
- record parameters only as supplied;
- identify the responsible role;
- preserve explicit start/end dates when supplied;
- include verifier role and time.

The validator checks structure and provenance only. It does not parse or judge a medication, procedure, therapy, device, referral, or instruction.

## 4. Goals, monitoring, and checkpoints

Separate:

- goals — statement, measurement, target, target date, and source facts;
- monitoring items — item, method, supplied frequency text, explicit next due date, owner, and source facts;
- checkpoints — exact supplied date, purpose, owner, linked records, and source facts.

Do not convert a narrative frequency into dates. Do not infer a checkpoint from a target, medication, intervention type, standard interval, or prior appointment.

## 5. Informed preferences and shared decisions

Record only what the authorized clinician documented:

- decision topic;
- options actually presented;
- whether benefits, harms, and uncertainty were documented;
- the person's stated preference;
- the clinician-documented outcome;
- participant and author roles;
- source facts, time, and acknowledgment status.

Do not generate missing options, risk estimates, benefit claims, alternatives, or consent language.

## 6. Transition and reconciliation

Record:

- sending and receiving settings and roles;
- exact handoff date;
- medication-reconciliation status;
- source and destination list fact references;
- discrepancy status and authorized reviewer;
- handoff items, owners, recipients, and acknowledgment;
- unresolved items and their local route.

`completed_by_authorized_clinician` is a declaration to be verified against the local record. The script does not perform reconciliation.

## 7. Deterministic checks

Run in this order:

```bash
python3 scripts/validate_treatment_plan.py PACKAGE_DIRECTORY
python3 scripts/validate_traceability.py PACKAGE_DIRECTORY
python3 scripts/check_completeness.py PACKAGE_DIRECTORY
python3 scripts/privacy_process_check.py PACKAGE_DIRECTORY
python3 scripts/check_consistency.py PACKAGE_DIRECTORY
python3 scripts/timeline_generator.py PACKAGE_DIRECTORY --output SCHEDULE.json
```

Run these commands from the skill directory. New empty templates pass structural validation but intentionally fail completeness and schedule generation until supplied records and dates exist.

The checks answer different questions:

- structural validator — are document types, fields, types, enums, bounds, and dates valid?
- traceability validator — do all clinical/process records point to existing verified facts?
- completeness checker — are required records, reviews, routes, acknowledgments, sign-off, and release declarations complete?
- privacy/process checker — are local authorization, minimization, external-tool prohibition, qualified review, retention, and direct-identifier safeguards documented?
- consistency checker — do package IDs, statuses, classifications, references, and explicit date order agree?
- timeline generator — after structural and cross-record consistency checks, what events occur on dates already supplied?

Run every check again after any change. A pass evaluates declarations, not their authenticity. The completeness output is `documentation_declarations_complete`; `handoff_authorized_by_script` is always false. The fixed completeness profile requires at least one intervention, goal, monitoring item, checkpoint, shared-decision entry, and handoff item. These are package constraints, not universal care requirements. If the supplied workflow does not have such records, leave it blocked and retain the authorized source workflow; never invent care or consent documentation merely to pass.

Dates use full `YYYY-MM-DD` form. Timestamps use `YYYY-MM-DDTHH:MM:SS`, optional 1-6 fractional digits, and `Z` or `±HH:MM`. A schedule keeps the calendar date in the supplied offset, without converting timezones. It omits clinical text and subject IDs but is still sensitive when derived from patient data.

## 8. Minimized issue handling

Reports use known field paths, not values; unknown field names and unrecognized document-type values are suppressed. For example, a report may identify `interventions[0].verification.status` without printing the action text.

Resolve each issue in the authoritative local record:

1. Locate the field path.
2. Compare with the signed source.
3. Ask the responsible authorized role to supply or verify the missing value.
4. Update provenance.
5. Re-run all checks.

Never correct clinical content 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

