---
id: sciref-markitdown-migration
name: "Scientific Ref: Migration and Release Notes"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (markitdown): Migration and Release Notes"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "markitdown migration"
  - "migration and release notes"
keywords:
  - "markitdown"
  - "migration"
  - "specialized"
  - "scientific"
  - "reference"
  - "release"
---

# Migration and Release Notes

This skill targets MarkItDown 0.1.8. The timeline below summarizes changes that affect user code and operational guidance.

## Release Timeline

### 0.1.0 — March 22, 2025

Major architecture release:

- Optional dependency feature groups introduced
- Plugin architecture introduced
- Conversions moved to in-memory streams; temporary files removed
- EPUB support added
- CLI extension, MIME, and charset hints added
- `--keep-data-uris` added

Breaking changes:

- Install `[all]` for behavior comparable to earlier all-in-one installs.
- `convert_stream()` now requires a binary stream.
- `DocumentConverter` implementations now receive binary streams plus `StreamInfo`, not file paths.

### 0.1.1 — March 25, 2025

- `convert_url()` renamed to `convert_uri()`.
- `file:` and `data:` URI handling added.
- `convert_url()` retained as a compatibility alias.

### 0.1.2 — May 28, 2025

- DOCX math-equation rendering
- Dedicated CSV-to-Markdown conversion
- XML/OMML parsing switched to `defusedxml`
- Document Intelligence credential/API-version improvements
- Streamable HTTP MCP support
- YouTube transcript fixes
- Python requirement updated to 3.10+

### 0.1.3 — August 26, 2025

- Safer ExifTool handling, requiring version 12.24 or later
- MCP plugin enablement through `MARKITDOWN_ENABLE_PLUGINS`
- DOCX linked-image fixes
- Document Intelligence HTML type handling
- Custom LLM prompt forwarding fix
- Additional HTML/PPTX robustness

### 0.1.4 — December 1, 2025

Security maintenance release:

- Mammoth updated to address CVE-2025-11849
- `pdfminer.six` updated to address GHSA-wf5f-4jwr-ppcp

### 0.1.5 — February 20, 2026

- Better aligned and wide PDF tables
- Partially numbered PDF-list fix
- `text/markdown` added to the HTTP Accept header
- Windows ONNX Runtime pin removed

### 0.1.6 — May 26, 2026

- Official OCR layer/plugin for embedded images and scanned PDFs
- PDF page cleanup to fix linear memory growth
- Deeply nested HTML recursion fix
- Azure Content Understanding converter
- Expanded security guidance for broad I/O and MCP binding

### 0.1.7 and 0.1.8 — maintenance through September 21, 2026

- Python supports >=3.10,<3.15.
- Document Intelligence defers API version selection to its SDK instead of hardcoding the old preview.
- CU uses the SDK `to_llm_input()` helper and requires `azure-ai-contentunderstanding>=1.2.0b1`; see the preview-default caveat in `cloud_and_ocr.md`.
- CLI cloud endpoints can come from `MARKITDOWN_DOCINTEL_ENDPOINT` and `MARKITDOWN_CU_ENDPOINT`; stdin is buffered before detection.
- CSV preserves wider rows and CR-only lines; notebook BOM/headings, RSS/Atom links/content, and duplicate ZIP member handling improved.
- `markitdown-ocr==0.1.1` uses core Office image hooks and needs core >=0.1.8.
- `markitdown-mcp==0.0.1a7` uses MCP SDK 2.x.
- URI schemes are case-insensitive; `file:` rejects UNC/device paths. Local path authorization is still the caller's responsibility.

## Upgrade Installation

Create a clean environment for the comparison:

```bash
uv venv --python 3.12 .venv-markitdown
source .venv-markitdown/bin/activate
uv pip install "markitdown[all]==0.1.8"
```

Do not test a migration in an environment that still contains unknown third-party plugins.

## Code Replacements

### Result content

Old/compatibility:

```python
content = result.text_content
```

Current:

```python
content = result.markdown
```

`text_content` still works in 0.1.8 but is explicitly documented in source as a soft-deprecated alias.

### Local conversion

Broad:

```python
result = converter.convert(user_value)
```

Narrow local path:

```python
result = converter.convert_local(validated_path)
```

Use `convert_stream()` for validated uploaded bytes and `convert_response()` after an application-controlled download.

### Streams

Old:

```python
from io import StringIO

result = converter.convert_stream(StringIO("text"))
```

Current:

```python
from io import BytesIO

from markitdown import StreamInfo

result = converter.convert_stream(
    BytesIO(b"text"),
    stream_info=StreamInfo(
        extension=".txt",
        mimetype="text/plain",
        charset="utf-8",
    ),
)
```

### URI API

Old:

```python
result = converter.convert_url(uri)
```

Current:

```python
result = converter.convert_uri(validated_uri)
```

Prefer caller-controlled fetching plus `convert_response()` for HTTP(S).

### Hints

Legacy:

```python
result = converter.convert_stream(stream, file_extension=".pdf")
```

Current:

```python
from markitdown import StreamInfo

result = converter.convert_stream(
    stream,
    stream_info=StreamInfo(
        extension=".pdf",
        mimetype="application/pdf",
        filename="upload.pdf",
    ),
)
```

The legacy `file_extension`/`url` parameters still exist but are marked for migration in source.

## Custom Converter Migration

Pre-0.1 converter:

```python
class OldConverter(DocumentConverter):
    def convert(self, file_path):
        ...
```

0.1.x converter:

```python
from typing import Any, BinaryIO

from markitdown import DocumentConverter, DocumentConverterResult, StreamInfo


class CurrentConverter(DocumentConverter):
    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        ...

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        return DocumentConverterResult(markdown="...")
```

If `accepts()` peeks at bytes, restore the original stream position before returning.

## Plugin Packaging Migration

Outdated entry-point group:

```toml
[project.entry-points."markitdown.plugins"]
```

Current group:

```toml
[project.entry-points."markitdown.plugin"]
example = "example_markitdown_plugin"
```

The plugin module must export:

```python
__plugin_interface_version__ = 1


def register_converters(markitdown, **kwargs):
    ...
```

Use `pyproject.toml`; old `setup.py`-only examples are no longer the preferred packaging pattern.

## Installation Guidance Migration

Outdated:

```bash
uv pip install markitdown
uv pip install "markitdown[all]"
```

Repository-standard reproducible install:

```bash
uv pip install "markitdown[all]==0.1.8"
```

The base package no longer implies every format dependency. Select an extra or `[all]`.

## OCR Guidance Migration

Remove these stale claims:

- "Built-in PDF conversion uses Tesseract"
- "All images 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

