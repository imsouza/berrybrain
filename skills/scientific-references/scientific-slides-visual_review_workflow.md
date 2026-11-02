---
id: sciref-scientific-slides-visual-review-workflow
name: "Scientific Ref: Visual Review Workflow for Presentations"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-slides): Visual Review Workflow for Presentations"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific slides visual review workflow"
  - "cientifico slides visual revisao workflow"
  - "visual review workflow for presentations"
keywords:
  - "scientific"
  - "slides"
  - "visual"
  - "review"
  - "workflow"
  - "cientifico"
  - "revisao"
  - "specialized"
  - "reference"
---

# Visual Review Workflow for Presentations

## Overview

Visual review is a critical quality assurance step for presentations, allowing you to identify and fix layout issues, text overflow, element overlap, and design problems before presenting. This guide covers converting presentations to images, systematic visual inspection, common issues, and iterative improvement strategies.

## Render for layout; extract text for content checks

Render every slide with `pdf_to_images.py` to inspect layout, cropping, and labels.
Use PDF text extraction separately to check citations and wording; it cannot detect
visual overlap. Work in page batches if tool/image limits require it. A past tool buffer
failure is not a property of all PDFs and does not prohibit direct PDF inspection.

1. Export PDF from PowerPoint/Beamer.
2. Render pages and review them visually.
3. Check the source text, citations, original figures and reading order separately.
4. Correct source files, export again and recheck affected pages.

## Why Visual Review Matters

### Common Problems Invisible in Source

**LaTeX Beamer Issues**:
- Text overflow from text boxes
- Overlapping elements (equations over images)
- Poor line breaking
- Figures extending beyond slide boundaries
- Font size issues at actual resolution

**PowerPoint Issues**:
- Text cut off by shapes or slide edges
- Images overlapping with text
- Inconsistent spacing between slides
- Color rendering differences
- Font substitution problems

**Projection Issues**:
- Content visible on laptop but cut off when projected
- Colors looking different on projector
- Low contrast elements becoming invisible
- Small details disappearing

### Benefits of Visual Review

- **Catch layout errors early**: Fix before printing or presenting
- **Verify readability**: Ensure text is large enough and high contrast
- **Check consistency**: Spot inconsistencies across slides
- **Test accessibility**: Verify color contrast and clarity
- **Validate design**: Ensure professional appearance

## Conversion: PDF to Images

### Method 1: Using pdf_to_images.py Script (Recommended)

**No External Dependencies Required**:
The script uses PyMuPDF, a self-contained Python library - no poppler or other system software needed.

**Installation**:
```bash
# Install in your task environment (the repository environment omits scientific dependencies)
uv pip install pymupdf
```

**Basic Conversion**:
```bash
# Convert all slides to JPEG images
python skills/scientific-slides/scripts/pdf_to_images.py presentation.pdf slide --dpi 150

# Creates: slide-001.jpg, slide-002.jpg, slide-003.jpg, ...
```

**High-Resolution Conversion**:
```bash
# Higher quality for detailed inspection (300 DPI)
python skills/scientific-slides/scripts/pdf_to_images.py presentation.pdf slide --dpi 300

# PNG format (lossless, larger files)
python skills/scientific-slides/scripts/pdf_to_images.py presentation.pdf slide --dpi 150 --format png
```

**Convert Specific Slides**:
```bash
# Slides 5-10 only
python skills/scientific-slides/scripts/pdf_to_images.py presentation.pdf slide --dpi 150 --first 5 --last 10

# Single slide
python skills/scientific-slides/scripts/pdf_to_images.py presentation.pdf slide --dpi 150 --first 3 --last 3
```

**Output Options**:
```bash
# Different output directory
python skills/scientific-slides/scripts/pdf_to_images.py presentation.pdf review/slide --dpi 150

# Custom naming
python skills/scientific-slides/scripts/pdf_to_images.py presentation.pdf output/presentation --dpi 150
```

### Method 2: Exporting PowerPoint Through LibreOffice

For PowerPoint presentations, export to PDF with LibreOffice, then render as in Method 1:

```bash
soffice --headless --convert-to pdf --outdir review presentation.pptx
python skills/scientific-slides/scripts/pdf_to_images.py review/presentation.pdf review/slide --dpi 150
```

LibreOffice substitutes fonts that are not installed, so confirm final text fit in PowerPoint.

**Advantages**:
- Optimized for PowerPoint files
- Can create overview grids
- Handles .pptx format directly
- Customizable layout

### Method 3: Using ImageMagick 7 (Optional)

**Installation**:
```bash
# Ubuntu/Debian
sudo apt-get install imagemagick

# macOS
brew install imagemagick
```

**Conversion** (PDF reading also requires Ghostscript and an enabled PDF security policy; prefer PyMuPDF if unavailable):
```bash
# Convert PDF to images
magick -density 150 presentation.pdf slide.jpg

# Higher quality
magick -density 300 presentation.pdf slide.jpg

# Specific format
magick -density 150 presentation.pdf slide.png
```

### Method 4: Using Python (Programmatic)

```python
import pymupdf as fitz  # PyMuPDF

# Open PDF
doc = fitz.open('presentation.pdf')

# Convert each page to image
for i, page in enumerate(doc, start=1):
    pixmap = page.get_pixmap(dpi=200)
    pixmap.save(f'slide-{i:03d}.jpg', output='jpeg')

doc.close()
```

**Install PyMuPDF**:
```bash
uv pip install pymupdf
# No external dependencies needed!
```

## Systematic Visual Inspection

### Inspection Workflow

**Step 1: Overview Pass**
- View all slides quickly
- Note overall consistency
- Identify obviously problematic slides
- Create list of slides needing detailed review

**Step 2: Detailed Inspection**
- Review each flagged slide carefully
- Check against issue checklist (below)
- Document specific problems with slide numbers
- Take notes on required fixes

**Step 3: Cross-Slide Comparison**
- Check consistency across similar slides
- Verify uniform spacing and alignment
- Ensure consistent font sizes
- Check color scheme consistency

**Step 4: Distance Test**
- View images at reduced size (simulates projection)
- Check readability from ~6 feet
- Verify key elements are visible
- Test if main message is clear

### Issue Checklist

Review each slide for these common problems:

#### Text Issues

**Overflow and Truncation**:
- [ ] Text cut off at slide edges
- [ ] Text extending beyond text boxes
- [ ] Equations running into margins
- [ ] Captions cut off at bottom
- [ ] Bullet points extending beyond boundary

**Readability**:
- [ ] Font size too small (minimum 18pt visible)
- [ ] Poor contrast (text vs background)
- [ ] Inadequate line spacing
- [ ] Text too close to slide edge
- [ ] Overlapping lines of text

#### Element Overlap

**Text Overlaps**:
- [ ] Text overlapping with images
- [ ] Text overlapping with shapes
- [ ] Multiple text boxes overlapping
- [ ] Labels overlapping with data points
- [ ] Title overlapping with cont

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

