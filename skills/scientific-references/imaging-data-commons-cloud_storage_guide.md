---
id: sciref-imaging-data-commons-cloud-storage-guide
name: "Scientific Ref: Cloud Storage Guide for IDC"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (imaging-data-commons): Cloud Storage Guide for IDC"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "imaging commons cloud storage guide"
  - "cloud storage guide for idc"
keywords:
  - "imaging"
  - "commons"
  - "cloud"
  - "storage"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
---

# Cloud Storage Guide for IDC

IDC maintains all DICOM files in public cloud storage buckets mirrored between Google Cloud Storage (GCS) and AWS S3. This guide covers bucket organization, file structure, access methods, and versioning.

## When to Use Direct Cloud Storage Access

Use direct bucket access when you need:
- Maximum download performance with parallel transfers
- Integration with cloud-native workflows (e.g., running analysis on cloud VMs)
- Programmatic access from tools like s5cmd or gsutil
- Access to specific file versions for reproducibility

For most use cases, `idc-index` is simpler and recommended -— it uses s5cmd internally to download from these same S3 buckets, handling the UUID lookups automatically. Use direct cloud storage when you need raw file access, custom parallelization, or are building cloud-native pipelines.

## Storage Buckets

IDC organizes data across multiple buckets based on licensing and content type. All buckets are mirrored between AWS and GCS with identical content and file paths.

### Bucket Summary

| Purpose | AWS S3 Bucket | GCS Bucket | License | Content |
|---------|---------------|------------|---------|---------|
| Primary data | `idc-open-data` | `idc-open-data` | Mixed; query metadata | Most IDC series |
| Head scans | `idc-open-data-two` | `idc-open-idc1` | Query metadata | Collections potentially containing head imaging |
| Commercial-restricted | `idc-open-data-cr` | `idc-open-cr` | Query metadata | Some CC BY-NC data |

**Notes:**
- All AWS buckets are in AWS region `us-east-1`
- Prior to IDC v19, GCS used `public-datasets-idc` (now superseded by `idc-open-data`)
- The head scans bucket exists for potential future policy changes regarding facial imaging data
- **Important** Use `idc-index` to get license information - do not rely on bucket name! 

### Why Multiple Buckets?

1. **Licensing separation**: Some CC BY-NC data is separated into `idc-open-data-cr` / `idc-open-cr`, but restricted series also exist in `idc-open-data`; use metadata, not bucket names
2. **Head scan handling**: Collections labeled by TCIA as potentially containing head scans are in separate buckets (`idc-open-data-two` / `idc-open-idc1`) for potential future policy compliance
3. **Historical reasons**: The bucket structure evolved as IDC grew and partnered with different cloud programs

## File Organization Within Buckets

Files are organized by CRDC UUIDs, not DICOM UIDs. This enables versioning while maintaining consistent paths across cloud providers.

### Directory Structure

```
<bucket>/
└── <crdc_series_uuid>/
    ├── <crdc_instance_uuid_1>.dcm
    ├── <crdc_instance_uuid_2>.dcm
    └── ...
```

**Example path:**
```
s3://idc-open-data/7a6b2389-53c6-4c5b-b07f-6d1ed4a3eed9/0d73f84e-70ae-4eeb-96a0-1c613b5d9229.dcm
```

- `7a6b2389-53c6-4c5b-b07f-6d1ed4a3eed9` = series UUID (folder)
- `0d73f84e-70ae-4eeb-96a0-1c613b5d9229.dcm` = instance UUID (file)

### CRDC UUIDs vs DICOM UIDs

| Identifier Type | Format | Changes When | Use For |
|-----------------|--------|--------------|---------|
| DICOM UID (e.g., SeriesInstanceUID) | Numeric (e.g., `1.3.6.1.4...`) | Never (included in DICOM metadata) | Clinical identification, DICOMweb queries |
| CRDC UUID (e.g., crdc_series_uuid) | UUID (e.g., `e127d258-37c2-...`) | Content changes | File paths, versioning, reproducibility |

**Key insight:** A single DICOM SeriesInstanceUID may have multiple CRDC series UUIDs across IDC versions if the series content changed (instances added/removed, metadata corrected). The CRDC UUID uniquely identifies a specific version of the data.

### Mapping DICOM UIDs to File Paths

Use `idc-index` to get file URLs from DICOM identifiers:

```python
from idc_index import IDCClient

client = IDCClient()

# Get all file URLs for a series
series_uid = "1.3.6.1.4.1.14519.5.2.1.6450.9002.217441095430480124587725641302"
urls = client.get_series_file_URLs(seriesInstanceUID=series_uid)

for url in urls[:3]:
    print(url)
# Returns S3 URLs like: s3://idc-open-data/<crdc_series_uuid>/<crdc_instance_uuid>.dcm
```

Or query the index directly for URL columns:

```python
# Get series-level URL (points to folder)
result = client.sql_query("""
    SELECT SeriesInstanceUID, series_aws_url
    FROM index
    WHERE collection_id = 'rider_pilot' AND Modality = 'CT'
    LIMIT 3
""")

print(result[['SeriesInstanceUID', 'series_aws_url']])
```

**Available URL column in index:**
- `series_aws_url`: S3 URL to series folder (e.g., `s3://idc-open-data/uuid/*`)

GCS object keys are the same, but bucket names differ: map `idc-open-data-two` to
`idc-open-idc1` and `idc-open-data-cr` to `idc-open-cr`; `idc-open-data` stays unchanged.
Then use `gs://` for GCS tools. `idc-index` handles this mapping internally.

## Accessing Cloud Storage

All IDC buckets support free egress (no download fees) through partnerships with AWS Open Data and Google Public Data programs. No authentication required.

### AWS S3 Access

**Using AWS CLI (no account required):**
```bash
# List bucket contents
aws s3 ls --no-sign-request s3://idc-open-data/

# List files in a series folder
aws s3 ls --no-sign-request s3://idc-open-data/7a6b2389-53c6-4c5b-b07f-6d1ed4a3eed9/

# Download a single file
aws s3 cp --no-sign-request \
    s3://idc-open-data/7a6b2389-53c6-4c5b-b07f-6d1ed4a3eed9/0d73f84e-70ae-4eeb-96a0-1c613b5d9229.dcm \
    ./local_file.dcm

# Download entire series folder
aws s3 cp --no-sign-request --recursive \
    s3://idc-open-data/7a6b2389-53c6-4c5b-b07f-6d1ed4a3eed9/ \
    ./series_folder/
```

**Using s5cmd (faster for bulk downloads):**
```bash
# Install s5cmd
# macOS: brew install s5cmd
# Linux: download from https://github.com/peak/s5cmd/releases

# Download specific series
s5cmd --no-sign-request cp 's3://idc-open-data/7a6b2389-53c6-4c5b-b07f-6d1ed4a3eed9/*' ./local_folder/

# Download from manifest file
s5cmd --no-sign-request run manifest.txt
```

**s5cmd manifest format:** The `s5cmd run` command expects one s5cmd command per line, not just URLs:
```
cp s3://idc-open-data/uuid1/instance1.dcm ./local_folder/
cp s3://idc-open-data/uuid1/instance2.dcm ./local_folder/
cp s3://idc-open-data/uuid2/instance3.dcm ./local_folder/
```

IDC Portal exports manifests in this format. When creating manifests programmatically, use `idc-index` download methods (which handle this internally) rather than constructing manifests manually.

### GCS Access

**Using gsutil:**
```bash
# List bucket contents
gsutil ls gs://idc-open-data

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

