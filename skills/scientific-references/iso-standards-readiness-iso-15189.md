---
id: sciref-iso-standards-readiness-iso-15189
name: "Scientific Ref: ISO 15189 Process Framework (No Standard Text)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (iso-standards-readiness): ISO 15189 Process Framework (No Standard Text)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "iso standards readiness iso 15189"
  - "iso 15189 process framework (no standard text)"
keywords:
  - "iso"
  - "standards"
  - "readiness"
  - "15189"
  - "specialized"
  - "scientific"
  - "reference"
  - "process"
---

# ISO 15189 Process Framework (No Standard Text)

Research basis: **2026-10-01**. This reference summarizes a preparation process and
evidence architecture for medical laboratory quality and competence work. It does not
reproduce requirements and is not a substitute for the standard.

## Copyright and authorized access

ISO publications are copyrighted. Obtain ISO 15189 from
[ISO](https://www.iso.org/standard/76677.html), an ISO national member, or another
authorized source; see [ISO copyright](https://www.iso.org/copyright.html). Do not ask
an agent to retrieve, transcribe, summarize clause-by-clause, or store proprietary
text. Accreditation-body and CAP checklists that quote requirements are separately
licensed material — do not paste them into shared repositories or prompts.

## Current edition and the closed transition

- [ISO 15189:2022](https://www.iso.org/standard/76677.html) is Edition 4, published
  December 2022, cancelling and replacing ISO 15189:2012; catalogue metadata was
  read directly for this review.
- The 2022 edition aligns structurally with ISO/IEC 17025:2017 and **incorporates
  point-of-care testing requirements previously held in ISO 22870**. Do not cite
  ISO 22870:2016 as a current separate basis: the ISO catalogue lists it as withdrawn.
- The ILAC-agreed transition for accredited medical laboratories ran to **December
  2025**. A 2012-based quality system is out of date, not "in transition" — do not
  build a gap baseline that assumes a future deadline.
- Record publisher, title, edition, amendments, authorized location, access date,
  source owner, currency-review date, impact decision, and approval in the controlled
  source ledger.

## Keep four lanes separate

### 1. ISO 15189 accreditation

An accreditation body grants accreditation for a defined scope of examinations, per
laboratory and per location, under ISO/IEC 17011. A medical laboratory is
**accredited**, not "ISO 15189 certified." Since 2026-01-01 the recognition arrangement
sits with Global Accreditation Cooperation Incorporated; verify current claim and logo
wording with the accreditation body.

### 2. United States CLIA certification

CLIA covers US human-specimen testing for diagnosis, prevention, treatment, or
health assessment. Applicable laboratories need the appropriate CLIA certificate
or an applicable exemption. Under [42 CFR 493.3](https://www.ecfr.gov/current/title-42/chapter-IV/subchapter-G/part-493/subpart-A/section-493.3),
research testing without patient-specific results for those clinical purposes is an
explicit exception. This does not make every research-labelled study exempt: the
authorized owner must evaluate the actual testing and reporting purpose.

**ISO 15189 accreditation does not satisfy CLIA and cannot replace a CLIA-based
accreditation.** Deemed status flows only from a CMS-approved accreditation
organization's program. CMS approves a limited set of accreditation organizations whose
approved programs support the CLIA accreditation route; read the
[current AO list](https://www.cms.gov/media/678411)
rather than relying on a remembered count. The CAP 15189 program is layered on top of
CAP Laboratory Accreditation Program accreditation rather than offered as a standalone
substitute. CAP's current program page also excludes POCT from the CAP 15189
program scope and keeps a quality-manual requirement. These are scheme-specific
conditions; ISO 15189's broader POCT coverage does not override them.

Never let an ISO 15189 readiness output be read as CLIA compliance, deemed status,
licensure, or an inspection result.

### 3. Other national licensure and inspection regimes

State licensure, national health-authority requirements, and payer conditions of
participation are separate again, with their own inspection processes and their own
records. Non-US jurisdictions may make ISO 15189 accreditation mandatory, voluntary, or
irrelevant. This is an applicability decision for authorized humans.

### 4. IVD device regulation

The performance of an in vitro diagnostic device, and any laboratory-developed test
regime that applies to it, is regulated separately from laboratory accreditation. EU
IVDR conformity assessment, notified-body involvement, and performance-study
requirements are not laboratory accreditation questions. See `references/iso-13485.md`
and the EU entries in `references/source-ledger.md`.

## Hard boundary

This skill and its files cannot:

- accredit a laboratory, issue or validate an accreditation certificate or schedule,
  or predict an assessment or inspection outcome;
- establish CLIA certification, deemed status, licensure, or personnel qualification;
- decide which scheme, jurisdiction requirement, or payer condition applies;
- replace the laboratory director, quality manager, authorized signatory,
  accreditation body, assessor, EQA provider, or competent authority;
- verify or validate an examination procedure, set biological reference intervals,
  establish traceability of assigned values, or judge clinical suitability; or
- infer competence or patient safety from a document title, keyword, template,
  checklist, or script result.

Use outputs as a list of evidence questions for accountable human review.

## Scope of accreditation is per examination

Each scope item is defined by discipline, the examination or measurand reported, the
controlled procedure and its issue, and the primary sample type with its acceptance
requirements. Point-of-care testing performed under the laboratory's responsibility
belongs in the scope discussion explicitly, including devices operated by clinical
staff outside the laboratory.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_scope_intake.py \
  /path/to/medical-laboratory-scope-intake.json --standard iso-15189
```

Copy `assets/templates/medical-laboratory-scope-intake-template.json` outside the skill
first. The distributed template fails closed by design.

## Process and evidence domains

The `iso-15189` profile carries these domain labels for manifests and gap reports.
They are workflow topics, not clause references:

`scope-and-impartiality`, `organizational-structure-and-governance`,
`personnel-competence`, `facilities-and-safety`, `equipment-and-calibration`,
`metrological-traceability`, `reagents-and-consumables`,
`externally-provided-products-and-services`, `pre-examination-processes`,
`examination-methods-verification-and-validation`, `measurement-uncertainty`,
`validity-of-results-and-external-qualit

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

