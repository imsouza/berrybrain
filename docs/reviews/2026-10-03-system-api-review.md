# Revisão do sistema e da API BerryBrain — 2026-10-03

Escopo: produto, arquitetura, API reutilizável, persistência, segurança, jobs, recuperação, grafo, Ask, interface e operação. Não inclui revisão do TCC, novos experimentos acadêmicos ou chamadas pagas de IA. Alterações anteriores do workspace são preservadas.

`[x]` significa trabalho implementado/verificado com evidência descrita neste arquivo. `[ ]` identifica trabalho pendente ou limite não validado; não representa certificação de ausência de bugs.

## Plano e acompanhamento

- [x] Identificar instalação, serviços e alterações preexistentes.
- [x] Conferir proposta e propriedade dos dados na documentação da arquitetura.
- [x] Auditar autenticação, validação de entradas, autorização e contrato OpenAPI.
- [x] Revisar os fluxos de notas, anexos, identidade, concorrência e recuperação.
- [x] Revisar jobs, leases, cancelamento, retentativas e processamento assíncrono.
- [x] Revisar admissibilidade de evidências, Ask, grafo e cores.
- [x] Revisar configuração de IA, interface, build, dependências e operação.
- [x] Corrigir falhas reproduzíveis e acrescentar regressões relevantes.
- [x] Documentar API para aplicações externas, exemplos, erros e limites.
- [x] Validar o produto em ambiente isolado, registrar resultados e atualizar checkboxes.
- [x] Verificar publicação local e saúde dos serviços alterados, registrando separadamente os alertas de infraestrutura.

## Parecer: o projeto corresponde à proposta?

A divisão Next.js → FastAPI → SQLite/vault/worker/HippoRAG corresponde à proposta de uma arquitetura local-first. Markdown é conteúdo canônico; identidades, políticas, credenciais, proveniência e jobs são estado operacional persistente. Índices, caches e projeções do grafo são derivados. Inferência pode ser local ou em nuvem.

A API `/api/v1` já existia e era utilizada pela interface e pelo worker. Esta revisão a consolida como interface documentada para outras aplicações, com credenciais independentes, modelos de resposta para os fluxos principais, paginação, conflitos de edição e acompanhamento assíncrono. Não foi criado um segundo backend paralelo.

**Conclusão:** é uma arquitetura funcional de conhecimento pessoal, com recursos reais além de um editor com chatbot. É apropriada para uso pessoal supervisionado e integrações confiáveis em uma instância. Ainda não a classificaria como plataforma pública multiusuário pronta para terceiros não confiáveis ou como sistema livre de bugs. A API reutilizável fortalece o enquadramento arquitetural, mas sua existência não prova, sozinha, escalabilidade, isolamento ou correção das respostas.

| Área | Evidência no sistema | Maturidade / limite |
| --- | --- | --- |
| Notas e propriedade | Markdown, identidade estável, hash de conteúdo, bloqueio cooperativo, escrita atômica, recuperação | Base sólida; um editor externo que ignora locks ainda exige detecção de conflito e reconciliação. |
| Processamento | Fila persistente, dependências, claim tokens, leases, cancelamento, retentativas e dead letters | Implementado e verificado funcionalmente; não é garantia de operação contínua ou execução exatamente uma vez em qualquer efeito externo. |
| Conhecimento | Extração, grafo tipado, admissibilidade de artefatos, proveniência e revisão | Implementado; confiança estimada e aprovação do Judge não são verdade factual demonstrada. |
| Ask e recuperação | Busca lexical/vetorial/grafo, fusão de resultados, citações identificadas e revalidação da fonte | Controle de evidência real; ainda depende da qualidade do material e do modelo. Não há garantia de 100% contra alucinações/injeções. |
| HippoRAG | Sidecar opcional com projeção e recuperação multi-hop | Implementação própria de recuperação em múltiplos saltos; não presumir equivalência integral com toda implementação/artigo oficial de HippoRAG. |
| IA local/nuvem | Rotas por capacidade, configurações, catálogo, validação de Judge e fallback | Implementado; modelos gratuitos podem mudar, falhar ou não oferecer embeddings. Não houve chamada real de provedor nesta revisão. |
| API externa | REST v1, Bearer, sessão/CSRF, OpenAPI, guia e cliente independente | Integração beta para backends confiáveis; workspace compartilhado, sem escopos por token/vault e sem isolamento entre tenants. |
| Interface | Editor, Ask em Markdown, BrainView, painel de configurações, documentação | Verificação estática e funcional aprovada; não equivale a homologação visual completa em todos os navegadores/dispositivos. |
| Operação | Docker Compose, healthchecks, métricas, correlação, backup/export e restauração | Adequado ao self-hosting supervisionado; alta disponibilidade, quotas e operação distribuída ainda não demonstradas. |

## Correções aplicadas

### Segurança e integridade

- [x] **SYS-02 / alta:** exceções de autenticação por prefixo substituídas por pares exatos de método/caminho. `/judge/mode` e `/judge/scorecard` agora exigem autenticação para leitura; nenhuma exceção genérica para caminhos parecidos.
- [x] **SYS-03 / alta:** limite HTTP verifica bytes efetivamente recebidos, incluindo corpo sem `Content-Length` ou tamanho subdeclarado; rejeição ocorre antes da execução da rota.
- [x] **SYS-07 / média:** validação 422 deixa de devolver o `input` recebido, evitando repetir chaves, senhas e conteúdo de notas em erros.
- [x] **SYS-08 / média:** sessões de usuários bloqueados deixam de ser aceitas. Autenticação SQLite foi retirada do event loop assíncrono; timestamps de uso são atualizados no máximo uma vez por minuto por registro, reduzindo escritas concorrentes desnecessárias.
- [x] **SYS-09 / alta:** rotação global não reativa tokens já expirados. Emissão independente preserva o token existente do worker e evita duplicação do registro de bootstrap; expiração aparece corretamente na listagem.
- [x] **SYS-10 / média:** respostas da API recebem `Cache-Control: no-store`. A documentação interativa possui política de conteúdo específica para carregar seus assets, sem relaxar a política das demais rotas.

### Notas, grafo, busca e jobs

- [x] **SYS-01 / média:** auditoria de falhas usa `JobRecord.type`, corrigindo a exceção que aparecia quando havia jobs com falha.
- [x] **SYS-04 / média:** limites com intervalo explícito para busca, jobs, atividade e metadados. Consulta global de metadados deixa de filtrar equivocadamente `note_id = NULL`; ramos por nota também respeitam `limit`.
- [x] **SYS-05 / alta:** organização automática usa a mesma operação de movimentação manual, sob lock do vault, preservando identidade e caminho dos anexos e executando sincronização/reprocessamento. Tópicos rejeitados/provisórios não são usados como autorização para reorganizar notas.
- [x] **SYS-06 / média:** status de processamento utiliza identidade/caminho estruturados, em vez de `LIKE` no JSON do payload; dead letters são contabilizadas como falhas.
- [x] **SYS-11 / média:** relações rejeitadas por qualidade não ampliam resultados nem backlinks da busca híbrida.
- [x] **SYS-12 / média:** paginação de arestas exige que os dois nós extremos estejam visíveis na mesma política de admissão. Não expõe referências a nós rejeitados/ocultos.
- [x] **SYS-13 / média:** renovação de lease continua após erros temporários de transporte/servidor. Erros de credencial ou perda definitiva da posse do job encerram a renovação.
- [x] **SYS-14 / média:** requisições de atualização das estatísticas do grafo têm timeout explícito de 60 s por chamada, dentro do orçamento do job, em vez de herdar o timeout curto padrão do cliente.
- [x] **SYS-15 / baixa:** heartbeat de lote captura explicitamente o estado do provedor, removendo dependência ambígua de variável do laço.

As formas, tamanhos e paleta existentes do BrainView não foram redesenhados nesta revisão. A semântica continua: forma = tipo ontológico; cor = contexto semântico, com exceções documentadas. A correção desta rodada é a coerência dos artefatos entregues, não pintar todos os nós artificialmente para criar variedade visual.

### API como fronteira da arquitetura

- [x] **API-01:** [guia de integração](../api.md) cobre autenticação, emissão/revogação, CRUD de notas, conflitos, geração assíncrona, paginação, Ask, erros e limites.
- [x] **API-02:** emissão independente em `POST /api/v1/security/service-tokens`, validade de 1 a 365 dias, nome por integração, segredo retornado somente na emissão. Exige sessão do proprietário e CSRF.
- [x] **API-03:** descoberta em `/api/v1`, contrato em `/api/v1/openapi.json` e Swagger em `/api/v1/docs`, inclusive pelo proxy `/berrybrain`.
- [x] **API-04:** OpenAPI informa Bearer versus sessão/CSRF e identifica rotas administrativas que não aceitam apenas token de serviço. A inspeção considera os routers incluídos da versão instalada do FastAPI.
- [x] **API-05:** modelos explícitos para leitura/criação/edição de notas, busca, páginas de nós/arestas e Ask. Demais respostas genéricas permanecem sinalizadas como dívida de contrato.
- [x] **API-06:** paginação opcional de notas (`limit`, `offset`, `total`, `nextOffset`) preserva compatibilidade com clientes antigos. Edição mantém `base_content_hash`, identidade e versão da fonte.
- [x] **API-07:** [cliente Python independente](../../examples/berrybrain_client.py), sem dependências externas, com timeout, tratamento de 409, codificação de caminhos e bloqueio de redirecionamentos que poderiam encaminhar credenciais a outro destino.
- [x] **API-08:** links e explicação no README, na arquitetura e na documentação pública do site. Não é necessário usar a interface web para executar os fluxos de integração.

## Evidência de verificação

- [x] **676 testes Python**, em **83 módulos**, sem falhas ou skips no último resultado de cada módulo: API 513; worker 59; regressões 96; sidecar 8.
- [x] **14 testes da interface**: Markdown seguro do Ask, manutenção de rascunhos/edições concorrentes, seleção de Judge e atualização de configuração.
- [x] TypeScript (`tsc --noEmit`) e ESLint de `src` aprovados.
- [x] Ruff dos arquivos Python alterados e verificação de whitespace aprovados.
- [x] Regressões novas verificam cliente externo, credenciais, contratos, tamanho do corpo, paginação, conflitos, organização de anexos, admissão de arestas e recuperação de leases.
- [x] [Registro por módulo em JSON](2026-10-03-system-verification.json), com contagens e comandos. Os números consolidam a execução ampla e as reexecuções direcionadas após correções; não representam um novo benchmark acadêmico.
- [x] Runner reproduzível em `scripts/check-system.py`: processo separado por módulo, banco/vault temporários, conexão de rede bloqueada e suites de pesquisa excluídas. Inclui testes de funções que o runner antigo de `unittest` não coletava.
- [x] Workflow adicional de integração contínua em `.github/workflows/ci-system.yml`. Sua execução no GitHub ainda depende do push normal do mantenedor; não foi afirmada aprovação remota.
- [x] Fixtures antigas atualizadas para os contratos atuais: posse do job, autenticação de Judge, fontes existentes/hash/identidade, citações por ID, transporte vetorial e restauração transacional. As proteções de produção não foram relaxadas para fazer os testes passarem.
- [x] Build/publicação local confirmados por imagem em execução, hashes de fontes e verificações HTTP.
- [x] **2 testes de navegador** da documentação pública e de OpenAPI/Swagger pelo proxy `/berrybrain` aprovados; sem criar notas ou chamar modelos.

Os testes são funcionais/de engenharia. Usam transportes simulados para modelos e serviços externos; não demonstram disponibilidade de provedores, qualidade de respostas reais, desempenho no Raspberry Pi, superioridade científica ou ausência de todos os bugs. Não houve alteração de arquivos, resultados ou ZIPs do TCC.

## Plano de evolução pendente

Pendências abaixo exigem desenvolvimento adicional ou validação específica. Não foram marcadas como concluídas por haver uma rota ou um teste unitário.

- [ ] **P1 — Permissões de integração:** escopos de leitura/escrita/Ask e autorização por vault, testes de separação entre aplicações e quotas por credencial. Pré-requisito antes de entregar tokens a terceiros não confiáveis.
- [ ] **P1 — Contrato completo:** tipar respostas administrativas e secundárias restantes; definir política de compatibilidade, comparação automática de OpenAPI entre versões e testes de um consumidor externo separado.
- [ ] **P1 — Latência e operação contínua:** a [release 1.4.9](2026-10-03-release-1.4.9.md) corrigiu leitura integral do histórico e consultas sem índices. As primeiras observações HTTP passaram de 24,44 s/26,70 s (Home/fila) para 1,08–1,55 s/0,12–0,14 s; em uma leitura posterior foram 7,06 s/2,51 s. Ainda há variação que exige acompanhar contenção e cache frio. Não são medições sob condições controladas, percentis ou um novo benchmark; a pendência de operação contínua não foi marcada como resolvida.
- [ ] **P1 — Estado do Docker:** o Compose continua referenciando os contêineres antigos inexistentes `259dec67c8c7` e `4a0c3f5d3f80`, retornando código 1 ao tentar iniciá-los. API, web e worker novos estão executando as imagens corretas e saudáveis; o erro residual do gerenciador não foi ocultado. Reconciliar o Docker em janela de manutenção; não foi reiniciado o daemon, que hospeda outros serviços.
- [ ] **P1 — Limites de memória do host:** o Docker avisou que o kernel/cgroup não suporta os limites configurados e os descartou. `mem_limit` no Compose, neste host, não prova contenção efetiva de memória. Corrigir a configuração do host e validar os limites em manutenção; não alterei kernel/boot nem reiniciei a máquina.
- [ ] **P1 — Proveniência e qualidade:** acompanhar respostas reais com fontes atuais, casos de injeção de prompt e avaliações humanas. “Fonte verificada” não equivale a “cada afirmação provada”.
- [ ] **P2 — Paginação de notas eficiente:** a resposta foi limitada, mas o inventário ainda percorre o vault; substituir por consulta indexada/coerente com o watcher e paginação com cursor estável.
- [ ] **P2 — Anexos grandes:** harmonizar limites por categoria com o limite global do corpo. Atualmente base64 aumenta o tamanho; configurações de vídeo/áudio maiores não anulam o teto HTTP. Avaliar upload em streaming sem base64.
- [ ] **P2 — Idempotência e notificações:** contrato geral de `Idempotency-Key` e webhooks/eventos autenticados, evitando polling contínuo e criação duplicada após timeout. Idempotência interna de jobs não substitui a da API pública.
- [ ] **P2 — Modularidade:** reduzir concentração de lógica nos routers e em `second_brain.py`/`graph_write_service.py`; ampliar os módulos de domínio já existentes. Separar melhor contratos de aplicação, persistência e efeitos externos.
- [ ] **P2 — Dependências/operação:** fixar imagens opcionais que ainda usam `latest`, validar combinações de versões e política de atualização. Não atualizei provedores/imagens indiscriminadamente nesta revisão.
- [ ] **P2 — Documentação offline:** empacotar assets de Swagger/ReDoc para dispensar CDN; REST e OpenAPI JSON já funcionam sem essa dependência visual.
- [ ] **P3 — SDKs e delegação:** SDK TypeScript/Python versionados, fluxo de autorização delegada se necessário e exemplos de aplicações completas. O cliente incluído é referência executável, não um SDK certificado.
- [ ] **P3 — Escala/alta disponibilidade:** definir concorrência e durabilidade suportadas antes de múltiplas instâncias de API/worker em hosts diferentes. Não presumir que SQLite + locks de arquivos compartilham todas as garantias de um banco distribuído.

## Termos usados

API: interface de programação entre aplicações. REST: estilo de interface baseado em recursos e operações HTTP. OpenAPI: especificação legível por ferramentas do contrato HTTP. CRUD: criar, ler, atualizar e excluir. CSRF: falsificação de requisições entre sites, mitigada no fluxo de sessão por token vinculado ao cookie. Bearer: credencial que autoriza quem a apresenta; deve permanecer secreta. Lease: prazo renovável de posse temporária de um job. Claim token: identificador secreto da posse atual, que impede um worker antigo de concluir uma execução nova. Dead letter: job que esgotou o processamento normal e requer análise/retentativa explícita. RAG: geração aumentada por recuperação de conteúdo. Multi-hop: recuperação por múltiplos saltos entre relações. SDK: biblioteca cliente empacotada para desenvolvedores. CI: integração contínua. CORS: política do navegador para acesso entre origens. Tenant: unidade de isolamento de usuários/dados de uma plataforma.

## Publicação local inicial — sucedida pela 1.4.9

A publicação abaixo registra a primeira rodada. A versão atual, correções adicionais, checksums e confirmação em execução estão no [fechamento da release 1.4.9](2026-10-03-release-1.4.9.md).

Concluída em 2026-10-03. Imagens geradas e serviços atualizados somente para API, web e worker; HippoRAG preservado. Os quatro serviços estão `healthy`. Comparação de hashes encontrou zero divergências em sete fontes críticas da API e duas do worker; os três serviços atualizados usam exatamente as imagens construídas.

| Serviço | Imagem em execução (prefixo SHA-256) | Estado |
| --- | --- | --- |
| API | `41c52bdb49b50a3d` | healthy |
| Web | `d6b469087f6340c10` | healthy |
| Worker | `d92716bca5e3974e` | healthy |
| HippoRAG, não recriado | `f176f95662536d8b` | healthy |

A API publicada declara autenticação em **237/237 operações** do OpenAPI, incluindo declaração vazia para rotas intencionalmente públicas, e possui 84 schemas. Essa contagem de schemas não significa que todas as respostas já estejam tipadas. Health, descoberta, contrato, páginas de nós/arestas, Home e saúde da fila retornaram 200; leitura de Judge sem credencial retornou 401. Swagger e documentação pública passaram no navegador pelo mount `/berrybrain`.

O comando Compose retornou erro residual de IDs antigos, apesar de iniciar os serviços novos. Por isso a confirmação acima usa estado, ID da imagem e HTTP de cada serviço, não uma afirmação de sucesso do comando. A limpeza demorada de um contêiner temporário de verificação se concluiu; o contêiner de web anterior já existente foi preservado. Permanecem os alertas P1 de infraestrutura e latência.

Sem migração destrutiva, limpeza de vault, recriação de volume, commit/push automático ou alteração de credenciais reais. Arquivos e experimentos do TCC não foram alterados.
