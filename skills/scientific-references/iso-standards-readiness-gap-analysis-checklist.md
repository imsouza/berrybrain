---
id: sciref-iso-standards-readiness-gap-analysis-checklist
name: "Scientific Ref: Fail-Closed Evidence Review"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (iso-standards-readiness): Fail-Closed Evidence Review"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "iso standards readiness gap analysis checklist"
  - "iso standards readiness gap analise checklist"
  - "fail-closed evidence review"
keywords:
  - "iso"
  - "standards"
  - "readiness"
  - "gap"
  - "analysis"
  - "checklist"
  - "analise"
  - "specialized"
  - "scientific"
  - "reference"
  - "fail"
---

# Fail-Closed Evidence Review

Research basis: **2026-10-01**; current-source details are in `references/source-ledger.md`. This
checklist organizes evidence questions; it is not ISO or IEC text, an audit, an
assessment, a legal determination, or a compliance score.

Sections up to "Training, competence, and change control" apply to the device QMS lanes
(`iso-13485`, `iso-14971`). The laboratory sections near the end apply to `iso-17025`
and `iso-15189`. Use the sections your declared profile covers; do not report on a
domain you did not sample.

## Status vocabulary

Use only:

- `not-assessed` — no authorized decision was recorded;
- `evidence-missing` — applicable/expected evidence was not supplied;
- `evidence-incomplete` — evidence is draft, unapproved, unsourced, stale, or
  insufficiently linked;
- `evidence-present-for-human-review` — controlled evidence is available for
  substantive review; no adequacy claim;
- `not-applicable-approved` — an authorized person approved a documented rationale.

Never convert these states into a “compliance percentage.” Unequal, conditional,
product-specific, and jurisdiction-specific evidence cannot be responsibly reduced
to keyword counts.

## Required fields for every review item

| Field | Required content |
|---|---|
| Item ID | Stable unique identifier |
| Scope | Products, sites, processes, suppliers, systems, and period |
| Owner | Accountable role |
| Status | One value from the vocabulary above |
| Evidence | Controlled IDs, revisions/dates, and locations |
| Source/version | Official source, exact edition/version/date, access/currency review |
| Rationale | Evidence-based conclusion or approved not-applicable rationale |
| Action | Gap/change/CAPA ID, owner, due date, and status |
| Approval | Named authorized approver, decision, date, and record ID |

Blank, placeholder, inaccessible, stale, or unapproved fields fail closed.

## Workflow

1. Freeze the review purpose and boundaries: internal audit, ISO certification
   preparation, laboratory accreditation assessment preparation, FDA inspection
   preparation, national regulatory inspection preparation, MDSAP, or EU conformity
   assessment. One purpose per review.
2. Obtain authorized standards and current official regulatory sources.
3. Record product/site/market/activity scope; route applicability decisions to
   authorized management, RA/QA, and legal roles.
4. Build a controlled evidence manifest. Do not classify files from names alone.
5. Sample implementation records across time, products, sites, shifts, suppliers,
   and risk as justified.
6. Trace findings to risk, correction, CAPA, change, validation, training, and
   management review.
7. Preserve limitations and unresolved decisions in the report.
8. Obtain human approval. Do not issue a certification/readiness/compliance claim.

## Scope, roles, and source basis

- [ ] Legal entities, sites, products/families, lifecycle activities, outsourced
      processes, and markets considered are explicit.
- [ ] Authorized management representative, RA/QA owner, process owners, document/
      record owners, delegates, and escalation are documented.
- [ ] Independence and authority for audit, release, complaint/reportability,
      nonconformity disposition, CAPA closure, and change approval are defined.
- [ ] Each applicability or not-applicable decision cites current official
      source/version evidence and authorized approval.
- [ ] ISO, FDA, MDSAP, EU, and product-specific criteria are separately identified.
- [ ] External-source currency reviews and change-impact records are current.

## Document and record control

- [ ] Every controlled document has ID, title, revision, owner, status, approval,
      effective date, change rationale, controlled location, and training impact.
- [ ] Point-of-use control prevents unintended use of draft or obsolete documents.
- [ ] External standards, regulations, guidance, specifications, and customer/
      supplier documents have exact versions and currency-review ownership.
- [ ] Record creation, attribution, correction, integrity, security, audit trail,
      backup/recovery, retrieval, retention, legal hold, and disposition are controlled.
- [ ] Each retention period has an approved source/version and start-event rationale.
- [ ] Electronic systems and migrations preserve integrity and retrievability.
- [ ] Document changes link to affected risk, design, supplier, production,
      validation/software, postmarket, and training evidence.

## Risk management

- [ ] Product and process risk scope, responsibilities, methods, criteria, reviews,
      and records are approved.
- [ ] Intended use, reasonably foreseeable use, hazards/signals, evaluations,
      controls, verification, residual-risk decisions, and production/postmarket
      feedback are traceable.
- [ ] Risk controls link to design inputs/outputs, verification/validation,
      production controls, labeling/information, and acceptance evidence.
- [ ] Supplier, software, process, usability, cybersecurity, clinical/performance,
      and postmarket risks are considered where applicable.
- [ ] Complaints, trends, vigilance, CAPA, and changes update risk evidence.
- [ ] ISO 14971 and any EN A11 source are identified by exact edition and role.

## Design and development

- [ ] Authorized applicability decision covers the actual legal/lifecycle role.
- [ ] Plans define stages, responsibilities, interfaces, reviews, resources,
      verification, validation, transfer, and change controls.
- [ ] Inputs are approved, testable, traceable, and linked to risk and
      product/regulatory requirements.
- [ ] Outputs support production, suppliers, acceptance, service, labeling, and safe
      use as applicable.
- [ ] Reviews preserve participants, independence/competence, issues, decisions, and
      follow-up evidence.
- [ ] Verification and validation have approved protocols, objective criteria,
      representative configurations/samples, deviations, results, and approvals.
- [ ] Transfer and design changes include risk, validation, production, supplier,
      software, training, product-file, and postmarket impact evidence.

## Supplier and outsourced-process controls

- [ ] Supplier/product/process criticality has an approved risk basis.
- [ ] Selection, qualification, approval, and scope are evidenced.
- [ ] Purchasing information defines requirements, acceptance, records, change
      notification, and sub-tier flow-down as ap

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

