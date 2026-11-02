---
id: sciref-venue-templates-reviewer-expectations
name: "Scientific Ref: Reviewer Expectations and Rebuttals"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (venue-templates): Reviewer Expectations and Rebuttals"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "venue templates reviewer expectations"
  - "reviewer expectations and rebuttals"
keywords:
  - "venue"
  - "templates"
  - "reviewer"
  - "expectations"
  - "specialized"
  - "scientific"
  - "reference"
---

# Reviewer Expectations and Rebuttals

**Reviewed: 2026-10-01.** This is a self-review aid, not a prediction of scores,
acceptance, reviewer counts, or turnaround times. Obtain the actual review form
for the venue, contribution type, and cycle.

## Primary sources

- Nature editorial criteria: https://www.nature.com/nature/for-authors/editorial-criteria-and-processes
- Cell author instructions: https://www.cell.com/cell/authors
- NeurIPS 2026 handbook: https://neurips.cc/Conferences/2026/MainTrackHandbook
- ICML 2026 instructions: https://icml.cc/Conferences/2026/AuthorInstructions
- ICLR 2026 guide: https://iclr.cc/Conferences/2026/AuthorGuide
- CVPR 2026 guidelines: https://cvpr.thecvf.com/Conferences/2026/AuthorGuidelines
- CHI 2026 review process: https://chi2026.acm.org/papers-review-process/
- ARR current call: https://aclrollingreview.org/cfp
- Medical reporting resources: `medical_journal_styles.md`

## Evaluate the contribution on its terms

| Contribution | Questions to ask |
|---|---|
| Multidisciplinary finding | Is its significance clear outside the specialty? Are claims supported by appropriate controls and uncertainty? |
| Mechanistic biology | Which alternatives does the design distinguish? Are perturbation, rescue, measurement, and replication appropriate? |
| Clinical research | Are design, estimand, population, precision, harms, bias, and applicability clear? |
| ML method or analysis | Are assumptions, comparisons, tuning, evaluation, and reproducibility adequate for the claim? |
| HCI | Does evidence support the stated empirical, design, theoretical, or methodological contribution? |
| NLP | Are tasks/languages, data, metrics, human evaluation where relevant, and failure modes properly characterized? |
| Mining/IR systems | Are scale, resource use, effectiveness, and real-world claims evaluated under stated conditions? |

Do not assign invented fixed “Critical/High/Moderate” official weights. Scientific
soundness is not demonstrated by checklist completion, a large sample alone, a
small P value, animal work, or a state-of-the-art benchmark win. Novel insight,
negative findings, theoretical work, and other contributions may be in scope.

## Common substantive concerns

- Claims exceed the design, analysis, data coverage, or uncertainty.
- Important controls, assumptions, alternative explanations, or baselines are missing.
- Data splitting, tuning, exclusions, missingness, or outcome selection compromise inference.
- Methods are insufficiently specified for interpretation or reproduction.
- Related work, overlapping submissions, or access restrictions are misrepresented.
- Ethical review, consent, disclosures, or privacy protections are inadequately reported.

A failure to beat a benchmark, a small numeric improvement, an older comparator,
or one dataset is not by itself a universal rejection rule. Judge whether the
evidence is adequate for the actual claim.

## Rebuttal contract comes first

Check the response format, anonymity, word/page limit, permitted links, new-data
policy, revision policy, and deadline before drafting. Examples:

- ICML 2026 permits author responses but no revised paper during author feedback;
  its instructions explicitly encourage prioritizing substantive concerns.
- CVPR 2026 uses a one-page anonymous rebuttal and restricts external links and
  new contributions or unrequested experimental results.
- ICLR 2026 allows documented revisions under its discussion rules.
- CHI 2026 has a specified revise-and-resubmit process for invited papers.

A general suggestion to “do every requested experiment now” must not override
these rules or the authors' research scope.

## Evidence-based response workflow

1. Separate factual misunderstandings, unclear exposition, methodological
   problems, and requests for expanded scope.
2. Identify what can be corrected, clarified, or tested within the allowed stage.
3. Give the evidence and exact manuscript location for each material response.
4. Label new analyses, planned work, and untested hypotheses distinctly.
5. State remaining limitations without promising nonexistent results.
6. Check all response and supplementary files for identity leaks when required.

Illustrative response pattern:

```text
Concern: [reviewer's substantive point]
Response: [agreement, clarification, or justified disagreement]
Evidence: [existing analysis or actually completed allowed new analysis]
Change: [specific text/table/figure and location, if revisions are allowed]
Remaining limit: [what the evidence still does not establish]
```

For a precision concern, give the prespecified sample-size rationale and the
observed confidence interval. Do not use observed/post hoc power or the favorable
direction of a noisy estimate as proof of adequate evidence. For a method concern,
show the relevant diagnostic or bounded correction; do not fabricate a rescue
experiment, deployment, participant quotation, or benchmark comparison.

## Human and policy responsibilities

Authors remain responsible for accurate responses and submission decisions.
Follow the venue's rules on AI use and confidential material. This guide does not
authorize an agent to submit a review, contact reviewers, or upload a manuscript.
Journal-specific policies may restrict permitted assistance; see the medical
reference for JAMA's current exceptions.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

