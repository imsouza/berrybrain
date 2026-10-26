---
id: sciref-dnanexus-integration-configuration
name: "Scientific Ref: Current `dxapp.json` Configuration"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dnanexus-integration): Current `dxapp.json` Configuration"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dnanexus integration configuration"
  - "current `dxapp.json` configuration"
keywords:
  - "dnanexus"
  - "integration"
  - "configuration"
  - "specialized"
  - "scientific"
  - "reference"
  - "current"
---

# Current `dxapp.json` Configuration

## Quick Navigation

- [Manifest purpose](#what-dxappjson-controls)
- [Applets versus apps](#applets-versus-apps)
- [Input and output specifications](#input-and-output-specifications)
- [`runSpec`](#runspec)
- [Regional resources](#regional-resources)
- [Retry and timeout policy](#retry-and-timeout-policy)
- [Dependencies](#dependencies)
- [Access requirements](#access-requirements)
- [Validation checklist](#validation-checklist)

## What `dxapp.json` Controls

`dxapp.json` is the source manifest consumed by `dx build` and
`dx build --create-app`. It describes:

- App metadata and version
- Input and output contracts
- Entry-point interpreter and source file
- Application Execution Environment (AEE)
- Dependencies
- Timeout and restart policies
- Requested project, network, and developer permissions
- Region-specific resources

Do not confuse the source manifest with the canonical API payload produced by
the build tool. For field constraints, the API methods `/applet/new`,
`/app/new`, and the I/O and Run Specifications are authoritative.

## Applets Versus Apps

| Requirement | Applet | App |
|---|---|---|
| `name` | Required | Required |
| `runSpec` | Required | Required |
| `version` | Optional | Required |
| `inputSpec` | Recommended | Required |
| `outputSpec` | Recommended | Required |
| Region | Build project region | Declare supported regions |
| Lifecycle | Project data object | Versioned, publishable executable |

An applet without both input and output specifications cannot be added as a
workflow stage.

## Minimal Applet

This is valid JSON; comments are intentionally omitted.

```json
{
  "name": "qc-fastq",
  "inputSpec": [
    {
      "name": "reads",
      "class": "file",
      "patterns": ["*.fastq", "*.fastq.gz"],
      "help": "Input FASTQ file"
    }
  ],
  "outputSpec": [
    {
      "name": "report",
      "class": "file",
      "patterns": ["*.html"]
    }
  ],
  "runSpec": {
    "interpreter": "python3",
    "file": "src/qc_fastq.py",
    "distribution": "Ubuntu",
    "release": "24.04",
    "version": "0"
  }
}
```

The `dxapi` field is optional; it is not a required manifest field.
App names cannot start with `app-`. App versions are nonempty strings using
letters, digits, `.`, `_`, `+`, and `-`; semantic versioning is recommended,
but the API also accepts versions such as `release_2026`.

## Production App Skeleton

Replace the region and instance type with values available to the target
project. Do not copy a static instance list from old documentation.

```json
{
  "name": "qc-fastq",
  "title": "FASTQ quality control",
  "summary": "Creates a quality-control report for one FASTQ file",
  "version": "1.0.0",
  "inputSpec": [
    {
      "name": "reads",
      "label": "Reads",
      "class": "file",
      "patterns": ["*.fastq.gz"],
      "help": "A gzip-compressed FASTQ file"
    }
  ],
  "outputSpec": [
    {
      "name": "report",
      "label": "QC report",
      "class": "file",
      "patterns": ["*.html"]
    }
  ],
  "runSpec": {
    "interpreter": "python3",
    "file": "src/qc_fastq.py",
    "distribution": "Ubuntu",
    "release": "24.04",
    "version": "0",
    "timeoutPolicy": {
      "main": {"hours": 4}
    },
    "executionPolicy": {
      "restartOn": {
        "ExecutionError": 1,
        "UnresponsiveWorker": 2,
        "SpotInstanceInterruption": 2
      },
      "maxRestarts": 3
    }
  },
  "access": {
    "network": []
  },
  "regionalOptions": {
    "aws:us-east-1": {
      "systemRequirements": {
        "main": {
          "instanceType": "mem2_ssd1_v2_x4"
        }
      }
    }
  }
}
```

Run the bundled offline check from this skill's root before building:

```bash
uv run python "scripts/validate_dxapp.py" \
  "path/to/dxapp.json" --kind app --strict
```

## Input and Output Specifications

Common classes:

- Primitives: `string`, `int`, `float`, `boolean`, `hash`
- Data objects: `file`, `record`, `applet`
- Arrays: `array:int`, `array:float`, `array:string`, `array:boolean`,
  `array:file`, `array:record`, and `array:applet`. `array:hash` is not supported.

Every parameter needs a unique `name` and a `class`. Required array inputs are
nonempty; mark an array input optional if an empty value is valid. Useful optional fields
include:

- `label`
- `help`
- `optional`
- `default`
- `choices`
- `patterns`
- `suggestions`
- `group`

Use `patterns` as a user-interface hint, not as a security or content
validation boundary. Validate actual content in app code.

Defaults must match the declared class. File and record defaults use DNAnexus
links, not raw local paths.
`default`, `choices`, and `suggestions` apply only to inputs, not outputs.

## `runSpec`

For the source manifest, set:

```json
{
  "runSpec": {
    "interpreter": "python3",
    "file": "src/main.py",
    "distribution": "Ubuntu",
    "release": "24.04",
    "version": "0"
  }
}
```

Supported combinations at the current baseline:

- Ubuntu 24.04, environment version `0`, `python3` or `bash`
- Ubuntu 20.04, environment version `0`, `python3` or `bash`

Prefer Ubuntu 24.04 for new development. Use 20.04 only for a tested
compatibility requirement and plan migration.

## Regional Resources

### Current placement

For new manifests, place resource requirements under:

```text
regionalOptions.<region>.systemRequirements.<entry-point>
```

The older locations below are deprecated:

- `runSpec.systemRequirements`
- top-level `resources`

They remain accepted for some single-region compatibility cases but should not
be used in new apps.

If one region declares `systemRequirements`, declare it for every region
listed in `regionalOptions` and omit it from `runSpec`. Region-bound asset and resource IDs must also be
available in the corresponding region.

### Fixed instance type

```json
{
  "regionalOptions": {
    "aws:us-east-1": {
      "systemRequirements": {
        "main": {"instanceType": "mem2_ssd1_v2_x4"},
        "process": {"instanceType": "mem3_ssd1_v2_x8"}
      }
    }
  }
}
```

Available instance types differ by cloud and region. Retired types are rejected
when an app or applet is created or updated.

### Dynamic instance selection

Where licensed, provide an ordered fallback list:

```json
{
  "regionalOptions": {
    "aws:us-east-1": {
      "systemRequirements": {
        "main": {
          "instanceTypeSelector": {
            "allowedInstanceTypes": [
              "mem1_ssd1_v2_x4",
              "mem1_ssd1_v2_x8

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

