---
id: sciref-database-lookup-jaspar
name: "Scientific Ref: JASPAR (Transcription Factor Binding Profiles)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): JASPAR (Transcription Factor Binding Profiles)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup jaspar"
  - "jaspar (transcription factor binding profiles)"
keywords:
  - "database"
  - "lookup"
  - "jaspar"
  - "specialized"
  - "scientific"
  - "reference"
---

# JASPAR (Transcription Factor Binding Profiles)

## Base URL
```
https://jaspar.elixir.no/api/v1/
```

## Auth
No auth required.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/matrix/` | List all TF binding profiles |
| `/matrix/{matrix_id}/` | Specific profile (e.g. MA0139.1 for CTCF) |
| `/matrix/?tax_id={id}&collection=CORE` | Filter by species + collection |
| `/matrix/{id}/?format=jaspar` | Profile in JASPAR format |
| `/matrix/{id}/?format=meme` | Profile in MEME format |
| `/matrix/{id}/?format=transfac` | Profile in TRANSFAC format |
| `/taxon/` | List taxonomic groups |
| `/collections/` | List collections (CORE, CNE, etc.) |

## Filter Parameters
- `tax_id` — NCBI taxonomy ID (9606 for human)
- `collection` — CORE, CNE, PHYLOFACTS, etc.
- `tf_class` — TF structural class
- `name` — TF name search
- `page`, `page_size` — pagination

## Example Calls
```
# Get CTCF binding profile
https://jaspar.elixir.no/api/v1/matrix/MA0139.1/

# Human CORE TF profiles
https://jaspar.elixir.no/api/v1/matrix/?tax_id=9606&collection=CORE&page_size=10

# Get profile in MEME format
https://jaspar.elixir.no/api/v1/matrix/MA0139.1/?format=meme
```

## Response Format
JSON. Profiles include: `matrix_id`, `name`, `pfm` (position frequency matrix as A/C/G/T dict), `sequence_logo` URL, `species`, `class`, `family`.

## API Docs
Swagger at https://jaspar.elixir.no/api/v1/docs/

## Rate Limits
No published limits. Be reasonable.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

