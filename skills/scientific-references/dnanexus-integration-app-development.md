---
id: sciref-dnanexus-integration-app-development
name: "Scientific Ref: App and Applet Development"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dnanexus-integration): App and Applet Development"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dnanexus integration app development"
  - "app and applet development"
keywords:
  - "dnanexus"
  - "integration"
  - "app"
  - "development"
  - "specialized"
  - "scientific"
  - "reference"
  - "applet"
---

# App and Applet Development

## Quick Navigation

- [Model and source layout](#model)
- [Python and Bash entry points](#python-entry-point)
- [Execution environment](#execution-environment)
- [Local testing](#separate-pure-logic-from-platform-io)
- [Build and platform tests](#build)
- [Subjobs, reuse, and errors](#subjobs-and-parallelism)
- [Publish checklist](#publish-checklist)

## Model

- **Applet**: immutable executable data object in one project; best for
  development, testing, and project-local tools.
- **App**: versioned executable that can be authorized, published, and run
  across projects/regions; best for maintained reusable products.
- **Job**: execution of an app or applet.
- **Entry point**: named function within an executable. `main` is used for a
  normal app/applet run; other entry points can be launched as subjobs.

Develop as an applet, test in a non-production project, then create and publish
an app only after reviewing code, permissions, dependencies, and regions.

## Source Layout

```text
my-app/
├── dxapp.json
├── src/
│   └── my_app.py
├── resources/
│   └── requirements.txt
└── test/
    ├── input.json
    └── expected.json
```

`resources/` is bundled into the executable. Never place tokens, private keys,
registry passwords, or patient data in it.

## Create a Skeleton

```bash
dx-app-wizard
```

The wizard supports templates such as:

- `basic`
- `parallelized`
- `scatter-process-gather`

The generated code is a starting point, not a production security boundary.
Review all access and dependency fields.

## Python Entry Point

The following adapter is illustrative: `quality-filter` is a placeholder for
your tested scientific tool, not a bundled executable. It has not been run on
a DNAnexus worker during this documentation review.

```python
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import dxpy


@dxpy.entry_point("main")
def main(reads: dict[str, Any], min_quality: int = 20) -> dict[str, Any]:
    if not 0 <= min_quality <= 93:
        raise dxpy.AppError("min_quality must be between 0 and 93")

    input_path = Path("reads.fastq.gz")
    output_path = Path("filtered.fastq.gz")

    reads_file = dxpy.get_handler(reads)
    if not isinstance(reads_file, dxpy.DXFile):
        raise dxpy.AppError("reads must reference a DNAnexus file")

    dxpy.download_dxfile(reads_file, str(input_path))

    # Fixed executable + argv list; no shell interpretation of user input.
    subprocess.run(
        [
            "quality-filter",
            "--input",
            str(input_path),
            "--output",
            str(output_path),
            "--min-quality",
            str(min_quality),
        ],
        check=True,
    )

    report = dxpy.upload_local_file(
        str(output_path),
        wait_on_close=True,
    )
    return {"filtered_reads": dxpy.dxlink(report.get_id())}


dxpy.run()
```

Key points:

- `dxpy.get_handler()` accepts an ID or DNAnexus link.
- Pass subprocess arguments as a list. Do not use `shell=True` with inputs.
- Return a mapping whose keys exactly match `outputSpec`.
- Return file/record outputs as DNAnexus links.
- Use `AppError` for an expected, actionable user/input error.
- Do not catch every exception and convert it to success.

The Python execution template reads `job_input.json`, calls the selected entry
point with keyword arguments, and writes the returned mapping to
`job_output.json`.

## Bash Entry Point

```bash
#!/usr/bin/env bash

main() {
  dx download "$reads" --output "reads.fastq.gz"

  quality-filter \
    --input "reads.fastq.gz" \
    --output "filtered.fastq.gz" \
    --min-quality "$min_quality"

  filtered_reads="$(dx upload "filtered.fastq.gz" --brief)"
  dx-jobutil-add-output \
    "filtered_reads" "$filtered_reads" --class=file
}
```

The platform invokes Bash with error-exit behavior. Still quote variables,
validate scalar inputs, and avoid building command strings. Input values are
untrusted even when provided by a trusted platform user.

## Execution Environment

Current AEEs:

- Ubuntu 24.04, version `0`
- Ubuntu 20.04, version `0`

Jobs run on ephemeral workers. The platform:

1. Provisions the worker and app container.
2. Installs `execDepends`.
3. Configures API, networking, and logs.
4. Unpacks bundled dependencies and assets.
5. Runs the selected interpreter/entry point.
6. Captures `stdout` and `stderr`.
7. Processes `job_output.json` or `job_error.json`.
8. Destroys the workspace unless a supported debugging hold is requested.

Useful system-provided values include:

- `DX_JOB_ID`
- `DX_WORKSPACE_ID`
- `DX_PROJECT_CONTEXT_ID`
- `DX_RESOURCES_ID`
- `DX_SECURITY_CONTEXT`

Use `dxpy` rather than parsing these directly where possible. Never print the
security context.

Network access is restricted unless requested in app metadata. Prefer a domain
allowlist; do not request `["*"]` solely to install dependencies at runtime.

## Separate Pure Logic from Platform I/O

Do not use `python src/my_app.py` as the only local test. `dxpy.run()` expects
the platform execution contract.

Instead:

1. Put scientific logic in ordinary functions/modules.
2. Unit-test those functions with local files.
3. Keep the entry point as a thin download → validate → compute → upload
   adapter.
4. Test the packaged applet on DNAnexus with small non-sensitive fixtures.

Example:

```python
def build_command(
    input_path: str,
    output_path: str,
    min_quality: int,
) -> list[str]:
    if not 0 <= min_quality <= 93:
        raise ValueError("min_quality must be between 0 and 93")
    return [
        "quality-filter",
        "--input",
        input_path,
        "--output",
        output_path,
        "--min-quality",
        str(min_quality),
    ]
```

Test `build_command()` locally without credentials.

## Build

Validate offline from this skill's root (or resolve `scripts/` relative to the
loaded skill directory):

```bash
uv run python "scripts/validate_dxapp.py" \
  "/path/to/my-app/dxapp.json" --kind applet --strict
```

Build an applet:

```bash
dx build "my-app"
```

Build a versioned app:

```bash
dx build "my-app" --create-app
```

Use `dx build --help` from the installed toolkit for destination, overwrite,
regional, and advanced flags; these evolve with dx-toolkit.

After build:

```bash
dx describe "applet-xxxx"
dx run "applet-xxxx" -h
```

Verify:

- Input/output fields and defaults
- AEE release
- Regions and instance requirements
- Acce

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

