---
id: sciref-iso-standards-readiness-iso-17025
name: "Scientific Ref: ISO/IEC 17025 Process Framework (No Standard Text)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (iso-standards-readiness): ISO/IEC 17025 Process Framework (No Standard Text)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "iso standards readiness iso 17025"
  - "iso/iec 17025 process framework (no standard text)"
keywords:
  - "iso"
  - "standards"
  - "readiness"
  - "17025"
  - "specialized"
  - "scientific"
  - "reference"
  - "process"
---

# ISO/IEC 17025 Process Framework (No Standard Text)

Research basis: **2026-10-01**. This reference summarizes a preparation process and
evidence architecture for testing and calibration laboratory competence work. It does
not reproduce requirements and is not a substitute for the standard.

## Copyright and authorized access

ISO and IEC publications are copyrighted. Obtain ISO/IEC 17025 from
[ISO](https://www.iso.org/standard/66912.html), IEC, an ISO national member, or another
authorized source; see [ISO copyright](https://www.iso.org/copyright.html). Do not ask
an agent to retrieve, transcribe, summarize clause-by-clause, or store proprietary
text. Accreditation-body checklists that quote the standard are equally copyrighted and
are usually licensed only to the accredited laboratory.

## Current edition

- [ISO/IEC 17025:2017](https://www.iso.org/standard/66912.html) is Edition 3. No
  successor edition was identified at the research basis date. The catalogue confirms
  the 2017 edition after its 2023 review. Its listed 2018 corrections concern French
  and Spanish versions, not the English text.
- The 2017 edition restructured the 2005 edition around laboratory activities and
  risk-based thinking. Using a 2005 clause checklist as current criteria is
  obsolete. A manual may retain an older internal organization if its controlled
  cross-reference and implementation address the current standard; headings alone
  do not determine conformity.
- Record publisher, title, edition, amendments/corrigenda, authorized location, access
  date, source owner, currency-review date, impact decision, and approval in the
  controlled source ledger.

## The vocabulary trap: laboratories are accredited, not certified

A laboratory is **accredited** to ISO/IEC 17025 by an accreditation body. It is not
"ISO 17025 certified." A document labelled a certificate does not substitute for
accreditation or establish accredited technical scope.
Writing "certified" in a report, tender response, or quality manual is a substantive
error that assessors and customers both notice.

- Accreditation bodies operate under ISO/IEC 17011 and are peer-evaluated through the
  recognition arrangement. Certification bodies operate under ISO/IEC 17021-1. These
  are different schemes with different scope statements.
- Since **2026-01-01**, Global Accreditation Cooperation Incorporated has replaced the
  former ILAC and IAF and operates its own Multilateral Recognition Arrangement.
  Results and certificates issued under the former ILAC MRA / IAF MLA remain
  recognized during the transition. Verify current logo, claim, and endorsement wording
  with the accreditation body before reproducing any of it.
- ISO/IEC 17025 accreditation is not ISO 9001 certification, not a product approval,
  not a regulatory authorization, and not a statement that any particular result is
  correct.

## Hard boundary

This skill and its files cannot:

- accredit a laboratory, issue or validate an accreditation certificate or schedule,
  or predict an assessment outcome;
- decide which accreditation scheme, jurisdiction requirement, or customer
  specification applies;
- replace the laboratory's technical management, quality manager, authorized signatory,
  accreditation body, assessor, or proficiency-testing provider;
- validate a method, compute or approve a measurement uncertainty budget, establish
  metrological traceability, or judge whether a decision rule is fit for purpose; or
- infer competence from a document title, keyword, template, checklist, or script
  result.

Use outputs as a list of evidence questions for accountable human review.

## Scope of accreditation is per activity, not per organization

The accredited scope is defined item by item: field or discipline, method or procedure
and its issue, the measurand or property determined, and the range with the reported
uncertainty basis. For calibration laboratories this is normally expressed through
calibration and measurement capability statements.

Consequences for evidence preparation:

- Work outside the accredited scope must not carry an accreditation claim or
  endorsement, even at an accredited site under an accredited quality system.
- A method change, a range extension, a new location, or a new authorized signatory is
  a scope question, not only an internal change-control question.
- Subcontracted work has its own rules for customer notification and for the
  subcontractor's own accreditation status. Record both.

Capture scope items with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_scope_intake.py \
  /path/to/laboratory-scope-intake.json --standard iso-17025
```

Copy `assets/templates/laboratory-scope-intake-template.json` outside the skill first.
The distributed template fails closed by design.

## Process and evidence domains

The `iso-17025` profile carries these domain labels for manifests and gap reports.
They are workflow topics, not clause references:

`scope-and-impartiality`, `organizational-structure-and-management`,
`personnel-competence`, `facilities-and-environmental-conditions`,
`equipment-and-calibration`, `metrological-traceability`,
`externally-provided-products-and-services`, `review-of-requests-and-contracts`,
`method-selection-verification-and-validation`, `sampling`, `handling-of-items`,
`technical-records`, `measurement-uncertainty`,
`validity-of-results-and-proficiency-testing`, `reporting-and-decision-rules`,
`complaints`, `nonconforming-work`, `data-and-information-management`,
`internal-audit`, `management-review`, `corrective-action-and-improvement`.

Each domain needs an owner, status, evidence IDs, source/version reference, recorded
approval, and links to open gaps. Sample **records**, not only procedures: a procedure
describing uncertainty evaluation is not evidence that a budget exists for a reported
measurand.

## The four technical areas that carry most findings

### 1. Metrological traceability

Traceability is a documented, unbroken chain to a stated reference with stated
uncertainty at each step — not a drawer of calibration certificates. The governing
policy is **ILAC P10:07/2020** (implementation July 2021, revised for the 2017
edition), still carried in the current Global ACI library. Its proposed successor
Global ACI-TECH-1-011 remains in process in the September 2026 cross-reference
table; do not cite that identifier as a published policy.

Evidence to assemble per measurement: the stated reference, the cal

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

