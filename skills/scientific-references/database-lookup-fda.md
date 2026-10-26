---
id: sciref-database-lookup-fda
name: "Scientific Ref: OpenFDA API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): OpenFDA API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup fda"
  - "openfda api"
keywords:
  - "database"
  - "lookup"
  - "fda"
  - "specialized"
  - "scientific"
  - "reference"
  - "openfda"
---

# OpenFDA API

## Base URL
```
https://api.fda.gov
```

## Auth
Optional free API key (240 req/min with or without). Register at https://open.fda.gov/apis/authentication/
Pass as: `?api_key=YOUR_KEY`

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/drug/event.json` | Drug adverse events (FAERS) |
| `/drug/label.json` | Drug product labeling (SPL) |
| `/drug/ndc.json` | NDC directory |
| `/drug/drugsfda.json` | Drugs@FDA (approvals) |
| `/drug/enforcement.json` | Drug recalls |
| `/device/event.json` | Device adverse events |
| `/device/510k.json` | 510(k) clearances |
| `/food/event.json` | Food adverse events |
| `/food/enforcement.json` | Food enforcement |

## Query Parameters

- `search` — query using OpenFDA syntax
- `count` — count unique values for a field
- `limit` — results per request (max 1000)
- `skip` — pagination offset (max 25000)

### Search Syntax
- Field search: `field:"value"`
- AND: `field1:value1+AND+field2:value2`
- OR: `field1:value1+OR+field2:value2`
- Date range: `field:[20230101+TO+20231231]`
- Wildcards: `field:aspir*`
- OpenFDA harmonized fields use `openfda.` prefix

## Example Calls

```
# Adverse events for aspirin
/drug/event.json?search=patient.drug.openfda.brand_name:"aspirin"&limit=5

# Top adverse reactions for a drug
/drug/event.json?search=patient.drug.openfda.generic_name:"metformin"&count=patient.reaction.reactionmeddrapt.exact

# Drug labels by generic name
/drug/label.json?search=openfda.generic_name:"ibuprofen"&limit=3

# Drug recalls in date range
/drug/enforcement.json?search=report_date:[20230101+TO+20231231]&limit=10

# Serious adverse events only
/drug/event.json?search=patient.drug.openfda.brand_name:"warfarin"+AND+serious:1&limit=10
```

## Rate Limits
| Tier | Requests/min | Requests/day |
|------|-------------|-------------|
| No API key | 240 | 1,000 |
| With API key (free) | 240 | 120,000 |

FAERS reports are not incidence estimates or proof that a drug caused an event. Preserve report versions and avoid double-counting follow-ups. OpenFDA harmonization is incomplete; a missing harmonized name is not evidence of absence.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

