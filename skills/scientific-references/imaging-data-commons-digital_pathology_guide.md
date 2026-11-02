---
id: sciref-imaging-data-commons-digital-pathology-guide
name: "Scientific Ref: Digital Pathology Guide for IDC"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (imaging-data-commons): Digital Pathology Guide for IDC"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "imaging commons digital pathology guide"
  - "digital pathology guide for idc"
keywords:
  - "imaging"
  - "commons"
  - "digital"
  - "pathology"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
---

# Digital Pathology Guide for IDC

**Tested with:** idc-index 0.12.5 (IDC data version v24)

For general IDC queries and downloads, use `idc-index` (see main SKILL.md). This guide covers slide microscopy (SM) imaging, microscopy bulk simple annotations (ANN), and segmentations (SEG) in the context of digital pathology in IDC.

## Index Tables for Digital Pathology

Five specialized index tables provide curated metadata without needing BigQuery:

| Table | Row Granularity | Description |
|-------|-----------------|-------------|
| `sm_index` | 1 row = 1 SM series | Slide Microscopy series metadata: container/slide ID, tissue type, anatomic structure, diagnosis, lens power, pixel spacing, image dimensions |
| `sm_instance_index` | 1 row = 1 SM instance | Instance-level (SOPInstanceUID) metadata for individual slide images |
| `seg_index` | 1 row = 1 SEG series | DICOM Segmentation metadata: algorithm, segment count, reference to source series. Used for both radiology and pathology — filter by source Modality to find pathology-specific segmentations |
| `ann_index` | 1 row = 1 ANN series | Microscopy Bulk Simple Annotations series metadata; includes `referenced_SeriesInstanceUID` linking to the annotated slide |
| `ann_group_index` | 1 row = 1 annotation group | Annotation group details: `AnnotationGroupLabel`, `GraphicType`, `NumberOfAnnotations`, `AlgorithmName`, property codes |

All require `client.fetch_index("table_name")` before querying. Use `client.indices_overview` to inspect column schemas programmatically.

## Slide Microscopy Queries

### Basic SM metadata

```python
from idc_index import IDCClient
client = IDCClient()

# sm_index has detailed metadata; join with index for collection_id
client.fetch_index("sm_index")
client.sql_query("""
    SELECT i.collection_id, COUNT(*) as slides,
           MIN(s.min_PixelSpacing_2sf) as min_resolution
    FROM sm_index s
    JOIN index i ON s.SeriesInstanceUID = i.SeriesInstanceUID
    GROUP BY i.collection_id
    ORDER BY slides DESC
""")
```

### Find SM series with specific properties

```python
# Find high-resolution slides with specific objective lens power
client.fetch_index("sm_index")
client.sql_query("""
    SELECT
        i.collection_id,
        i.PatientID,
        s.ObjectiveLensPower,
        s.min_PixelSpacing_2sf
    FROM sm_index s
    JOIN index i ON s.SeriesInstanceUID = i.SeriesInstanceUID
    WHERE s.ObjectiveLensPower >= 40
    ORDER BY s.min_PixelSpacing_2sf
    LIMIT 20
""")
```

### Filter by specimen preparation

The `sm_index` includes staining, embedding, and fixative metadata. These columns are **arrays** (e.g., `[hematoxylin stain, water soluble eosin stain]` for H&E) — use `array_to_string()` with `LIKE` or `list_contains()` to filter.

```python
# Find H&E-stained slides in a collection
client.fetch_index("sm_index")
client.sql_query("""
    SELECT
        i.PatientID,
        s.staining_usingSubstance_CodeMeaning as staining,
        s.embeddingMedium_CodeMeaning as embedding,
        s.tissueFixative_CodeMeaning as fixative
    FROM sm_index s
    JOIN index i ON s.SeriesInstanceUID = i.SeriesInstanceUID
    WHERE i.collection_id = 'tcga_brca'
      AND array_to_string(s.staining_usingSubstance_CodeMeaning, ', ') LIKE '%hematoxylin%'
    LIMIT 10
""")
```

```python
# Compare FFPE vs frozen slides across collections
client.sql_query("""
    SELECT
        i.collection_id,
        s.embeddingMedium_CodeMeaning as embedding,
        COUNT(*) as slide_count
    FROM sm_index s
    JOIN index i ON s.SeriesInstanceUID = i.SeriesInstanceUID
    GROUP BY i.collection_id, embedding
    ORDER BY i.collection_id, slide_count DESC
""")
```

## Identifying Tumor vs Normal Slides

The `sm_index` table provides two ways to identify tissue type:

| Column | Use Case |
|--------|----------|
| `primaryAnatomicStructureModifier_CodeMeaning` | Structured tissue type from DICOM specimen metadata (e.g., `Neoplasm, Primary`, `Normal`, `Tumor`, `Neoplasm, Metastatic`). Availability depends on the collection; missing values do not establish normal tissue. |
| `ContainerIdentifier` | Slide/container identifier. For TCGA collections, contains the [TCGA barcode](https://docs.gdc.cancer.gov/Encyclopedia/pages/TCGA_Barcode/) where the [sample type code](https://gdc.cancer.gov/resources-tcga-users/tcga-code-tables/sample-type-codes) (positions 14-15) encodes tissue origin: `01`-`09` = tumor, `10`-`19` = normal. |

### Using structured tissue type metadata

```python
from idc_index import IDCClient
client = IDCClient()
client.fetch_index("sm_index")

# Discover tissue type values across all SM data
client.sql_query("""
    SELECT
        s.primaryAnatomicStructureModifier_CodeMeaning as tissue_type,
        COUNT(*) as slide_count
    FROM sm_index s
    WHERE s.primaryAnatomicStructureModifier_CodeMeaning IS NOT NULL
    GROUP BY tissue_type
    ORDER BY slide_count DESC
""")
```

#### Example: Tumor vs normal slides in TCGA-BRCA

```python
# Tissue type breakdown for TCGA-BRCA
client.sql_query("""
    SELECT
        s.primaryAnatomicStructureModifier_CodeMeaning as tissue_type,
        COUNT(*) as slide_count,
        COUNT(DISTINCT i.PatientID) as patient_count
    FROM sm_index s
    JOIN index i ON s.SeriesInstanceUID = i.SeriesInstanceUID
    WHERE i.collection_id = 'tcga_brca'
    GROUP BY tissue_type
    ORDER BY slide_count DESC
""")
# Returns: Neoplasm, Primary (2704 slides), Normal (399 slides)
```

### Using TCGA barcode (TCGA collections only)

For TCGA collections, `ContainerIdentifier` contains the slide barcode (e.g., `TCGA-E9-A3X8-01A-03-TSC`). Extract the sample type code to classify tissue:

```python
# Parse sample type from TCGA barcode
client.sql_query("""
    SELECT
        SUBSTRING(SPLIT_PART(s.ContainerIdentifier, '-', 4), 1, 2) as sample_type_code,
        s.primaryAnatomicStructureModifier_CodeMeaning as tissue_type,
        COUNT(*) as slide_count
    FROM sm_index s
    JOIN index i ON s.SeriesInstanceUID = i.SeriesInstanceUID
    WHERE i.collection_id = 'tcga_brca'
    GROUP BY sample_type_code, tissue_type
    ORDER BY sample_type_code
""")
# Returns: 01 → Neoplasm, Primary (2704), 06 → None (8), 11 → Normal (399)
```

The barcode approach catches cases where structured metadata is NULL (e.g., `06` = Metastatic slides have `primaryAnatomicStructureModifier_CodeMeaning` = NULL in TCGA-BRCA).

## Annotation Queries (ANN)

DICOM Microscopy Bulk Simple Annotations (Modality = 'ANN') are annotations

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

