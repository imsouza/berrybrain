---
id: sciref-nextflow-configuration
name: "Scientific Ref: Nextflow Configuration, Executors & CLI"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (nextflow): Nextflow Configuration, Executors & CLI"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "nextflow configuration"
  - "nextflow configuration, executors & cli"
keywords:
  - "nextflow"
  - "configuration"
  - "specialized"
  - "scientific"
  - "reference"
---

# Nextflow Configuration, Executors & CLI

How to configure, scale, cache, observe, and drive Nextflow runs. Targets stable 26.04.6. Sources: [configuration](https://docs.seqera.io/nextflow/config), [runtime config](https://docs.seqera.io/nextflow/reference/config), [executors](https://docs.seqera.io/nextflow/executor), and [cache](https://docs.seqera.io/nextflow/cache-and-resume). HPC/cloud configurations below are illustrative and were not submitted.

## Table of Contents

- [nextflow.config and scopes](#nextflowconfig-and-scopes)
- [Profiles](#profiles)
- [Process selectors](#process-selectors-withname-withlabel)
- [Executors](#executors)
- [Cloud executors](#cloud-executors)
- [Caching and -resume](#caching-and--resume)
- [Tracing and reports](#tracing-and-reports)
- [The nextflow CLI](#the-nextflow-cli)
- [Environment variables](#environment-variables)

## nextflow.config and scopes

`nextflow.config` configures a run **without touching pipeline code**. Files are auto-loaded and merged in **increasing precedence**: (1) `$NXF_HOME/config` (`~/.nextflow/config`), (2) `nextflow.config` in the **project** dir (where the script lives), (3) `nextflow.config` in the **launch** dir (current working dir), (4) each `-c custom.config` (repeatable). Using `-C file` instead loads **only** that file and ignores every other source. CLI `--param`/`-params-file` override config params. Values are grouped into **scopes**.

```groovy
// nextflow.config
params {
    input  = null
    outdir = 'results'
    genome = 'GRCh38'
}

process {
    cpus   = 2
    memory = '4 GB'
    errorStrategy = 'retry'
    maxRetries    = 2
    container = 'ubuntu:22.04'
}

executor {
    queueSize     = 100        // max parallel tasks submitted
    submitRateLimit = '10/1min'
}

docker.enabled = true          // pick ONE container engine
// singularity.enabled = true
// conda.enabled = true

timeline.enabled = true
report.enabled   = true
trace.enabled    = true

manifest {
    name = 'my/pipeline'
    nextflowVersion = '!>=26.04.0'   // enforce a minimum engine version
}
```

Key scopes: `params`, `process`, `executor`, `docker`/`singularity`/`apptainer`/`podman`/`conda`/`wave`, `aws`/`google`/`azure`/`k8s`, `tower` (Seqera Platform), `report`/`timeline`/`trace`/`dag`, `manifest`, `env`, `cleanup`.

Assignment uses `=`. Use the dotted form (`docker.enabled = true`) or block form (`docker { enabled = true }`) interchangeably.

## Profiles

A **profile** is a named bundle of config, activated with `-profile`. nf-core pipelines ship profiles for each container engine plus a `test` profile.

```groovy
profiles {
    standard { process.executor = 'local' }

    docker      { docker.enabled = true; docker.runOptions = '-u $(id -u):$(id -g)' }
    singularity { singularity.enabled = true; singularity.autoMounts = true }
    conda       { conda.enabled = true }

    slurm {
        process.executor = 'slurm'
        process.queue    = 'compute'
    }

    test {
        params.input  = "${baseDir}/assets/test_samplesheet.csv"
        params.genome = 'R64-1-1'
    }
}
```

Activate (combine with commas; **order matters** — later profiles override earlier):

```bash
nextflow run main.nf -profile test,singularity
```

Choose one execution environment profile (`docker`, `singularity`, or `conda`). Site/executor profiles can be combined with it; verify the resolved configuration. If no `-profile` is given, the `standard` profile (if defined) is used.

> Ordering caveat: with the legacy parser, profiles are applied in the **order they are defined in the config**, regardless of CLI order; with the strict parser (default in 26.04) they apply in **CLI order**. To stay safe, avoid combining profiles that set the *same* option to conflicting values.

## Process selectors (withName, withLabel)

Target configuration at specific processes inside the `process` scope. This is how nf-core sets per-tool resources and arguments without editing modules.

```groovy
process {
    // by resource label
    withLabel: 'process_low'    { cpus = 2;  memory = 6.GB;  time = 4.h }
    withLabel: 'process_medium' { cpus = 6;  memory = 36.GB; time = 8.h }
    withLabel: 'process_high'   { cpus = 12; memory = 72.GB; time = 16.h }

    // by process name (regex / fully-qualified WORKFLOW:SUB:PROCESS)
    withName: 'FASTQC' { cpus = 4 }
    withName: '.*:ALIGN' {
        // Keep the module’s pinned environment; it must contain every piped tool.
        ext.args  = '-M'                 // injected into the script as task.ext.args
        publishDir = [ path: { "${params.outdir}/bam" }, mode: 'copy' ]
    }
}
```

Precedence: `withName` overrides `withLabel` overrides generic `process` settings. nf-core keeps all `withName` blocks in `conf/modules.config`.

## Executors

The executor maps tasks onto compute. Default is `local` (subprocesses on the current machine). Set globally or per-process.

```groovy
process.executor = 'slurm'        // global
// or
process { withLabel: 'process_high' { executor = 'slurm'; queue = 'bigmem' } }
```

| Executor | Platform |
|----------|----------|
| `local` | The current machine (default) |
| `slurm` | SLURM clusters |
| `sge` | Sun/Univa-compatible Grid Engine |
| `lsf` | IBM Spectrum LSF |
| `pbs` / `pbspro` | PBS / Torque / PBS Pro |
| `awsbatch` | AWS Batch |
| `google-batch` | Google Cloud Batch |
| `azurebatch` | Azure Batch |
| `k8s` | Kubernetes |
| `flux`, `hyperqueue`, `oar`, `moab` | Other schedulers |

SLURM example with cluster options:

```groovy
process {
    executor   = 'slurm'
    queue      = 'compute'             // SLURM partition
    clusterOptions = '--account=lab123'
}
executor {
    queueSize       = 200              // max jobs queued at once
    submitRateLimit = '10/1min'        // throttle submissions
    perCpuMemAllocation = true         // emit --mem-per-cpu instead of --mem (some clusters require this)
}
```

## Cloud executors

Each cloud needs its scope configured, credentials/permissions, a compatible task image, and a work directory visible to its tasks. AWS/Google/Azure Batch examples below use object storage. Kubernetes commonly uses a shared persistent volume or a supported Fusion setup; object storage is not a universal executor requirement.

```groovy
// AWS Batch
process.executor = 'awsbatch'
process.queue    = 'my-batch-queue'
aws {
    region = 'us-east-1'
    batch.cliPath = '/home/ec2-user/miniconda/bin/aws'
}
workDir = 's3://my-bucket/work'
```

```groovy
// Google Cloud 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

