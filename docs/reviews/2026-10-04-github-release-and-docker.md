# BerryBrain 1.4.9 — GitHub e manutenção do Docker

Esta etapa distingue publicação no servidor, publicação do código na `main` e
publicação de uma GitHub Release. O [relatório anterior](2026-10-03-release-1.4.9.md)
registra o build e a publicação **locais**, não uma release remota.

## Publicação do sistema

- [x] Confirmado: `main` remota em `b14eee8a6efc4d2523a3d0000f2c7f44a57639e7`;
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
- [ ] Corrigir e validar todos os bloqueios do CI; não desabilitar proteções.
- [ ] Publicar PR, acompanhar checks e incorporar à `main`.
- [ ] Publicar tag/release `v1.4.9` e confirmar `docs/api.md` na `main`.

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

Referências: [correção AnyIO/TLS](https://github.com/agronholm/anyio/security/advisories/GHSA-82r6-8w77-94w6),
[contenção de caminhos](https://codeql.github.com/codeql-query-help/python/py-path-injection/).
