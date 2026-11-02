---
id: sciref-imaging-data-commons-dicomweb-guide
name: "Scientific Ref: DICOMweb Guide for IDC"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (imaging-data-commons): DICOMweb Guide for IDC"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "imaging commons dicomweb guide"
  - "dicomweb guide for idc"
keywords:
  - "imaging"
  - "commons"
  - "dicomweb"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
---

# DICOMweb Guide for IDC

Reviewed 2026-09-30 against IDC endpoint/policy documentation and Google Healthcare
conformance. Public QIDO and metadata reads were probed; authenticated Google-store
access and pixel/frame retrieval were not executed.

## When to Use DICOMweb

Use DICOMweb when you need:
- Integration with PACS systems or DICOMweb-compatible tools
- Streaming metadata without downloading full files
- Building custom viewers or web applications
- Using existing DICOMweb client libraries (OHIF, dicomweb-client, etc.)

For most use cases, `idc-index` is simpler and recommended. Use DICOMweb when you specifically need the DICOMweb protocol.

## Endpoints

### Public Proxy (No Authentication)

```
https://proxy.imaging.datacommons.cancer.gov/current/viewer-only-no-downloads-see-tinyurl-dot-com-slash-3j3d9jyp/dicomWeb
```

- **100% data coverage** - Contains all IDC data from all storage buckets
- Points to the latest IDC version automatically
- **Updates immediately** on new IDC releases
- Per-IP and global daily egress quotas; use when bucket downloads cannot meet the task
- No authentication required
- Read-only access
- Note: "viewer-only-no-downloads" in URL is legacy naming with no functional meaning

### Google Healthcare API (Requires Authentication)

```
https://healthcare.googleapis.com/v1/projects/nci-idc-data/locations/us-central1/datasets/idc/dicomStores/idc-store-v{VERSION}/dicomWeb
```

The pattern is historical, not proof that a store exists for the latest IDC release.
IDC currently documents `idc-store-v23`, while Google
[documents `idc-store` and an access-request form](https://docs.cloud.google.com/healthcare-api/docs/resources/public-datasets/idc).
Confirm the provisioned store URL and access with those pages/the IDC health monitor; do
not synthesize `idc-store-v24` solely from this client output:

```python
from idc_index import IDCClient
client = IDCClient()
print(client.get_idc_version())  # e.g., "v24" for current version
```

- Replicates `idc-open-data`; excludes the other two buckets, so check your selected series
- IDC targets synchronization within 1-2 weeks of a release; this is not guaranteed
- Requires authentication and provides higher quotas
- Better performance (no proxy routing)
- Each release gets a new versioned store

See [Content Coverage Differences](#content-coverage-differences) and [Authentication](#authentication-for-google-healthcare-api) sections below.

## Content Coverage Differences

**Important:** The two DICOMweb endpoints have different data coverage. The IDC public proxy contains MORE data than the authenticated Google Healthcare endpoint.

### Coverage Summary

| Endpoint | Coverage | Missing Data |
|----------|----------|--------------|
| **IDC Public Proxy** | 100% | None |
| **Google Healthcare API** | Only `idc-open-data` | Two other buckets; possibly newer releases |

### What's Missing from Google Healthcare?

The Google Healthcare DICOM store **only replicates data from the `idc-open-data` S3 bucket**. It does not include data from two additional buckets:

- `idc-open-data-cr`
- `idc-open-data-two`

The often-quoted 95.89% coverage is an IDC v21 series-count snapshot. Recalculate the
share for the selected release; it is not a current guarantee or a fraction by file size.

See `cloud_storage_guide.md` for details on bucket organization, file structure, and direct access methods.

### Update Timing

- **IDC Public Proxy**: Updates immediately when new IDC versions are released
- **Google Healthcare**: Independently maintained; synchronization within 1-2 weeks is a goal.

Verify the actual store release and query representative selected UIDs before a large job.

**Warning from IDC documentation:** *"Google-hosted DICOM store may not contain the latest version of IDC data!"* - Check during the weeks following a new release.

### Choosing the Right Endpoint

**Use IDC Public Proxy when:**
- You need complete data coverage (100%)
- You need the absolute latest data immediately after a new version release
- You don't want to set up GCP authentication
- Your usage fits within per-IP quotas (can request increases via support@canceridc.dev)
- You're accessing slide microscopy images frame-by-frame

**Use Google Healthcare API when:**
- Your selected series exist in the particular Google store
- You need higher quotas for heavy usage
- You want better performance (direct access, no proxy routing)

### Checking Your Data Availability

Before choosing an endpoint, verify whether your data might be in the missing buckets:

```python
from idc_index import IDCClient

client = IDCClient()

# Check which buckets contain your collection's data
results = client.sql_query("""
    SELECT aws_bucket, COUNT(*) as series_count
    FROM index
    WHERE collection_id = 'your_collection_id'
    GROUP BY aws_bucket
""")

print(results)

# Look for bucket values 'idc-open-data-cr' or 'idc-open-data-two'
# If present, that data won't be available in Google Healthcare endpoint
```

## Implementation Details

IDC DICOMweb is provided through Google Cloud Healthcare API DICOM stores. The implementation follows DICOM PS3.18 Web Services with specific characteristics documented in the [Google Healthcare DICOM conformance statement](https://docs.cloud.google.com/healthcare-api/docs/dicom).

### Supported Operations

| Service | Description | Supported |
|---------|-------------|-----------|
| QIDO-RS | Search for DICOM objects | Yes |
| WADO-RS | Retrieve DICOM objects and metadata | Yes |
| STOW-RS | Store DICOM objects | No (IDC is read-only) |

**Not supported:** URI Service, Worklist Service, Non-Patient Instance Service, Capabilities Transactions

### Searchable DICOM Tags (QIDO-RS)

The implementation supports a limited set of searchable tags:

| Level | Searchable Tags |
|-------|-----------------|
| Study | StudyInstanceUID, PatientName, PatientID, AccessionNumber, ReferringPhysicianName, StudyDate |
| Series | All study tags + SeriesInstanceUID, Modality |
| Instance | All series tags + SOPInstanceUID |

**Important:** Only exact matching is supported, except for:
- StudyDate: supports range queries
- PatientName: supports fuzzy matching

### Query Limitations

- Maximum results: 5,000 for studies/series searches; 50,000 for instances
- Maximum offset: 1,000,000
- Sequence tags (VR SQ) larger than approximately 1 MiB are omitted without a BulkDataURI;
  other bulk data can have a BulkDataURI. Retrieve the full instance for omitted sequenc

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

