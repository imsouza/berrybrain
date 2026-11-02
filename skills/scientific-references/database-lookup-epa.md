---
id: sciref-database-lookup-epa
name: "Scientific Ref: EPA Envirofacts Data Service"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): EPA Envirofacts Data Service"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup epa"
  - "epa envirofacts data service"
keywords:
  - "database"
  - "lookup"
  - "epa"
  - "specialized"
  - "scientific"
  - "reference"
  - "envirofacts"
---

# EPA Envirofacts Data Service

Current public base: `https://data.epa.gov/dmapservice`.
[Official query contract](https://www.epa.gov/enviro/web-services).
No key is required for this service; AQS below is separate.

Tables are qualified as `program.table`. Discover table/column names through the
EPA data model, rather than guessing names from a program abbreviation.

```text
GET https://data.epa.gov/dmapservice/tri.tri_facility/state_abbr/equals/VA/1:10/JSON
```

Filters use `/column/operator/value`; available operators include `equals`,
`notEquals`, `lessThan`, `greaterThan`, `beginsWith`, `contains`, `in`, and `notIn`.
Combine filters with `/and/` or `/or/`; encode values in path segments.
Rows are one-based and inclusive (`1:10`, then `11:20`). Sort with
`/sort/column:asc` or `:desc` for repeatable paging. JSON is the default;
CSV, XML and other formats are available.

The API supports server-side joins. For example, qualifying two tables and
joining on their documented common identifier avoids mismatching similarly named
facilities. Use explicit join keys when needed and verify row cardinality.

The older `/efservice/.../rows/0:9` grammar is not the current documented contract.
Keep program, reporting year, units and method with environmental observations;
facility records alone do not measure exposure or individual health risk.

## AQS Data API (Separate System)

For more granular air quality data, EPA also provides the AQS Data API at:
```
https://aqs.epa.gov/data/api
```

- **Requires:** Free account at https://aqs.epa.gov/data/api/signup?email=YOUR_EMAIL
- **Auth:** Pass `email` and `key` as query parameters.
- Key endpoints: `/dailyData/byState`, `/annualData/byState`, `/sampleData/bySite`, `/monitors/byState`.

**Example:**
```
https://aqs.epa.gov/data/api/dailyData/byState?email=YOUR_EMAIL&key=YOUR_KEY&param=44201&bdate=20240101&edate=20240131&state=06
```

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

