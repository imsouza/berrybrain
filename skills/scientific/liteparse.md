---
id: sci-liteparse
name: "Scientific: liteparse"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Local document and PDF parsing that returns spatial text with bounding boxes. Use for extracting text from PDFs, DOCX, Office files, and images; running OCR on scans; producing layout-preserved JSON for RAG; batch-ingesting folders of papers; or rendering pages to PNG for multimo"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "liteparse"
keywords:
  - "liteparse"
  - "local"
  - "document"
  - "parsing"
  - "returns"
  - "spatial"
  - "text"
---

# LiteParse — Local Document Parsing

## Overview

LiteParse is an open-source document parser (Rust core, Python/Node bindings) for **local, layout-aware text extraction**. It produces layout text, structured JSON, or heuristic Markdown. Spatial text items may span several words; Python `emit_word_boxes=True` adds word boxes when needed.

**Verified release:** Python **liteparse 2.15.0** (September 29, 2026); CLI and synthetic local PDF/image fixtures tested on Python 3.13. Node/Rust examples below are source-checked and illustrative. Images convert through bundled Rust libraries, not ImageMagick. No cloud account is needed, but missing Tesseract language data can download from GitHub and an explicitly configured HTTP OCR service receives document images.

For parser selection vs MarkItDown, PDF manipulation libraries, or LlamaParse, see `references/choosing_a_parser.md`.

## When to Use This Skill

Use LiteParse when you need:

- **Fast local parsing** of PDFs or converted Office/image files without cloud dependencies
- **Spatial text** with bounding boxes for layout-aware RAG, citation grounding, or figure/table region logic
- **OCR** on scanned PDFs or images (bundled Tesseract, or a user-run HTTP OCR server)
- **Page screenshots** (PNG) for multimodal agents that must see charts, figures, or handwriting
- **Batch ingestion** of literature folders, supplementary PDFs, or protocol libraries
- **Page subsets** or **password-protected** PDFs

## When Not to Use

| Task | Use instead |
|------|-------------|
| Markdown for LLM ingestion (EPUB, audio, YouTube, HTML) | `markitdown` skill |
| Merge/split PDFs, forms, watermarks, rotation | A PDF manipulation library such as `pypdf` |
| Dense tables, handwriting, production cloud pipelines | [LlamaParse](https://developers.llamaindex.ai/llamaparse/parse/) (cloud; sign up separately) |

## Installation

```bash
uv pip install "liteparse==2.15.0"
```

This installs the Python bindings and the **`lit`** CLI. Verify:

```bash
lit --help
python -c "import liteparse; print(liteparse.__version__)"
```

**Optional system tool** (for Office inputs):

- **LibreOffice** — Word, Excel, PowerPoint, OpenDocument, CSV/TSV

PNG, JPEG, TIFF, WebP, SVG and other supported images convert natively.

Install commands are in `references/ocr_and_formats.md`.

**Node.js / TypeScript** (optional): `npm i @llamaindex/liteparse@2.15.0` — see `references/api_reference.md`.

---

## Quick Start

### Python

```python
from liteparse import LiteParse

parser = LiteParse(quiet=True)
result = parser.parse("paper.pdf")
print(result.text)

for page in result.pages:
    print(f"Page {page.page_num}: {len(page.text_items)} items")
```

### CLI

```bash
# Layout-preserved text (default)
lit parse paper.pdf

# Structured JSON with bounding boxes
lit parse paper.pdf --format json -o paper.json

# Heuristic Markdown, including headings, tables and links
lit parse paper.pdf --format markdown -o paper.md

# Disable OCR on text-native PDFs (faster)
lit parse paper.pdf --no-ocr
```

---

## Core Workflows

### 1. Parse to layout-preserved text

Best for quick full-document text or feeding chunkers that do not need coordinates.

```python
parser = LiteParse(ocr_enabled=True, quiet=True)
result = parser.parse("document.pdf")
full_text = result.text
```

```bash
lit parse document.pdf -o output.txt
```

### 2. Parse to structured JSON (bounding boxes)

Use when building layout-aware RAG, highlighting source regions, or joining text with screenshots.

```python
from liteparse import LiteParse

parser = LiteParse(output_format="json", quiet=True)
result = parser.parse("document.pdf")

# Programmatic access
for page in result.pages:
    for item in page.text_items:
        bbox = (item.x, item.y, item.width, item.height)
        # item.text, item.confidence, item.font_name, item.font_size
```

```bash
lit parse document.pdf --format json -o document.json
```

JSON field layout: `references/output_formats.md`.

### 3. Parse specific pages

```python
parser = LiteParse(target_pages="1-5,10,15-20", quiet=True)
result = parser.parse("long_paper.pdf")
```

```bash
lit parse long_paper.pdf --target-pages "1-5,10"
```

### 4. Parse from bytes or stdin

Useful for uploads, S3 downloads, or piping remote PDFs.

```python
with open("document.pdf", "rb") as f:
    result = parser.parse(f.read())
```

```bash
curl -sL https://example.com/report.pdf | lit parse -
```

### 5. Page screenshots for multimodal agents

Screenshots capture visual content that text extraction alone misses (figures, complex tables, handwriting).

```python
from pathlib import Path

parser = LiteParse(dpi=150, quiet=True)
shots = parser.screenshot("document.pdf", page_numbers=[1, 2, 3])
out = Path("screenshots")
out.mkdir(exist_ok=True)
for s in shots:
    (out / f"page_{s.page_num}.png").write_bytes(s.image_bytes)
```

```bash
lit screenshot document.pdf --target-pages "1,3,5" -o ./screenshots
lit screenshot document.pdf --dpi 300 -o ./screenshots
```

Combine **JSON parse + screenshots** when an agent needs both coordinates and pixels for the same pages.

### 6. Batch-parse a directory

Use the CLI or bundled script. OCR workers parallelize OCR tasks; they do not parallelize whole-document PDFium parsing. Python worker pools provide process-level parallelism and hard parse timeouts; see the API reference.

```bash
lit batch-parse ./papers ./parsed --format json --recursive
lit batch-parse ./papers ./parsed --extension .pdf --no-ocr
```

```bash
python scripts/batch_parse_dir.py ./papers ./parsed --format json --recursive
```

The wrapper mirrors subdirectories, preserves source suffixes (`paper.pdf.json`), and rejects existing outputs or partial-page results. It emits a documented Python JSON subset, not the native CLI schema. Native `lit batch-parse` uses `paper.json`, so same-stem inputs in one directory can collide; restrict the input extension or use the wrapper.

### 7. OCR configuration

OCR is **on by default**. Tesseract is bundled; missing `.traineddata` files are downloaded on demand, including when a custom tessdata directory is set.

```python
parser = LiteParse(
    ocr_enabled=True,
    ocr_language="eng",       # Tesseract codes: fra, deu, etc.
    num_workers=4,            # parallel OCR (default: CPU cores - 1)
    dpi=150,                  # higher DPI → better OCR, slower
)
```

```bash
lit parse scan.pdf --ocr-language fra
lit parse scan.pdf --no-ocr
lit parse scan.pdf --ocr-server-url http://local

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

