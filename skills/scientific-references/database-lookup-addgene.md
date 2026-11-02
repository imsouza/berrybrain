---
id: sciref-database-lookup-addgene
name: "Scientific Ref: Addgene Catalog API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): Addgene Catalog API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup addgene"
  - "addgene catalog api"
keywords:
  - "database"
  - "lookup"
  - "addgene"
  - "specialized"
  - "scientific"
  - "reference"
---

# Addgene Catalog API

## Access and authentication

Base: `https://api.developers.addgene.org`. Access requires approval and a license
for each requested scope; a normal Addgene account does not grant API access.
Use `Authorization: Token <ADDGENE_API_KEY>`.

## Read endpoints

| GET path | Purpose |
|---|---|
| `/catalog/plasmid/` | Search/list plasmids |
| `/catalog/plasmid/{id}/` | One plasmid |
| `/catalog/plasmid-with-sequences/{id}/` | One plasmid with sequences; requires `catalog:retrieve-with-sequences` |
| `/catalog/viral-prep/` | List viral preparations |
| `/catalog/viral-prep/{id}/` | One viral preparation |

Ordinary catalog reads require `catalog:retrieve` or the sequence-enabled scope.
Use `q` for free text; documented field filters include `name`, `backbone`,
`genes`, `article_pmid`, and `species`. List responses contain `count`, `next`,
`previous`, and `results`. Follow `next`; `page` and `page_size` control pagination.
Use `sort_by=id` for stable pagination; relevance sorting requires `q`.

Illustrative authenticated request (not executed):

```bash
curl --fail-with-body --get 'https://api.developers.addgene.org/catalog/plasmid/' \
  -H "Authorization: Token ${ADDGENE_API_KEY}" \
  --data-urlencode 'q=GFP' --data-urlencode 'sort_by=id' \
  --data-urlencode 'page_size=5'
```

Plasmid records include cloning, insert, sequence, and article data according to
scope; nullable fields and empty arrays are legitimate. Use licensed daily JSON
bulk downloads for large retrievals. The old `/api/plasmids`, `/depositors`, and
`/articles` routes are not the documented developer API.

Reviewed 2026-09-30: [OpenAPI schema](https://docs.developers.addgene.org/docs/schema/)
and [access requirements](https://developers.addgene.org/access-options/).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

