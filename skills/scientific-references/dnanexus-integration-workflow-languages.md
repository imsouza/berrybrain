---
id: sciref-dnanexus-integration-workflow-languages
name: "Scientific Ref: Workflow Languages and Imports"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dnanexus-integration): Workflow Languages and Imports"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dnanexus integration workflow languages"
  - "workflow languages and imports"
keywords:
  - "dnanexus"
  - "integration"
  - "workflow"
  - "languages"
  - "specialized"
  - "scientific"
  - "reference"
---

# Workflow Languages and Imports

## Choose a Workflow Path

| Source | DNAnexus path |
|---|---|
| Existing apps/applets assembled visually or by API | Native workflow |
| WDL draft-2, 1.0, or 1.1 | dxCompiler |
| CWL 1.2 | dxCompiler |
| Nextflow source folder/repository | `dx build --nextflow` |
| One Python/Bash program | Applet/app, not a workflow |

Keep the source workflow, compiler/importer version, container digests, input
JSON, and generated executable IDs together as provenance.

## Native Workflows

Native workflows connect app/applet stages. Build from a `dxworkflow.json`:

```bash
dx build --workflow "path/to/workflow-source" \
  --destination "project-xxxx:/workflows/my-workflow"
```

Inspect inputs:

```bash
dx run "workflow-xxxx" -h
```

Run:

```bash
dx run "workflow-xxxx" \
  --input-json-file "inputs.json" \
  --destination "project-xxxx:/runs/run-001" \
  --cost-limit 50
```

This returns an `analysis-...` ID. Each stage runs as a job or nested analysis.

Use native workflows when:

- Components already exist as maintained DNAnexus apps/applets.
- Users need UI-editable stage connections.
- The pipeline is small enough to maintain as a native workflow definition.

Promote stable inputs/outputs to workflow-level fields. Keep project-qualified
default links only when the referenced data is deliberately shared and
accessible in every intended context.

## WDL and CWL with dxCompiler

Current baseline: **dxCompiler 2.18.0**.

Supported language versions at that baseline:

- WDL draft-2
- WDL 1.0
- WDL 1.1
- CWL 1.2

WDL 2.0/development support is not production-ready. CWL 1.0 and 1.1 must be
upgraded to 1.2 before compilation.

### Setup

Prerequisites:

- Current `dx` toolkit and authenticated project context
- dxCompiler 2.18.0 JAR from the official GitHub release
- Java 8 or 11
- Docker only if using the documented containerized compiler workflow

Pin the JAR release and verify release checksums or provenance before use. Do
not use an unversioned download URL in production automation.

### Validate WDL

dxCompiler uses strict WDL parsing. Validate and lint with the matching
wdlTools release before compilation.

Then compile:

```bash
java -jar "dxCompiler-2.18.0.jar" compile \
  "workflow.wdl" \
  -project "project-xxxx" \
  -folder "/workflows" \
  -inputs "inputs.json"
```

The compile command can create a DNAnexus-formatted input JSON. Run the
compiled workflow with `dx run` and the generated input file:

```bash
dx run "workflow-xxxx" \
  --input-json-file "inputs.dx.json" \
  --destination "project-xxxx:/runs/run-002" \
  --cost-limit 50
```

Run `java -jar dxCompiler-2.18.0.jar help` for the exact options supported by
that pinned release.

### Authenticated WDL imports

dxCompiler 2.17.0 and later support per-domain bearer tokens for protected HTTP(S) WDL
imports through `DXCOMPILER_WDL_IMPORT_BEARER_TOKENS`.

This variable is highly sensitive:

- Inject only through a secret manager.
- Scope each token to the required import domain.
- Never print or log the variable.
- Never accept an arbitrary import host while credentials are active.
- Remove the variable after compilation.
- Do not embed it in workflow source, inputs, or extras.

Prefer immutable source references and checksum imported WDL dependencies.

### Prepare CWL

dxCompiler expects one packed CWL 1.2 document.

1. Upgrade older CWL to 1.2.
2. Pack imports into one compound document.
3. Validate with `cwltool --validate`.
4. Compile the packed file.

```bash
cwltool --validate "workflow.cwl.json"

java -jar "dxCompiler-2.18.0.jar" compile \
  "workflow.cwl.json" \
  -project "project-xxxx" \
  -folder "/workflows"
```

Pin `cwltool`, the upgrader/packer, and dxCompiler in reproducible
environments.

### Known constraints

Review the current dxCompiler README and release notes before migration. At the
documented baseline, relevant limitations include:

- WDL task/workflow names must be unique across the import tree.
- Some permissive type conversions accepted by other WDL engines are rejected.
- CWL 1.0/1.1 is not compiled directly.
- Calling native DNAnexus apps/applets from CWL through `dxni` is not supported.
- Some CWL requirements and global workflow publication remain unsupported.

Do not promise byte-identical behavior to Cromwell or another CWL runner
without conformance tests.

## Nextflow

Creating a DNAnexus app/applet from Nextflow source requires a DNAnexus license.
Current dx-toolkit supports Nextflow engine versions `25.10` and `24.10`;
`25.10` is the current default and `24.10` is retained only as an unmaintained
compatibility option.

### Repository import

```bash
dx build --nextflow \
  --repository "https://github.com/nextflow-io/hello" \
  --repository-tag "<pinned-tag-or-commit>" \
  --destination "project-xxxx:/applets/hello"
```

Pin a repository tag or commit. Do not import a floating default branch for a
production pipeline.

For a private repository, `--git-credentials` accepts a DNAnexus file. Use a
short-lived, read-only credential and store it in a project whose membership
has been reviewed. Anyone with sufficient project access may be able to read
that file.

### Local source

```bash
dx build --nextflow "path/to/pipeline" \
  --nextflow-version "25.10" \
  --destination "project-xxxx:/applets/my-pipeline"
```

An nf-core-style layout is encouraged but not required.

### Inspect and run

```bash
dx run "applet-xxxx" -h
```

The generated executable exposes fields for Nextflow run options,
configuration files, and a YAML/JSON parameter file. Use the generated help
rather than assuming field names.

```bash
dx run "applet-xxxx" \
  --input-json-file "nextflow-inputs.json" \
  --destination "project-xxxx:/runs/run-003" \
  --cost-limit 100
```

The execution is a head job supervising process subjobs. Monitor both:

```bash
dx watch "job-head"
dx watch "job-child"
dx find jobs --root-execution "job-head"
```

Check current CLI help if a filter name differs; dx-toolkit evolves.

### Offline execution

With dx-toolkit 0.415.0, rebuilt Nextflow applets honor
`nextflow_run_opts="-offline"` and automatically enable offline mode when the
job has no outbound network access. `-offline=false` requests online mode; it
does not grant network permission. Pre-stage required plugins, pipeline
resources, containers, and input data so offline execution does not need a
registry or remote download. Rebuild older applets to incorporate the updated
template, then test a small run under

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

