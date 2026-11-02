---
id: sci-nextflow
name: "Scientific: nextflow"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Builds, runs, and debugs Nextflow DSL2 pipelines and nf-core workflows. Use for Nextflow, nf-core, .nf files, nextflow.config, processes/channels/operators, samplesheets, nf-test, modules/subworkflows, container and executor configuration, HPC/SLURM or cloud deployment, and faile"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "nextflow"
keywords:
  - "nextflow"
  - "builds"
  - "runs"
  - "debugs"
  - "pipelines"
  - "core"
---

# Nextflow

## Overview

Nextflow is a workflow language and runtime for building **reproducible, portable, scalable** data pipelines. It is dominant in bioinformatics but works for any data-heavy computation. nf-core is a community curating production-grade Nextflow pipelines, reusable modules, and the `nf-core` tooling on top of Nextflow.

Key ideas:
- **Dataflow programming**: pipelines are `process` tasks connected by **channels**. Nextflow infers execution order and parallelism from data dependencies — there is no explicit scheduler to write.
- **Write once, run anywhere**: the same pipeline runs locally, on HPC (SLURM, SGE, LSF, PBS), and on cloud (AWS Batch, Google Batch, Azure Batch, Kubernetes) by changing config/profiles, not code.
- **Reproducibility**: pinned software environments and pipeline revisions, immutable inputs/references, recorded parameters and seeds. `-resume` is a computational cache, not scientific validation. Conda is an environment manager; Wave resolves/builds images rather than executing them.
- **DSL2** is the modern, required syntax: modular `process`/`workflow`/`include` definitions.

This skill covers both **running** existing pipelines and **developing** your own (Nextflow language + nf-core conventions, testing with nf-test, configuration, and deployment).

## When to Use This Skill

Use this skill when the user wants to:
- Run an nf-core or custom Nextflow pipeline, or debug a failing/resuming run.
- Write or modify `.nf` scripts, `nextflow.config`, profiles, or `nextflow_schema.json`.
- Author or test nf-core-style modules/subworkflows (`main.nf`, `meta.yml`, `tests/`, nf-test).
- Configure executors, containers, or resources; scale to HPC or cloud.
- Implement a scientific workflow in Nextflow or adapt an existing nf-core pipeline.
- Understand processes, channels, operators, `take`/`emit`, `publishDir`, `ext.args`, meta maps.

## Setup

This review targets stable **Nextflow 26.04.6**, **nf-core tools 4.1.0**, and **nf-test 0.9.5**. Nextflow needs **Bash 3.2+** and **Java 17–26**; verify `java -version` (a launcher on PATH does not prove a runtime is installed). The strict parser is the default in 26.04. See [release notes](https://github.com/nextflow-io/nextflow/releases/tag/v26.04.6) and the [26.04 migration guide](https://docs.seqera.io/nextflow/migrations/26-04). Stable and edge documentation can differ; do not use a preview feature without its version/flag.

```bash
# Install Nextflow (self-installing launcher)
export NXF_VER=26.04.6
curl -fsSL https://get.nextflow.io -o install-nextflow.sh
# Review the installer before executing it.
bash < install-nextflow.sh
mkdir -p "$HOME/.local/bin"
mv nextflow "$HOME/.local/bin/"
export PATH="$HOME/.local/bin:$PATH"
nextflow info                                # verify

# Alternative (illustrative; confirm package availability and Java compatibility)
conda create -n nf -c conda-forge -c bioconda nextflow=26.04.6 nf-core=4.1.0
```

```bash
# nf-core tools (Python) for creating/linting/running nf-core assets
uv tool install "nf-core==4.1.0"
nf-core --version
```

Pin the engine for reproducibility: `export NXF_VER=26.04.6`; check the selected pipeline release’s engine constraint before upgrading. Use edge only for a required, explicitly tested feature. For air-gapped/HPC, see `references/running-pipelines.md` (offline mode) and `references/configuration.md`.

## Two Modes of Work

Decide which path the user is on — it changes everything:

| Goal | Start here |
|------|-----------|
| **Run** an existing pipeline (nf-core or a `.nf` you were given) | `references/running-pipelines.md` |
| **Develop** a new pipeline / module / subworkflow | `references/language.md` + `references/developing.md` |
| **Configure / scale** (HPC, cloud, containers, resources) | `references/configuration.md` + `references/containers.md` |
| **Test** modules/pipelines | `references/testing.md` |

## Quick Start

### Run an nf-core pipeline

Use the selected release’s small `test` profile first after checking its resource/download requirements. A passing smoke test verifies that configuration and fixture, not scientific accuracy or full-scale capacity. The following RNA-seq examples are illustrative; no biological pipeline or containers were run in this review.

```bash
# 1. Confirm setup works (downloads pipeline + tiny test data)
nextflow run nf-core/rnaseq -r 3.27.0 -profile test,docker --outdir test_results

# 2. Real run: pin a revision (-r), pick a container engine, pass inputs
nextflow run nf-core/rnaseq -r 3.27.0 \
  -profile docker \
  --input samplesheet.csv \
  --fasta reference.fa --gtf annotation.gtf \
  --outdir results \
  -resume
```

- `-profile` (single dash) selects bundled config profiles; **combine** them comma-separated, e.g. `test,docker`. Choose one execution environment profile (`docker`, `singularity`, or `conda`); a site/executor profile can be combined with it when compatible.
- `--input`, `--genome`, `--outdir` (double dash) are **pipeline** parameters. Many nf-core pipelines take a **samplesheet CSV**; use the selected pipeline release’s input schema.
- `-resume` reuses cached results from the last run. `-r <version>` pins a release for reproducibility.

Use `nf-core pipelines launch <name>` for an interactive, schema-validated way to build the command and a `-params-file`. See `references/running-pipelines.md`.

### Write a minimal pipeline

This fixed-input example was executed with Nextflow 26.04.6, including `-resume`. Do not interpolate unvalidated sample IDs or arbitrary text into shell commands.

```nextflow
#!/usr/bin/env nextflow

process SAYHELLO {
    tag "$greeting"
    publishDir "results", mode: 'copy'

    input:
    val greeting

    output:
    path "${greeting}.txt", emit: message

    script:
    """
    echo '$greeting world' > ${greeting}.txt
    """
}

workflow {
    channel.of('hello', 'bonjour', 'hola') | SAYHELLO
}
```

```bash
nextflow run main.nf            # add -resume on reruns
```

The full language (processes, channels, operators, DSL2 workflows with `take`/`main`/`emit`, modules) is in `references/language.md`.

## Core Concepts at a Glance

- **Process**: a unit of work that runs a script (Bash by default). Declares `input:`, `output:`, directives (resources, container, `publishDir`, `tag`, `errorStrategy`), and a `script:` or `exec:` block (`shell:` is deprecated). Each task runs in its own isolated work directory (`work/xx/yy…`).
- **Channel**: the async queue

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

