---
id: sciref-bids-bids-specification
name: "Scientific Ref: BIDS Specification Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (bids): BIDS Specification Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "bids bids specification"
  - "bids specification reference"
keywords:
  - "bids"
  - "specification"
  - "specialized"
  - "scientific"
  - "reference"
---

# BIDS Specification Reference

> **Note**: The canonical, machine-readable source of truth is `bids_schema.json` (in this directory), exported from the [BIDS Schema](https://github.com/bids-standard/bids-specification/tree/master/src/schema). The tables below are a human-readable summary. Snapshot reviewed against BIDS 1.11.2 / schema 2.0.0 on 2026-09-30. Read rule selectors and prose together; field definitions alone do not establish requiredness.

## Entity Table

Complete list of BIDS entities, their keys, and where they apply. **Rows are listed in the required filename ordering** — entities must appear in this order in BIDS filenames. This order is defined in the schema at `rules.entities` (see `bids_schema.json`).

| # | Entity | Key | Format | Applies to |
|---|--------|-----|--------|------------|
| 1 | Subject | `sub-` | `<label>` | Subject-specific raw data (not dataset-level files) |
| 2 | Template | `tpl-` | `<label>` | derivatives (template-based) |
| 3 | Session | `ses-` | `<label>` | All datatypes |
| 4 | Cohort | `cohort-` | `<label>` | derivatives (template cohorts) |
| 5 | Sample | `sample-` | `<label>` | microscopy |
| 6 | Task | `task-` | `<label>` | func, eeg, meg, ieeg, beh, pet, nirs, motion |
| 7 | Tracking system | `tracksys-` | `<label>` | motion |
| 8 | Acquisition | `acq-` | `<label>` | All datatypes |
| 9 | Nucleus | `nuc-` | `<label>` | MR spectroscopy |
| 10 | Volume | `voi-` | `<label>` | MR spectroscopy |
| 11 | Contrast enhancing agent | `ce-` | `<label>` | anat |
| 12 | Tracer | `trc-` | `<label>` | pet |
| 13 | Stain | `stain-` | `<label>` | microscopy |
| 14 | Reconstruction | `rec-` | `<label>` | anat, func, pet |
| 15 | Direction | `dir-` | `<label>` | fmap, dwi, perf, func |
| 16 | Run | `run-` | `<index>` (integer) | All datatypes |
| 17 | Modality | `mod-` | `<label>` | fieldmaps |
| 18 | Echo | `echo-` | `<index>` | func, fmap |
| 19 | Flip | `flip-` | `<index>` | anat (quantitative MRI) |
| 20 | Inversion | `inv-` | `<index>` | anat (quantitative MRI) |
| 21 | Magnetization transfer | `mt-` | `on`/`off` | anat (quantitative MRI) |
| 22 | Part | `part-` | `mag`/`phase`/`real`/`imag` | anat, func |
| 23 | Processing | `proc-` | `<label>` | eeg, meg, ieeg |
| 24 | Hemisphere | `hemi-` | `L`/`R` | derivatives (surface data) |
| 25 | Space | `space-` | `<label>` | derivatives |
| 26 | Split | `split-` | `<index>` | func, dwi, eeg, meg, ieeg |
| 27 | Recording | `recording-` | `<label>` | physio, stim, eeg, meg |
| 28 | Chunk | `chunk-` | `<index>` | large files split across chunks |
| 29 | Atlas | `atlas-` | `<label>` | derivatives (atlas-based) |
| 30 | Segmentation | `seg-` | `<label>` | derivatives |
| 31 | Scale | `scale-` | `<label>` | derivatives |
| 32 | Resolution | `res-` | `<label>` | derivatives |
| 33 | Density | `den-` | `<label>` | derivatives (surface meshes) |
| 34 | Label | `label-` | `<label>` | derivatives (segmentation labels) |
| 35 | Description | `desc-` | `<label>` | derivatives only |

## Datatypes (Top-Level Directories)

| Datatype | Description | Common Suffixes |
|----------|-------------|-----------------|
| `anat` | Structural MRI | `T1w`, `T2w`, `FLAIR`, `T2starw`, `inplaneT1`, `inplaneT2`, `PDw`, `T1map`, `T2map`, `T1rho`, `UNIT1`, `MP2RAGE`, `MTR`, `MTS` |
| `func` | Functional MRI | `bold`, `cbv`, `sbref` |
| `dwi` | Diffusion-weighted imaging | `dwi`, `sbref` |
| `fmap` | Fieldmaps | `phasediff`, `phase1`, `phase2`, `magnitude1`, `magnitude2`, `fieldmap`, `epi` |
| `perf` | Perfusion imaging (ASL) | `asl`, `m0scan`, `aslcontext` |
| `eeg` | Electroencephalography | `eeg`, `channels`, `electrodes`, `events`, `coordsystem` |
| `meg` | Magnetoencephalography | `meg`, `channels`, `coordsystem`, `events`, `headshape` |
| `ieeg` | Intracranial EEG | `ieeg`, `channels`, `electrodes`, `events`, `coordsystem` |
| `pet` | Positron Emission Tomography | `pet`, `blood` |
| `micr` | Microscopy | `2PE`, `BF`, `CARS`, `CONF`, `DIC`, `DF`, `FLUO`, `MPE`, `NLO`, `OCT`, `PC`, `PLI`, `SRS`, `XPCT` |
| `beh` | Behavioral data (no imaging) | `events`, `beh`, `physio`, `stim` |
| `motion` | Motion capture | `motion`, `channels`, `events` |
| `nirs` | Near-infrared spectroscopy | `nirs`, `channels`, `optodes`, `coordsystem`, `events` |
| `mrs` | MR spectroscopy | `svs`, `mrsi`, `unloc` |
| `emg` | Electromyography | `emg`, `channels`, `electrodes`, `coordsystem`, `events` |
| `phenotype` | Dataset-level phenotypic tables | questionnaire-specific TSV names |

## File Extensions

| Extension | Description |
|-----------|-------------|
| `.nii.gz` | Compressed NIfTI (standard for MRI/fMRI/DWI) |
| `.nii` | Uncompressed NIfTI |
| `.json` | JSON sidecar metadata |
| `.tsv` | Tab-separated values (events, participants, etc.) |
| `.bvec` | b-vectors (DWI gradient directions) |
| `.bval` | b-values (DWI gradient strengths) |
| `.edf` | European Data Format (EEG) |
| `.bdf` | BioSemi Data Format (EEG) |
| `.vhdr`/`.vmrk`/`.eeg` | BrainVision format (EEG) |
| `.set` | EEGLAB format (EEG) |
| `.fif` | Elekta/MEGIN format (MEG) |
| `.ds` | CTF dataset (MEG) |
| `.sqd`/`.con` | KIT/Yokogawa (MEG) |

## Required Files

### Dataset-level (always required)
- `dataset_description.json`

### Dataset-level (recommended)
- `README` or `README.md`
- `CHANGES`
- `participants.tsv` + `participants.json`
- `LICENSE`

### Run-level (recommended)
- `sub-<label>/[ses-<label>/]sub-<label>[_ses-<label>]_scans.tsv` - per-run acquisition metadata

### Modality-specific required files
- **func/bold**: `TaskName` plus valid volume timing metadata; describe recorded events in `_events.tsv` (not every task has recorded events)
- **dwi**: `.bvec` and `.bval` files
- **eeg/meg/ieeg**: consult datatype rules for channel tables and event recordings; iEEG requires electrodes and coordinate metadata. Requirements differ by datatype and format
- **perf/asl**: `_aslcontext.tsv`

## Directory Structure Rules

1. Subject directories are named `sub-<label>` and sit at dataset root
2. For multi-session subjects, use `ses-<label>` directories. When any subject has multiple sessions, this layer SHOULD be added for all subjects (not a universal MUST)
3. Datatype directories (`anat/`, `func/`, etc.) sit inside subject (or session) directories
4. `sourcedata/` stores raw unprocessed data (DICOM, etc.) - not validated
5. `derivatives/` stores processed outputs - each pipeline in its own subdirectory
6. `code/` stores analysis scripts
7. `stimuli/` stores stimulus files used duri

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

