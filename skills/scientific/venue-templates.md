---
id: sci-venue-templates
name: "Scientific: venue-templates"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Prepares journal manuscripts, conference papers, research posters, and grant documents using venue-specific formatting guidance and bundled LaTeX scaffolds. Supports selecting an official template, checking current page or anonymity rules, adapting academic writing to a venue, or"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "venue templates"
  - "venue-templates"
keywords:
  - "venue"
  - "templates"
  - "prepares"
  - "journal"
  - "manuscripts"
  - "conference"
  - "papers"
  - "research"
---

# Venue Templates

Prepare publication and funding documents without treating stale formatting details as authoritative. This skill combines:

- a verification-first workflow for current venue rules;
- bundled LaTeX scaffolds for a small, explicit set of document types;
- writing-style and reviewer-expectation guides; and
- local helpers for discovering, copying, and inspecting templates.

## Mandatory Currency Rule

Venue requirements are time-sensitive. Before giving exact page limits, deadlines, style-file names, anonymity rules, or required sections:

1. Identify the exact venue, year or funding cycle, track, and article or proposal type.
2. Open the official author instructions, call, solicitation, notice of funding opportunity (NOFO), or policy guide.
3. Record the source URL and the date checked.
4. Distinguish initial submission, revision/rebuttal, and camera-ready rules.
5. Treat bundled files as scaffolds unless this skill explicitly says they are a copy of an official template.

Never infer a current style-file name by changing the year in an old filename. Never present a generic scaffold as an official venue template.

## When to Use

Use this skill for:

- locating official journal or conference author instructions;
- checking page limits, required sections, anonymity, supplemental-material rules, or citation style;
- choosing and adapting a bundled LaTeX scaffold;
- preparing NSF, NIH, DOE, DARPA, or foundation proposal documents;
- designing a research poster after checking event-specific dimensions;
- adapting prose to a venue's audience and reviewer expectations; or
- inspecting a PDF's page count and embedded fonts.

## Verification-First Workflow

### 1. Resolve the exact target

Ask for or derive:

- venue or funding agency;
- year/cycle and track;
- document type, such as research article, short paper, main track, R01, or R21;
- submission stage; and
- authoring format, such as LaTeX or Word.

Do not combine rules from similarly named venues or tracks.

### 2. Consult the right reference

| Need | Reference |
|---|---|
| Journal submission and official publisher resources | `references/journals_formatting.md` |
| Conference rules and 2026 verified snapshots | `references/conferences_formatting.md` |
| Poster sizes, layout, and accessibility | `references/posters_guidelines.md` |
| NSF, NIH, DOE, DARPA, and foundation proposals | `references/grants_requirements.md` |
| Cross-venue writing comparison | `references/venue_writing_styles.md` |
| Nature and Science writing | `references/nature_science_style.md` |
| Cell Press writing | `references/cell_press_style.md` |
| Medical journal writing | `references/medical_journal_styles.md` |
| ML and computer-vision conference writing | `references/ml_conference_style.md` |
| ACL, EMNLP, CHI, and other CS writing | `references/cs_conference_style.md` |
| Review criteria and rebuttals | `references/reviewer_expectations.md` |

Reference files summarize rules but do not override the current official source.

### 3. Capture a compliance note

Before editing, write a short note in the working document or task log:

```text
Target: ICML 2026 main track, initial submission
Official source: https://icml.cc/Conferences/2026/AuthorInstructions
Checked: 2026-10-01
Main-text limit: 8 pages
References/appendices: additional pages allowed in the same PDF
Anonymity: required
Official template: ICML 2026 style package linked by the author instructions
```

This makes later validation reproducible.

### 4. Start from the official template

For annual conferences and publisher-managed workflows:

1. Download the template from the official source.
2. Keep its class/style files unchanged.
3. Add content without overriding margins, font sizes, spacing, or headers.
4. Use a bundled scaffold only for drafting or when the official source explicitly permits it.

For grants, many components are entered or uploaded separately. Do not submit a combined bundled `.tex` file as if it were an agency-issued form.

### 5. Validate manually and mechanically

Verify at least:

- main-text and total-file page rules;
- font, margin, line-spacing, and paper-size rules;
- anonymity and metadata;
- required sections, statements, checklists, and disclosures;
- figure/table placement and accessibility;
- reference and supplemental-material treatment; and
- source-package and PDF requirements.

The helper counts PDF pages and reads Poppler font-embedding flags. It reports
nonembedded fonts as failures, but cannot prove margin, font-size, excluded-section,
or anonymity compliance. A zero exit status means no automated failure was found;
manual and skipped inspections still require attention.

## Bundled Assets

The repository intentionally bundles only the following templates. Other venues listed in references require an official external template.

### Journal and conference scaffolds

| File | Status |
|---|---|
| `assets/journals/nature_article.tex` | Generic Nature-oriented writing scaffold; not an official Nature template |
| `assets/journals/plos_one.tex` | PLOS ONE-oriented scaffold; compare with the current official PLOS LaTeX package |
| `assets/journals/neurips_article.tex` | NeurIPS 2026 wrapper; requires the official `neurips_2026.sty` |
| `assets/journals/elsarticle-template-num.tex` | Elsevier `elsarticle` numeric example |
| `assets/journals/elsarticle-template-num-names.tex` | Elsevier `elsarticle` numbered/name example |
| `assets/journals/elsarticle-template-harv.tex` | Elsevier `elsarticle` author-year example |

The matching Elsevier `.bst` files are in `assets/journals/`.

### Grant scaffolds

| File | Status |
|---|---|
| `assets/grants/nsf_proposal_template.tex` | Planning scaffold for common NSF narrative components; upload components separately |
| `assets/grants/nih_specific_aims.tex` | Writing scaffold for a one-page NIH Specific Aims attachment |

Use SciENcv and agency-provided common forms where required. Do not recreate biosketch or current-support forms in LaTeX. NSF DMSPs now use the Research.gov tool under Supplement 2; the bundled narrative is only a planning aid.

### Poster scaffold

| File | Status |
|---|---|
| `assets/posters/beamerposter_academic.tex` | Venue-agnostic beamerposter scaffold; set dimensions from the event's current presenter instructions |

## Common Workflows

### Annual conference paper

1. Open `references/conferences_formatting.md`.
2. Follow the official link for the exact year and track.
3. Download

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

