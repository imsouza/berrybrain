---
id: sciref-nextflow-language
name: "Scientific Ref: Nextflow Language (DSL2)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (nextflow): Nextflow Language (DSL2)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "nextflow language"
  - "nextflow language (dsl2)"
keywords:
  - "nextflow"
  - "language"
  - "specialized"
  - "scientific"
  - "reference"
---

# Nextflow Language (DSL2)

A working reference for the untyped DSL2 interfaces used by many existing nf-core pipelines: processes, channels, operators, workflows, and modules. Nextflow is a Groovy-based DSL; DSL2 is the default and only DSL (DSL1 is removed, so `nextflow.enable.dsl=2` is unnecessary). Targets stable 26.04.6. Source: https://github.com/nextflow-io/nextflow/tree/v26.04.6/docs and https://docs.seqera.io/nextflow/ . Incomplete biological/tool examples below are illustrative; they require the named tools, references and missing module definitions.

**Current syntax conventions**: `NXF_SYNTAX_PARSER=v2` is the default in **26.04** (opt-in in 25.x). Strict syntax does not imply static typing. Typed processes/workflows remain a preview and require `nextflow.enable.types = true` in each applicable script; do not mix their syntax with untyped examples.
- **`channel.of(...)`** (lowercase namespace) is canonical; `Channel.of(...)` still works but is discouraged.
- **Explicit closure parameters** (`{ v -> v * 2 }`) are preferred over the implicit `it`.
- Name process outputs with **`emit:`**; scale resources with **`task.attempt`**.
- **`output {}` + `publish:`** (full feature in 25.10) is the new declarative way to publish results; `publishDir` still works and remains dominant in nf-core — both are shown below.
- Avoid removed/deprecated idioms: `for`/`while` loops (use `each`/`collect`), `import`/custom `class` (use functions or `lib/`), `process shell:` (use `script:`), `include … addParams()`.

## Table of Contents

- [Script structure](#script-structure)
- [Processes](#processes)
- [Process directives](#process-directives)
- [Channels](#channels)
- [Operators](#operators)
- [Workflows](#workflows)
- [Modules](#modules)
- [Dynamic resources and error handling](#dynamic-resources-and-error-handling)
- [Groovy essentials and gotchas](#groovy-essentials-and-gotchas)

## Script structure

A Nextflow script (`.nf`) uses process/workflow definitions and the supported subset of Groovy; strict syntax does not allow arbitrary Groovy. Every script enables DSL2 implicitly (it is the default since 22.03). A run begins at the **unnamed `workflow {}`** block (the entry workflow).

```nextflow
#!/usr/bin/env nextflow

params.input = 'data/*.fastq'        // pipeline parameter with a default

process FASTQC { /* ... */ }          // a process definition

workflow {                            // entry point
    reads = channel.fromPath(params.input, checkIfExists: true)
    FASTQC(reads)
}
```

Run with `nextflow run main.nf --input 'data/*.fastq'`. Parameters declared as `params.x` are overridable on the CLI (`--x`), in `nextflow.config`, or in a `-params-file`.

## Processes

A `process` defines a task: a (usually Bash) script executed in its own isolated **work directory**. Nextflow stages declared inputs in and declared outputs out, so processes never read/write each other's files directly — they communicate only through channels.

```nextflow
process ALIGN {
    tag    "$meta.id"                 // label shown in the log/trace
    label  'process_high'             // maps to resources in config
    // Supply a pinned environment containing BOTH bwa and samtools.
    publishDir "${params.outdir}/bam", mode: 'copy'

    input:
    tuple val(meta), path(reads)      // a sample: metadata map + file(s)
    tuple path(reference), path(index_files)  // shared FASTA + BWA sidecars as a value

    output:
    tuple val(meta), path("*.bam"), emit: bam
    path  "versions.yml",           emit: versions

    when:
    meta.run_alignment != false       // skip task if false

    script:
    def prefix = task.ext.prefix ?: meta.id
    def args   = task.ext.args  ?: ''   // extra flags injected from config
    """
    bwa mem $args -t $task.cpus "$reference" ${reads} | samtools sort -o "${prefix}.bam"

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        bwa: \$(bwa 2>&1 | sed -n 's/Version: //p')
        samtools: \$(samtools --version | sed '1!d; s/samtools //')
    END_VERSIONS
    """

    stub:
    """
    touch ${meta.id}.bam
    touch versions.yml
    """
}
```

### Inputs

Declared one per line under `input:`. Each input consumes one item from a channel.

| Qualifier | Meaning |
|-----------|---------|
| `val(x)` | Any value (string, number, map) |
| `path(f)` | A file/dir; staged into the work dir. Use `path` (not the old `file`) |
| `tuple val(meta), path(reads)` | A composite item — the nf-core standard: a meta map + files |
| `env(NAME)` | Value exposed as an environment variable |
| `stdin` | Feed the channel item to the script's stdin |
| `each x` | Repeat the process once per value in `x` (combinatorial) |

Inputs are positional and matched to channels in call order: `ALIGN(reads_ch, index_ch)`.

### Outputs

Declared under `output:`; each becomes a channel. Use `emit:` to name outputs so callers can reference `ALIGN.out.bam` instead of positional `ALIGN.out[0]`.

| Form | Meaning |
|------|---------|
| `path "*.bam"` | Files matched by glob in the work dir after the script runs |
| `tuple val(meta), path("*.bam")` | Carry metadata forward with the file |
| `val x` | Emit a value computed in the process |
| `stdout` | Capture the script's stdout as the output |
| `eval('cmd')` | Capture the stdout of a command run in the task env (24.04+) — used for tool versions |
| `path "out", emit: name` | Named output channel (reference as `PROC.out.name`) |
| `..., topic: versions` | Also route this output to a named topic channel |
| `path "out", optional: true` | Output may be absent without erroring |

### Script, shell, exec

- **`script:`** (default) — a multi-line string run as Bash. Nextflow variables interpolate with `$var`/`${expr}`; escape shell vars you do NOT want Nextflow to touch as `\$var`.
- **`shell:`** — like script but Nextflow vars use `!{var}`, leaving `$` for the shell. **Deprecated as of 25.04** — use `script:` with `\$` to escape shell vars.
- **`exec:`** — native Groovy, no external process (for in-line computation).
- A process can run any interpreter via a shebang (e.g. `#!/usr/bin/env python`).

```nextflow
process PY {
    input: val x
    output: stdout
    script:
    """
    #!/usr/bin/env python
    print(${x} ** 2)
    """
}
```

### Conditional execution

- `when:` — skip the task when the expression is false (prefer filtering channels upstream when possible).
- A `script:` can branch with normal Groovy `if/else` returning different command

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

