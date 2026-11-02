---
id: sciref-imaging-data-commons-clinical-data-guide
name: "Scientific Ref: Clinical Data Guide for IDC"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (imaging-data-commons): Clinical Data Guide for IDC"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "imaging commons clinical guide"
  - "imaging commons clinico guide"
  - "clinical data guide for idc"
keywords:
  - "imaging"
  - "commons"
  - "clinical"
  - "guide"
  - "clinico"
  - "specialized"
  - "scientific"
  - "reference"
---

# Clinical Data Guide for IDC

**Tested with:** idc-index 0.12.5 (IDC data version v24)

Clinical data (demographics, diagnoses, therapies, lab tests, staging) accompanies many IDC imaging collections. This guide covers how to discover, access, and integrate clinical data with imaging data using `idc-index`.

## When to Use This Guide

Use this guide when you need to:
- Find what clinical metadata is available for a collection
- Filter patients by clinical criteria (e.g., cancer stage, treatment history)
- Join clinical attributes with imaging data for cohort selection
- Understand and decode coded values in clinical tables

For basic clinical data access, see the "Clinical Data Access" section in the main SKILL.md. This guide provides detailed workflows and advanced patterns.

## Prerequisites

Needs `idc-index` installed — run `python scripts/check_version.py`, which reports the installed
version and prints the install command for the interpreter you are running.

No BigQuery credentials are required. `fetch_index("clinical_index")` downloads the
dictionary and the release-specific clinical Parquet tables from public storage; network
access is needed on first fetch.

## Understanding Clinical Data in IDC

### What is Clinical Data?

Clinical data refers to non-imaging information that accompanies medical images:
- Patient demographics (age, sex, race)
- Clinical history (diagnoses, surgeries, therapies)
- Lab tests and pathology results
- Cancer staging (clinical and pathological)
- Treatment outcomes

### Data Organization

Clinical data in IDC comes from collection-specific spreadsheets provided by data submitters. IDC parses these into queryable tables accessible via `idc-index`.

**Important characteristics:**
- Clinical data is **not harmonized** across collections (terms and formats vary)
- Not all collections have clinical data (check availability first)
- All data is **anonymized** - `dicom_patient_id` links to imaging

### The clinical_index Table

The `clinical_index` serves as a dictionary/catalog of all available clinical data:

| Column | Purpose | Use For |
|--------|---------|---------|
| `collection_id` | Collection identifier | Filtering by collection |
| `table_name` | Full BigQuery table reference | BigQuery queries (if needed) |
| `short_table_name` | Short name | `get_clinical_table()` method |
| `column` | Column name in table | Selecting data columns |
| `column_label` | Human-readable description | Searching for concepts |
| `values` | Observed attribute values for the column | Interpreting coded values |

### The `values` Column

The `values` column contains an array of observed attribute values for the column defined in the `column` field. Each entry has:
- **option_code**: The actual value observed in that column
- **option_description**: Human-readable description of that value (from data dictionary if available, otherwise `None`)

For ACRIN collections, value descriptions come from provided data dictionaries. For other collections, they are derived from inspection of the actual data values.

**Note:** For columns with >20 unique values, the `values` array is left empty (`[]`) for simplicity.

## Core Workflow

### Step 1: Fetch Clinical Index

```python
from idc_index import IDCClient

client = IDCClient()
client.fetch_index('clinical_index')

# View available columns
print(client.clinical_index.columns.tolist())
```

### Step 2: Discover Available Clinical Data

```python
# List all collections with clinical data
collections_with_clinical = client.clinical_index["collection_id"].unique().tolist()
print(f"{len(collections_with_clinical)} collections have clinical data")

# Find clinical attributes for a specific collection
nlst_columns = client.clinical_index[client.clinical_index['collection_id']=='nlst']
nlst_columns[['short_table_name', 'column', 'column_label', 'values']]
```

### Step 3: Search for Specific Attributes

```python
# Search by keyword in column_label (case-insensitive)
stage_attrs = client.clinical_index[
    client.clinical_index["column_label"].str.contains("[Ss]tage", na=False)
]
stage_attrs[["collection_id", "short_table_name", "column", "column_label"]]
```

### Step 4: Load Clinical Table

```python
# Load table using short_table_name
nlst_canc_df = client.get_clinical_table("nlst_canc")

# Examine structure
print(f"Rows: {len(nlst_canc_df)}, Columns: {len(nlst_canc_df.columns)}")
nlst_canc_df.head()
```

### Step 5: Map Coded Values to Descriptions

Many clinical attributes use coded values. The `values` column in `clinical_index` contains an array of observed values with their descriptions (when available).

```python
# Get the clinical_index rows for NLST
nlst_clinical_columns = client.clinical_index[client.clinical_index['collection_id']=='nlst']

# Get observed values for a specific column
# Filter to the row for 'clinical_stag' and extract the values array
clinical_stag_values = nlst_clinical_columns[
    nlst_clinical_columns['column']=='clinical_stag'
]['values'].values[0]

# View the observed values and their descriptions
print(clinical_stag_values)
# Output: array([{'option_code': '.M', 'option_description': 'Missing'},
#                {'option_code': '110', 'option_description': 'Stage IA'},
#                {'option_code': '120', 'option_description': 'Stage IB'}, ...])

# Create mapping dictionary from codes to descriptions
mapping_dict = {item['option_code']: item['option_description'] for item in clinical_stag_values}

# Apply to DataFrame - convert column to string first for consistent matching
nlst_canc_df['clinical_stag_meaning'] = nlst_canc_df['clinical_stag'].astype(str).map(mapping_dict)
```

### Step 6: Join with Imaging Data

The `dicom_patient_id` column links clinical data to imaging. It matches the `PatientID` column in the imaging index.

```python
# Pandas merge approach
import pandas as pd

# Get NLST CT imaging data
nlst_imaging = client.index[(client.index['collection_id']=='nlst') & (client.index['Modality']=='CT')]

# Join with clinical data
merged = pd.merge(
    nlst_imaging[['PatientID', 'StudyInstanceUID']].drop_duplicates(),
    nlst_canc_df[['dicom_patient_id', 'clinical_stag', 'clinical_stag_meaning']],
    left_on='PatientID',
    right_on='dicom_patient_id',
    how='inner'
)
```

```python
# SQL join approach
# Clinical tables loaded via get_clinical_table() are not automatically
# registered in DuckDB. Register the DataFrame manually before joining.
nlst_canc_df = client.get_cli

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

