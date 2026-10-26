---
id: sciref-markitdown-file-formats
name: "Scientific Ref: File Formats and Conversion Behavior"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (markitdown): File Formats and Conversion Behavior"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "markitdown file formats"
  - "file formats and conversion behavior"
keywords:
  - "markitdown"
  - "file"
  - "formats"
  - "specialized"
  - "scientific"
  - "reference"
---

# File Formats and Conversion Behavior

This reference targets Microsoft MarkItDown 0.1.8. "Built-in" means the converter ships in the `markitdown` package; some built-ins still require an optional dependency extra.

## Installation by Format

```bash
# Full built-in feature set
uv pip install "markitdown[all]==0.1.8"

# Common document subset
uv pip install "markitdown[pdf,docx,pptx,xlsx]==0.1.8"

# Minimal package; suitable for core text/HTML/CSV/ZIP/EPUB/IPYNB paths
uv pip install "markitdown==0.1.8"
```

## Built-in Converter Matrix

| Input | Typical extensions/source | Extra | Main behavior | Important limitations/network |
|---|---|---|---|---|
| Plain text | `.txt`, `.md`, recognized text, JSON/XML text | Core | Decodes text while preserving content | JSON/XML are not guaranteed to be normalized or pretty-printed |
| CSV | `.csv`, `text/csv` | Core | Dedicated CSV-to-Markdown table conversion | Very wide/large tables can create large Markdown |
| HTML | `.html`, `.htm` | Core | Headings, links, lists, tables, and readable text | CSS layout, client-side rendering, and visual fidelity are not preserved |
| RSS/Atom-like XML | feed content/URLs | Core | Feed-focused Markdown | Remote retrieval uses network if a URI is supplied |
| Wikipedia page | Wikipedia URL | Core | Page-oriented Markdown | Network; URL-specific converter |
| Bing result page | Bing search-result URL | Core | Search-result-oriented Markdown | Network; HTML and service behavior can change |
| YouTube | watch, `youtu.be`, shorts or embed URLs | `youtube-transcription` for transcript | Metadata, description, and available transcript | Fetches YouTube page/transcript; captions may be absent or restricted |
| ZIP | `.zip` | Core | Iterates members and invokes nested converters | Treat untrusted archives as hostile; output can expand substantially |
| EPUB | `.epub` | Core | Book metadata and structured text | Complex styling, fixed layout, DRM, and interactive content are not preserved |
| Jupyter Notebook | `.ipynb` | Core | Notebook cells and content to Markdown | Runtime state is not reproduced; cells remain inert text during conversion |
| PDF | `.pdf` | `pdf` | Extracts existing text and tables | No built-in local OCR for scanned pages; multi-column order and complex tables require validation |
| Word | `.docx` | `docx` | Headings, lists, links, tables, images/alt text, and OMML math | Track changes, floating layout, and visual pagination are not faithfully reproduced |
| PowerPoint | `.pptx` | `pptx` | Slide text, tables, notes, and shape ordering | Animations and layout fidelity are lost; image description requires an LLM client |
| Excel | `.xlsx` | `xlsx` | Worksheets rendered as Markdown tables | Formulas, charts, merged cells, and formatting require source-level validation |
| Legacy Excel | `.xls` | `xls` | Worksheets rendered as Markdown tables | Legacy parser limitations; no visual workbook fidelity |
| Outlook message | `.msg` | `outlook` | Message headers and body | Attachments and rich formatting may need separate handling |
| Image | `.jpg`, `.jpeg`, `.png` | Core | Selected ExifTool metadata; optional LLM description | Built-in converter does not locally OCR text; image may be sent to an external LLM |
| Audio/video-audio | `.wav`, `.mp3`, `.m4a`, `.mp4` | `audio-transcription` | Metadata plus speech transcript | Transcription uses Google Web Speech through `SpeechRecognition`; content leaves the machine |

### Formats commonly overstated

- The 0.1.8 built-in `ImageConverter` accepts JPEG and PNG, not GIF or WebP.
- Built-in PDF conversion extracts a text layer; Tesseract is not part of MarkItDown's PDF path.
- The package does not promise page ranges, bounding boxes, coordinates, or pixel-faithful output.
- JSON and XML are text-based inputs, not schema-aware transformations.
- A successful conversion does not imply complete figure, equation, table, or reading-order recovery.

## PDF

### Built-in extraction

```python
from markitdown import MarkItDown

result = MarkItDown().convert_local("paper.pdf")
print(result.markdown)
```

Use for born-digital PDFs where text is selectable. MarkItDown 0.1.5 improved aligned/wide table output and partially numbered lists; 0.1.6 fixed linear memory growth across PDF pages.

### Scanned PDFs

Choose one:

1. `markitdown-ocr==0.1.1` with an approved vision provider
2. Azure Document Intelligence
3. Azure Content Understanding
4. A local OCR/layout parser when content cannot leave the environment

Do not claim OCR was performed unless the selected path actually supplied it.

### Validate

- Reading order in multi-column papers
- Equations, superscripts, and symbols
- Table headers and row alignment
- Figure captions and footnotes
- References and hyperlinks
- Missing pages or empty scanned sections

## DOCX

Install:

```bash
uv pip install "markitdown[docx]==0.1.8"
```

Version 0.1.2 added DOCX math-equation rendering. Conversion is semantic, not page-layout preserving.

Validate:

- Heading levels and list nesting
- Tables and merged cells
- OMML equations
- Hyperlinks and image alt text
- Footnotes/endnotes
- Tracked changes and comments

For custom Mammoth mapping:

```python
from markitdown import MarkItDown

converter = MarkItDown(style_map="p[style-name='Abstract'] => blockquote.abstract")
result = converter.convert_local("manuscript.docx")
```

## PPTX

Install:

```bash
uv pip install "markitdown[pptx]==0.1.8"
```

The converter orders shapes to approximate reading order and extracts textual slide content. Optional `llm_client`, `llm_model`, and `llm_prompt` values can describe image content.

Validate:

- Slide order and boundaries
- Speaker notes
- Grouped/overlapping shapes
- Tables and chart labels
- Images containing essential text
- Content conveyed only by position, color, or animation

## XLSX and XLS

Install:

```bash
uv pip install "markitdown[xlsx,xls]==0.1.8"
```

The result is useful for textual review and LLM ingestion, but it is not a workbook round trip.

Validate:

- Sheet names and order
- Hidden rows, columns, and sheets
- Merged cells
- Formula text versus cached/displayed values
- Date/number interpretation
- Charts, images, comments, and conditional formatting

The 0.1.8 XLSX converter reads **all worksheets** (`sheet_name=None`); hiding a
sheet in Excel is not an extraction filter. Inventory sheet visibility before
sharing the Markdown and use an explicitly selected workbook copy if only certain
sheets belong in the out

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

