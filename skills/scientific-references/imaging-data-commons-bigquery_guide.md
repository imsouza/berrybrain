---
id: sciref-imaging-data-commons-bigquery-guide
name: "Scientific Ref: BigQuery Guide for IDC"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (imaging-data-commons): BigQuery Guide for IDC"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "imaging commons bigquery guide"
  - "bigquery guide for idc"
keywords:
  - "imaging"
  - "commons"
  - "bigquery"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
---

# BigQuery Guide for IDC

**Reviewed 2026-09-30:** current IDC table documentation and Google BigQuery API/cost guidance.
The GoogleSQL examples below are illustrative; no authenticated BigQuery jobs were run.
Use a dry run against your pinned dataset before executing them.

For most queries and downloads, use `idc-index` (see main SKILL.md). This guide covers BigQuery for advanced use cases requiring full DICOM metadata or complex joins.

## Prerequisites

**Requirements:**
1. Google account
2. Google Cloud project with BigQuery access ([sandbox](https://docs.cloud.google.com/bigquery/docs/sandbox) supports limited public queries without a billing account; billing applies beyond applicable limits)
3. `google-cloud-bigquery[pandas]` Python package for `.to_dataframe()`, or BigQuery console access

**Authentication setup:**
```bash
# Install Google Cloud SDK, then:
gcloud auth application-default login
```

## When to Use BigQuery

Use BigQuery instead of `idc-index` when you need:
- Instance-level DICOM metadata beyond the compact series-level index; extraction has depth/size limits
- Hosted queries across large clinical/imaging tables (local DuckDB and REST also support clinical joins)
- DICOM sequence attributes (nested structures)
- Queries on fields not in the idc-index mini-index
- Private DICOM elements (vendor-specific tags in OtherElements column)
- **Per-segment detail from DICOM Segmentation objects** — `idc-index` `seg_index` gives series-level metadata, but not per-segment rows/number associations; use the `segmentations` table when those details are needed
- **Quantitative measurements from DICOM SR** — radiomics features (volume, diameter, shape descriptors) without downloading and parsing SR files; no idc-index equivalent
- **Qualitative measurements from DICOM SR** — coded evaluations (malignancy rating, texture, margin) without parsing SR files; no idc-index equivalent

## Accessing IDC in BigQuery

The same metadata is also exported as public Parquet in `idc-open-metadata`, including
clinical tables and SR measurements. For an unauthenticated alternative see
`references/parquet_access_guide.md`; large instance-level joins may still favor BigQuery.

### Dataset Structure

All IDC tables are in the `bigquery-public-data` BigQuery project.

**Current version (recommended for exploration):**
- `bigquery-public-data.idc_current.*`
- `bigquery-public-data.idc_current_clinical.*`

**Versioned datasets (recommended for reproducibility):**

- `bigquery-public-data.idc_v{IDC version}.*`
- `bigquery-public-data.idc_v{IDC version}_clinical.*`

Always use versioned datasets for reproducible research!

## Key Tables

### dicom_all
Primary table joining complete DICOM metadata with IDC-specific columns (collection_id, gcs_url, license). Contains exported DICOM fields plus collection and administrative metadata, one row per instance. See [dicom_all.sql](https://github.com/ImagingDataCommons/etl_flow/blob/master/bq/generate_tables_and_views/derived_tables/BQ_Table_Building/derived_data_views/sql/dicom_all.sql) for the exact derivation.

```sql
SELECT 
  collection_id,
  PatientID,
  StudyInstanceUID, 
  SeriesInstanceUID,
  Modality,
  BodyPartExamined,
  SeriesDescription,
  gcs_url,
  license_short_name
FROM `bigquery-public-data.idc_current.dicom_all`
WHERE Modality = 'CT'
  AND BodyPartExamined = 'CHEST'
LIMIT 10
```

### Derived Tables

These tables are derived from DICOM objects (Segmentation and Structured Report) and have **no equivalent in idc-index**. Use them to query per-segment anatomy, radiomics features, and qualitative assessments without downloading DICOM files.

**segmentations** — one row per segment within a DICOM SEG object. Lets you search by anatomical structure name or DICOM coded concept. The `idc-index` `seg_index` gives series-level metadata; this table gives per-segment detail.

**measurement_groups** — one row per SR TID1500 measurement group. The parent grouping for quantitative and qualitative measurements; links measurements to segmentations and source images.

**quantitative_measurements** — one row per numeric measurement within an SR TID1500 group. Contains radiomics features (volume, diameter, shape descriptors, texture) extracted from DICOM SR without downloading or parsing SR files.

**qualitative_measurements** — one row per coded evaluation within an SR TID1500 group. Contains assessed findings (malignancy likelihood, texture, margin type) using coded concept values.

See the [Derived Tables: Detailed Documentation](#derived-tables-detailed-documentation) section below for schemas, column descriptions, and query examples.

### Collection Metadata

**original_collections_metadata** - Collection-level descriptions

```sql
SELECT
  collection_id,
  cancer_types,
  tumor_locations,
  subjects,
  src.source_doi,
  src.modalities,
  src.license.license_short_name
FROM `bigquery-public-data.idc_current.original_collections_metadata`,
UNNEST(sources) AS src
WHERE cancer_types LIKE '%Lung%'
```

## Common Query Patterns

### Find Collections by Criteria

```sql
SELECT 
  collection_id,
  COUNT(DISTINCT PatientID) as patient_count,
  COUNT(DISTINCT SeriesInstanceUID) as series_count,
  ARRAY_AGG(DISTINCT Modality) as modalities
FROM `bigquery-public-data.idc_current.dicom_all`
WHERE BodyPartExamined LIKE '%BRAIN%'
GROUP BY collection_id
HAVING patient_count > 50
ORDER BY patient_count DESC
```

### Get Download URLs

```sql
SELECT
  SeriesInstanceUID,
  gcs_url
FROM `bigquery-public-data.idc_current.dicom_all`
WHERE collection_id = 'rider_pilot'
  AND Modality = 'CT'
```

### Find Studies with Multiple Modalities

```sql
SELECT
  StudyInstanceUID,
  ARRAY_AGG(DISTINCT Modality) as modalities,
  COUNT(DISTINCT SeriesInstanceUID) as series_count
FROM `bigquery-public-data.idc_current.dicom_all`
GROUP BY StudyInstanceUID
HAVING ARRAY_LENGTH(ARRAY_AGG(DISTINCT Modality)) > 1
LIMIT 100
```

### License Filtering

```sql
SELECT
  collection_id,
  license_short_name,
  COUNT(*) as instance_count
FROM `bigquery-public-data.idc_current.dicom_all`
WHERE license_short_name = 'CC BY 4.0'
GROUP BY collection_id, license_short_name
```

### Find Segmentations with Source Images

```sql
SELECT
  src.collection_id,
  seg.SeriesInstanceUID as seg_series,
  seg.SegmentedPropertyType,
  src.SeriesInstanceUID as source_series,
  src.Modality as source_modality
FROM `bigquery-public-data.idc_current.segmentations` seg
JOIN (SELECT DISTINCT SeriesInstanceUID, collectio

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

