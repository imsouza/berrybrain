# Suporte de evidências e Judge — 13/10/2026

Escopo: sistema BerryBrain, sem experimentos do research ou chamadas de inferência
para fabricar resultados. Produção observada: v1.4.13; correção em branch separado.

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
- [ ] Concluir regressões de navegador sobre o build recém-gerado.
- [ ] Publicar/implantar nova versão, com backup e rollback.
- [ ] Auditar/recalcular registros de produção em lotes e verificar distribuição
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
- Primeiro harness isolado não iniciou testes por ausência de pytest; dependência
  instalada somente no ambiente temporário e execução refeita. Um lote conjunto
  anterior também revelou acoplamento de configuração entre testes; os testes de
  produto são executados em processos e armazenamentos temporários separados.
- Nenhum dado de produção foi reescrito por esta correção até esta etapa.
