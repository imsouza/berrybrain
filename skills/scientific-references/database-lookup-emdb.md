---
id: sciref-database-lookup-emdb
name: "Scientific Ref: EMDB (Electron Microscopy Data Bank)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): EMDB (Electron Microscopy Data Bank)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup emdb"
  - "emdb (electron microscopy data bank)"
keywords:
  - "database"
  - "lookup"
  - "emdb"
  - "specialized"
  - "scientific"
  - "reference"
---

# EMDB (Electron Microscopy Data Bank)

## Base URL
```
https://www.ebi.ac.uk/emdb/api/
```

## Auth
No auth required.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/entry/{emdb_id}` | Full entry metadata (e.g. EMD-1234) |
| `/entry/map/{emdb_id}` | Map/volume metadata |
| `/entry/experiment/{emdb_id}` | Experimental details |
| `/entry/fitted/{emdb_id}` | Fitted PDB models |
| `/search/{query}?rows={n}` | Search entries by keyword |

## Example Calls
```
# Entry metadata
https://www.ebi.ac.uk/emdb/api/entry/EMD-1234

# Search for ribosome entries
https://www.ebi.ac.uk/emdb/api/search/ribosome?rows=5

# Experimental details
https://www.ebi.ac.uk/emdb/api/entry/experiment/EMD-1234
```

## Response Format
JSON. Search accepts `rows`, `page`, and `fl` (field selection); inspect its returned search envelope and pagination before iterating. Entry metadata is an object with `emdb_id`, `map`, and experimental/sample sections, not the map density file itself.

## Rate Limits
EBI fair-use policy. Map files (MRC/CCP4) available via FTP for bulk access.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

