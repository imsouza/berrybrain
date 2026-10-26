---
id: sciref-dnanexus-integration-python-sdk
name: "Scientific Ref: Python SDK (`dxpy`)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dnanexus-integration): Python SDK (`dxpy`)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dnanexus integration python sdk"
  - "python sdk (`dxpy`)"
keywords:
  - "dnanexus"
  - "integration"
  - "python"
  - "sdk"
  - "specialized"
  - "scientific"
  - "reference"
---

# Python SDK (`dxpy`)

## Quick Navigation

- [Baseline and authentication](#baseline)
- [Handlers and links](#handler-model)
- [Describe and files](#describe)
- [Search](#search)
- [Projects and records](#projects-and-folders)
- [Run executables](#run-executables)
- [Wait and output](#wait-and-output)
- [Exceptions](#exceptions)
- [Low-level API bindings](#low-level-api-bindings)
- [Reliability checklist](#reliability-checklist)

## Baseline

This reference was verified against `dxpy==0.415.0` (released 2026-09-22).
PyPI declares Python 3.8 or newer. This repository recommends Python 3.11+.

For a project:

```bash
uv add "dxpy==0.415.0"
```

For an isolated script:

```bash
uv run --with "dxpy==0.415.0" "script.py"
```

Inspect the installed API without authenticating. From this skill's root:

```bash
uv run --with "dxpy==0.415.0" \
  "scripts/inspect_dxpy.py" --strict
```

## Authentication

`dxpy` uses the same configuration sources as `dx`. Prefer `dx login` for
interactive work and named secret injection for automation.

Never print:

- `DX_SECURITY_CONTEXT`
- API token values
- `dxpy.SECURITY_CONTEXT`
- full process environments

See `authentication.md` for configuration precedence and safe diagnosis.

## Handler Model

Use handlers for objects and executions:

| Class | Purpose |
|---|---|
| `DXFile` | File object |
| `DXRecord` | Structured metadata record |
| `DXApplet` | Project-local executable |
| `DXApp` | Versioned app |
| `DXWorkflow` | Native workflow |
| `DXJob` | App/applet execution |
| `DXAnalysis` | Workflow execution |
| `DXProject` | Project/data container |

Create handlers from IDs:

```python
import dxpy

file_obj = dxpy.DXFile("file-xxxx", project="project-xxxx")
applet = dxpy.DXApplet("applet-xxxx", project="project-xxxx")
app = dxpy.DXApp("app-xxxx")
workflow = dxpy.DXWorkflow("workflow-xxxx", project="project-xxxx")
job = dxpy.DXJob("job-xxxx")
analysis = dxpy.DXAnalysis("analysis-xxxx")
project = dxpy.DXProject("project-xxxx")
```

For an ID or link whose class is not known:

```python
handler = dxpy.get_handler(id_or_link, project="project-xxxx")
```

`get_handler()` accepts a string ID or a mapping containing a DNAnexus link.

## Links

Create a data-object link:

```python
link = dxpy.dxlink("file-xxxx")
```

Include project context for a project-qualified link:

```python
link = dxpy.dxlink("file-xxxx", "project-xxxx")
```

Create a job-based output reference:

```python
output_reference = job.get_output_ref("aligned_bam")
```

Do not wrap a job output reference with `dxpy.dxlink()`. It is already a valid
reference.

## Describe

```python
import dxpy

description = dxpy.describe(
    "file-xxxx",
    fields={"name", "size", "state", "archivalState"},
)
```

Handler:

```python
description = dxpy.DXFile(
    "file-xxxx",
    project="project-xxxx",
).describe(
    fields={"name", "size", "state"}
)
```

Request only needed fields. Object descriptions can contain PHI or internal
metadata.

## Files

### Upload

Verified signature:

```text
upload_local_file(
    filename=None,
    file=None,
    media_type=None,
    keep_open=False,
    wait_on_close=False,
    use_existing_dxfile=None,
    show_progress=False,
    write_buffer_size=None,
    multithread=True,
    **kwargs
)
```

Example:

```python
remote_file = dxpy.upload_local_file(
    "results.vcf.gz",
    project="project-xxxx",
    folder="/results",
    properties={"sample_id": "S001"},
    tags=["validated"],
    wait_on_close=True,
)
```

Exactly one of `filename` or `file` is required. `wait_on_close=True` is useful
when the next operation requires a closed object.

### Download

```python
dxpy.download_dxfile(
    "file-xxxx",
    "results.vcf.gz",
    project="project-xxxx",
    show_progress=True,
)
```

`project` can affect which project/billing context is used for the download.

### Stream

```python
with dxpy.open_dxfile(
    "file-xxxx",
    project="project-xxxx",
) as remote_stream:
    prefix = remote_stream.read(4096)
```

`DXFile.open_file()` does not exist in dxpy 0.415.0. Use
`dxpy.open_dxfile()`.

### Upload a string

```python
report = dxpy.upload_string(
    '{"status":"ok"}\n',
    project="project-xxxx",
    folder="/reports",
    name="status.json",
    media_type="application/json",
    wait_on_close=True,
)
```

Do not use this for credentials or sensitive diagnostic dumps.

## Search

### Data objects

Verified signature includes:

```text
find_data_objects(
    classname=None,
    state=None,
    visibility=None,
    name=None,
    name_mode="exact",
    properties=None,
    typename=None,
    tags=None,
    project=None,
    folder=None,
    recurse=None,
    describe=False,
    limit=None,
    region=None,
    archival_state=None,
    return_handler=False,
    ...
)
```

Example:

```python
results = dxpy.find_data_objects(
    classname="file",
    project="project-xxxx",
    folder="/results",
    recurse=True,
    name="*.vcf.gz",
    name_mode="glob",
    state="closed",
    describe={
        "fields": {
            "name": True,
            "size": True,
            "archivalState": True,
        }
    },
    limit=200,
)

for result in results:
    description = result["describe"]
    print(result["id"], description["name"])
```

Important:

- Searches return generators.
- `name_mode` defaults to exact.
- `tags` means all specified tags.
- `tag` is deprecated.
- `describe=True` returns full default descriptions; a field mapping is safer.
- Omitted `limit` means dxpy keeps paging until all matching results are read.
- In dxpy 0.415.0, an explicit `limit` is also sent as the first API page size;
  keep it at most 1000. To consume a larger bounded result set, use
  `itertools.islice(dxpy.find_data_objects(...), total_limit)` with the SDK
  `limit` omitted, so its internal page sizes remain valid.
- Scope broad searches by project/folder/time.

Timestamps accept:

- Epoch milliseconds
- Negative milliseconds relative to now
- Relative strings such as `"-2d"` or `"-1w"`

### Executions

```python
executions = dxpy.find_executions(
    project="project-xxxx",
    state="failed",
    created_after="-2d",
    include_subjobs=True,
    include_restarted=True,
    describe={"fields": {"name": True, "failureReason": True}},
    limit=100,
)
```

Use:

- `find_executions()` for jobs and analyses
- `find_jobs()` for jobs only
- `find_analyses()` for analyses only

`find_executions()` supports `classname="job"` or
`classname="analysis"`.

## Projects and Folders


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

