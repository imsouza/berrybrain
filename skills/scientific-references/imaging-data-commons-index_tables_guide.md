---
id: sciref-imaging-data-commons-index-tables-guide
name: "Scientific Ref: Index Tables Guide for IDC"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (imaging-data-commons): Index Tables Guide for IDC"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "imaging commons index tables guide"
  - "index tables guide for idc"
keywords:
  - "imaging"
  - "commons"
  - "index"
  - "tables"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
---

# Index Tables Guide for IDC

**Tested with:** idc-index 0.12.5 (IDC data version v24)

This guide covers the structure and access patterns for IDC index tables: programmatic schema discovery, DataFrame access, and join column references. For the overview of available tables and their purposes, see the "Index Tables" section in the main SKILL.md.

**Complete index table documentation:** https://idc-index.readthedocs.io/en/latest/indices_reference.html

## When to Use This Guide

Load this guide when you need to:
- Discover table schemas and column types programmatically
- Access index tables as pandas DataFrames (not via SQL)
- Understand key columns and join relationships between tables

For SQL query examples (filter discovery, finding annotations, size estimation), see `references/sql_patterns.md`.

## Prerequisites

Needs `idc-index` installed — run `python scripts/check_version.py`, which reports the installed
version and prints the install command for the interpreter you are running.

## Available Tables

`SKILL.md` carries a compact map of the table families. This is the full inventory with row
granularity and contents. Always call `client.fetch_index("table_name")` before querying any
of them — it is safe and idempotent for all tables, including those loaded automatically at
startup.

| Table | Row Granularity | Description |
|-------|-----------------|-------------|
| `index` | 1 row = 1 DICOM series | Primary metadata for all current IDC data |
| `version_metadata_index` | 1 row = 1 IDC release version | IDC version release timestamps; join on `idc_version` to correlate series with their release date |
| `collections_index` | 1 row = 1 collection | Collection-level metadata and descriptions |
| `analysis_results_index` | 1 row = 1 analysis result collection | Metadata about derived datasets (annotations, segmentations) |
| `clinical_index` | 1 row = 1 (collection, table, column) triple | Dictionary mapping clinical data table columns to collections |
| `sm_index` | 1 row = 1 slide microscopy series | Slide Microscopy (pathology) series metadata |
| `sm_instance_index` | 1 row = 1 slide microscopy instance | Instance-level (SOPInstanceUID) metadata for slide microscopy |
| `seg_index` | 1 row = 1 DICOM Segmentation series | Segmentation metadata: algorithm, segment count, reference to source image series |
| `ann_index` | 1 row = 1 DICOM ANN series | Microscopy Bulk Simple Annotations series metadata; references annotated image series |
| `ann_group_index` | 1 row = 1 annotation group | Detailed annotation group metadata: graphic type, annotation count, property codes, algorithm |
| `contrast_index` | 1 row = 1 series with contrast info | Contrast agent metadata: agent name, ingredient, administration route (CT, MR, PT, XA, RF) |
| `volume_geometry_index` | 1 row = 1 CT/MR/PT series | 3D volume geometry validation for single-frame CT, MR, and PT series; boolean checks for orientation, spacing, dimensions, and slice positions; composite `regularly_spaced_3d_volume` flag |
| `rtstruct_index` | 1 row = 1 RTSTRUCT series | RT Structure Set metadata: total ROI count, ROI names, generation algorithms, interpreted types, and the referenced image series UID |
| `ct_index` | 1 row = 1 CT series | CT acquisition/reconstruction parameters: pixel spacing, slice thickness, kVp, convolution kernel, tube current (min/max for dose-modulated), exposure, spiral pitch, scan options |
| `mr_index` | 1 row = 1 MR series | MR acquisition/sequence parameters: field strength, scanning sequence, TE (array for multi-echo), TR, flip angle, DiffusionBValue (array for DWI), pixel bandwidth, receive coil, number of temporal positions |
| `pt_index` | 1 row = 1 PET series | PET acquisition/reconstruction/radiopharmaceutical parameters: series type, units, decay/scatter/attenuation correction, reconstruction method, radionuclide, injected dose, frame duration (array for dynamic PET) |
| `prior_versions_index` | 1 row = 1 historical CRDC series version | Historical content, including revised versions with a SeriesInstanceUID still in `index`. Use `crdc_series_uuid` plus `min_idc_version`/`max_idc_version` to pin a revision. For current-release additions use `series_init_idc_version`/`series_revised_idc_version` in `index`; those fields have different semantics. |

## Accessing Index Tables

### Via SQL (recommended for filtering/aggregation)

```python
from idc_index import IDCClient
client = IDCClient()

# Query the primary index (always available)
results = client.sql_query("SELECT * FROM index WHERE Modality = 'CT' LIMIT 10")

# Fetch and query additional indices
client.fetch_index("collections_index")
collections = client.sql_query("SELECT collection_id, cancer_types, tumor_locations FROM collections_index")

client.fetch_index("analysis_results_index")
analysis = client.sql_query("SELECT * FROM analysis_results_index LIMIT 5")
```

### As pandas DataFrames (direct access)

```python
# Primary index (always available after client initialization)
df = client.index

# Fetch and access on-demand indices
client.fetch_index("sm_index")
sm_df = client.sm_index
```

## Discovering Table Schemas

The `indices_overview` dictionary contains complete schema information for all tables.
Schema `mode: REPEATED` means a list-valued column; `type: STRING` alone does not imply
a scalar string. Inspect both fields, or use `DESCRIBE` after fetching the table. **Always consult this when writing queries or exploring data structure.**

**DICOM attribute mapping:** Many columns are populated directly from DICOM attributes in the source files. The column description in the schema indicates when a column corresponds to a DICOM attribute (e.g., "DICOM Modality attribute" or references a DICOM tag). This allows leveraging DICOM knowledge when querying — standard DICOM attribute names like `PatientID`, `StudyInstanceUID`, `Modality`, `BodyPartExamined` work as expected.

```python
from idc_index import IDCClient
client = IDCClient()

# List all available indices with descriptions
for name, info in client.indices_overview.items():
    print(f"\n{name}:")
    print(f"  Installed: {info['installed']}")
    print(f"  Description: {info['description']}")

# Get complete schema for a specific index (columns, types, descriptions)
schema = client.indices_overview["index"]["schema"]
print(f"\nTable: {schema['table_description']}")
print("\nColumns:")
for col in schema['columns']:
    desc = col.get('description', 'No description')
  

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

