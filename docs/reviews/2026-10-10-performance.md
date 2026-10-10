# Otimização de desempenho — 10/10/2026

Escopo: sistema BerryBrain. Não inclui novos experimentos, números ou alterações
do TCC. Base em execução: v1.4.11. Mudanças abaixo ainda não implantadas.

## Checklist

- [x] Medir endpoints e identificar campos grandes sem divulgar conteúdo privado.
- [x] Inspecionar CPU, memória, swap e consultas da Home, sem alterar o banco.
- [x] Grafo: projeção opcional `compact=true`; auditoria completa preservada.
- [x] Grafo: páginas de 1.000 arestas, cancelamento ao sair/recarregar,
  metadados em paralelo e menos reconstruções da estrutura visual.
- [x] Progresso: projetar apenas identidade e estado dos jobs; não carregar
  conteúdo completo das notas/nós para obter IDs e caminhos.
- [x] Progresso: filtrar jobs ligados a notas antes do limite de 500 registros;
  manutenção global não pode esconder a atividade das notas.
- [x] Editor/grafo/sidebar: polling sem sobreposição, pausado em abas ocultas,
  com prazo máximo e supressão de resultados após desmontagem.
- [x] Home/assimilação: eliminar join por nota sobre identidade JSON legada,
  preservando validade por hash e compatibilidade com registros antigos.
- [x] Assimilação: consultar apenas arestas incidentes às notas solicitadas.
- [x] Home: selecionar IDs dos insights antes de carregar suas colunas extensas.
- [x] Documentar projeção e limites na API para clientes externos.
- [x] Três regressões de backend: equivalência, paginação e identidade legada.
- [x] Quatro regressões de polling: concorrência, visibilidade, teardown e erros.
- [x] Adicionar testes de polling ao workflow de CI web.
- [x] Suíte ampliada: 69 testes de backend aprovados.
- [x] Build final de produção, typecheck e lint aprovados.
- [x] Comparação operacional das projeções em leitura estrita.
- [x] Validação de navegador com o build final: 19 cenários aprovados.
- [ ] Publicação e implantação controlada com backup e rollback.

## Evidências iniciais

Leituras únicas, locais e autenticadas; não são benchmark controlado:

| Recurso na v1.4.11 | Tempo | Resposta |
| --- | ---: | ---: |
| Pipeline progress | 1,197 s | 12 bytes; lista vazia |
| Graph edges, limite 5.000 | 0,741 s | 1.435.615 bytes; 1.170 arestas |
| Graph palette | 0,071 s | 119.849 bytes; 378 cores |
| Home summary | 0,623 s | 48.810 bytes |
| Notes, limite 200 | 0,035 s | 8.008 bytes; 56 notas |
| Ask suggestions | 0,210 s | 4.873 bytes |

No grafo, a soma do JSON de intervalos de confiança era 474.316 bytes e a de
evidências era 258.383 bytes. Esses tamanhos por campo usam serialização Python,
não correspondem exatamente aos bytes HTTP. O canvas não precisa dos fatores
completos ou citações de auditoria para desenhar a rede. A projeção compacta
omite esses campos, sem fabricar uma lista vazia nem apagar evidências.

Em diagnóstico posterior sob carga, a montagem direta da Home levou 17,778 s,
com 33 consultas e 6.605,90 ms no estágio de execução SQL instrumentado. O join
legado de jobs consumiu 3.482,24 ms e a seleção de insights 2.571,72 ms nessa
leitura. O tempo restante inclui carregamento de resultados, Python e I/O;
não deve ser atribuído integralmente à CPU. Condições diferentes impedem usar
os 0,623 s e 17,778 s como comparação antes/depois.

Host ARM64 com cerca de 8 GB de RAM e aproximadamente 2,8 GB disponíveis na
primeira leitura; swap de 2 GB quase toda ocupada. Swap ocupada, isoladamente,
não prova thrashing atual. A amostra `vmstat` mostrou intervalo com 23% de espera
de I/O, mas sem swap-in/out nesse intervalo. Não foram alterados serviços alheios,
limites de memória ou parâmetros globais do kernel.

## Comparação somente leitura

Executada em processo diagnóstico separado, com `PRAGMA query_only=ON` em
todas as conexões desse processo. O código candidato foi carregado somente
na memória desse processo; a aplicação ativa permaneceu na v1.4.11.

| Operação | Código anterior | Candidato | Observação |
| --- | ---: | ---: | --- |
| Serialização de 1.170 arestas | 1.435.615 bytes | 899.000 bytes | Redução de 37,38% |
| Leitura/serialização de arestas | 1,598 s | 0,232 s | Topologia e graphVersion iguais |
| Montagem da Home | 12,549 s | 0,676 s | Estatísticas das notas iguais; 47.489 bytes em ambos |
| Progresso | 2,801 s | 0,110 s | Correção: 0 para 27 notas na amostra |

São chamadas diretas aos handlers, não medidas HTTP ponta a ponta. Uma execução
por versão, ordem fixa (anterior primeiro), cache aquecido e build concorrente:
não é possível atribuir toda a diferença temporal ao código. A redução de bytes
e a igualdade da topologia foram verificadas diretamente; percentis de latência
e experiência pós-deploy continuam pendentes. O build concorrente e demais
serviços competem pelo host, reforçando a necessidade de medições posteriores
sem essa interferência.

## Load balancer: decisão

Não adicionar agora. Um balanceador distribui requisições; não reduz o custo de
cada consulta, o tamanho dos dados ou o desenho no navegador. Réplicas no mesmo
Raspberry Pi duplicariam memória e disputariam o mesmo disco. SQLite permite
um escritor por vez por banco; várias réplicas não eliminam esse limite.

Primeiro reduzir trabalho por requisição e requisições desnecessárias. Depois,
medir concorrência real e percentis de latência com carga autorizada, separados
dos experimentos acadêmicos. Se a API continuar limitada por CPU com RAM/I/O
disponíveis, avaliar poucos processos de API. Não duplicar indiscriminadamente
workers de automação ou watchers.

Para múltiplos hosts/usuários intensivos: projetar banco cliente-servidor,
ownership dos vaults, estado/sessões compartilhados, leases/idempotência e
observabilidade antes do balanceamento. Não compartilhar SQLite por NFS nem
introduzir Redis/PostgreSQL sem necessidade demonstrada e plano de migração.

Referências: [SQLite — usos adequados](https://www.sqlite.org/whentouse.html),
[FastAPI — replicação e memória](https://fastapi.tiangolo.com/deployment/concepts/).

## Limites e riscos

- Polling do editor/grafo passa de 5 s para pelo menos 15 s após concluir a
  leitura: menos requisições, em troca de atualização periódica menos imediata.
- Progresso continua limitado aos últimos 500 jobs elegíveis; não é um ledger
  completo. Histórico permanece em `/jobs`.
- Regressões locais validam semântica, não garantem percentis sob carga real.
- Um contêiner descartável de testes ficou preso em remoção no Docker do host;
  o launcher foi encerrado, sem reiniciar o daemon ou tocar nos serviços ativos.
  O contêiner posteriormente desapareceu do Docker. A validação de backend foi
  transferida para um virtualenv temporário isolado.
- Não houve reexecução em massa de jobs, troca de modelos ou inferência paga.
