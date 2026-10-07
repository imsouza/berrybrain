# BerryBrain 1.4.9 — GitHub e manutenção do Docker

Esta etapa distingue publicação no servidor, publicação do código na `main` e
publicação de uma GitHub Release. O [relatório anterior](2026-10-03-release-1.4.9.md)
registra o build e a publicação **locais**, não uma release remota.

## Publicação do sistema

- [x] Verificação inicial em 04/10: `main` remota em `b14eee8a6efc4d2523a3d0000f2c7f44a57639e7`;
  `docs/api.md` ainda não estava publicado; tag `v1.4.9` ausente.
- [x] Permissões de publicação verificadas. `main` exige PR e checks; as proteções
  serão preservadas, sem force-push ou bypass administrativo.
- [x] Inventariadas 496 alterações/arquivos locais. Arquivos do TCC, resultados de
  pesquisa, bancos, vault e credenciais não serão adicionados a esta release.
- [x] Separados 142 arquivos do sistema; README com staging parcial para preservar
  as alterações acadêmicas locais sem publicá-las nesta release.
- [x] Gitleaks 8.30.1 aprovado antes do push, sem achados. O executável oficial foi
  conferido pelo checksum publicado. Um literal fictício de teste foi marcado
  explicitamente, e hashes de fontes foram representados como pares caminho/SHA-256;
  nenhuma regra global foi desativada.
- [x] Ruff 0.6.9, versão usada no CI, aprovado nos 88 arquivos Python da mudança.
- [x] Cópia limpa do primeiro commit: 694 verificações Python em 85 módulos,
  sem falhas ou skips. ESLint completo da interface também aprovado.
- [x] [PR #26](https://github.com/imsouza/berrybrain/pull/26) publicado. A primeira
  rodada de CI aprovou worker e testes isolados, mas encontrou erros de tipagem,
  alertas CodeQL, dependência vulnerável e falhas no smoke de navegador.
- [x] Corrigidos os bloqueios originais do CI no commit `50bc7a0`; todos os nove
  checks do PR #26 aprovados em 05/10, sem desabilitar proteções.
- [x] Segunda correção local: 73 verificações em seis módulos isolados passaram,
  sem falhas ou skips; sem acesso à rede, ao banco real ou a provedores de IA.
- [x] Alerta CodeQL 67 triado como falso positivo com justificativa específica;
  regra e proteções de branch permanecem ativas.
- [x] Terceira rodada: segurança, CodeQL, web, worker e testes isolados aprovados.
  O backend passou nos testes, mas a cobertura ficou abaixo do mínimo de 78,5%.
- [x] Incluir a cobertura dos testes de regressão isolados na medição do backend
  e validar novamente os limites total, crítico e de regressão, sem reduzi-los.
  Resultado: 80,62% de cobertura combinada, 90,49% em jobs e 100% nos endpoints
  de tokens. A suíte principal executou 486 testes; nove módulos de regressão
  executaram 129 verificações. A suíte global isolada executou 709 verificações
  em 86 módulos, sem falhas ou skips. As suítes se sobrepõem: não somar contagens.
- [x] PR #26 incorporado à `main` em 07/10/2026, commit
  `30cca75ed72d6cf3b5efb031814a6d87a65d0a33`.
- [x] [docs/api.md publicado na main](https://github.com/imsouza/berrybrain/blob/main/docs/api.md),
  verificado pela API do GitHub: 12.452 bytes.
- [x] Tag `v1.4.9` criada no commit do merge; a GitHub Release ainda não foi publicada.
- [ ] Concluir correção de segurança identificada no novo audit de 07/10 e decidir
  o destino da tag antes de retomar imagens, assinaturas e GitHub Release.

### Validação adicional em 07/10/2026

O [audit da main](https://github.com/imsouza/berrybrain/actions/runs/37610832325)
encontrou GHSA-68fv-2mgg-jv7q em `source-map-js` 1.2.1. O aviso foi revisado em
05/10, depois do audit anterior; a versão corrigida é 1.2.2. O pacote entra pela
cadeia PostCSS. O override e o lockfile foram atualizados para impedir instalar a
versão vulnerável, sem atualização incompatível de framework.

- [x] [Pipeline de release 37610960174](https://github.com/imsouza/berrybrain/actions/runs/37610960174)
  cancelado antes da publicação da GitHub Release; não substituiu os serviços locais.
- [ ] Validar e incorporar a correção adicional por PR com os checks obrigatórios.
- [ ] Obter a escolha do responsável: recriar apenas a tag recém-criada e ainda
  sem release, ou preservar a tag e publicar a correção como uma nova versão.
  Não foi feito force-push nem removida qualquer tag.

## Docker do host

- [x] API, web, worker e HippoRAG continuam em execução e saudáveis.
- [x] Confirmada inconsistência: os IDs `259dec67c8c7` e `4a0c3f5d3f80`
  aparecem como `Dead` na listagem, mas `inspect` retorna `no such object`.
- [x] Há 34 contêineres em execução de outros projetos. `LiveRestoreEnabled=false`.
  Não se deve reiniciar globalmente o Docker como se afetasse apenas o BerryBrain.
- [x] Acesso administrativo verificado: `sudo -n` exige autenticação. A existência
  dos diretórios internos dos dois IDs **não foi determinada** por essa consulta.
- [ ] Obter autorização de manutenção global e uma sessão administrativa, sem
  solicitar ou armazenar senha no chat.
- [ ] Executar recuperação suportada do daemon, preservando dados e conferindo
  serviços antes/depois; verificar novamente os IDs e o Compose.

A hipótese é estado residual do daemon, não dados ativos do BerryBrain. Ainda
não há evidência suficiente para prometer que um reinício será a única medida
necessária. Não serão apagados diretórios internos, volumes ou backups para
forçar a limpeza. A documentação do Docker descreve
[live restore](https://docs.docker.com/engine/daemon/live-restore/) como proteção
para manter contêineres executando durante indisponibilidade do daemon; habilitá-lo
e validar sua configuração exige manutenção administrativa do host.

## Correções adicionais exigidas pelo CI

- AnyIO: elevar o mínimo para 4.14.2, que contém as correções apontadas pelo
  pip-audit/Trivy; a versão 4.9.0 estava presa pelo limite antigo `<4.10`.
- Tipagem: explicitar o resultado de atualização SQLAlchemy e as tuplas das
  arestas usadas no resumo do grafo.
- Pastas: normalizar caminhos reais, validar prefixo com separador, rejeitar
  caminhos absolutos/Windows, bytes nulos e symlinks que escapam do vault.
- Markdown do relatório operacional: escapar também barras invertidas.
- Hashes de tokens: usar a API HMAC explícita, preservando o digest já armazenado.
  O fluxo do alerta CodeQL partia de `settings.api_token`, não de senhas de usuário;
  senhas continuam com Argon2id/PBKDF2. A compatibilidade tem teste de regressão.
- Dependências web: atualizar Next.js e eslint-config-next para a linha corrigida
  15.5.27 e exigir Sharp >= 0.35.4. A segunda rodada de CI identificou RCE na
  otimização de imagens e problemas na dependência nativa anterior; o audit Python
  já passou com o novo limite do AnyIO.
- Executor de testes: converter os quatro testes unitários de seleção de trechos
  para `unittest`, o executor do CI backend. Antes, o import de pytest falhava
  nesse job; simplesmente instalar pytest não faria suas funções serem executadas
  pelo discovery de unittest.
- Contenção de pastas: separar o retorno da raiz canônica da verificação de
  descendentes. A checagem agora também trata corretamente o separador da raiz do
  sistema de arquivos; os casos de raiz vazia e caminhos aninhados têm regressões.

### Revisão do alerta CodeQL de hash de tokens

O [alerta 67](https://github.com/imsouza/berrybrain/security/code-scanning/67)
classifica o token de serviço legado como senha. O SARIF da análise Python
1890514415 mostra quatro fluxos: as duas migrações de `settings.api_token` em
`security.py` e duas chamadas nos testes de ciclo de vida de tokens. Nenhum
fluxo parte da senha de login. O destino é HMAC-SHA256 com chave separada
`session_secret`, usado para comparar identificadores opacos sem armazenar o
token em claro. Tokens novos usam 48 bytes aleatórios; senhas de usuário seguem
Argon2id ou PBKDF2-HMAC-SHA256 com 600.000 iterações.

A classificação de algoritmo rápido para **senha** é um falso positivo nesse
fluxo de token. A triagem deve limitar-se a esse alerta, com justificativa
registrada no GitHub; não desabilita a regra nem aceita outros achados. Manter o
digest evita invalidar silenciosamente sessões e integrações existentes. O token
legado configurado pelo operador deve ser forte e pode ser substituído pelos
tokens gerenciados aleatórios documentados na API.

### Pendência da cadeia de desenvolvimento

- [x] Atualizações compatíveis adicionais corrigiram avisos de brace-expansion,
  browserslist, js-yaml e baseline-browser-mapping no lockfile.
- [ ] Acompanhar correção upstream de `braces` (GHSA-vfj7-8cjw-p6xm) ou planejar
  migração compatível da cadeia Tailwind/ESLint. O audit completo ainda aponta
  sete pacotes de desenvolvimento afetados pela mesma dependência sem versão
  corrigida. Não foi aplicado `npm audit fix --force`, que propõe mudanças
  incompatíveis de ferramentas. Não executar build/lint de código ou configuração
  não confiáveis. Este alerta não deve ser apresentado como corrigido.

Referências: [correção AnyIO/TLS](https://github.com/agronholm/anyio/security/advisories/GHSA-82r6-8w77-94w6),
[contenção de caminhos](https://codeql.github.com/codeql-query-help/python/py-path-injection/),
[correção Next.js](https://github.com/advisories/GHSA-2xp9-vwfh-vxw4),
[correção Sharp](https://github.com/advisories/GHSA-rgj7-g3m4-5g8c),
[correção source-map-js](https://github.com/advisories/GHSA-68fv-2mgg-jv7q).
