---
id: sciref-bids-conversion-tools
name: "Scientific Ref: BIDS Conversion Tools Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (bids): BIDS Conversion Tools Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "bids conversion tools"
  - "bids conversion tools reference"
keywords:
  - "bids"
  - "conversion"
  - "tools"
  - "specialized"
  - "scientific"
  - "reference"
---

# BIDS Conversion Tools Reference

This reference covers detailed workflows for converting DICOM and other raw data formats to BIDS using the three main conversion tools.

## HeuDiConv

HeuDiConv supports Python heuristic-based DICOM-to-BIDS conversion. It supports three usage modes — from fully automatic turnkey conversion to fully custom heuristics — and handles duplicates, provenance tracking, and sourcedata archiving out of the box.

**Repository**: https://github.com/nipy/heudiconv
**Docs**: https://heudiconv.readthedocs.io/
**Tutorials**: https://heudiconv.readthedocs.io/en/latest/tutorials.html

### Installation

```bash
uv pip install heudiconv

# HeuDiConv wraps dcm2niix for the actual conversion
# Install dcm2niix separately and verify `dcm2niix --version`; for example:
# conda install -c conda-forge dcm2niix
# or: apt-get install dcm2niix
```

### Mode 1: ReproIn (Turnkey Conversion — Recommended for New Studies)

If scanner protocol names follow the [ReproIn naming convention](https://github.com/repronim/reproin), conversion is fully automatic with no heuristic file to write. ReproIn is a setup for automatic generation of sharable, version-controlled BIDS datasets directly from MR scanners.

```bash
# Turnkey conversion — just point at DICOMs, HeuDiConv does the rest
heudiconv --files dicom/001 -o data -f reproin --bids --minmeta
```

#### ReproIn Protocol Naming Rules

Protocol names encode BIDS entities directly. Format: `<seqtype>[-<suffix>][_<entity>-<label>]...`

| Protocol name at scanner | BIDS output |
|--------------------------|-------------|
| `anat-T1w` | `sub-XX/anat/sub-XX_T1w.nii.gz` |
| `func-bold_task-rest` or `func_task-rest` | `sub-XX/func/sub-XX_task-rest_bold.nii.gz` |
| `dwi_dir-AP` | `sub-XX/dwi/sub-XX_dir-AP_dwi.nii.gz` |
| `fmap_dir-PA` or `fmap-epi_dir-PA` | `sub-XX/fmap/sub-XX_dir-PA_epi.nii.gz` |
| `fmap_acq-4mm` | `sub-XX/fmap/sub-XX_acq-4mm_epi.nii.gz` |

**Key features:**
- **Suffixes**: specify anatomical contrast explicitly; ReproIn may infer suffixes from DICOM image type, not a universal `anat` -> `T1w` default
- **Subject ID**: extracted automatically from DICOM metadata (Patient ID)
- **Session**: set once on any sequence (e.g., `anat-scout_ses-pre`) and ReproIn propagates it to all sequences in that scanner Program/Patient
- **Run/duplicate handling**: encode `_run-01` or the documented increment convention. Repeated/cancelled runs can be marked `__dup...`; inspect them rather than assuming every repeat becomes a valid run
- **Locator hierarchy**: output is nested under Region/Exam from the scanner's Study Description (customizable with `--locator`)
- **sourcedata**: original DICOMs are archived as `.tgz` files under `sourcedata/` for reproducibility
- **Dashes in names**: scanners may strip dashes from protocol names during DICOM export — ReproIn handles this gracefully

#### ReproIn Overview

See also:
- [ReproIn Walkthrough](https://github.com/repronim/reproin#walkthrough) for scanner setup
- [ReproNim Webinar slides and recording](https://github.com/repronim/reproin#presentations) on HeuDiConv + ReproIn

### Mode 2: Custom Heuristic Mapping into ReproIn (For Existing Data)

If you already have collected data with non-ReproIn protocol names (or cannot control scanner naming), you can write a thin heuristic that maps your protocol names into ReproIn conventions. This gives you all ReproIn benefits (automatic entity handling, duplicate management, sourcedata archiving) while accommodating arbitrary scanner naming.

See https://github.com/repronim/reproin/issues/18 for a brief HOWTO on this approach.

Use a custom heuristic that imports ReproIn and remaps sequence metadata before delegating to its `infotodict`, or configure its `protocols2fix` substitutions. Merely returning ReproIn-looking keys from an unrelated heuristic does not invoke ReproIn.

### Mode 3: Custom Heuristic (Full Flexibility)

For studies with complex mappings or non-standard requirements, write a full Python heuristic file. This is the most common workflow for retrospective conversion of existing datasets.

#### Step 1: Reconnaissance — Discover DICOM series

```bash
# -f convertall: built-in heuristic that lists all series without converting
# -c none: don't convert, just generate dicominfo.tsv
heudiconv \
    --files dicom/219/itbs/*/*.dcm \
    -s 219 \
    -f convertall \
    -c none \
    -o Nifti/
```

This creates `.heudiconv/219/info/dicominfo.tsv` containing one row per DICOM series with columns:
- `series_id`, `sequence_name`, `protocol_name`, `series_description`
- `dim1`-`dim4` (image dimensions), `TR`, `TE`, `image_type`
- `is_derived`, `is_motion_corrected` — important for filtering

Review this TSV (open in a spreadsheet) to understand what was acquired and plan the mapping to BIDS names. Repeat reconnaissance for protocol variants, sessions and scanners; one participant does not establish all mappings.

#### Step 2: Write a heuristic file

Illustrative study-specific mapping, exercised with synthetic `SeqInfo` records on
HeuDiConv 1.5.1. Confirm actual series before use. Fieldmap phase versus phasedifference
and matching echo pairs require protocol knowledge; `ImageType` alone cannot establish them.

```python
"""HeuDiConv heuristic for a typical fMRI study.

Study design:
- T1w MPRAGE anatomical
- Resting-state BOLD
- Task BOLD (n-back working memory)
- DWI with two phase-encoding directions
- Fieldmap (phase-difference)
"""

def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes


def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where.

    Parameters
    ----------
    seqinfo : list of namedtuples
        Each namedtuple has fields: .series_id, .sequence_name,
        .protocol_name, .series_description, .dim1, .dim2, .dim3, .dim4,
        .TR, .TE, .is_derived, .is_motion_corrected, .image_type, etc.

    Returns
    -------
    info : dict
        Keys are tuples from create_key(), values are lists of series_id
    """
    # Define BIDS output templates
    t1w = create_key(
        '{bids_subject_session_dir}/anat/{bids_subject_session_prefix}_run-{item:02d}_T1w'
    )
    rest_bold = create_key(
        '{bids_subject_session_dir}/func/{bids_subject_session_prefix}_task-rest_run-{item:02d}_bold'
    )
    # {item:02d} auto-numb

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

