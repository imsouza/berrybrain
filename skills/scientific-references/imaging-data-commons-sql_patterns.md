---
id: sciref-imaging-data-commons-sql-patterns
name: "Scientific Ref: SQL Query Patterns for IDC"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (imaging-data-commons): SQL Query Patterns for IDC"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "imaging commons sql patterns"
  - "sql query patterns for idc"
keywords:
  - "imaging"
  - "commons"
  - "sql"
  - "patterns"
  - "specialized"
  - "scientific"
  - "reference"
  - "query"
---

# SQL Query Patterns for IDC

**Tested with:** idc-index 0.12.5 (IDC data version v24)

Quick reference for common SQL query patterns when working with IDC data. For detailed examples with context, see the "Core Capabilities" section in the main SKILL.md.

## When to Use This Guide

Load this guide when you need quick-reference SQL patterns for:
- Discovering available filter values (modalities, body parts, manufacturers)
- Finding annotations and segmentations across collections
- Querying slide microscopy and annotation data
- Estimating download sizes before download
- Linking imaging data to clinical data
- Filtering by 3D volume geometry validity (volume_geometry_index)
- Finding RT Structure Set series and ROI metadata (rtstruct_index)
- Filtering by CT/MR/PET acquisition parameters (ct_index, mr_index, pt_index)

For table schemas, DataFrame access, and join column references, see `references/index_tables_guide.md`.

## Prerequisites

Needs `idc-index` installed — run `python scripts/check_version.py`, which reports the installed
version and prints the install command for the interpreter you are running.

```python
from idc_index import IDCClient
client = IDCClient()
```

## Overall Data Scale

Counts and total size across all of IDC — useful for orienting a user, and for sanity-checking
that the index loaded the release you expect:

```python
stats = client.sql_query("""
    SELECT
        COUNT(DISTINCT collection_id) as collections,
        COUNT(DISTINCT analysis_result_id) as analysis_results,
        COUNT(DISTINCT (collection_id, PatientID)) as patients,
        COUNT(DISTINCT StudyInstanceUID) as studies,
        COUNT(DISTINCT SeriesInstanceUID) as series,
        SUM(instanceCount) as instances,
        SUM(series_size_MB)/1000000 as size_TB
    FROM index
""")
print(stats)
```

### Per-collection breakdown

```python
# Get summary statistics from primary index
collections_summary = client.sql_query("""
    SELECT collection_id,
           COUNT(DISTINCT PatientID) as patients,
           COUNT(DISTINCT SeriesInstanceUID) as series,
           SUM(series_size_MB) as size_mb
    FROM index
    GROUP BY collection_id
    ORDER BY patients DESC
""")
```

For richer per-collection metadata — cancer types, tumor locations, species, supporting data —
query `collections_index` instead; for derived datasets, `analysis_results_index`. Both need
`client.fetch_index(...)` first:

```python
client.fetch_index("collections_index")
collections_info = client.sql_query("""
    SELECT collection_id, cancer_types, tumor_locations, species, subjects, supporting_data
    FROM collections_index
""")

client.fetch_index("analysis_results_index")
analysis_info = client.sql_query("""
    SELECT analysis_result_id, analysis_result_title, subjects, collections, modalities
    FROM analysis_results_index
""")
```

## Discover Available Filter Values

```python
# What modalities exist?
client.sql_query("SELECT DISTINCT Modality FROM index")

# What body parts for a specific modality?
client.sql_query("""
    SELECT DISTINCT BodyPartExamined, COUNT(*) as n
    FROM index WHERE Modality = 'CT' AND BodyPartExamined IS NOT NULL
    GROUP BY BodyPartExamined ORDER BY n DESC
""")

# What manufacturers for MR?
client.sql_query("""
    SELECT DISTINCT Manufacturer, COUNT(*) as n
    FROM index WHERE Modality = 'MR'
    GROUP BY Manufacturer ORDER BY n DESC
""")
```

## Find Annotations and Segmentations

**Note:** Not all image-derived objects belong to analysis result collections. Some annotations are deposited alongside original images. Use DICOM Modality or SOPClassUID to find all derived objects regardless of collection type.

```python
# Find ALL segmentations and structure sets by DICOM Modality
# SEG = DICOM Segmentation, RTSTRUCT = Radiotherapy Structure Set
client.sql_query("""
    SELECT collection_id, Modality, COUNT(*) as series_count
    FROM index
    WHERE Modality IN ('SEG', 'RTSTRUCT')
    GROUP BY collection_id, Modality
    ORDER BY series_count DESC
""")

# Find segmentations for a specific collection (includes non-analysis-result items)
client.sql_query("""
    SELECT SeriesInstanceUID, SeriesDescription, analysis_result_id
    FROM index
    WHERE collection_id = 'tcga_luad' AND Modality = 'SEG'
""")

# List analysis result collections (curated derived datasets)
client.fetch_index("analysis_results_index")
client.sql_query("""
    SELECT analysis_result_id, analysis_result_title, collections, modalities
    FROM analysis_results_index
""")

# Find analysis results for a specific source collection
client.sql_query("""
    SELECT analysis_result_id, analysis_result_title
    FROM analysis_results_index
    WHERE Collections LIKE '%tcga_luad%'
""")

# Use seg_index for detailed DICOM Segmentation metadata
client.fetch_index("seg_index")

# Get segmentation statistics by algorithm
client.sql_query("""
    SELECT AlgorithmName, AlgorithmType, COUNT(*) as seg_count
    FROM seg_index
    WHERE AlgorithmName IS NOT NULL
    GROUP BY AlgorithmName, AlgorithmType
    ORDER BY seg_count DESC
    LIMIT 10
""")

# Find segmentations for specific source images (e.g., chest CT)
client.sql_query("""
    SELECT
        s.SeriesInstanceUID as seg_series,
        s.AlgorithmName,
        s.total_segments,
        s.segmented_SeriesInstanceUID as source_series
    FROM seg_index s
    JOIN index src ON s.segmented_SeriesInstanceUID = src.SeriesInstanceUID
    WHERE src.Modality = 'CT' AND src.BodyPartExamined = 'CHEST'
    LIMIT 10
""")

# Find TotalSegmentator results with source image context
client.sql_query("""
    SELECT
        seg_info.collection_id,
        COUNT(DISTINCT s.SeriesInstanceUID) as seg_count,
        SUM(s.total_segments) as total_segments
    FROM seg_index s
    JOIN index seg_info ON s.SeriesInstanceUID = seg_info.SeriesInstanceUID
    WHERE s.AlgorithmName LIKE '%TotalSegmentator%'
    GROUP BY seg_info.collection_id
    ORDER BY seg_count DESC
""")

# Use ann_index and ann_group_index for Microscopy Bulk Simple Annotations
# ann_group_index has AnnotationGroupLabel, GraphicType, NumberOfAnnotations, AlgorithmName
client.fetch_index("ann_index")
client.fetch_index("ann_group_index")
client.sql_query("""
    SELECT g.AnnotationGroupLabel, g.GraphicType, g.NumberOfAnnotations, i.collection_id
    FROM ann_group_index g
    JOIN ann_index a ON g.SeriesInstanceUID = a.SeriesInstanceUID
    JOIN index i ON a.SeriesInstanceUID = i.SeriesInstanceUID
    WHERE g.AlgorithmName

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

