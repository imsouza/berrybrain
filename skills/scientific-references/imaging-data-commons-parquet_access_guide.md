---
id: sciref-imaging-data-commons-parquet-access-guide
name: "Scientific Ref: Direct Parquet Access Guide for IDC"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (imaging-data-commons): Direct Parquet Access Guide for IDC"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "imaging commons parquet access guide"
  - "direct parquet access guide for idc"
keywords:
  - "imaging"
  - "commons"
  - "parquet"
  - "access"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
  - "direct"
---

# Direct Parquet Access Guide for IDC

**Reviewed 2026-09-30:** idc-index-data 24.2.2 (IDC data version v24), DuckDB 1.5

All idc-index metadata tables are published as Parquet files to a public GCS bucket with unrestricted CORS access. This enables metadata queries with DuckDB or pandas without installing idc-index.

**Limitation:** download helpers (`download_from_selection()`), viewer URLs (`get_viewer_URL()`), and citation generation require the idc-index client and are not available from raw Parquet files.

**This is not the first no-install option to reach for.** It still needs DuckDB installed. This GCS artifact set contains only the `clinical_index` dictionary; full clinical and BigQuery tables are exported separately to public S3 (below). For ad-hoc metadata with nothing installed, the REST API (`rest_api_guide.md`) needs no install at all and reaches `clinical.<table>` through `POST /sql`.

## When to Use This Guide

Load this guide when you need to:
- Pin queries to a specific IDC data version (see *Pinning to a Specific Version* below) rather than whatever the hosted API currently serves
- Return more rows than the REST `/sql` ceiling of 10 000
- Run heavy or repeated local DuckDB analysis without driving the hosted API
- Query IDC metadata where DuckDB is available but idc-index is not

For downloads, viewer URLs, and citations, use idc-index as documented in the main SKILL.md.

## URL Pattern

```
https://storage.googleapis.com/idc-index-data-artifacts/current/release_artifacts/{filename}.parquet
```

`current/` always resolves to the latest data release. To pin to a specific version, replace `current` with the data version number (e.g., `23.10.1`).

## Available Files

| File | Approximate Size | Description |
|------|-----------------|-------------|
| `idc_index.parquet` | ~70 MB | Primary index (all DICOM series metadata) |
| `volume_geometry_index.parquet` | ~5 MB | 3D geometry validation for CT/MR/PT series |
| `rtstruct_index.parquet` | ~2 MB | RT Structure Set ROI metadata |
| `seg_index.parquet` | ~6 MB | DICOM Segmentation cross-references |
| `sm_index.parquet` | ~2 MB | Slide microscopy series metadata |
| `contrast_index.parquet` | ~1 MB | Contrast agent metadata |
| `ann_index.parquet` | ~0.2 MB | Microscopy annotation series metadata |
| `ann_group_index.parquet` | ~0.5 MB | Annotation group metadata |
| `collections_index.parquet` | — | Collection-level metadata |
| `analysis_results_index.parquet` | — | Derived dataset metadata |
| `clinical_index.parquet` | ~0.2 MB | Clinical data column dictionary |
| `ct_index.parquet` | — | CT acquisition/reconstruction parameters |
| `mr_index.parquet` | — | MR sequence/acquisition parameters |
| `pt_index.parquet` | — | PET acquisition/radiopharmaceutical parameters |
| `prior_versions_index.parquet` | — | Series from previous IDC releases |
| `sm_instance_index.parquet` | — | Slide microscopy instance metadata |
| `version_metadata_index.parquet` | — | IDC release timestamps |

**Note:** the main index file is named `idc_index.parquet`, not `index.parquet`. Reference it with an alias in SQL queries (e.g., `FROM read_parquet(...) AS index`).

## Prerequisites

Install the Python `duckdb` package, using whatever installer manages the environment you are
running in.

DuckDB reads Parquet directly from HTTPS URLs using HTTP range requests — no GCS client library or authentication required.

## Basic Queries

```python
import duckdb

BASE = "https://storage.googleapis.com/idc-index-data-artifacts/current/release_artifacts"

# Discover modalities and series counts
duckdb.sql(f"""
    SELECT Modality, COUNT(*) as series_count, ROUND(SUM(series_size_MB)/1000, 1) as size_GB
    FROM read_parquet('{BASE}/idc_index.parquet')
    GROUP BY Modality
    ORDER BY series_count DESC
""").df()

# Collections with CT data, ordered by size
duckdb.sql(f"""
    SELECT collection_id,
           COUNT(DISTINCT PatientID) as patients,
           COUNT(*) as series,
           ROUND(SUM(series_size_MB)/1000, 1) as size_GB
    FROM read_parquet('{BASE}/idc_index.parquet')
    WHERE Modality = 'CT'
    GROUP BY collection_id
    ORDER BY size_GB DESC
    LIMIT 10
""").df()
```

## Volume Geometry Validation

`volume_geometry_index` covers single-frame CT, MR, and PT series. Each row has boolean checks for orientation, spacing, dimensions, and slice positions, plus a composite `regularly_spaced_3d_volume` flag.

```python
import duckdb

BASE = "https://storage.googleapis.com/idc-index-data-artifacts/current/release_artifacts"

# Candidate regularly spaced CT series; verify task-specific geometry before analysis
duckdb.sql(f"""
    SELECT i.collection_id, i.SeriesInstanceUID, i.BodyPartExamined,
           v.obliquity_degrees, v.regularly_spaced_3d_volume
    FROM read_parquet('{BASE}/idc_index.parquet') i
    JOIN read_parquet('{BASE}/volume_geometry_index.parquet') v
        ON i.SeriesInstanceUID = v.SeriesInstanceUID
    WHERE i.Modality = 'CT'
      AND v.regularly_spaced_3d_volume = TRUE
    LIMIT 10
""").df()

# Fraction of 3D-valid series per collection and modality
duckdb.sql(f"""
    SELECT i.collection_id, i.Modality,
           COUNT(*) as total,
           SUM(CASE WHEN v.regularly_spaced_3d_volume THEN 1 ELSE 0 END) as valid_3d,
           ROUND(100.0 * SUM(CASE WHEN v.regularly_spaced_3d_volume THEN 1 ELSE 0 END) / COUNT(*), 1) as pct_valid
    FROM read_parquet('{BASE}/idc_index.parquet') i
    JOIN read_parquet('{BASE}/volume_geometry_index.parquet') v
        ON i.SeriesInstanceUID = v.SeriesInstanceUID
    WHERE i.Modality IN ('CT', 'MR', 'PT')
    GROUP BY i.collection_id, i.Modality
    ORDER BY total DESC
    LIMIT 10
""").df()
```

Key columns in `volume_geometry_index`:

| Column | Type | Description |
|--------|------|-------------|
| `SeriesInstanceUID` | STRING | Join key |
| `single_orientation` | BOOLEAN | All instances share the same ImageOrientationPatient |
| `orthogonal_orientation` | BOOLEAN | Orientation direction cosines are orthogonal |
| `unique_slice_positions` | BOOLEAN | No duplicate or overlapping slices |
| `consistent_pixel_spacing` | BOOLEAN | All instances share the same PixelSpacing |
| `consistent_image_dimensions` | BOOLEAN | All instances share the same Rows and Columns |
| `uniform_slice_spacing` | BOOLEAN | Spacing between consecutive slices is constant |
| `obliquity_degrees` | FLOAT | Angle between slice normal and nearest cardinal axis (0 = pure axial/sagittal/coronal) |
| `regularly

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

