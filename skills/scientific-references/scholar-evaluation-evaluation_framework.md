---
id: sciref-scholar-evaluation-evaluation-framework
name: "Scientific Ref: Evaluation Framework"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scholar-evaluation): Evaluation Framework"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scholar evaluation evaluation framework"
  - "evaluation framework"
keywords:
  - "scholar"
  - "evaluation"
  - "framework"
  - "specialized"
  - "scientific"
  - "reference"
---

# Evaluation Framework

## What ScholarEval is—and is not

The paper currently referenced by this skill is Moussa et al.,
[*ScholarEval: Research Idea Evaluation Grounded in
Literature*](https://arxiv.org/abs/2510.16234), arXiv:2510.16234v2,
revised 2026-02-28.

The preprint describes an experimental retrieval-augmented system for evaluating
research ideas on:

- **soundness:** whether existing literature empirically supports proposed
  methods; and
- **contribution:** how an idea advances beyond prior work along comparison
  dimensions.

It reports a 117-idea, four-discipline dataset, coverage comparisons with
expert-annotated review points, and a user study. Those studies evaluate that
framework. They do **not** validate the generalized rubric in this skill as a
psychometric instrument, establish stable score meaning across disciplines, or
authorize use in consequential decisions.

As of the dated source review, arXiv and the official project repository were
the verified primary publication records. No peer-reviewed publication status
was verified. Cite it as an arXiv preprint unless a later primary record is
checked. See `references/source_ledger.md`.

## Relationship to this skill

This skill borrows the useful discipline of:

1. defining what is being assessed;
2. grounding judgments in traceable literature and work evidence;
3. separating soundness-like questions from contribution-like questions; and
4. auditing whether generated feedback covers expert concerns.

It does not reproduce ScholarEval's model pipeline, prompts, retrieval system,
dataset, or reported metrics. The bundled scripts do not call ScholarEval,
search the web, invoke a model, or evaluate private documents.

The template is a **locally governed developmental rubric**. Its default
construct is:

> Traceable support for a scholarly work's claims and methods: the degree to
> which a work states a bounded question, situates its contribution, uses
> fit-for-purpose methods, aligns analysis with claims, and documents
> transparent and responsible practices using traceable evidence.

This construct must be reviewed and adapted by relevant disciplinary experts.

## Five template criteria

### 1. Question and scope

Review:

- a clear, bounded question or objective;
- significance rationale appropriate to the field and work stage;
- assumptions, boundary conditions, and success conditions; and
- feasibility of the proposed or reported scope.

Do not treat fashionable topics, institutional affiliation, or venue
expectations as evidence of significance.

### 2. Literature grounding and contribution claim

Review:

- source-selection or search boundaries;
- engagement with relevant and contrary evidence;
- traceable primary sources for comparison claims;
- comparison dimensions used to define the contribution; and
- limits on novelty or advancement claims.

Failure to find prior work does not establish novelty. Search coverage varies by
database, language, date, indexing, terminology, discipline, and access.

### 3. Method and design fit

Review:

- alignment between question, design, data or materials, and method;
- sampling, corpus, inclusion, exclusion, and measurement choices;
- alternatives and design rationale;
- validity threats, bias, and mitigation;
- ethics, consent, privacy, safety, and governance; and
- detail sufficient for appropriate checking or reproduction.

Use discipline-specific reporting and methods standards. Do not reward
complexity for its own sake.

### 4. Analysis, claims, and uncertainty

Review:

- fit of analytical methods to data and inferential target;
- assumptions and diagnostics;
- robustness, sensitivity, negative cases, and alternative explanations;
- appropriate statistical or qualitative uncertainty;
- alignment between results and claims; and
- explicit limits on generalization and causal language.

The rubric's `uncertainty` value is a rater-supplied bounded judgment range. It
is not a sampling confidence interval, posterior interval, or standard error.

### 5. Transparency, integrity, and reproducibility

Review:

- complete reporting, provenance, and stable evidence locators;
- protocols, registrations, data, code, materials, and justified restrictions;
- negative, null, and contradictory findings where relevant;
- conflicts, limitations, corrections, and research-integrity safeguards;
- accessible communication; and
- transparent attribution of contributions.

Open practice is not an absolute requirement when privacy, consent, safety,
security, Indigenous data governance, commercial constraints, or other
legitimate restrictions apply. Assess whether restrictions are justified and
whether safe access or metadata alternatives are provided.

## Scale semantics

The template uses an ordinal 0–4 scale:

- **0 — observed lack of support**
- **1 — limited support**
- **2 — mixed support**
- **3 — substantial support**
- **4 — strong support**

These are evidence anchors, not labels of a person or universal levels of
research quality. The rubric defines criterion-specific anchors. Raters must use
the anchor text, not intuition about what a number “usually means.”

Do not convert the score to:

- accept/reject or publication readiness;
- exceptional/poor labels;
- predicted success or impact;
- person ranking; or
- funding, hiring, promotion, tenure, admissions, award, or discipline advice.

## Rating statuses

Each criterion has exactly one status:

- `rated`: score, uncertainty, evidence identifiers, and rationale reference
  are required;
- `missing`: evidence needed for assessment is absent or unavailable; score and
  uncertainty are null; or
- `not_applicable`: the criterion does not apply to this work under a documented
  rationale; score and uncertainty are null.

A rated zero must cite inspected evidence demonstrating lack of support or a
contradiction. An inaccessible section or unassessed evidence is `missing`, not
zero. Do not encode missing or not-applicable as zero.

## Transparent score math

Numeric averaging additionally assumes meaningful spacing between anchors and
compensatory tradeoffs between criteria. Ordinal labels alone do not justify
these assumptions. Use a composite only when the local rubric owner documents
them for the stated developmental purpose; otherwise retain criterion findings.

For rated criteria \(R\), score \(s_i\), and predeclared weight \(w_i\):

\[
\text{descriptive score}
=
\frac{\sum_{i \in R} w_i s_i}
     {\sum_{i \in R} w_i}
\]

The sc

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

