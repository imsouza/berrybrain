---
id: sciref-liteparse-choosing-a-parser
name: "Scientific Ref: Choosing a Document Parser"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (liteparse): Choosing a Document Parser"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "liteparse choosing parser"
  - "choosing a document parser"
keywords:
  - "liteparse"
  - "choosing"
  - "parser"
  - "specialized"
  - "scientific"
  - "reference"
  - "document"
---

# Choosing a Document Parser

LiteParse **2.15.0** supports text, JSON and Markdown locally. Do not route away
from it solely because the consumer wants Markdown.

| Need | Suitable path |
|---|---|
| Text boxes, page PNGs, local PDF/Office/image parsing | LiteParse |
| Heuristic Markdown from PDFs or converted Office files | LiteParse; visually inspect complex layouts |
| HTML, EPUB, audio or other formats outside LiteParse's supported inputs | Review the `markitdown` skill and its converter dependencies |
| Merge/split/rotate, watermark or fill PDF forms | A PDF manipulation library such as `pypdf` |
| Local extraction fails on dense tables, handwriting or hard scans | Review LlamaParse cloud capabilities, document-sharing authorization and pricing separately |

LiteParse's HTTP OCR is optional and may send rasterized pages to a remote
server. Its bundled Tesseract can download missing language files. A local
parser therefore does not imply a network-free first run.

For layout-aware RAG, store page number, page dimensions and bounding boxes
alongside text; pair the same pages/settings with screenshots. For Markdown,
use `output_format="markdown"` directly and inspect headings, tables, equations,
units and references. No local heuristic parser guarantees faithful scientific
transcription or chart-data recovery.

The general comparison does not certify another parser's current format matrix
or output fidelity. See its own skill/docs before execution. LlamaParse is a
separate cloud service, not an endpoint or drop-in credential for LiteParse's
HTTP OCR contract.

Reviewed 2026-10-01:
[LiteParse overview](https://developers.llamaindex.ai/liteparse/),
[released LiteParse README](https://github.com/run-llama/liteparse/blob/d3a79177b9e9e570f8c2d9878ace601445fdaf76/README.md),
[LlamaParse overview](https://developers.llamaindex.ai/llamaparse/parse/).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

