# Planing V3 - Auditoria de bugs, logica e produto do BerryBrain

Data: 2026-07-08

Escopo:
- Projeto local: `\\192.168.3.36\Public\Antigravity\berrybrain`.
- API FastAPI em `apps/api`.
- Worker Python em `apps/worker`.
- Frontend Next/React em `apps/web`.
- Banco real em `data/sqlite/berrybrain.db`.
- Comparacao com Obsidian usando fontes oficiais consultadas em 2026-07-08.

## Veredito curto

O BerryBrain ainda nao e um segundo cerebro melhor que Obsidian.

Ele ja tem uma ideia mais ambiciosa em um ponto especifico: IA local/cloud para assimilar notas, extrair conceitos, sugerir conexoes e gerar um grafo de conhecimento com evidencia. Essa direcao pode superar o Obsidian para estudo ativo e revisao assistida por IA.

Mas, no estado atual, o BerryBrain perde para o Obsidian como produto real. O pipeline automatico e instavel, muitos jobs falham, ha jobs presos, a busca e limitada, a revisao/flashcards esta inconsistente, o scanner do vault quebra em Windows, a seguranca padrao e fraca, e nao ha ecossistema equivalente a plugins, mobile, sync, web clipper, canvas maduro e confiabilidade diaria.

Conclusao operacional:
- Como prototipo local com grafo e IA: promissor.
- Como segundo cerebro de uso diario: ainda nao.
- Como alternativa melhor que Obsidian hoje: nao.
- Como produto que pode ficar melhor que Obsidian em um nicho de "segundo cerebro automatico com IA local": sim, se os P0/P1 deste plano forem resolvidos.

## Evidencias executadas

### Estrutura

Arquivos principais encontrados:
- `apps/api/src/berrybrain_api/main.py`
- `apps/api/src/berrybrain_api/jobs.py`
- `apps/api/src/berrybrain_api/second_brain.py`
- `apps/api/src/berrybrain_api/services.py`
- `apps/api/src/berrybrain_api/vault_scan.py`
- `apps/worker/src/berrybrain_worker/main.py`
- `apps/web/src/contexts/workspace-context.tsx`
- `apps/web/src/components/home/home-view.tsx`
- `apps/web/src/components/graph-screen.tsx`

### Verificacoes

- `python -X pycache_prefix=C:\tmp\berrybrain-pycache -m compileall -q apps\api\src apps\worker\src`: passou.
- `python -m pytest`: nao estava disponivel no Python do host.
- `npm run typecheck` e `npm run build`: nao rodaram porque `npm`/`node` nao estao no PATH do host.
- Criei um venv temporario em `C:\tmp\berrybrain-venv` para rodar `unittest` sem alterar o repositorio.
- API tests com `unittest`: 52 testes, 2 falhas e 4 erros.
- Worker tests com `unittest`: 1 teste, passou.

Falhas de teste relevantes:
- `test_jobs.py` e `test_automation_logs.py` esperam 6 jobs, mas o pipeline atual cria 12. Os testes ficaram defasados.
- `test_vault_scan.py`, `test_vault_watcher.py` e `test_integration.py` quebram no Windows por diferenca entre caminho curto `MTZ-AD~1` e caminho longo `mtz-admin` em `vault_scan.py:31`.
- `test_integration.py` tambem deixa SQLite travado no cleanup, indicando vazamento/engine aberta em teste.

### Estado real do banco

Banco consultado: `data/sqlite/berrybrain.db`.

Contagens:
- `notes`: 21
- `jobs`: 404
- `concepts`: 33
- `connections`: 1
- `graph_nodes`: 104
- `graph_edges`: 118
- `insights`: 4
- `flashcards`: 21
- `generated_metadata`: 27
- `embeddings`: 2
- `automation_logs`: 399
- `worker_status`: 1

Status dos jobs:
- `completed`: 145
- `failed`: 257
- `running`: 2

Jobs presos:
- `ASSIMILATE_NOTE`, id 27, `running`, attempts 2/2, erro anterior `Expecting value`.
- `CLASSIFY_NOTE`, id 41, `running`, attempts 2/2, erro anterior `Expecting value`.

Falhas recentes:
- `EXPAND_KNOWLEDGE_GRAPH`: 500 da API.
- `GENERATE_EMBEDDING`: Ollama embedding connection failed.
- `EXTRACT_CONTEXT`, `DETECT_TOPICS`, `EXTRACT_ENTITIES`, `EXTRACT_CONCEPTS`, `ASSIMILATE_NOTE`: JSON invalido.
- `CLASSIFY_NOTE`: cloud response sem `content`.

Estado do grafo:
- Nos por tipo: `concept` 33, `topico` 22, `entidade` 22, `note` 20, `insight` 4, `lacuna` 2, `contexto` 1.
- Arestas por tipo: `related` 53, `shared_concept` 35, `shared_context` 30.
- `connections` persistidas: apenas 1.

Interpretacao:
- O grafo visual existe e ja tem dados, mas grande parte das arestas nao vem da tabela de conexoes explicaveis entre notas.
- O pipeline esta produzindo algum conhecimento, mas com taxa de falha alta demais para uso confiavel.

## Comparacao com Obsidian

Fontes oficiais consultadas:
- Obsidian overview: https://obsidian.md/
- Graph view: https://obsidian.md/help/plugins/graph
- Backlinks: https://obsidian.md/help/plugins/backlinks
- Canvas: https://obsidian.md/help/plugins/canvas
- Pricing/Sync/Publish: https://obsidian.md/pricing
- Web Clipper: https://obsidian.md/clipper

O que o Obsidian ja entrega oficialmente:
- Notas locais e privadas em arquivos Markdown.
- Links, backlinks, mencoes nao linkadas e grafo visual.
- Canvas visual com arquivos `.canvas` em formato aberto JSON Canvas.
- Sync opcional com criptografia ponta a ponta, historico de versoes e colaboracao paga.
- Publish pago com busca e grafo.
- Web Clipper oficial para salvar paginas, metadata, destaques e templates em Markdown.
- Ecossistema grande de plugins e temas.
- Apps desktop e mobile.

Onde o BerryBrain pode ser melhor:
- Assimilacao automatica de notas por IA.
- Extracao de conceitos, entidades, topicos, lacunas e insights.
- Grafo que tenta ir alem de backlinks manuais.
- Pipeline local com Ollama e opcao cloud OpenAI-compatible.
- Home como centro de controle do processamento.
- Possibilidade de usar evidencia, confidence, provider/model e status por no/conexao.

Onde o BerryBrain esta pior hoje:
- Menos confiavel: 257 jobs falhos em 404.
- Menos maduro como editor.
- Sem mobile, sync maduro, web clipper, importadores, plugins e canvas equivalente.
- Busca nao e realmente hibrida/semantica no endpoint atual.
- Revisao/flashcards esta inconsistente entre API, worker e testes.
- Autopilot nao tem garantia de ordem, idempotencia e recuperacao total.
- Dados de IA podem virar "conhecimento" com pouca validacao ou evidencia fraca.

Veredito de produto:
- Obsidian e melhor como segundo cerebro geral hoje.
- BerryBrain so sera melhor se assumir um posicionamento diferente: "segundo cerebro local que trabalha enquanto voce escreve, explica conexoes e transforma notas em estudo ativo".
- Para vencer Obsidian, BerryBrain nao deve copiar tudo. Deve ser excelente no que Obsidian nao faz nativamente: assimilacao automatica, grafo semantico explicavel, revisao gerada de fontes reais e agente local transparente.

## Bugs e falhas criticas

### P0. Jobs presos com tentativas esgotadas nao sao recuperados

Evidencia:
- Banco: 2 jobs `running` com attempts 2/2.
- `apps/api/src/berrybrain_api/jobs.py:149-150` recupera apenas jobs `running` com `attempts < max_attempts`.

Problema:
- Se um job fica `running` e ja esta com tentativas esgotadas, ele nunca volta para `pending` nem vira `failed`.
- Isso deixa o sistema mentindo que ainda esta processando.

Acao:
- Alterar `recover_stale_running_jobs` para:
  - se stale e `attempts < max_attempts`: voltar para `pending`;
  - se stale e `attempts >= max_attempts`: marcar `failed`;
  - registrar automation log de recuperacao.

Criterio de aceite:
- Nenhum job pode ficar `running` alem do lease sem heartbeat.
- Teste cobre stale com attempts abaixo e igual ao maximo.

### P0. Pipeline executa etapas dependentes em paralelo

Evidencia:
- `apps/worker/src/berrybrain_worker/main.py:66` reclama ate 4 jobs por loop.
- O pipeline e enfileirado em ordem em `apps/api/src/berrybrain_api/jobs.py:64`, mas nao ha dependencias.

Problema:
- Para a mesma nota, jobs como `PARSE_NOTE`, `CLASSIFY_NOTE`, `ASSIMILATE_NOTE` e `EXTRACT_CONCEPTS` podem rodar ao mesmo tempo.
- `EXPAND_KNOWLEDGE_GRAPH` pode rodar antes de conceitos/entidades/contexto existirem.
- Resultado: grafo parcial, falhas JSON, jobs duplicados e progresso falso.

Acao:
- Implementar DAG por nota ou `depends_on`.
- Bloquear proxima etapa ate a anterior estar `completed` para o mesmo `note_path` e `content_hash`.
- Permitir paralelismo apenas entre notas diferentes ou etapas explicitamente independentes.

Criterio de aceite:
- Criar/editar uma nota gera pipeline linear observavel.
- `graph/expand` so roda depois de metadata minima existir.
- Teste comprova ordem por nota.

### P0. Taxa de falha do Autopilot e inaceitavel

Evidencia:
- Banco: 257 jobs falhos de 404.
- Falhas por tipo mostram `ASSIMILATE_NOTE` 42 falhas, `CLASSIFY_NOTE` 42 falhas, `GENERATE_EMBEDDING` 43 falhas, `GENERATE_FLASHCARDS` 22 falhas.

Problema:
- O sistema parece ativo, mas a maior parte dos jobs de IA falhou.
- Um segundo cerebro precisa ser confiavel e explicar falhas claramente.

Acao:
- Criar painel de erro por causa raiz: provider offline, JSON invalido, endpoint ausente, 500, timeout.
- Adicionar reparo de JSON ou schema validator com retry orientado.
- Distinguir `provider_unavailable`, `invalid_ai_response`, `api_contract_error`, `dependency_waiting`.

Criterio de aceite:
- Home mostra "o que falhou e como corrigir".
- Jobs falhos sao agrupados por causa e nota.

### P0. Flashcards/revisao estao quebrados por contrato inconsistente

Evidencia:
- `apps/worker/src/berrybrain_worker/main.py:154` completa `GENERATE_FLASHCARDS` sem chamar `process_generate_flashcards`.
- `persist_flashcards` chama `/api/v1/flashcards/{path}` em `apps/worker/src/berrybrain_worker/main.py:211`.
- Nao existe router `/api/v1/flashcards`.
- Existe `routers/review.py`, mas ele nao e incluido em `main.py:90-100`.
- `apps/api/tests/test_integration.py:160` espera que flashcards/review estejam removidos, enquanto `apps/worker/tests/test_worker_flashcards.py` espera persistencia em `/flashcards`.

Problema:
- O projeto tem tres verdades conflitantes:
  - banco possui flashcards;
  - worker tem funcao de gerar;
  - API publica nao monta review nem flashcards.
- Usuario nao pode confiar que revisao funciona.

Decisao necessaria:
- Ou remover revisao/flashcards do produto por enquanto.
- Ou reativar oficialmente com endpoints consistentes.

Recomendacao:
- Se o objetivo e "melhor que Obsidian para estudo", manter revisao e flashcards como diferencial.
- Criar `POST /api/v1/flashcards/{note_path}` e montar `review.router`.
- Corrigir `process_job` para chamar `process_generate_flashcards`.

Criterio de aceite:
- Nota nova gera flashcards reais.
- `/api/v1/review/today` retorna cards vencidos.
- Testes de API e worker concordam.

### P0. Embedding cloud e descartado e sempre substituido por Ollama

Evidencia:
- `apps/worker/src/berrybrain_worker/main.py:494` gera embedding cloud.
- `apps/worker/src/berrybrain_worker/main.py:511` chama Ollama no `else` quando `vec` ja existe.

Problema:
- Mesmo com cloud configurado e sucesso, o worker descarta `vec` cloud e chama Ollama.
- Se Ollama estiver offline, embedding falha apesar da cloud ter funcionado.

Acao:
- Remover o `else` que substitui `vec`.
- Persistir `model`/`provider` real no endpoint de embeddings.

Criterio de aceite:
- Teste com cloud mockada confirma que Ollama nao e chamado quando cloud retorna vetor.

### P0. Writes importantes ignoram resposta HTTP

Evidencia:
- `upsert_metadata` em `apps/worker/src/berrybrain_worker/main.py:183` faz `PUT`, mas nao chama `raise_for_status`.
- `connections/sync` em `apps/worker/src/berrybrain_worker/main.py:606` nao valida resposta.
- `process_generate_inferred_connections` em `apps/worker/src/berrybrain_worker/main.py:966` faz POST sem payload para endpoint que exige body e engole erro.

Problema:
- Jobs podem ser marcados como completos mesmo quando a API recusou a escrita.
- Isso cria grafo/home inconsistentes.

Acao:
- Toda mutacao HTTP do worker precisa `raise_for_status`.
- Endpoints de sync devem retornar contagens validadas.
- Jobs devem falhar quando persistencia falha.

Criterio de aceite:
- Teste simula 422/500 da API e o job termina `failed`, nao `completed`.

### P0. Scanner do vault quebra em Windows

Evidencia:
- Testes falham em `apps/api/src/berrybrain_api/vault_scan.py:31`.
- Erro: caminho curto `C:\Users\MTZ-AD~1\...` nao e subpath de `C:\Users\mtz-admin\...`.

Problema:
- Em Windows/NAS, scan e watcher podem quebrar por normalizacao de caminho.
- Como o usuario esta em workspace Windows/UNC, isso e risco real.

Acao:
- Normalizar root e path com a mesma estrategia antes de calcular relativo.
- Preferir `os.path.relpath(path, vault_path)` com normalizacao de case, ou resolver ambos via API de caminho longo.
- Adicionar teste Windows-like com path curto/long path.

Criterio de aceite:
- `vault_scan` passa em Windows.
- `VaultWatcher.run_once` nao derruba o loop.

### P0. Endpoint destrutivo reset ignora confirmacao

Evidencia:
- `apps/api/src/berrybrain_api/main.py:213` define `/api/v1/system/reset`.
- A classe `_Reset` com `confirm` e declarada em `main.py:224`, mas nao e usada como parametro.
- `drop_all` e `rmtree` ocorrem em `main.py:235-245`.

Problema:
- O frontend envia confirmacao, mas a API nao valida payload.
- Se `BERRYBRAIN_API_TOKEN` estiver vazio, qualquer POST local autorizado pela rede pode apagar dados.

Acao:
- Exigir body `{"confirm":"berrybrain-reset-all"}`.
- Exigir token mesmo em ambiente local para reset.
- Mover reset para router/admin com protecao dupla.

Criterio de aceite:
- POST sem confirmacao retorna 400.
- POST sem token retorna 401 quando token configurado.
- Teste cobre reset.

### P0. Autenticacao protege apenas metodos nao-GET

Evidencia:
- `apps/api/src/berrybrain_api/main.py:76` ignora token para `GET`.
- `.env.example` e `.env.prod.example` deixam `BERRYBRAIN_API_TOKEN=` e `BERRYBRAIN_CORS_ORIGINS=*`.

Problema:
- Com API exposta na rede, qualquer cliente pode ler notas, grafo, insights, settings e dados pessoais via GET.
- Para um segundo cerebro, leitura e tao sensivel quanto escrita.

Acao:
- Proteger GET tambem, exceto `/health`.
- Em prod, `BERRYBRAIN_API_TOKEN` deve ser obrigatorio.
- CORS deve ser restrito ao host do frontend.

Criterio de aceite:
- GET `/api/v1/notes` sem token retorna 401 em modo protegido.
- CORS `*` nao e padrao de prod.

## Falhas de logica do segundo cerebro

### Conceitos estao poluidos por lacunas e frases longas

Evidencia:
- Banco tem conceitos como:
  - `falta conexao com conceitos de ciencia de dados...`
  - `nao ha mencao a desafios praticos...`
- `second_brain.py` extrai `gaps` como conceitos em `_extract_note_concepts`.

Problema:
- Lacuna nao e conceito.
- Isso suja o grafo, cria nos ruins e prejudica inferencia.

Acao:
- Separar `concept`, `gap`, `question`, `topic`, `entity`.
- Gaps devem virar `GraphNodeRecord(type="lacuna")`, nao `ConceptRecord`.
- Criar normalizador e validador de conceito: tamanho, classe semantica, stopwords, frases negativas.

Criterio de aceite:
- Frases de lacuna nao aparecem em `/api/v1/concepts`.
- Lacunas aparecem na secao correta.

### Grafo tem muitas arestas, mas poucas conexoes de conhecimento persistidas

Evidencia:
- `graph_edges`: 118.
- `connections`: 1.

Problema:
- O grafo visual parece rico, mas o modelo de conexoes explicaveis entre notas ainda e pobre.
- Arestas `related` geradas para tipos auxiliares nao substituem relacoes fortes nota-nota/conceito-nota.

Acao:
- Definir claramente:
  - `GraphEdgeRecord`: aresta visual/grafo vivo.
  - `ConnectionRecord`: relacao auditavel entre notas/conceitos com decisao do usuario.
- Toda aresta importante deve ter origem, evidencia, confidence, status e caminho de confirmacao.

Criterio de aceite:
- Duas notas relacionadas geram `ConnectionRecord` com reason/evidence.
- Confirmar/ignorar no grafo reflete no modelo de conexao quando aplicavel.

### Expansao do grafo tem dedupe fraco e perde relacoes

Evidencia:
- `second_brain.py:270-271` verifica se ja existe qualquer edge entre typed node e note, ignorando tipo/direcao/label.
- Funcoes de extracao usam `seen = set()` global por execucao, por exemplo `second_brain.py:1200`, `1273`, `1344`, `1408`, `1460`.

Problema:
- Se ja existe uma aresta entre dois nos, outra relacao valida pode ser bloqueada.
- Se o mesmo topico/entidade aparece em varias notas, a extracao pode ignorar a segunda ocorrencia e nao atualizar `source_note_ids`.

Acao:
- Dedupe por `(source, target, type, source_note_ids)` ou regra explicita.
- Para typed nodes, upsert por normalizacao e sempre atualizar frequencia/source_note_ids/evidence.

Criterio de aceite:
- Mesmo topico em 3 notas vira 1 no com 3 source notes, nao duplicata nem perda.

### Busca chamada de "hybrid" nao usa conteudo nem embeddings de forma real

Evidencia:
- `main.py` aceita `mode="hybrid"`, mas chama `text_search`.
- `search.py` cria FTS com `content='notes'`, mas a tabela `notes` nao tem coluna de conteudo; o FTS indexa basicamente title.
- `process_find_connections` busca candidatos por titulo da nota.

Problema:
- Conexoes semanticamente boas dependem de busca real por conteudo/embedding.
- Hoje o worker procura candidatos fracos, especialmente quando titulos nao compartilham termos.

Acao:
- Persistir conteudo indexavel ou snippets em FTS.
- Implementar busca hibrida real: FTS + embedding cosine + backlinks + conceitos compartilhados.
- `FIND_CONNECTIONS` deve receber candidatos com trecho de evidencia.

Criterio de aceite:
- Buscar termo presente no corpo da nota retorna a nota.
- Duas notas relacionadas por conteudo, nao titulo, entram como candidatas.

### Reprocessar nota no painel direito envia payload invalido

Evidencia:
- `apps/web/src/components/panel/right-panel.tsx:62` faz `PUT /notes/{path}` com body `{ reprocess: true }`.
- `UpdateNoteRequest` em `routers/notes.py` exige `content: str`.

Problema:
- Botao "Reprocessar" pode retornar 422 e a UI ignora o erro.

Acao:
- Criar endpoint `POST /api/v1/notes/{path}/reprocess`.
- UI deve chamar endpoint correto e mostrar sucesso/falha.

Criterio de aceite:
- Botao reprocessar cria jobs novos sem alterar conteudo.

### Remover/renomear nota nao limpa grafo, metadata e backlinks

Evidencia:
- `delete_note_endpoint` chama `remove_note_record`, mas nao apaga metadata, embeddings, flashcards, connections, graph nodes/edges.
- `rename_note_endpoint` remove o registro antigo e sincroniza o novo, mas nao atualiza backlinks.

Problema:
- O grafo pode ficar com nos/arestas orfaos ou apontando para nota antiga.
- Links Markdown `[[...]]` nao sao atualizados.

Acao:
- Criar servico de lifecycle de nota:
  - delete: cascade controlado;
  - rename: atualizar `NoteRecord`, backlinks, graph metadata, connections e generated metadata por note_id;
  - logar acao reversivel.

Criterio de aceite:
- Renomear nota preserva note_id ou migra referencias.
- Deletar nota remove/arquiva dependencias associadas.

## Falhas de produto e UX

### Home ja melhorou, mas progresso pode ser enganoso

Evidencia:
- `home_summary.py` calcula progresso usando todos os jobs historicos.
- Banco tem 257 falhos antigos e 145 completos.

Problema:
- Percentual de progresso mistura passado, fila atual e falhas antigas.
- Usuario nao sabe "esta nota esta pronta?" nem "o sistema esta saudavel agora?".

Acao:
- Separar:
  - progresso atual da fila;
  - saude historica;
  - progresso por nota;
  - jobs falhos ativos que precisam decisao.

Criterio de aceite:
- Home responde em linguagem clara: "processando X", "falhou Y", "pronto Z".

### Editor ainda nao tem maturidade de Obsidian

Faltas:
- Backlinks in-document.
- Mencoes nao linkadas.
- Rename com atualizacao de links.
- Pane multiplo/tab real.
- Busca por corpo.
- Templates robustos.
- Import/web clipper.
- Mobile/offline distribuido.
- Plugin API.

Acao:
- Nao tentar copiar tudo no curto prazo.
- Priorizar editor estavel, links/backlinks, busca e captura.

### Dados aparecem com encoding quebrado em docs/UI antigas

Evidencia:
- Arquivos de auditoria existentes mostram `nÃ£o`, `cÃ©rebro`, etc.

Problema:
- Isso passa impressao de produto quebrado e dificulta leitura.

Acao:
- Padronizar UTF-8.
- Corrigir documentos gerados antigos ou recria-los.
- Garantir headers/encoding no ambiente Windows/NAS.

## Roadmap priorizado

### Fase 0 - Estancar confiabilidade

Objetivo: parar de acumular estado falso.

Tarefas:
1. Corrigir stale jobs esgotados.
2. Implementar lease/heartbeat por job.
3. Proibir etapas paralelas da mesma nota.
4. Fazer worker validar todos os writes HTTP.
5. Corrigir embedding cloud.
6. Corrigir `vault_scan` em Windows.
7. Corrigir reset com confirmacao obrigatoria.
8. Proteger GETs sensiveis com token.

Aceite:
- Zero jobs `running` stale.
- Scan passa no Windows.
- Pipeline de uma nota nao roda fora de ordem.
- API tests passam sem falhas P0.

### Fase 1 - Contratos de API coerentes

Objetivo: alinhar worker, API, testes e UI.

Tarefas:
1. Decidir oficialmente se flashcards/review ficam no produto.
2. Se ficarem:
   - montar `review.router`;
   - criar endpoint de persistencia de flashcards;
   - chamar `process_generate_flashcards`;
   - atualizar testes.
3. Criar endpoint `POST /notes/{path}/reprocess`.
4. Criar contratos typed para `home/summary`, `graph`, `connections`, `concepts`.
5. Atualizar testes que ainda esperam pipeline de 6 jobs.

Aceite:
- Testes nao contradizem produto.
- Worker nao chama endpoints inexistentes.

### Fase 2 - Grafo semantico limpo

Objetivo: transformar grafo visual em conhecimento auditavel.

Tarefas:
1. Separar conceito, topico, entidade, lacuna, pergunta, insight.
2. Impedir frases longas/lacunas em `ConceptRecord`.
3. Corrigir dedupe e source_note_ids.
4. Criar conexoes nota-nota e nota-conceito com evidence real.
5. Reprocessar o banco atual para limpar conceitos ruins.
6. Adicionar endpoint de rebuild com dry-run.

Aceite:
- `/concepts` retorna conceitos limpos.
- `/connections` tem mais que uma conexao real quando notas compartilham conhecimento.
- Grafo mostra por que cada no/aresta existe.

### Fase 3 - Busca e inferencia reais

Objetivo: fazer o BerryBrain responder perguntas com base no vault.

Tarefas:
1. Indexar corpo das notas em FTS.
2. Usar embeddings em busca hibrida.
3. Candidatos de conexao devem trazer snippet/evidence.
4. `graph/infer` deve citar notas/conexoes.
5. Resposta sem evidencia deve ser comum e clara, nao fallback generico.

Aceite:
- Pergunta sobre um tema no corpo da nota retorna evidencia.
- Inferencia salva insight com source nodes e source notes.

### Fase 4 - Produto melhor que Obsidian em IA local

Objetivo: competir onde o Obsidian nao e nativo.

Tarefas:
1. Inbox que assimila automaticamente.
2. Criacao de nota permanente a partir de conceito/lacuna.
3. Revisao espacada gerada com evidencias.
4. Trilhas de estudo por lacunas e conexoes.
5. Painel "o que aprendi esta semana?".
6. Auditoria de IA por provider/model/prompt/custo/tempo.

Aceite:
- O usuario escreve notas soltas e recebe conceitos, conexoes, lacunas, revisoes e trilhas sem configurar manualmente links.
- Cada sugestao pode ser confirmada, ignorada ou transformada em nota.

### Fase 5 - Paridade minima com Obsidian

Objetivo: nao perder por falta de fundamentos.

Tarefas:
1. Backlinks e unlinked mentions.
2. Rename seguro com update de links.
3. Busca rapida no corpo inteiro.
4. Web clipper/importacao basica.
5. Sync/backup confiavel para NAS ou Git.
6. Plugin/script API simples.
7. Mobile ou PWA responsivo com uso offline.

Aceite:
- Migrar um vault Markdown do Obsidian nao perde links, tags ou estrutura.
- Usuario consegue trabalhar diariamente sem abrir Obsidian para tarefas basicas.

## Arquitetura recomendada

### Job engine

Criar campos:
- `lease_until`
- `heartbeat_at`
- `depends_on`
- `note_path`
- `content_hash`
- `stage`
- `provider`
- `model`
- `result_summary`

Regras:
- Job so pode completar se writes obrigatorios foram confirmados.
- Job stale com attempts esgotados vira `failed`.
- Jobs por nota respeitam ordem.
- Jobs de grafo global rodam depois de lote de notas, nao no meio de cada nota sem controle.

### Knowledge model

Separar:
- `Note`
- `Concept`
- `Topic`
- `Entity`
- `Gap`
- `Question`
- `Insight`
- `Source`
- `KnowledgeEdge`
- `ReviewItem`

Campos obrigatorios para item automatico:
- source note ids
- evidence
- confidence
- provider
- model
- prompt version
- status
- created_by
- reversible/action log

### API

Endpoints prioritarios:
- `POST /api/v1/notes/{path}/reprocess`
- `GET /api/v1/notes/{path}/backlinks`
- `GET /api/v1/search?mode=hybrid`
- `POST /api/v1/graph/rebuild?dry_run=true`
- `POST /api/v1/jobs/recover-stale`
- `GET /api/v1/jobs/health`
- `POST /api/v1/flashcards/{note_path}` se revisao ficar
- `GET /api/v1/review/today` se revisao ficar

### Frontend

Prioridades:
- Mostrar falhas e proximas acoes, nao so contadores.
- Reprocessar nota por endpoint correto.
- Mostrar evidencias e source notes sempre.
- Evitar botoes que parecem funcionar mas so disparam endpoint inexistente/invalido.
- Deixar Home focada em estudo e Monitor focado em tecnico.

## Matriz de decisao: BerryBrain vs Obsidian

| Area | Obsidian hoje | BerryBrain hoje | Como BerryBrain vence |
|---|---:|---:|---|
| Editor Markdown | Alto | Medio | Editor estavel, backlinks, rename seguro |
| Arquivos locais | Alto | Medio/Alto | Manter vault simples e interoperavel |
| Backlinks/grafo manual | Alto | Medio | Links reais + grafo semantico |
| Canvas visual | Alto | Baixo/Medio | Nao competir agora; foco em grafo inteligente |
| IA nativa | Baixo | Medio | Autopilot confiavel e explicavel |
| Revisao ativa | Plugin/dependente | Baixo/Quebrado | Flashcards/revisao com evidencia |
| Busca | Alto | Baixo/Medio | FTS corpo + embeddings |
| Sync/mobile | Alto | Baixo | NAS/Git/PWA ou sync proprio |
| Plugins/ecossistema | Muito alto | Baixo | API simples e integrações |
| Confiabilidade | Alto | Baixo/Medio | P0/P1 deste plano |

## Riscos de ideia/proposito

1. Tentar ser "Obsidian + IA" e amplo demais.
   - Melhor posicionamento: "segundo cerebro automatico local para estudo".

2. Grafo pode virar decoracao.
   - So vale se cada aresta tiver evidence, reason e acao.

3. IA pode gerar ruido.
   - Precisa status `suggested`, confirmacao, ignore e audit trail.

4. Automacao pode destruir confianca.
   - Jobs precisam ser previsiveis, recuperaveis e transparentes.

5. Local-first sem seguranca nao basta.
   - GETs, reset e CORS precisam ser tratados como dados privados.

## Proximo passo recomendado

Implementar primeiro a Fase 0.

Ordem exata:
1. Corrigir stale jobs esgotados.
2. Corrigir pipeline por dependencia/per-note lock.
3. Corrigir writes HTTP do worker com `raise_for_status`.
4. Corrigir embedding cloud.
5. Corrigir scan Windows.
6. Resolver decisao flashcards/review.
7. Proteger reset e GETs sensiveis.
8. Atualizar testes.

Depois disso, reprocessar uma copia do vault e medir:
- jobs criados;
- jobs concluidos;
- jobs falhos;
- conceitos limpos;
- conexoes reais;
- insights validos;
- tempo total;
- evidencias por item.

So depois dessa medicao vale investir em UI nova ou features grandes.

## Definicao de pronto para "melhor que Obsidian"

O BerryBrain so pode ser chamado de melhor que Obsidian quando:
- O usuario consegue escrever por dias sem perder dados.
- O pipeline automatico conclui acima de 95% dos jobs em ambiente normal.
- Toda falha e visivel e recuperavel.
- Busca encontra conteudo no corpo e por semantica.
- Backlinks e rename seguro funcionam.
- Grafo tem conexoes explicaveis, nao apenas layout bonito.
- IA gera insights e revisoes com evidence.
- Usuario consegue confirmar/ignorar conhecimento sugerido.
- Dados continuam em Markdown/local e exportaveis.
- Existe uma resposta clara para sync/backup/mobile.

Estado atual: ainda nao atende.
