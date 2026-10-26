---
id: sci-latchbio-integration
name: "Scientific: latchbio-integration"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Builds, registers, debugs, and operates bioinformatics workflows on Latch using the Python SDK, CLI, Latch Data and Registry, Nextflow, Snakemake, programmatic execution, and Latch MCP. Use when authoring or deploying Latch workflows, configuring resources or interfaces, moving d"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "latchbio integration"
  - "latchbio-integration"
keywords:
  - "latchbio"
  - "integration"
  - "builds"
  - "registers"
  - "debugs"
  - "operates"
  - "bioinformatics"
  - "workflows"
---

# LatchBio Integration

## Current Baseline

This skill targets **Latch SDK 2.77.1**, released September 17, 2026. The package
metadata supports Python 3.9–3.12 and declares Python 3.9+.

Review status: the SDK imports, documented signatures, CLI help, and selected
workflow graph examples were checked locally with Python 3.12. Network-backed
examples are illustrative: no authenticated registration, data mutation, launch,
or MCP tool call was performed during this refresh.

Treat the installed package and its changelog as authoritative when a guide
disagrees with the SDK. Some Latch guides retain older Python ranges or
compatibility-specific pre-release pins, especially the Snakemake v2 tutorial.
Never combine commands or imports from different tracks without checking their
version requirements.

## When to Use

Use this skill to:

- Create or maintain Python SDK workflows and task graphs
- Package and register Python, Nextflow, or Snakemake pipelines
- Configure task CPU, memory, storage, GPU, caching, retries, and timeouts
- Work with Latch Data through `LPath`, `LatchFile`, `LatchDir`, or the CLI
- Read or update Latch Registry projects, tables, and records
- Design workflow forms, launch plans, samplesheets, messages, and result links
- Stage and debug workflow images with `latch register --staging` and `latch develop`
- Launch and monitor workflows through Python or Latch MCP
- Discover and use ready-to-run Latch workflows

## Route to the Right Reference

Read only the references needed for the task:

| Need | Reference |
|---|---|
| Python workflows, tasks, maps, conditions, caching | `references/workflow-creation.md` |
| `LPath`, legacy file types, Latch URLs, data CLI | `references/data-management.md` |
| Registry reads, transactions, samplesheets | `references/registry.md` |
| CPU, memory, storage, GPU, dynamic resources | `references/resource-configuration.md` |
| Nextflow and Snakemake packaging | `references/nextflow-snakemake.md` |
| Metadata, forms, launch plans, messages, automations | `references/ui-and-automation.md` |
| Registration, development, execution, monitoring | `references/operations-and-debugging.md` |
| Ready-to-use workflows and `latch.verified` | `references/verified-workflows.md` |
| Remote MCP setup and tool workflow | `references/latch-mcp.md` |

Before relying on a symbol, run `scripts/inspect_latch_sdk.py` against the
target SDK version. It performs local imports only and does not authenticate or
make network requests.

## Installation and Authentication

For a reproducible environment:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install "latch==2.77.1"
```

On Windows, use WSL for the documented Linux workflow tooling.

Authenticate through the supported OAuth flow; do not read, print, copy, or
parse `~/.latch/token` manually:

```bash
latch login
latch workspace
```

Select a workspace non-interactively when its numeric ID is already known:

```bash
latch workspace --id 12345
```

`latch login` credentials are for the SDK and CLI. Latch MCP uses a separate
OAuth authorization and its credentials cannot be reused for general SDK
access.

## Fast Path

Create and remotely register the maintained subprocess template:

```bash
latch init covid-wf --template subprocess
latch register --yes --open covid-wf
```

Remote image building is the default. Use `--no-remote` only when a local
Docker daemon is available and a local build is intentional.

## Minimal Python Workflow

Keep workflow bodies declarative: invoke tasks and return their promises.
Perform computation and side effects inside tasks.

```python
from latch import small_task, workflow


@small_task
def reverse_complement(sequence: str) -> str:
    table = str.maketrans("ACGTacgt", "TGCAtgca")
    return sequence.translate(table)[::-1]


@workflow
def reverse_complement_workflow(sequence: str) -> str:
    """Reverse-complement a DNA sequence.

    This minimal example handles A, C, G, and T bases.
    """
    return reverse_complement(sequence=sequence)
```

Use `@workflow(metadata)` when the generated interface needs custom labels,
sections, validation rules, samplesheets, or documentation links. Use `LatchFile` or
`LatchDir` for automatic task input staging and output upload; use `LPath` for
imperative remote path operations.

## Recommended Development Lifecycle

1. **Inspect compatibility**
   - Confirm the installed SDK and Python version.
   - Identify whether the project is Python, Nextflow, the legacy Snakemake
     flag path, or the separately pinned Snakemake v2 tutorial track.

2. **Define a typed interface**
   - Annotate every workflow and task input and output.
   - Keep module import time free of network calls, data mutations, and secret
     retrieval. Isolate documented exceptions such as `workflow_reference`,
     which resolves the active workspace when its decorator is evaluated.
   - Use dataclasses and enums for structured parameters.

3. **Configure metadata and resources**
   - Match metadata parameter keys to the workflow signature.
   - Start with named task decorators, then use `custom_task` only when measured
     requirements justify it.

4. **Validate in the execution image**

   Fresh Nextflow and Snakemake projects must generate their
   version-compatible Python entrypoint before staging. In SDK 2.77.1, the
   staging branch does not generate one from `--nf-script` or `--snakefile`.

   ```bash
   latch register --staging .
   latch develop .
   ```

   Re-run staging registration after changing the Dockerfile or dependencies.
   Edits made inside the development container are not synced back.

5. **Register deliberately**

   ```bash
   latch register --yes --open .
   ```

   Useful controls:

   ```bash
   latch register --workspace-id 12345 .
   latch register --mark-as-release .
   latch register --workflow-module wf.custom_entrypoint .
   ```

   Ordinary duplicate registration exits with status `2`; duplicate **staging**
   registration exits with status `1`. Staging uses the active workspace and
   does not honor `--workspace-id`; select it with `latch workspace --id` first.

6. **Launch only after reviewing cost and parameters**
   - Prefer the Console or Latch MCP for interactive operation.
   - Prefer `latch_cli.services.launch.launch_v2` for Python automation.
   - Do not use the deprecated `latch launch` CLI as a new integration pattern.

7. **Monitor and verify**
   - Check terminal status, task logs, result links, and sci

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

