---
id: sciref-latchbio-integration-nextflow-snakemake
name: "Scientific Ref: Nextflow and Snakemake Integration"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (latchbio-integration): Nextflow and Snakemake Integration"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "latchbio integration nextflow snakemake"
  - "nextflow and snakemake integration"
keywords:
  - "latchbio"
  - "integration"
  - "nextflow"
  - "snakemake"
  - "specialized"
  - "scientific"
  - "reference"
---

# Nextflow and Snakemake Integration

Latch supports Python, Nextflow, and Snakemake workflows, but their packaging
paths are not interchangeable. Confirm the SDK version and choose one track
before generating files.

## Nextflow: Documented SDK Wrapper Path

### Prerequisites

- A runnable Nextflow pipeline
- A `nextflow_schema.json`
- Containers or a documented execution profile for every process
- A pinned Latch SDK

Install:

```bash
uv pip install "latch==2.77.1"
```

### Generate metadata

```bash
latch generate-metadata nextflow_schema.json --nextflow
```

Current generation creates:

```text
latch_metadata/
├── __init__.py
└── generated.py
```

- `generated.py` is regenerated from the schema. Do not edit it.
- Put persistent custom metadata and flow changes in `latch_metadata/__init__.py`.
- Re-run generation after changing `nextflow_schema.json`.
- Review inferred file, enum, default, and required types before registration.

SDK 2.67.0 changed Nextflow generation to use one generated dataclass containing
all parameters and a generated base flow. Older `parameters.py` examples may no
longer match the generated layout.

### Register

The currently documented wrapper command is:

```bash
latch login
latch register . \
  --nf-script main.nf \
  --nf-execution-profile docker,test
```

Registration generates a Latch workflow wrapper and `latch.config`. The exact
entrypoint location depends on the generation path and SDK version.

Important:

- If a root `Dockerfile` exists, registration uses it.
- Otherwise Latch can generate a Dockerfile under `.latch/`.
- Passing `--nf-script` again can regenerate and overwrite wrapper code.
- After intentionally customizing a generated entrypoint, re-register without
  `--nf-script` to preserve it.
- Keep custom code in a separate module when possible.

### Generate an entrypoint explicitly

SDK 2.77.1 also exposes:

```bash
latch nextflow generate-entrypoint . \
  --nf-script main.nf \
  --execution-profile docker,test \
  --output wf/custom_entrypoint.py
```

This requires a valid `NextflowMetadata` object in the metadata root.

### Experimental Forch-only registration

The CLI also has:

```bash
latch nextflow register . --script-path main.nf
```

The official CLI guide marks this command **experimental** and only applicable
to Forch, Latch's architecture for running Nextflow in the user's own AWS
account. It is not a general alternative to `latch register --nf-script`.
Use it only for a configured Forch/BYOC project with current Latch guidance.

### Nextflow configuration rules

- Define every process container.
- Use profiles for environment-specific settings rather than editing the
  pipeline for Latch.
- Keep Latch's generated `latch.config` in the effective config chain.
- Use the official Latch shared-storage guidance for processes that need a
  common work directory.
- Configure private registries through Latch's supported credentials path.
- Follow the Latch GPU guide for process accelerators; do not translate Python
  task decorators into Nextflow resource syntax.
- Set `NextflowRuntimeResources.storage_gib` for the runtime/shared filesystem,
  not just final outputs.
- Understand storage-retention cost before increasing
  `storage_expiration_hours`.

### Debugging

```bash
latch register --staging .
latch develop .
latch nextflow attach --execution-id <execution-id>
```

Within `latch develop`, the production storage initializer is unavailable.
Follow the official debug-mode guidance: use the local executor, bypass the
initializer in debug mode, use a compatible Latch Nextflow base image, and
reduce process resources.

## Snakemake: Choose a Compatibility Track

The current docs and current stable package expose different Snakemake tracks.
Do not mix them.

### Track A: legacy flags in 2.77.1 source (documentation conflict)

The `2.77.1` wheel still exposes the `snakemake` extra, legacy metadata classes,
`generate-metadata --snakemake`, and `register --snakefile`. However, the
official CLI guide marks the Snakemake metadata and registration flags
deprecated and says metadata generation no longer works for
`latch >= 2.55.0.a6`.

Treat this as an unresolved source/documentation conflict. The commands below
are useful when maintaining a legacy project already known to use this path,
but should not be presented as a supported new-project flow without confirming
with current Latch documentation or support.

Use Python 3.11 for the broadest compatibility with the pinned Snakemake 7.x
dependency:

```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip install "latch[snakemake]==2.77.1"
```

Generate metadata from the workflow config:

```bash
latch generate-metadata config.yaml --snakemake
```

Register:

```bash
latch register . --snakefile Snakefile
```

Relevant options:

```bash
latch register . \
  --snakefile Snakefile \
  --metadata-root latch_metadata \
  --cache-tasks
```

Use the current `SnakemakeMetadata`, `SnakemakeParameter`, `FileMetadata`,
`EnvironmentConfig`, and `DockerMetadata` APIs from `latch.types.metadata`.
Inspect their signatures before generating hand-written metadata.

### Track B: official Snakemake v2 tutorial

The current Snakemake v2 tutorial is a compatibility-specific path. At the time
of this refresh, it explicitly requires:

```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip install "latch==2.62.1a2"
```

It uses imports such as:

```python
from latch.types.metadata.snakemake_v2 import SnakemakeV2Metadata
```

and commands such as:

```bash
latch snakemake generate-entrypoint .
latch dockerfile --snakemake -c environment.yaml . -f
latch register -y .
```

Those v2 metadata modules and the `latch snakemake` command group are not
present in the stable 2.77.1 source tree. The tutorial's generated Dockerfile
also pins the workflow runtime separately to
`latch[snakemake]==2.55.0.a6`.

Therefore:

- Re-check the official tutorial's exact pin before starting.
- Use an isolated environment.
- Preserve and review both the local CLI pin and generated runtime pin.
- Do not upgrade that environment to stable 2.77.1 without a migration plan.
- Do not copy v2 imports into a stable-track project.
- Treat the alpha pin as pre-release software and validate end to end.

### Snakemake resource and environment rules

- Give every rule CPU and memory resources or define safe defaults in
  `profiles/default/config.yaml`.
- Pin Conda and container environments.
- Keep the Latch executor/storage plugin

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

