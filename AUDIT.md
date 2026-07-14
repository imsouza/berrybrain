# Auditoria de Maturidade do BerryBrain

**Data:** 13 de julho de 2026  
**Escopo:** produto local-first, API, Worker, Web, Cognitive Layer, segurança, dados, instalação e release.  
**Resultado local:** 295/307 critérios do planejamento concluídos (96,1%).  
**Estado:** implementação local pronta; release 1.0 bloqueada por gates remotos e histórico de CI.

## Conclusão Executiva

O BerryBrain implementa o núcleo de um segundo cérebro funcional:

- notas Markdown reais permanecem como fonte primária;
- o Worker executa um pipeline cognitivo persistido;
- chunks e embeddings alimentam recuperação semântica;
- nós e arestas representam notas, conceitos, tópicos, entidades, lacunas e insights;
- conexões e insights mantêm motivo, evidência, confiança e origem;
- a busca do grafo combina dados das notas, memória semântica e estrutura do grafo;
- jobs, falhas e diagnósticos ficam separados de insights de conhecimento;
- ações no grafo são persistidas, reversíveis e registradas;
- anexos podem se tornar fontes cognitivas com extração, OCR e transcrição controlados;
- autenticação protege uma conta owner local, sem senha padrão.

O produto não deve ser chamado de release 1.0 final até os gates remotos listados nesta auditoria serem comprovados.

## Evidência Reproduzida

| Área | Evidência | Resultado |
|---|---|---|
| API | suíte unitária e de integração | 156 testes aprovados |
| Worker | integração, fallbacks, prompts e resiliência | 34 testes aprovados |
| Web | Playwright contra API e banco descartáveis | 13/13 aprovados |
| Build Web | `next build` de produção | aprovado |
| Tipos | TypeScript `--noEmit` | aprovado |
| Diff | `git diff --check` | aprovado |
| Instalação | projeto Compose isolado | Web, API e Worker saudáveis |
| Pipeline | nota descartável em instalação limpa | 100% em 82s |
| Busca | busca da nota descartável | 19ms |
| Worker | heartbeat no Compose limpo | running, zero erros antes do pipeline |
| Dados | banco, volume e vault descartáveis | ambiente real não alterado |

## Correções Encontradas Pela Validação Limpa

### Host interno do Worker

O Worker usa `http://api:8000`, mas o hostname `api` não fazia parte de `BERRYBRAIN_ALLOWED_HOSTS`. O middleware retornava HTTP 400, o Worker reiniciava e os jobs não eram processados.

Correção:

- Compose sempre adiciona `api` aos hosts permitidos;
- `.env.example` e README documentam o hostname interno;
- o smoke limpo confirmou heartbeat e processamento.

### Arquivo de ambiente do Compose

Os serviços fixavam `env_file: .env`, impedindo instâncias isoladas e testes reprodutíveis.

Correção:

- `BERRYBRAIN_ENV_FILE` seleciona um arquivo alternativo;
- `.env` continua sendo o padrão;
- credenciais descartáveis podem ser usadas sem modificar a configuração real.

## Avaliação por Subsistema

| Subsistema | Estado | Observação |
|---|---|---|
| Vault Markdown | OK | arquivos reais, watcher, scan, links e frontmatter |
| Editor | OK | edição, autosave, anexos e navegação |
| Job Engine | OK | claim, lease, retry, dead-letter, heartbeat e progresso |
| Model Router | OK | local/cloud, consentimento remoto e rastreabilidade |
| Knowledge Base | OK | chunking, embeddings e retrieval híbrido persistido |
| Knowledge Graph | OK | nós e arestas persistidos, explicáveis e deduplicados |
| Graph Inference | OK | respostas fundamentadas e recusa por evidência insuficiente |
| Insight Engine | OK | insights de conhecimento separados de diagnósticos técnicos |
| Reviews | OK | revisão derivada de evidência, sem sistema legado de flashcards |
| Attachments | OK | limites, segurança, extração, OCR e Faster Whisper |
| Home | OK | status, progresso, aprendizados, atenção e atividade |
| Monitor/Activity | OK | backlog, falhas, jobs e detalhes técnicos |
| Auth | OK | owner único, setup one-shot, rate limiting e sessões seguras |
| Backup/Restore | OK | manifesto, checksum, restauração e migrações versionadas |
| Landing/Docs | OK | produto, arquitetura, confiabilidade e login documentados |
| Containerização | OK | Web, API e Worker iniciam no comando padrão |
| Release remoto | PENDENTE | exige GitHub autenticado, CI histórico e tag real |

## Segurança

Controles implementados:

- senha forte criada pelo owner; não existe senha padrão `admin`;
- erros de autenticação genéricos;
- rate limiting e lockout;
- cookie de sessão e proteção CSRF;
- token de serviço com rotação;
- allowlist de hosts e CORS;
- consentimento explícito para conteúdo enviado a provider remoto;
- redação de segredos em logs;
- validação de paths e anexos;
- sandbox e timeout para extratores;
- política de conteúdo não confiável contra prompt injection;
- ações destrutivas com confirmação e escopo explícito.

## Integridade Cognitiva

Um artefato de conhecimento só é válido quando possui origem verificável. O sistema aplica as seguintes regras:

- insight sem evidência de nota, conceito ou conexão não entra como Knowledge Insight;
- diagnóstico de jobs pertence ao Monitor/Activity;
- conexão de IA exige motivo, confiança e evidência;
- inferência sem suporte responde com evidência insuficiente;
- provider, modelo e prompt version são registrados quando aplicáveis;
- nós sugeridos e conexões sugeridas podem ser confirmados ou ignorados;
- escrita canônica reduz duplicidade de nós e arestas;
- notas do usuário não são traduzidas automaticamente.

## Governança Preparada

O repositório contém:

- `CODEOWNERS` para `@imsouza`;
- formulário estruturado de épico;
- contato privado para segurança;
- workflows separados para API, Worker, Web, containers, segurança e CodeQL;
- workflow de release com imagens imutáveis, SBOM e assinatura;
- script idempotente `scripts/bootstrap-github-governance.sh`.

O script exige uma sessão válida do GitHub CLI e não aceita nem persiste token no repositório.

## Gates Remotos Pendentes

Os seguintes critérios dependem do GitHub e não podem ser comprovados apenas pelo worktree:

1. abrir e atribuir os épicos reais;
2. proteger `main`;
3. exigir todos os checks antes do merge;
4. exigir uma revisão;
5. obter dez execuções consecutivas verdes no `main`;
6. criar a tag `v1.0.0` somente após o histórico verde;
7. publicar imagens com tags imutáveis;
8. assinar as imagens publicadas;
9. publicar o SBOM da release;
10. comprovar CI verde para o commit final;
11. publicar esta auditoria no commit/release final.

O repositório público mostrava, na data desta auditoria, zero issues, duas execuções históricas de workflow e nenhuma release. Portanto, esses itens permanecem abertos.

## Parecer Final

O BerryBrain já possui arquitetura e comportamento de segundo cérebro, não apenas editor com chatbot. A maturidade local é suficiente para uso self-hosted controlado e testes de release. A classificação correta, neste momento, é:

**Segundo cérebro funcional e localmente validado; release 1.0 ainda não certificada.**

A certificação 100% depende agora de governança remota, histórico de estabilidade e publicação verificável dos artefatos de release.
