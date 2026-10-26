---
id: sciref-paperclip-python-sdk
name: "Scientific Ref: GXL Paperclip Python SDK and HTTP contracts"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (paperclip): GXL Paperclip Python SDK and HTTP contracts"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "paperclip python sdk"
  - "gxl paperclip python sdk and http contracts"
keywords:
  - "paperclip"
  - "python"
  - "sdk"
  - "specialized"
  - "scientific"
  - "reference"
---

# GXL Paperclip Python SDK and HTTP contracts

Reviewed on 2026-09-30 against **gxl_paperclip 0.7.92** installed client/source, request-construction
smoke tests with fake HTTP responses, and the public
[OpenAPI 3.1 schema](https://paperclip.gxl.ai/api/v1/openapi.json). Public metadata/unauthenticated
probes were checked; authenticated retrieval, LLM execution, account permissions, uploads, and
repository mutations were not exercised. Remote examples below are illustrative.

## Install and connect

Install the official wheel in an environment you control; the managed CLI's private library is not
on an arbitrary Python interpreter's path. See [installation.md](installation.md).

```bash
uv pip install https://paperclip.gxl.ai/paperclip.whl
```

```python
import gxl_paperclip
from gxl_paperclip import PaperclipClient

print(gxl_paperclip.__version__)
client = PaperclipClient.from_env(no_color=True)
```

Ordinary `from_env()` precedence is `PAPERCLIP_BEARER_TOKEN`, `PAPERCLIP_API_KEY`, then stored OAuth.
It also accepts `base_url`, `timeout`, `user_agent`, `session`, and `no_color`. API keys use
`X-API-Key`; bearer auth uses `Authorization`. `FileCredentialsAuth` can refresh stored OAuth on
401 and retry once. Do not print credentials, authorization headers, or a complete private config.

Explicit auth is useful when a notebook must select exactly one configured identity:

```python
import os
from gxl_paperclip import APIKeyAuth, PaperclipClient

client = PaperclipClient(auth=APIKeyAuth(os.environ["PAPERCLIP_API_KEY"]), no_color=True)
```

The ordinary request timeout is 120 seconds. In this version map defaults to 1,500 seconds,
structured/exhaustive maps have separate longer defaults, and reduce/ask-image default to 300.
These can be environment-configured. Pass a **per-call** `timeout` to override a slow command;
setting the constructor timeout alone does not override every command-specific default.

## Structured search and lookup

```python
result = client.search("CRISPR delivery", source="pmc", limit=5)
if result.exit_code != 0 or result.output.lstrip().startswith("ERR:"):
    raise RuntimeError(result.output)
for paper in result.papers:
    doc_id = paper.get("document_id") or paper.get("id") or paper.get("paper_id")
    if not doc_id:
        raise ValueError("Search hit has no document identifier")
    print(doc_id, paper.get("title"), paper.get("doi"))
print(result.result_id)
```

`ExecuteResult` has `output`, `exit_code`, `elapsed_ms`, `result_id`, `result_data`, `raw`, `cwd`,
`download_url`, and `download_filename`. Newer `papers` and `count` properties expose structured
search/lookup hits. `papers` reads the `papers` or `results` array in `result_data`; `count` uses its
length when nonempty, otherwise a declared count. It is not an independent completeness check.
Search/lookup attempt saved-result hydration if data is absent/truncated; hydration failures can
leave a preview. Compare declared counts/truncation with retrieved rows before calling a cohort
complete. Do not parse ANSI-colored terminal titles to reconstruct IDs.

Supported `search` keyword arguments in 0.7.92:

```text
limit, source, exact, since, sort, author, journal, year, type, category,
mode, min_embedding_similarity, min_bm25_score, all, timeout
```

The wrapper serializes `mode` as `-m`; the CLI's documented spelling is `--ranking`.
The score floors also exist as CLI flags and affect only their respective retrieval legs.
Source/date/ranking caveats are in [search-and-retrieval.md](search-and-retrieval.md).

```python
identified = client.lookup("doi", "10.1073/pnas.2307796121", limit=1)
counts = client.sql("SELECT source, COUNT(*) AS n FROM documents GROUP BY source")
protein_count = client.sql("SELECT COUNT(*) FROM uniprot_v.proteins", source="proteins")
```

Load the current protein domain reference before constructing protein queries. SQL output remains
an `ExecuteResult`, not a guaranteed pandas table.

## Reading and arbitrary commands

```python
import json

path = "/papers/PMC10945750"
metadata_result = client.papers.cat(f"{path}/meta.json")
if metadata_result.exit_code != 0 or metadata_result.output.lstrip().startswith("ERR:"):
    raise RuntimeError(metadata_result.output)
meta = json.loads(metadata_result.output)
opening = client.papers.head(f"{path}/content.lines", lines=40)
ending = client.papers.tail(f"{path}/content.lines", lines=20)
sections = client.papers.ls(f"{path}/sections/")
hits = client.papers.grep("lipid nanoparticle", f"{path}/content.lines", ignore_case=True)
scanned = client.papers.scan(f"{path}/content.lines", ["IC50", "EC50", "dose"])
```

These typed methods preserve argument boundaries and support per-call `timeout`. `papers.grep`
also accepts `extended=True`. Do not assume every metadata source has `journal` or `pub_year`; inspect
keys and use optional access for nullable source-specific fields. `L<n>` prefixes in text are the
source for line citations.

```python
client.execute("grep", ["-n", "-C", "3", "IC50", "/papers/PMC10945750/content.lines"])
```

Use `execute(command, args)` for commands without a wrapper. `bash(script)` exists for server-side
pipelines, but old versions failed on this path and current authenticated behavior was not tested.
Prefer argument lists and local Python composition. `ask_image(path, question=None, fn=None)` returns
an `ExecuteResult`; list the figure directory first. `pull(target, dest=None)` returns textual
metadata and any server-provided download URL; **the SDK does not stream image bytes to `dest`**.
Never interpret `exit_code == 0` as proof that a local image was written.

## Map events and schemas

```python
from gxl_paperclip import MapProgressEvent, MapResultEvent

schema = {
    "type": "object",
    "required": ["effect"],
    "additionalProperties": False,
    "properties": {"effect": {"type": ["number", "null"]}},
}
for event in client.map_(
    "Extract the reported effect; use null when absent.",
    from_results="s_ID", output_schema=schema, timeout=1500.0,
):
    if isinstance(event, MapProgressEvent):
        print(event.completed, event.failed, event.total)
    elif isinstance(event, MapResultEvent):
        if event.exit_code:
            raise RuntimeError(event.output)
        print(event.result_id, event.output)
```

Use `isinstance`; these dataclasses do not provide the `event.type` used in an old website example.
`map_` returns an iterator. On the unified `paperclip.gxl.ai` host, API-key and OAuth maps use the
str

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

