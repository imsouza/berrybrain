---
id: sciref-database-lookup-mousemine
name: "Scientific Ref: MouseMine (Mouse Genome Informatics, InterMine-based)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): MouseMine (Mouse Genome Informatics, InterMine-based)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup mousemine"
  - "mousemine (mouse genome informatics, intermine-based)"
keywords:
  - "database"
  - "lookup"
  - "mousemine"
  - "specialized"
  - "scientific"
  - "reference"
---

# MouseMine (Mouse Genome Informatics, InterMine-based)

## Base URL
```
https://www.mousemine.org/mousemine/service
```

## Auth
No auth for most queries. Free account token needed for saved lists.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/search?q={query}&format=json` | Keyword search across all objects |
| `/template/results?name={template}&op1=LOOKUP&value1={value}&format=json` | Run pre-built template query |
| `/query/results` (POST) | Run custom PathQuery (XML) |
| `/model` | Retrieve data model |
| `/templates?format=json` | Discover currently available templates and editable constraints |

## Example Calls
```
# Keyword search for Brca1
https://www.mousemine.org/mousemine/service/search?q=Brca1&format=json

# Discover templates before constructing template/results parameters
https://www.mousemine.org/mousemine/service/templates?format=json
```

## Custom Query (POST)
```
POST /query/results
Content-Type: application/x-www-form-urlencoded
query=<query model="genomic" view="Gene.symbol Gene.name" sortOrder="Gene.symbol asc"><constraint path="Gene.organism.name" op="=" value="Mus musculus"/></query>&format=json
```

## Response Format
JSON: `{"results": [...], "statusCode": 200}`. Also supports XML, TSV, CSV via `format` param.

## Rate Limits
No published limits. Be reasonable.

The live template catalogue includes `MFeature_GO` (editable `SequenceFeature` lookup); `Gene_GO` is not present. Supply the template's actual constraint paths/operators and preserve the fixed organism/data-source constraints.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

