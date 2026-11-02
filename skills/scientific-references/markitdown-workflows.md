---
id: sciref-markitdown-workflows
name: "Scientific Ref: Practical Workflows"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (markitdown): Practical Workflows"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "markitdown workflows"
  - "practical workflows"
keywords:
  - "markitdown"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
  - "practical"
---

# Practical Workflows

All workflows target MarkItDown 0.1.8 and use `.markdown`, not the legacy `.text_content` alias.

## 1. One Trusted Local Document

```python
from hashlib import sha256
from pathlib import Path

from markitdown import MarkItDown

source = Path("protocol.docx").resolve(strict=True)
output = Path("protocol.md")

result = MarkItDown().convert_local(source)
output.write_text(result.markdown, encoding="utf-8")

provenance = {
    "source": source.name,
    "sha256": sha256(source.read_bytes()).hexdigest(),
    "title": result.title,
    "output": str(output),
}
print(provenance)
```

For very large files, compute the hash incrementally rather than loading the source again.

## 2. Binary Upload

Validate size and type before conversion. Use `BytesIO` plus explicit hints:

```python
from io import BytesIO

from markitdown import MarkItDown, StreamInfo


def convert_pdf_upload(payload: bytes, filename: str) -> str:
    max_bytes = 25 * 1024 * 1024
    if len(payload) > max_bytes:
        raise ValueError("PDF exceeds the 25 MiB conversion limit")
    if not payload.startswith(b"%PDF-"):
        raise ValueError("Payload does not have a PDF signature")

    result = MarkItDown().convert_stream(
        BytesIO(payload),
        stream_info=StreamInfo(
            extension=".pdf",
            mimetype="application/pdf",
            filename=filename,
        ),
    )
    return result.markdown
```

Signature checks are only one validation layer; they do not make the parser sandboxed.

## 3. Batch Directory Conversion

```bash
python scripts/batch_convert.py inputs/ outputs/ \
  --recursive \
  --extensions .pdf .docx .pptx .xlsx .csv .html \
  --manifest outputs/manifest.json
```

Properties:

- Local paths only
- Symlinks skipped
- Deterministic path ordering
- Relative directories preserved
- Output name retains the source suffix, e.g. `paper.pdf.md`
- Existing output skipped unless `--overwrite`
- Plugins off unless `--plugins`
- Nonzero exit when a conversion fails

Retry failed files after installing the missing format extra:

```bash
uv pip install "markitdown[pdf,docx,pptx,xlsx]==0.1.8"
python scripts/batch_convert.py inputs/ outputs/ --recursive --overwrite
```

Use a fresh output directory when comparing converter versions.

## 4. Literature Collection

Input naming convention:

```text
Author_Year_Title.pdf
```

Convert and build indexes:

```bash
python scripts/convert_literature.py papers/ literature/ \
  --recursive \
  --create-index
```

Organize by inferred year:

```bash
python scripts/convert_literature.py papers/ literature/ \
  --recursive \
  --organize-by-year \
  --create-index
```

Each output contains provenance front matter:

```yaml
---
title: "Example title"
author: "Smith"
year: "2025"
source: "incoming/Smith_2025_Example_Title.pdf"
converted_at: "2026-10-01T17:00:00+00:00"
markitdown_version: "0.1.8"
---
```

The helper also writes `catalog.json` and `INDEX.md` when `--create-index` is requested. Metadata inferred from a filename is a convenience, not authoritative bibliographic metadata.

## 5. RAG Ingestion

Recommended sequence:

1. Validate and hash the source.
2. Convert with a pinned package/plugin version.
3. Keep source metadata separate from converted text.
4. Check non-empty output and expected section markers.
5. Sanitize active HTML and unsafe links if Markdown will be rendered.
6. Chunk by semantic headings with overlap.
7. Store source/hash/converter/page-or-section provenance with every chunk.
8. Mark chunks as untrusted source content in the retrieval prompt.
9. Retain the original source for verification.

Example conversion envelope:

```python
from dataclasses import asdict, dataclass
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path

from markitdown import MarkItDown


@dataclass(frozen=True)
class ConvertedDocument:
    source_name: str
    source_sha256: str
    converter_version: str
    title: str | None
    markdown: str


def convert_for_ingestion(path: Path) -> ConvertedDocument:
    path = path.resolve(strict=True)
    digest = sha256(path.read_bytes()).hexdigest()
    result = MarkItDown().convert_local(path)
    if not result.markdown.strip():
        raise ValueError(f"Conversion produced no text: {path.name}")

    return ConvertedDocument(
        source_name=path.name,
        source_sha256=digest,
        converter_version=version("markitdown"),
        title=result.title,
        markdown=result.markdown,
    )
```

Do not treat Markdown line numbers as stable page citations. MarkItDown does not expose PDF page coordinates.

## 6. Mixed-Format Study Folder

Use a two-pass workflow:

### Pass A: inventory

- Count files by extension and byte size.
- Detect duplicates by content hash.
- Exclude temporary, lock, and hidden files.
- Identify encrypted/unsupported inputs.
- Classify which files require external OCR/cloud processing.

### Pass B: convert

- Use local built-ins first.
- Route only failed scanned/complex files to an approved OCR/cloud path.
- Record the selected mode per file.
- Compare file count, failure count, and output count.

This minimizes cost and external data transfer.

## 7. Spreadsheet Orientation, Then Structured Analysis

Use MarkItDown to understand workbook organization:

```python
from markitdown import MarkItDown

preview = MarkItDown().convert_local("assay-results.xlsx").markdown
print(preview)
```

Then use a spreadsheet/dataframe library for calculations:

- Inspect formulas and cached values explicitly.
- Select the authoritative sheet/range.
- Preserve data types.
- Validate merged cells and hidden rows.

Do not parse a scientific numeric dataset back out of Markdown when the original workbook is available.

## 8. Presentation Review

```python
from markitdown import MarkItDown

result = MarkItDown().convert_local("lab-meeting.pptx")
```

Review:

- Slide boundaries
- Title hierarchy
- Speaker notes
- Text in charts/images
- Claims encoded only by color/position

If images carry essential meaning, add an approved vision description or OCR pass and label generated text as model-derived.

## 9. Scanned-PDF Escalation

1. Try built-in PDF extraction.
2. Detect unexpectedly short/empty output relative to page/file size.
3. Confirm the source is scanned by visual inspection.
4. Choose:
   - Local OCR/layout parser for restricted data
   - `markitdown-ocr` for approved vision-provider processing
   - Document Intelligence for Azure l

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

