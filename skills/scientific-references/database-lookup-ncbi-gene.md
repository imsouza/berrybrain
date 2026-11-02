---
id: sciref-database-lookup-ncbi-gene
name: "Scientific Ref: NCBI Gene (E-utilities)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): NCBI Gene (E-utilities)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup ncbi gene"
  - "ncbi gene (e-utilities)"
keywords:
  - "database"
  - "lookup"
  - "ncbi"
  - "gene"
  - "specialized"
  - "scientific"
  - "reference"
---

# NCBI Gene (E-utilities)

## Base URL
```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
```

## Auth
API key optional but recommended. Without key: 3 req/sec. With key: 10 req/sec.
Free key from: https://www.ncbi.nlm.nih.gov/account/settings/
Pass as: `&api_key=YOUR_KEY`

## Key Endpoints

### eSearch — Search for gene IDs
```
GET /esearch.fcgi?db=gene&term={query}&retmode=json&retmax={n}
```

Parameters:
- `db=gene` (required)
- `term` — search query (e.g. `BRCA1[gene]+AND+human[orgn]`)
- `retmode=json`
- `retmax` — max results (default 20)
- `retstart` — pagination offset

Example:
```
/esearch.fcgi?db=gene&term=BRCA1[gene]+AND+human[orgn]&retmode=json&retmax=5
```

### eSummary — Get gene metadata
```
GET /esummary.fcgi?db=gene&id={gene_ids}&retmode=json
```

Key response fields: `name`, `description`, `chromosome`, `maplocation`, `otheraliases`, `nomenclaturesymbol`, `organism`

Example:
```
/esummary.fcgi?db=gene&id=672&retmode=json
```

### eFetch — Full gene records (XML/text only, no JSON)
```
GET /efetch.fcgi?db=gene&id={gene_ids}&rettype=gene_table&retmode=text
```

### eLink — Cross-database links (gene to PubMed, OMIM, sequences)
```
GET /elink.fcgi?dbfrom=gene&db={target_db}&id={gene_id}&retmode=json
```

Target databases include `pubmed`, `omim`, `nuccore`, and `protein`; discover supported links with EInfo. BioSystems is retired; use current KEGG/Reactome resources for pathways.

Example — gene to PubMed:
```
/elink.fcgi?dbfrom=gene&db=pubmed&id=672&retmode=json
```

## Rate Limits
- Without API key: 3 requests/second
- With API key: 10 requests/second
- For bulk: use `usehistory=y` with eSearch, then retrieve via `query_key` and `WebEnv`

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

