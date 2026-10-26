---
id: sciref-markitdown-api-reference
name: "Scientific Ref: MarkItDown 0.1.8 API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (markitdown): MarkItDown 0.1.8 API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "markitdown api reference"
  - "markitdown 0.1.8 api reference"
keywords:
  - "markitdown"
  - "api"
  - "reference"
  - "specialized"
  - "scientific"
---

# MarkItDown 0.1.8 API Reference

Verified against the `v0.1.8` source tag and installed package on October 1, 2026.

## Public Imports

```python
from markitdown import (
    DocumentConverter,
    DocumentConverterResult,
    FileConversionException,
    MarkItDown,
    MissingDependencyException,
    PRIORITY_GENERIC_FILE_FORMAT,
    PRIORITY_SPECIFIC_FILE_FORMAT,
    StreamInfo,
    UnsupportedFormatException,
)
```

Azure file-type enums are exported from `markitdown.converters`:

```python
from markitdown.converters import (
    ContentUnderstandingFileType,
    DocumentIntelligenceFileType,
)
```

## `MarkItDown`

### Constructor

```python
MarkItDown(
    *,
    enable_builtins: bool | None = None,
    enable_plugins: bool | None = None,
    **kwargs,
)
```

Built-in converters are enabled by default. Third-party plugins are disabled by default.

Recognized constructor keywords include:

| Keyword | Purpose |
|---|---|
| `requests_session` | Custom `requests.Session` used by HTTP(S) URI conversion |
| `llm_client` | OpenAI-compatible client for image descriptions and compatible plugins |
| `llm_model` | Provider-specific model identifier |
| `llm_prompt` | Prompt for image description/OCR |
| `exiftool_path` | Explicit trusted ExifTool executable |
| `style_map` | Mammoth style map for DOCX conversion |
| `docintel_endpoint` | Enable Azure Document Intelligence |
| `docintel_credential` | Explicit `AzureKeyCredential` or token credential |
| `docintel_file_types` | Restrict Document Intelligence routing |
| `docintel_api_version` | Azure Document Intelligence API version |
| `cu_endpoint` | Enable Azure Content Understanding |
| `cu_credential` | Explicit `AzureKeyCredential` or token credential |
| `cu_analyzer_id` | Custom Content Understanding analyzer |
| `cu_file_types` | Restrict Content Understanding routing |

The public signature uses `**kwargs`; spell these names exactly. Unknown names can be silently ignored: there is no `cu_api_version` option. `docintel_api_version=None` delegates to the installed Azure SDK default. See `cloud_and_ocr.md` for the tested SDK versions and network contracts.

### Conversion methods

#### `convert()`

```python
convert(
    source: str | Path | requests.Response | BinaryIO,
    *,
    stream_info: StreamInfo | None = None,
    **kwargs,
) -> DocumentConverterResult
```

Dispatch rules:

- `str` with a parsed `http:`, `https:`, `file:`, or `data:` scheme (case-insensitive) → `convert_uri()`
- other `str` or `Path` → `convert_local()`
- `requests.Response` → `convert_response()`
- binary file-like object → `convert_stream()`
- text stream → `TypeError`

This convenience method is broad. Prefer a narrower method for untrusted or application-facing inputs.

#### `convert_local()`

```python
convert_local(
    path: str | Path,
    *,
    stream_info: StreamInfo | None = None,
    file_extension: str | None = None,
    url: str | None = None,
    **kwargs,
) -> DocumentConverterResult
```

`file_extension` and `url` are legacy parameters; put overrides in `StreamInfo`.

```python
from pathlib import Path

from markitdown import MarkItDown

source = Path("experiment.xlsx")
result = MarkItDown().convert_local(source)
Path("experiment.md").write_text(result.markdown, encoding="utf-8")
```

#### `convert_stream()`

```python
convert_stream(
    stream: BinaryIO,
    *,
    stream_info: StreamInfo | None = None,
    file_extension: str | None = None,
    url: str | None = None,
    **kwargs,
) -> DocumentConverterResult
```

Requirements and behavior:

- The stream must be binary.
- A seekable stream is preferred.
- A non-seekable stream is copied completely into an in-memory `BytesIO`.
- `file_extension` and `url` are legacy hints; prefer `StreamInfo`.

```python
from io import BytesIO

from markitdown import MarkItDown, StreamInfo

payload = b"sample,value\ncontrol,1\ntreated,2\n"
result = MarkItDown().convert_stream(
    BytesIO(payload),
    stream_info=StreamInfo(
        extension=".csv",
        mimetype="text/csv",
        charset="utf-8",
        filename="results.csv",
    ),
)
print(result.markdown)
```

#### `convert_uri()`

```python
convert_uri(
    uri: str,
    *,
    stream_info: StreamInfo | None = None,
    file_extension: str | None = None,
    mock_url: str | None = None,
    **kwargs,
) -> DocumentConverterResult
```

Supported schemes:

- `file:` with an empty authority or `localhost`
- `data:`
- `http:`
- `https:`

HTTP(S) conversion uses the configured `requests.Session`, follows Requests defaults, and then buffers the complete response in memory. It does not provide an application-level SSRF policy, download-size limit, or redirect allowlist. Validate and fetch remote resources yourself before calling `convert_response()`.

`convert_url()` remains a backward-compatible alias, but new code should use `convert_uri()`.

#### `convert_response()`

```python
convert_response(
    response: requests.Response,
    *,
    stream_info: StreamInfo | None = None,
    file_extension: str | None = None,
    url: str | None = None,
    **kwargs,
) -> DocumentConverterResult
```

The method derives hints from `Content-Type`, `Content-Disposition`, and the response URL, then buffers every response chunk into memory. The caller is responsible for destination validation, redirect handling, timeout, maximum size, authentication, and TLS policy.

## `StreamInfo`

```python
StreamInfo(
    *,
    mimetype: str | None = None,
    extension: str | None = None,
    charset: str | None = None,
    filename: str | None = None,
    local_path: str | None = None,
    url: str | None = None,
)
```

Examples:

```python
pdf_info = StreamInfo(
    mimetype="application/pdf",
    extension=".pdf",
    filename="paper.pdf",
)

html_info = StreamInfo(
    mimetype="text/html",
    extension=".html",
    charset="utf-8",
    filename="article.html",
)
```

Hints are merged with extension, HTTP header, and Magika content-detection guesses. If a caller-supplied hint conflicts with content detection, MarkItDown may try both guesses.

## `DocumentConverterResult`

```python
DocumentConverterResult(
    markdown: str,
    *,
    title: str | None = None,
)
```

Attributes and conversions:

| Interface | Status |
|---|---|
| `result.markdown` | Canonical converted Markdown |
| `result.title` | Optional source-derived title |
| `result.text_content` | Soft-deprecated alias for `markdown` |
| `str(result)` | Returns `markdown` |

```python
result = MarkI

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

