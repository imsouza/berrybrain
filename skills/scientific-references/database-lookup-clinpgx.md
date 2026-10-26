---
id: sciref-database-lookup-clinpgx
name: "Scientific Ref: ClinPGx (PharmGKB) API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): ClinPGx (PharmGKB) API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup clinpgx"
  - "clinpgx (pharmgkb) api"
keywords:
  - "database"
  - "lookup"
  - "clinpgx"
  - "specialized"
  - "scientific"
  - "reference"
---

# ClinPGx (PharmGKB) API

Base: `https://api.clinpgx.org/v1`. Public read access, JSON, at most **2 requests/second**.
The old `api.pharmgkb.org` hostname was shut down July 20, 2026.
See the [service notice](https://api.clinpgx.org/) and
[current OpenAPI schema](https://api.clinpgx.org/openapi.json).

| GET path | Purpose |
|---|---|
| `/data/gene?symbol=CYP2D6` | Resolve gene to PA accession |
| `/data/chemical?name=warfarin` | Resolve drug/chemical |
| `/data/summaryAnnotation?location.genes.symbol=CYP2C19&relatedChemicals.name=clopidogrel&levelOfEvidence.term=1A` | Clinical summary annotations |
| `/data/guidelineAnnotation?source=CPIC&relatedGenes.accessionId={PA_ID}` | Prescribing guideline annotations |
| `/data/pathway?name={name}` | Pathways by name |
| `/data/label?relatedChemicals.name=warfarin&source=FDA` | Drug-label annotations |

Each resource also supports `/{id}` lookup. `view` controls returned detail;
use the enum for that resource in the schema. Inspect the JSON envelope and
`data` field; these endpoints do not share a documented `page`/`size` search API.
Do not substitute invented `/drug`, `/clinicalAnnotation`, `/guideline`,
`/drugLabel` or general `/search` routes.

Resolve PA identifiers before joining resources. Keep annotation evidence level,
gene, allele/diplotype, phenotype, population and guideline source/version.
A pharmacogenomic association alone is not an individualized dosing recommendation.
Bulk exports and reuse are governed by ClinPGx's data-use policy (CC BY-SA 4.0).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

