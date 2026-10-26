---
id: knowledge-enrichment-24h
name: 24h Continuous Knowledge Enrichment & Web Source Validation
category: enrichment
description: Governa o agente autônomo 24h (Enrich AI & Graph Research) que valida nós do grafo no próprio conteúdo do Vault, identifica lacunas e complementa/verifica fontes na internet com rastreabilidade epistêmica.
task_types:
  - enrich_node
  - research_graph
  - validate_web
  - ask
recommended_max_tokens: 2048
triggers:
  - enriquecer conhecimento
  - validar com fontes web
  - validar fontes na internet
  - enrich ai
  - enriquecimento continuo
  - enriquecimento contínuo
keywords:
  - enrich
  - enriquecimento
  - validacao web
  - validação web
---

# Skill: 24h Continuous Knowledge Enrichment & Web Source Validation

## 1. Princípios Fundamentais do Enrich AI 24h
1. **Soberania do Vault Local:** O conteúdo das notas do usuário (`sourceNotes`) e as conexões confirmadas (`connections`) são a referência primária de verdade do Segundo Cérebro.
2. **Validação e Complementação com Busca Web (`externalResearch` / Fontes Web):**
   - Quando um conceito, entidade, tópico ou nota possui evidência parcial, baixa confiança ou `validation_status` pendente, o agente utiliza os resultados verificados da pesquisa externa (`externalResearch`, fontes acadêmicas/enciclopédicas via SearXNG / Wikipedia / Crossref / OpenAlex) para:
     - **Validar (`source_supports`):** Confirmar que a definição ou relação local é consistente com a literatura externa.
     - **Expandir (`source_expands`):** Preencher contexto, definições formais e referências complementares sem sobrescrever a nota original do usuário.
     - **Sinalizar Divergência (`source_contradicts`):** Alertar de forma transparente caso uma fonte externa contradiga uma hipótese local.
3. **Rastreabilidade de Origem:** Toda evidência incluída no enriquecimento ou em respostas do Ask deve preservar sua fonte exata (título/caminho da nota local com `[Título](bbref:<evidenceId>)` ou URL/título da fonte externa verificada).
