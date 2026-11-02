---
id: sciref-scientific-visualization-journal-requirements
name: "Scientific Ref: Publisher and Journal Figure Snapshots"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-visualization): Publisher and Journal Figure Snapshots"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific visualization journal requirements"
  - "cientifico visualization journal requirements"
  - "publisher and journal figure snapshots"
keywords:
  - "scientific"
  - "visualization"
  - "journal"
  - "requirements"
  - "cientifico"
  - "specialized"
  - "reference"
  - "publisher"
---

# Publisher and Journal Figure Snapshots

Reviewed 2026-10-01 against official pages, except the explicitly historical Science snapshot below. Requirements are date-sensitive and often depend on the journal, article type, figure type, and submission phase. Verify the live target-journal page before submission. Source IDs resolve in `sources.md`.

The machine-readable subset in `assets/publisher_profiles.json` is for planning and deterministic screening only. `scripts/export_plan.py` never claims compliance.

## Nature (flagship journal)

**Scope:** `Nature` final submission after acceptance in principle, not all Nature Portfolio journals [NATURE-FINAL] [NATURE-FIG].

- Standard widths: 89 mm single column, 183 mm double column; 120-136 mm is possible for one-and-a-half columns.
- Full page depth: 247 mm.
- Panels: lowercase bold upright `a`, `b`, `c`, 8 pt.
- Other text: 5-7 pt at final size; Helvetica or Arial preferred.
- Keep text and line art editable; do not outline or rasterize them.
- Preferred line/graph containers include AI, PostScript, vector EPS, and PDF.
- Preferred raster source: layered PSD or TIFF. The final-submission page states 300-600 dpi for photographs; minimum 300 dpi at maximum use size.
- The newer research-figure guide recommends export images at 450 dpi or above because online proofs top out at 450 dpi. This is a recommendation layered on the final-submission minimum, not a universal 450 dpi rule.
- RGB is recommended; final print conversion may use CMYK.
- Type 42 fonts are requested. The figure guide explicitly gives `matplotlib.rcParams["pdf.fonttype"] = 42`.
- High-quality JPEG can be accepted when it is the only option for a photograph. Therefore, “Nature never accepts JPEG” is false.
- Extended Data has different rules: RGB, maximum 300 ppi, maximum 10 MB, and JPEG preferred with TIFF/EPS alternatives.

Do not apply these flagship rules automatically to Nature Communications, Scientific Reports, npj journals, or Nature Reviews; each has its own page.

## Science (AAAS flagship journal)

**Scope:** historical `Science` snapshot accessed 2026-07-23, with separate initial and revised stages [SCIENCE-INITIAL] [SCIENCE-REVISED]. Both pages blocked direct and fresh extraction on 2026-10-01. The numbers below remain provisional until live instructions are checked.

### Initial submission

- A single manuscript file with embedded figures is preferred.
- Figures should be 300 dpi for review.
- Printed widths are usually 5.7 cm (one column), 12.1 cm (two columns), or 18.4 cm (three columns).
- Vector creation is preferred.
- Use sans serif, preferably Helvetica. Lettering should be about 7 pt after reduction and no smaller than 5 pt.
- Avoid red/green combinations and similar hues as sole identifiers; add shape/texture where needed.
- Scales should not extend beyond the plotted data merely as empty range.

### Revised manuscript

- Upload each figure separately.
- Preferred vector formats: PDF, EPS, or AI.
- Raster illustrations/diagrams and photographs/microscopy: TIFF.
- Vector/raster combinations: PDF or EPS.
- Line art without a vector original: at least 300 dpi at final size, preferably higher.
- Color and grayscale images: at least 300 dpi at final size.
- Upsampling is not permitted.
- PowerPoint and figures embedded in Word are not accepted at this stage.

The 2026-07-23 snapshot did **not** state the older blanket “1,000 dpi line art / 600 dpi combination” numbers that this skill previously claimed.

Science Advances and other AAAS journals publish separate figure guides; do not reuse the flagship profile without checking.

## Cell Press

**Scope:** general Cell Press figure page; exceptions are explicitly listed for STAR Protocols and `Cell` Leading Edge [CELL-FIG].

### Initial submission and review

- Cell Press accepts a wide range of formats, sizes, and resolutions.
- Figures may be embedded or uploaded separately.
- Individual 1-2 MB files are recommended for reviewer convenience.

### Final production

- Upload each main figure as one separate file containing all its panels; keep titles/legends in the manuscript.
- Recommended overall maximum: 16.5 × 20 cm. This is framed as a recommendation.
- Two-column article widths: 8.5 cm, 11.4 cm, and 17.4 cm.
- Three-column formats: 5.5 cm, 11.4 cm, and 17.4 cm.
- Maximum individual file size: 20 MB.
- TIFF and PDF are preferred for most journals/types. EPS, JPEG, and CDX are accepted. Special cases differ.
- Color/grayscale: at least 300 dpi; black-and-white: at least 500 dpi; line art: at least 1,000 dpi at final size.
- RGB, Arial, capital panel letters, 6-8 pt text, and 0.5-1.5 pt strokes.
- Embed fonts. General production guidance says flatten layers, except specified `Cell` Leading Edge material.
- Do not use red and green together as the only distinction.

Cell Press requires minimal image processing, original unprocessed data on request, and disclosure of processing/stitching. Its current policy prohibits generative AI/AI-assisted alteration of research/data images, including brightness, contrast, or color-balance adjustment performed by such tools.

## PLOS research journals

**Scope:** current PLOS Computational Biology page, consistent with the sampled PLOS research-journal figure pages [PLOS-FIG]. Verify the selected PLOS journal.

- Formatting requirements are waived until provisional Editorial Accept.
- Final figure format: TIFF or EPS.
- Width: 789-2250 px at 300 dpi, equivalent to 6.68-19.05 cm.
- Text-column alignment recommendation: no wider than 13.2 cm.
- Maximum height: 2625 px at 300 dpi, equivalent to 22.23 cm.
- Resolution: 300-600 dpi at final dimensions. The page warns that above 600 may trigger resizing and below 300 will degrade output.
- The summary table says less than 10 MB; the detailed section says 10 MB or less. The planner conservatively uses the stricter boundary and flags the inconsistency.
- Text: Arial, Times, or Symbol, 8-12 pt.
- Color mode: RGB 8-bit/channel or grayscale.
- Put all panels of one figure in one single-page file. TIFF must have no alpha channel and must use LZW compression.
- The pixel bounds are expressed at 300 dpi: a 600 dpi raster at the same physical size contains twice as many pixels per axis. The screen compares physical size via its 300 dpi equivalent, not an absolute 2250-pixel cap.
- Captions remain in the manuscript; filenames are `Fig1.tif`, `Fig2.eps`, and so on.
- Do not increase pixel count and present that as improved resolutio

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

