---
id: sciref-dnanexus-integration-data-operations
name: "Scientific Ref: Data Operations"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dnanexus-integration): Data Operations"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dnanexus integration operations"
  - "data operations"
keywords:
  - "dnanexus"
  - "integration"
  - "operations"
  - "specialized"
  - "scientific"
  - "reference"
---

# Data Operations

## Quick Navigation

- [Safety and lifecycle](#safety-model)
- [Transfer tool selection](#transfer-tool-selection)
- [Small transfers](#small-transfers-with-dx)
- [Upload Agent](#upload-agent)
- [Download Agent](#download-agent)
- [Python transfers](#python-upload-and-download)
- [Search and metadata](#search)
- [Records and folders](#records)
- [Cloning and archival](#cloning)
- [Deletion](#deletion)
- [Batch checklist](#batch-operation-checklist)

## Safety Model

DNAnexus data objects live in projects or other data containers. Before a
mutation:

1. Resolve the project to a `project-...` ID.
2. Resolve every path to an object ID.
3. Detect duplicate names.
4. Inspect state, archival state, size, and relevant metadata.
5. Confirm source/destination permissions and restrictions.
6. Show exact IDs and impact for deletion, cloning, archival, or egress.

Names and paths are convenient for humans but are not immutable identifiers.
Use IDs in automation.

## Object Lifecycle

Files use:

```text
open → closing → closed
```

- `open`: parts/content can still be uploaded.
- `closing`: finalization is in progress; content cannot be read or written.
- `closed`: content is immutable and available to download/share.

Files must be closed before they can be read or cloned. They may be submitted
as job inputs while open or closing, but the job remains `waiting_on_input`
until closure. Open/closing files inactive for about 24 hours are considered
abandoned and are later deleted by the platform.

When a data object closes, content plus types, details/links, and visibility
become fixed. User-editable metadata such as name, properties, and tags can
still be managed according to permissions.

Records may intentionally remain open when mutable structured details are
required. Document this exception because open records weaken reproducibility.

## Transfer Tool Selection

| Workload | Tool |
|---|---|
| One or a few small files | `dx upload`, `dx download` |
| Multiple files or a file larger than 50 MB | Upload Agent (`ua`) |
| Many/large/long-running downloads | Download Agent (`dx-download-agent`) |
| Custom Python automation | `dxpy` |

Use platform transfer agents when resumability and per-part integrity matter.

## Small Transfers with `dx`

Upload:

```bash
dx upload "sample.fastq.gz" \
  --path "project-xxxx:/raw/sample.fastq.gz" \
  --property "sample_id=S001" \
  --tag "raw"
```

Download:

```bash
dx download "project-xxxx:/results/sample.bam" \
  --output "sample.bam"
```

Use quoted full paths. If a name is non-unique, use the object ID.

For scripts, use `--brief` or machine-readable output where supported instead
of parsing human-formatted tables.

Current `dx` warns when a download or generated download URL targets a file
flagged as malicious. Stop on that warning unless the user approves a
containment procedure that prevents execution and protects the local system.

## Upload Agent

Upload Agent is resumable and uses parallel connections. Important behavior:

- Uncompressed files are compressed by default.
- `.gz` is appended to the remote name.
- Already compressed inputs are not recompressed.
- `--do-not-compress` preserves the original bytes/name behavior.
- Repeating the same command resumes a matching incomplete transfer.
- `--wait-on-close` blocks until uploaded file objects are closed.
- Per-part `Content-MD5` is verified by the platform.

Example:

```bash
ua \
  --project "project-xxxx" \
  --folder "/raw" \
  --wait-on-close \
  --progress \
  "sample.fastq.gz"
```

For an uncompressed file that must not be transformed:

```bash
ua \
  --project "project-xxxx" \
  --folder "/raw" \
  --do-not-compress \
  --wait-on-close \
  "reference.fa"
```

Do not run `ua --env` in captured output because it displays the active token.
Treat any Upload Agent `--auth-token` value and the toolkit
`DX_SECURITY_CONTEXT` as secrets.

Use `--do-not-resume` only when creating a deliberate second copy. Otherwise
let the agent resume interrupted uploads.

## Download Agent

Download Agent consumes a BZIP2-compressed JSON manifest. Use the manifest
creation utility from the official `dnanexus/dxda` release and review its
resolved file set before starting egress.

Download Agent checks the secret `DX_API_TOKEN` and otherwise falls back to
`~/.dnanexus_config/environment.json`. This is a Download Agent-specific
variable; do not assume it configures Upload Agent, `dx`, or `dxpy`.

```bash
dx-download-agent download "manifest.json.bz2"
dx-download-agent progress "manifest.json.bz2"
dx-download-agent inspect "manifest.json.bz2"
```

`inspect` revalidates downloaded parts against manifest checksums. If a part is
missing or corrupt, rerun `download`.
Run `inspect` before retrying files that were moved, removed, or changed after
a completed download; a bare `download` trusts its completion database and
does not discover these changes by itself.

Before a large download:

- Confirm local free space.
- Confirm data egress approval and cost.
- Confirm download restrictions/TRE policy.
- Check that all files are live and closed.
- Review the manifest for unexpected projects or PHI.
- Use a token that remains valid for the expected transfer duration.

Do not place an API token in a Docker command line or committed compose file.

## Python Upload and Download

```python
from pathlib import Path

import dxpy

project_id = "project-xxxx"
Path("downloads").mkdir(parents=True, exist_ok=True)

remote = dxpy.upload_local_file(
    "sample.fastq.gz",
    project=project_id,
    folder="/raw",
    properties={"sample_id": "S001"},
    tags=["raw"],
    wait_on_close=True,
    show_progress=True,
)

dxpy.download_dxfile(
    remote,
    str(Path("downloads") / "sample.fastq.gz"),
    project=project_id,
    show_progress=True,
)
```

`project` on download is also a billing/context hint. Pass it when the same file
has copies in multiple projects or the billing context matters.

Read a remote file as a stream:

```python
import dxpy

with dxpy.open_dxfile("file-xxxx", project="project-xxxx") as stream:
    first_chunk = stream.read(1024)
```

`DXFile.open_file()` is not a current dxpy method; use
`dxpy.open_dxfile()`.

## Search

### CLI

```bash
dx find data \
  --class file \
  --path "project-xxxx:/results" \
  --name "*.bam" \
  --name-mode glob
```

Use `dx find data --help` from the installed toolkit for current filter flags.

### dxpy

```python
import dxpy

results = dxpy.find_data_objects(


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

