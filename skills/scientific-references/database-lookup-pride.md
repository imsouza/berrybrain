---
id: sciref-database-lookup-pride
name: "Scientific Ref: PRIDE Archive API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): PRIDE Archive API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup pride"
  - "pride archive api"
keywords:
  - "database"
  - "lookup"
  - "pride"
  - "specialized"
  - "scientific"
  - "reference"
---

# PRIDE Archive API

Public base: `https://www.ebi.ac.uk/pride/ws/archive/v3` (no key).
Use the current [OpenAPI schema](https://www.ebi.ac.uk/pride/ws/archive/v3/v3/api-docs).

| GET path | Purpose |
|---|---|
| `/projects?page=0&pageSize=5` | List projects |
| `/search/projects?keyword=alzheimer&page=0&pageSize=5` | Search projects |
| `/projects/PXD010000` | Retrieve project metadata |
| `/projects/PXD010000/files?page=0&pageSize=10` | List project files |
| `/projects/PXD010000/files/count` | File count |
| `/files/{fileAccession}` | File details |
| `/projects/count` | Project count |

`/projects` does not implement keyword search. Use `/search/projects`; its
`filter` syntax is `field==value`, with fields from the current search/facet
schema. Search supports `sortFields`, `sortDirection`, and `dateGap`.
Pagination uses zero-based `page` and `pageSize` (documented default 100).
List/search/file-list responses are JSON arrays, not a universal `results`
envelope. A single project is an object; inspect actual keys before parsing.

The Archive API does not expose the previously suggested `/spectra`,
`/peptideevidences`, or `/proteinevidences` routes. For identified molecules and
spectra, use the linked PRIDE analysis resources or download the project files.
Retain PXD accession, assay provenance, organism and submission/publication dates;
submitted data alone do not establish peptide/protein identification confidence.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

