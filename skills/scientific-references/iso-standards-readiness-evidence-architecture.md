---
id: sciref-iso-standards-readiness-evidence-architecture
name: "Scientific Ref: Documentation and Evidence Architecture"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (iso-standards-readiness): Documentation and Evidence Architecture"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "iso standards readiness evidence architecture"
  - "iso standards readiness evidence arquitetura"
  - "documentation and evidence architecture"
keywords:
  - "iso"
  - "standards"
  - "readiness"
  - "evidence"
  - "architecture"
  - "arquitetura"
  - "specialized"
  - "scientific"
  - "reference"
  - "documentation"
---

# Documentation and Evidence Architecture

Research basis: **2026-10-01**; current-source details are in `references/source-ledger.md`. This is a
process-oriented planning reference, not a list of copyrighted ISO or IEC requirements.

The five-layer hierarchy below applies to every standard this skill covers. Where the
wording is device-specific, the laboratory equivalent is noted; for depth read
`references/iso-17025.md` or `references/iso-15189.md`.

## Do not use a fixed “31 procedures” claim

ISO 13485 does not require one universal package of a fixed number of separately
titled procedures for every organization. Document architecture depends on QMS
scope, products, lifecycle activities, sites, outsourced processes, applicable
regulatory requirements, and how controlled processes are combined or split.

Avoid:

- declaring a QMS complete because a named-document count was reached;
- equating a filename or keyword hit with implementation;
- treating an example document name as mandatory;
- labeling every conditional process “not applicable” without an authorized decision;
- assuming one regime's records satisfy another regime; or
- claiming certification/readiness from document presence.

Use an authorized copy of ISO 13485 and current jurisdiction/product sources to
identify the documentation and records that actually apply. ISO publications are
copyrighted; see [ISO copyright](https://www.iso.org/copyright.html).

## Controlled evidence hierarchy

### 1. Source and applicability layer

Maintain:

- dated official-source ledger with exact edition/version;
- product/site/market/lifecycle scope intake;
- authorized applicability and not-applicable decisions;
- regulatory/product-requirements matrix;
- certification, MDSAP, FDA, and EU assurance-route distinctions;
- source-change monitoring and impact assessments.

Minimum fields: source ID, publisher, title, edition/version/date, authorized
location, access date, owner, status, currency-review date, impact record, and
approval.

### 2. Governance and policy layer

Typical controlled documents and records:

- QMS scope and quality manual or equivalent policy architecture;
- quality policy/objectives and measures;
- organization chart, role authorities, delegates, independence, and escalation;
- authorized management representative appointment;
- process-interaction map;
- management review plan, records, decisions, and follow-up.

The quality manual is not evidence that the processes operate. Link it to approved
procedures and sampled implementation records.

### 3. Process-control layer

An organization may combine or separate controlled procedures. Use titles that match
actual work. At minimum, assess whether controlled documentation is needed for:

- document, record, and external-source control;
- risk management;
- design and development, transfer, and design change;
- customer/product requirements and communications;
- suppliers, purchasing, outsourced processes, and acceptance;
- production, service, infrastructure, environment, and maintenance;
- process, equipment, test-method, and software validation;
- monitoring/measurement equipment;
- identification, traceability, preservation, installation, and servicing;
- feedback, complaints, postmarket surveillance, and vigilance/reporting;
- nonconforming outputs, corrections, removals/advisory actions, and CAPA;
- internal audit, data/trend analysis, and management review;
- competence, training, authorization, and awareness; and
- QMS/product/process/source/software change control.

Each controlled process should identify purpose, scope, roles, inputs, outputs,
methods, decision criteria, records, interfaces, measures, change controls,
source/version basis, approval, and effective date.

### 4. Product and technical evidence layer

Maintain a controlled file architecture for each applicable product/type/family.
Depending on product and jurisdiction, evidence may include:

- product description, intended purpose/use, claims, variants, accessories;
- classifications and authorized decision records;
- requirements/specifications and acceptance criteria;
- risk management and benefit-risk evidence;
- design planning, inputs, outputs, reviews, verification, validation, transfer,
  and changes;
- production, supplier, packaging, labeling, installation, and service information;
- software lifecycle, cybersecurity, usability, biocompatibility, electrical safety,
  sterilization, clinical/performance, and other product-specific evidence;
- acceptance/release and distribution/traceability records;
- postmarket plans, reports, complaints, vigilance, field actions, and updates.

Do not claim that an ISO 13485 “medical device file” automatically replaces every
FDA, EU, or other jurisdiction-specific file or record concept. Build a cross-reference
that preserves each required record and its source/version.

**Laboratory equivalent.** For ISO/IEC 17025 and ISO 15189 the technical evidence layer
is organized per scope item — per method, measurand, or examination — rather than per
product family. Depending on the activity it may include:

- the controlled method or examination procedure and its issue, with the authorization
  to put it into service;
- verification or validation evidence: performance characteristics evaluated,
  acceptance criteria, data, and approval;
- the measurement-uncertainty evaluation and its stated basis;
- metrological traceability evidence: stated reference, provider and its accreditation
  scope, certificate identity, uncertainty carried forward, interval justification, and
  intermediate checks;
- the documented decision rule and customer-agreement record where conformity is
  stated;
- proficiency-testing or external-quality-assessment enrolment, results, evaluation
  against criteria, and investigation of unsatisfactory outcomes;
- equipment, reagent, consumable, and reference-material records;
- technical records sufficient to reproduce the reported result; and
- report and certificate templates, amendment/retraction handling, and authorized
  signatories.

An accredited scope schedule is not this layer — it is the output of the accreditation
body. Keep the two apart in the register.

### 5. Implementation-record layer

Procedures describe controls; records show what happened. Sample actual records for:

- approvals, revision/effective status, training, and point-of-use control;
- competence and role authorization;
- management review inputs, decisions, re

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

