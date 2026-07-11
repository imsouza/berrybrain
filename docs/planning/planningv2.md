# Planning V2 - BerryBrain como segundo cerebro real

## Resumo

Transformar o BerryBrain de um editor com grafo inicial em um segundo cerebro operacional: notas viram conceitos, contextos, conexoes explicaveis, insights acionaveis e um grafo que cresce com evidencia, confianca, origem, provider/modelo e controle do usuario.

## Fase 1 - Estabilizacao e transparencia

- Garantir que a Home carregue apenas dados reais de API/service, sem numeros hardcoded.
- Fazer a inferencia do grafo usar sempre a IA configurada e exibir provider, modelo, status, erro, timeout e evidencias.
- Quando a IA nao responder, mostrar `waiting_provider` ou erro operacional; nao converter isso em falta de evidencia.
- Resolver higiene de build e ambiente: `.next`, `tsc --noEmit`, testes de API e build web.
- Remover flashcards/review da experiencia principal e substituir revisao por sugestoes de estudo baseadas no grafo.

## Fase 2 - Modelo real de segundo cerebro

- Expandir o grafo para nos dinamicos: nota, conceito, topico, contexto, entidade, insight, lacuna, anexo, trilha de estudo, cluster e fonte.
- Cada no deve persistir tipo, label, resumo, origem, notas fonte, confianca, status, provider, modelo, prompt versionado, `aiNotes`, `userNotes` e metadata.
- Cada conexao deve persistir origem/destino, tipo, motivo, evidencia, confianca, status, provider, modelo e historico de decisao.
- Conexoes deterministicas podem ser confirmadas automaticamente.
- Conexoes geradas por IA devem iniciar como `suggested`, salvo regra configuravel de auto-confirmacao por confianca.

## Fase 3 - Expansao automatica do grafo

- Pipeline de expansao: extrair conceitos, contexto, entidades, topicos, resumo, embeddings, notas proximas, conexoes sugeridas, lacunas, insights, clusters e estatisticas.
- Jobs alvo: `EXTRACT_CONCEPTS`, `EXTRACT_CONTEXT`, `EXTRACT_ENTITIES`, `DETECT_TOPICS`, `GENERATE_NODE_SUMMARY`, `GENERATE_INFERRED_CONNECTIONS`, `GENERATE_GRAPH_INSIGHTS`, `UPDATE_GRAPH_CLUSTERS`, `UPDATE_GRAPH_STATS`, `EXPAND_KNOWLEDGE_GRAPH`.
- Registrar evento para cada criacao, atualizacao, confirmacao, ignoracao e reprocessamento do grafo.

## Fase 4 - IA, prompts e inferencia

- Versionar prompts: `graph-expand.v1`, `graph-infer.v1`, `node-summary.v1`, `connection-reason.v1`, `concept-extract.v1`, `insight-generate.v1`.
- A inferencia deve usar dados reais do grafo/notas, citar evidencias e responder `insufficient_evidence` somente quando nao houver base real.
- Permitir salvar uma inferencia como insight.
- Settings devem controlar provider/modelo por tarefa, fallback local/cloud, auto-confirmacao, limites por nota e reprocessamento automatico.

## Fase 5 - Home como centro de controle

- A Home deve responder: o que meu segundo cerebro aprendeu recentemente?
- Secoes obrigatorias: status, progresso do Autopilot, processando agora, pronto recentemente, insights da IA, conceitos emergentes, conexoes recentes, lacunas, grafo vivo, precisa de atencao e acoes rapidas.
- Conceitos detectados devem permitir abrir no grafo, criar nota permanente, adicionar nota manual, reprocessar e ver conexoes.
- Insights so aparecem se forem persistidos com evidencia, impacto no grafo e acao sugerida.

## Fase 6 - Grafo visual e UX

- `Brain View` deve ser o layout padrao persistente.
- Layouts: Brain View, radial, por tipo, centralidade e clusters.
- Clique simples seleciona no; duplo clique abre nota.
- Painel do no mostra resumo, conceitos, conexoes, evidencias, insights, lacunas, notas da IA, notas manuais, provider/model e status.
- Painel da conexao mostra motivo, evidencia, confianca, origem, status e acoes confirmar/ignorar/reprocessar.
- Filtros por tipo, status, confianca, provider e conexoes sugeridas/confirmadas.

## Fase 7 - Editor e painel da nota

- Painel direito da nota deve mostrar conceitos extraidos, contexto detectado, conexoes relacionadas, insights, lacunas e historico de processamento.
- Acoes: adicionar conceito manual, adicionar conexao manual, confirmar sugestao, ignorar sugestao, reprocessar nota, gerar insight e criar nota permanente.

## APIs e interfaces

- Validar ou criar: `GET /api/graph`, `GET /api/graph/summary`, `POST /api/graph/expand`, `POST /api/graph/infer`, `GET /api/graph/nodes/:id/summary`, `POST /api/graph/nodes/:id/confirm`, `POST /api/graph/nodes/:id/ignore`, `POST /api/graph/connections/:id/confirm`, `POST /api/graph/connections/:id/ignore`.
- Validar ou criar: `GET /api/concepts`, `POST /api/concepts/:id/create-note`, `GET /api/insights`, `POST /api/insights/generate`, `POST /api/insights/from-inference`, `POST /api/insights/:id/apply`, `POST /api/insights/:id/ignore`.
- Criar endpoint agregado de settings do grafo/IA quando necessario.

## Testes e aceite

- API: expansao cria nos/conexoes com evidencia; inferencia usa provider configurado; confirmar/ignorar persiste; Home nao retorna mock.
- UI: grafo abre em Ver grafo; layout padrao volta para Brain View; clique simples seleciona; duplo clique abre nota; botoes funcionam.
- Integracao: criar nota dispara expansao; Home e grafo atualizam; falha de provider aparece como problema visivel.
- Verificacoes minimas: testes API, `tsc --noEmit`, build web e teste manual com nota nova, inferencia e conexao confirmada.

## Decisoes padrao

- Flashcards ficam fora da experiencia principal.
- Conexoes geradas por IA comecam como `suggested`.
- Nada importante deve parecer real sem persistencia e evidencia.
- Notas manuais complementam a IA e ficam separadas de `aiNotes`.
- Provider indisponivel e falha operacional, nao ausencia de conhecimento.
