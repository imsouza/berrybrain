---
id: sciref-database-lookup-quickgo
name: "Scientific Ref: QuickGO (EBI GO Annotation Browser)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): QuickGO (EBI GO Annotation Browser)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup quickgo"
  - "quickgo (ebi go annotation browser)"
keywords:
  - "database"
  - "lookup"
  - "quickgo"
  - "specialized"
  - "scientific"
  - "reference"
---

# QuickGO (EBI GO Annotation Browser)

## Base URL
```
https://www.ebi.ac.uk/QuickGO/services/
```

## Auth
No auth required.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ontology/go/terms/{goId}` | GO term details |
| `/ontology/go/terms/{goId}/children` | Child terms |
| `/ontology/go/terms/{goId}/ancestors` | Ancestor terms |
| `/ontology/go/search?query={term}` | Search GO terms by keyword |
| `/annotation/search` | Search annotations by gene/taxon/GO term |

## Annotation Search Parameters
- `goId` — GO term (e.g. GO:0003723)
- `taxonId` — NCBI taxonomy (e.g. 9606 for human)
- `geneProductId` — UniProt accession
- `evidenceCode` — ECO evidence code (e.g. ECO:0000269)
- `aspect` — biological_process, molecular_function, cellular_component
- `limit`, `page` — pagination; page is one-based, and annotation search limits each page to 200
- Include `Accept: application/json`; preserve evidence, qualifiers/negation and annotation provenance.

## Example Calls
```
# GO term details
https://www.ebi.ac.uk/QuickGO/services/ontology/go/terms/GO:0003723

# Human annotations for RNA binding
https://www.ebi.ac.uk/QuickGO/services/annotation/search?goId=GO:0003723&taxonId=9606&limit=10

# Search terms by keyword
https://www.ebi.ac.uk/QuickGO/services/ontology/go/search?query=apoptosis&limit=5
```

## Response Format
JSON. Annotations: paginated results with gene product, GO term, evidence, qualifier.

## Rate Limits
EBI fair-use policy. Use download endpoint for large result sets.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

