---
id: sciref-database-lookup-tcga-gdc
name: "Scientific Ref: TCGA / GDC Data Portal API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): TCGA / GDC Data Portal API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup tcga gdc"
  - "tcga / gdc data portal api"
keywords:
  - "database"
  - "lookup"
  - "tcga"
  - "gdc"
  - "specialized"
  - "scientific"
  - "reference"
---

# TCGA / GDC Data Portal API

## Base URL
```
https://api.gdc.cancer.gov
```

## Auth
No auth for public data. Token needed only for controlled-access downloads.

## Key Endpoints

All search endpoints accept GET or POST (POST preferred for complex filters).

| Endpoint | Description |
|----------|-------------|
| `/projects` | List/filter cancer projects (e.g. TCGA-BRCA) |
| `/cases` | Search cases (patients/samples) |
| `/files` | Search/filter files (BAM, VCF, expression) |
| `/genes` | Search gene-level data |
| `/ssms` | Search simple somatic mutations |
| `/ssm_occurrences` | Mutation occurrences across cases |
| `/files/{uuid}` | File metadata by UUID |
| `/data/{uuid}` | Download file by UUID |

## Filter Syntax (POST body)
```json
{
  "filters": {
    "op": "in",
    "content": {"field": "cases.project.project_id", "value": ["TCGA-BRCA"]}
  },
  "fields": "file_id,file_name,data_type",
  "format": "JSON",
  "size": 10
}
```
Operators: `in`, `=`, `!=`, `>`, `<`, `>=`, `<=`, `is`, `not`, `and`, `or`

## Example Calls
```
# List projects
https://api.gdc.cancer.gov/projects?size=5&fields=project_id,name,primary_site

# BRCA1 mutations (POST)
curl -X POST https://api.gdc.cancer.gov/ssms \
  -H "Content-Type: application/json" \
  -d '{"filters":{"op":"in","content":{"field":"consequence.transcript.gene.symbol","value":["BRCA1"]}},"fields":"ssm_id,genomic_dna_change","size":5}'

# Cases in TCGA-LUAD
https://api.gdc.cancer.gov/cases?filters=%7B%22op%22%3A%22in%22%2C%22content%22%3A%7B%22field%22%3A%22project.project_id%22%2C%22value%22%3A%5B%22TCGA-LUAD%22%5D%7D%7D&size=3&fields=submitter_id,disease_type
```

## Pagination
`from` (offset) and `size` (limit, max 10000). Default size is 10.

## Rate Limits
No fixed metadata rate guarantee is assumed. Honor throttling, inspect `data.pagination`, and use the GDC Data Transfer Tool for large downloads. Controlled-access authorization is file-specific; a successful public metadata search does not authorize its files.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

