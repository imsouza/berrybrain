---
id: sci-bids
name: "Scientific: bids"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: ">"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "bids"
keywords:
  - "bids"
---

# Brain Imaging Data Structure (BIDS)

## Overview

The Brain Imaging Data Structure (BIDS) is a community standard for organizing and describing neuroscience and biomedical research datasets. It defines a consistent file naming convention, directory hierarchy, and metadata schema so that datasets are immediately understandable by humans and software tools alike. BIDS is governed by the BIDS Specification (reviewed against v1.11.2, released 2026-09-29) and is maintained by the community via the BIDS-Standard GitHub organization.

While BIDS originated for MRI, it has grown well beyond neuroimaging. The specification now covers 11 modalities spanning imaging, electrophysiology, and behavioral data:

- **Imaging**: MRI (structural, functional, diffusion, fieldmaps, perfusion/ASL), PET, microscopy
- **Electrophysiology**: EEG, MEG, iEEG (intracranial EEG), EMG
- **Other**: NIRS (near-infrared spectroscopy), motion capture, behavioral data (without imaging), MR spectroscopy

Active BEPs are extending BIDS further — notably BEP032 (microelectrode electrophysiology) proposes support for extracellular recordings including Neuropixels probes, bringing BIDS to a prevalent methodology in animal neuroscience research (see also the neuropixels-analysis skill).

Repository submission requirements vary by modality and archive; check the target archive before preparing a deposit.

The Python ecosystem for BIDS centers on **PyBIDS** (`pybids`) for querying and indexing BIDS datasets, and the **bids-validator** (Deno-based, available as PyPI package `bids-validator-deno` or via Deno directly) for compliance checking. Conversion from DICOM is typically done with **HeuDiConv**, **dcm2bids**, or **BIDScoin**.

## When to Use This Skill

Apply this skill when:
- Organizing raw neuroscience data (imaging, electrophysiology, behavioral) into BIDS-compliant directory structures
- Querying an existing BIDS dataset to find specific files by subject, session, task, run, or modality
- Validating a dataset against the BIDS specification before sharing or submission
- Converting DICOM data from scanners into BIDS format
- Writing or editing JSON sidecar metadata files
- Creating BIDS-compliant derivatives (preprocessed data, analysis outputs)
- Setting up a `dataset_description.json` for a new dataset
- Working with BIDS entities (subject, session, task, acquisition, run, etc.)
- Configuring `.bidsignore` to exclude files from validation
- Preparing data for upload to OpenNeuro, DANDI, or other BIDS-aware repositories

## Installation

```bash
# Core BIDS querying library
uv pip install pybids

# BIDS validator (Deno-based, installed via PyPI wrapper)
uv pip install bids-validator-deno
# Alternative: install directly via Deno
# deno install -ERWN -g -n bids-validator jsr:@bids/validator

# DICOM-to-BIDS converters (install as needed)
uv pip install heudiconv       # HeuDiConv - heuristic-based DICOM conversion
uv pip install dcm2bids        # dcm2bids - config-file-based conversion
# BIDScoin: uv pip install bidscoin

# Useful companions
uv pip install nibabel          # NIfTI/other neuroimaging file I/O
uv pip install pydicom          # DICOM file reading (used by converters)
```

## Core Workflows

Twelve workflow areas, each with worked code, are documented in
[references/core_workflows.md](references/core_workflows.md):

1. **BIDS directory structure** — the required layout and where each modality belongs.
2. **`dataset_description.json`** — the required fields and how to generate it.
3. **Querying with PyBIDS** — `BIDSLayout`, entity filters, sidecar metadata with
   automatic inheritance, and building paths from entities.
4. **Validation** — `bids-validator` via the PyPI wrapper (recommended), via Deno
   directly, the legacy Node validator, and using `.bidsignore` to exclude files.
5. **Entities and file naming** — the entity order and naming grammar.
6. **DICOM to BIDS conversion** — HeuDiConv (including the turnkey ReproIn path and the
   reconnaissance → heuristic → convert sequence) and dcm2bids (config-file based).
7. **Metadata sidecars** — required and recommended JSON fields per modality.
8. **Events files** — task fMRI event timing and column conventions.
9. **Participants file** — `participants.tsv` and its data dictionary.
10. **Derivatives** — the derivatives layout and its `dataset_description.json`.
11. **Advanced PyBIDS** — index caching, including derivatives, confound regressors, and
    DataFrame output.
12. **BIDS-Apps** — the standard invocation pattern, and fMRIPrep, MRIQC, and QSIPrep.

Validate with the BIDS validator as well as indexing with PyBIDS. Successful indexing
is not a full compliance check; record the validator and BIDS schema versions, and
inspect warnings and metadata inheritance before analysis.

## Reference Materials

This skill includes detailed reference documentation:

- **bids_schema.json**: Machine-readable BIDS schema (from https://bids-specification.readthedocs.io/en/stable/schema.json). This is the authoritative source for entity definitions, ordering rules, filename templates, allowed suffixes per datatype, and metadata field requirements. BEP-specific schemas are at https://github.com/bids-standard/bids-schema/tree/main/BEPs.
- **beps.yml**: Current list of all BIDS Extension Proposals with titles, leads, status, and links (from [bids-website](https://github.com/bids-standard/bids-website/blob/main/data/beps/beps.yml))
- **bids_specification.md**: Human-readable summary of the entity table, datatype reference, directory structure rules, template spaces, and specification changelog
- **metadata_fields.md**: Required and recommended JSON sidecar fields for every BIDS modality (anat, func, dwi, fmap, eeg, meg, pet, etc.)
- **conversion_tools.md**: Detailed workflows for HeuDiConv, dcm2bids, and BIDScoin including heuristic/config examples and troubleshooting

From the skill directory, update schema and BEPs with `python scripts/update_schema.py`.
The bundled snapshot is BIDS 1.11.2 / schema 2.0.0; BEP proposals are not adopted requirements.
If ReadTheDocs blocks an automated fetch, use the documented versioned GitHub export in the updater help.

## Common Issues and Solutions

### 1. Validator reports "Not a BIDS dataset"
**Cause**: Missing `dataset_description.json` at the root.
**Fix**: Create the file with at minimum `{"Name": "...", "BIDSVersion": "1.11.2"}`.

### 2. Inconsistent subjects warning
**Cause**: Not all subjects have the same set of files 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

