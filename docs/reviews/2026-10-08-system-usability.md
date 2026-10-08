# Correções de operação e usabilidade — 08/10/2026

Base: v1.4.10. Trabalho isolado das alterações acadêmicas. Não executar novos
experimentos do TCC, apagar falhas históricas ou repetir jobs em massa.

## Plano e evidências

- [x] Diagnosticar latência e falhas de Home, Activity e grafo no servidor real.
- [x] Reduzir consultas caras, chamadas duplicadas e bloqueios de carregamento.
- [x] Monitor: contagens globais coerentes e histórico de falhas consultável.
- [x] Settings: visualização/exportação limitada de logs com proteção de segredos.
- [x] Alertar indisponibilidade de modelos configurados sem trocar modelos sozinho.
- [x] Desabilitar gravação de áudio quando o navegador não oferece contexto seguro.
- [x] Sidebar persistente no workspace, incluindo Ask, Activity e editor.
- [x] Logo retorna ao Brain e encerra a seleção do editor sem perder rascunhos.
- [x] Ask: exemplos em cards/grid e integração visual com o workspace.
- [x] Markdown: Mermaid e LaTeX, renderização segura e tratamento de erros.
- [x] Grafo: tooltip único, posições fixadas após arrastar e polimento visual,
  preservando as formas ontológicas e cores semânticas catalogadas.
- [ ] Regressões de produto, lint/typecheck/build e smoke checks operacionais.
- [ ] Atualizar instalação somente após validação, preservando rollback e dados.

Checkboxes acima indicam implementação no worktree, não publicação no servidor.

## Diagnóstico operacional (sem novos experimentos acadêmicos)

Em leituras isoladas do servidor em 08/10, Home respondeu em 1,311 s, jobs em
1,124 s, Monitor/stats em 3,244 s e graph/summary em 0,051 s. O endpoint antigo
de automation-logs excedeu 30 s. A consulta compacta nova, executada em modo
somente leitura sobre o mesmo banco, retornou 50 registros em 0,727 s. São
observações operacionais, não medições controladas nem promessa de latência.

Os logs carregavam snapshots extensos e ordenavam todo o histórico por uma
coluna sem índice. Agora usam projeção compacta e paginação pelo ID indexado.
Activity e Monitor aguardavam conjuntos inteiros de requisições; uma falha ou
lentidão escondia os demais resultados. Agora os painéis são independentes,
com timeout, indicação de erro e nova tentativa. O Monitor confundia uma
amostra de 200 jobs com a fila global. Na leitura posterior havia 1.074 jobs
em dead_letter: o histórico foi preservado, sem repetir trabalhos em massa.

Home/sidebar compartilham requisições simultâneas. O workspace persiste entre
rotas e a lista de notas é paginada até o fim. Polling pausa quando a aba está
oculta; no Monitor também pausa ao consultar páginas antigas. Ask não baixa
o grafo completo. Falhas parciais do grafo mantêm os nós disponíveis e mostram
aviso explícito, sem tentar em seguida um endpoint completo mais pesado.

## Comportamento e limites

- Sidebar completa em desktop; trilho de navegação permanente em telas pequenas.
  O compromisso vale para as páginas do workspace, não login/landing públicas.
- Arrastar fixa o nó; vizinhos não fixados continuam sujeitos à física. As
  posições são mantidas em sessionStorage durante a sessão, independentes da
  versão dos dados. Não são um layout global sincronizado entre dispositivos.
- Formas ontológicas e cores semânticas permanecem intactas. O hover usa apenas
  o tooltip; rótulos no canvas aparecem quando filtrados. Agrupamento inicial
  evita cópias quadráticas de arrays e atualização de paleta não reinicia física.
- Logs exportados são eventos da aplicação, não stdout do Docker. Limite de
  1.000 registros; snapshots omitidos e segredos conhecidos redigidos. Caminhos,
  títulos e descrições ainda podem conter informações privadas.
- Indisponibilidade de modelo é inferida de falhas observadas, não de uma prova
  automática de remoção do catálogo. Sem probes de inferência, troca de modelos
  ou confusão com rate limiting. Detalhes e limites em [API](../api.md).
- Mermaid é carregado sob demanda, usa modo strict e imagem SVG inerte;
  tamanho/arestas limitados, imagens externas desabilitadas. LaTeX usa KaTeX sem
  trust. Syntax inválida mostra erro, sem quebrar o editor. HTTP inseguro não
  solicita microfone: o botão fica desabilitado e explica a necessidade de HTTPS.

## Validação em andamento

- Typecheck e ESLint passaram; auditoria de dependências de produção sem
  vulnerabilidades na verificação inicial (dependências de desenvolvimento
  ainda exigem avaliação separada).
- Rodada de navegador: 6 regressões novas e 5 existentes aprovadas, incluindo
  arraste/persistência, tooltip, física de 42 nós, lista do grafo, voz segura e
  desabilitada em HTTP, falha parcial, sidebar, Activity/Monitor e Markdown.
- API: 6 regressões de Activity/alertas, 27 regressões anteriores e 64 testes
  de Home/jobs/ledger aprovados (97 no total, sem testes acadêmicos).
- O build de produção passou. A versão final 1.4.11 inclui ainda o ajuste para
  não fixar nós com um simples clique; validação final/release continuam pendentes.
- Leitura posterior dos jobs: 1.076 falhas históricas, 619 com texto de timeout,
  120 relacionadas a lease e 337 não classificadas por esse filtro simples.
  Dos jobs falhos, 570 eram UPDATE_GRAPH_STATS. Esses grupos não provam uma
  causa única; não foram reexecutados nem apagados.
- O recálculo de confiança consultava feedback por artefato. A otimização usa
  snapshot limitado à operação e mantém endpoints das arestas em memória,
  preservando precedência exata/sobreposta de feedback e fórmulas. As 45
  verificações de feedback/confiança/escrita passaram; a regressão faz 100
  resoluções com uma leitura compartilhada, sem mudar decisões. Total atual:
  142 testes de backend e 11 cenários de navegador aprovados.
- Release/deploy ainda pendentes. Não foi modificado o banco real nem seus vaults.

## Referências de interação e segurança

- [NetworkX spring_layout: posições fixas](https://networkx.org/documentation/stable/reference/generated/networkx.drawing.layout.spring_layout.html).
- [vis-network: interação e tooltip](https://visjs.github.io/vis-network/docs/network/interaction.html).
- [Mermaid: securityLevel](https://mermaid.js.org/config/schema-docs/config-properties-securitylevel.html).

## Limites

Os registros Docker Dead e os contêineres de rollback tornam `compose up`
indiscriminado inseguro neste host. Não reiniciar o daemon global. Não incluir
credenciais, conteúdo privado de notas nem backups em artefatos públicos.
