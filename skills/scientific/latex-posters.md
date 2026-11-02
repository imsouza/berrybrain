---
id: sci-latex-posters
name: "Scientific: latex-posters"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Creates research posters in LaTeX using beamerposter, tikzposter, or baposter. Use for conference posters, academic presentations, multi-column scientific layouts, figure integration, typography, compilation, and PDF preflight."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "latex posters"
  - "latex-posters"
keywords:
  - "latex"
  - "posters"
  - "creates"
  - "research"
  - "beamerposter"
  - "tikzposter"
---

# LaTeX Research Posters

Create a conference-sized PDF from scientific content, editable LaTeX, and verified
figures. Use for new posters, paper-to-poster adaptation, institutional templates,
and poster compilation or print preflight.

## Choose the poster package

| Package | Use when | Reviewed target |
| --- | --- | --- |
| beamerposter | Beamer blocks or institutional Beamer themes fit the project | CTAN 1.13 |
| tikzposter | TikZ styling and automatically stacked blocks are useful | CTAN 2.0 |
| baposter | A supplied project uses its named, relative-positioned boxes | Archived class v2.0, 2011/11/26; upstream site unavailable at review |

The three bundled templates were compiled locally with pdfLaTeX (TeX Live 2025)
and inspected using Poppler 26.09.0. baposter was tested using the pinned archival
source described in [references/latex_poster_packages.md](references/latex_poster_packages.md).
Do not interpret an old stable package version as proof of current tagged-PDF support.
Other reference snippets are illustrative building blocks unless explicitly tested;
they require the indicated class, packages, actual data, and figure files.

## Workflow

### 1. Establish the scientific content and output requirements

- Record exact paper width, height, orientation, venue rules, and printer requirements.
- Choose 1-3 main messages and the results needed to support them. A useful starting
  budget is 300-800 words with 3-5 figures; adjust to the audience and available space.
- Preserve study design, sample sizes, units, effect sizes, uncertainty, limitations,
  and data provenance. Include the relevant citations, contact, and acknowledgments.
- Use actual analysis outputs for plots and original research images for evidence.
  Do not use an image model to invent numerical charts, microscopy, spectra, or results.

### 2. Prepare and review figures

Prefer vector PDF for numerical plots, TikZ for precise diagrams, and suitable PNG/JPEG
for photographs or conceptual artwork. Convert SVG to PDF before ordinary
`\includegraphics`; SVG is not a directly supported pdfLaTeX image format.

Optional AI schematics can help explain a concept. Generate them only when useful;
there is no required AI-image quota. Keep titles, citations, numerical values, and QR
codes editable in LaTeX or a deterministic plotting tool. Use official logo assets.

```bash
# From the skill root; save project output outside the installed skill directory.
# Illustrative paid call, not executed during this review.
python scripts/generate_schematic.py \
  "Conceptual A0 poster diagram: three boxes SAMPLE, MEASURE, ANALYZE connected left to right. Large dark labels on white, generous margins, no numerical results." \
  -o /path/to/project/figures/methods.png --doc-type poster --iterations 1
```

The helper uses OpenRouter's `POST /api/v1/images` with Nano Banana 2
(`google/gemini-3.1-flash-image`) and reviews through `POST /api/v1/chat/completions`
with `google/gemini-3.7-flash`. It accepts PNG output paths and 1-2 iterations.
Generation and review both consume API credits. A saved image or an AI score does
not establish scientific correctness or final print quality. Check the image and
`*_review_log.json`, including `quality_met` and `termination_reason`.

Inspect every figure before assembly: relationships, labels, units, colors, license,
and accuracy. Check actual placed size, pixel dimensions, and raster PPI. A requested
“120 pt” font in an image prompt is not a physical typesetting guarantee. See
[references/ai_graphics_for_posters.md](references/ai_graphics_for_posters.md).

### 3. Create the layout

Copy one of the three files in `assets/` into the project:

- `beamerposter_template.tex`
- `tikzposter_template.tex`
- `baposter_template.tex`

Each template compiles with visibly marked draft figure boxes when its assets are
missing. These are placeholders, not example research findings. Replace them,
example references, author details, logo boxes, and the example QR target before delivery.

Use 2-3 columns as a starting layout. Keep sufficient page margins and gaps between
blocks. Figure widths must fit the containing box; `0.85\linewidth` is a reasonable
starting point, not a universal maximum. Body text around 24-36 pt at final print
size is a starting range. Font commands vary with class and scale; verify the actual
rendered sizes rather than assuming that `\Large` is always a fixed size.

Package details, valid option keys, and layout caveats:
[references/latex_poster_packages.md](references/latex_poster_packages.md).

### 4. Compile and inspect the actual PDF

Run these from the poster project directory:

```bash
pdflatex -interaction=nonstopmode -halt-on-error poster.tex
pdflatex -interaction=nonstopmode -halt-on-error poster.tex
pdfinfo poster.pdf
pdffonts poster.pdf
pdfimages -list poster.pdf
pdftoppm -scale-to 2000 -singlefile -png poster.pdf poster-preview
rg -n 'Overfull|Underfull|Warning|undefined' poster.log
```

Use LuaLaTeX/XeLaTeX if a project needs `fontspec` and installed OpenType fonts;
changing engines still requires compilation and visual verification. Run BibTeX
or Biber only when the bibliography setup calls for it.

Open the rendered page and inspect all edges, column boundaries, figure labels, and
footer. Overfull boxes require investigation; they do not always imply page clipping.
TikZ/baposter overlaps can occur without overfull warnings, so a clean log is insufficient.
An underfull box is a spacing diagnostic, not automatic evidence of clipped content.

Run the bundled read-only preflight using its absolute path:

```bash
bash /path/to/latex-posters/scripts/review_poster.sh poster.pdf
```

Exit status is 0 when automated checks pass, 1 for failures such as unreadable PDF,
multiple pages, or unembedded fonts, and 2 when required Poppler tools are absent.
The script reports all fonts and placed raster PPI. It does not certify accessibility,
PDF/X compliance, scientific accuracy, QR destinations, or absence of overlap.

### 5. Proof and deliver

- Compare exact PDF dimensions with the venue specification and confirm one page.
- Check all `emb` entries from `pdffonts`; rebuild offending fonts in the LaTeX or
  imported figure source. `-dEmbedAllFonts=true` is a Ghostscript option, not pdflatex.
- For raster artwork, calculate PPI at placed size; use the printer's requirements.
  A 300 PPI target is useful for close inspection, but vector figures have no raster PPI.
- A0-to-A4 is approximately

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

