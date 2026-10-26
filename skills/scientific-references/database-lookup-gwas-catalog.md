---
id: sciref-database-lookup-gwas-catalog
name: "Scientific Ref: GWAS Catalog (EBI)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): GWAS Catalog (EBI)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup gwas catalog"
  - "gwas catalog (ebi)"
keywords:
  - "database"
  - "lookup"
  - "gwas"
  - "catalog"
  - "specialized"
  - "scientific"
  - "reference"
---

# GWAS Catalog (EBI)

## Base URL
```
https://www.ebi.ac.uk/gwas/rest/api
```

## Auth
No API key required.

## Note: Responses use HAL+JSON format with `_links` and `_embedded` keys.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/studies/{accession}` | Single study (e.g. GCST001633) |
| `/studies/search/findByPublicationIdPubmedId?pubmedId={id}` | Studies by PubMed ID |
| `/singleNucleotidePolymorphisms/{rsId}` | SNP details |
| `/singleNucleotidePolymorphisms/{rsId}/associations` | Associations for a SNP |
| `/singleNucleotidePolymorphisms/search/findByRsId?rsId={rsId}` | Search by rsID |
| `/associations` | List associations |
| `/associations/{id}` | Single association |
| `/efoTraits` | List EFO traits |
| `/efoTraits/search/findByEfoTrait?trait={name}` | Search traits |

## Pagination
`?page=0&size=20` (zero-indexed, max ~500)

## Example Calls
```
# Get a study
https://www.ebi.ac.uk/gwas/rest/api/studies/GCST001633

# Associations for a SNP
https://www.ebi.ac.uk/gwas/rest/api/singleNucleotidePolymorphisms/rs7329174/associations

# Search traits
https://www.ebi.ac.uk/gwas/rest/api/efoTraits/search/findByEfoTrait?trait=diabetes&page=0&size=5
```

## Response Format
HAL+JSON. Results in `_embedded.studies[]` or `_embedded.associations[]`. Key fields: `pvalue`, `riskFrequency`, `orPerCopyNum`, `betaNum`.

## Rate Limits
No published limit. Bulk data via FTP at ftp.ebi.ac.uk/pub/databases/gwas/

Follow HAL `_links.next.href` until absent and inspect `_links.search` for exact finder names/parameters. The official endpoint catalogue is https://www.ebi.ac.uk/gwas/rest/documents/api.html.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

