---
id: sciref-database-lookup-lincs-l1000
name: "Scientific Ref: LINCS L1000 (Clue.io) API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): LINCS L1000 (Clue.io) API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup lincs l1000"
  - "lincs l1000 (clue.io) api reference"
keywords:
  - "database"
  - "lookup"
  - "lincs"
  - "l1000"
  - "specialized"
  - "scientific"
  - "reference"
---

# LINCS L1000 (Clue.io) API Reference

## Overview
The LINCS L1000 dataset is accessible via the **Connectivity Map (CMap) API** at clue.io.

## Base URL
```
https://api.clue.io/api
```

## Authentication
- **API key required** (free registration at clue.io)
- Pass via header: `user_key: YOUR_API_KEY`

## Key Endpoints

| Endpoint | Description |
|---|---|
| `GET /perts` | Query perturbagens (compounds, gene knockdowns, overexpression) |
| `GET /genes` | Query genes (L1000 landmark + inferred) |
| `GET /cells` | Query cell lines used in L1000 |
| `GET /sigs` | Query connectivity signatures |
| `GET /profiles` | Profile metadata (not the full level 5 expression matrix) |
| `GET /pcls` | Perturbagen classes |

## Query Parameters
All endpoints support a `filter` parameter using Loopback-style JSON:
- `where` — filter conditions
- `fields` — select specific fields
- `limit` / `skip` — pagination

## Example Calls

```bash
# Illustrative authenticated queries; JSON is encoded as one query parameter.
curl --fail-with-body --get 'https://api.clue.io/api/perts' \
  -H "user_key: $CLUE_API_KEY" \
  --data-urlencode 'filter={"where":{"pert_iname":"vorinostat"},"limit":5}'
curl --fail-with-body --get 'https://api.clue.io/api/genes' \
  -H "user_key: $CLUE_API_KEY" \
  --data-urlencode 'filter={"where":{"l1000_type":"landmark"},"limit":10}'
curl --fail-with-body --get 'https://api.clue.io/api/sigs' \
  -H "user_key: $CLUE_API_KEY" \
  --data-urlencode 'filter={"where":{"pert_iname":"vorinostat"},"limit":5}'
```

## Response Format
JSON. Example (perturbagen):
```json
[
  {
    "pert_id": "BRD-K81418486",
    "pert_iname": "vorinostat",
    "pert_type": "trt_cp",
    "moa": ["HDAC inhibitor"],
    "target": ["HDAC1","HDAC2","HDAC3","HDAC6"]
  }
]
```

## Rate Limits
- Free tier: moderate rate limiting (exact numbers not publicly documented)
- Bulk data downloads available separately via clue.io data portal

For expression matrices, obtain the versioned data release and join on signature
and gene identifiers. Level 5 contains replicate-collapsed differential-expression
signatures; it is not raw abundance. Official contract: https://clue.io/developer-resources

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

