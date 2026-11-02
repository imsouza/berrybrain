---
id: sciref-hypothesis-generation-ethics-safety-and-ai
name: "Scientific Ref: Ethics, Safety, Feasibility, and Responsible AI"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (hypothesis-generation): Ethics, Safety, Feasibility, and Responsible AI"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "hypothesis generation ethics safety"
  - "hipotese generation ethics safety"
  - "ethics, safety, feasibility, and responsible ai"
keywords:
  - "hypothesis"
  - "generation"
  - "ethics"
  - "safety"
  - "hipotese"
  - "specialized"
  - "scientific"
  - "reference"
---

# Ethics, Safety, Feasibility, and Responsible AI

## This is a routing guide

This reference helps identify gates. It is not legal, medical, regulatory, biosafety, biosecurity, export-control, ethics, or institutional advice. Requirements vary by jurisdiction, sponsor, institution, organism, material, and intended use.

When applicability is uncertain, mark the gate `undetermined`, stop operational planning, and obtain a determination from the qualified local authority.

## Universal intake

Record:

- accountable owner and institution;
- intended purpose and foreseeable misuse;
- affected people, animals, communities, ecosystems, infrastructure, or security interests;
- data and material sensitivity;
- funding, jurisdiction, and collaborating sites;
- required expertise;
- conflicts and incentives;
- approvals, determinations, and unresolved blocks;
- less risky ways to answer the question.

Feasibility never overrides ethics or safety.

## Human-participant gate

Potential triggers include:

- intervention or interaction with living people;
- identifiable private information or biospecimens;
- secondary use, linkage, re-identification, recruitment, or contact;
- vulnerable populations or sensitive topics;
- international or community-governed data.

Required action:

- obtain an IRB/REC or other authorized determination before research starts;
- do not self-declare exemption;
- address consent or authorized waiver, privacy, security, equitable selection, risk/benefit, compensation, return of results, and community governance as applicable;
- use additional protections required by law or policy.

In the United States, HHS 45 CFR 46 includes the Common Rule and additional subparts. Local and non-U.S. rules can differ. The 2024 revision of the World Medical Association Declaration of Helsinki is a relevant international ethical statement for medical research involving human participants.

This skill does not provide clinical advice or authorize an intervention.

## Animal-research gate

Potential triggers include live vertebrate animals, field capture, breeding, procedures, tissues tied to ongoing animal activities, or covered training/testing.

Required action:

- obtain the applicable IACUC or equivalent approval before work;
- establish institutional assurance and veterinary oversight where required;
- apply replacement, reduction, and refinement;
- justify species/model, numbers, endpoints, welfare monitoring, analgesia/anesthesia, and humane endpoints through the authorized process;
- use current reporting guidance such as ARRIVE when applicable.

The bundled tools do not calculate animal numbers or approve protocols.

## Biosafety and biosecurity gate

Potential triggers include:

- recombinant or synthetic nucleic acids;
- infectious agents, toxins, biological materials, gene transfer, or modified organisms;
- environmental release;
- select agents or regulated materials;
- procedures that could alter hazard, host range, pathogenicity, transmissibility, resistance, or detection;
- work beyond established institutional containment and training.

Required action:

- stop before operational detail;
- route to the biosafety officer, Institutional Biosafety Committee, and other required authority;
- use the current NIH Guidelines, CDC/NIH *Biosafety in Microbiological and Biomedical Laboratories*, local biosafety manual, and applicable regulations;
- document containment and occupational-health decisions only after authorized review.

Do not infer a containment level or operating procedure from this skill.

## Dual-use and harmful-use gate

Potential triggers include research, data, models, or protocols that could reasonably enable:

- increased biological harm or spread;
- evasion of detection, treatment, control, or safeguards;
- scalable production or dissemination of harmful agents;
- weaponization;
- exploitation of critical vulnerabilities;
- transfer of restricted technical information.

Required action:

1. Do not provide optimization, stepwise procedures, parameter choices, sequences, acquisition pathways, or troubleshooting that increase harmful capability.
2. Preserve only a high-level scientific question, benefit rationale, and risk statement.
3. Route to institutional dual-use/biosecurity review, funder, legal/export-control, and other required authorities.
4. Follow current policy, award terms, and jurisdiction-specific controls.

### U.S. policy status checked 2026-10-01

- The July 2026 [USG Policy for Stopping High-Risk Life Sciences Research](https://www.whitehouse.gov/wp-content/uploads/2026/07/USG-Policy-for-Stopping-High-Risk-Life-Sciences-Research_July-2026.pdf) has been issued; it is no longer an awaited replacement for the 2024 DURC/PEPP framework.
- NIH [NOT-OD-26-101](https://grants.nih.gov/grants/guide/notice-files/NOT-OD-26-101.html), issued July 28, 2026, describes federal funding prohibitions and oversight for dangerous gain-of-function research and international research of concern. It states that activities previously identified as potential dangerous gain-of-function research remain paused until NIH-specific implementation requirements are established. Do not infer that policy publication authorizes resumption.
- The [NIH biosafety/biosecurity portal](https://osp.od.nih.gov/policies/biosafety-and-biosecurity-policy/) still directs researchers to the April 2024 NIH Guidelines. Its separately proposed [Draft NIH Biosafety Policy](https://grants.nih.gov/grants/guide/notice-files/NOT-OD-26-112.html), released August 19 with comments due October 19, 2026, would replace those Guidelines only when finalized. The draft is not an effective replacement.

Check the current agency implementation notices, award terms, and institutional determination for every project; neither a historical policy nor a pending proposal is clearance.

WHO’s *Global Guidance Framework for the Responsible Use of the Life Sciences* provides an international risk-governance framework; it does not replace national or local rules.

## Data-governance gate

Before using data:

- confirm authority, consent, license, data-use agreement, and purpose limitation;
- classify sensitivity and re-identification risk;
- minimize fields and access;
- use approved storage, retention, deletion, audit, and sharing controls;
- address community and Indigenous governance;
- separate public, controlled, confidential, proprietary, and export-controlled materials.

Passing a local schema check is not

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

