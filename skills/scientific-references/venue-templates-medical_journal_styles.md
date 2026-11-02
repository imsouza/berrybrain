---
id: sciref-venue-templates-medical-journal-styles
name: "Scientific Ref: Medical Journal Writing Style"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (venue-templates): Medical Journal Writing Style"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "venue templates medical journal styles"
  - "medical journal writing style"
keywords:
  - "venue"
  - "templates"
  - "medical"
  - "journal"
  - "styles"
  - "specialized"
  - "scientific"
  - "reference"
---

# Medical Journal Writing Style

**Reviewed: 2026-10-01.** Resolve journal, article type, study design, and stage
before applying a numerical limit. A publisher family is not one author contract.

## Official author sources

| Target | Source and verification scope |
|---|---|
| NEJM | https://www.nejm.org/author-center — fresh retrieval returned navigation rather than complete article-type instructions; obtain the current full instructions before setting a word limit |
| The Lancet | https://www.thelancet.com/lancet/information-for-authors — the August 2026 [Information for Authors](https://www.thelancet.com/pb-assets/Lancet/authors/tl-info-for-authors-1787150940677.pdf) specifies a five-paragraph summary up to 300 words for original research and requires Research in Context; check the exact article category |
| JAMA | https://jamanetwork.com/journals/jama/pages/instructions-for-authors — original-data abstracts have a 350-word maximum and specified headings |
| The BMJ | https://www.bmj.com/about-bmj/resources-authors/article-types — research has no fixed main-text word limit; abstracts ordinarily use 250–300 words, with up to 400 for CONSORT/PRISMA reporting |
| Annals of Internal Medicine | https://www.acpjournals.org/journal/aim/authors — retrieval returned site navigation, not usable current instructions; verify article type before setting limits |

The previous generic 250/300/350/300/325 abstract table mixed article types and
unverified rules. Do not copy its numbers into a submission. JAMA's original
investigation requirements do not apply to every JAMA Network journal or section.

## Abstract structure

Choose the actual journal's headings; the following are writing patterns, not
universal required labels:

- **NEJM-style research:** Background, Methods, Results, Conclusions.
- **Lancet-style research:** Background, Methods, Findings, Interpretation, Funding.
- **JAMA original data:** Importance; Objective; Design, Setting, and Participants;
  Interventions or Exposures; Main Outcomes and Measures; Results; Conclusions
  and Relevance; applicable trial registration.
- **The BMJ research:** Objectives, Design, Setting, Participants, Interventions
  where relevant, Main Outcome Measures, Results, Conclusions, Trial Registration.

Summary boxes such as The BMJ's “What is already known” and “What this study adds”
are distinct from the structured abstract. Do not import BMJ Open's template or
its separate strengths-and-limitations box into The BMJ without checking.

Use `assets/examples/medical_structured_abstract.md` (relative to the skill root)
for placeholder-based drafting. It intentionally contains no simulated drug
trial outcomes that could be mistaken for published clinical evidence.

## Match claims to evidence

Write the precise population, intervention/exposure, comparator, outcome, time
horizon, and estimand. Randomization supports causal interpretation when its
assumptions and execution hold; it does not automatically remove bias from
nonadherence, missing outcomes, outcome measurement, or selective reporting.
Small trials are not automatically “associational” merely because of size.

For observational analyses, use association language unless a causal estimand,
identification assumptions, design, and sensitivity analysis justify a carefully
qualified causal interpretation. Do not claim benefit from a case report.

A non-significant result does not establish equivalence or “similar safety.”
Describe the interval and which important benefit/harm values remain compatible
with it. Equivalence/noninferiority requires the relevant design, margin, and
analysis. Avoid stock claims about residual confounding as the main limitation
of a randomized intention-to-treat contrast; identify the actual source of bias.

## Numerical reporting

- Give group denominators, event counts, follow-up, effect estimates, and
  uncertainty appropriate to the prespecified analysis.
- For binary outcomes, provide absolute risks/differences alongside relative
  measures when estimable. A hazard ratio is not a risk ratio.
- State the confidence level and whether intervals/tests are adjusted for
  multiplicity. A point estimate plus a P value is insufficient.
- Report exact P values where practical and follow the journal's small-value
  convention. Statistical significance alone does not establish clinical value.
- Give NNT/NNH only when meaningful from an absolute effect at a stated time
  horizon and baseline-risk context. Do not invert a hazard ratio or a
  significance threshold to obtain NNT. If the risk-difference interval crosses
  zero, the reciprocal interval is discontinuous; do not invent a finite range.
- Report prespecified outcomes regardless of direction or significance. Label
  exploratory and post hoc analyses. Report adverse events systematically.

## Manuscript workflow

1. Establish the clinical question and the gap the design addresses.
2. Describe study design, setting, participants, recruitment, intervention or
   exposure, outcomes, sample-size rationale, and prespecified analysis.
3. Report ethics review/consent or the documented exemption, and registration
   where required. Never invent an approval number, funding source, or registry ID.
4. Show participant flow and analysis populations, including missing outcomes.
   Loss to follow-up does not automatically justify excluding randomized people
   from an intention-to-treat analysis.
5. Report results in the prespecified hierarchy, with uncertainty and harms.
6. Discuss strengths, bias, precision, generalizability, and clinical relevance
   without extending conclusions beyond the data.

For diagnostic and prediction studies, specify the intended use, reference
standard/outcome timing, validation design, calibration, discrimination, and
threshold-dependent tradeoffs. A high AUC alone does not show patient benefit.

## Reporting guidelines

Use the current guideline and the applicable design extension. Check the
journal's requested checklist version rather than silently substituting one.

| Design | Current primary starting point |
|---|---|
| Randomized trial results | [CONSORT 2025](https://www.consort-spirit.org/), 30-item core checklist plus flow diagram |
| Randomized trial protocol | [SPIRIT 2025](https://www.consort-spirit.org/), 34-item core checklist |
| Observational cohort/case-control/cross-sectional | [STROBE](https://www.strobe-statement.org/), 22 items |
| Systematic review/meta-analysis | [PRISMA 2020]

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

