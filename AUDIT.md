# Auditoria Funcional do BerryBrain

Data: 2026-07-07

## Resumo Executivo

- Status geral: PARCIAL, não funcional como segundo cérebro completo.
- Percentual estimado de implementação real: 35%.
- O segundo cérebro funciona de ponta a ponta? Parcial. Editor/vault/jobs existem, mas IA, revisão, insights, embeddings, conexões e grafo semântico não fecham o ciclo.
- Grafo funciona de verdade? Parcial. Mostra nós reais de notas, mas sem arestas/conexões reais no estado atual.
- Estatísticas são reais? Parcial. Contagens básicas vêm do banco; estatísticas avançadas e gráficos não existem.
- Gráficos são reais? Não.
- Insights da IA funcionam? Não no estado atual. Endpoint existe, mas retorna vazio.
- Revisão funciona? Parcial em infraestrutura. Tela e endpoints existem, mas não há flashcards gerados.
- Autopilot funciona? Parcial. Cria jobs e worker processa alguns, mas pipeline fica pendente/rodando e não entrega assimilação completa.
- Maior risco técnico: jobs e worker não garantem conclusão do pipeline; há job preso em `running` e backlog pendente.
- Maior risco de UX: fluxo ainda não é editor-first completo; API exige título, título automático é job separado e não confiável.
- Prioridade máxima: tornar o pipeline Autopilot idempotente, recuperável e capaz de processar nota até metadata/embeddings/conexões/revisão.

## Evidências Executadas

### Ambiente

- `docker compose ps`: API healthy em `8000`; web ativo em `3000`.
- `GET /health`: `{"status":"ok"}`.
- `GET /api/v1/status`: `{"notes":2,"vault_path":"/app/vault"}`.
- `HEAD http://127.0.0.1:3000`: `HTTP/1.1 200 OK`.

### Testes Automatizados

- `python -m unittest discover -s /app/apps/api/tests`: falha.
- Falha: `apps/api/tests/test_integration.py` importa `fastapi.testclient`, mas `starlette.testclient` exige pacote `httpx2`.
- Resultado observado: `Ran 21 tests`, `FAILED (errors=1)`.
- Conclusão: suíte completa não passa no ambiente atual.

### Home / Monitor

- `GET /api/v1/home/summary` retornou:
  - `notes: 2`
  - `connections: 0`
  - `flashcards: 0`
  - `pendingReviews: 0`
  - `pendingJobs: 18`
  - `worker: offline`
  - `ollama: false`
  - `insights: []`
- `GET /api/v1/monitor/stats` depois do worker:
  - `metadata: 1`, depois `metadata: 2`
  - `embeddings: 0`
  - `connections: 0`
  - `flashcards: 0`
  - `insights: 0`
  - `jobs.total: 24`
  - `completed: 1`
  - `pending: 22`

### Fluxo de Nota Testado

Criação via API:

- `POST /api/v1/notes` com título `"Auditoria Edge Computing <timestamp>"`.
- Resultado: `201`, arquivo `inbox/auditoria-edge-computing-1783448524572.md`.
- Update via `PUT /api/v1/notes/{path}` salvou conteúdo e detectou link `[[Observabilidade]]`.
- Read via `GET /api/v1/notes/{path}` retornou conteúdo salvo.
- Jobs criados: `PARSE_NOTE`, `CLASSIFY_NOTE`, `ASSIMILATE_NOTE`, `GENERATE_EMBEDDING`, `FIND_CONNECTIONS`, `GENERATE_FLASHCARDS`.

Criação sem título:

- `POST /api/v1/notes` sem `title`: `422 Field required`.
- `POST /api/v1/notes` com `title: ""`: `422 String should have at least 1 character`.
- Conclusão: requisito "usuário não precisa digitar nome" não está atendido na API.

Worker:

- `docker compose run --rm worker` com timeout de 35s.
- Efeito observado:
  - completou `PARSE_NOTE`;
  - criou metadata `parse`;
  - criou metadata `classification`;
  - deixou job `ASSIMILATE_NOTE` em `running`.
- `GET /api/v1/worker/status`: reportou `jobs_processed:1`, `errors:0`, `ollama_healthy:true`.
- Problema: job em `running` ficou preso após interrupção do worker.

## Auditoria Geral do Projeto

| Área | Status | Evidência | Problema | Prioridade |
|---|---|---|---|---|
| Estrutura de pastas | PARCIAL | `apps/api`, `apps/web`, `apps/worker`, `packages`, `prompts`, `vault` | `packages/domain/application/infrastructure` são praticamente placeholders; regras reais estão em API/worker | Média |
| Arquitetura | PARCIAL | `apps/api/src/berrybrain_api/services.py`, routers e worker | Clean Architecture não está realmente aplicada; muitos casos de uso estão em `services.py` e worker | Média |
| Frontend | PARCIAL | `apps/web/src/components/*` | UI tem Home/editor/grafo/revisão/settings, mas várias seções dependem de dados vazios/parciais | Alta |
| Backend | PARCIAL | `apps/api/src/berrybrain_api/main.py`, routers | Endpoints existem, mas vários fluxos não fecham resultado final | Alta |
| Worker | PARCIAL | `apps/worker/src/berrybrain_worker/main.py` | Loop existe, mas jobs podem ficar presos em `running`; processamento completo não validado | Alta |
| Ollama | PARCIAL | `apps/worker/src/berrybrain_worker/ollama_gateway.py` | Gateway existe; pipeline real não completou assimilação/embedding/flashcards no teste | Alta |
| Banco | PARCIAL | `apps/api/src/berrybrain_api/models.py` | Tabelas existem; várias permanecem zeradas | Alta |
| Vault Markdown | OK/PARCIAL | `vault/inbox/*.md`, `vault.py` | Markdown real funciona; renomeação automática por conteúdo não funciona de ponta a ponta | Alta |
| Job Engine | PARCIAL | `jobs.py` | Cria pipeline, muda status, tem retry; recuperação de `running` morto ausente | Alta |
| APIs | PARCIAL | routers em `apps/api/src/berrybrain_api/routers` | Muitas APIs retornam vazio; algumas não refletem resultado gerado real | Média |
| Logs | PARCIAL | `automation_logs.py`, Home activity | Logs registram enfileiramento, mas logs de IA/erro não estão completos na UI | Média |
| Loading/empty/offline | PARCIAL | `home-view.tsx`, `graph-view.tsx`, `review-view.tsx` | Existem alguns estados, mas não cobrem todos os fluxos | Média |

## Fluxo Principal do Segundo Cérebro

| Passo | Status | Evidência | Problema |
|---|---|---|---|
| Abrir aplicação | OK | `HEAD :3000` retorna `200 OK` | Sem validação visual via navegador real nesta auditoria |
| Criar nota sem nome manual | PARCIAL/FALTA | `createDraft()` em `workspace-context.tsx:93-98` cria `"Nota sem titulo"`; API exige `title` em `routers/notes.py:22-25` | Não é criação livre baseada em escrita; API rejeita ausência de título |
| Escrever no editor | PARCIAL | `note-editor.tsx:74-78` textarea com placeholder | Só funciona após draft criado |
| Autosave | PARCIAL | `workspace-context.tsx:141-145` salva após 3s | Só após nota ativa existir; não cria automaticamente ao digitar em Home |
| Salvar Markdown no vault | OK | arquivo real em `vault/inbox/*.md`; `vault.py` usa `write_text` | OK para CRUD básico |
| Nome automático por conteúdo | FALTA/PARCIAL | `aiRename()` cria job em `workspace-context.tsx:129-135`; worker `process_generate_note_title()` | Não é automático confiável; não foi processado no teste; API exige título inicial |
| Slug seguro | PARCIAL | `slugify_title()` em `vault.py:27` | Remove acentos; duplicidade vira erro em vez de sufixo incremental |
| Jobs automáticos | OK/PARCIAL | `enqueue_note_changed_jobs()` cria pipeline; fila mostrou jobs | Criação OK; execução completa não |
| Autopilot processa nota | PARCIAL | Worker completou parse/classification, parou em assimilation running | Pipeline não chegou ao fim |
| Conceitos/tags/resumo | PARCIAL | metadata `classification` gerou tags; `summary/concepts` ausentes | Assimilação não concluída |
| Embeddings | FALTA | `EmbeddingRecord` count `0` | Nenhum embedding persistido |
| Conexões | FALTA | `connections:0`; `graph.edges:[]` | Sem conexões reais |
| Flashcards/revisão | FALTA | `/review/today` retorna `[]` | Sem flashcards gerados |
| Insights | FALTA | `/insights` retorna `[]` | Sem insights gerados |
| Home atualiza | PARCIAL | `/home/summary` mostra contagens reais | Mostra muitos zeros/backlog |
| Grafo atualiza | PARCIAL | `/graph` mostra 2 nós | Sem arestas, clusters, semântica |
| Estatísticas/gráficos | PARCIAL/FALTA | `/monitor/stats` contagens simples | Gráficos não existem |

Conclusão do fluxo: não funciona 100%. Funciona parcialmente como editor/vault/job queue; não funciona como segundo cérebro completo.

## Notas Markdown e Vault

| Item | Status | Evidência | Problema |
|---|---|---|---|
| Markdown real | OK | `vault/inbox/nota-sem-titulo.md`, `vault/inbox/test.md` | OK |
| Vault correto | OK | `/api/v1/status` mostra `/app/vault`; Docker mapeia workspace | OK |
| Frontmatter | PARCIAL | `parse_frontmatter()` em `vault.py`; metadata parse | Lê frontmatter; não há fluxo forte para salvar/atualizar frontmatter automático |
| Conteúdo preservado | OK | `PUT` e `GET` testados com conteúdo de auditoria | OK |
| Autosave | PARCIAL | `workspace-context.tsx:141-145` | Não cria nota automaticamente no primeiro caractere |
| Renomear nota | PARCIAL | `routers/notes.py:62-70`, `rename_note()` | Não atualiza backlinks; não foi integrado automaticamente |
| Slug | PARCIAL | `slugify_title()` | Sem sufixo incremental em duplicidade |
| Duplicidade | PARCIAL | `create_note()` retorna conflito se arquivo existe | Não gera alternativa |
| Nota manual + scan | OK/PARCIAL | `vault_scan.py`; endpoint `/api/v1/vault/scan` | Scan funciona; watcher pode duplicar jobs por eventos/hash se backlog não processa |
| Watcher | PARCIAL | `vault_watcher.py` | Polling existe; recuperação de jobs travados não |
| Nome automático | FALTA/PARCIAL | `GENERATE_NOTE_TITLE` job | Não fecha fluxo no teste |

## Autopilot e Job Engine

Jobs esperados versus estado:

| Job | Status | Criado? | Processado? | Resultado salvo? | Problema |
|---|---|---|---|---|---|
| PARSE_NOTE | PARCIAL | Sim | Sim para alguns | Sim em generated metadata | OK parcial |
| CLASSIFY_NOTE | PARCIAL | Sim | Sim para um caso | Sim em metadata | Depende de Ollama; não integrado a tags reais |
| GENERATE_NOTE_TITLE | PARCIAL/FALTA | Só via `aiRename()` UI | Não validado | Não validado | Não é parte padrão do pipeline de nota criada |
| GENERATE_EMBEDDING | FALTA/PARCIAL | Sim | Não no teste | Não | `EmbeddingRecord` count `0` |
| ASSIMILATE_NOTE | QUEBRADO/PARCIAL | Sim | Ficou `running` | Não | Job preso após worker interrompido |
| FIND_CONNECTIONS | FALTA/PARCIAL | Sim | Não | Não | Sem conexões salvas |
| GENERATE_FLASHCARDS | FALTA/PARCIAL | Sim | Não | Não | Flashcards count `0` |
| SCHEDULE_REVIEW | FALTA | Não observado | Não | Não | Não está no pipeline observado |
| GENERATE_INSIGHTS | PARCIAL/FALTA | Implementado no worker, não no pipeline de nota | Não | Não | Insights `[]` |
| UPDATE_GRAPH | FALTA | Não observado | Não | Não | Grafo precisa sync manual/API |
| ORGANIZE_INBOX | FALTA | Não observado | Não | Não | Não implementado funcionalmente |

Problemas críticos:

- `claim_next_job()` seleciona `pending`, mas não há mecanismo de expirar `running` órfão.
- Worker infinito foi morto por timeout e deixou `ASSIMILATE_NOTE` em `running`.
- UI lista jobs, mas isso não significa Autopilot concluído.
- Backlog atual: 24 jobs totais, 22 pendentes, 1 running, 1+ completados no momento auditado.

## IA Local / Ollama

| Item | Status | Evidência | Problema |
|---|---|---|---|
| Frontend não chama Ollama direto | OK | busca no frontend só chama API (`workspace-context.tsx`, componentes) | OK |
| Worker chama Ollama | PARCIAL | `ollama_gateway.py`, `main.py:154-191` | Gateway existe |
| URL/modelos configurados | OK/PARCIAL | `WorkerSettings` contém `ollama_base_url`, `main_model`, `fast_model`, `embedding_model` | Config existe |
| Health Ollama | PARCIAL | `/worker/status` reportou `ollama_healthy:true` | Não garante processamento completo |
| Logs de IA | PARCIAL | `log_ai_call()` existe em `ollama_gateway.py` | Não auditado na UI; metadata só classificação |
| Fallback offline | PARCIAL/FALTA | `process_generate_note_title()` tem fallback determinístico; `ollama_call()` relança `OllamaError` | Classify/assimilate/flashcards falham sem IA; só título tem fallback |
| Resposta inválida IA | PARCIAL | `json.loads` direto em worker | Pode quebrar job; retry existe, mas sem reparo |
| Cloud externa | OK aparente | Sem indícios de API externa; usa Ollama local | OK aparente |

## Geração Automática de Título

Testes exigidos:

| Texto | Status | Evidência | Problema |
|---|---|---|---|
| Edge computing | FALTA/PARCIAL | API exige título; worker title job não processado no fluxo testado | Não gerou “Edge Computing e Processamento na Borda” |
| Observabilidade | FALTA/PARCIAL | Não há execução automática comprovada | Não gerou “Observabilidade em Sistemas Distribuídos” |

Regras:

- H1 como título: parcial em `process_generate_note_title()` e `sync.title_from_markdown()`.
- IA local se sem H1: parcial em worker, não garantido.
- Fallback offline: parcial no título.
- Conteúdo curto mantém temporário: parcial (`default_title = "Rascunho"` / `"Nota sem titulo"`).
- Usuário travar título manual: falta.
- Renomear arquivo com slug seguro: parcial.
- Duplicidade com sufixo incremental: falta.
- Atualizar backlinks ao renomear: falta.

## Grafo de Conhecimento

Endpoint auditado:

`GET /api/v1/graph`:

```json
{
  "nodes": [
    {"id":"note_1","label":"Nota Sem Titulo","type":"note","path":"inbox/nota-sem-titulo.md"},
    {"id":"note_2","label":"Test","type":"note","path":"inbox/test.md"}
  ],
  "edges": [],
  "stats": {"node_count":2,"edge_count":0,"orphan_count":2,"central_nodes":[]}
}
```

| Recurso do Grafo | Status | Evidência | Problema |
|---|---|---|---|
| Nós reais | OK/PARCIAL | `/api/v1/graph` retorna notas reais | OK para nós |
| Arestas reais | FALTA | `edges: []` | Sem links/conexões reais |
| Backlinks | FALTA/PARCIAL | links parseados em metadata, mas não viraram arestas | Não aparece no grafo |
| Conexões semânticas | FALTA | `connections:0` | Embeddings/conexões ausentes |
| Conceitos | FALTA | graph nodes só notas | Conceitos não aparecem |
| Clusters | FALTA | Sem algoritmo/estado visível | Não implementado |
| Órfãs | PARCIAL | `orphan_count:2` | Apenas por ausência de arestas |
| Filtros | PARCIAL/FALTA | UI legendas, mas sem filtros funcionais completos auditados | Não atende requisitos |
| Clique para abrir nota | PARCIAL | `GraphScreen` chama `onNavigate` | Só se nó tiver path |

## Estatísticas

| Estatística | Status | Fonte dos dados | Atualiza? | Problema |
|---|---|---|---|---|
| total de notas | OK | `/home/summary`, `/monitor/stats` | Sim | OK |
| notas criadas hoje | FALTA | Não encontrado | Não | Ausente |
| notas editadas recentemente | PARCIAL | `recentNotes` | Parcial | Não é métrica completa |
| notas não assimiladas | FALTA | Não encontrado | Não | Ausente |
| notas órfãs | PARCIAL | `/graph.stats.orphan_count` | Parcial | Depende de grafo incompleto |
| notas sem tags | FALTA | Não encontrado | Não | Ausente |
| duplicadas | FALTA | Não encontrado | Não | Ausente |
| total palavras | PARCIAL | metadata parse tem `word_count` para notas processadas | Parcial | Não agregado |
| conceitos | FALTA/PARCIAL | metadata/classification parcial | Não | Não agregado |
| links/backlinks | PARCIAL/FALTA | parse links existe | Não completo | Não agregado |
| conexões semânticas | FALTA | `connections:0` | Não | Ausente |
| flashcards/revisões | PARCIAL/FALTA | contagens existem | Sim, mas zero | Sem geração real |
| jobs pendentes/ativos/concluídos | OK/PARCIAL | `/monitor/stats` | Sim | Bom para job técnico |
| modelo usado por tarefa | PARCIAL | generated metadata tem `model_used` | Parcial | Não exposto como estatística completa |
| tempo médio processamento | FALTA | Não encontrado | Não | Ausente |

## Gráficos

| Gráfico | Status | Dados reais? | Arquivo | Problema |
|---|---|---|---|---|
| Notas 7 dias | FALTA | Não | Não encontrado | Ausente |
| Conexões 7 dias | FALTA | Não | Não encontrado | Ausente |
| Revisões pendentes/dia | FALTA | Não | Não encontrado | Ausente |
| Atividade Autopilot | FALTA/PARCIAL | Lista, não gráfico | `home-view.tsx`, `observability-panel.tsx` | Sem gráfico |
| Tags mais usadas | FALTA | Não | Não encontrado | Ausente |
| Heatmap atividade | FALTA | Não | Não encontrado | Ausente |
| Uso por modelo IA | FALTA | Não | Não encontrado | Ausente |
| Erros por job | FALTA/PARCIAL | Contagem técnica existe | `monitor/stats` | Sem gráfico |

Biblioteca de gráficos: nenhuma evidência de Recharts/Chart.js/ECharts/D3 em uso.

## Insights da IA

| Insight | Status | Gerado por IA? | Ação funciona? | Problema |
|---|---|---|---|---|
| lacuna conhecimento | FALTA | Não observado | Não | `/insights` retorna `[]` |
| nota fraca | FALTA | Não | Não | Ausente |
| nota isolada | FALTA/PARCIAL | Não | Não | Grafo mostra órfãs, mas não insight |
| conceito recorrente | FALTA | Não | Não | Ausente |
| conexão sugerida | FALTA | Não | Não | Ausente |
| duplicidade | FALTA | Não | Não | Ausente |
| trilha estudo | FALTA | Não | Não | Ausente |
| ignorar insight | PARCIAL | endpoint existe | Não testado com dado real | Sem insights reais |

## Flashcards e Revisão

| Recurso | Status | Evidência | Problema |
|---|---|---|---|
| Flashcards | FALTA/PARCIAL | `/review/today` retorna `[]`; tabela count `0` | Worker gera metadata `flashcards`, não cria `FlashcardRecord` no trecho auditado |
| Revisão diária | PARCIAL/FALTA | endpoint e UI existem | Sem cards reais |
| Dificuldade | PARCIAL | `review_flashcard()` e campos existem | Não exercitado com dados reais |
| Estatísticas revisão | FALTA/PARCIAL | contagem `pendingReviews` existe | Sem dados e métricas completas |

## Home

| Seção da Home | Status | Dados reais? | Problema |
|---|---|---|---|
| Saudação/contexto | PARCIAL | Nome vem de `localStorage` | Não é configuração robusta |
| Continuar | PARCIAL | recentNotes reais | OK parcial |
| Revisar hoje | PARCIAL/FALTA | reviewCount real | Sem flashcards |
| Insights recentes | FALTA/PARCIAL | endpoint real | Vazio |
| Estatísticas rápidas | PARCIAL | contagens reais | Incompletas |
| Gráficos | FALTA | Não | Ausentes |
| Resumo Autopilot | PARCIAL | status real | Mostra backlog/offline |
| Preview grafo | PARCIAL | botão/tela | Sem conexões reais |
| Acessos rápidos | PARCIAL | Botões/modais existem | Nem todos têm funcionalidade completa |

## Painel Direito Contextual

Status: PARCIAL.

Evidência:

- `apps/web/src/components/panel/right-panel.tsx` mostra informações da nota, jobs/estatísticas e mensagem para processar com Autopilot.
- Não mostra resumo/conceitos/conexões/lacunas reais porque metadata de assimilação não está disponível no estado atual.
- Logs técnicos ainda aparecem como conteúdo principal em algumas áreas; atividade automática não está completamente separada.

Problema:

- Painel contextual deveria ser orientado à nota aberta; hoje ainda é técnico e incompleto.

## Configurações

| Configuração | Status | Persiste? | Tem efeito real? | Problema |
|---|---|---|---|---|
| Tema | PARCIAL | local/API settings | Sim no CSS vars | Parcial |
| Accent color | PARCIAL | sim | sim | OK parcial |
| Fonte UI/editor | PARCIAL | sim | sim provável | Sem validação visual profunda |
| Autosave config | FALTA/PARCIAL | Não visto como setting real | Não | Ausente |
| Ollama URL/modelos | PARCIAL | env/worker settings | Sim no worker | Não há tela completa ligada |
| Autopilot toggles | FALTA/PARCIAL | Alguns settings | Não completo | Ausente |
| Backup/reset | PARCIAL | endpoints/painel | Reset é destrutivo exposto | Requer cuidado UX |

## Design, UX e Polimento

Status: PARCIAL.

Pontos positivos:

- Visual atual é mais limpo que versão inicial.
- Sidebar redimensionável existe (`resize-handle.tsx`).
- Editor tem modos `Editar`, `Preview`, `Split`.
- Porta `3000` serve app.

Problemas:

- Fluxo ainda exige ação explícita para criar draft.
- Não há criação automática ao começar a escrever.
- Dados avançados aparecem vazios, gerando sensação de dashboard incompleto.
- Excluir ainda é ação acessível na UI; precisa revisão de UX destrutiva.
- Grafo/revisão/insights existem como telas, mas majoritariamente vazias.
- Sem gráficos.
- Sem validação visual responsiva por browser real nesta auditoria.

## Testes End-to-End Obrigatórios

| Teste | Status | Evidência | Resultado |
|---|---|---|---|
| Criar nota automaticamente | FALHA | API retorna 422 sem title; UI usa `createDraft()` com título fixo | Não atende |
| Assimilação | FALHA/PARCIAL | Worker deixou `ASSIMILATE_NOTE` running; metadata summary/concepts ausentes | Não fecha |
| Grafo | PARCIAL/FALHA | `/graph` tem nós, zero arestas | Sem conexões |
| Estatísticas | PARCIAL | `/home/summary`, `/monitor/stats` | Contagens básicas, sem gráficos |
| IA offline | PARCIAL/FALHA | `ollama_call()` relança; só title tem fallback | Não mantém pipeline completo |
| Configurações | PARCIAL | `/api/v1/settings`, settings panel | Algumas persistem, efeito parcial |
| Revisão | FALHA/PARCIAL | `/review/today` vazio | Sem flashcards |
| Design | PARCIAL | UI responde em `3000`; código mostra estados | Sem teste visual profundo |

## Tabela Geral

| Área | Status | Evidência | Problema | Prioridade |
|---|---|---|---|---|
| Editor-first | PARCIAL/FALTA | `createDraft()` e API title obrigatório | Não cria nota ao digitar livremente | Alta |
| Autosave | PARCIAL | `workspace-context.tsx:141-145` | Só depois de nota ativa | Alta |
| Nome automático | PARCIAL/FALTA | `GENERATE_NOTE_TITLE` job | Não integrado/confiável | Alta |
| Autopilot | PARCIAL | jobs criados e alguns processados | Pipeline não conclui | Alta |
| Worker/Ollama | PARCIAL | worker/gateway existem | job preso em running; IA não entrega fluxo | Alta |
| Embeddings | FALTA | count `0` | Sem busca semântica real | Alta |
| Conexões | FALTA | count `0` | Sem rede de conhecimento | Alta |
| Grafo | PARCIAL | `/graph` nós reais | Sem arestas/conexões | Alta |
| Estatísticas | PARCIAL | `/monitor/stats` | Só contagens básicas | Média |
| Gráficos | FALTA | sem lib/componente | Ausentes | Média |
| Insights IA | FALTA | `/insights` vazio | Não funciona | Alta |
| Flashcards/Revisão | FALTA/PARCIAL | `/review/today` vazio | Sem geração real | Alta |
| Home | PARCIAL | `/home/summary`, `home-view.tsx` | Dados avançados vazios | Média |
| Painel direito | PARCIAL | `right-panel.tsx` | Não mostra assimilação real | Média |
| Configurações | PARCIAL | `settings-panel.tsx`, settings API | Parcialmente funcionais | Média |
| Design/UX | PARCIAL | app `3000`, componentes atuais | Ainda não produto premium completo | Média |
| Clean Architecture | PARCIAL/FALTA | lógica em `services.py`, worker grande | Camadas não estão bem isoladas | Média |

## Pendências por Prioridade

### P0 - Crítico

#### 1. Recuperar jobs presos em `running`

- Corrigir: adicionar timeout/lease de job e requeue automático.
- Por que: worker interrompido deixou `ASSIMILATE_NOTE` em `running`.
- Arquivos prováveis: `apps/api/src/berrybrain_api/jobs.py`, `apps/worker/src/berrybrain_worker/main.py`.
- Risco: alto; bloqueia Autopilot.
- Critério de pronto: job `running` sem heartbeat expira e volta para `pending` ou `failed`.

#### 2. Fechar pipeline Autopilot por nota

- Corrigir: processar até parse, classify, assimilate, embedding, connections, flashcards, review e graph.
- Por que: hoje jobs são criados, mas resultados finais ficam vazios.
- Arquivos prováveis: `jobs.py`, `worker/main.py`, `services.py`, routers metadata/review/graph.
- Risco: alto.
- Critério de pronto: uma nota nova gera summary, concepts, embedding, connections quando houver candidato, flashcards e Home atualizada.

#### 3. Criar nota editor-first sem título obrigatório

- Corrigir: API aceitar draft sem título ou endpoint de draft; UI criar nota no primeiro input.
- Por que: requisito central falha com 422.
- Arquivos prováveis: `routers/notes.py`, `vault.py`, `workspace-context.tsx`, `note-editor.tsx`.
- Risco: alto.
- Critério de pronto: usuário abre app, digita, arquivo Markdown é criado e salvo sem preencher campo de título.

#### 4. Título automático funcional

- Corrigir: título gerado por H1/IA/fallback, renomeia arquivo, evita duplicidade e respeita lock manual.
- Por que: requisito central de segundo cérebro.
- Arquivos prováveis: `worker/main.py`, `vault.py`, `routers/notes.py`, novo serviço title.
- Risco: alto.
- Critério de pronto: textos Edge/Observabilidade geram títulos próximos aos esperados e slug seguro.

### P1 - Alto

#### 5. Embeddings reais e note_id correto

- Corrigir: worker não pode usar `status.notes` como fallback de `note_id`.
- Por que: `process_generate_embedding()` pode salvar embedding no note_id errado.
- Arquivos prováveis: `worker/main.py`, `routers/notes.py`, `generated_metadata.py`.
- Risco: alto.
- Critério de pronto: embedding salvo com `note_id` real da nota.

#### 6. Flashcards em tabela real

- Corrigir: worker deve criar `FlashcardRecord`, não só metadata.
- Por que: revisão depende da tabela `flashcards`.
- Arquivos prováveis: `worker/main.py`, `services.py`, `routers/review.py`.
- Risco: alto.
- Critério de pronto: `/review/today` retorna cards gerados.

#### 7. Conexões reais e grafo

- Corrigir: salvar conexões em `connections` e sincronizar graph nodes/edges.
- Por que: grafo sem arestas não representa conhecimento.
- Arquivos prováveis: `services.py`, `routers/connections.py`, `routers/graph.py`, worker.
- Risco: alto.
- Critério de pronto: duas notas relacionadas geram aresta com justificativa.

#### 8. Insights reais

- Corrigir: gerar e persistir `InsightRecord`.
- Por que: endpoint existe, mas vazio.
- Arquivos prováveis: `worker/main.py`, `services.py`, `routers/insights.py`.
- Risco: médio/alto.
- Critério de pronto: Home mostra insight acionável com ação/ignore.

#### 9. Suíte de testes completa

- Corrigir: instalar/adicionar `httpx2` ou adaptar `test_integration.py`.
- Por que: `unittest discover` falha.
- Arquivos prováveis: `apps/api/pyproject.toml`, `apps/api/tests/test_integration.py`.
- Risco: médio.
- Critério de pronto: todos os testes passam no container.

### P2 - Médio

#### 10. Estatísticas avançadas e gráficos

- Corrigir: criar endpoints agregados e componentes de gráfico.
- Por que: estatísticas atuais são contagens simples.
- Arquivos prováveis: routers stats, `home-view.tsx`, nova tela statistics.
- Risco: médio.
- Critério de pronto: gráficos com dados reais e empty states.

#### 11. Painel contextual por nota

- Corrigir: exibir resumo, conceitos, conexões, flashcards, lacunas e atividade filtrada da nota.
- Por que: painel ainda técnico/incompleto.
- Arquivos prováveis: `right-panel.tsx`, metadata endpoints.
- Risco: médio.
- Critério de pronto: abrir nota muda painel com dados reais da nota.

#### 12. Configurações com efeito total

- Corrigir: ligar settings a autosave, IA, Autopilot, editor e layout.
- Por que: settings existem parcialmente.
- Arquivos prováveis: `settings-panel.tsx`, settings API, worker config.
- Risco: médio.
- Critério de pronto: alteração persiste e muda comportamento após reload.

### P3 - Baixo

#### 13. Polimento visual e responsividade

- Corrigir: estados vazios, loading, erro, responsividade e microinterações.
- Por que: produto ainda parece parcial quando dados estão vazios.
- Arquivos prováveis: componentes web.
- Risco: baixo/médio.
- Critério de pronto: UI confortável em desktop/mobile, sem seções mortas.

#### 14. UX de ações destrutivas

- Corrigir: mover excluir/reset para menus seguros com confirmação forte.
- Por que: ações destrutivas estão expostas.
- Arquivos prováveis: `note-editor.tsx`, `settings-panel.tsx`.
- Risco: médio.
- Critério de pronto: destrutivas exigem confirmação e não ficam como ação primária.

## Conclusão

O BerryBrain não está funcionando como segundo cérebro completo. Ele já é uma base local com editor, vault Markdown, APIs, jobs, watcher, worker e algumas telas. Mas o valor principal prometido ainda não fecha: assimilação, embeddings, conexões, grafo real, insights, flashcards/revisão, estatísticas avançadas e criação editor-first automática ainda estão ausentes ou parciais.

O sistema está mais próximo de um protótipo funcional de editor local com fila de automação do que de um segundo cérebro autônomo com IA.
