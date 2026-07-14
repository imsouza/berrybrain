# Auditoria de Maturidade do BerryBrain

**Data:** 13 de julho de 2026  
**Escopo:** produto local-first, API, Worker, Web, Cognitive Layer, segurança, dados, instalação e release.  
**Resultado:** 302/307 critérios do planejamento concluídos (98,4%).
**Estado:** implementação e governança remota validadas; publicação da release 1.0 em andamento.

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

O produto não deve ser chamado de release 1.0 final até o histórico de estabilidade e os artefatos assinados listados nesta auditoria serem comprovados.

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
| Governança remota | OK | épicos, PRs, checks obrigatórios e proteção de `main` ativos |
| Release remoto | EM ANDAMENTO | exige histórico verde final, tag e artefatos assinados |

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

## Governança Remota

O repositório aplica:

- `CODEOWNERS` para `@imsouza`;
- formulário estruturado de épico;
- contato privado para segurança;
- workflows separados para API, Worker, Web, containers, segurança e CodeQL;
- workflow de release com imagens imutáveis, SBOM e assinatura;
- script idempotente `scripts/bootstrap-github-governance.sh`;
- seis épicos rastreáveis;
- proteção estrita de `main` com oito contextos obrigatórios;
- uma aprovação com CODEOWNERS, resolução de conversas e bloqueio de force-push/deleção;
- execução real de API, Worker, Web, Compose, segurança e CodeQL em pull requests.

O script exige uma sessão válida do GitHub CLI e não aceita nem persiste token no repositório.

## Evidência Remota

Evidências verificadas no GitHub:

1. [PR #7](https://github.com/imsouza/berrybrain/pull/7) corrigiu e validou os gates reais de CI;
2. [PR #8](https://github.com/imsouza/berrybrain/pull/8) tornou o smoke de container obrigatório e repetível;
3. `main` exige Backend, Worker, Web, Compose, Security e os contextos CodeQL;
4. o branch exige revisão de CODEOWNER e bloqueia force-push e deleção;
5. o smoke de container constrói as três imagens, executa Trivy, inicia a stack, roda o baseline e gera SBOM.
6. [12 execuções consecutivas](https://github.com/imsouza/berrybrain/actions/workflows/ci-container.yml) do smoke de container passaram no SHA `dfb1ecb3d8256d38791bc7ca7a3c0a4d479a127c` de `main`.

Gates ainda abertos neste documento:

1. criar a tag `v1.0.0`;
2. publicar imagens com tags imutáveis;
3. assinar as imagens publicadas;
4. publicar e atestar os SBOMs da release;
5. publicar esta auditoria junto da release final.

## Parecer Final

O BerryBrain já possui arquitetura e comportamento de segundo cérebro, não apenas editor com chatbot. A maturidade local é suficiente para uso self-hosted controlado e testes de release. A classificação correta, neste momento, é:

**Segundo cérebro funcional, localmente validado e protegido por CI; release 1.0 ainda não certificada.**

A certificação 100% depende agora de governança remota, histórico de estabilidade e publicação verificável dos artefatos de release.
