---
id: scientific-article
name: Scientific Article & Academic Paper (IMRaD / ABNT / IEEE / SBC)
category: academic
description: Estrutura e redige artigos científicos completos no padrão acadêmico internacional (IMRaD, IEEE, ACM, SBC, JBCS, ABNT) fundamentados exclusivamente nas evidências do Vault, do Grafo de Conhecimento e das fontes validadas pelo Enrich AI 24h.
task_types:
  - ask
  - synthesis
  - draft
recommended_max_tokens: 4096
triggers:
  - artigo cientifico
  - artigo científico
  - scientific article
  - scientific paper
  - academic paper
  - research paper
  - paper academico
  - paper acadêmico
  - imrad
  - formato ieee
  - formato sbc
  - formato abnt
  - escrever um artigo
  - criar um artigo
  - redigir um artigo
  - elabore um artigo
  - gere um artigo
keywords:
  - artigo
  - cientifico
  - científico
  - paper
  - abstract
  - resumo
  - metodologia
  - experimentos
  - resultados
  - imrad
  - abnt
  - ieee
  - sbc
---

# Skill: Scientific Article & Academic Paper (IMRaD / ABNT / IEEE / SBC)

## 1. Objetivo e Princípios Epistêmicos do BerryBrain
Quando acionada, esta skill transforma a resposta em um **Artigo Científico rigoroso, completo e formalmente estruturado**, seguindo o padrão **IMRaD** (*Introduction, Methodology, Results, and Discussion*) compatível com periódicos e conferências (IEEE, ACM, SBC, JBCS, Springer, ABNT).

**Regras Inegociáveis do BerryBrain:**
1. **Ancoragem Primária no Próprio Conteúdo (Vault & Grafo):** Todo conceito, premissa, dado empírico, equação ou conclusão DEVE vir das notas do usuário, anexos processados e nós/arestas do Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Quando o pacote de evidências contiver nós enriquecidos ou fontes externas validadas (`source_supports`, `source_expands`, `source_contradicts`, `web_validated`), utilize-os para fundamentar o referencial teórico e a validação cruzada.
3. **Citação Verificável Obrigatória:** Cite cada fonte diretamente nas sentenças usando exatamente o formato `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente referências bibliográficas fora do conjunto de evidências.
4. **Transparência sobre Lacunas:** Se alguma seção do padrão IMRaD (por exemplo, uma métrica experimental específica) não constar integralmente nas notas atuais, estruture a seção com o que está provado nas evidências e aponte explicitamente a lacuna epistêmica sob *Limitações / Trabalhos Futuros*.

## 2. Estrutura Obrigatória do Artigo Científico (Markdown)

Organize o documento exatamente com as seguintes seções em Markdown (no idioma solicitado pelo usuário):

### `# [Título Acadêmico Preciso e Descritivo]`

### `## Resumo / Abstract`
- Parágrafo único e denso (150–250 palavras) contendo: **Contexto**, **Problema de Pesquisa**, **Objetivo/Proposta**, **Método/Arquitetura**, **Principais Resultados/Evidências** e **Conclusão**.
- Seguido de **Palavras-chave / Keywords:** 4 a 6 termos técnicos extraídos dos conceitos do grafo.

### `## 1. Introdução (Introduction)`
- Contextualização do domínio com base nas notas do vault `[Fonte](bbref:...)`.
- Declaração clara do problema ou lacuna (*knowledge gap*) identificada no grafo.
- Questões de pesquisa (*Research Questions*) ou hipóteses extraídas das evidências.
- Lista objetiva das principais contribuições sistematizadas a partir do acervo.

### `## 2. Fundamentação Teórica e Trabalhos Relacionados (Background & Related Work)`
- Definição formal dos conceitos centrais, entidades e tópicos conectados no Grafo de Conhecimento.
- Síntese das relações semânticas (`semantic_relation`, `shared_concept`, `derived_from`, `source_supports`) entre as notas e fontes validadas.

### `## 3. Metodologia / Arquitetura Proposta (Methodology & Architecture)`
- Descrição sistemática dos métodos, algoritmos, fluxos de trabalho, modelagem matemática (usando blocos LaTeX `$$ ... $$` quando aplicável) ou decisões arquiteturais documentadas nas notas.
- Caso haja fluxo estrutural claro nas evidências, inclua um diagrama `mermaid` ou tabela síntese.

### `## 4. Análise de Evidências, Experimentos e Resultados (Evidence Analysis & Results)`
- Apresentação estruturada das evidências empíricas, observações, métricas, comparações ou estudos de caso presentes nas notas e anexos.
- Tabelas comparativas em Markdown relacionando achados e respectivas fontes `[Fonte](bbref:...)`.

### `## 5. Discussão, Ameaças à Validade e Limitações (Discussion & Limitations)`
- Interpretação crítica dos resultados frente às hipóteses iniciais.
- **Limitações Epistêmicas e Lacunas do Acervo:** explicitação honesta do que as evidências atuais cobrem com alta confiança e do que permanece como hipótese aberta ou lacuna no grafo.

### `## 6. Conclusão e Trabalhos Futuros (Conclusion & Future Work)`
- Síntese das conclusões comprovadas pelas evidências.
- Direções de pesquisa futura ou novos experimentos sugeridos pelas lacunas do segundo cérebro.

### `## Referências Fundamentadas no Vault & Grafo`
- Lista consolidada de todas as fontes citadas com seus links verificáveis `[Título](bbref:<evidenceId>)`.
