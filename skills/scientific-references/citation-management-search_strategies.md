---
id: sciref-citation-management-search-strategies
name: "Scientific Ref: Search Strategies"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (citation-management): Search Strategies"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "citation management search strategies"
  - "citacao management search strategies"
  - "search strategies"
keywords:
  - "citation"
  - "management"
  - "search"
  - "strategies"
  - "citacao"
  - "specialized"
  - "scientific"
  - "reference"
---

# Search Strategies

Google Scholar and PubMed query construction: operators, field tags, MeSH terms,
date and publication-type filters, and worked query examples.

## Search Strategies

### Google Scholar Best Practices

Use [Google Scholar's documented search controls](https://scholar.google.com/intl/en/scholar/help.html):
quoted titles/phrases, `author:`, exclusion terms, and the Advanced Search
publication/title/date fields. Use year controls or script arguments rather
than `2020..2024`; Scholar does not offer a global `sort:citations` operator.
Citation counts reflect age, field, and database coverage; they are discovery
signals, not evidence-quality thresholds.

```bash
# Find recent reviews; examples are illustrative searches.
python scripts/search_google_scholar.py 'CRISPR review' --year-start 2023 --year-end 2024

# Author and topic
python scripts/search_google_scholar.py 'author:Church "synthetic biology"'

# Citation sorting applies only to the retrieved sample.
python scripts/search_google_scholar.py '"deep learning"' \
  --year-start 2012 --year-end 2015 --sort-by citations --limit 50
```

For global citation-count ordering over API search matches, use the bundled
OpenAlex client (`--sort-by citations`); document the different database coverage.

### PubMed Best Practices

**Using MeSH Terms**:
MeSH (Medical Subject Headings) provides controlled vocabulary for precise searching.

1. **Find MeSH terms** at https://meshb.nlm.nih.gov/search
2. **Use in queries**: `"Diabetes Mellitus, Type 2"[MeSH]`
3. **Combine with keywords** for comprehensive coverage

**Field Tags**:
```
[Title]              # Search in title only
[Title/Abstract]     # Search in title or abstract
[Author]             # Search by author name
[Journal]            # Search specific journal
[Publication Date]   # Date range
[Publication Type]   # Article type
[MeSH]              # MeSH term
```

**Building Complex Queries**:
```bash
# Clinical trials on diabetes treatment published recently
"Diabetes Mellitus, Type 2"[MeSH] AND "Drug Therapy"[MeSH] 
AND "Clinical Trial"[Publication Type] AND 2020:2024[Publication Date]

# Reviews on CRISPR in specific journal
"CRISPR-Cas Systems"[MeSH] AND "Nature"[Journal] AND "Review"[Publication Type]

# Specific author's recent work
"Smith AB"[Author] AND cancer[Title/Abstract] AND 2022:2024[Publication Date]
```

**E-utilities for Automation**:
The bundled PubMed script uses ESearch and EFetch. Other E-utilities are documented
manual alternatives:
- **ESearch**: Search and retrieve PMIDs
- **EFetch**: Retrieve full metadata
- **ESummary**: Get summary information
- **ELink**: Find related articles

See `references/pubmed_search.md` for complete API documentation.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

