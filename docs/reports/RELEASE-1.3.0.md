# BerryBrain v1.3.0 - Relatorio de maturidade e release candidate

Data da validacao: 2026-08-09  
Status: **release candidate local aprovado; publicacao remota aguardando autorizacao do mantenedor**

## 1. SHAs e escopo

- SHA base: `8a21e532bd6312f9b14bdcbf10a6d05e43c5327d`.
- SHA funcional final: `e9109cc277d40fafbd6a624b2ed68d4a756c14cd`.
- Versao: `1.3.0` em API, worker e web.
- Planejamento validado: `docs/planning/planejamento-performace-grafo.md`.
- Nenhum push, tag ou release remota foi feito sem autorizacao.

## 2. Causas-raiz e correcoes

| Problema | Causa-raiz | Correcao |
| --- | --- | --- |
| 4 rascunhos e 3 itens no grafo | O scan sincronizava notas e enfileirava jobs, mas a visualizacao podia ler o grafo antes do rebuild. | Pipeline e diagnostico alinhados; E2E confirma que um vault novo aparece apos scan. |
| Jobs antigos nao reprocessavam | Payload guardava `note_path`; renomear a nota invalidava o caminho mesmo com mesmo ID/hash. | Referencia canonica por ID/hash, refresh de caminho, supersede para conteudo ausente/alterado e reparo auditavel. |
| Ask retornava HTTP 500 | Configuracao parcial, contrato de erro opaco e falta de orquestracao grounded. | Setup obrigatorio, validacao por capability, respostas tipadas, recusas sem evidencia, Flow e persistencia de insight. |
| Lista de modelos vazia | URL/provider/model eram tratados como campos independentes e sem normalizacao comum. | Catalogo central da API, URL automatica por provider, descoberta de modelos e selecao explicita por slot. |
| Settings podia falhar com IDs numericos | Conversao inconsistente entre formulario, API e persistencia. | Contratos tipados e configuracao v2 atomica, com Cloud XOR Local. |
| HippoRAG era incompleto | Sidecar e worker nao fechavam index/delete/reconcile/rebuild por vault. | Ciclo real implementado, autenticado e coberto por testes. |
| Grafo degradava em escala | Payload monolitico e layout no main thread. | Endpoints progressivos, cursor, resumo, Web Worker de layout e budgets cold/warm. |
| Chaves i18n apareciam na UI | 39 chaves estaticas estavam ausentes nos dois idiomas. | Catalogos pt-BR/en completos e regressao que rejeita identificadores internos visiveis. |
| Worker saudavel aparecia offline | `/monitor/stats` nao retornava o heartbeat consumido pela sidebar. | Contrato API/frontend alinhado e regressao E2E com heartbeat recente. |
| Imagem HippoRAG tinha 2 CVEs HIGH | `setuptools 79.0.1` vendorizava `wheel` e `jaraco.context` vulneraveis. | `setuptools>=84.0.0`; novo scan Trivy com zero HIGH/CRITICAL corrigivel. |

## 3. Contadores antes e depois

- Fila antes do reparo: 53 `completed`, 73 `dead_letter`, 16 `superseded`.
- Fila final: 59 `completed`, 67 `dead_letter`, 16 `superseded`, 0 ativos.
- Seis jobs de nota renomeada foram reparados e concluidos.
- Os 67 jobs historicos restantes foram classificados e mantidos em quarentena:
  46 `invalid_payload`, 20 `semantic_source_changed`, 1 `graph_node_missing`.
- Estado real final: 1 nota sincronizada (`inbox/meu-portfolio.md`), 27 nos,
  64 conexoes, 2 orfaos, 7 clusters e 8 atribuicoes semanticas.
- O conjunto antigo de quatro rascunhos nao permanece como quatro arquivos no vault atual;
  a regressao do defeito foi validada por contrato e E2E, sem fabricar dados no ambiente.

## 4. Provider, modelos, Judge e HippoRAG

Configuracao real validada:

| Capability | Provider | Modelo |
| --- | --- | --- |
| Main/Ask | NVIDIA NIM | `z-ai/glm-5.2` |
| Embeddings | NVIDIA NIM | `nvidia/nv-embedqa-e5-v5` |
| Judge | NVIDIA NIM | `z-ai/glm-5.2` |
| HippoRAG | NVIDIA NIM | `z-ai/glm-5.2` |

O Judge nao escolhe nem chama LLMs ocultas. Ele usa o slot configurado; no modo
`single_model`, a mesma LLM avalia a saida com prompt/versionamento e metricas separados.
Em Ollama, cada slot lista modelos automaticamente, mas a escolha e salva explicitamente.
Em providers cloud, a URL vem do catalogo e os modelos sao descobertos; a selecao tambem e
explicita. O HippoRAG usa o provider/model configurado e mantem seu indice por vault.

## 5. Migrations e configuracao

- Schema atual/alvo: `8/8`, compativel.
- Configuracao v2 atomica: modo `cloud` ou `local`, nunca mistura silenciosa.
- Slots: main, embedding, Judge e HippoRAG.
- Chave criptografada em repouso e mascarada na API/export.
- Providers conhecidos exigem endpoint registrado; custom cloud exige HTTPS e endereco
  publico, com bloqueio SSRF.
- Catalogo duplicado e nao usado do frontend foi removido. Defaults locais, endpoints
  oficiais, rotas e textos de produto permanecem como constantes intencionais;
  estado operacional e segredos permanecem configuraveis.

## 6. Produto e UX

- Setup de IA obrigatorio: [AI setup](assets/v1.3.0-ai-setup.png).
- Settings reorganizado por tarefas: [Settings](assets/v1.3.0-settings.png).
- Sidebar de no com resumo, confianca, origem, modelo, evidencia, analise semantica,
  notas e acao Ask: [Node sidebar](assets/v1.3.0-graph-node-sidebar.png).
- Landing e documentacao atualizadas: [Landing](assets/v1.3.0-landing.png).
- Ask ganhou prioridade no topo do grafo, resposta grounded, recusa sem evidencia,
  salvar insight e erros acionaveis.
- Flow mantem contexto, permite continuar resposta e cancelar turno ativo.
- Check Online e global, opt-in, com estado, fontes, conclusao e falha explicita.
- Improve/enriquecimento e automatico via fila; falha semantica mostra causa e permite retry.

### What BerryBrain understands

Antes, o painel podia ficar generico, pendente ou sem explicar a origem. Depois, o no
`computer science` mostra significado no contexto, relevancia, achados suportados,
inferencias, incertezas, evidencias, versao, historico, provider e modelo. A captura acima
usa dados reais e aguarda a analise terminar antes de registrar a tela.

## 7. Check Online e Flow

- Check Online antes: comportamento fragmentado e sem ciclo global verificavel.
- Check Online depois: comando global no grafo, pesquisa externa opt-in, fontes e status;
  E2E `runs global online research and reports completion` passou.
- Flow antes: Ask isolado.
- Flow depois: contexto continuado e cancelamento; E2E
  `continues a grounded answer in Flow and can cancel an active turn` passou.

## 8. Performance de paginas

Budget: DCL publico <= 2.500 ms, autenticado <= 3.000 ms e scripts <= 400.000 bytes.

| Rota publica | DCL ms | JS bytes |
| --- | ---: | ---: |
| `/` | 401.1 | 132878 |
| `/docs` | 241.2 | 60074 |
| `/faq` | 144.4 | 0 |
| `/contact` | 138.3 | 0 |
| `/privacy` | 134.1 | 0 |
| `/security` | 121.7 | 0 |
| `/terms` | 86.6 | 0 |
| `/gdpr-lgpd` | 164.6 | 0 |
| `/login` | 78.1 | 0 |
| `/setup` | 88.2 | 0 |
| `/berrybrain/setup` | 111.4 | 0 |
| `/welcome` | 255.3 | 0 |

| Rota autenticada | DCL ms | JS bytes |
| --- | ---: | ---: |
| `/brain` | 130.5 | 197816 |
| `/account` | 1527.4 | 0 |
| `/activity` | 232.4 | 0 |
| `/berrybrain/account` | 138.9 | 0 |
| `/insights` | 161.3 | 0 |
| `/notifications` | 1017.6 | 0 |
| `/reviews` | 695.8 | 0 |

Paineis lazy: Settings 145.9 ms; grafo 697.7 ms. Build: `/brain` 195 kB first
load, `/docs` 189 kB e shared 103 kB.

## 9. Benchmark do grafo

- API 5k nos/20k arestas: p95 2.536 ms, payload 11.329.062 bytes,
  pico 82.131.820 bytes.
- UI 10k nos/40k arestas: first visual cold 1.863 ms, warm 331 ms,
  carga completa 4.147 ms, interacao p95 175 ms, heap 21,7 MB.
- Paginacao progressiva usa lotes de 1k; 1k/5k/10k e 20k/40k de arestas estao cobertos.
- Mobile sem overflow horizontal; reduced motion e foco visivel validados.

## 10. Semantica, homonimos, cores e vaults

- Benchmark semantico: Recall@10, MRR e NDCG@10 = 1,0; p95 47,34 ms;
  cobertura 1,0; perfis stale 0.
- Insight e cognicao: precisao, recall, provenance e usefulness = 1,0;
  unsupported/leakage = 0.
- Caso Roberto Carlos: piloto agrupa com motorsport; cantor permanece separado pela
  evidencia contextual.
- Clusters sao estaveis; pendentes e vaults usam namespaces reservados.
- Vault nodes nao entram em clusters semanticos e recebem `vault-*` exclusivo.
- Paleta e legendas sao explicaveis; gate automatizado nao detectou violacoes WCAG A/AA.

## 11. Backup, restore e dados

- Backup final: `backup-20260809T022722Z`, manifesto verificado, 14 arquivos.
- Metadados conferidos: 1 nota e 142 jobs, iguais as tabelas.
- Restore e rollback foram testados em ambiente isolado; nenhum restore destrutivo foi
  executado sobre o ambiente atual.
- Dry-run de reparo classificou seis jobs recuperaveis e 67 irreparaveis antes da escrita.

## 12. Testes e qualidade

- API: 348 passed, 55 subtests, 1 warning deprecado do Starlette/httpx.
- Worker: 44 passed.
- HippoRAG: 7 passed.
- E2E final: 43 passed em 3,1 min, sem retry ou caso flaky.
- SQLite de producao validado em WAL com `busy_timeout=30000`; leituras autenticadas
  permaneceram disponiveis durante escritas concorrentes do worker.
- Ruff: 168 arquivos formatados, zero erros.
- TypeScript/ESLint/build: aprovados.
- Architecture fitness: 12/12; sem caminhos absolutos de maquina.
- Security source audit: 9/9; sem secrets, vault pessoal ou indices derivados versionados.
- `npm audit`: zero vulnerabilidades; `pip-audit`: zero achados.
- Trivy final: zero HIGH/CRITICAL corrigivel nas quatro imagens.

## 13. SBOM e artefatos

CycloneDX 1.7:

| Imagem | Componentes | SHA-256 do SBOM |
| --- | ---: | --- |
| API | 220 | `61923242e9d4a993f0751c576e59f3de217da2eda07007777c47b9f8010952c2` |
| Worker | 105 | `6242fc174ea92dac9b9a6b97c5d998f794d966d5389c1d084f840b43128e6e98` |
| Web | 51 | `9e7da475a9d2c8430a59e0e1615dde5c665fd61b5e92ce5aa9342d0d24896999` |
| HippoRAG | 120 | `d638406c9d229ef88bf631431a4642831da5e7cf552ad812dea7cb4049fdda57` |

## 14. Riscos restantes

- 67 jobs historicos irreparaveis permanecem em dead-letter por desenho, auditados e
  inativos; nao bloqueiam a fila.
- O host nao oferece cgroup memory limits; os budgets foram medidos, mas Docker informa
  que nao consegue impor o limite neste kernel.
- Ha um warning de deprecacao Starlette/httpx nos testes, sem falha funcional.
- Assinatura Cosign, CI remoto, tag e GitHub Release dependem da publicacao. Esses itens
  permanecem pendentes por ordem explicita do mantenedor.

## 15. Publicacao e rollback

- Commits locais: `b5e8745` (v1.3.0), `e9109cc` (heartbeat/monitor), `2856dbc`
  (evidencias) e `7689be2` (concorrencia/performance).
- Tag pretendida: `v1.3.0`.
- Release remota: autorizada; verificacao pendente ate o push da tag e conclusao do CI.
- Rollback de codigo: voltar para a tag `v1.2.0`.
- Rollback de dados: validar o manifesto e restaurar o backup
  `backup-20260809T022722Z` com os comandos documentados no README/Docs.
- O smoke local passou com API, worker, web e HippoRAG saudaveis.
- Proximo gate: push da `main`, tag, CI, assinatura, assets e verificacao da release publicada.
