---
id: sciref-database-lookup-hca
name: "Scientific Ref: Human Cell Atlas (HCA)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): Human Cell Atlas (HCA)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup hca"
  - "human cell atlas (hca)"
keywords:
  - "database"
  - "lookup"
  - "hca"
  - "specialized"
  - "scientific"
  - "reference"
  - "human"
---

# Human Cell Atlas (HCA)

## Base URL
```
https://service.azul.data.humancellatlas.org/
```

## Auth
No auth required.

## Select the catalogue

GET `/index/catalogs` and choose `default_catalog` or an explicitly required
catalogue from `catalogs`. The live default on 2026-09-30 was `dcp60`; pin the
returned name for the entire retrieval. Do not hard-code the old `dcp2` catalogue.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/index/projects?size={n}&catalog={catalog}` | List/search projects |
| `/index/samples?size={n}&catalog={catalog}` | List/search samples |
| `/index/files?size={n}&catalog={catalog}` | List/search files |
| `/index/summary?catalog={catalog}` | Summary statistics |

## Example Calls
```
# List projects
https://service.azul.data.humancellatlas.org/index/projects?size=5&catalog={catalog}

# Summary stats
https://service.azul.data.humancellatlas.org/index/summary?catalog={catalog}
```

Encode `filters` as JSON, for example `{"organ":{"is":["lung"]}}`.
Follow `pagination.next` for continuation; the API uses search-after tokens,
not a general numeric offset. Query parameters and filter names are defined in
the [OpenAPI schema](https://service.azul.data.humancellatlas.org/openapi.json).

## Response Format
JSON. `hits` array with project/sample/file metadata + pagination.

## Rate Limits
No published limits. Be reasonable.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

