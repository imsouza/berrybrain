---
id: sciref-peer-review-ethical-review-practice
name: "Scientific Ref: Ethical and Confidential Peer Review"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (peer-review): Ethical and Confidential Peer Review"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "peer review ethical review practice"
  - "peer revisao ethical revisao practice"
  - "ethical and confidential peer review"
keywords:
  - "peer"
  - "review"
  - "ethical"
  - "practice"
  - "revisao"
  - "specialized"
  - "scientific"
  - "reference"
---

# Ethical and Confidential Peer Review

Reviewed on **2026-10-01** against COPE, ICMJE, and illustrative publisher policies listed in `assets/source_ledger.csv`. Source-specific access limits and dates are recorded there.

COPE’s current membership framework is its [Code of Conduct](https://publicationethics.org/membership/code-of-conduct), published 21 July 2026 with a 12-month implementation transition. It replaces the 2017 Core Practices, which were [retired in 2024](https://publicationethics.org/about/what-we-do/our-story/history-code-conduct). This membership framework is distinct from the still-current reviewer-specific **Ethical Guidelines for Peer Reviewers, version 2 (2017)** used below. The target journal’s published process controls the individual assignment.

## Role boundary

This skill supports an accountable human preparing a review draft or structured assessment. It must not:

- Claim to be the assigned reviewer, editor, journal, funder, or decision-maker
- Submit a review or contact authors, editors, institutions, or third parties without authorization
- Invent manuscript content, experiments, analyses, citations, reviewer identity, or editorial outcomes
- Present generated text as an independently completed review
- Investigate authors or search unpublished content outside the authorized process

The editor decides the editorial outcome. The reviewer provides evidence-bounded advice within the requested scope.

## Before accepting or starting

COPE’s Ethical Guidelines for Peer Reviewers and ICMJE recommendations require reviewers to consider:

### Competence

- Accept only work for which the reviewer can provide a useful assessment.
- State material subject-matter, methods, statistics, ethics, language, or domain limits.
- Ask the editor for a specialist reviewer when a central issue exceeds competence.
- Do not conceal limits by producing confident generic criticism.

### Conflicts

Disclose actual, potential, or perceived conflicts before proceeding. They can be:

- Financial or commercial
- Personal or family
- Institutional
- Recent collaboration, supervision, mentorship, or competition
- Intellectual commitments or directly competing work
- Political, religious, advocacy, or legal interests

The journal decides whether a disclosed conflict permits review. If unresolved, stop. In the intake, `disclosed_to_editor` remains blocked; record `editor_cleared` only after clearance. Do not accept merely to gain access to unpublished work.

### Capacity and timeliness

Accept only if the review can be completed within the agreed time. Tell the editor promptly if scope or timing changes.

### Journal policy

Record:

- Review model and anonymity expectations
- Whether co-review is allowed and how contributors are named
- Confidentiality and retention requirements
- Required author-facing and editor-only fields
- AI and tool policy
- Citation, image-integrity, data, ethics, and reporting expectations

Journal practices differ. A policy from another publisher is an example, not authority for the target venue.

Use `scripts/validate_review_intake.py` before substantive review.

## Confidentiality and data handling

An unpublished manuscript, its supplements, review comments, and editorial correspondence are privileged confidential material.

### Default rule

Keep processing local. Do not send, paste, upload, transcribe, summarize, or expose unpublished manuscript or review text to:

- Public or external generative-AI systems
- Search engines or web research tools
- Citation, plagiarism, grammar, translation, or image services
- Unapproved collaborators
- Cloud storage or telemetry outside the authorized environment

unless the publisher or author has authorized that specific use, the target venue permits it, and applicable privacy, contract, intellectual-property, and data-governance requirements are satisfied.

Authorization to review is not automatically authorization to disclose material to a service. A tool’s promise not to train on data is not, by itself, authorization.

A hosted assistant reading a file is external processing even when its shell or bundled validator executes locally. Do not confuse the CLI's local-only behavior with the assistant platform's handling of content.

The bundled CLIs:

- Use only Python’s standard library
- Read bounded local JSON, CSV, or Markdown
- Make no network, model, image, subprocess, environment-variable, or dynamic-code calls
- Emit identifiers, counts, rule codes, and line numbers rather than raw manuscript or review text
- Refuse symlink inputs and implicit output overwrite

They do not make an external service safe and do not authorize its use.

### Assistance and co-review

Obtain journal permission before sharing with a trainee or colleague. Record the contributor and acknowledge the contribution to the editor as required. The invited reviewer remains responsible for confidentiality and the submitted report.

### No reuse

Do not:

- Appropriate ideas, methods, code, data, or language before publication
- Use the material for model training, benchmarking, product improvement, or unrelated research
- Build a private corpus of manuscripts or reviews
- Retain content for convenience beyond policy

### Retention and deletion

After submitting or ending the review:

1. Follow the target venue’s retention rule.
2. Delete local manuscript and review copies when required.
3. Empty derivative exports and temporary files within the authorized workspace.
4. Retain only what policy requires.
5. Record deletion or authorized retention without copying confidential content into the record.

ICMJE recommends that reviewers not retain manuscripts for personal use and delete copies after review. Local law, publisher policy, or a documented investigation may impose a different rule; follow the controlling requirement.

## AI and automated assistance

ICMJE says reviewers must follow the journal’s AI policy or request permission before using AI, maintain confidentiality, disclose use, and remain responsible for output that may be incorrect, incomplete, or biased.

For any permitted assistance:

- Identify the tool, version, purpose, and material exposed
- Use only the minimum necessary content
- Keep an accountable human in control
- Verify every statement, citation, calculation, and proposed comment
- Disclose use exactly as the journal requires
- Do not let a model create an autonomous review or editorial outcome

If permission is abse

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

