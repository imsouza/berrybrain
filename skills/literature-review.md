---
id: literature-review
name: Systematic Literature Review & State of the Art (PRISMA / Synthesis)
category: academic
description: Produz revisões sistemáticas de literatura, levantamentos do estado da arte e matrizes de síntese comparativa entre as fontes do Vault e evidências externas validadas pelo Enrich AI 24h.
task_types:
  - ask
  - synthesis
recommended_max_tokens: 4096
triggers:
  - revisao de literatura
  - revisão de literatura
  - revisao sistematica
  - revisão sistemática
  - revisao bibliografica
  - revisão bibliográfica
  - estado da arte
  - state of the art
  - literature review
  - systematic review
  - levantamento bibliografico
  - levantamento bibliográfico
  - referencial teorico
  - referencial teórico
keywords:
  - revisao
  - revisão
  - literatura
  - sistematica
  - sistemática
  - bibliografica
  - bibliográfica
  - estado da arte
  - prisma
  - estado-da-arte
---

# Skill: Systematic Literature Review & State of the Art

## 1. Diretrizes Epistêmicas
1. **Mapeamento Exaustivo do Acervo:** Agrupe todas as notas, conceitos, conexões e fontes validadas pelo Enrich AI 24h por eixos temáticos, cronológicos ou metodológicos.
2. **Convergências e Divergências:** Destaque explicitamente onde as fontes do vault concordam (`source_supports`, `shared_concept`) e onde há tensões, contradições (`source_contradicts`, `contradicts`) ou complementaridades (`source_expands`).
3. **Citação Estrita:** Toda afirmação atribuída a uma nota ou fonte deve conter `[Título](bbref:<evidenceId>)`.

## 2. Estrutura Obrigatória da Revisão de Literatura

### `# Revisão de Literatura: [Tema Central]`
### `## 1. Escopo e Questões Norteadoras`
- Definição do recorte temático e cobertura das fontes disponíveis no Vault e no Grafo.

### `## 2. Taxonomia Conceitual e Eixos Temáticos`
- Organização dos conceitos e tópicos do grafo em categorias estruturadas, explicando a evolução e relação entre cada linha de pensamento documentada nas notas.

### `## 3. Matriz Comparativa das Fontes Analisadas`
- Tabela Markdown contendo: **Fonte (`[Título](bbref:...)`)**, **Foco Principal / Conceitos-Chave**, **Abordagem / Evidência**, **Convergências / Limitações**.

### `## 4. Síntese Crítica (Consensos, Controvérsias e Fronteiras)`
- Análise integrada cruzando múltiplas notas (*multi-hop synthesis*).

### `## 5. Lacunas de Pesquisa Identificadas (Research Gaps)`
- Oportunidades de investigação e pontos ainda não cobertos pelo acervo atual.
