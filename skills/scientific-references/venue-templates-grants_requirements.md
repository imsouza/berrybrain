---
id: sciref-venue-templates-grants-requirements
name: "Scientific Ref: Grant Proposal Requirements"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (venue-templates): Grant Proposal Requirements"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "venue templates grants requirements"
  - "grant proposal requirements"
keywords:
  - "venue"
  - "templates"
  - "grants"
  - "requirements"
  - "specialized"
  - "scientific"
  - "reference"
  - "grant"
---

# Grant Proposal Requirements

Funding requirements are controlled by the current solicitation or notice of funding opportunity (NOFO), the effective agency guide, and the submission portal. A general agency summary never overrides the call.

**Reviewed:** 2026-10-01

## Required Order of Authority

Use sources in this order:

1. current solicitation, NOFO, or Broad Agency Announcement (BAA);
2. amendments and agency notices;
3. effective agency application guide and form set;
4. submission-portal validation; and
5. institutional sponsored-research guidance.

Record the source URLs, versions, and date checked in the proposal workspace.

## NSF

### Current policy basis

- PAPPG landing page: https://www.nsf.gov/policies/pappg
- Proposal preparation overview: https://www.nsf.gov/funding/preparing-proposal
- Current PAPPG Chapter II: follow the version marked current on the landing page
- SciENcv: https://www.ncbi.nlm.nih.gov/sciencv/

As reviewed on 2026-10-01, **NSF 24-1** remains the current PAPPG for proposals submitted or due on or after 2024-05-20, with [Supplement 1 (26-200)](https://www.nsf.gov/policies/document/pappg24-1-supplement-1) and [Supplement 2 (26-202)](https://www.nsf.gov/policies/document/pappg24-1-supplement-2). Recheck this status for every deadline.

### Verified common research-proposal rules

Unless the solicitation modifies them:

| Component | Current general rule |
|---|---|
| Project Summary | No more than 1 page; include Overview, Intellectual Merit, and Broader Impacts |
| Project Description | Up to 15 pages for a standard research proposal |
| References Cited | Separate section; follow PAPPG content rules |
| Data Management and Sharing Plan | Create using the Research.gov DMSP tool; Supplement 2 supersedes the old two-page PDF-upload rule from 2026-04-27 |
| Biographical Sketch | Generated in SciENcv for each senior/key person; no old three-page cap |
| Current and Pending (Other) Support | Generated and certified in SciENcv |
| Synergistic Activities | Separate document, up to 1 page and up to 5 examples per senior/key person |

**General formatting**

- Times New Roman or Computer Modern at 11 points or larger under the current general rule.
- No more than six lines of text in one vertical inch.
- Margins of at least one inch in every direction.
- Portal-generated forms and solicitation-specific instructions may control individual sections.

### Important change from older guidance

Do not use the obsolete “three-page NSF biosketch with Synergistic Activities inside it” pattern.

Current workflow:

1. prepare and certify the Biographical Sketch in SciENcv;
2. prepare and certify Current and Pending (Other) Support in SciENcv; and
3. upload Synergistic Activities as its own one-page document.

### Project Summary

Clearly label:

- **Overview** — proposed activity, objectives, and methods;
- **Intellectual Merit** — potential to advance knowledge; and
- **Broader Impacts** — potential to benefit society and produce desired societal outcomes.

The summary should be understandable to a broad scientific audience and is not merely the proposal abstract.

### Project Description

A practical drafting structure is:

1. problem, prior work, and gap;
2. objectives or hypotheses;
3. research plan and methods;
4. expected outcomes, risks, and alternatives;
5. timeline and team roles;
6. Intellectual Merit and Broader Impacts; and
7. Results from Prior NSF Support when required.

This is writing guidance, not a required section order. Follow the solicitation.

### Data Management and Sharing Plan

Use the Research.gov tool and current program prompts. Data supporting NSF-funded
publications must be shared at publication unless an exception is justified in the
plan. Do not upload the bundled prose as an assumed two-page substitute.

Address applicable plans for:

- data and other research products;
- standards and metadata;
- access, sharing, and any justified restrictions;
- reuse and redistribution;
- preservation and archiving; and
- roles and responsibilities.

Directorate, office, division, or program guidance may add requirements.

### Bundled NSF scaffold

`assets/grants/nsf_proposal_template.tex` is a planning scaffold for common narrative components. It is not an NSF-issued upload package. Split content into the appropriate Research.gov or Grants.gov fields and use SciENcv/common forms where required.

## NIH

### Current policy basis

- Application Guide: https://grants.nih.gov/grants-process/write-application/how-to-apply-application-guide
- Attachment formatting: https://grants.nih.gov/grants-process/write-application/how-to-apply-application-guide/format-attachments
- Page limits: https://grants.nih.gov/grants-process/write-application/how-to-apply-application-guide/page-limits

Use the form set and instructions applicable to the due date. The NOFO always takes precedence over general page-limit tables.

### Verified common page limits

As reviewed on 2026-10-01:

| Attachment | General limit unless the NOFO says otherwise |
|---|---|
| Specific Aims | 1 page |
| R01 Research Strategy | 12 pages |
| R21 Research Strategy | 6 pages; combined mechanisms can differ |
| Introduction to resubmission/revision | 1 page |
| Project Summary/Abstract | 30 lines |
| Project Narrative | 3 sentences for most activity codes |
| Legacy Biographical Sketch | Historical only; do not select this for a current application merely because it remains in the page-limit table |
| Biographical Sketch Common Form and Supplement | No hard page limit; length is controlled through SciENcv data entry |

Not every activity code uses every attachment. Check the NOFO and activity-code instructions.

### Attachment formatting

Verify the current guide for:

- accepted PDF format;
- paper size and margins;
- approved fonts and minimum size;
- file naming;
- hyperlinks;
- headers, footers, and page numbers; and
- whether a format page or common form is mandatory.

The current NIH attachment guide requires text of at least 11 points, at most
15 characters per linear inch, at most six lines per vertical inch, and margins of
at least half an inch. Smaller legible text is permitted in graphics. Helvetica
is among the recommended fonts; Arial is not uniquely required. Do not add
headers or footers/page numbers unless the attachment instructions request them.
Do not compress text or figures to evade a page limit.

### Specific Aims

A useful writing pattern is:

1. significance and un

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

