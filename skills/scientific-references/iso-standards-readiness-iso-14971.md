---
id: sciref-iso-standards-readiness-iso-14971
name: "Scientific Ref: ISO 14971 Process Framework (No Standard Text)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (iso-standards-readiness): ISO 14971 Process Framework (No Standard Text)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "iso standards readiness iso 14971"
  - "iso 14971 process framework (no standard text)"
keywords:
  - "iso"
  - "standards"
  - "readiness"
  - "14971"
  - "specialized"
  - "scientific"
  - "reference"
  - "process"
---

# ISO 14971 Process Framework (No Standard Text)

Research basis: **2026-10-01**. This
reference summarizes a preparation process and evidence architecture for medical device
risk management. It does not reproduce requirements and is not a substitute for the
standard.

## Copyright and authorized access

ISO publications are copyrighted. Obtain ISO 14971 and ISO/TR 24971 from
[ISO](https://www.iso.org/standard/72704.html), an ISO national member, or another
authorized source; see [ISO copyright](https://www.iso.org/copyright.html). Do not ask
an agent to retrieve, transcribe, summarize clause-by-clause, or store proprietary
text.

## Current edition, the guidance companion, and the European amendment

- [ISO 14971:2019](https://www.iso.org/standard/72704.html) is Edition 3, published
  December 2019, reviewed and confirmed in 2025.
- [ISO/TR 24971:2020](https://www.iso.org/standard/74437.html) is Edition 2 and is the
  guidance companion, following the same clause structure. It is a **Technical
  Report**: informative, not normative. Conformity is claimed to ISO 14971, never to
  ISO/TR 24971, and a TR cannot relax or reinterpret a normative requirement. Record
  which guidance the organization adopted and why. ISO marks the TR for revision;
  [ISO/AWI TS 24971-1](https://www.iso.org/standard/94297.html) is stage 20.00,
  under development. Keep the published 2020 TR as the guidance baseline until an
  authorized change review; a work item is not a published replacement.
- **EN ISO 14971:2019/A11:2021** is a European amendment to the EN adoption, cited for
  MDR and, through the corresponding decision, IVDR support. It does not change the
  international normative part. Track it only where the European source basis applies.

## This profile supports risk evidence inside a named assurance lane

ISO 14971 is a device risk-management process standard. This skill does not define a
standalone management-system certification scheme for it. Risk evidence supports
other assessments, for example:

- an ISO 13485 certification audit examines the risk-management process as part of the
  QMS;
- an FDA inspection examines risk-based decisions against applicable FDA requirements;
- an MDSAP audit treats risk management as a foundation across its process areas; and
- EU conformity assessment examines the risk-management file as part of technical
  documentation against the applicable general safety and performance requirements.

If a third party supplies a certificate or assessment referencing ISO 14971, record
its actual issuer, scheme, scope, and limitations. Do not treat its label as ISO 13485
certification, product approval, or a regulator decision. Report risk evidence as
supporting the declared lane, without issuing an assurance result.

## Hard boundary

This skill and its files cannot:

- certify, approve, or validate a risk-management file or process;
- determine device classification, intended use, reportability, conformity route,
  market access, or product authorization;
- decide whether a risk is acceptable, whether benefit outweighs residual risk, or
  whether a risk-control measure is adequate or safe;
- set or approve risk-acceptability criteria, severity or probability scales, or a
  risk matrix;
- replace top management, the risk-management owner, qualified clinical and engineering
  reviewers, RA/QA, a notified body, or a regulator; or
- infer that a hazard set is complete, or that residual risk is acceptable, from a
  template, a matrix, a document count, or a script result.

Use outputs as a list of evidence questions for accountable human review. **Completeness
of hazard identification cannot be established by any check in this skill** — a
zero-finding structural result says the declared links are present, not that the
analysis found everything.

## Process and evidence domains

The `iso-14971` profile carries these domain labels for manifests and gap reports.
They are workflow topics, not clause references:

`risk-management-plan`, `risk-management-file`, `competence-and-authority`,
`intended-use-and-characteristics`, `hazard-identification`,
`risk-estimation-and-evaluation`, `risk-control-option-analysis`,
`risk-control-implementation-and-verification`, `risk-control-side-effects-review`,
`residual-risk-evaluation`, `benefit-risk-analysis`,
`overall-residual-risk-evaluation`, `risk-management-review-and-report`,
`production-and-postproduction-information`, `change-control`.

Each domain needs an owner, status, evidence IDs, source/version reference, recorded
approval, and links to open gaps.

## The chain that has to hold together

Risk-management evidence is judged as a connected chain, not as a set of documents. For
each analysed item, the following must be traceable in both directions:

intended use and reasonably foreseeable misuse → characteristics related to safety →
hazard → foreseeable sequence of events → hazardous situation → harm with severity →
probability basis → risk evaluation against declared criteria → risk-control option
analysis and decision → implemented control → verification that the control was
implemented → verification of its effectiveness → review for new or increased risks
introduced by the control → residual risk evaluation → benefit-risk analysis where
residual risk is not acceptable → contribution to overall residual risk → disclosure of
residual risk → production and post-production information feeding back.

Break any one link and the file stops being evidence. The two links most often missing
are **verification of control effectiveness** (distinct from verifying the control
exists) and **review of risks introduced by the control itself**.

Build the traceability register with:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_traceability.py \
  /path/to/traceability-matrix.json
```

That check links intended use, hazard or signal, risk evaluation, risk control, design
input and output, verification, validation, production control, and post-market source.
It verifies declared linkage, not analytical adequacy.

## Where risk management meets the QMS

ISO 14971 work is not separable from the device QMS. Keep these joins explicit and
evidenced:

- **Design and development** — risk controls that are design outputs must appear as
  design inputs with verification, not only as risk-file rows.
- **Production** — controls realized as process parameters, in-process checks, or
  acceptance criteria need production evidence, and process val

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

