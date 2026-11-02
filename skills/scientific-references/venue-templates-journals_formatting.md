---
id: sciref-venue-templates-journals-formatting
name: "Scientific Ref: Journal Formatting Requirements"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (venue-templates): Journal Formatting Requirements"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "venue templates journals formatting"
  - "journal formatting requirements"
keywords:
  - "venue"
  - "templates"
  - "journals"
  - "formatting"
  - "specialized"
  - "scientific"
  - "reference"
  - "journal"
---

# Journal Formatting Requirements

Journal requirements vary by journal, article type, and submission stage. Publisher-wide conventions are useful for discovery but do not replace the target journal's current Guide for Authors.

**Reviewed:** 2026-10-01

## Verification Workflow

Before formatting:

1. identify the exact journal and article type;
2. open the journal's official author instructions;
3. determine whether the initial submission is format-flexible;
4. distinguish initial-submission rules from revised/final-production rules;
5. record length, abstract, display-item, data/code, reporting, and disclosure requirements; and
6. use the official template only when the journal requires or recommends it.

Do not apply rules from a flagship journal to every journal in the same publisher family.

## Nature Portfolio

### Nature

**Official resources**

- Author hub: https://www.nature.com/nature/for-authors
- Initial submission: https://www.nature.com/nature/for-authors/initial-submission
- Formatting guide: https://www.nature.com/nature/for-authors/formatting-guide

Nature states that initial submissions are flexible in format within reason. Authors are encouraged to combine text and figures in one Word file or PDF for review. The formatting guide describes article formats and typical final print lengths; these are not a generic “five-page submission limit.”

For Articles, the formatting guide describes:

- a fully referenced summary paragraph, ideally no more than 200 words;
- typical final print lengths that differ for physical-science and biological/clinical/social-science papers; and
- detailed figure, reference, methods, and reporting requirements.

Use `assets/journals/nature_article.tex` only as a writing scaffold. It is not an official Nature class or a guarantee of compliance.

### Other Nature Portfolio journals

Open the exact journal's **Submission Guidelines**. Some Nature Portfolio journals explicitly accept PDF, Word, or compiled TeX/LaTeX for a format-flexible initial submission, while others provide journal-specific structure and final-format instructions.

Do not assume that Nature, Nature Communications, Scientific Reports, and subject journals share one word limit or template.

## Science Family

**Official starting point**

- Science author instructions: https://www.science.org/content/page/instructions-authors

Resolve the exact journal and contribution type before applying length, abstract, reference, or supplementary-material rules. Fresh Science author-page retrieval was blocked in this audit; this skill therefore does not assert a current Science word or reference limit. Science, Science Advances, and specialist journals have different workflows.

No Science template is bundled in this skill. Use the official instructions and files provided by the target journal.

## PLOS

**Official resources**

- PLOS ONE submission guidelines: https://journals.plos.org/plosone/s/submission-guidelines
- PLOS ONE LaTeX package: https://journals.plos.org/plosone/s/latex

PLOS supplies an official LaTeX package and BibTeX style for LaTeX submissions. Follow the target PLOS journal's package and upload instructions; manuscript and figure-file handling can be specific to the journal and submission stage.

`assets/journals/plos_one.tex` is a drafting scaffold, not a substitute for the current PLOS package.

## Cell Press

**Official starting point**

- Cell author resources: https://www.cell.com/cell/authors

Check the exact journal and article type for:

- Summary and Highlights limits;
- graphical abstract or eTOC requirements;
- STAR Methods or other methods structure;
- Resource Availability and Lead Contact sections;
- Limitations of the Study;
- data/code availability declarations; and
- generative-AI or AI-assisted-technology declarations.

No Cell Press LaTeX template is bundled. Use `references/cell_press_style.md` for writing guidance and the official author resources for submission requirements. Current Cell reference citations are numbered superscripts, not the older author-year style.

## IEEE

**Official resources**

- IEEE journal templates: https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/authoring-tools-and-templates/tools-for-ieee-authors/ieee-article-templates
- IEEE Template Selector: https://template-selector.ieee.org/

Use the Template Selector to resolve the publication-specific Word or LaTeX package. Page limits, review layout, biographies, open-access declarations, and overlength charges vary by journal.

No IEEE template is bundled in this skill.

## ACM

**Official resources**

- ACM LaTeX preparation: https://authors.acm.org/proceedings/production-information/preparing-your-article-with-latex
- ACM journals submission process: https://authors.acm.org/journals/submission-process

ACM uses the `acmart` class with publication-specific options and the TAPS production workflow. The review format selected by a conference or journal may differ from the final TAPS output.

No ACM template is bundled. Use the official ACM Master Article Template and the target publication's instructions.

## Elsevier

**Official resource**

- LaTeX instructions: https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions

Elsevier documents the `elsarticle` class and provides separate CAS single- and double-column templates. The exact journal's Guide for Authors determines word limits, article structure, reference style, highlights, graphical abstracts, and whether PDF-only initial submission is accepted.

Bundled examples:

| File | Citation mode | Matching bibliography style |
|---|---|---|
| `assets/journals/elsarticle-template-num.tex` | numeric | `elsarticle-num.bst` |
| `assets/journals/elsarticle-template-num-names.tex` | numeric with author names | `elsarticle-num-names.bst` |
| `assets/journals/elsarticle-template-harv.tex` | author-year | `elsarticle-harv.bst` |

The six bundled Elsevier files match the official CTAN `elsarticle` 3.5 bundle (2026-01-09); their LPPL notices are preserved. `elsarticle-num-names.bst` supports author names with numeric citations; sorting and compression are separate natbib options. The plain numeric style does not provide author metadata for `\citet`; use the numeric-with-names style when textual author citations are required. The current upstream sample repeats the label `fig1` for a table and figure: assign unique labels in your working copy. The class itself is not bundled. 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

