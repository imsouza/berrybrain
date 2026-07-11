# BerryBrain - Planning dos Blocos Restantes

Data: 2026-07-07

## Estado Atual

Base funcional já existe:

- Docker Compose com `web`, `api` e perfil `worker`.
- Vault Markdown local.
- CRUD de notas pela API.
- Interface web mínima redesenhada.
- SQLite com modelo inicial.
- Scan manual do vault.
- Watcher automático por polling.
- Job Engine com `pending`, `running`, `completed`, `failed`.
- Worker mínimo consumindo jobs.
- Settings API.
- Automation logs.
- Testes unitários da API.

Ainda falta implementar o cérebro de IA e os fluxos avançados.

## Ordem Recomendada

### Bloco 1 - Worker Robusto

Objetivo: transformar o worker atual de execução única em um worker real.

Entregáveis:

- Loop contínuo configurável.
- Backoff quando não houver jobs.
- Tratamento de erro por job.
- Retry respeitando `attempts`.
- Heartbeat/status do worker.
- Endpoint de status do worker na API.

Critério de pronto:

- Worker roda em loop e processa jobs sem intervenção manual.
- Erros aparecem em `jobs.error_message`.
- API mostra último heartbeat do worker.

### Bloco 2 - Ollama Gateway

Objetivo: permitir que o worker chame Ollama local no Windows/PC.

Entregáveis:

- Cliente Ollama no worker.
- Health check do Ollama.
- Configuração dos modelos por settings/env.
- Timeout e erro controlado.
- Log de chamadas de IA em `automation_logs`.

Critério de pronto:

- Worker executa um job simples chamando `gemma3:4b` ou modelo configurado.
- Falha de Ollama não derruba o worker.

### Bloco 3 - Generated Metadata

Objetivo: salvar saídas automáticas separadas da nota original.

Entregáveis:

- Tabela ou armazenamento para resultados gerados por nota.
- Tipos: summary, concepts, gaps, questions, tags, aliases.
- Versionamento simples por `content_hash`.
- Endpoint para consultar metadata gerada.

Critério de pronto:

- Nenhuma IA sobrescreve Markdown original.
- UI consegue mostrar metadata gerada no painel contextual.

### Bloco 4 - Assimilation Engine

Objetivo: gerar análise estruturada de uma nota.

Entregáveis:

- Job `ASSIMILATE_NOTE`.
- Prompt `assimilation.v1.md` usado pelo worker.
- JSON schema validado.
- Persistência de resumo, conceitos, lacunas e perguntas.
- Logs de automação.

Critério de pronto:

- Ao alterar uma nota, o BerryBrain gera assimilação útil e persistida.

### Bloco 5 - Embeddings

Objetivo: gerar vetores locais para busca semântica.

Entregáveis:

- Job `GENERATE_EMBEDDING`.
- Chamada Ollama embeddings com `bge-m3`.
- Escolha final entre Qdrant/Chroma ou fallback local inicial.
- Persistência dos vetores.
- Reprocessamento por `content_hash`.

Critério de pronto:

- Cada nota processada tem embedding associado.

### Bloco 6 - Busca Semântica

Objetivo: encontrar notas por significado.

Entregáveis:

- Endpoint de busca semântica.
- Busca textual simples + busca vetorial.
- Ranking híbrido inicial.
- UI de busca/command palette básica.

Critério de pronto:

- Consulta em português encontra notas relacionadas por sentido, não só por termo exato.

### Bloco 7 - Connection Engine

Objetivo: criar conexões entre notas.

Entregáveis:

- Job `FIND_CONNECTIONS`.
- Candidatos via embeddings.
- Prompt `connections.v1.md`.
- Persistência em `connections`.
- Tipos: semantic, prerequisite, related, duplicate, contrast, example, application.
- Justificativa e confidence score.

Critério de pronto:

- Painel contextual mostra conexões com motivo.

### Bloco 8 - Flashcards

Objetivo: gerar estudo ativo a partir das notas.

Entregáveis:

- Job `GENERATE_FLASHCARDS`.
- Prompt `flashcards.v1.md`.
- Persistência em `flashcards`.
- Endpoint de listagem por nota.
- UI simples no painel contextual.

Critério de pronto:

- Uma nota assimilada gera flashcards revisáveis.

### Bloco 9 - Review Engine

Objetivo: criar fila diária de revisão.

Entregáveis:

- Repetição espaçada inicial.
- Endpoint `review/today`.
- Marcar acerto/erro/dificuldade.
- Atualizar `next_review_at`.
- Modo revisão básico na UI.

Critério de pronto:

- Usuário consegue revisar flashcards do dia e reagendar automaticamente.

### Bloco 10 - Insight Engine

Objetivo: gerar inteligência sobre a base.

Entregáveis:

- Jobs `GENERATE_INSIGHTS`.
- Insights diários/semanais.
- Notas fracas.
- Conceitos isolados.
- Duplicidades.
- Trilhas sugeridas.
- Persistência em `insights`.

Critério de pronto:

- Home mostra insights acionáveis baseados no vault.

### Bloco 11 - Graph Engine

Objetivo: visualizar rede de conhecimento.

Entregáveis:

- Endpoint de grafo com nós e arestas.
- Nós de notas e conceitos.
- Filtros básicos.
- UI inicial de grafo.
- Destaque de órfãs, centrais e clusters simples.

Critério de pronto:

- Usuário vê conexões entre notas no navegador.

### Bloco 12 - Autopilot Completo

Objetivo: orquestrar todos os jobs automaticamente.

Entregáveis:

- Pipeline por evento de nota.
- Ordem: parse, classify, embedding, assimilate, connections, flashcards, review, insights, graph.
- Configurações de modo: manual, assistido, automático, autopilot.
- Deduplicação de jobs por nota/hash.
- Painel de atividade completo.

Critério de pronto:

- Usuário salva nota e o pipeline completo roda sem ação manual.

### Bloco 13 - Customização Avançada

Objetivo: permitir ajustar visual e comportamento sem código.

Entregáveis:

- Tela de settings.
- Tema claro/escuro/OLED/sepia.
- Accent color.
- Densidade confortável/compacta.
- Fonte e tamanho do editor.
- Modelo principal/rápido/embeddings/raciocínio.
- Frequência do watcher/autopilot.

Critério de pronto:

- Settings persistem no SQLite e afetam UI/comportamento.

### Bloco 14 - Segurança Local

Objetivo: garantir privacidade e operação local.

Entregáveis:

- Revisão de chamadas externas.
- Bloqueio documentado de cloud.
- Autenticação local opcional.
- CORS restrito por configuração.
- Proteção básica da API local.
- Orientação para não expor Ollama na rede.

Critério de pronto:

- BerryBrain funciona sem internet e sem enviar notas para fora.

### Bloco 15 - Backup e Restore

Objetivo: recuperar vault, SQLite e metadata.

Entregáveis:

- Backup do vault.
- Backup do SQLite.
- Backup de metadata gerada.
- Snapshot antes de automações grandes.
- Endpoint/comando de restore.
- Exportação completa.

Critério de pronto:

- Usuário consegue restaurar o BerryBrain após erro ou automação ruim.

### Bloco 16 - Observabilidade Completa

Objetivo: diagnosticar qualquer problema.

Entregáveis:

- Dashboard de jobs.
- Logs de IA.
- Status do worker.
- Status do Ollama.
- Erros recentes.
- Filtros por job/status/nota.

Critério de pronto:

- Problema em IA, worker, vault ou API aparece claramente na UI.

### Bloco 17 - Testes de Integração

Objetivo: estabilizar fluxos principais.

Entregáveis:

- Teste API CRUD + jobs.
- Teste watcher + scan.
- Teste worker + job fake.
- Teste Ollama gateway mockável.
- Teste pipeline autopilot.
- Teste web build.

Critério de pronto:

- Fluxos centrais têm cobertura automatizada.

### Bloco 18 - Polimento de Produto

Objetivo: fazer o BerryBrain parecer produto real.

Entregáveis:

- Empty states melhores.
- Loading states.
- Error states.
- Responsividade.
- Acessibilidade básica.
- Atalhos de teclado.
- Command palette.
- Refinamento visual final.

Critério de pronto:

- Interface fica rápida, calma, clara e confortável para estudo diário.

## Dependências Críticas

- Ollama precisa estar rodando no PC Windows.
- Worker precisa conseguir acessar a API do Raspberry/NAS.
- API nunca deve chamar Ollama pelo frontend.
- Markdown original deve continuar protegido.
- Resultados automáticos devem ser versionados por hash.
- Toda automação precisa gerar log.

## Próximo Bloco Recomendado

Começar pelo Bloco 1 - Worker Robusto.

Motivo:

- Ollama, embeddings, assimilação e conexões dependem de um worker estável.
- Evita implementar IA pesada em cima de execução manual.
- Reduz risco antes de processar notas reais.

---

# Subtasks Técnicas por Bloco

## Bloco 1 - Worker Robusto

**Arquivos alvo:**
- `apps/worker/src/berrybrain_worker/main.py`
- `apps/worker/src/berrybrain_worker/config.py`
- `apps/api/src/berrybrain_api/main.py` (novo endpoint heartbeat)
- `apps/api/src/berrybrain_api/models.py` (nova coluna `worker_heartbeat`)

### 1.1 Loop contínuo configurável
- [ ] `WorkerSettings.loop_interval_seconds: int = 5`
- [ ] `WorkerSettings.max_consecutive_empty: int = 30`
- [ ] `WorkerSettings.max_job_attempts: int = 3`
- [ ] Substituir `asyncio.run(main())` por `asyncio.run(run_loop())`
- [ ] `run_loop()`: enquanto `True`, chama `process_one()`, dorme `loop_interval_seconds`

### 1.2 Backoff quando sem jobs
- [ ] `empty_count = 0` no loop
- [ ] Se `claim_next_job()` retorna `None`: `empty_count += 1`
- [ ] Se `empty_count >= max_consecutive_empty`: sleep escala até `loop_interval_seconds * 4`
- [ ] Se job encontrado: `empty_count = 0`

### 1.3 Tratamento de erro por job
- [ ] `try/except` envolvendo `process_job()` captura `httpx.HTTPError`, `ValueError`, `Exception`
- [ ] Em falha: chama `fail_job()` com `error_message` truncado a 2000 chars
- [ ] Worker nunca quebra — sempre continua para o próximo job

### 1.4 Retry respeitando attempts
- [ ] `claim_next_job()` na API: adicionar coluna `max_attempts` ao `JobRecord` (default 3)
- [ ] No `fail_job()` da API: se `attempts < max_attempts`, resetar status para `pending` em vez de `failed`
- [ ] No `claim_next_job()`: pular jobs onde `attempts >= max_attempts` e status != `pending`

### 1.5 Heartbeat/status do worker
- [ ] Nova coluna `worker_heartbeat` no model `JobRecord` ou tabela separada `worker_status` com colunas `id`, `status`, `last_heartbeat`, `jobs_processed`, `errors`
- [ ] Worker chama `POST /api/v1/worker/heartbeat` a cada `loop_interval_seconds`
- [ ] API endpoint: `GET /api/v1/worker/status` retorna `{status, last_heartbeat, uptime, jobs_processed, errors}`

### 1.6 Endpoint de status na API
- [ ] `GET /api/v1/worker/status`
- [ ] `POST /api/v1/worker/heartbeat` (recebe `{jobs_processed, errors}`)

### 1.7 Testes
- [ ] `tests/test_worker_loop.py`: mock `httpx.AsyncClient`, simula 3 ciclos (sem job, com job, erro no job)
- [ ] `tests/test_worker_heartbeat.py`: verifica endpoint heartbeat registra timestamp
- [ ] `tests/test_worker_retry.py`: job com `attempts=2` de `max_attempts=3` volta a `pending`, job com `attempts=3` fica `failed`

---

## Bloco 2 - Ollama Gateway

**Arquivos alvo:**
- `apps/worker/src/berrybrain_worker/main.py` (módulo `ollama_gateway.py` novo)
- `apps/worker/src/berrybrain_worker/config.py`

### 2.1 Cliente Ollama no worker
- [ ] Novo arquivo `apps/worker/src/berrybrain_worker/ollama_gateway.py`
- [ ] `async def check_health(base_url) -> bool`: `GET {base_url}/api/tags`, retorna `True` se status 200
- [ ] `async def generate(base_url, model, prompt, system=None) -> str`: `POST {base_url}/api/generate`, stream=False, timeout 120s
- [ ] `async def generate_json(base_url, model, prompt, system=None) -> dict`: mesmo acima + `format="json"`

### 2.2 Health check do Ollama
- [ ] Na inicialização do worker: `assert_ollama_ready()` chama `check_health()`
- [ ] Loga warning se Ollama indisponível mas não quebra — worker segue tentando

### 2.3 Configuração por settings/env
- [ ] `WorkerSettings.ollama_timeout: int = 120` (já existe `ollama_base_url` e modelos)

### 2.4 Timeout e erro controlado
- [ ] `httpx.Timeout(ollama_timeout)` no client do gateway
- [ ] Captura `httpx.ReadTimeout` → retorna erro descritivo
- [ ] Captura conexão recusada → loga, worker não crasha

### 2.5 Log de chamadas IA
- [ ] Toda chamada `generate()`/`generate_json()` registra em `automation_logs` via `POST /api/v1/automation-logs`:
  - `action_type`: `"OLLAMA_GENERATE"`
  - `target_type`: `"note"` se associado a nota, `"system"` caso contrário
  - `before_state`: `{model, prompt_length, system_length}`
  - `after_state`: `{response_length, duration_ms}`

### 2.6 Testes
- [ ] `tests/test_ollama_gateway.py`: mock `httpx.AsyncClient`, testa health check OK/fail, generate OK/timeout, generate_json com parse válido/inválido

---

## Bloco 3 - Generated Metadata

**Arquivos alvo:**
- `apps/api/src/berrybrain_api/models.py` (nova tabela)
- `apps/api/src/berrybrain_api/main.py` (novos endpoints)
- `apps/api/src/berrybrain_api/generated_metadata.py` (novo)
- `apps/api/src/berrybrain_api/database.py` (ensure_sqlite_columns)

### 3.1 Tabela `generated_metadata`
- [ ] Novo model `GeneratedMetadataRecord`:
  - `id`: Integer PK
  - `note_id`: Integer FK → notes.id, NOT NULL
  - `generation_type`: String(50) NOT NULL — valores: `summary`, `concepts`, `gaps`, `questions`, `tags`, `aliases`, `classification`
  - `content`: Text NOT NULL (JSON string)
  - `content_hash`: String(128) NOT NULL (hash da nota no momento da geração)
  - `model_used`: String(80)
  - `created_at`: DateTime default utc_now
- [ ] Índice composto: `(note_id, generation_type)` para lookup rápido

### 3.2 CRUD de metadata
- [ ] `upsert_generated_metadata(session, note_id, generation_type, content, content_hash, model_used)` — upsert por `(note_id, generation_type)`
- [ ] `get_generated_metadata(session, note_id, generation_type=None)` — filtra opcionalmente por tipo
- [ ] `delete_generated_metadata(session, note_id, generation_type)` — limpeza antes de regenerar

### 3.3 Versionamento por content_hash
- [ ] No upsert: se `content_hash` mudou desde última geração, sobrescreve; senão, skip
- [ ] `is_stale(session, note_id, current_hash) -> list[generation_type]` — retorna tipos com hash desatualizado

### 3.4 Endpoints
- [ ] `GET /api/v1/metadata?note_path={path}` — retorna todos os metadados gerados da nota
- [ ] `GET /api/v1/metadata/{type}?note_path={path}` — retorna tipo específico
- [ ] `DELETE /api/v1/metadata/{type}?note_path={path}` — permite regeneração manual

### 3.5 Serialização
- [ ] Função `serialize_generated_metadata(record)` — parse do JSON content, retorna dict limpo

### 3.6 Testes
- [ ] `tests/test_generated_metadata.py`: CRUD básico, upsert com mesmo hash não duplica, upsert com hash diferente atualiza, is_stale retorna corretamente, endpoint GET/DELETE

---

## Bloco 4 - Assimilation Engine

**Arquivos alvo:**
- `apps/worker/src/berrybrain_worker/main.py` (novo job type)
- `apps/worker/src/berrybrain_worker/ollama_gateway.py`
- `apps/api/src/berrybrain_api/jobs.py` (nova constante)
- `apps/api/src/berrybrain_api/main.py` (endpoints criados no Bloco 3)
- `prompts/assimilation.v1.md` (já existe, pode precisar de ajuste)

### 4.1 Job ASSIMILATE_NOTE
- [ ] Constante `ASSIMILATE_NOTE = "ASSIMILATE_NOTE"` em `jobs.py`
- [ ] `enqueue_note_changed_jobs()`: após `PARSE_NOTE`, também enfileira `ASSIMILATE_NOTE`

### 4.2 Prompt carregado do disco
- [ ] Worker lê `prompts/assimilation.v1.md` na inicialização (caminho relativo ao project root)
- [ ] `PROMPTS_DIR = Path(__file__).resolve().parents[4] / "prompts"` (sobe de `berrybrain_worker/` até `berrybrain/`)
- [ ] Cache do prompt em memória: `_prompt_cache: dict[str, str] = {}`

### 4.3 Processamento do job
- [ ] `process_job()`: novo branch `elif job_type == ASSIMILATE_NOTE:`
- [ ] Extrai `note_id`, `note_path`, `content_hash` do payload
- [ ] Busca conteúdo da nota via `GET /api/v1/notes/{path}`
- [ ] Chama `ollama_gateway.generate_json(main_model, prompt + note_content)`
- [ ] Valida JSON schema da resposta
- [ ] Persiste via endpoints do Bloco 3:
  - `PUT /api/v1/metadata/summary?note_path={path}`
  - `PUT /api/v1/metadata/concepts?note_path={path}`
  - `PUT /api/v1/metadata/gaps?note_path={path}`
  - `PUT /api/v1/metadata/questions?note_path={path}`

### 4.4 JSON schema validation
- [ ] Schema esperado: `{summary: str, concepts: [{name, description}], gaps: [{topic, reason}], questions: [str], language: str}`
- [ ] `validate_assimilation_output(data: dict) -> dict` — preenche defaults para campos ausentes
- [ ] Se JSON inválido: retry uma vez com prompt reforçando o schema

### 4.5 Logs de automação
- [ ] `POST /api/v1/automation-logs` com `action_type="ASSIMILATE_NOTE"`, `target_type="note"`, `target_id=note_path`

### 4.6 Testes
- [ ] `tests/test_assimilation_engine.py`: mock Ollama response, verifica extração de summary/concepts/gaps/questions, valida schema, testa retry em JSON inválido

---

## Bloco 5 - Embeddings

**Arquivos alvo:**
- `apps/worker/src/berrybrain_worker/ollama_gateway.py` (nova função)
- `apps/worker/src/berrybrain_worker/main.py` (novo job type)
- `apps/api/src/berrybrain_api/models.py` (nova tabela)
- `apps/api/src/berrybrain_api/jobs.py` (nova constante)
- `apps/api/src/berrybrain_api/main.py` (novos endpoints)

### 5.1 Fallback local inicial
- [ ] Tabela `embeddings` no SQLite:
  - `id`: Integer PK
  - `note_id`: Integer FK → notes.id
  - `chunk_index`: Integer default 0
  - `vector`: Text NOT NULL (JSON array de floats)
  - `model`: String(80)
  - `dimensions`: Integer
  - `content_hash`: String(128)
  - `created_at`: DateTime
- [ ] Índice em `note_id`
- [ ] Para busca semântica inicial: brute-force cosine similarity em Python (≤ 1000 notas é instantâneo). Sem Qdrant/Chroma ainda.

### 5.2 Job GENERATE_EMBEDDING
- [ ] Constante `GENERATE_EMBEDDING = "GENERATE_EMBEDDING"` em `jobs.py`
- [ ] Enfileirado após `ASSIMILATE_NOTE` no pipeline

### 5.3 Chamada Ollama embeddings
- [ ] `async def embed(base_url, model, text) -> list[float]`: `POST {base_url}/api/embeddings` com `{model, prompt: text}`
- [ ] Timeout 60s
- [ ] Chunking: se nota > 2000 tokens (~8000 chars), divide em chunks de 2000 tokens com overlap de 200

### 5.4 Persistência
- [ ] `upsert_embedding(session, note_id, chunk_index, vector, model, dimensions, content_hash)`
- [ ] `get_embeddings_for_note(session, note_id) -> list`
- [ ] `delete_embeddings_for_note(session, note_id)`

### 5.5 Reprocessamento por content_hash
- [ ] Antes de gerar embedding: verifica se `content_hash` atual bate com o armazenado
- [ ] Se hash diferente: deleta embeddings antigos, gera novos

### 5.6 Endpoints
- [ ] `GET /api/v1/notes/{note_path:path}/embeddings` — status dos embeddings (dimensões, modelo, data)

### 5.7 Testes
- [ ] `tests/test_embeddings.py`: mock Ollama embed response, verifica persistência, testa chunking, testa reprocessamento por hash

---

## Bloco 6 - Busca Semântica

**Arquivos alvo:**
- `apps/api/src/berrybrain_api/main.py` (novo endpoint)
- `apps/api/src/berrybrain_api/search.py` (novo)
- `apps/web/src/app/page.tsx` ou novo componente de busca
- `apps/web/src/components/command-palette.tsx` (novo)

### 6.1 Endpoint de busca semântica
- [ ] `GET /api/v1/search?q=texto&limit=10&mode=hybrid`
- [ ] Parâmetros: `q` (obrigatório), `limit` (default 10), `mode` (semantic, text, hybrid)

### 6.2 Busca vetorial (cosine similarity)
- [ ] `semantic_search(session, query_embedding, limit) -> list[(note_id, score)]`
- [ ] Para cada embedding no SQLite, calcula cosine similarity com o query embedding
- [ ] Ordena por score descendente, limita

### 6.3 Busca textual simples
- [ ] `text_search(session, query, limit) -> list[(note_id, score)]`
- [ ] FTS5 no SQLite: `CREATE VIRTUAL TABLE notes_fts USING fts5(title, body, content=notes, content_rowid=id)`
- [ ] Triggers para manter FTS sincronizado com `notes` (INSERT, UPDATE, DELETE)
- [ ] Score via `bm25(notes_fts)`

### 6.4 Ranking híbrido
- [ ] `hybrid_search(session, query, limit) -> list[(note_id, score)]`
- [ ] Gera embedding da query
- [ ] Busca semântica (top 50) + busca textual (top 50)
- [ ] Combina com `score = 0.7 * semantic_score + 0.3 * text_score` (normalizados)
- [ ] Deduplica por note_id, ordena, limita

### 6.5 UI de busca
- [ ] Componente `command-palette.tsx`: `Cmd+K` abre modal com input de busca
- [ ] Debounce 300ms no input
- [ ] Resultados em lista com título, snippet (primeiras 80 chars), score
- [ ] Enter/click abre a nota no workspace

### 6.6 Testes
- [ ] `tests/test_search.py`: mock embeddings, testa semantic/text/hybrid, verifica ranking, testa FTS5 sync

---

## Bloco 7 - Connection Engine

**Arquivos alvo:**
- `apps/worker/src/berrybrain_worker/main.py` (novo job type)
- `apps/api/src/berrybrain_api/jobs.py` (nova constante)
- `apps/api/src/berrybrain_api/connections.py` (novo)
- `apps/api/src/berrybrain_api/main.py` (novos endpoints)
- `apps/api/src/berrybrain_api/models.py` (tabela já existe)
- `prompts/connections.v1.md` (já existe)

### 7.1 Job FIND_CONNECTIONS
- [ ] Constante `FIND_CONNECTIONS = "FIND_CONNECTIONS"` em `jobs.py`
- [ ] Payload: `{note_id, note_path, content_hash}`
- [ ] Enfileirado após `GENERATE_EMBEDDING` no pipeline

### 7.2 Candidatos via embeddings
- [ ] Worker busca top 10 notas mais similares via endpoint de busca semântica
- [ ] Filtra a própria nota e notas já conectadas (em ambas direções)
- [ ] Monta prompt com: nota fonte + {candidato: título, trecho relevante} para cada candidato

### 7.3 Prompt connections.v1.md
- [ ] Worker carrega prompt do disco (já existe em `prompts/connections.v1.md`)
- [ ] Prompt recebe contexto da nota + candidatos
- [ ] Response: JSON array de `{target_note_path, type, confidence, reason}`

### 7.4 Persistência em connections
- [ ] `create_connection(session, source_note_id, target_note_id, connection_type, confidence, reason, created_by="assimilation")`
- [ ] `get_connections_for_note(session, note_id) -> list` (bidirecional: source ou target)
- [ ] `delete_stale_connections(session, note_id)` — limpa antes de regenerar
- [ ] Tipos validados contra enum: `semantic, prerequisite, related, duplicate, contrast, example, application`

### 7.5 Endpoints
- [ ] `GET /api/v1/connections/{note_path:path}` — lista conexões com detalhes
- [ ] Conexão serializada inclui: `{id, type, confidence, reason, source_note: {title, path}, target_note: {title, path}}`

### 7.6 UI no painel contextual
- [ ] No `note-workspace.tsx`: seção "Conexões" no painel direito quando nota ativa
- [ ] Agrupado por tipo com badge colorido
- [ ] Click na conexão abre a nota alvo

### 7.7 Testes
- [ ] `tests/test_connections.py`: CRUD connection, valida tipos, testa bidirecional, testa delete stale, mock Ollama response

---

## Bloco 8 - Flashcards

**Arquivos alvo:**
- `apps/worker/src/berrybrain_worker/main.py` (novo job type)
- `apps/api/src/berrybrain_api/jobs.py` (nova constante)
- `apps/api/src/berrybrain_api/flashcards.py` (novo)
- `apps/api/src/berrybrain_api/main.py` (novos endpoints)
- `apps/api/src/berrybrain_api/models.py` (tabela já existe)
- `prompts/flashcards.v1.md` (já existe)

### 8.1 Job GENERATE_FLASHCARDS
- [ ] Constante `GENERATE_FLASHCARDS = "GENERATE_FLASHCARDS"` em `jobs.py`
- [ ] Payload: `{note_id, note_path, content_hash}`
- [ ] Enfileirado após `FIND_CONNECTIONS` no pipeline

### 8.2 Prompt flashcards.v1.md
- [ ] Worker carrega prompt do disco
- [ ] Inclui summary e concepts do metadata gerado como contexto extra
- [ ] Response: JSON `{flashcards: [{question, answer, difficulty}]}`

### 8.3 Persistência
- [ ] `create_flashcards_batch(session, note_id, flashcards: list[dict])` — deleta flashcards existentes da nota, insere novos
- [ ] `get_flashcards_for_note(session, note_id) -> list[FlashcardRecord]`
- [ ] `get_flashcards_for_review(session, before_date, limit) -> list[FlashcardRecord]` — flashcards com `next_review_at <= before_date`

### 8.4 Endpoints
- [ ] `GET /api/v1/notes/{note_path:path}/flashcards` — lista flashcards da nota
- [ ] `POST /api/v1/notes/{note_path:path}/flashcards/review` — registra review: `{flashcard_id, result: "correct"|"wrong"|"hard"}`
- [ ] `GET /api/v1/review/today` — flashcards do dia

### 8.5 UI no painel contextual
- [ ] Aba "Flashcards" no painel direito quando nota ativa
- [ ] Lista de flashcards com pergunta visível, resposta em toggle (click expande)
- [ ] Botão "Revisar" abre modal de revisão sequencial

### 8.6 Testes
- [ ] `tests/test_flashcards.py`: create batch, get by note, get for review por data, mock Ollama response

---

## Bloco 9 - Review Engine

**Arquivos alvo:**
- `apps/api/src/berrybrain_api/review.py` (novo)
- `apps/api/src/berrybrain_api/main.py` (novos endpoints)
- `apps/web/src/components/review-mode.tsx` (novo)

### 9.1 Repetição espaçada (SM-2 simplificado)
- [ ] `calculate_next_review(result: str, current_interval_days: int, ease_factor: float) -> (next_interval, ease_factor)`
- [ ] `correct`: `interval *= ease_factor`, `ease_factor += 0.1`
- [ ] `wrong`: `interval = max(1, interval * 0.5)`, `ease_factor = max(1.3, ease_factor - 0.2)`
- [ ] `hard`: `interval *= 1.2`, `ease_factor = max(1.3, ease_factor - 0.15)`

### 9.2 Endpoint review/today
- [ ] `GET /api/v1/review/today?limit=20` — flashcards com `next_review_at <= now` e `next_review_at is null` (nunca revisados)
- [ ] Ordenado por: overdue primeiro (mais antigo), depois por dificuldade

### 9.3 Registrar resultado da revisão
- [ ] `POST /api/v1/review/{flashcard_id}` — body: `{result: "correct"|"wrong"|"hard"}`
- [ ] Atualiza `last_reviewed_at`, `next_review_at` (calculado), `difficulty` (ajustado se necessário)
- [ ] Campos novos no model `FlashcardRecord`: `review_interval_days: Integer default 1`, `ease_factor: Float default 2.5`, `review_count: Integer default 0`

### 9.4 Modo revisão na UI
- [ ] Componente `review-mode.tsx`: tela cheia ou modal
- [ ] Mostra pergunta → usuário pensa → revela resposta (click/botão)
- [ ] Botões: "Acertei" (verde), "Errei" (vermelho), "Difícil" (amarelo)
- [ ] Progresso: "3/15" no topo
- [ ] Ao final: resumo da sessão (corretos, erros, difíceis)

### 9.5 Testes
- [ ] `tests/test_review.py`: algoritmo SM-2 para correct/wrong/hard, endpoint review/today filtra por data, POST review atualiza campos

---

## Bloco 10 - Insight Engine

**Arquivos alvo:**
- `apps/worker/src/berrybrain_worker/main.py` (novo job type)
- `apps/api/src/berrybrain_api/jobs.py` (nova constante)
- `apps/api/src/berrybrain_api/insights.py` (novo)
- `apps/api/src/berrybrain_api/main.py` (novos endpoints)
- `apps/api/src/berrybrain_api/models.py` (tabela já existe)
- `prompts/daily-insights.v1.md` (já existe)
- `apps/web/src/app/page.tsx` (home dashboard)

### 10.1 Job GENERATE_INSIGHTS
- [ ] Constante `GENERATE_INSIGHTS = "GENERATE_INSIGHTS"` em `jobs.py`
- [ ] Payload: `{scope: "daily"|"weekly"|"full"}`
- [ ] Job disparado por scheduler simples no worker (a cada N ciclos de loop) ou endpoint manual `POST /api/v1/insights/generate`

### 10.2 Coleta de dados para prompt
- [ ] Worker agrega dados da API:
  - Notas sem assimilação (sem metadata)
  - Conceitos isolados (connections count = 0)
  - Notas fracas (flashcards com review_count > 0 e baixa taxa de acerto)
  - Duplicidades (connections type=duplicate)
  - Notas mais antigas sem revisão

### 10.3 Prompt daily-insights.v1.md
- [ ] Worker carrega prompt do disco
- [ ] Injeta dados agregados no prompt
- [ ] Response parseado: `[{type, title, description, related_notes, priority}]`

### 10.4 Persistência
- [ ] `create_insight(session, type, title, description, related_notes: list[int], priority)`
- [ ] `get_active_insights(session, limit) -> list[InsightRecord]` — `dismissed_at is null`, ordenado por priority desc
- [ ] `dismiss_insight(session, insight_id)` — seta `dismissed_at = now`

### 10.5 Tipos de insight
- [ ] `knowledge_gap` — tópico mencionado mas sem nota própria
- [ ] `weak_note` — flashcards consistentemente errados
- [ ] `isolated_concept` — conceito sem conexões
- [ ] `duplicate_content` — notas muito similares
- [ ] `study_path` — trilha sugerida (pré-requisitos → atual → próximo)
- [ ] `review_opportunity` — notas que deveriam ser revisadas

### 10.6 Endpoints
- [ ] `GET /api/v1/insights?limit=10` — insights ativos
- [ ] `POST /api/v1/insights/{id}/dismiss` — dispensa insight
- [ ] `POST /api/v1/insights/generate` — dispara geração manual

### 10.7 Home dashboard
- [ ] Seção "Insights" no home (`page.tsx`)
- [ ] Cards de insight com ícone por tipo, título, descrição curta
- [ ] Click "Ver nota" abre nota relacionada
- [ ] Botão "Dispensar" (X) remove do dashboard

### 10.8 Testes
- [ ] `tests/test_insights.py`: CRUD insight, dismiss, get_active não retorna dismissed, mock Ollama response

---

## Bloco 11 - Graph Engine

**Arquivos alvo:**
- `apps/api/src/berrybrain_api/graph.py` (novo)
- `apps/api/src/berrybrain_api/main.py` (novo endpoint)
- `apps/web/package.json` (adicionar lib de grafo — D3.js ou vis-network)
- `apps/web/src/components/graph-view.tsx` (novo)

### 11.1 Endpoint de grafo
- [ ] `GET /api/v1/graph` — retorna `{nodes: [...], edges: [...]}`
- [ ] Parâmetros opcionais: `?concept=name` (filtra por conceito), `?max_depth=2` (profundidade)
- [ ] `nodes`: `[{id, label, type: "note"|"concept", group, metadata: {note_count, connection_count}}]`
- [ ] `edges`: `[{source, target, type, confidence, label}]`

### 11.2 Nós e arestas
- [ ] Notas → nodes com `type: "note"`, `group` por `note_type` ou pasta
- [ ] Conceitos → nodes com `type: "concept"`, `group: "concept"`, `metadata.note_count`
- [ ] Conexões → edges com `label = connection_type`
- [ ] Links internos (`[[wikilinks]]`) → edges com `type: "link"`, `confidence: 100`

### 11.3 Métricas de grafo
- [ ] `compute_graph_stats(nodes, edges) -> {orphan_count, central_nodes: [id], cluster_count}`
- [ ] Órfãs: notas com degree 0 (sem conexões nem links)
- [ ] Centrais: top 5 nós por degree

### 11.4 UI de grafo
- [ ] Lib: `vis-network` (mais simples que D3 para grafo interativo, ~200KB)
- [ ] Componente `graph-view.tsx`: canvas interativo
- [ ] Nós coloridos por tipo/pasta
- [ ] Hover mostra título + tipo
- [ ] Click navega para a nota
- [ ] Zoom/pan com mouse
- [ ] Legenda de tipos de conexão

### 11.5 Testes
- [ ] `tests/test_graph.py`: endpoint retorna estrutura correta, filtro por conceito funciona, métricas de órfãs e centrais

---

## Bloco 12 - Autopilot Completo

**Arquivos alvo:**
- `apps/worker/src/berrybrain_worker/main.py` (orquestração)
- `apps/worker/src/berrybrain_worker/pipeline.py` (novo)
- `apps/api/src/berrybrain_api/jobs.py` (novas constantes, dedup)
- `apps/api/src/berrybrain_api/settings_store.py` (modos de automação)
- `apps/web/src/components/autopilot-panel.tsx` (novo)

### 12.1 Pipeline por evento de nota
- [ ] `NOTE_PIPELINE = [PARSE_NOTE, ASSIMILATE_NOTE, GENERATE_EMBEDDING, FIND_CONNECTIONS, GENERATE_FLASHCARDS]`
- [ ] `enqueue_pipeline(session, note_path, event_type, content_hash)` — enfileira todos em ordem
- [ ] Jobs têm `depends_on: job_id` no payload para execução sequencial

### 12.2 Ordem de execução
- [ ] Worker alterado para respeitar `depends_on`: só processa job se job dependente está `completed`
- [ ] Ou: pipeline roda jobs sequencialmente no mesmo ciclo do worker (claim → process → complete → claim next no pipeline)

### 12.3 Modos de automação
- [ ] Setting `automation.mode`: `manual`, `assisted`, `automatic`, `autopilot`
- [ ] `manual`: jobs são criados mas não processados automaticamente (worker ignora)
- [ ] `assisted`: worker processa mas pede confirmação antes de modificar dados (futuro, começa igual automatic)
- [ ] `automatic`: worker processa tudo, só jobs sem `depends_on` pendente
- [ ] `autopilot`: worker processa tudo + insights diários + revisão automática

### 12.4 Deduplicação de jobs
- [ ] `is_duplicate_job(session, job_type, note_id, content_hash) -> bool` — verifica se já existe job pendente/running do mesmo tipo para a mesma nota com o mesmo hash
- [ ] No `enqueue_note_changed_jobs`: pular tipos já enfileirados

### 12.5 Painel de atividade
- [ ] Componente `autopilot-panel.tsx`: status do pipeline para a nota ativa
- [ ] Lista vertical: cada etapa do pipeline com ícone (pending/processing/done/error)
- [ ] Barra de progresso geral
- [ ] Tempo estimado por etapa

### 12.6 Testes
- [ ] `tests/test_pipeline.py`: enqueue pipeline cria todos os jobs em ordem, dedup bloqueia duplicata, depends_on impede execução prematura

---

## Bloco 13 - Customização Avançada

**Arquivos alvo:**
- `apps/web/src/app/globals.css` (CSS custom properties)
- `apps/web/src/app/layout.tsx` (theme provider)
- `apps/web/src/components/settings-panel.tsx` (novo)
- `apps/web/src/components/theme-provider.tsx` (novo)
- `apps/api/src/berrybrain_api/settings_store.py` (uso dos settings)

### 13.1 Tela de settings
- [ ] Rota `/settings` ou modal/drawer no workspace
- [ ] Abas: Aparência, Editor, IA, Automação

### 13.2 Temas
- [ ] CSS custom properties para cada tema:
  - `light`: cores atuais
  - `dark`: inversão de foreground/background
  - `oled`: fundo preto puro, contraste reduzido
  - `sepia`: tons quentes para leitura longa
- [ ] `ThemeProvider` lê `data-theme` do localStorage/settings, aplica classe no `<html>`
- [ ] Setting `ui.theme` persistido no SQLite

### 13.3 Accent color e densidade
- [ ] Setting `ui.accent_color`: 6 opções (green atual, blue, purple, orange, rose, amber)
- [ ] CSS: `--color-accent` trocado dinamicamente
- [ ] Setting `ui.density`: `comfortable` (padrão), `compact` (alturas menores, gaps reduzidos)

### 13.4 Fonte e tamanho do editor
- [ ] Setting `ui.editor_font`: `sans`, `serif`, `mono`
- [ ] Setting `ui.editor_font_size`: 12-24px em passos de 2
- [ ] Textarea aplica inline style lido do settings

### 13.5 Configuração de modelos
- [ ] Settings `ai.main_model`, `ai.fast_model`, `ai.embedding_model`, `ai.reasoning_model`
- [ ] Worker lê settings da API na inicialização (fallback para env)
- [ ] `GET /api/v1/ollama/models` — proxy para `{OLLAMA_BASE_URL}/api/tags` listando modelos disponíveis

### 13.6 Frequência do watcher/autopilot
- [ ] Setting `automation.watcher_interval_seconds`
- [ ] Setting `automation.autopilot_interval_minutes`

### 13.7 Testes
- [ ] `tests/test_settings_ui.py`: testa persistência e leitura de settings de tema, accent, densidade, fonte

---

## Bloco 14 - Segurança Local

**Arquivos alvo:**
- `apps/api/src/berrybrain_api/main.py` (CORS, auth)
- `apps/api/src/berrybrain_api/auth.py` (novo, opcional)
- `docs/security.md` (novo)
- `.env.example`

### 14.1 Revisão de chamadas externas
- [ ] Auditar todo código: confirmar que nenhuma chamada HTTP sai para cloud
- [ ] Documentar no código com comentário `# LOCAL ONLY: no external calls`

### 14.2 Bloqueio documentado
- [ ] `docs/security.md` explicando que todas as operações são locais:
  - API roda no Raspberry Pi
  - Worker roda no PC Windows (ou mesmo Pi)
  - Ollama roda localmente
  - Nenhum dado sai da rede local

### 14.3 Autenticação local opcional
- [ ] Setting `security.auth_enabled: bool` (default false)
- [ ] Se ativado: `POST /api/v1/auth/login` com `{password}` (senha única configurada no .env `BERRYBRAIN_AUTH_PASSWORD`)
- [ ] Middleware FastAPI que verifica header `Authorization: Bearer <token>` em todas as rotas exceto `/health`
- [ ] Token JWT simples com `python-jose` ou token aleatório armazenado em settings

### 14.4 CORS restrito
- [ ] Substituir `allow_origins=["*"]` por `allow_origins` lido de setting `security.allowed_origins` (default `["http://localhost:3000"]`)

### 14.5 Proteção da API local
- [ ] Rate limiting simples: middleware que conta requests por IP, bloqueia após 100/min
- [ ] Validação de `note_path` contra path traversal (`../`, symlinks)
- [ ] Limite de tamanho de request body (10MB)

### 14.6 Orientação Ollama
- [ ] Documentar que `OLLAMA_HOST` deve ser `127.0.0.1` (nunca `0.0.0.0`) para evitar exposição na rede

### 14.7 Testes
- [ ] `tests/test_security.py`: path traversal bloqueado, rate limit funciona, CORS headers corretos, auth middleware bloqueia não autenticados

---

## Bloco 15 - Backup e Restore

**Arquivos alvo:**
- `apps/api/src/berrybrain_api/backup.py` (novo)
- `apps/api/src/berrybrain_api/main.py` (novos endpoints)
- `scripts/backup.sh` (novo)

### 15.1 Backup do vault
- [ ] `POST /api/v1/backup/vault` — cria `.tar.gz` do diretório vault em `data/backups/vault_YYYYMMDD_HHMMSS.tar.gz`
- [ ] Exclui `anexos/` se > 100MB (opcional)

### 15.2 Backup do SQLite
- [ ] `POST /api/v1/backup/database` — copia `berrybrain.db` para `data/backups/berrybrain_YYYYMMDD_HHMMSS.db`
- [ ] Usa SQLite backup API (`connection.backup()`) para cópia consistente

### 15.3 Backup de metadata
- [ ] `POST /api/v1/backup/metadata` — exporta `generated_metadata`, `embeddings`, `connections`, `flashcards`, `insights` como JSON em `data/backups/metadata_YYYYMMDD_HHMMSS.json`

### 15.4 Snapshot antes de automações
- [ ] Antes de qualquer job que modifique metadata em massa, worker chama `POST /api/v1/backup/metadata`
- [ ] Snapshot rotacionado (manter últimos 5)

### 15.5 Restore
- [ ] `POST /api/v1/backup/restore` — body: `{backup_id: "vault_20260707_120000.tar.gz"}`
- [ ] Restaura vault do tar.gz (sobrescreve arquivos existentes, não deleta extras)
- [ ] `POST /api/v1/backup/restore/database` — restaura SQLite de backup (requer reinicialização da API)
- [ ] `POST /api/v1/backup/restore/metadata` — importa JSON de metadata (upsert)

### 15.6 Exportação completa
- [ ] `GET /api/v1/backup/export` — baixa um `.zip` com vault + database + metadata combinados

### 15.7 Listagem de backups
- [ ] `GET /api/v1/backup/list` — lista backups existentes com tipo, tamanho, data

### 15.8 Script CLI
- [ ] `scripts/backup.sh`: script bash que chama endpoints de backup, útil para cron jobs

### 15.9 Testes
- [ ] `tests/test_backup.py`: cria backup vault/db/metadata, verifica arquivo existe, restore vault, export zip

---

## Bloco 16 - Observabilidade Completa

**Arquivos alvo:**
- `apps/api/src/berrybrain_api/main.py` (endpoints agregados)
- `apps/api/src/berrybrain_api/observability.py` (novo)
- `apps/web/src/app/page.tsx` (dashboard home)
- `apps/web/src/components/job-dashboard.tsx` (novo)
- `apps/web/src/components/error-feed.tsx` (novo)

### 16.1 Dashboard de jobs
- [ ] `GET /api/v1/jobs/stats` — `{pending, running, completed, failed, total}`
- [ ] `GET /api/v1/jobs/recent?limit=20` — últimos jobs com detalhes
- [ ] `GET /api/v1/jobs?status=failed&limit=50` — filtrar por status
- [ ] Componente `job-dashboard.tsx`: cards de stats + tabela filtrável

### 16.2 Logs de IA
- [ ] `GET /api/v1/automation-logs?action_type=OLLAMA_GENERATE&limit=50` — filtrar por tipo
- [ ] `GET /api/v1/automation-logs/stats` — contagem por action_type

### 16.3 Status do worker
- [ ] `GET /api/v1/worker/status` (Bloco 1) já cobre
- [ ] Componente visual: indicador verde/amarelo/vermelho + uptime + jobs processados

### 16.4 Status do Ollama
- [ ] `GET /api/v1/ollama/status` — proxy health check + lista modelos carregados
- [ ] Worker reporta status do Ollama no heartbeat

### 16.5 Erros recentes
- [ ] `GET /api/v1/jobs?status=failed&order=completed_at&limit=10`
- [ ] Componente `error-feed.tsx`: lista de erros com job type, nota, mensagem truncada, timestamp

### 16.6 Filtros
- [ ] Jobs: por status, type, note_path (parcial), data
- [ ] Logs: por action_type, target_type, data
- [ ] Na UI: dropdown de filtro + input de busca textual

### 16.7 Testes
- [ ] `tests/test_observability.py`: endpoint stats retorna contagens corretas, filtros funcionam

---

## Bloco 17 - Testes de Integração

**Arquivos alvo:**
- `apps/api/tests/test_integration_*.py` (novos)
- `apps/web/` (testes E2E opcionais com Playwright)

### 17.1 Teste API CRUD + jobs
- [ ] `test_integration_crud_jobs.py`: cria nota via API → verifica job PARSE_NOTE criado → worker processa → verifica completed

### 17.2 Teste watcher + scan
- [ ] `test_integration_watcher.py`: cria arquivo .md no vault → espera watcher detectar → verifica NoteRecord criado + job enfileirado

### 17.3 Teste worker + job fake
- [ ] `test_integration_worker_loop.py`: mock API com httpx, worker loop processa job, verifica complete/fail
- [ ] Job tipo `TEST_JOB` que worker processa sem Ollama (só ecoa payload)

### 17.4 Teste Ollama gateway mockável
- [ ] `test_integration_ollama.py`: mock server HTTP que responde como Ollama `/api/generate` e `/api/embeddings`
- [ ] Worker chama gateway → verifica resposta parseada corretamente

### 17.5 Teste pipeline autopilot
- [ ] `test_integration_pipeline.py`: workflow completo — cria nota → scan → pipeline jobs criados → worker processa sequencial → verifica metadata, embeddings, connections, flashcards

### 17.6 Teste web build
- [ ] `npm run build` no `apps/web` — verifica que compila sem erros
- [ ] (Opcional) Playwright: smoke test — página carrega, lista notas, abre uma nota

---

## Bloco 18 - Polimento de Produto

**Arquivos alvo:**
- `apps/web/src/components/` (vários)
- `apps/web/src/app/globals.css`
- `apps/web/src/app/layout.tsx`

### 18.1 Empty states
- [ ] Vault vazio: mensagem "Nenhuma nota ainda. Crie sua primeira nota ou coloque arquivos .md na pasta vault/inbox."
- [ ] Sem jobs: "Nenhum job pendente. O autopilot está em dia."
- [ ] Sem conexões: "Nenhuma conexão encontrada para esta nota."
- [ ] Sem insights: "Nenhum insight no momento. Novas análises aparecerão aqui."
- [ ] Sem flashcards: "Nenhum flashcard gerado para esta nota ainda."

### 18.2 Loading states
- [ ] Skeleton cards para lista de notas (pulsing gray rectangles)
- [ ] Skeleton para conteúdo da nota (linhas de texto pulsando)
- [ ] Spinner no botão "Scan vault" e "Salvar"
- [ ] Progresso de geração IA: "Assimilando nota... (etapa 2/5)"

### 18.3 Error states
- [ ] Toast/notificação para erros de rede ("API indisponível")
- [ ] Mensagem inline quando nota não encontrada
- [ ] Botão "Tentar novamente" em operações que falharam
- [ ] Fallback quando Ollama offline: "Ollama não está rodando. Inicie o Ollama no PC Windows."

### 18.4 Responsividade
- [ ] Mobile (< 768px): single column, sidebar vira drawer/modal
- [ ] Tablet (768-1024px): two column (lista + conteúdo)
- [ ] Desktop (> 1024px): three column atual
- [ ] Ajustar Tailwind breakpoints nos componentes

### 18.5 Acessibilidade básica
- [ ] Labels em inputs e botões
- [ ] Focus visible em todos elementos interativos
- [ ] Alt text em ícones (quando não decorativos)
- [ ] Role attributes em regiões (nav, main, aside)
- [ ] Keyboard navigation: Tab entre nota e editor, Escape fecha modais
- [ ] `prefers-reduced-motion`: desabilita animações e transições

### 18.6 Atalhos de teclado
- [ ] `Cmd/Ctrl + K`: abrir command palette (busca)
- [ ] `Cmd/Ctrl + S`: salvar nota atual
- [ ] `Cmd/Ctrl + N`: nova nota
- [ ] `Cmd/Ctrl + Shift + F`: buscar em todas as notas
- [ ] `Escape`: fechar modal/voltar ao home

### 18.7 Command palette
- [ ] Componente unificado de busca + navegação (Bloco 6 + este)
- [ ] Resultados: notas, comandos (Nova nota, Scan vault, Abrir settings)
- [ ] Navegação por setas + Enter

### 18.8 Refinamento visual final
- [ ] Transições suaves: fade in para painéis, slide para sidebar mobile
- [ ] Consistência de espaçamento (auditar padding/margin)
- [ ] Tipografia: hierarquia clara (h1 > h2 > h3 > body > caption)
- [ ] Micro-interações: hover em notas, botão salvar pulsando quando dirty
- [ ] Favicon e título da página: "BerryBrain"

### 18.9 Testes
- [ ] `npm run lint` sem erros
- [ ] `npm run build` sem warnings
- [ ] Verificação manual: fluxo criar nota → editar → salvar → ver autopilot → revisar flashcards
