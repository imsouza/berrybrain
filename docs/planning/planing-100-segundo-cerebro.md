# BerryBrain 100% Segundo Cerebro - Planning

## Veredito atual

O BerryBrain ainda nao esta 100% como segundo cerebro real. A arquitetura correta ja existe em parte, mas ainda faltam garantias operacionais e cognitivas.

Estado validado em 2026-07-09:

- Cognitive Layer criada: `Knowledge Base`, `Knowledge Graph`, `Semantic Data Layer`, `Model Router` e `Retrieval Orchestrator`.
- Modelo configurado: `qwen/qwen3.5-397b-a17b` via cloud/NVIDIA NIM.
- Grafo atual: 29 nos, 28 conexoes.
- Grafo apos limpeza/enriquecimento: 28 nos, 41 arestas totais, 31 arestas visiveis.
- Evidencia nos nos visiveis: 100%.
- Contexto IA nos nos visiveis: 100%.
- Arestas com motivo: 100%.
- Insights reais: 3 insights validados com `why_it_matters`, evidencia, acao, impacto no grafo, raciocinio, provider/model e nos enriquecidos.
- Arestas de insight: 13 `insight_suggested` conectando insights as fontes citadas.
- Knowledge Base: 9 notas indexadas, 6 notas processaveis, 6 embeddings.
- Embedding model: `nvidia/nv-embed-v1`.
- Jobs atuais: sem pendentes/running; existem falhas historicas antigas.

Conclusao: a base cognitiva ja opera com KB, grafo e camada semantica. O ponto ainda mais critico e a qualidade dos insights: eles precisam ser gerados somente quando houver evidencia real, explicacao, impacto no grafo e acao concreta.

## O que falta para 100%

### 1. Knowledge Base semantica real

Status: executado para o banco local atual.

Falta:

- Adapter externo Qdrant/Chroma ainda e opcional/futuro; SQLite segue default local-first.
- Persistir chunks formais em `kb_chunks` ainda e melhoria futura; hoje o chunking e calculado e os embeddings ficam por nota.
- Retrieval vetorial por chunk ainda nao substitui o lexical; a cobertura de embeddings ja existe.
- Reindexacao por alteracao de nota precisa continuar sendo validada em fluxo real.

Critério de pronto:

- `embeddings > 0`. OK.
- 100% das notas processaveis com embedding ou erro explicito. OK no vault atual.
- Busca por pergunta retorna chunks relevantes por similaridade.
- Cada resposta mostra chunks/fontes usados.

### 2. Model Router confiavel

Status: parcial.

Falta:

- Centralizar todas as chamadas IA em um router unico.
- Registrar `provider`, `model`, `promptVersion`, `latencyMs`, `status`, `error`, `estimatedCost`.
- Validar schema JSON por tarefa.
- Fazer retry com prompt de reparo quando Qwen/NIM retorna JSON invalido.
- Separar modelos por tarefa: embeddings, enrich node, graph infer, insight engine, title.

Critério de pronto:

- Nenhuma chamada IA importante fica sem log.
- Falha de modelo nunca cria dado falso.
- JSON invalido vira erro recuperavel ou retry controlado.
- UI mostra provider/model usado.

### 3. Graph Node Enrichment

Status: executado para nos visiveis atuais.

Falta:

- Corrigir prompt/schema do `ENRICH_GRAPH_NODE`. OK.
- Gerar `aiSummary`, `aiContext`, `sourceEvidence`, `learningValue`, `sourceQuality`. OK para 87.5% dos nos visiveis.
- Enriquecer nos de nota, conceito, topico, contexto, insight e lacuna. Parcial: nos uteis atuais enriquecidos; futuros nos devem seguir o mesmo job.
- Nao aceitar resposta vazia. OK.
- Reprocessar nos antigos sem contexto. OK para os candidatos uteis atuais.

Critério de pronto:

- `pct_with_ai_context >= 80%` para nos visiveis. OK: 87.5%.
- Cada no importante explica por que existe.
- Cada no mostra origem, evidencia e modelo.

### 4. Insight Engine real

Status: executado para o vault atual.

Falta:

- Gerar insights usando KB + Graph + Semantic Data juntos. OK: worker consulta `/api/v1/cognitive/retrieve`.
- Bloquear insights genericos por validador. OK: `/api/v1/insights/sync` rejeita titulo generico, evidencia fraca e campos cognitivos ausentes.
- Cada insight deve ter:
  - conclusao ou hipotese;
  - por que importa;
  - evidencias;
  - impacto no grafo;
  - acao sugerida;
  - confianca;
  - provider/model.
- Criar insight nodes conectados aos nos/fontes que sustentam o insight. OK: arestas `insight_suggested` criadas a partir das evidencias.

Critério de pronto:

- Insights nao sao contadores. OK para novos insights.
- Insights citam notas, chunks e conexoes reais. OK.
- Home e tela Insights mostram descobertas uteis, nao mensagens genericas. OK para novos insights; insights legados incompletos foram filtrados.

### 5. Graph Inference Search

Status: executado.

Falta:

- Usar sempre KB + Graph + Semantic quando a pergunta envolver conhecimento. OK.
- Destacar nos relacionados na tela. OK: `GraphCanvas` recebe `highlightedIds`.
- Permitir criar insight a partir da resposta. OK: `/api/v1/insights/from-inference` usa Cognitive Layer.
- Permitir criar nota permanente a partir da resposta.
- Permitir sugerir conexao nova com status `suggested`.
- Responder `insufficient_evidence` quando nao houver base real.

Critério de pronto:

- Perguntas como "qual a relacao entre Docker e Linux shell?" citam notas e arestas. OK.
- Perguntas sobre jobs usam Semantic Data Layer. OK.
- Perguntas sobre conceitos fracos usam Graph + stats. OK pela rota hibrida.
- UI mostra evidencias e acoes. OK; evidencias ricas agora renderizam sem `[object Object]`.

### 6. Knowledge Graph consistente

Status: parcial.

Falta:

- Remover/ignorar nos fracos como `pt-BR` e `Nao especificado no prompt`.
- Deduplicar topicos/conceitos equivalentes.
- Padronizar tipos: `note`, `concept`, `topic`, `context`, `entity`, `insight`, `gap`, `source`.
- Toda aresta deve ter `reason`, `evidence`, `confidence`, `provider`, `model`, `status`.
- Criar lacunas reais como nos conectados.
- Criar conexoes semanticas por embedding quando KB estiver pronta.

Critério de pronto:

- Grafo visual nao mostra lixo por padrao.
- Grafo tem relacoes uteis, nao apenas backlinks/topicos.
- Confirm/ignore muda estado e a UI reflete.
- No duplo clique abre nota; clique unico abre painel.

### 7. Semantic Data Layer completo

Status: executado.

Falta:

- Expor perguntas naturais sobre:
  - jobs;
  - erros;
  - fila;
  - notas nao assimiladas;
  - cobertura de embeddings;
  - cobertura do grafo;
  - insights pendentes;
  - conexoes sugeridas;
  - provider status.
- Criar endpoints agregados para qualidade do sistema. OK: `/api/v1/cognitive/semantic-data`.

Critério de pronto:

- "Por que nao esta processando?" retorna causa objetiva. OK.
- "Quais notas nao foram assimiladas?" retorna lista real. OK.
- "Quais jobs falharam?" retorna tipo, erro e acao. OK.

### 8. Home como centro cognitivo

Status: parcial.

Falta:

- Mostrar "O que o cerebro aprendeu recentemente".
- Mostrar qualidade da KB, Graph e Semantic Layer.
- Mostrar progresso por etapa.
- Mostrar insights reais com evidencia.
- Mostrar lacunas reais.
- Mostrar alertas uteis, nao ruido.

Critério de pronto:

- Home responde rapidamente:
  - sistema funcionando?
  - o que foi processado?
  - o que a IA descobriu?
  - o que falta?
  - o que revisar/criar/conectar?

### 9. Revisao sem flashcards legados

Status: pendente.

Falta:

- Remover resquicios de flashcards se o produto nao usa mais.
- Substituir por "review prompts" ou "study actions" derivados de insights/conceitos.
- Revisao deve usar KB + Graph para sugerir perguntas.

Critério de pronto:

- Nenhum job/estatistica antiga de flashcard aparece se removido.
- Revisao mostra acoes cognitivas reais.

### 10. Observabilidade e testes

Status: parcial.

Falta:

- Testes para:
  - Cognitive Layer retrieval;
  - graph inference;
  - JSON repair;
  - enrich node sem resposta util;
  - semantic data query;
  - graph quality report;
  - job dependency/recovery.
- Dashboard de qualidade do cerebro.

Critério de pronto:

- Testes passam.
- Jobs nao ficam presos apos restart.
- Falhas aparecem como problema acionavel.

## Fases de implementacao

### Fase 1 - KB real com embeddings

1. Criar tabela/estrutura `kb_chunks`. Parcial/futuro.
2. Gerar chunks por nota. OK em runtime.
3. Gravar embeddings por chunk. Parcial: embeddings por nota no banco atual.
4. Adicionar adapter Qdrant/Chroma opcional. Configuravel no Settings; adapter externo futuro.
5. Alterar retrieval para vetor quando embeddings existirem. Pendente.
6. Expor cobertura da KB. OK em `/api/v1/cognitive/status`.

### Fase 2 - Graph cleanup e enriquecimento

1. Filtrar lixo semantico. OK.
2. Deduplicar topicos/conceitos. Parcial, com limpeza de duplicatas/lixo atual.
3. Corrigir prompt do enrich node. OK.
4. Reprocessar nos sem contexto. OK para nos uteis atuais.
5. Validar `pct_with_ai_context`. OK: 87.5% dos nos visiveis.

### Fase 3 - Insight Engine

1. Gerar insights por KB + Graph + Semantic. OK.
2. Validar contra genericidade. OK.
3. Criar nos de insight conectados. OK.
4. Mostrar na Home/Insights/Grafo. OK para novos insights validados.

### Fase 4 - Semantic Data Layer

1. Criar endpoints de perguntas estruturadas. OK: `/api/v1/cognitive/semantic-data`.
2. Unificar jobs/status/quality. OK: estado semantico inclui jobs, failures, KB, grafo, insights e provider.
3. Mostrar diagnostico de processamento. OK: `/api/v1/cognitive/query` responde com causa objetiva usando semantic data.

### Fase 5 - Graph inference UI

1. Mostrar evidencias por resposta. OK.
2. Destacar nos relacionados. OK.
3. Criar insight/conexao/nota a partir da inferencia. Parcial: insight OK; nota pode ser criada pelo fluxo de insight; conexao sugerida direta ainda e futura.

### Fase 6 - Neo4j opcional

1. Manter SQLite como default local-first.
2. Criar interface de repositorio para grafo.
3. Implementar Neo4j apenas quando volume justificar.

## Definicao de 100%

BerryBrain sera considerado 100% segundo cerebro quando:

- 100% das notas processaveis estiverem chunkadas.
- 100% das notas processaveis tiverem embedding ou erro explicito.
- 80%+ dos nos visiveis tiverem contexto IA com evidencia.
- 100% das conexoes visiveis tiverem reason/evidence/confidence/status.
- Insights reais forem gerados com evidencia e acao.
- Perguntas no grafo usarem KB + Graph + Semantic Data.
- Home mostrar aprendizado recente, lacunas, acoes e problemas reais.
- Worker nao ficar preso apos falha/restart.
- Nenhum dado cognitivo importante for mock/hardcoded.
