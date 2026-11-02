---
id: sci-iso-standards-readiness
name: "Scientific: iso-standards-readiness"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Prepares and structurally reviews readiness evidence for ISO management-system and laboratory-competence standards - ISO 13485 medical device QMS, ISO 14971 device risk management, ISO/IEC 17025 testing and calibration laboratories, and ISO 15189 medical laboratories. Use when or"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "iso standards readiness"
  - "iso-standards-readiness"
keywords:
  - "iso"
  - "standards"
  - "readiness"
  - "prepares"
  - "structurally"
  - "reviews"
  - "evidence"
  - "management"
---

# ISO Standards Readiness Evidence Preparation

## Purpose

Use this skill to organize declared scope, controlled documents, implementation
records, traceability, and readiness evidence for substantive human review against a
named standard. It summarizes process workflows and provides deterministic local
checks. It contains no clause text and performs no audit.

`SKILL.md` holds the boundary, lane discipline, shared evidence workflow, and CLI
contract. Per-standard preparation details live in `references/`.

## Non-negotiable boundary

This skill cannot:

- certify or accredit anything, issue or validate a certificate, accreditation
  schedule, or licence, or promise an audit, assessment, or inspection result;
- determine legal/regulatory applicability, device classification, reportability,
  conformity route, product authorization, market access, licensure, personnel
  qualification, or compliance;
- replace authorized management, the management representative, laboratory director,
  quality manager, authorized signatory, RA/QA, legal counsel, regulatory/competent
  authorities, a notified body, an MDSAP Auditing Organization, an accreditation body,
  an assessor, or a certification body;
- validate a method, compute or approve measurement uncertainty, establish
  metrological traceability, set risk-acceptability criteria, or judge whether a risk,
  decision rule, or reference interval is fit for purpose; or
- infer implementation, competence, conformity, compliance, or readiness from a
  template, checklist, filename, keyword, document count, percentage, or script
  result.

Always label outputs **draft evidence-preparation material for authorized human
review**. Preserve unresolved decisions as blockers rather than resolving them.

## ISO and IEC copyright

ISO and IEC standards are copyrighted. Obtain each standard from
[ISO](https://www.iso.org/standards.html), IEC, an ISO national member, or another
authorized source. Do not retrieve, paste, reproduce, or generate clause text.
Summarize the organization's own process and cite the controlled authorized copy. See
[ISO copyright](https://www.iso.org/copyright.html). Accreditation-body, CAP, and
scheme checklists that quote requirements are separately licensed — keep them out of
shared repositories and prompts too.

## Standards covered

Read the reference file for the standard in play **before** preparing evidence. Each
one carries its own current edition, lane, domain vocabulary, and failure modes.

| Standard | Profile key | Lane | Reference |
| --- | --- | --- | --- |
| ISO 13485 medical device QMS | `iso-13485` | Certification | `references/iso-13485.md` |
| ISO 14971 device risk management | `iso-14971` | Supports a declared lane | `references/iso-14971.md` |
| ISO/IEC 17025 testing and calibration laboratories | `iso-17025` | Accreditation | `references/iso-17025.md` |
| ISO 15189 medical laboratories | `iso-15189` | Accreditation | `references/iso-15189.md` |

A standard absent from this table is out of scope for the bundled checks. Do not
repurpose a profile for a standard it does not name — a domain vocabulary borrowed from
a different standard produces a report that looks complete and means nothing.

## Current baseline (read the ledger before any time-sensitive statement)

- **ISO 13485:2016** Edition 3, confirmed after its 2025 systematic review.
  **EN ISO 13485:2016/A11:2021** is a European amendment, not an ISO international
  "Amendment 1:2021."
- **ISO 14971:2019** Edition 3, confirmed in 2025, with **ISO/TR 24971:2020** as its
  informative guidance companion. Its proposed successor **ISO/AWI TS 24971-1**
  is under development, not a published replacement or a new normative basis.
- **ISO/IEC 17025:2017** Edition 3 remains current; no successor edition identified.
- **ISO 15189:2022** Edition 4 replaced the 2012 edition, absorbed the POCT
  requirements formerly in ISO 22870, and its accreditation transition closed in
  **December 2025** — implemented, not upcoming.
- **FDA QMSR** effective and enforced since **2026-02-02**; Part 820 is titled
  *Quality Management System Regulation*; QSIT is retired in favour of Compliance
  Program **7382.850**.
- **MDSAP** current Audit Approach is **MDSAP AU P0002.011**, version date
  **2026-08-03**.
- **Accreditation recognition:** Global Accreditation Cooperation Incorporated
  commenced full operations **2026-01-01**, replacing ILAC and IAF, with its own MRA;
  former IAF MLA / ILAC MRA outputs stay recognized during the transition.
- **EU:** use current consolidated MDR/IVDR texts, current OJEU harmonised-standard
  decisions, current MDCG guidance, and the product-specific conformity route.

Read `references/source-ledger.md` before making any time-sensitive statement. It
records catalogue confirmation, published versus draft documents, and the remaining
EU source-retrieval limitations. The bundled report `basis_date` is this skill
release's research baseline, not the organization's review date or a freshness guarantee.

## Keep the assurance lanes separate

Lane confusion, not missing documents, causes most substantive errors here.
Certification, accreditation, regulator inspection, mandatory licensure, regulatory
audit programmes, and product conformity assessment are decided by different bodies
against different bases, and none substitutes for another. Two rules that are violated
constantly:

- Organizations are **certified**; laboratories are **accredited**. "ISO 17025
  certified" and "ISO 15189 certified" are category errors.
- A certificate never displaces a regulator. ISO 13485 certification does not exempt
  anyone from FDA inspection, and ISO 15189 accreditation does not satisfy CLIA.

Read `references/assurance-lanes.md` for the full lane table, scope-statement limits,
and the titling rule.

## Core workflow

### Step 1: Declare the standard, purpose, and authorized owners

Name the standard(s), the lane(s) the work supports, and the owners: management
representative or laboratory director, quality owner, legal/applicability owner,
process or technical owners, approvers, and escalation route. A lane is a declared
input, never an inference.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_scope_intake.py \
  assets/templates/scope-intake-template.json --standard iso-13485
```

Use the matching template and profile:

| Profile | Template |
| --- | --- |
| `iso-13485`, `iso-14971` | `assets/templates/scope-intake-template.json` |
| `iso-17025` 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

