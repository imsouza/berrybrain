---
id: sciref-imaging-data-commons-cli-guide
name: "Scientific Ref: idc-index Command Line Interface Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (imaging-data-commons): idc-index Command Line Interface Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "imaging commons cli guide"
  - "idc-index command line interface guide"
keywords:
  - "imaging"
  - "commons"
  - "cli"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
  - "index"
---

# idc-index Command Line Interface Guide

**Verified:** idc-index 0.12.5 CLI signatures and dry runs, 2026-09-30. Downloads below are illustrative.

The `idc-index` package provides command-line tools for downloading DICOM data from the NCI Imaging Data Commons without writing Python code.

## Installation

Needs `idc-index` installed — run `python scripts/check_version.py`, which reports the installed
version and prints the install command for the interpreter you are running.

After installation, the `idc` command is available in your terminal.

In 0.12.5, Boolean options take a value: `--dry-run true`, `--show-progress-bar true`,
`--use-s5cmd-sync true`, `--quiet false`, `--validate-manifest true`. They are not bare flags.
Always include a selection. In 0.12.5 an entirely omitted selection errors; do not rely
on this implementation detail to limit a transfer.

## Available Commands

| Command | Purpose |
|---------|---------|
| `idc download` | General-purpose download with auto-detection of input type |
| `idc download-from-manifest` | Download from manifest file with validation and progress tracking |
| `idc download-from-selection` | Filter-based download with multiple criteria |

---

## idc download

General-purpose download command that intelligently interprets input. It determines whether the input corresponds to a manifest file path or a list of identifiers (collection_id, PatientID, StudyInstanceUID, SeriesInstanceUID, crdc_series_uuid).

### Usage

```bash
# Download entire collection
idc download rider_pilot --download-dir ./data

# Download specific series by UID
idc download "1.3.6.1.4.1.9328.50.1.69736" --download-dir ./data

# Download multiple items (comma-separated)
idc download "tcga_luad,tcga_lusc" --download-dir ./data

# Download from manifest file (auto-detected because the file exists)
idc download manifest.txt --download-dir ./data
```

### Options

| Option | Description |
|--------|-------------|
| `--download-dir` | Destination directory (default: current directory) |
| `--dir-template` | Directory hierarchy template (default: `%collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID`) |
| `--log-level` | Verbosity: debug, info, warning, error, critical |

### Directory Template Variables

The same templates apply in Python, where the argument is `dirTemplate=` rather than the
`--dir-template` flag. The default is
`%collection_id/%PatientID/%StudyInstanceUID/%Modality_%SeriesInstanceUID`:

```python
# Simplified hierarchy (omit StudyInstanceUID level)
client.download_from_selection(
    downloadDir="./data",
    collection_id="tcga_luad",
    dirTemplate="%collection_id/%PatientID/%Modality"
)
# Results in: ./data/tcga_luad/TCGA-05-4244/CT/

# dirTemplate="" disables the hierarchy, writing every file straight into downloadDir
```

Use these variables in `--dir-template` to organize downloads:

- `%collection_id` - Collection identifier
- `%PatientID` - Patient identifier
- `%StudyInstanceUID` - Study UID
- `%SeriesInstanceUID` - Series UID
- `%Modality` - Imaging modality (CT, MR, PT, etc.)

**Examples:**

```bash
# Flat structure (all files in one directory)
idc download rider_pilot --download-dir ./data --dir-template ""

# Simplified hierarchy
idc download rider_pilot --download-dir ./data --dir-template "%collection_id/%PatientID/%Modality"
```

---

## idc download-from-manifest

Specialized for downloading from manifest files with built-in validation, progress tracking, and resume capability.

### Usage

```bash
# Basic download from manifest
idc download-from-manifest --manifest-file cohort.txt --download-dir ./data

# With progress bar and validation
idc download-from-manifest --manifest-file cohort.txt --download-dir ./data --show-progress-bar true

# Resume interrupted download with s5cmd sync
idc download-from-manifest --manifest-file cohort.txt --download-dir ./data --use-s5cmd-sync true
```

### Options

| Option | Description |
|--------|-------------|
| `--manifest-file` | **Required.** Path to manifest file containing S3 URLs |
| `--download-dir` | **Required.** Destination directory |
| `--validate-manifest true` | Validate manifest before download (enabled by default) |
| `--show-progress-bar true` | Display download progress |
| `--use-s5cmd-sync true` | Enable resumable downloads - skips already-downloaded files |
| `--quiet true` | Suppress subprocess output |
| `--dir-template` | Directory hierarchy template |
| `--log-level` | Logging verbosity |

### Manifest File Format

Manifest files contain S3 URLs, one per line. A CSV of bare DICOM UIDs is not a download
manifest; `idc download existing-file.csv` treats it as a manifest and fails validation:

```
s3://idc-open-data/cb09464a-c5cc-4428-9339-d7fa87cfe837/*
s3://idc-open-data/88f3990d-bdef-49cd-9b2b-4787767240f2/*
```

**How to get a manifest file:**

1. **IDC Portal**: Export cohort selection as manifest
2. **Python query**: Generate from SQL results

```python
from idc_index import IDCClient

client = IDCClient()
results = client.sql_query("""
    SELECT series_aws_url
    FROM index
    WHERE collection_id = 'rider_pilot' AND Modality = 'CT'
""")

with open('ct_manifest.txt', 'w') as f:
    for url in results['series_aws_url']:
        f.write(url + '\n')
```

---

## idc download-from-selection

Download data using one explicit identifier selection. In 0.12.5 the SDK uses the most
specific supplied selector, not the intersection of all selectors: CRDC UUID, SOP UID
(Python only), series UID, study UID, patient ID, then collection ID. Higher-level filters
are ignored when a more specific one is supplied. For a conjunction, query SQL first and
pass the resulting series UIDs or URL manifest.

### Usage

```bash
# Download by collection
idc download-from-selection --collection-id rider_pilot --download-dir ./data

# Download specific series
idc download-from-selection --series-instance-uid "1.3.6.1.4.1.9328.50.1.69736" --download-dir ./data

# Patient selection (the more-specific patient ID takes precedence over collection)
idc download-from-selection --collection-id nlst --patient-id "100004" --download-dir ./data

# Dry run - see what would be downloaded without actually downloading
idc download-from-selection --collection-id tcga_luad --dry-run true --download-dir ./data
```

### Options

| Option | Description |
|--------|-------------|
| `--download-dir` | **Required.** Destination directory |
| `--collection-id` | Filter by collection identifier |
| `--

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

