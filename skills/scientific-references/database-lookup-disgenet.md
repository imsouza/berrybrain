---
id: sciref-database-lookup-disgenet
name: "Scientific Ref: DISGENET — Gene/variant–disease associations"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): DISGENET — Gene/variant–disease associations"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup disgenet"
  - "disgenet — gene/variant–disease associations"
keywords:
  - "database"
  - "lookup"
  - "disgenet"
  - "specialized"
  - "scientific"
  - "reference"
---

# DISGENET — Gene/variant–disease associations

Use the current [DISGENET documentation](https://www.disgenet.com/docs) and
[API/tools page](https://www.disgenet.com/Tools). The old disgenet.org API and
email/password login recipes are not the current integration contract.

Access is plan-dependent: the [Academic plan](https://www.disgenet.com/Plans)
exposes the curated subset; full-dataset API access requires an appropriate
subscription. Obtain a key and the current base URL, authorization-header
syntax and endpoint schema from the account's API documentation before running
requests. These authenticated details could not be independently verified in
this review, so no speculative URL or token exchange is provided.

For a reproducible retrieval, choose gene–disease (GDA) or variant–disease (VDA),
resolve the input identifier, and save source filters, release, evidence rows,
PMIDs, score fields and pagination metadata. Summary rows aggregate evidence;
inspect supporting evidence before making a mechanistic claim.

[Current score guidance](https://support.disgenet.com/support/solutions/articles/202000100283-what-are-the-gda-score-vda-score-disgenet-score-)
removes the former cap at 1. Do not treat the raw DISGENET score as a probability,
clamp it to [0,1], or confuse it with a normalized score. DSI measures disease
specificity and DPI pleiotropy; neither is causal evidence.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

