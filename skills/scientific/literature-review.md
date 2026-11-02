---
id: sci-literature-review
name: "Scientific: literature-review"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Conducts systematic, scoping, and narrative literature reviews using PubMed, arXiv, bioRxiv, Semantic Scholar, and other appropriate sources. Use for research synthesis, reproducible literature searches, screening, citation checking, or preparing Markdown and PDF reviews. Tracks "
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "literature review"
  - "literatura revisao"
  - "literature-review"
keywords:
  - "literature"
  - "review"
  - "literatura"
  - "revisao"
  - "conducts"
  - "systematic"
  - "scoping"
  - "narrative"
  - "reviews"
---

# Literature Review

## Overview

Conduct systematic, comprehensive literature reviews following rigorous academic methodology. Search multiple literature databases, synthesize findings thematically, verify all citations for accuracy, and generate professional output documents in markdown and PDF formats.

Use discipline-appropriate bibliographic databases for the reproducible search, with **parallel-web** (`parallel-cli search`) for scoping and supplementary discovery. Ranked web results and extracted excerpts cannot establish exhaustive coverage or substitute for full-text assessment. Bundled scripts process normalized records, check DOI registration, and render documents; they do not run a complete systematic review automatically.

## When to Use This Skill

Use this skill when:
- Conducting a systematic literature review for research or publication
- Synthesizing current knowledge on a specific topic across multiple sources
- Performing meta-analysis or scoping reviews
- Writing the literature review section of a research paper or thesis
- Investigating the state of the art in a research domain
- Identifying research gaps and future directions
- Requiring verified citations and professional formatting

## Figures and PRISMA reporting

For systematic reviews, use the appropriate [PRISMA 2020 flow template](https://www.prisma-statement.org/prisma-2020-flow-diagram) and reconciled screening counts. Distinguish records, reports, and studies, including reports not retrieved and reasons for full-text exclusions. Use tables or deterministic plotting for exact numbers, effect estimates, and risk-of-bias results.

Conceptual schematics are optional. The bundled generator needs `OPENROUTER_API_KEY` and creates a PNG draft with up to two generation/review iterations:

```bash
python scripts/generate_schematic.py "Conceptual evidence map; labels from the reviewed extraction table" \
  -o figures/evidence_map.png --doc-type journal --iterations 2
```

Generation uses OpenRouter's `POST /api/v1/images` with
`google/gemini-3.1-flash-image`; review uses `POST /api/v1/chat/completions` with
`google/gemini-3.7-flash`. The output path must end in `.png`. Inspect labels,
counts, arrows, and accessibility yourself: `success` means an image was saved,
whereas `quality_met`, `final_reviewed`, and `termination_reason` in the review
log describe the automated review. Neither proves scientific accuracy. A failed
refinement preserves the previous draft. Check current model availability before
running paid generation; do not fabricate study counts in an image prompt.

## Core Workflow

A literature review runs in seven phases, documented in full with commands and templates
in [references/core_workflow.md](references/core_workflow.md):

1. **Planning and scoping** — the question, inclusion and exclusion criteria, and scope.
2. **Systematic literature search** — multi-database searching with recorded queries.
3. **Screening and selection** — title/abstract then full-text screening with counts kept
   for the PRISMA flow.
4. **Data extraction and quality assessment** — structured extraction and risk-of-bias
   or quality appraisal.
5. **Synthesis and analysis** — thematic or quantitative synthesis across studies.
6. **Citation verification** — every citation checked against the actual source.
7. **Document generation** — assembling the review with a complete bibliography.

Record every search string and date as you go: a review that cannot reproduce its own
search is not systematic. Per-database search guidance and citation styles are in
[references/search_and_citation.md](references/search_and_citation.md), and a full worked
review is in [references/example_workflow.md](references/example_workflow.md).

## Best Practices

### Search Strategy
1. **Pilot the question**: Optionally use `parallel-cli search` for scoping, then test database queries against known eligible reports
2. **Choose complementary sources**: Justify database and registry coverage for the question; no fixed number of databases guarantees completeness
3. **Include preprint servers**: Captures latest unpublished findings
4. **Document everything**: Search strings, dates, result counts for reproducibility — save all parallel-cli output to `sources/`
5. **Test and refine**: Run pilot searches, review results, adjust search terms
6. **Preserve all eligible records**: Citation counts can order exploratory reading but must not determine eligibility or replace risk-of-bias assessment
7. **Verify retrieved content**: Extraction can be incomplete; obtain the actual full report, or record it as not retrieved

### Records, Reports, and Studies
1. **Deduplicate records, then link reports**: DOI/title deduplication removes repeated search hits; it does not identify every paper from the same study. Link preprints, journal articles, protocols, and follow-up reports using trial IDs, cohort descriptions, sites, and recruitment dates.
2. **Keep a study-to-report map**: Preserve each source and explain which report supplies each outcome; do not count overlapping participants twice in a meta-analysis.
3. **Reconcile PRISMA counts**: Track records screened, reports sought/not retrieved/assessed, reports excluded with reasons, and included studies separately. Report counts can exceed study counts. See the [Cochrane selection guidance](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-04).

### Screening and Selection
1. **Use clear criteria**: Document inclusion/exclusion criteria before screening
2. **Screen systematically**: Title → Abstract → Full text
3. **Document exclusions**: Record reasons for excluding studies
4. **Use independent eligibility decisions**: For systematic reviews, use two reviewers for final full-text eligibility and document disagreement resolution; disclose any single-reviewer limitation

### Synthesis
1. **Organize thematically**: Group by themes, NOT by individual studies
2. **Synthesize across studies**: Compare, contrast, identify patterns
3. **Be critical**: Evaluate quality and consistency of evidence
4. **Identify gaps**: Note what's missing or understudied

### Quality and Reproducibility
1. **Assess study quality**: Use appropriate quality assessment tools
2. **Verify citations and claims**: Run verify_citations.py for DOI registration/metadata, then compare the reference and the cited claim with the actual source
3. **Document methodology**: Provide enough detail for others to reproduce
4. **F

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

