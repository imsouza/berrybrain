---
id: sciref-bids-core-workflows
name: "Scientific Ref: BIDS Core Workflows"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (bids): BIDS Core Workflows"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "bids core workflows"
keywords:
  - "bids"
  - "core"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
---

# BIDS Core Workflows

The twelve workflow areas in full, with worked code and commands: directory structure,
`dataset_description.json`, querying with PyBIDS, validation (PyPI wrapper, Deno, legacy
Node, and `.bidsignore`), entities and file naming, DICOM-to-BIDS conversion with
HeuDiConv and dcm2bids, metadata sidecars, events files, the participants file,
derivatives, advanced PyBIDS usage, and running BIDS-Apps.

## Core Workflows

### 1. BIDS Directory Structure

Illustrative single-session layout (include only acquired modalities; not a complete ASL example):

```
my_dataset/
  dataset_description.json      # Required: name, BIDSVersion, etc.
  participants.tsv              # Recommended: subject-level phenotypic data
  participants.json             # Recommended: column descriptions
  README                        # Recommended: dataset documentation
  CHANGES                       # Recommended: version history
  .bidsignore                   # Optional: patterns to exclude from validation
  sub-01/
    anat/
      sub-01_T1w.nii.gz
      sub-01_T1w.json           # Sidecar metadata
    func/
      sub-01_task-rest_bold.nii.gz
      sub-01_task-rest_bold.json
      sub-01_task-rest_events.tsv     # Event timing for task fMRI
      sub-01_task-rest_events.json
    dwi/
      sub-01_dwi.nii.gz
      sub-01_dwi.json
      sub-01_dwi.bvec
      sub-01_dwi.bval
    fmap/
      sub-01_phasediff.nii.gz
      sub-01_phasediff.json
      sub-01_magnitude1.nii.gz
    perf/
      sub-01_asl.nii.gz
      sub-01_asl.json
```

**Key points:**
- Required metadata must be available through matching JSON sidecars and inheritance; a separate JSON file beside every NIfTI is not mandatory
- File names encode entities: `sub-<label>[_ses-<label>][_task-<label>][_acq-<label>][_run-<index>]_<suffix>.<extension>`
- Entity order in filenames is fixed by the specification
- `dataset_description.json` is required at the root; additional files depend on dataset type and modality
- For multiple sessions use `sub-01/ses-pre/anat/sub-01_ses-pre_T1w.nii.gz`; do not mix session and sessionless acquisitions for one subject

### 2. Creating dataset_description.json

```python
import json

dataset_description = {
    "Name": "My Neuroimaging Study",
    "BIDSVersion": "1.11.2",
    "DatasetType": "raw",
    "License": "CC0",
    "Authors": ["First Author", "Second Author"],
    "GeneratedBy": [
        {
            "Name": "HeuDiConv",
            "Version": "1.5.1",
            "CodeURL": "https://github.com/nipy/heudiconv"
        }
    ]
}

with open("dataset_description.json", "w") as f:
    json.dump(dataset_description, f, indent=4)
```

Illustrative provenance: replace author, pipeline, and version values with actual records.
For **derivatives**, set `"DatasetType": "derivative"` and add `"GeneratedBy"` listing the pipeline:

```python
deriv_description = {
    "Name": "fMRIPrep - fMRI PREProcessing",
    "BIDSVersion": "1.11.2",
    "DatasetType": "derivative",
    "GeneratedBy": [
        {
            "Name": "fMRIPrep",
            "Version": "24.1.0",
            "CodeURL": "https://github.com/nipreps/fmriprep"
        }
    ]
}
```

### 3. Querying BIDS Datasets with PyBIDS

```python
from bids import BIDSLayout

# Index BIDS-compatible names; this is not full dataset validation
layout = BIDSLayout("/path/to/bids_dataset")

# Basic queries
subjects = layout.get_subjects()          # ['01', '02', '03', ...]
sessions = layout.get_sessions()          # ['pre', 'post'] or []
tasks = layout.get_tasks()                # ['rest', 'nback']
runs = layout.get_runs()                  # [1, 2] or []

# Find specific files
bold_files = layout.get(
    suffix="bold",
    extension=".nii.gz",
    return_type="filename"
)

# Filter by subject, task, session
nback_sub01 = layout.get(
    subject="01",
    task="nback",
    suffix="bold",
    extension=".nii.gz",
    return_type="filename"
)

# Get metadata from JSON sidecars (automatic inheritance)
metadata = layout.get_metadata(bold_files[0])  # first check that a match exists
tr = metadata["RepetitionTime"]

# Get entity definitions in this layout
entities = layout.get_entities()

# Inspect a matching file and its entity values
bids_file = layout.get(subject="01", suffix="T1w", extension=".nii.gz")[0]
print(bids_file.path)
print(bids_file.get_entities())
```

**Key points:**
- `BIDSLayout` indexes the entire dataset on initialization; for large datasets use `database_path` to cache the index
- Metadata inheritance: a JSON sidecar at a higher level (e.g., root or subject) is inherited by matching files below unless overridden; minimize overrides and resolve ambiguous same-level matches
- Use `return_type="filename"` for paths, `return_type="object"` (default) for `BIDSFile` objects

### 4. Validating BIDS Datasets

#### Using bids-validator via PyPI (recommended)

The `bids-validator-deno` PyPI package bundles the Deno-based validator as a standalone CLI:

```bash
# Install
uv pip install bids-validator-deno
# Use an activated virtual environment so the wrapper can locate its Deno runtime.

# Validate a dataset
bids-validator-deno /path/to/bids_dataset

# Save a full machine-readable report, including NIfTI header checks
bids-validator-deno /path/to/bids_dataset --format json --max-rows -1 --outfile validation.json
# Pin the schema when reproducing a review
bids-validator-deno /path/to/bids_dataset --schema file:///absolute/path/to/bids_schema.json
```

#### Using bids-validator via Deno directly

If Deno is already available, you can install or run the validator without PyPI:

```bash
# Install globally via Deno
deno install -ERWN -g -n bids-validator jsr:@bids/validator

# Or run without installing
deno run -ERWN jsr:@bids/validator /path/to/bids_dataset
```

#### Legacy Node.js validator

The older Node.js-based validator (`npm install -g bids-validator`) is deprecated in favor of the Deno-based version. Use the current schema validator for new work. The PyPI wrapper command is `bids-validator-deno`; the Deno installation above deliberately names its executable `bids-validator`.

Validator 3.0.2 defaults to checking 1000 TSV rows; pass `--max-rows -1` for all rows.
Use `--format json` (`--json` is a deprecated alias in 3.0.2). A local schema must be
a `file:///...` URI, not a bare filesystem path.
`--ignoreNiftiHeaders` skips header-dependent checks and cannot establish full compliance.
The legacy `--ignoreSubjectConsistency` flag is absent. Inspect JSON 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

