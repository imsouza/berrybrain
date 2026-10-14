# Suporte de evidências e Judge — 13/10/2026

Escopo: sistema BerryBrain, sem experimentos do research ou chamadas de inferência
para fabricar resultados. Diagnóstico em v1.4.13; v1.4.14 publicada e implantada
em 14/10/2026 (horários de implantação abaixo em UTC).

## Diagnóstico confirmado

- [x] Encontrar a origem dos 50%: o método anterior armazenava o ponto médio
  do intervalo. Com poucos sinais, limites 0–1 resultavam em 0,5 independentemente
  das medidas. Não era uma probabilidade medida de acerto.
- [x] Verificar atividade real: na consulta de 12/10, Judge #71543 estava em
  execução; #71540, #71541 e #71542 concluídos; enriquecimento #71535 concluído.
  Estado concluído de um job não comprova sozinho calibração/correção factual.
  Em nova leitura de 13/10, #71543 estava `superseded`; os Judges #72032–#72036
  estavam concluídos. Avaliações #70091–#70095 registravam provider `nvidia-nim`,
  prompt v2 e escores totais antigos de 3/5, fora da escala 0–1. O modo configurado
  era `single_model`. Nenhuma chamada de inferência foi necessária para a consulta.
- [x] Identificar a integração incompleta: avaliações Judge atualizavam
  `quality_score`, mas não necessariamente a pontuação exibida.
- [x] Separar `pending` de indisponibilidade: a apresentação de um valor ausente
  usava texto de fila mesmo sem comprovar trabalho pendente.
- [x] Corrigir enriquecimento que sobrescrevia a evidência de entrada e tornava
  a própria análise recém-gravada incompatível com seu fingerprint.

Leitura de produção antes da implantação: 364 nós (74 com método legado, todos
em 0,5; 290 sem medição) e 3.444 arestas (252 legadas em 0,5; 3.192 sem medição).
A consulta foi SQLite read-only; o comando Docker atingiu o limite de tempo após
emitir o resultado. São contagens do armazenamento, não apenas dos itens visíveis
no grafo nem comprovação de que todos necessitam avaliação por IA.

## Alterações

- [x] Média dos sinais reais separada do intervalo descritivo; método versionado
  `evidence-support-mean-v2`, sem constante substituta para 50%.
- [x] Persistir observações e fontes para auditoria/reprodução do agregado.
- [x] Ignorar valores inválidos e proveniência sem medição; preservar nota zero.
- [x] Judge interno: calcular o total pelos cinco critérios da rubrica, validar
  limites e aplicar regras numéricas, mantendo rejeições semânticas mais estritas.
  Prompt v3 separado do v2 histórico; submissão pública rejeita booleanos,
  valores não finitos, escalas inválidas e verdicts desconhecidos.
- [x] Atualizar suporte após Judge; substituir avaliação anterior sem inflar
  amostra por retries. Modo determinístico sem avaliação não vale como nota zero.
- [x] Evidência textual não inclui IDs, hashes nem nomes de campos JSON.
- [x] Home: excluir itens não avaliados da média e corrigir escala de 1%.
- [x] UI: suporte de evidência, incerteza separada, estado não avaliado e aviso
  para valores legados, sem apresentar o midpoint antigo como nova média.
- [x] Impedir auto-fit da câmera durante/depois de iniciar arrasto de um nó.
  A regressão visual revelou que o worker podia reenquadrar a câmera após a ação
  manual, mesmo com coordenadas do nó fixadas.
- [x] Recalcular sob demanda preservando observações registradas; recuperar
  sinais semânticos versionados apenas se a origem ainda corresponder.
- [x] Documentar método e contrato reutilizável em `docs/confidence-model.md`
  e `docs/api.md`.
- [x] Concluir testes da API e regressões dos módulos alterados; build de produção,
  TypeScript, ESLint e Ruff aprovados.
- [x] Concluir regressões de navegador sobre o build recém-gerado: 22 aprovadas,
  sem retries na rodada final (5,6 minutos).
- [x] Publicar v1.4.14: PR #34 integrado à main, imagens AMD64/ARM64, assinaturas
  e atestações SPDX verificadas; seis artefatos de integridade anexados à release.
- [x] Implantar nova versão localmente, com backup validado e rollback.
- [x] Auditar/recalcular registros de produção em lotes e verificar distribuição
  real; não substituir percentuais em massa nem forçar inferência paga.

## Limites necessários

A pontuação é suporte descritivo, não probabilidade de verdade. Os sinais são
heterogêneos e podem ser correlacionados; não existe calibração factual validada.
Um resultado genuíno de 50% continua possível. Sem medidas recuperáveis, o correto
é informar indisponibilidade, não inventar um valor para preencher a interface.
O histórico antigo nem sempre preservou os escores individuais; não é possível
recuperá-los matematicamente apenas do midpoint. Avaliações novas ou perfis
versionados compatíveis são necessários nesses casos.

## Verificações

- Suíte API: 490 testes aprovados em 66 módulos, sem falhas/erros/skips.
- CI do primeiro commit do PR #34: 820 testes de produto em 91 módulos, sem
  falhas/skips; verificações de backend, worker, web, segurança e CodeQL aprovadas.
- Após ajustes finais: 97 testes aprovados em 11 módulos afetados, sem
  falhas/erros/skips. Esse lote sobrepõe a suíte anterior; não somar os totais.
- Verificações isoladas, com armazenamento temporário e rede bloqueada; nenhuma
  avaliação paga ou experimento de pesquisa executado.
- TypeScript, ESLint, Ruff e build Next.js de produção aprovados em 13/10.
- Primeira rodada de navegador: 21 aprovações diretas e um hover aprovado no retry.
  O teste usava geometria/espera fixas; sincronização do canvas ajustada. A rodada
  seguinte revelou deslocamento de câmera após arrasto. Corrigido o controle da
  câmera; novo build e rodada visual exigidos antes da aprovação final.
- Relatórios locais: `/tmp/berrybrain-confidence-api-checks.json` e
  `/tmp/berrybrain-confidence-final-checks.json`.
- Revisão final `ef908f15e21fc29cbb559fdf93fcee50289c2d00`: nove checks do PR #34
  aprovados, novo build/TypeScript/ESLint aprovados e 22 testes de navegador
  aprovados sem repetição. As falhas transitórias anteriores foram investigadas,
  não ocultadas por retries no resultado final.
- Primeiro harness isolado não iniciou testes por ausência de pytest; dependência
  instalada somente no ambiente temporário e execução refeita. Um lote conjunto
  anterior também revelou acoplamento de configuração entre testes; os testes de
  produto são executados em processos e armazenamentos temporários separados.
- As verificações pré-implantação não reescreveram dados de produção. A manutenção
  posterior é discriminada abaixo; não é experimento nem nova avaliação por IA.

## Publicação

- Release: https://github.com/imsouza/berrybrain/releases/tag/v1.4.14
- Código: `64d430ecbef20a77e174a393d227ab0d26a0a89e`; árvore idêntica à revisão
  final aprovada do PR #34.
- Pipeline: https://github.com/imsouza/berrybrain/actions/runs/38439951233
  (dez jobs aprovados).
- Três assinaturas e três atestações verificadas com Cosign 3.1.3, identidade
  OIDC do workflow/tag e subjects correspondentes aos manifestos publicados.
- Artefatos: `IMAGE_DIGESTS.txt`, `SHA256SUMS`, `VERIFICATION.md` e SBOMs SPDX
  de API/web/worker. SHA-256 verificado antes do upload. Inventários standalone
  correspondem ao AMD64; atestações de plataforma ficam nos manifestos OCI.
- Nenhum vault, banco, backup privado ou credencial foi anexado à release.

## Implantação local — 14/10/2026

- Backup `backup-20261014T035046Z-aacd69be`: 71 arquivos verificados por hash,
  SQLite `quick_check = ok`, 56 notas e 72.340 jobs no snapshot. Uma tentativa
  anterior atingiu timeout no cliente; sua conclusão não foi usada como garantia.
- Troca concluída às 04:09:42 UTC; API, web e worker saudáveis. Schema 14
  mantido, mesmos volumes, vault, portas, rede e variáveis de ambiente.
- Imagens ARM64 executadas pelos manifestos verificados:
  API `sha256:3cd1282a1e91398f036927d73b741f93ac8292b9bb3600ac160b1687dcb5254b`;
  web `sha256:db95b4a7c6545ce0c04887c8ed74adfa238666c3f048d0cda98d4d4d3e3105fa`;
  worker `sha256:46db04a41d69e6d636a590d912a04abea6b795679db39a31cc2b189f21709440`.
- Contêineres anteriores retidos, parados, como
  `berrybrain-{api,web,worker}-rollback-pre-1.4.14-20261014`. Não houve remoção de
  volumes, prune ou reinício do daemon. Reversão de contêiner não restaura dados;
  para isso existe o backup validado.
- Comparação dos 32 outros serviços conhecidos: IDs, imagens, estado, início e
  contagem de reinícios iguais antes/depois.
- Smoke somente leitura: 16 respostas HTTP 200, incluindo Home, notificações,
  jobs, grafo, Brain, Activity, Ask, Settings e proxy web. Contagens dos gráficos
  de jobs consistentes; notificações retornaram três itens não lidos.
- Após reinício, Home levou 10,844 s na primeira leitura e 1,312 s pelo proxy
  posteriormente. Grafo: resumo 112 ms, nós 81 ms, arestas compactas 133 ms.
  São medições pontuais locais, não benchmark ou garantia de latência.
- Smoke repetido após reparo: novamente 16 respostas HTTP 200; API/web/worker
  v1.4.14 saudáveis, zero reinícios. Home 5,510 s e depois 937 ms pelo proxy;
  `jobs/health` 9,155 s. A latência residual permanece pendente, não resolvida.
- Fila observada: 70.399 concluídos, 1.603 substituídos e 338 em `dead_letter`.
  Esses 338 não foram apagados nem reprocessados em massa; estado saudável do
  worker não significa que o histórico inteiro foi resolvido.

## Pendências reveladas pela auditoria de produção

- [ ] Investigar latência de primeira leitura da Home e `jobs/health` (6,258–9,155 s).
- [ ] Tratar historicamente verdicts inválidos: dois nós e 16 arestas ativos
  tinham strings fora do contrato de qualidade. A nova entrada estrita impede
  novos valores desse tipo, mas não reinterpreta silenciosamente os antigos.
- [ ] Recuperar avaliações antigas do Judge apenas com rubrica e versão
  verificáveis; escores antigos fora de 0–1 não devem virar probabilidades ou
  ser normalizados arbitrariamente. Preservar os registros de auditoria.
- [ ] Rotacionar coordenadamente token interno e credencial SMTP: uma falha de
  diagnóstico Docker imprimiu variáveis de ambiente na saída da sessão. Valores
  não foram incluídos no repositório/release. A rotação não foi feita unilateralmente
  para evitar quebra de integrações e envio de e-mail.

## Reparo rastreável dos dados — 14/10/2026

- [x] Prévia em conexão SQLite `mode=ro`, sem autoflush, encerrada com rollback;
  usar funções do sistema, sem provider, geração de jobs ou conteúdo sintético.
- [x] Recuperar 163 nós ativos pelos perfis semânticos versionados cujo fingerprint
  ainda corresponde à origem. Nós/insights processados em lotes de até 25, com
  transação de escrita exclusiva por lote para evitar sobrescrita concorrente.
- [x] Recalcular 1.631 conexões e 12 respostas salvas pelo serviço existente de
  auditoria; 112 conceitos examinados, sem recalculação pendente.
- [x] Recalcular 169 insights ativos com cobertura textual das evidências salvas.
  Não reutilizar midpoint antigo ou `quality_score` inválido como observação.
- [x] Reabrir em modo somente leitura e reproduzir as 1.967 médias disponíveis;
  todas coincidiram com as observações registradas e ficaram no domínio 0–1.
  Nas conexões, verificar também o arredondamento da coluna percentual inteira.

| Registros recalculados | Disponíveis | Sem medição | Faixa observada de suporte |
| --- | ---: | ---: | --- |
| Nós ativos recuperáveis | 163 | 52 ativos mantidos sem medição | 40%–90% |
| Conexões | 1.627 | 4 | 0%–82,8571% |
| Respostas salvas | 8 | 4 | 2%–65,6716% |
| Insights ativos | 169 | 0 | 0%–35% |

As faixas não são comparações de acurácia: nós recuperaram notas semânticas do
modelo; os demais itens recuperaram cobertura lexical do texto registrado. Zero
ocorreu legitimamente em 91 conexões e três insights. Baixa sobreposição lexical
não comprova falsidade, especialmente entre idiomas; tampouco alta sobreposição
comprova verdade. Nenhum novo julgamento por IA foi solicitado nesta manutenção.

As 3.149 arestas processáveis não tinham observações recuperáveis nessa prévia e
não receberam pontuação fabricada. Permaneceram históricos: 76 nós e 257 arestas
legados fora do conjunto processável, além de 97 insights expirados/arquivados.
O método antigo continua explicitamente identificado, não promovido à média v2.

O primeiro comando de reparo abortou na validação do primeiro lote, antes de
qualquer commit: o verificador temporário contava fatores de proveniência junto
das observações. Corrigido para verificar apenas as observações efetivas após o
filtro do estimador. A segunda execução concluiu; a verificação independente
somente leitura aprovou todos os agregados persistidos. Nenhuma avaliação Judge,
nota, evidência original ou registro de job foi apagado pelo reparo.
