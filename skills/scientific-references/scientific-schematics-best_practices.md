---
id: sciref-scientific-schematics-best-practices
name: "Scientific Ref: Best Practices for Scientific Diagrams"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-schematics): Best Practices for Scientific Diagrams"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific schematics best practices"
  - "cientifico schematics best practices"
  - "best practices for scientific diagrams"
keywords:
  - "scientific"
  - "schematics"
  - "best"
  - "practices"
  - "cientifico"
  - "specialized"
  - "reference"
---

# Best Practices for Scientific Diagrams

## Overview

This guide supports prompt writing and manual figure review. Numeric design suggestions below are starting points; the target journal and article type determine submission requirements. AI-generated artwork also needs the venue's current permissions/disclosure policy checked before use.

### How this relates to the generator

These are the standards a figure is judged against — not a description of what
`scripts/generate_schematic.py` does for you. The generator produces a **PNG** and nothing else.
Read this file for two purposes:

- **To write the prompt.** Typography, colour, contrast, layout, labelling, and accessibility are
  all things the image model will attempt if you ask for them specifically. The sections below are
  the vocabulary for asking.
- **To judge the result, and to plan post-processing.** File format, resolution, colour space, and
  physical dimensions are fixed once the PNG exists. Where a journal's requirement differs from what
  came out, that is a conversion step you perform afterwards — the skill has no vector path, no DPI
  control, and no CMYK output.

## Publication Standards

### 1. File Format Requirements

**Vector Formats (Preferred)**
- **PDF**: Common for vector artwork and LaTeX; acceptance is venue-specific
  - Use for: Line drawings, flowcharts, block diagrams, circuit diagrams
  - Advantages: Scalable, small file size, embeds fonts
  - Standard for LaTeX workflows

- **EPS (Encapsulated PostScript)**: Legacy format, still accepted
  - Use for: Older publishing systems
  - Compatible with most journals
  - Can be converted from PDF

- **SVG (Scalable Vector Graphics)**: Web-friendly, increasingly accepted
  - Use for: Online publications, interactive figures
  - Can be edited in vector graphics software
  - Not all journals accept SVG

**Raster Formats (When Necessary)**
- **TIFF**: Professional standard for raster graphics
  - Use for: Microscopy images, photographs combined with diagrams
  - Minimum 300 DPI at final print size
  - Lossless compression (LZW)

- **PNG**: Web-friendly, lossless compression
  - Use for: Online supplementary materials, presentations
  - Minimum 300 DPI for print
  - Supports transparency

**Avoid for new diagram masters**
- **JPEG**: Lossy compression can damage text and lines; some venues accept high-quality JPEG for photographs
- **GIF**: Limited colors, inappropriate for scientific figures
- **BMP**: Uncompressed, unnecessarily large files

### 2. Resolution Requirements

**Vector Graphics**
- Infinite resolution (scalable)
- **Recommended**: Always use vector when possible

**Raster graphics**
- Calculate effective pixels per inch at the final physical size.
- Photographic submission targets commonly start at 300 ppi; line art may require more.
- Screen quality depends on pixel dimensions and display size, not DPI metadata.
- Check the venue-specific requirement before exporting; changing DPI metadata or upsampling cannot recover missing detail.

**Calculating DPI**
```
DPI = pixels / (inches at final size)

Example:
Image size: 2400 × 1800 pixels
Final print size: 8 × 6 inches
DPI = 2400 / 8 = 300 ✓ (acceptable)
```

### 3. Size and Dimensions

**Choose the venue and article type first**
- Nature's main-figure guide lists 89 mm and 183 mm widths; Extended Data has separate rules.
- Other publishers have different width ranges and file requirements. Do not reuse Nature dimensions for Science, Cell, PLOS, or IEEE without checking that venue's current instructions.
- See the source links under Journal-Specific Guidelines below.

**Best Practices**
- Design at final print size (avoid scaling)
- Use journal templates when available
- Allow margins for cropping
- Test appearance at final size before submission

### 4. Typography Standards

**Font Selection**
- **Recommended**: Arial, Helvetica, Calibri (sans-serif)
- **Acceptable**: Times New Roman (serif) for mathematics-heavy
- **Avoid**: Decorative fonts, script fonts, system fonts that may not embed

**Font Sizes (at final print size)**
- **Minimum**: 6-7 pt (journal dependent)
- **Axis labels**: 8-9 pt
- **Figure labels**: 10-12 pt
- **Panel labels (A, B, C)**: 10-14 pt, bold
- **Main text**: Should match manuscript body text

**Text Clarity**
- Use sentence case: "Time (seconds)" not "TIME (SECONDS)"
- Include units in parentheses: "Temperature (°C)"
- Spell out abbreviations in figure caption
- Avoid rotated text when possible (exception: y-axis labels)
- **No figure numbers in diagram** - do not include "Figure 1:", "Fig. 1", etc. (these are added by LaTeX/document)

### 5. Line Weights and Strokes

**Recommended Line Widths**
- **Diagram outlines**: 0.5-1.0 pt
- **Connection lines/arrows**: 1.0-2.0 pt
- **Emphasis elements**: 2.0-3.0 pt
- **Minimum visible**: 0.25 pt at final size

**Consistency**
- Use same line weight for similar elements
- Vary line weight to show hierarchy
- Avoid hairline rules (too thin to print reliably)

## Accessibility and Colorblindness

### 1. Colorblind-Safe Palettes

**Okabe-Ito Palette (Recommended)**
A useful starting palette from [Color Universal Design](https://jfly.uni-koeln.de/color/); no palette guarantees accessibility for every viewer, background, or adjacent pair:

```latex
% RGB values
Orange:     #E69F00 (230, 159,   0)
Sky Blue:   #56B4E9 ( 86, 180, 233)
Green:      #009E73 (  0, 158, 115)
Yellow:     #F0E442 (240, 228,  66)
Blue:       #0072B2 (  0, 114, 178)
Vermillion: #D55E00 (213,  94,   0)
Purple:     #CC79A7 (204, 121, 167)
Black:      #000000 (  0,   0,   0)
```

**Alternative: ColorBrewer Palettes**
- **Qualitative**: consider Set2, Paired, Dark2 after enabling ColorBrewer's colorblind-safe filter for the chosen number of categories
- **Sequential**: Blues, Greens, Oranges (avoid Reds/Greens together)
- **Diverging**: RdBu (Red-Blue), PuOr (Purple-Orange)

**Colors to Avoid Together**
- Red-Green combinations without redundant labels or shapes
- Blue-Purple combinations
- Yellow-Light green combinations

### 2. Redundant Encoding

Don't rely on color alone. Use multiple visual channels:

**Shape + Color**
```
Circle + Blue   = Condition A
Square + Orange = Condition B
Triangle + Green = Condition C
```

**Line Style + Color**
```
Solid + Blue = Treatment 1
Dashed + Orange = Treatment 2
Dotted + Green = Control
```

**Pattern Fill + Color**
```
Solid fill + Blue = Group A
Diagonal stripes + Orange = Group B
Cross-hatch + Green = Group C
```

### 3.

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

