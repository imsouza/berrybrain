# Recuperação autônoma e Home — 12/10/2026

Escopo: sistema, sem novos experimentos do research. Histórico de erros preservado;
sem retry indiscriminado de jobs antigos ou troca automática de provedor.

## Checklist solicitado

- [x] Inspecionar o retry existente: worker repete erros transitórios; a fila
  encerra em dead letter quando esgota o orçamento. Não há supervisor que
  recupere esses jobs depois do encerramento.
- [x] Recuperação autônoma limitada, com espera, classificação de erro,
  validação da versão da origem e deduplicação de trabalho.
- [x] Separar falhas históricas substituídas de trabalho ainda recuperável;
  manter auditoria e não fabricar sucesso de pipelines.
- [x] Contador de Alerts baseado nas notificações não lidas, não na quantidade
  de categorias resumidas da Home.
- [x] Corrigir texto literal `act_forNote` em Automatic Activity.
- [x] Insight criado manualmente: destacar no primeiro acesso posterior ao
  grafo, consumir o destaque apenas quando ele for efetivamente exibido.
- [x] Knowledge Operations compacto, legível e responsivo.
- [x] Statistics com gráficos acessíveis, dados reais e identidade visual atual.
- [x] Regressões isoladas de backend e frontend, build e revisão do diff.
- [x] Publicar/implantar após validação, com backup e rollback.
- [ ] Reduzir a latência residual de Home e diagnóstico da fila sob carga;
  a implantação não encerra a otimização de desempenho.
- [ ] Investigar o timeout persistente de inferência do job `#71279`; retomada
  automática confirmada, conclusão bem-sucedida ainda não obtida.

## Segurança da recuperação

Erros de autenticação, modelo removido, dados inválidos e permissão não devem
ser repetidos cegamente. Cancelamentos, versões antigas e fontes removidas
não devem voltar à fila. Um supervisor determinístico agenda recuperação;
subagentes de IA executam suas etapas, mas não decidem ignorar limites ou
duplicar tarefas. Falhas permanentes precisam continuar visíveis ao usuário.

## Implementação e limites

- Supervisor determinístico em `job_recovery.py`: até 50 candidatos/minuto,
  cursor persistido, um retorno à fila/5 minutos, fila ativa menor que quatro,
  três ciclos extras no máximo, esperas mínimas de 5/30/120 minutos. Mesmo ID,
  histórico e tentativas preservados. Não há replay em massa dos 1.076 jobs.
- Notas exigem hash atual; enriquecimento exige fingerprint atual. Judge usa
  timestamp `updated_at` e fingerprint da configuração, não o contador inteiro
  `artifact_version` do grafo. Origem removida/alterada é superseded, não sucesso.
- Estatísticas antigas só são substituídas por resultado concluído com escopo
  compatível. Uma atualização parcial não cobre uma falha global. Trabalho
  equivalente ainda ativo apenas adia a recuperação.
- Erros de modelo/credencial/quota permanente não geram retries cegos. HTTP
  transitório e circuit breaker mantêm sinal legível para recuperação. Timeout
  de estatísticas aponta API/banco local, não acusa incorretamente o modelo.
- Expansão/inferência herdavam timeout HTTP de 10 segundos mesmo com orçamento
  maior para o job. Agora essas chamadas têm 120 segundos; admissão de
  enriquecimento, 60 segundos. O limite total de expansão é no mínimo 330
  segundos. Lease expirado fecha a tentativa com diagnóstico, sem marcar sucesso.
- `/notifications/summary` conta todas as notificações não lidas. Abrir o painel
  não zera o badge; marcar como lido preserva histórico. Notificações históricas
  não desaparecem automaticamente quando um job é recuperado.
- Destaque manual persiste por navegador/workspace (até 100 IDs), é consumido
  apenas ao desenhar o insight visível no grafo e respeita movimento reduzido.
  Não é sincronizado entre dispositivos. Cores e formas dos nós preservadas.
- Home usa SVG leve, sem biblioteca adicional ou chamadas extras de dados:
  assimilação, inventário e estados dos jobs. São fotografias do estado real,
  não séries temporais inventadas. Operações alternam processamento, conexões
  e atividade, com área limitada e detalhes sob demanda.
- Contratos e controles documentados em `docs/api.md`. Para desativar o
  supervisor: setting `automatic_job_recovery_enabled=false`.

## Validação local

- 118 testes de backend aprovados: recuperação (24), jobs (44), contratos (5),
  notificações (2), Home (2), resiliência do worker (14), fallbacks (18), Judge (2),
  leases (4), cancelamento (3).
- 7 testes auxiliares de frontend aprovados: polling (4), fila de destaque (3).
- ESLint, TypeScript, Ruff, formatação e `git diff --check` aprovados.
- Build de produção Next.js aprovado (23 páginas, antes do bump de versão).
  Imagens finais da versão 1.4.13 construídas no CI e implantadas conforme abaixo.
- 22 cenários de navegador aprovados, sem retries na execução completa;
  inspeção visual de Home desktop/mobile aprovada (fixtures, não produção).
  O primeiro lote foi interrompido pelo limite global de 5 minutos do harness;
  a execução completa com prazo maior terminou em 5,2 minutos, sem falhas.
- PR de implementação: https://github.com/imsouza/berrybrain/pull/32.

## Publicação verificada

- Release [v1.4.13](https://github.com/imsouza/berrybrain/releases/tag/v1.4.13)
  publicada em 12/10/2026, commit `cf206766781c510178a65b6293347b0084ec1998`.
- Nove verificações do PR aprovadas. CI de produto: 766 testes em 91 módulos,
  sem falhas ou testes ignorados. Esses testes e os locais se sobrepõem;
  não somar os totais como cobertura independente.
- Imagens API/worker/web publicadas para AMD64 e ARM64; assinaturas Cosign e
  atestações SPDX verificadas antes de obter as imagens ARM64 do servidor.
- Seis arquivos públicos anexados: três SBOMs, `IMAGE_DIGESTS.txt`,
  `VERIFICATION.md` e `SHA256SUMS`; checksums conferidos.
- Backup privado `backup-20261012T233213Z-94ed14d3`: 71 arquivos verificados,
  SQLite `quick_check=ok`, schema 14, 56 notas e 71.529 jobs. Vault, banco e
  credenciais não foram enviados à release pública.

## Implantação e observação em produção

- Concluída em 12/10/2026 às 23:44 UTC (20:44 em São Paulo). API, worker e web
  saudáveis, versão 1.4.13 e revisão da release conferidas. Mesmas configurações,
  volumes, vault, rede e portas; containers anteriores preservados para rollback.
- 32 outros containers conhecidos comparados antes/depois: mesmos IDs, imagens,
  estados, horários de início e contadores de reinício. Não houve restart global
  do Docker, prune, exclusão de volumes ou reenvio em massa de jobs.
- Smoke de leitura: 16 requisições HTTP 200, incluindo Home, notificações,
  saúde/progresso da fila, resumo/nós/arestas do grafo e páginas brain, activity,
  ask e account. Soma dos estados dos jobs igual ao total da Home; contagem de
  notificações não lidas válida (1.414 na leitura), independente do limite da lista.
- Grafo: resumo 421 ms, página de nós 210 ms e arestas compactas 203 ms nessa
  amostra. São tempos de requisição local, não benchmark de renderização ou research.
- Limitação ainda aberta: Home 10,7 s na primeira leitura e 1,7 s via proxy,
  depois 10,2 s durante processamento; diagnóstico da fila 9,5–14,1 s. Não há
  evidência para declarar resolvida toda a latência. Priorizar perfil das consultas
  e contenção de I/O antes de considerar balanceamento de carga.
- Snapshot pós-atualização: 69.399 concluídos, 1.025 dead letters, 1.104
  superseded e um job ativo; a fila mudou durante a observação. Contagens
  menores de falhas não significam que todo job antigo foi executado com sucesso.
- Recuperação observada via API: job `#71279` (`GENERATE_INFERRED_CONNECTIONS`)
  retomado com `automaticRecovery.count=1`, agendado às 23:43:25 UTC. A terceira
  tentativa começou às 23:43:31 e terminou às 23:48:02 após 271.257 ms, novamente
  com timeout. O job retornou a dead letter; a tentativa foi encerrada com
  `transient_job_error`, diferentemente das duas antigas, ainda abertas no histórico.
  Isso confirma a retomada e a auditoria, não a solução da causa. O estágio registrado
  permaneceu `context_loading`; a mensagem sugere conferir o provedor, mas não prova
  que ele seja o gargalo. Próximo diagnóstico: separar espera HTTP, consultas locais
  e inferência, sem aumentar cegamente limites ou forçar novas tentativas.
- Pendência de infraestrutura: enumeração global do Docker e atualização dos
  aliases `berrybrain-*:local` excederam os prazos. Os aliases ainda apontam para
  1.4.12; os containers ativos usam os digests verificados de 1.4.13. Não executar
  recriação cega pelo alias `local`; usar os digests publicados e preservar rollback.
  A pendência foi mantida explícita, sem reiniciar o daemon compartilhado.

## Leitura operacional, sem mutações

Em 12/10, o banco apresentou 69.172 jobs concluídos, 1.072 dead letters e 1.058
superseded. As seis atualizações de estatísticas mais recentes estavam concluídas.
Jobs de expansão/inferência antigos tinham tentativa ainda aberta em
`context_loading`, apesar do encerramento por lease expirado. Logs mostraram
timeouts e falhas ao reportar o resultado; HTTP 409 em geração de título foi
um caso distinto, não prova da causa de todas as falhas. Os timeouts curtos e a
auditoria incompleta foram corrigidos; a eficácia operacional requer observação
após implantação, sem prometer que todo erro antigo desapareça.

Os testes usam fixtures/bancos isolados. Nenhum novo experimento do research, probe
de inferência paga ou exclusão do histórico de produção foi realizado.
