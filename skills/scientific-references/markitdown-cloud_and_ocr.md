---
id: sciref-markitdown-cloud-and-ocr
name: "Scientific Ref: Vision, OCR, and Azure Extraction"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (markitdown): Vision, OCR, and Azure Extraction"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "markitdown cloud ocr"
  - "vision, ocr, and azure extraction"
keywords:
  - "markitdown"
  - "cloud"
  - "ocr"
  - "specialized"
  - "scientific"
  - "reference"
  - "vision"
  - "azure"
---

# Vision, OCR, and Azure Extraction

This guide distinguishes four different features that are often conflated:

1. Built-in image metadata/description
2. Official `markitdown-ocr` vision plugin
3. Azure Document Intelligence
4. Azure Content Understanding

All examples target MarkItDown 0.1.8. Hosted examples are illustrative: October 1, 2026 verification used installed SDKs, official source, and synthetic mocked requests, not authenticated service calls.

## Decision Guide

| Requirement | Best fit |
|---|---|
| Describe a standalone JPEG/PNG or images on PPTX slides | Built-in `llm_client` path |
| Read text from PDF/DOCX/PPTX/XLSX embedded images | `markitdown-ocr` |
| OCR scanned PDFs with Azure layout extraction | Document Intelligence |
| Custom fields, YAML front matter, video, or richer multimodal analysis | Content Understanding |
| Data must remain local | Use a separate local OCR/layout parser |

None of the first four options is a local Tesseract workflow.

## Data-Handling Rule

Before using an external service:

- Identify the exact provider, endpoint, region, account, and model/analyzer.
- Tell the user which source bytes, images, audio, video, and prompts will leave the machine.
- Confirm that the provider is approved for the source's classification and regulatory requirements.
- Estimate cost and retention implications.
- Send only the required files/pages.
- Never log API keys, bearer tokens, source bytes, or full base64 payloads.

## Built-in Image Descriptions

The built-in JPEG/PNG and PPTX paths can call an OpenAI-compatible client. MarkItDown encodes image bytes as a data URI and calls:

```text
client.chat.completions.create(model=..., messages=...)
```

Install a reviewed client version:

```bash
uv pip install "markitdown[pptx]==0.1.8" "openai==3.22.1"
```

```python
import os

from markitdown import MarkItDown
from openai import OpenAI

# The SDK obtains only its named provider credential through its normal
# configuration. The image and prompt are sent to that provider.
client = OpenAI()

converter = MarkItDown(
    llm_client=client,
    llm_model=os.environ["MARKITDOWN_VISION_MODEL"],
    llm_prompt=(
        "Describe the scientific figure. Transcribe visible labels, identify "
        "axes and units, and report trends without inventing missing values."
    ),
)

result = converter.convert_local("figure.png")
print(result.markdown)
```

Set `MARKITDOWN_VISION_MODEL` to an approved model supporting image input on Chat Completions. This variable belongs to the example, not MarkItDown itself. Client/model availability is provider-specific. With `OpenAI()`, the SDK reads `OPENAI_API_KEY` and sends `POST https://api.openai.com/v1/chat/completions` using bearer authentication. The body contains `model` and one user message with `text` plus `image_url.url="data:image/png;base64,..."`; MarkItDown reads `choices[0].message.content`. It does not use the image-generation or Responses endpoints. Empty/refused responses require explicit quality checks.

### Limitations

- Built-in image conversion accepts JPEG and PNG.
- Without ExifTool or an LLM client, output can be empty.
- A description is not guaranteed OCR or quantitative chart extraction.
- Generated descriptions can hallucinate labels, values, or relationships.
- Always compare critical claims with the original image.

## Official `markitdown-ocr` Plugin

Core 0.1.6 introduced the official monorepo plugin. The current plugin is 0.1.1 and requires `markitdown>=0.1.8,<0.2.0`; it reuses the core Office image-rendering hooks.

Install exact versions:

```bash
uv pip install \
  "markitdown==0.1.8" \
  "markitdown-ocr==0.1.1" \
  "openai==3.22.1"
```

Review discovery before activation:

```bash
markitdown --list-plugins
```

Configure through Python:

```python
import os

from markitdown import MarkItDown
from openai import OpenAI

converter = MarkItDown(
    enable_plugins=True,
    llm_client=OpenAI(),
    llm_model=os.environ["MARKITDOWN_VISION_MODEL"],
    llm_prompt=(
        "Extract all visible text exactly. Preserve table rows, columns, "
        "symbols, signs, decimal points, and units. Do not summarize."
    ),
)

result = converter.convert_local("scanned-paper.pdf")
print(result.markdown)
```

### Supported plugin paths

- PDF embedded images, interleaved by page position
- Full-page rendering fallback for scanned PDF pages without extractable text
- PyMuPDF rendering fallback for some malformed PDFs
- DOCX embedded images
- PPTX image shapes, placeholders, and grouped images: native LLM captions run first; OCR is the fallback when no caption is returned
- XLSX worksheet images after each sheet's table, not interleaved with cell rows; legacy XLS has no image OCR

OCR blocks are inserted using markers similar to:

```text
*[Image OCR]
<extracted text>
[End OCR]*
```

### Operational behavior

- The plugin registers enhanced converters at priority `-1.0`, ahead of built-ins.
- Selected images/pages can become provider calls. Office OCR caches repeated image bytes per conversion; native PPTX caption calls precede that OCR cache. Do not assume one call per document.
- If a provider call fails, conversion can continue without that image's OCR.
- If no `llm_client` is supplied, the plugin loads but silently falls back to standard conversion.
- Large scanned documents can be expensive and slow because pages are rendered at 300 DPI.

### CLI discrepancy in 0.1.8

The plugin README shows `--llm-client` and `--llm-model`, but MarkItDown 0.1.8's core CLI parser does not define those options. Use the Python API above rather than copying that CLI example.

## Azure Document Intelligence

Install:

```bash
uv pip install "markitdown[az-doc-intel]==0.1.8"
```

The converter sends the complete file to Azure's `prebuilt-layout` analyzer and requests Markdown output. For PDF/images it enables formula extraction, high-resolution OCR, and font-style analysis.

### Authentication

If no explicit credential is supplied, MarkItDown:

1. Uses the named `AZURE_API_KEY` value with `AzureKeyCredential` when present.
2. Otherwise uses `DefaultAzureCredential`.

Prefer workload identity, managed identity, or another `DefaultAzureCredential` source over long-lived keys.

### CLI

```bash
markitdown report.pdf \
  --use-docintel \
  --endpoint "https://RESOURCE.cognitiveservices.azure.com/" \
  -o report.md
```

The CLI requires a filename; stdin is not accepted with this mode.

### Python

```python
from azure.identity 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

