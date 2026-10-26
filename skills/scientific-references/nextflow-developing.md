---
id: sciref-nextflow-developing
name: "Scientific Ref: Developing nf-core Pipelines, Modules & Subworkflows"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (nextflow): Developing nf-core Pipelines, Modules & Subworkflows"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "nextflow developing"
  - "developing nf-core pipelines, modules & subworkflows"
keywords:
  - "nextflow"
  - "developing"
  - "specialized"
  - "scientific"
  - "reference"
  - "core"
---

# Developing nf-core Pipelines, Modules & Subworkflows

Conventions for building nf-core-compliant components. Reviewed against nf-core tools 4.1.0 templates and current [module specifications](https://nf-co.re/docs/specifications/components/modules/general). The small teaching wrapper was checked locally with SAMtools 1.24; container/Conda execution and full biological pipelines were not tested.

## Table of Contents

- [Pipeline directory layout](#pipeline-directory-layout)
- [The meta map convention](#the-meta-map-convention)
- [Anatomy of a module](#anatomy-of-a-module)
- [meta.yml](#metayml)
- [ext.args and modules.config](#extargs-and-modulesconfig)
- [Subworkflows](#subworkflows)
- [Resource labels and base.config](#resource-labels-and-baseconfig)
- [Schema and parameters](#schema-and-parameters)
- [Linting and the Harshil alignment style](#linting-and-the-harshil-alignment-style)

## Pipeline directory layout

`nf-core pipelines create` scaffolds this structure:

```
my-pipeline/
├── main.nf                     # entry: includes the main workflow
├── nextflow.config             # params defaults, profiles, includes conf/*
├── nextflow_schema.json        # parameter schema (validation + docs + launch GUI)
├── workflows/
│   └── mypipeline.nf           # the primary workflow (orchestrates subworkflows)
├── subworkflows/
│   ├── local/                  # pipeline-specific subworkflows
│   └── nf-core/                # installed shared subworkflows
├── modules/
│   ├── local/                  # pipeline-specific modules
│   └── nf-core/                # installed shared modules
├── conf/
│   ├── base.config             # default resources keyed by process_* labels
│   ├── modules.config          # per-process ext.args, publishDir (withName:)
│   ├── test.config             # tiny test profile inputs
│   └── igenomes.config         # reference genome keys
├── assets/                     # samplesheet schema, email templates, MultiQC config
├── bin/                        # executable helper scripts (on PATH in tasks)
├── docs/                       # usage.md, output.md, parameter docs
├── modules.json                # pins installed nf-core modules/subworkflows by SHA
└── .nf-core.yml                # tools config (lint rules, template features)
```

`main.nf` includes the workflow in `workflows/`; that workflow includes subworkflows and modules. Parameters are declared in `nextflow.config` + `nextflow_schema.json`; per-process behavior lives in `conf/modules.config`. Keep logic in workflows/modules, not in `main.nf`.

## The meta map convention

nf-core carries a **metadata map** alongside every sample's files in input/output tuples. This keeps samples labeled and lets `groupTuple`/`join` operate on the key as data flows through the pipeline.

```nextflow
// channel item shape:
[ [ id:'sample1', single_end:false ], [ sample1_R1.fastq.gz, sample1_R2.fastq.gz ] ]
```

- **Prefer `meta.id` and `meta.single_end`**. Current specifications also recognize `meta.strandedness`, but new modules SHOULD pass strandedness through `ext.args`; direct use is reserved for siblings of tools already following that convention.
- Inside a **module**, avoid custom hardcoded meta keys (the documented strandedness exception above is narrow); pass per-sample values in via `ext.args` from `conf/modules.config` instead (e.g. `ext.args = { "--strandedness ${meta.strandedness}" }`).
- The first meta in a tuple is named `meta`, the second `meta2`, etc. — not custom names.
- Outputs re-emit the **same `meta`** so downstream steps stay aligned: `tuple val(meta), path("*.bam")`.
- Build it from the samplesheet with `splitCsv` + `map` (see `references/language.md`). **Subworkflows** may create/emit new meta keys (document them in `meta.yml`).

Why it matters: decoupling metadata from module logic lets any pipeline name its metadata however it likes while reusing the same module unchanged.

## Anatomy of a module

A module lives in `modules/nf-core/<tool>/<subtool>/` (all lowercase, one command/subcommand per module) with these files:

```
modules/nf-core/samtools/sort/
├── environment.yml     # Conda channels + pinned deps
├── main.nf             # the process
├── meta.yml            # documented I/O + tools (schema-validated)
└── tests/
    ├── main.nf.test    # nf-test tests (required, incl. a stub test)
    └── main.nf.test.snap
```

`environment.yml` (pin the version, not the build):

```yaml
channels:
  - conda-forge
  - bioconda
dependencies:
  - bioconda::samtools=1.24
```

The following **BAM-only teaching wrapper** uses the current topic-version convention; it is not a copy of the installed nf-core `samtools/sort` module. The current upstream module takes three inputs (BAM tuple, reference tuple, index format). Inspect the installed `meta.yml` and pin its SHA before wiring modules together. Keep existing tool pins unless intentionally upgrading.

```nextflow
process SAMTOOLS_SORT {
    tag "$meta.id"                        // per-sample label
    label 'process_medium'                // exactly ONE bundled resource label (conf/base.config)

    conda "${moduleDir}/environment.yml"  // references the file above (NOT inline package strings)
    container "${ workflow.containerEngine in ['singularity', 'apptainer'] && !task.ext.singularity_pull_docker_container ?
        'https://community-cr-prod.seqera.io/docker/registry/v2/blobs/sha256/e9/e994bf4eb3731150511a14f5706b7bdfd64df1b6d40898fff334286c027e0859/data' :
        'community.wave.seqera.io/library/htslib_samtools:1.24--d697cfb9dce007cd' }"

    input:
    tuple val(meta), path(bam)            // meta map is ALWAYS the first tuple element

    output:
    tuple val(meta), path("*.bam"), emit: bam
    tuple val("${task.process}"), val("samtools"),
          eval('samtools --version | sed "1!d; s/samtools //"'),
          emit: versions_samtools, topic: versions

    when:
    task.ext.when == null || task.ext.when           // frozen line; gate via ext.when in config

    script:
    def args   = task.ext.args   ?: ''               // tool flags come from config, never hardcoded
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    samtools sort $args -@ $task.cpus -o ${prefix}.bam $bam

    """

    stub:                                            // required: each required file output is created
    def prefix = task.ext.prefix ?: "${meta.id}"
    """
    touch ${prefix}.bam
    """
}
```

Key module rules:
- **Both** `conda "${moduleDi

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

