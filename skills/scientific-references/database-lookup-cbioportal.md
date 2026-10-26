---
id: sciref-database-lookup-cbioportal
name: "Scientific Ref: cBioPortal API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): cBioPortal API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup cbioportal"
  - "cbioportal api"
keywords:
  - "database"
  - "lookup"
  - "cbioportal"
  - "specialized"
  - "scientific"
  - "reference"
---

# cBioPortal API

## Base URL
```
https://www.cbioportal.org/api
```

## Auth
No authentication for the public instance. Private/institutional instances (e.g. `genie.cbioportal.org`) require a data access token via `Authorization: Bearer <token>` header.

## Common Headers
```
Accept: application/json
Content-Type: application/json
```

## Common Query Parameters

Most list endpoints support these:

| Parameter | Type | Description | Default |
|---|---|---|---|
| `projection` | string | Detail level: `ID`, `SUMMARY`, `DETAILED`, `META` | `SUMMARY` |
| `pageNumber` | int | Zero-based page index | `0` |
| `pageSize` | int | Results per page; explicitly request a bounded size | Route-dependent, often `10000000` |
| `sortBy` | string | Property to sort by | varies |
| `direction` | string | `ASC` or `DESC` | `ASC` |

## Key Endpoints

### Studies

| Method | Endpoint | Description |
|---|---|---|
| GET | `/studies` | List all cancer studies |
| GET | `/studies/{studyId}` | Get a single study |
| POST | `/studies/fetch` | Fetch multiple studies by ID |

Example:
```
GET https://www.cbioportal.org/api/studies?projection=SUMMARY&pageSize=10
GET https://www.cbioportal.org/api/studies/brca_tcga
```

Response fields: `studyId`, `name`, `description`, `cancerTypeId`, `pmid`, `citation`, `allSampleCount`, `referenceGenome`, `publicStudy`, `importDate`

### Cancer Types

| Method | Endpoint | Description |
|---|---|---|
| GET | `/cancer-types` | List all cancer types |
| GET | `/cancer-types/{cancerTypeId}` | Get one cancer type |

Response fields: `cancerTypeId`, `name`, `shortName`, `dedicatedColor`, `parent`

### Genes

| Method | Endpoint | Description |
|---|---|---|
| GET | `/genes` | List all genes (paginated) |
| GET | `/genes/{geneId}` | Gene by Hugo symbol or Entrez ID |
| GET | `/genes/{geneId}/aliases` | Gene aliases |
| POST | `/genes/fetch` | Fetch multiple genes |

Example:
```
GET https://www.cbioportal.org/api/genes/TP53
```
Response: `{"entrezGeneId": 7157, "hugoGeneSymbol": "TP53", "type": "protein-coding"}`

### Molecular Profiles

| Method | Endpoint | Description |
|---|---|---|
| GET | `/molecular-profiles` | All profiles across all studies |
| GET | `/studies/{studyId}/molecular-profiles` | Profiles in a study |
| GET | `/molecular-profiles/{molecularProfileId}` | Single profile |

Profile types (`molecularAlterationType`): `MUTATION_EXTENDED`, `COPY_NUMBER_ALTERATION`, `MRNA_EXPRESSION`, `PROTEIN_LEVEL`, `METHYLATION`

Example:
```
GET https://www.cbioportal.org/api/studies/brca_tcga/molecular-profiles
```

### Mutations

| Method | Endpoint | Description |
|---|---|---|
| GET | `/molecular-profiles/{profileId}/mutations` | Mutations in a profile |
| POST | `/molecular-profiles/{profileId}/mutations/fetch` | Filtered mutation query |
| POST | `/mutations/fetch` | Multi-profile mutation fetch |

Parameters for GET:
| Parameter | Type | Description |
|---|---|---|
| `sampleListId` | string | Required: sample list to query (e.g. `brca_tcga_all`) |
| `entrezGeneId` | int | Required: filter by gene |
| `projection` | string | `SUMMARY`, `DETAILED`, `ID`, `META` |

Example — TP53 mutations in TCGA breast cancer:
```
GET https://www.cbioportal.org/api/molecular-profiles/brca_tcga_mutations/mutations?sampleListId=brca_tcga_all&entrezGeneId=7157&projection=DETAILED
```

POST body for `/molecular-profiles/{profileId}/mutations/fetch` (multi-gene, single profile; `/mutations/fetch` uses a different multi-study schema):
```json
{
  "sampleListId": "brca_tcga_all",
  "entrezGeneIds": [7157, 672]
}
```

Response fields: `entrezGeneId`, `sampleId`, `patientId`, `proteinChange`, `mutationType`, `mutationStatus`, `chr`, `startPosition`, `endPosition`, `referenceAllele`, `variantAllele`, `variantType`, `ncbiBuild`, `tumorAltCount`, `tumorRefCount`

### Copy Number Alterations

| Method | Endpoint | Description |
|---|---|---|
| GET | `/molecular-profiles/{profileId}/discrete-copy-number` | CNA data |
| POST | `/molecular-profiles/{profileId}/discrete-copy-number/fetch` | Filtered CNA query |

### Molecular Data (expression, methylation)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/molecular-profiles/{profileId}/molecular-data` | Expression/methylation data |
| POST | `/molecular-data/fetch` | Multi-profile molecular data fetch |

### Clinical Data

| Method | Endpoint | Description |
|---|---|---|
| GET | `/studies/{studyId}/clinical-data` | Clinical data for a study |
| POST | `/clinical-data/fetch` | Multi-study clinical data |
| GET | `/studies/{studyId}/clinical-attributes` | Available clinical attributes |

Parameters for GET:
| Parameter | Type | Description |
|---|---|---|
| `clinicalDataType` | string | `PATIENT` or `SAMPLE` |
| `attributeId` | string | e.g. `OS_STATUS`, `OS_MONTHS`, `CANCER_TYPE` |

Example:
```
GET https://www.cbioportal.org/api/studies/brca_tcga/clinical-data?clinicalDataType=PATIENT&attributeId=OS_STATUS&projection=SUMMARY
```

### Patients & Samples

| Method | Endpoint | Description |
|---|---|---|
| GET | `/studies/{studyId}/patients` | Patients in a study |
| GET | `/studies/{studyId}/samples` | Samples in a study |
| POST | `/patients/fetch` | Multi-study patient fetch |
| POST | `/samples/fetch` | Multi-study sample fetch |

### Sample Lists

| Method | Endpoint | Description |
|---|---|---|
| GET | `/studies/{studyId}/sample-lists` | Predefined sample groups |
| GET | `/sample-lists/{sampleListId}` | Single sample list |

### Gene Panels

| Method | Endpoint | Description |
|---|---|---|
| GET | `/gene-panels` | All gene panels |
| GET | `/gene-panels/{genePanelId}` | Panel details with gene list |
| POST | `/gene-panel-data/fetch` | Which panels cover which samples |

### API surface and versions

Use the public OpenAPI schema at `https://www.cbioportal.org/api/v3/api-docs/public` for the selected instance. The current public schema does not expose `/treatments/patient`, `/treatments/sample`, or a global `/discrete-copy-number/fetch`; do not infer these routes from internal UI requests or older installations.

### System

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Server health check |
| GET | `/info` | Portal version, DB schema version |

## Typical Workflow

1. **Find studies**: `GET /studies` — browse available cancer studies, get `studyId` values
2. **Get molecular profiles**: `GET /studies/{studyId}/molecular-profiles` — find profile IDs (e.g. `brca_tcga_mutations`, `brca_tcga_gistic`)
3. **Get sampl

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

