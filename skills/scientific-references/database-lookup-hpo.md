---
id: sciref-database-lookup-hpo
name: "Scientific Ref: Human Phenotype Ontology (HPO)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): Human Phenotype Ontology (HPO)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup hpo"
  - "human phenotype ontology (hpo)"
keywords:
  - "database"
  - "lookup"
  - "hpo"
  - "specialized"
  - "scientific"
  - "reference"
  - "human"
---

# Human Phenotype Ontology (HPO)

Public term API: `https://ontology.jax.org/api/hp` (no key).

| GET path | Use |
|---|---|
| `/search?q=seizure&page=0&limit=5` | Search terms; response `terms`, `totalCount` |
| `/terms/HP%3A0001250` | Term details |
| `/terms/HP%3A0001250/parents` | Direct parents |
| `/terms/HP%3A0001250/children` | Direct children |
| `/terms/HP%3A0001250/ancestors` | All ancestors |
| `/terms/HP%3A0001250/descendants` | All descendants |
| `/terms?filter=HP%3A0001250,HP%3A0001249` | Selected terms |

Search is zero-based and needs `q`, `page`, and `limit`; encode query values.
Term records include `id`, `name`, `definition`, `synonyms`, and `xrefs`.
Hierarchy endpoints return arrays. An absent term can return null.

Annotations use a separate service:
`GET https://ontology.jax.org/api/network/annotation/HP%3A0001250`.
Inspect its entity-specific response; there are no documented `/hpo/term/.../genes`
or `/hpo/gene/...` routes in the current term API. For bulk gene/disease analyses,
use the versioned HPO annotation downloads and preserve evidence and negation.

Official schemas: [terms](https://ontology.jax.org/api/hp/docs/),
[annotation network](https://ontology.jax.org/api/network/docs).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

