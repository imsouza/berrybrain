---
id: sciref-database-lookup-monarch
name: "Scientific Ref: Monarch Initiative API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): Monarch Initiative API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup monarch"
  - "monarch initiative api"
keywords:
  - "database"
  - "lookup"
  - "monarch"
  - "specialized"
  - "scientific"
  - "reference"
---

# Monarch Initiative API

## Base URL
```
https://api.monarchinitiative.org/v3/api
```

## Auth
No API key required.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/search?q={query}` | Text search across all entities |
| `/autocomplete?q={prefix}` | Autocomplete entity names |
| `/entity/{id}` | Entity details (gene, disease, phenotype) |
| `/association?entity={id}` | Associations for an entity |
| `/association?entity={id}&category={cat}` | Filtered associations |

## Entity ID Prefixes
- `MONDO:` — diseases (e.g. `MONDO:0007947`)
- `HP:` — phenotypes (e.g. `HP:0001250`)
- `HGNC:` — genes (e.g. `HGNC:3603`)
- `NCBIGene:` — genes (e.g. `NCBIGene:7157`)

## Association Categories
`biolink:GeneToPhenotypicFeatureAssociation`, `biolink:DiseaseToPhenotypicFeatureAssociation`, `biolink:GeneToDiseaseAssociation`

## Example Calls
```
# Search for Marfan syndrome
https://api.monarchinitiative.org/v3/api/search?q=Marfan+syndrome&limit=5

# Entity details for a disease
https://api.monarchinitiative.org/v3/api/entity/MONDO:0007947

# Gene-to-phenotype for FBN1
https://api.monarchinitiative.org/v3/api/association?entity=HGNC%3A3603&category=biolink:GeneToPhenotypicFeatureAssociation&limit=10
```

## Response Format
Paginate search/associations with `limit` and zero-based `offset`. JSON. Search: `items[]` with `id`, `name`, `category`. Associations: `items[]` with `subject`, `predicate`, `object`, `publications`.

## Rate Limits
No published limits. Be reasonable.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

