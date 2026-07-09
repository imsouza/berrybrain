# Auditoria e Planning da Home BerryBrain

Data: 2026-07-08

Escopo auditado:
- Frontend: `apps/web/src/components/home/home-view.tsx`, `workspace-context.tsx`, `graph-view.tsx`, `observability-panel.tsx`, `right-panel.tsx`, `settings-panel.tsx`, `types/index.ts`, `globals.css`, `tailwind.config.ts`.
- API: `apps/api/src/berrybrain_api/main.py`, routers `monitor.py`, `graph.py`, `connections.py`, `insights.py`, `settings.py`, services e models.
- Worker: `apps/worker/src/berrybrain_worker/main.py`, `cloud_gateway.py`, `ollama_gateway.py`.
- Banco SQLite: `data/sqlite/berrybrain.db`.
- API local consultada em `http://localhost:8000`.

Limitação operacional:
- O MCP `context-mode` falhou com `Transport closed`; a auditoria seguiu com comandos `rtk` e saídas filtradas.
- Não houve implementação de UI/API neste passo. Este documento é auditoria + plano.

## Resumo Executivo

A Home atual não é mock puro: ela consome `GET /api/v1/home/summary`, e esse endpoint agrega dados reais de notas, conexões, flashcards, revisões, jobs, insights, logs e Worker/Ollama. Porém a implementação é parcial: o resumo não inclui conceitos, grafo, provider cloud/NVIDIA NIM, progresso percentual, jobs ativos detalhados, conclusões recentes, nem seção "precisa de atenção".

O banco e os modelos possuem estruturas para `ConceptRecord`, `ConnectionRecord`, `InsightRecord`, `GraphNodeRecord`, `GraphEdgeRecord`, `EmbeddingRecord`, `FlashcardRecord` e `JobRecord`, mas os dados reais hoje mostram:

- `notes`: 20
- `concepts`: 0
- `connections`: 0
- `graph_nodes`: 0
- `graph_edges`: 0
- `insights`: 0
- `flashcards`: 21
- `jobs`: 153
- `generated_metadata`: 11
- `embeddings`: 2
- `automation_logs`: 148
- `worker_status`: 1

Conclusão: o sistema tem base real de jobs, flashcards, metadados, embeddings, Worker e grafo derivado de notas. Conceitos, conexões, insights, nós persistidos e arestas persistidas ainda não aparecem como conhecimento real extraído no estado atual.

## Auditoria Obrigatória

| Área | Status | Evidência | Problema | Ação |
|---|---|---|---|---|
| Insights | PARCIAL | `InsightRecord` em `apps/api/src/berrybrain_api/models.py:113`; `GET /api/v1/insights` em `routers/insights.py:61`; Home renderiza `s.insights` em `apps/web/src/components/home/home-view.tsx:115`; DB `insights: 0` | Estrutura e endpoint existem, mas não há insights atuais; Home só mostra seção se houver dados e não mostra estado "gerando/sem insights"; tipos são limitados e sem ações sugeridas. | Incluir insights no `home/summary` com estado, related notes, ação sugerida, prioridade e empty/loading states; adicionar geração confiável e cards na Home. |
| Conceitos extraídos | PARCIAL | `ConceptRecord` em `models.py:66`; worker extrai `concepts` para `generated_metadata` em `apps/worker/src/berrybrain_worker/main.py:418`; DB `concepts: 0`; `/api/v1/concepts` retorna 404 | Conceitos extraídos ficam como metadata de assimilação, não são sincronizados para tabela `concepts`; não há endpoint público; Home não mostra conceitos. | Criar serviço e endpoint de conceitos, sincronizar concepts do worker para tabela, computar frequência/notas/confiança e expor no `home/summary`. |
| Conexões | PARCIAL | `ConnectionRecord` em `models.py:79`; `POST /api/v1/connections/sync` em `routers/connections.py:22`; worker chama sync em `main.py:585`; DB `connections: 0`; `/api/v1/connections` sem note path retorna 404 | Modelo e sync existem, mas endpoint é por nota, sem listagem geral/recentes; no estado atual não há conexões criadas; Home só mostra contador. | Criar listagem geral/recentes, status/confirm/ignore, razão/confiança, e incluir 3-5 conexões no `home/summary`. |
| Nós do grafo | PARCIAL | `GraphNodeRecord` em `models.py:172`; `GET /api/v1/graph` em `routers/graph.py:9`; `build_graph` cria nós em memória a partir de notes em `services.py:357`; DB `graph_nodes: 0`; API retorna `nodes: 20` | Grafo exibido é derivado dinamicamente de notas, não necessariamente persistido; sem conceitos no grafo; Home não tem resumo do grafo. | Expor `graphSummary` no `home/summary`; decidir se Home usa grafo derivado ou persistido; rodar/schedule `POST /api/v1/graph/sync` quando conexões/conceitos mudarem. |
| Correlações | FALTA | Nenhum modelo/endpoint de `correlation`; conexões semantic/prerequisite/etc existem em `routers/connections.py:37` | Correlação como conceito de produto não existe separada de Connection; Home não diferencia correlação, sugestão, backlink, contraste ou duplicidade validada. | Tratar correlação como tipo de connection ou criar campo `type/status`; incluir motivo/confiança/status e ação de confirmar/ignorar. |
| Estatísticas da Home | PARCIAL | `home_summary` em `main.py:133`; Home usa `stats.notes/connections/flashcards/pendingReviews/pendingJobs/runningJobs` em `home-view.tsx:105` | Dados são reais, mas básicos; faltam criadas hoje, não assimiladas, conceitos, novas conexões, confiança média, provider, tempo médio, últimas chamadas. | Expandir `stats` no `home/summary` e trocar cards soltos por cards explicativos. |
| Estatísticas da IA | PARCIAL | `monitor/stats` conta `metadata`, `embeddings` em `routers/monitor.py:42`; worker loga chamada IA em `main.py:270`; settings expõem AI config em `routers/settings.py:28`; endpoints `/provider/status` e `/provider/nim/status` retornam 404 | Há metadados/embeddings/logs e config cloud, mas não há status NVIDIA NIM dedicado, latência média, chamada atual, provider lento/timeout para Home. | Adicionar provider status agregado no `home/summary`, usando settings + logs/jobs; opcional criar `/api/v1/provider/status`. |
| Jobs/progresso | PARCIAL | `JobRecord` em `models.py:31`; `GET /api/v1/jobs` em `routers/jobs.py`; `monitor/stats` retorna `running_jobs`, `recent_completions`, `jobs.per_hour` em `monitor.py:48`; Home mostra processados/erros/pendentes/ativos em `home-view.tsx:137` | Jobs são reais, mas Home não calcula progresso percentual, etapa atual, tempo decorrido, jobs por tipo, active jobs detalhados, nem barra. | Criar `progress` no `home/summary`; calcular `completed/(completed+running+pending+failed)`; expor `activeJobs`, `jobsByType`, `recentlyCompleted`, `needsAttention`. |
| Atividade recente | PARCIAL | `AutomationLogRecord` em `models.py:126`; `automation-logs` em `observability-panel.tsx:44`; Home usa `autopilot.activity` de logs em `main.py:196` | É real, mas muito técnica: "Criou job X para NOTE_CREATED"; Home não traduz para linguagem de usuário. | Mapear ações técnicas para mensagens humanas no service agregado; manter log bruto só no Monitor. |
| Status Worker | OK | `WorkerStatus` em `models.py:46`; heartbeat em `monitor.py:90`; status em `monitor.py:117`; Home mostra `s.autopilot.worker` em `home-view.tsx:53`; API retorna worker running | Funcional, mas sem cálculo de offline por heartbeat stale; Home não mostra último processamento. | Incluir `lastHeartbeat`, `lastProcessedAt` e regra de stale/offline no summary. |
| Status Ollama | OK/PARCIAL | Worker checa health em `apps/worker/src/berrybrain_worker/ollama_gateway.py:10`; heartbeat grava `ollama_healthy` em `monitor.py:103`; Home mostra online/offline em `home-view.tsx:57` | Funcional para booleano, mas sem razão/latência/última checagem. | Manter booleano no header e incluir timestamp/diagnóstico opcional no `status`. |
| Status NVIDIA NIM | PARCIAL | Gateway cloud OpenAI-compatible em `apps/worker/src/berrybrain_worker/cloud_gateway.py:8`; worker escolhe provider cloud em `main.py:222`; settings AI config em `routers/settings.py:28`; `/api/v1/provider/nim/status` retorna 404 | Cloud/NIM pode processar, mas Home não sabe se NIM está online/processando/lento/timeout; não há endpoint/status persistido. | Expor provider/model/status no `home/summary`; registrar duração/erro por chamada; derivar `running`, `slow`, `timeout`. |
| Progresso de processamento | FALTA | Home mostra pendentes/ativos em `home-view.tsx:61` e Autopilot em `home-view.tsx:137`; não há `progress.percent` em API | Não existe barra nem percentual; usuário vê fila sem saber avanço. | Criar `progress` determinate/indeterminate e componente `ThemedProgressBar`. |
| Flashcards | OK/PARCIAL | `FlashcardRecord` em `models.py:94`; Review usa `/api/v1/review/today` em `review-view.tsx:27`; worker persiste flashcards em `main.py:616`; DB `flashcards: 21` | Funcional, mas Home só mostra contagem; não mostra criados recentemente nem contexto de nota. | Incluir flashcards criados recentemente e revisão pendente/vencida nos cards de Home. |
| Revisões | OK/PARCIAL | `review/today` em frontend `review-view.tsx:27`; Home card "Revisar hoje" usa `w.reviewCount` em `home-view.tsx:98` | Funcional básico; Home não separa dueToday/vencidas/estado vazio com boa mensagem. | Expandir `stats.reviews` e manter card "Revisar hoje" com detalhes. |

## Endpoints Verificados

Existem e responderam `200`:
- `GET /api/v1/home/summary`
- `GET /api/v1/monitor/stats`
- `GET /api/v1/insights?limit=5`
- `GET /api/v1/graph`
- `GET /api/v1/jobs?limit=8`
- `GET /api/v1/automation-logs?limit=5`
- `GET /api/v1/worker/status`
- `GET /api/v1/review/today?limit=5`
- `GET /api/v1/settings/ai/config`

Ausentes ou inadequados para Home:
- `GET /api/v1/provider/status`: 404
- `GET /api/v1/provider/nim/status`: 404
- `GET /api/v1/concepts`: 404
- `GET /api/v1/activity`: 404
- `GET /api/v1/autopilot`: 404
- `GET /api/v1/connections`: não é listagem geral; rota atual exige `/{note_path:path}` e sem path retorna "Note not found".

## Achados Técnicos Relevantes

1. `home/summary` é real, mas estreito.
   - Evidência: `apps/api/src/berrybrain_api/main.py:133`.
   - Falta incluir `status`, `progress`, `activeJobs`, `recentlyCompleted`, `detectedConcepts`, `recentConnections`, `graphSummary`, `needsAttention`.

2. Home usa `Summary = any`.
   - Evidência: `apps/web/src/components/home/home-view.tsx:6`.
   - Isso esconde quebra de contrato e facilita números ausentes ou formatos divergentes.

3. API tem conceitos modelados, mas sem fluxo de persistência.
   - Worker salva conceitos como `generated_metadata` (`main.py:418`), não em `ConceptRecord`.
   - Banco atual tem `concepts: 0`.

4. Grafo da tela é derivado de notas/connections, não dos registros `graph_nodes/graph_edges`.
   - `build_graph` lê `NoteRecord` e `ConnectionRecord` diretamente (`services.py:357`).
   - Banco atual tem `graph_nodes: 0`, `graph_edges: 0`, mas `GET /graph` retorna 20 nós e 0 arestas.

5. Conexões reais dependem do worker gerar payload com target path válido.
   - `FIND_CONNECTIONS` chama `/api/v1/connections/sync` (`worker/main.py:585`).
   - Banco atual tem `connections: 0`; Home mostra contador 0 sem explicar estado.

6. O worker tem cloud provider funcional, mas o produto não expõe status de NIM.
   - Cloud gateway: `cloud_gateway.py:8`.
   - Seleção cloud: `worker/main.py:222`.
   - Settings AI config: `routers/settings.py:28`.

7. O Monitor já tem dados que deveriam abastecer a Home melhorada.
   - `running_jobs`, `recent_completions`, `job_types`, `embeddings`, `per_hour`: `routers/monitor.py:41`.
   - Home atual não usa esses campos.

8. Há hardcoded visual/estatístico no Monitor.
   - Frontend mostra `Embeddings` como `0` em `observability-panel.tsx:272`, mesmo API retornando `embeddings: 2`.
   - Frontend mostra `Por hora` como `10` em `observability-panel.tsx:283`, embora API retorne `jobs.per_hour`.

## Objetivo da Nova Home

A Home deve virar mesa de estudos inteligente e centro de controle do segundo cérebro. Ela deve responder:

1. O sistema está funcionando?
2. O que está sendo processado agora?
3. Quanto já foi concluído?
4. O que a IA já descobriu?
5. Quais insights foram gerados?
6. Quais conceitos foram extraídos?
7. Quais conexões/correlações surgiram?
8. O grafo está atualizado?
9. O que revisar hoje?
10. O que precisa de atenção?

## Contrato Proposto para `GET /api/v1/home/summary`

Campos obrigatórios:

- `status`
  - `worker`, `workerLastHeartbeat`, `ollama`, `cloudProvider`, `cloudModel`, `cloudStatus`, `pendingJobs`, `activeJobs`, `lastProcessingAt`.
- `progress`
  - `mode`, `percent`, `active`, `pending`, `completed`, `failed`, `currentStep`, `lastResult`.
- `stats`
  - `notes`, `connections`, `concepts`, `flashcards`, `reviews`, `jobs`, `ai`.
- `activeJobs`
  - `id`, `type`, `label`, `notePath`, `noteTitle`, `provider`, `startedAt`, `elapsedSeconds`, `progress`.
- `recentlyCompleted`
  - resultados em linguagem humana, não logs brutos.
- `recentActivity`
  - eventos recentes traduzidos.
- `recentInsights`
  - `type`, `title`, `description`, `priority`, `relatedNotes`, `suggestedAction`.
- `detectedConcepts`
  - `id`, `name`, `frequency`, `relatedNotesCount`, `trend`, `hasPermanentNote`, `confidence`.
- `recentConnections`
  - `id`, `source`, `target`, `type`, `confidence`, `reason`, `status`.
- `graphSummary`
  - `nodes`, `edges`, `orphans`, `clusters`, `centralNotes`, `updatedAt`.
- `needsAttention`
  - `kind`, `title`, `description`, `action`.

Regra de progresso:

```text
total = completed + active + pending + failed
percent = total > 0 ? round(completed / total * 100) : 100
```

Para o estado atual do banco auditado:

```text
completed=26, active=8, pending=100, failed=19
total=153
percent=17
```

Se `completed` confiável não estiver disponível no agregado, usar modo `indeterminate`.

## Planning de Melhoria

### Fase 1 - API Home Summary Real

Objetivo: transformar `home/summary` no endpoint único da Home.

Arquivos:
- Modificar `apps/api/src/berrybrain_api/main.py`.
- Possível extrair para `apps/api/src/berrybrain_api/home_summary.py` se a função passar de 150 linhas.
- Reusar `models.py`, `jobs.py`, `services.py`, `settings_store.py`.

Tarefas:
1. Criar tipos/serializadores internos para `status`, `progress`, `stats`, `activeJobs`, `recentlyCompleted`, `recentActivity`, `graphSummary`, `needsAttention`.
2. Agregar `WorkerStatus`, `JobRecord`, `AutomationLogRecord`, `NoteRecord`, `FlashcardRecord`, `InsightRecord`, `ConnectionRecord`, `ConceptRecord`, `EmbeddingRecord`, `GeneratedMetadataRecord`.
3. Buscar AI config de settings (`ai_provider`, `ai_api_url`, `ai_model`) e expor provider/model sem vazar API key.
4. Calcular progresso com `completed + running + pending + failed`.
5. Derivar `currentStep` pelo job ativo mais antigo ou pela maior fila por tipo.
6. Traduzir tipos técnicos de jobs para labels humanos:
   - `PARSE_NOTE`: "Analisando nota"
   - `CLASSIFY_NOTE`: "Classificando nota"
   - `ASSIMILATE_NOTE`: "Assimilando conceitos"
   - `GENERATE_EMBEDDING`: "Gerando embeddings"
   - `FIND_CONNECTIONS`: "Buscando conexões"
   - `GENERATE_FLASHCARDS`: "Criando flashcards"
   - `GENERATE_INSIGHTS`: "Gerando insights"
7. Incluir `needsAttention` para worker offline/stale, Ollama offline, failed jobs, NIM lento/timeout inferido, notas não assimiladas, insights pendentes.
8. Testar com `apps/api/tests/test_home_summary.py`.

### Fase 2 - Conceitos Reais

Objetivo: fazer conceitos aparecerem como entidade consultável, não só metadata.

Arquivos:
- Modificar `apps/api/src/berrybrain_api/models.py` se precisar campos novos.
- Criar/alterar serviço em `apps/api/src/berrybrain_api/services.py`.
- Criar `apps/api/src/berrybrain_api/routers/concepts.py`.
- Modificar `apps/worker/src/berrybrain_worker/main.py`.

Tarefas:
1. Expandir `ConceptRecord` ou criar tabela auxiliar para note-concept:
   - `frequency`, `related_note_ids` ou tabela relacional, `updated_at`, `extracted_by`, `confidence`.
2. Criar `upsert_concepts_from_note(note_id, concepts, extracted_by, confidence)`.
3. No `ASSIMILATE_NOTE`, após salvar metadata `concepts`, chamar endpoint/serviço de sync de conceitos.
4. Criar `GET /api/v1/concepts?limit=...`.
5. Incluir top conceitos no `home/summary`.
6. Testar deduplicação por `normalized_name`.

### Fase 3 - Conexões e Correlações Recentes

Objetivo: exibir conexões reais com motivo, confiança e ação.

Arquivos:
- Modificar `apps/api/src/berrybrain_api/routers/connections.py`.
- Modificar `apps/api/src/berrybrain_api/models.py` se incluir `status`.
- Modificar `apps/api/src/berrybrain_api/services.py`.

Tarefas:
1. Adicionar `GET /api/v1/connections?limit=5&status=active`.
2. Incluir `status` em conexão: `suggested`, `confirmed`, `ignored` ou manter default `confirmed` para conexões AI atuais se migração simples.
3. Adicionar endpoints `POST /api/v1/connections/{id}/confirm` e `/ignore`.
4. Criar serializer com `source_note`, `target_note`, `type`, `confidence`, `reason`, `created_by`, `created_at`.
5. Incluir recentes no `home/summary`.
6. Testar listagem sem `note_path`.

### Fase 4 - Grafo Resumido na Home

Objetivo: mostrar saúde do conhecimento sem prender o grafo completo em card pesado.

Arquivos:
- Modificar `apps/api/src/berrybrain_api/services.py`.
- Modificar `apps/api/src/berrybrain_api/main.py`.
- Reusar `apps/web/src/components/graph-screen.tsx` sem embutir canvas pesado na Home.

Tarefas:
1. Criar `get_graph_summary(session)`.
2. Retornar `nodes`, `edges`, `orphans`, `clusters`, `centralNotes`, `updatedAt`.
3. Usar `build_graph` para dados reais atuais e preparar migração para `GraphNodeRecord/GraphEdgeRecord`.
4. Expor botões: abrir grafo, ver órfãs, recalcular conexões.

### Fase 5 - Frontend Home Nova

Objetivo: reorganizar a Home em blocos claros e transparentes.

Arquivos:
- Modificar `apps/web/src/components/home/home-view.tsx`.
- Criar componentes em `apps/web/src/components/home/`:
  - `home-header.tsx`
  - `system-status-row.tsx`
  - `themed-progress-bar.tsx`
  - `autopilot-progress-card.tsx`
  - `review-today-card.tsx`
  - `stats-grid.tsx`
  - `insights-preview.tsx`
  - `concepts-preview.tsx`
  - `recent-connections-list.tsx`
  - `graph-summary-card.tsx`
  - `active-jobs-panel.tsx`
  - `recent-activity-timeline.tsx`
  - `needs-attention-card.tsx`
  - `quick-actions.tsx`
  - `provider-status-badge.tsx`
- Atualizar `apps/web/src/types/index.ts`.

Layout:
1. Header de status.
2. Editor-first.
3. Autopilot progress.
4. Grid duas colunas:
   - Esquerda: Revisar hoje, Insights da IA, Conceitos detectados.
   - Direita: Processando agora, Grafo de conhecimento, Precisa de atenção.
5. Estatísticas.
6. Conexões recentes.
7. Atividade recente.
8. Ações rápidas.

Estados obrigatórios:
- Loading: "Carregando resumo do BerryBrain..."
- Sem notas: "Comece escrevendo sua primeira nota."
- Sem insights: "Nenhum insight ainda. Continue escrevendo para detectar padrões."
- Sem conexões: "Nenhuma conexão encontrada ainda. O Autopilot criará relações conforme assimilar suas notas."
- Processando: mostrar progress bar e jobs ativos.
- Erro: "Não foi possível carregar a Home." + tentar novamente.
- Provider lento: "NVIDIA NIM está demorando mais que o normal. Os jobs continuam na fila."
- Tudo pronto: "Tudo pronto. Seu segundo cérebro está atualizado."

### Fase 6 - Barra de Progresso com Tema

Objetivo: componente reutilizável e consistente com Settings.

Arquivos:
- Criar `apps/web/src/components/home/themed-progress-bar.tsx`.
- Modificar `apps/web/src/app/globals.css`.
- Modificar `apps/web/tailwind.config.ts` se necessário.
- Modificar `apps/web/src/components/settings-panel.tsx` para setar muted/success/warning/danger se necessário.

Tokens:
- Já existe `--color-accent` em `globals.css:11`.
- Já existe `--color-accent-soft` em `globals.css:12`.
- Faltam tokens explícitos `--color-success`, `--color-warning`, `--color-danger`.

Implementação visual:
- Track: `var(--color-accent-soft)` ou `var(--color-border)`.
- Fill running: `var(--color-accent)`.
- Fill completed: `var(--color-success)`.
- Fill failed: `var(--color-danger)`.
- Fill waiting provider: `var(--color-warning)`.
- Indeterminate: animação discreta.

### Fase 7 - Monitor e Painel Direito

Objetivo: não deixar Home carregar logs técnicos, mas manter drill-down.

Arquivos:
- Modificar `apps/web/src/components/observability-panel.tsx`.
- Modificar `apps/web/src/components/panel/right-panel.tsx`.

Tarefas:
1. Trocar hardcoded `Embeddings=0` por `stats.embeddings`.
2. Trocar hardcoded `Por hora=10` por `stats.jobs?.per_hour`.
3. No painel direito da nota, mostrar insights/conexões relacionados à nota aberta quando existirem.
4. Manter logs técnicos no Monitor, e Home com linguagem humana.

## Critérios de Pronto

- Auditoria inicial feita e registrada neste arquivo.
- `GET /api/v1/home/summary` expõe dados reais agregados.
- Home mostra header com Worker/Ollama/NVIDIA NIM/modelo/fila/último processamento.
- Home mostra barra de progresso real ou indeterminada.
- Barra usa tokens de tema e reage ao accent configurado em Settings.
- Home mostra insights, conceitos, conexões/correlações, grafo resumido, jobs ativos, pronto recentemente e precisa de atenção.
- Dados finais não usam números hardcoded.
- Logs técnicos ficam no Monitor.
- Estados loading/empty/error/offline/provider lento/tudo pronto implementados.
- Testes cobrem o service de summary e componentes principais.

## Ordem Recomendada

1. API `home/summary` expandida + testes.
2. Frontend `ThemedProgressBar` + `AutopilotProgressCard`.
3. Home reorganizada usando dados reais já disponíveis.
4. Concepts endpoint/sync.
5. Connections list/actions.
6. Graph summary.
7. Monitor/right panel polish.

Essa ordem entrega transparência rapidamente sem bloquear em conceitos/conexões, que hoje estão vazios no banco.
