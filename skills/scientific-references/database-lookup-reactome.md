---
id: sciref-database-lookup-reactome
name: "Scientific Ref: Reactome Content Service REST API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): Reactome Content Service REST API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup reactome"
  - "reactome content service rest api"
keywords:
  - "database"
  - "lookup"
  - "reactome"
  - "specialized"
  - "scientific"
  - "reference"
---

# Reactome Content Service REST API

## Base URL

```
https://reactome.org/ContentService
```

No authentication required. JSON by default.

## Key Endpoints

### Search (full-text across pathways, reactions, proteins)

```
GET /search/query?query={term}
```

Parameters:
- `query` (required) — search term (e.g. "apoptosis", "TP53", "R-HSA-109581")
- `species` — filter by species (e.g. "Homo sapiens")
- `types` — filter by type: `Pathway`, `Reaction`, `Protein`, `Complex`, `SmallMolecule`
- `cluster` — boolean, cluster results (default true)
- `rows` — page size
- `Start row` — zero-based offset (URL-encode the space as `%20`)
- `Force filters=true` — keep requested filters even when no records match; the default can relax filters to obtain results. Encode this name as `Force%20filters`.

Example:
```
/search/query?query=apoptosis&species=Homo+sapiens&types=Pathway
```

Response:
```json
{
  "results": [
    {
      "typeName": "Pathway",
      "rows": [
        {
          "dbId": 109581,
          "stId": "R-HSA-109581",
          "name": "Apoptosis",
          "species": ["Homo sapiens"],
          "summation": ["..."]
        }
      ]
    }
  ],
  "found": 42
}
```

### Autocomplete
```
GET /search/suggest?query={partial_term}
```

### Top-level pathways for a species
```
GET /data/pathways/top/{species}
```
Example: `/data/pathways/top/Homo%20sapiens`

### Pathway details
```
GET /data/query/{id}
```
Where `{id}` is a stable ID like `R-HSA-109581` or a numeric dbId.

### Events contained in a pathway
```
GET /data/pathway/{id}/containedEvents
```

### Participants of a reaction
```
GET /data/participants/{id}
```

### Ancestors of an event
```
GET /data/event/{id}/ancestors
```

### Map external ID to pathways (e.g. UniProt to Reactome pathways)
```
GET /data/mapping/{resource}/{id}/pathways
```
Example — find pathways for TP53 (UniProt P04637):
```
/data/mapping/UniProt/P04637/pathways
```

### Map external ID to reactions
```
GET /data/mapping/{resource}/{id}/reactions
```

### Generic entity lookup
```
GET /data/query/{id}
```

### Reference entities for an event
```
GET /data/participants/{id}/referenceEntities
```

### All species
```
GET /data/species/all
```

### Event hierarchy for a species (large response)
```
GET /data/eventsHierarchy/{species}
```

## Stable ID Format

`R-{species_code}-{number}`

| Code | Species |
|---|---|
| HSA | Homo sapiens |
| MMU | Mus musculus |
| RNO | Rattus norvegicus |
| DME | Drosophila melanogaster |
| CEL | C. elegans |
| SCE | S. cerevisiae |

## External Resource Names for Mapping

`UniProt`, `ChEBI`, `ENSEMBL`, `miRBase`, `GeneCards`, `NCBI`

Multiple values for same parameter: repeat the parameter (e.g. `types=Pathway&types=Reaction`).

## Rate Limits

No API key required. No formal rate limit published, but be reasonable — avoid hundreds of concurrent requests. For bulk data, use Reactome's downloadable dumps (MySQL, Neo4j, BioPAX, SBML).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

