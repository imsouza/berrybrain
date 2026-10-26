---
id: sciref-database-lookup-dailymed
name: "Scientific Ref: DailyMed (NIH/NLM Drug Labels)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): DailyMed (NIH/NLM Drug Labels)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup dailymed"
  - "dailymed (nih/nlm drug labels)"
keywords:
  - "database"
  - "lookup"
  - "dailymed"
  - "specialized"
  - "scientific"
  - "reference"
---

# DailyMed (NIH/NLM Drug Labels)

## Base URL
```
https://dailymed.nlm.nih.gov/dailymed/services/
```

## Auth
No API key required.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `v2/spls.json?drug_name={name}` | Search drug labels by name |
| `v2/spls/{setid}.json` | Get label metadata by SetID |
| `v2/spls/{setid}/ndcs.json` | NDC codes for a label |
| `v2/spls/{setid}/media.json` | Images/media for a label |
| `v2/drugnames.json?drug_name={prefix}` | Drug name autocomplete |
| `v2/drugclasses.json?drug_class_name={name}` | Search by pharmacologic class |
| `v2/rxcuis.json?rxcui={rxcui}` | Query RxNorm CUIs |
| `v2/spls.json?ndc={ndc_code}` | Find labels by NDC code |

## Additional filters for `/v2/spls.json`
- `drug_class_code` and `drug_class_coding_system` — pharmacologic class code and terminology; discover codes via `/drugclasses.json`
- `labeler` — manufacturer name
- `page` / `pagesize` — pagination (max 100)

## Example Calls

```
# Search metformin labels
https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?drug_name=metformin

# Drug name autocomplete
https://dailymed.nlm.nih.gov/dailymed/services/v2/drugnames.json?drug_name=ator

# Search by pharmacologic class
https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?drug_class_code={code_from_drugclasses}

# Full label XML (SPL content with sections)
https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/{setid}.xml
```

## Response Format
```json
{
  "metadata": {
    "total_elements": 12,
    "elements_per_page": 10,
    "current_page": 1,
    "total_pages": 2
  },
  "data": [
    {
      "published_date": "2024-01-15",
      "title": "METFORMIN HYDROCHLORIDE tablet",
      "setid": "b03f295f-..."
    }
  ]
}
```

## Rate Limits
No published limits. Be reasonable.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

