---
id: sciref-venue-templates-current-sources
name: "Scientific Ref: Source and execution ledger"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (venue-templates): Source and execution ledger"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "venue templates current sources"
  - "source and execution ledger"
keywords:
  - "venue"
  - "templates"
  - "current"
  - "sources"
  - "specialized"
  - "scientific"
  - "reference"
  - "source"
---

# Source and execution ledger

Reviewed **2026-10-01**. These are dated snapshots, not a promise that the next
submission cycle has identical rules. This skill has no remote API client:
its Python helpers only read local templates/PDFs and invoke Poppler. Publisher
and conference links are human-facing documentation or template downloads, not
submission endpoints.

## Journal sources

| Primary source | Verified scope and correction |
|---|---|
| [Nature initial submissions](https://www.nature.com/nature/for-authors/initial-submission), [formatting guide](https://www.nature.com/nature/for-authors/formatting-guide) | Format-flexible initial review within reason; referenced Article summary ideally at most 200 words; Methods in the main file after legends; separate funding statement. Published print lengths are not one universal submission cap. |
| [PLOS ONE submission guidelines](https://journals.plos.org/plosone/s/submission-guidelines), [LaTeX instructions](https://journals.plos.org/plosone/s/latex) | Abstract at most 300 words, no citations; double-spaced single-column manuscript with continuous line/page numbering. The official package controls actual LaTeX submission. |
| [Cell revision instructions](https://www.cell.com/cell/information-for-authors/revise-manuscript), [final instructions](https://www.cell.com/cell/information-for-authors/final-submission), [linked final-file checklist](https://www.cell.com/pb-assets/journals/EM/MasterFFCs/CELLFFC-1790092533770.pdf) | Summary at most 150 words; up to four Highlights of at most 85 characters each; eTOC/In Brief at most 50 words, two sentences, third person. References use numbered superscripts. Resource Availability, STAR Methods, and the Key Resources Table have distinct roles. Final graphical abstract: 1200 × 1200 pixels at 300 dpi, TIFF/PDF/JPG. These are Cell rules, not all Cell Press journals. |
| [STAR Methods resources](https://star-methods.com/) | Current author tool and resources for the Key Resources Table; no automated submission integration tested. |
| [Elsevier LaTeX instructions](https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions), [CTAN elsarticle](https://ctan.org/pkg/elsarticle) | Official elsarticle 3.5 (2026-01-09). All three bundled `.tex` samples and three `.bst` files match this release; LPPL notices retained. Editorial Manager source files need a single folder level. Journal instructions select class and citation mode. |
| [JAMA author instructions](https://jamanetwork.com/journals/jama/pages/instructions-for-authors) | Original-data abstract maximum 350 words, prescribed headings; article-type rules differ. AI drafting restrictions for Opinion, Letters, and Online Comments and the advice against AI-generated/formatted references are venue-specific. |
| [The BMJ article types](https://www.bmj.com/about-bmj/resources-authors/article-types) | No fixed research main-text word cap; abstract normally 250–300 words, up to 400 for CONSORT/PRISMA reporting. |
| [The Lancet author hub](https://www.thelancet.com/lancet/information-for-authors), [August 2026 instructions](https://www.thelancet.com/pb-assets/Lancet/authors/tl-info-for-authors-1787150940677.pdf) | Original research has a five-paragraph summary of at most 300 words and a Research in Context panel; apply the exact article category rather than publisher-wide limits. |

Discovery hubs were reviewed for their role, not treated as uniform formatting
rules: [IEEE templates](https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/authoring-tools-and-templates/tools-for-ieee-authors/ieee-article-templates/),
[BMC](https://link.springer.com/brands/bmc/why-publish-with-bmc),
[Frontiers](https://www.frontiersin.org/guidelines/author-guidelines),
[PNAS](https://www.pnas.org/author-center), and [APS](https://journals.aps.org/authors).

## Conference sources

| Primary source | Verified scope |
|---|---|
| [NeurIPS 2026 CFP](https://neurips.cc/Conferences/2026/CallForPapers), [Main Track Handbook](https://neurips.cc/Conferences/2026/MainTrackHandbook) | Initial main content 9 pages, camera-ready 10; references, technical appendices, and checklist excluded. Review omits acknowledgments. The official author ZIP provides `neurips_2026.sty` and `checklist.tex`; default submission mode is anonymous. No universal separately titled Broader Impacts section. |
| [ICML 2026 author instructions](https://icml.cc/Conferences/2026/AuthorInstructions), [CFP](https://icml.cc/Conferences/2026/CallForPapers) | Initial 8 pages, final 9; references/appendices additional in the same PDF. Anonymous code branch freezes at deadline. No revised manuscript during author feedback. |
| [ICLR 2026 author guide](https://iclr.cc/Conferences/2026/AuthorGuide) | Initial 9 pages, discussion/camera-ready 10; references/appendices excluded. This is a 2026 snapshot, not a verified 2027 rule. |
| [CVPR 2026 author guidelines](https://cvpr.thecvf.com/Conferences/2026/AuthorGuidelines) | Initial 8 pages plus cited references; anonymous one-page rebuttal, no external links, new contributions/unrequested experimental results discouraged. |
| [ARR current CFP](https://aclrollingreview.org/cfp) | 8/4-page long/short content; required Limitations after the conclusion and outside that count. Reviews are not public simply because ARR uses OpenReview. Check current October 2026 service/capacity policy. |
| [CHI 2026 papers](https://chi2026.acm.org/authors/papers/), [publication formats](https://chi2026.acm.org/chi-publication-formats/), [review process](https://chi2026.acm.org/papers-review-process/) | Single-column anonymous `acmart` manuscript for review; current TAPS production. Do not use the old `sigchi` option. |
| [KDD 2026 research CFP](https://kdd2026.kdd.org/research-track-call-for-papers/) | Research track uses `sigconf,anonymous,review`; other tracks have their own instructions. Theory need not claim empirical state of the art. |

Other families remain discovery links with no cached limits. The broken USENIX
and ISMB generic URLs were replaced with [USENIX conferences](https://www.usenix.org/conferences/security)
and [ISMB series](https://www.iscb.org/conferences-events/about-ismb); EMNLP resolves
through [SIGDAT](https://sigdat.org/). AAAI, IJCAI, KDD, SIGIR, RECOMB, PSB, and IEEE
conference/ICRA hubs were checked; select the actual year's call before drafting.

## Grants and reporting

- [NSF PAPPG](https://www.nsf.gov/policies/pappg) and [Cha

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

