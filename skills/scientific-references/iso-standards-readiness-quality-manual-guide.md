---
id: sciref-iso-standards-readiness-quality-manual-guide
name: "Scientific Ref: Quality Manual Development Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (iso-standards-readiness): Quality Manual Development Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "iso standards readiness quality manual guide"
  - "quality manual development guide"
keywords:
  - "iso"
  - "standards"
  - "readiness"
  - "quality"
  - "manual"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
---

# Quality Manual Development Guide

Research basis: **2026-10-01**; current-source details are in `references/source-ledger.md`. This guide
explains an evidence-controlled authoring process. It does not reproduce standard text
or prescribe a universal manual format.

The authoring process applies to any management-system documentation this skill covers.
Where it says "QMS scope," a laboratory's equivalent is the **scope of laboratory
activities** — per location and per method or examination — and a laboratory manual
should point to the accredited scope schedule rather than restate it. Read
`references/iso-17025.md` or `references/iso-15189.md` alongside this guide.

## Boundary and copyright

A quality manual template cannot establish an effective QMS, conformity,
certification, FDA compliance, MDSAP acceptance, EU conformity, or legal
applicability. It cannot replace authorized management, RA/QA, legal, notified-body,
regulatory-authority, MDSAP Auditing Organization, or certification-body decisions.

ISO publications are copyrighted. Obtain ISO 13485 from
[ISO](https://www.iso.org/standard/59752.html), a national member, or an authorized
source. Do not paste standard text into the manual. Summarize the organization's
actual processes and reference its controlled authorized copy.

## Purpose of a manual

A useful manual or equivalent policy architecture:

- identifies the approved QMS scope;
- identifies controlled processes and their interactions;
- states governance, authorities, and responsibilities;
- explains the documentation/evidence hierarchy;
- points to organization-specific controlled procedures and records; and
- distinguishes the applicable standard, regulatory, audit, and product sources.

The manual should be the length and structure needed for the organization. Page count,
a fixed procedure list, or mirroring standard headings does not prove adequacy.

## Development workflow

### 1. Establish an authorized source baseline

Create a controlled source ledger before drafting. At minimum record:

- ISO 13485:2016, Edition 3, and authorized location;
- the applicable EN adoption/amendment/corrigendum if European harmonisation is
  being used;
- current FDA QMSR/eCFR sources if U.S. operations are in declared scope;
- current MDSAP Audit Approach if MDSAP is in declared scope;
- current consolidated MDR or IVDR, OJEU harmonised-standard decisions, and relevant
  MDCG guidance if EU work is in declared scope;
- ISO 14971/EN A11 and product-specific standards where applicable; and
- current product/jurisdictional regulations and guidance.

For each source, capture publisher, title, edition/version/date, official URL or
authorized location, access date, owner, currency-review date, impact assessment,
status, and approval.

### 2. Freeze purpose and scope

Record:

- legal entities and sites;
- product types/families and controlled intended-use references;
- lifecycle activities performed at each site;
- outsourced processes and interfaces;
- markets being considered;
- organizational and physical boundaries;
- assurance purpose (ISO certification, FDA, MDSAP, EU, internal); and
- limitations and unresolved applicability decisions.

Do not let an agent decide applicability. `Undetermined` remains a blocker until an
authorized human approves a decision and rationale.

### 3. Map actual process interactions

Interview accountable process owners and inspect actual records. Build a process map
from the organization's work—not from copied standard headings.

For each process record:

- inputs and outputs;
- owner, authority, delegate, and escalation;
- controlled procedure/system;
- implementation records;
- interfaces to risk and change control;
- measures and review method;
- source/version basis;
- status and approval.

Include management, support, product lifecycle, assurance, feedback, and improvement
processes. Show how complaints/postmarket data update risk, design, production,
suppliers, CAPA, and management review.

### 4. Build a controlled cross-reference

Create a matrix that links manual statements to:

- controlled procedure IDs and revisions;
- forms and record series;
- product/device/technical files;
- risk and traceability evidence;
- system/software validation;
- process owners and approvals;
- source/version criteria; and
- open gaps/change/CAPA records.

Do not describe a referenced document as effective until its approval, effective date,
training, and availability are evidenced.

### 5. Draft policy-level content

Use the fail-closed template in
`assets/templates/quality-manual-template.md`. Keep statements factual and
organization-specific:

- “The approved process is defined in `<controlled ID/revision>`.”
- “Evidence is retained in `<controlled record series/location>`.”
- “`<role>` owns the decision, with approval in `<record ID>`.”
- “Applicability remains undetermined pending `<authorized review>`.”

Avoid:

- “The organization is compliant” or “audit ready”;
- “This template satisfies ISO/FDA/EU requirements”;
- generic quality policies presented as approved;
- fixed timelines or retention periods without source/risk basis;
- unsupported “not applicable” statements;
- old QSR clause maps presented as current QMSR; and
- claims that an ISO certificate covers FDA, MDSAP, or EU product conformity.

### 6. Review against evidence

Perform independent review in two directions:

1. **Manual to evidence:** every material statement points to a current controlled
   source, procedure, owner, and record set.
2. **Evidence to manual:** sampled implementation records match the described scope,
   roles, interactions, and controls.

Sample across products, sites, shifts/time periods, suppliers, systems, changes, and
risk as justified. Record limitations and open gaps.

### 7. Approve, train, release, and maintain

Before release:

- resolve placeholders;
- obtain technical, RA/QA, document-control, and authorized management approvals;
- complete source and applicability reviews;
- close or formally control open document/process gaps;
- approve process map and cross-reference;
- complete affected-person training;
- verify controlled point-of-use access;
- assign effective date and obsolete prior revisions; and
- record maintenance/currency-review triggers.

Review when products, sites, roles, processes, suppliers, systems, standards,
regulations, audit programs, certificates, or postmarket evidence change—not only on
an arbitrary calendar date.

## Suggested 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

