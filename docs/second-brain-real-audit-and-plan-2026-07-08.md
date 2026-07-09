# Segundo Cérebro Real - Auditoria e Plano

Data: 2026-07-08

Escopo auditado:
- API: `apps/api/src/berrybrain_api/models.py`, `services.py`, `home_summary.py`, routers `graph.py`, `connections.py`, `concepts.py`, `insights.py`, `monitor.py`, `settings.py`.
- Worker: `apps/worker/src/berrybrain_worker/main.py`, gateways local/cloud.
- Web: `apps/web/src/components/graph-screen.tsx`, `graph-view.tsx`, `home/home-view.tsx`, `panel/right-panel.tsx`, `settings-panel.tsx`.
- Prompts: `prompts/assimilation.v1.md`, `connections.v1.md`, `daily-insights.v1.md`, `classify-note.v1.md`.
- Banco: `data/sqlite/berrybrain.db`.
- Endpoints consultados: `/api/v1/home/summary`, `/api/v1/graph`, `/api/v1/concepts`, `/api/v1/connections`, `/api/v1/insights`.

## Estado Atual do Banco

Dados reais persistidos:

- `notes`: 20
- `concepts`: 0
- `connections`: 0
- `graph_nodes`: 0
- `graph_edges`: 0
- `insights`: 0
- `flashcards`: 21
- `jobs`: 153
- `generated_metadata`: 13
- `embeddings`: 2
- `automation_logs`: 148
- `worker_status`: 1

Tipos de metadata existentes:

- `classification`: 2
- `flashcards`: 1
- `gaps`: 1
- `parse`: 7
- `questions`: 1
- `summary`: 1

Endpoints reais:

- `/api/v1/graph`: 200, retorna 20 nós de nota, 0 arestas.
- `/api/v1/home/summary`: 200, retorna progresso, Home summary, grafo resumido e seções novas, mas conceitos/conexões/insights vazios.
- `/api/v1/concepts`: 200, retorna `concepts: []`.
- `/api/v1/connections`: 200, retorna `connections: []`.
- `/api/v1/insights`: 200, retorna `insights: []`.

Conclusão curta:

O BerryBrain já tem uma base operacional real de notas, jobs, metadata, embeddings, flashcards, logs, provider local/cloud e Home summary. Ainda não é um segundo cérebro real: os nós dinâmicos, conceitos persistidos, conexões explicáveis, insights reais, inferência no grafo e painéis de assimilação ainda estão ausentes ou parciais.

## Relatório Obrigatório

| Área | Status | Evidência | Problema | Ação |
|---|---|---|---|---|
| Extração de conceitos | PARCIAL | Worker salva `concepts` em metadata em `apps/worker/src/berrybrain_worker/main.py:418`; modelo `ConceptRecord` existe em `apps/api/src/berrybrain_api/models.py:66`; DB `concepts: 0`; `/api/v1/concepts` retorna lista vazia. | A IA pode retornar conceitos na assimilação, mas eles não viram entidades persistidas no grafo; ficam no máximo em `generated_metadata`. Não há frequência, related notes, provider/model, confidence ou status real por conceito. | Criar `conceptExtractionService`; persistir conceitos em tabela própria/relacional; popular `ConceptRecord`; registrar provider/model/promptVersion/evidence; criar nós conceituais. |
| Extração de contexto | PARCIAL | `process_parse_note` extrai frontmatter, links, headings, word count e language em `worker/main.py:283`; `process_assimilate_note` salva summary/gaps/questions em `worker/main.py:406`. | Contexto semântico não é entidade. Não existe `ContextNode`, `TopicNode` ou contexto da nota com evidência e status. | Adicionar jobs `EXTRACT_CONTEXT` e `DETECT_TOPICS`; criar modelo/metadata de contexto com `sourceNoteIds`, confidence e provider/model. |
| Nós dinâmicos | PARCIAL | `GraphNodeRecord` existe em `models.py:172`; `sync_knowledge_graph` cria nós de nota e conceito em `services.py:424`; `/api/v1/graph` monta nós dinâmicos em memória em `services.py:357`; DB `graph_nodes: 0`. | Grafo exibido não usa nós persistidos; só retorna notas markdown. Conceitos existem no código, mas não no banco. Não há nós de tópico/contexto/entidade/insight/lacuna/trilha/anexo. | Expandir schema de `graph_nodes`; criar serviço `graphExpansionService`; persistir nós sugeridos/confirmados; suportar tipos obrigatórios. |
| Conexões reais | PARCIAL | `ConnectionRecord` existe em `models.py:79`; `connections.v1.md` exige `confidence` e `reason`; worker chama `/api/v1/connections/sync` em `worker/main.py:585`; DB `connections: 0`. | Infra existe, mas estado atual não tem conexões. Sem evidence, provider/model, status, sourceNoteIds, label, createdByModel. Sync aceita `reason` vazio; não rejeita conexão sem explicação. | Criar `connectionReasoningService`; exigir reason/evidence; adicionar status `suggested/confirmed/ignored`; adicionar confirm/ignore/reprocess; criar conexões por backlink/shared_concept/semantic_similarity/inferência. |
| Insights reais | PARCIAL | `InsightRecord` existe em `models.py:113`; `routers/insights.py:20` sincroniza payload; worker `process_generate_insights` chama `/insights/sync` em `worker/main.py:667`; Home mostra `recentInsights` em `home-view.tsx`; DB `insights: 0`. | A estrutura existe, mas não há insights atuais. Insight não guarda evidence, action, graphImpact, provider/model, status nem source concepts. Não existe tela dedicada Insights auditada além do endpoint/lista. | Criar `insightGenerationService`; gerar insights a partir de graph + metadata + embeddings; persistir evidence/action/impact; expor Home, tela Insights, painel da nota e grafo. |
| Inferência no grafo | FALTA | `graph-screen.tsx:54` tem busca textual por label; não existe `/api/v1/graph/infer`; nenhum `GraphInferenceSearch`; nenhuma chamada ao modelo usando grafo. | Busca atual só filtra nome. Não responde perguntas, não usa evidências, não cria insight a partir de inferência. | Criar `graphInferenceService`, prompt `graph-infer.v1.md`, endpoint `POST /api/v1/graph/infer` e componente `GraphInferenceSearch`. |
| Resumo por nó | PARCIAL | `GraphScreen` tem drawer em `graph-screen.tsx:123`; mostra tipo, pasta, conexões, status e abrir nota. `GeneratedMetadataRecord` guarda summary por nota em `models.py:149`. | Painel é técnico e raso. Não mostra resumo curto/expandido, conceitos, contexto, insights, lacunas, flashcards, evidência, origem, provider/model ou por que o nó existe. Não há endpoint `/graph/nodes/:id/summary`. | Criar `nodeSummaryService`; endpoints de node detail/summary; painel por tipo de nó. |
| Expansão automática do grafo | PARCIAL | Pipeline atual: `PARSE_NOTE`, `CLASSIFY_NOTE`, `ASSIMILATE_NOTE`, `GENERATE_EMBEDDING`, `FIND_CONNECTIONS`, `GENERATE_FLASHCARDS`, `GENERATE_INSIGHTS` em `worker/main.py:136`; `sync_knowledge_graph` existe em `services.py:424`. | Não há jobs específicos `EXTRACT_CONCEPTS`, `EXTRACT_CONTEXT`, `EXTRACT_ENTITIES`, `DETECT_TOPICS`, `GENERATE_NODE_SUMMARY`, `GENERATE_INFERRED_CONNECTIONS`, `UPDATE_GRAPH_CLUSTERS`, `EXPAND_KNOWLEDGE_GRAPH`. Grafo não cresce dinamicamente na prática: conceitos/conexões/arestas persistidas estão zerados. | Criar pipeline de expansão com jobs granulares, progresso por etapa, sync automático do grafo e logs de cada mutação. |

## Auditoria Expandida

| Item | Status | Evidência | Observação |
|---|---|---|---|
| Criação de nós conceituais | PARCIAL | `sync_knowledge_graph` cria nós para `ConceptRecord` em `services.py:456`; DB `concepts: 0`, `graph_nodes: 0`. | Código existe, dados não chegam. |
| Criação de nós por entidade | FALTA | Nenhum `EntityRecord`, job `EXTRACT_ENTITIES`, prompt ou UI. | Ausente. |
| Criação de nós por tópico | FALTA | Nenhum `TopicRecord`, job `DETECT_TOPICS`, prompt ou UI. | Ausente. |
| Conexões por backlinks | PARCIAL | `process_parse_note` extrai `links` em `worker/main.py:310`; `build_graph` não cria conexão por backlink. | Links são metadata, não arestas. |
| Conexões por conceitos em comum | FALTA | Não existe serviço de shared concept. | Precisa de concept-note relation. |
| Conexões por inferência da IA | PARCIAL | `FIND_CONNECTIONS` usa `connections.v1.md` e `/connections/sync`; DB `connections: 0`. | Infra existe, sem resultado atual. |
| Insights salvos no banco | PARCIAL | `InsightRecord`; DB `insights: 0`. | Estrutura sem dados. |
| Insights na Home | PARCIAL | `home-view.tsx` renderiza `recentInsights`; endpoint retorna 0. | UI pronta, sem conteúdo real. |
| Insights na tela Insights | FALTA/PARCIAL | Endpoint existe; não foi encontrada página dedicada `Insights`. | Falta tela própria. |
| Insights no painel da nota | FALTA | `right-panel.tsx` não mostra insights por nota. | Ausente. |
| Insights no grafo | FALTA | Grafo só suporta tipos visualmente note/concept/tag/orphan; não há insight nodes. | Ausente. |
| Explicação por conexão | PARCIAL | `reason` existe em `ConnectionRecord` e edge payload; UI Home mostra reason se houver. | Sem evidence; reason pode ser vazio. |
| Busca/inferência no grafo | PARCIAL/FALTA | Busca textual simples em `graph-screen.tsx:54`; inferência ausente. | Precisa separar search/infer. |
| Atualização dinâmica após processamento | PARCIAL | Jobs rodam e logs existem; graph sync não é acionado automaticamente após concepts/connections. | Precisa orquestração. |
| Status por etapa | PARCIAL | Jobs têm status em `JobRecord`; Home mostra progresso global. | Falta pipeline visual `Expandindo grafo 6/10`. |
| Provider/model em nós/conexões/insights | PARCIAL/FALTA | `GeneratedMetadataRecord.model_used`; `EmbeddingRecord.model`; `ConnectionRecord` e `InsightRecord` não têm provider/model. | Precisa schema novo. |
| Eventos/undo/ignore | PARCIAL | `AutomationLogRecord` existe; insights têm dismiss; conexões/nós não têm confirm/ignore. | Falta lifecycle do grafo. |

## Problemas Estruturais

1. Grafo atual é derivado, não persistido como conhecimento vivo.
   - `GET /api/v1/graph` usa `build_graph`, que lê `NoteRecord` e `ConnectionRecord`, monta nós em memória e ignora `GraphNodeRecord`/`GraphEdgeRecord`.

2. Conceito não é uma entidade real no uso atual.
   - O worker pode salvar conceitos como metadata, mas não preenche a tabela `concepts`.

3. Conexões não são aceitáveis para segundo cérebro real.
   - Faltam evidence, sourceNoteIds, provider, model, promptVersion, status, updatedAt.
   - A API não rejeita conexão sem `reason`.

4. Insight ainda é “card de texto”, não unidade de assimilação.
   - Faltam evidências, impacto no grafo, ação sugerida, status, provider/model e relação com nós.

5. Busca do grafo não é inferência.
   - Não chama IA, não consulta evidências, não cita notas.

6. Painel de nó não explica “por que este nó existe”.
   - Mostra tipo/pasta/status/conexões, mas não resumo útil, conceitos, lacunas, insights ou evidência.

7. Pipeline de expansão não é granular.
   - Jobs atuais são bons para MVP, mas não representam as etapas obrigatórias do segundo cérebro real.

## Abordagens Possíveis

### Opção A - Evolução Incremental Recomendada

Expandir o sistema atual em camadas:

1. Schema novo para nós/arestas/insights com status, evidence, provider/model e lifecycle.
2. Serviços reais: concept extraction, graph expansion, node summary, connection reasoning, insight generation.
3. Endpoints do grafo vivo.
4. UI do grafo: search/inference, node panel, connection detail.
5. Home e painel da nota usando os novos dados.

Vantagem: preserva o app funcionando, usa jobs existentes, entrega valor em fases.
Risco: precisa cuidado em migração de dados.

### Opção B - Reescrever o Grafo Como Subsistema Separado

Criar um módulo novo isolado de graph domain, com tabelas e APIs próprias, e migrar a UI depois.

Vantagem: arquitetura mais limpa.
Risco: maior tempo até aparecer na Home e no grafo atual.

### Opção C - MVP Visual Primeiro

Criar UI e endpoints simulando campos futuros com dados parciais atuais.

Vantagem: rápido visualmente.
Risco: viola o requisito “não pode ser mock” e manteria o problema central.

Recomendação: Opção A.

## Desenho Proposto

### 1. Modelo de dados

Criar/expandir:

- `KnowledgeNodeRecord`
  - `id`, `type`, `label`, `title`, `summary`, `source`, `source_note_ids`, `source_attachment_ids`, `confidence`, `created_by`, `provider`, `model`, `prompt_version`, `status`, `created_at`, `updated_at`, `metadata`.

- `KnowledgeEdgeRecord`
  - `id`, `source_node_id`, `target_node_id`, `type`, `label`, `reason`, `evidence`, `source_note_ids`, `confidence`, `created_by`, `provider`, `model`, `prompt_version`, `status`, `created_at`, `updated_at`.

- `InsightRecord` expandido
  - `why_it_matters`, `evidence`, `suggested_action`, `graph_impact`, `source_node_ids`, `source_note_ids`, `provider`, `model`, `prompt_version`, `confidence`, `status`.

- `ConceptMentionRecord`
  - `concept_id`, `note_id`, `frequency`, `confidence`, `evidence`, `created_by`, `provider`, `model`.

Manter `GraphNodeRecord/GraphEdgeRecord` só se migrar para o novo schema; evitar duas fontes de verdade.

### 2. Serviços

Criar:

- `conceptExtractionService`
- `graphExpansionService`
- `graphInferenceService`
- `connectionReasoningService`
- `nodeSummaryService`
- `insightGenerationService`
- `graphStatsService`

Regra: nenhum nó/conexão/insight gerado por IA entra sem source/evidence/confidence/provider/model/status.

### 3. Jobs

Adicionar jobs:

- `EXTRACT_CONCEPTS`
- `EXTRACT_CONTEXT`
- `EXTRACT_ENTITIES`
- `DETECT_TOPICS`
- `GENERATE_NODE_SUMMARY`
- `GENERATE_CONCEPT_NODE`
- `GENERATE_CONTEXT_NODE`
- `GENERATE_INFERRED_CONNECTIONS`
- `GENERATE_GRAPH_INSIGHTS`
- `UPDATE_GRAPH_CLUSTERS`
- `UPDATE_GRAPH_STATS`
- `EXPAND_KNOWLEDGE_GRAPH`

Manter jobs atuais como compatibilidade e mapear:

- `ASSIMILATE_NOTE` vira orquestração de conceitos/contexto/lacunas.
- `FIND_CONNECTIONS` vira parte de `GENERATE_INFERRED_CONNECTIONS`.

### 4. Endpoints

Criar/validar:

- `GET /api/v1/graph/summary`
- `POST /api/v1/graph/rebuild`
- `POST /api/v1/graph/expand`
- `POST /api/v1/graph/infer`
- `GET /api/v1/graph/nodes/{id}`
- `GET /api/v1/graph/nodes/{id}/summary`
- `POST /api/v1/graph/nodes/{id}/reprocess`
- `POST /api/v1/graph/nodes/{id}/confirm`
- `POST /api/v1/graph/nodes/{id}/ignore`
- `GET /api/v1/graph/connections/{id}`
- `POST /api/v1/graph/connections/{id}/confirm`
- `POST /api/v1/graph/connections/{id}/ignore`
- `POST /api/v1/graph/connections/{id}/reprocess`
- `POST /api/v1/insights/generate`
- `POST /api/v1/insights/from-inference`
- `POST /api/v1/insights/{id}/apply`
- `POST /api/v1/insights/{id}/ignore`

### 5. Prompts versionados

Criar:

- `graph-expand.v1.md`
- `graph-infer.v1.md`
- `node-summary.v1.md`
- `connection-reason.v1.md`
- `concept-extract.v1.md`
- `insight-generate.v1.md`

Cada prompt deve exigir JSON com evidence, confidence, source ids e “insufficient evidence” quando não houver base.

### 6. UI

Grafo:

- `GraphInferenceSearch` no topo.
- Modo busca direta e modo inferência.
- Resultado com resposta curta, nós relacionados, conexões, evidências, ações.
- Painel de nó por tipo.
- Painel de conexão com reason/evidence/provider/model/status.
- Botões confirmar/ignorar/reprocessar.

Home:

- Conceitos emergentes usando `ConceptMentionRecord`.
- Conexões novas/sugeridas com evidence.
- Lacunas reais.
- Grafo vivo com últimos nós/arestas.
- Inferências recentes salvas.
- Próximas ações.

Painel da nota:

- Contexto da nota.
- Conceitos principais.
- Conexões relacionadas.
- Insights/lacunas.
- Timeline de processamento por etapa.

## Critérios de Pronto

Só considerar pronto quando:

- DB tiver conceitos e conexões reais após processar notas.
- `/api/v1/graph` retornar nós de tipos além de `note`.
- Conexões geradas tiverem `reason`, `evidence`, `confidence`, `provider`, `model`, `status`.
- Grafo tiver inferência com evidências e resposta “sem evidência suficiente” quando aplicável.
- Nó abrir painel de resumo útil.
- Home responder “o que meu segundo cérebro aprendeu recentemente?” com dados reais.
- Usuário puder confirmar/ignorar nós e conexões.
- Eventos forem registrados em `automation_logs`.
- Build e testes passarem.

## Próximo Passo Recomendado

Implementar a Opção A em fases:

1. Schema e services base de conhecimento.
2. Persistência real de conceitos a partir do worker.
3. Conexões com evidence/status/provider/model.
4. Grafo usando nós/arestas persistidos.
5. Node summary e connection detail.
6. GraphInferenceSearch.
7. Home/painel da nota/tela Insights conectados ao novo grafo.

Antes de implementar, revisar e aprovar este desenho.
