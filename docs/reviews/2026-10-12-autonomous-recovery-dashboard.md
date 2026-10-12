# Recuperação autônoma e Home — 12/10/2026

Escopo: sistema, sem novos experimentos do TCC. Histórico de erros preservado;
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
- [ ] Publicar/implantar após validação, com backup e rollback.

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
  Nenhuma implantação feita
  nesta etapa; a instância continua na versão 1.4.12.
- 22 cenários de navegador aprovados, sem retries na execução completa;
  inspeção visual de Home desktop/mobile aprovada (fixtures, não produção).
  O primeiro lote foi interrompido pelo limite global de 5 minutos do harness;
  a execução completa com prazo maior terminou em 5,2 minutos, sem falhas.
- PR de implementação: https://github.com/imsouza/berrybrain/pull/32.

## Leitura operacional, sem mutações

Em 12/10, o banco apresentou 69.172 jobs concluídos, 1.072 dead letters e 1.058
superseded. As seis atualizações de estatísticas mais recentes estavam concluídas.
Jobs de expansão/inferência antigos tinham tentativa ainda aberta em
`context_loading`, apesar do encerramento por lease expirado. Logs mostraram
timeouts e falhas ao reportar o resultado; HTTP 409 em geração de título foi
um caso distinto, não prova da causa de todas as falhas. Os timeouts curtos e a
auditoria incompleta foram corrigidos; a eficácia operacional requer observação
após implantação, sem prometer que todo erro antigo desapareça.

Os testes usam fixtures/bancos isolados. Nenhum novo experimento do TCC, probe
de inferência paga ou exclusão do histórico de produção foi realizado.
