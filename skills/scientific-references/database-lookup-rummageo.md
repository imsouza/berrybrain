---
id: sciref-database-lookup-rummageo
name: "Scientific Ref: RummaGEO — GEO signature search and enrichment"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): RummaGEO — GEO signature search and enrichment"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup rummageo"
  - "rummageo — geo signature search and enrichment"
keywords:
  - "database"
  - "lookup"
  - "rummageo"
  - "specialized"
  - "scientific"
  - "reference"
---

# RummaGEO — GEO signature search and enrichment

Public GraphQL endpoint: `https://rummageo.com/graphql`.
The official [application queries](https://github.com/MaayanLab/rummageo/blob/rummageo/src/graphql/core.graphql)
and [server](https://github.com/MaayanLab/rummageo/blob/rummageo/src/lib/postgraphile.ts)
define its query surface. The formerly suggested `/api/enrich` and `/api/table`
REST recipes are not supported by that source.

A small read-only term search (live-tested):
```bash
curl --fail-with-body 'https://rummageo.com/graphql' \
  -H 'Content-Type: application/json' \
  --data '{"query":"{ geneSetTermSearch(terms:[\"neuron\"],first:1,offset:0){ totalCount nodes{term} } }"}'
```

Gene-set enrichment uses `background(id: $id) { enrich(genes: $genes, first: $n,
offset: $offset) { nodes { pvalue adjPvalue oddsRatio nOverlap } totalCount } }`.
Select the appropriate species/background UUID from the service's current
background catalogue before querying. Consult the source for supported filters;
the gene list alone is insufficient to specify the analysis.

Inspect GraphQL `errors` even with HTTP 200. Paginate with `first` and `offset`.
Preserve background, species, signature direction, sample-group contrast and GEO
accession. An enriched signature is an association with a study contrast, not
proof of a causal drug or disease mechanism.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

