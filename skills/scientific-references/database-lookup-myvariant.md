---
id: sciref-database-lookup-myvariant
name: "Scientific Ref: MyVariant.info"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): MyVariant.info"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup myvariant"
  - "myvariant.info"
keywords:
  - "database"
  - "lookup"
  - "myvariant"
  - "specialized"
  - "scientific"
  - "reference"
---

# MyVariant.info

Public annotation aggregation service: `https://myvariant.info/v1`.
[Annotation contract](https://docs.myvariant.info/en/latest/doc/variant_annotation_service.html)
and [query contract](https://docs.myvariant.info/en/latest/doc/variant_query_service.html).

```text
GET /query?q=rs28934578&fields=cadd.phred,dbsnp.rsid&size=5
GET /variant/chr17:g.7578406C%3EG?fields=cadd.phred,dbsnp.rsid
```

`/variant/{id}` uses HGVS genomic identifiers on hg19 as documented. A returned
`hg38` coordinate field does not change the input identifier convention.
An rsID can produce multiple alternate-allele hits; compare alleles and assembly
before selecting a hit. `fields` supports comma-separated fields and dot paths.
Batch POST `/variant` accepts at most 1,000 `ids`; larger inputs can be omitted.
Query results use `hits`, `total`, and pagination parameters `size`/`from`.

Scores are aggregated from particular source releases. Record source and model
versions, genome assembly, alleles, transcript and retrieval date. A difference
between a stored CADD score and an Ensembl VEP score may reflect a release,
assembly or model difference; there is no justified universal PHRED threshold
for declaring a score stale. For clinical classifications, retrieve the full
ClinVar record, review status, condition and conflicting submissions.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

