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
- [x] Regressões locais de produto e lint/typecheck/build de produção.
- [x] CI final e smoke checks operacionais após implantação.
- [x] Atualizar instalação somente após validação, preservando rollback e dados.

Implementação publicada e implantada como v1.4.11 em 09/10/2026. Encerramento
operacional registrado neste arquivo local após a implantação; o commit da
release contém a versão anterior deste checklist, ainda de preparação.

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

## Validação concluída

- Typecheck e ESLint passaram; auditoria de dependências de produção sem
  vulnerabilidades na verificação inicial (dependências de desenvolvimento
  ainda exigem avaliação separada).
- Rodada de navegador: 6 regressões novas e 5 existentes aprovadas, incluindo
  arraste/persistência, tooltip, física de 42 nós, lista do grafo, voz segura e
  desabilitada em HTTP, falha parcial, sidebar, Activity/Monitor e Markdown.
- API: 6 regressões de Activity/alertas, 27 regressões anteriores e 64 testes
  de Home/jobs/ledger aprovados (97 no total, sem testes acadêmicos).
- O build final de produção 1.4.11 passou, incluindo o ajuste para não fixar
  nós com um simples clique. A rodada local final dos 11 cenários passou.
- No primeiro CI, oito checks passaram; web passou em 59/65 cenários e revelou
  seis mocks antigos (leitura completa do grafo e URL de jobs sem os novos
  parâmetros). Fixtures atualizadas para o contrato paginado, preservando as
  asserções funcionais. A reexecução passou nos nove checks antes do merge:
  716 testes de produto em 88 módulos, sem falhas nem skips, e 65 cenários de
  navegador aprovados. Essas suítes podem sobrepor os testes locais; seus
  números não devem ser somados para anunciar um total único.
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
- Dependências de produção: zero vulnerabilidades reportadas por
  `npm audit --omit=dev`. A auditoria incluindo desenvolvimento ainda indicou
  nove ocorrências (sete altas e duas moderadas); não afirmar ausência de
  vulnerabilidades em todas as dependências. CodeQL e scans de segurança e
  contêineres passaram no CI.

## Publicação e implantação — 09/10/2026

- [x] [PR #29](https://github.com/imsouza/berrybrain/pull/29) integrado após CI.
- [x] [Release v1.4.11](https://github.com/imsouza/berrybrain/releases/tag/v1.4.11)
  publicada como Latest, commit `0bf8e3cbc1f570cd74abf7f4d1e713946fcda785`.
- [x] Imagens API, worker e web multiarch publicadas; digests, assinaturas
  Cosign e attestations SPDX verificados antes da implantação ARM64.
- [x] Seis arquivos da release verificados por SHA-256: três SBOMs,
  `IMAGE_DIGESTS.txt`, `VERIFICATION.md` e `SHA256SUMS`. Os SBOMs avulsos são
  da plataforma AMD64; o inventário ARM64 está anexado à imagem OCI.
- [x] Backup privado `backup-20261009T181953Z-083a306f`: schema 14, 56 notas,
  71.098 jobs, 70 arquivos com hashes verificados e SQLite `quick_check` OK.
- [x] API, worker e web substituídos de forma controlada. Todos saudáveis,
  versão 1.4.11, revisão da release e zero reinicializações na leitura final.
- [x] Contêineres anteriores preservados para rollback; volumes, vaults e
  configurações mantidos. Sem reset de dados ou repetição em massa de jobs.
- [x] Outros 35 contêineres em execução mantiveram IDs, horários de início
  e contagens de reinicializações. O daemon Docker não foi reiniciado.
- [x] Documentação pública da [API](../api.md) incluída em `main`.

Leituras HTTP locais autenticadas após o deploy, todas com status 200:

| Recurso | Tempo observado | Escopo |
| --- | ---: | --- |
| Health | 0,351 s | Saúde da API |
| Home summary | 1,197 s | Resumo da Home |
| Automation logs | 0,043 s | 50 registros compactos |
| Jobs | 0,080 s | 3 falhas e contagens globais |
| Monitor stats | 0,826 s | Estatísticas operacionais |
| Model alerts | 0,048 s | Nenhum alerta observado retornado |
| Graph summary | 0,101 s | Incluindo dados provisórios |
| Graph nodes | 0,391 s | Página com 255 nós |
| Graph edges | 0,230 s | Primeira página com 500 arestas |
| Logs export | 0,030 s | 5 registros compactos |

As rotas web Brain, Activity e Ask retornaram HTML com status 200, entre
0,418 e 0,613 s. Isso valida entrega HTTP, não mede o tempo de interação
completo do navegador. O comportamento visual foi coberto pelos cenários
automatizados de navegador do build. Não houve teste manual completo na
sessão autenticada do usuário depois da implantação.

Na leitura pós-deploy havia 71.099 jobs, dos quais 1.076 classificados como
falhos pelo endpoint (incluindo dead_letter). São registros históricos,
não 1.076 novas falhas da release. Alertas vazios não garantem que todos os
modelos do provedor continuem disponíveis: o detector usa falhas observadas.
As durações acima são amostras operacionais únicas, sem controle de cache,
concorrência ou rede; não constituem benchmark nem resultado novo do TCC.

## Referências de interação e segurança

- [NetworkX spring_layout: posições fixas](https://networkx.org/documentation/stable/reference/generated/networkx.drawing.layout.spring_layout.html).
- [vis-network: interação e tooltip](https://visjs.github.io/vis-network/docs/network/interaction.html).
- [Mermaid: securityLevel](https://mermaid.js.org/config/schema-docs/config-properties-securitylevel.html).

## Limites

Os registros Docker Dead e os contêineres de rollback tornam `compose up`
indiscriminado inseguro neste host. Não reiniciar o daemon global. Não incluir
credenciais, conteúdo privado de notas nem backups em artefatos públicos.
