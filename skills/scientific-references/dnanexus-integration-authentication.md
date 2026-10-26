---
id: sciref-dnanexus-integration-authentication
name: "Scientific Ref: Authentication and Context"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dnanexus-integration): Authentication and Context"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dnanexus integration authentication"
  - "authentication and context"
keywords:
  - "dnanexus"
  - "integration"
  - "authentication"
  - "specialized"
  - "scientific"
  - "reference"
---

# Authentication and Context

## Principles

DNAnexus bearer tokens act as the creating user within the token's scope. They
can launch billable jobs where both user and token permissions allow it. Treat
`DX_SECURITY_CONTEXT` as a secret:

- Never print, log, serialize, return, or commit it.
- Never place a token directly in source code, notebooks, input JSON, job
  properties, tags, or command output.
- Never read or export the entire environment to locate the token.
- Use only the named DNAnexus credential supplied by the user or secret
  manager.
- Do not send it to any non-DNAnexus endpoint.

`dx env` and `dx env --bash` display the active token. Do not run either command
in captured terminals, CI logs, support bundles, or agent output.

## Interactive Login

Install `dxpy`, then authenticate:

```bash
dx login
dx whoami
dx select
dx pwd
```

`dx login` stores CLI state under `~/.dnanexus_config/`. Use `dx whoami` and
`dx pwd` to verify identity and project without exposing the token.

New login sessions under the normal security policy expire after two hours of
inactivity and no later than 18 hours after issuance. Organization policies can
shorten these limits. This includes UI, username/password CLI, and SSO
sessions; API tokens and job tokens have separate lifetimes.

For SSO accounts, follow the organization's login/token workflow. User-generated
API tokens cannot access resources in the UKB RAP region, including tokens
issued before this restriction. Use the supported interactive session workflow
there. Keep login interactive; avoid token values in shell history or transcripts.

## Token Login and Automation

The CLI supports `dx login --token TOKEN`, but placing the literal token on a
command line can expose it through shell history or process inspection.
Preferred automation:

1. Where API tokens are supported, create a short-lived token in the DNAnexus UI
   under **My Profile → API Tokens → New Token**. Choose **Selected projects**
   and the minimum required access level for each project.
2. Use a dedicated user/service identity with only the required project access.
3. Store the complete security context in the CI or orchestration secret
   manager under the exact key `DX_SECURITY_CONTEXT`.
4. Inject that single key directly into the process environment.
5. Mask the key in logs and never enable shell tracing around authentication.
6. Verify with `dx whoami`; do not use `dx env`.
7. Remove the secret from the process environment when the operation ends.

`DX_SECURITY_CONTEXT` must contain JSON text, not a bare UI token. Its secret
value has this shape:

```json
{
  "auth_token_type": "Bearer",
  "auth_token": "<secret-token>"
}
```

Have the secret manager inject the complete serialized object. Do not build or
echo it in a traced shell command.

Tokens with **All projects** have the account's access across projects,
including PHI data. **Selected projects** tokens limit access to the selected
projects and levels; they cannot exceed the creating user's permissions.
Some administrative APIs require a full-scope token even when the user has
the relevant project access. A permission failure can therefore reflect token
scope as well as project membership. Minimize both, and never broaden scope
automatically to make a failing command work.

Tokens created without an explicit expiration expire after one month according
to current platform guidance. Choose a shorter expiration whenever practical.

### Tool-specific variable names

- `dx` and `dxpy` primarily consume the JSON `DX_SECURITY_CONTEXT`.
- The dx-toolkit shell bootstrap maps `DX_AUTH_TOKEN` into
  `DX_SECURITY_CONTEXT` only when `DX_SECURITY_CONTEXT` is absent.
- Download Agent (`dx-download-agent`) checks `DX_API_TOKEN`; when absent, it
  falls back to `~/.dnanexus_config/environment.json`.

These names are all sensitive but are not generic substitutes in every tool.
Inject only the variable required by the selected client, and never mirror one
secret into multiple variables without a concrete compatibility need.

## Configuration Precedence

DNAnexus utilities resolve configuration in this order:

1. Command-line overrides
2. Environment variables already set in the shell
3. `~/.dnanexus_config/environment.json`
4. Built-in defaults

This means a stale `DX_SECURITY_CONTEXT` in the shell overrides a later
interactive `dx login`. A login can appear successful while subsequent
commands still use the older shell credential.

### Diagnose a context mismatch safely

Use only non-secret commands:

```bash
dx whoami
dx pwd
```

If the shell environment should be discarded in favor of the saved CLI state:

```bash
source "$HOME/.dnanexus_config/unsetenv"
dx whoami
dx pwd
```

If the saved CLI state should be discarded instead:

```bash
dx clearenv
```

Do not print either source to compare token values.

## Project Context

Select a project interactively:

```bash
dx select
dx pwd
```

For scripts, prefer explicit project IDs and full paths instead of relying on
ambient context:

```bash
dx ls "project-xxxx:/input"
dx download "project-xxxx:/input/sample.bam" --output "sample.bam"
```

In Python, pass `project="project-xxxx"` to searches, uploads, downloads when
needed for billing context, and executable runs. Explicit context prevents a
script from silently operating on the project selected in another terminal.

## Execution-Environment Credentials

Jobs receive a job-scoped security context from the platform. `dxpy` and `dx`
consume it automatically. App code normally should not parse
`DX_SECURITY_CONTEXT`.

Within an Application Execution Environment:

- Use the system-provided API host and security context unchanged.
- Do not forward the job environment to child processes that do not require it.
- If a subprocess needs only local computation, pass a minimal allowlisted
  environment.
- Never upload environment dumps, crash reports containing environment values,
  or shell traces.
- Do not override the internal API host with a user-controlled hostname.

Job authorization is inherited from the root execution and can expire. Current
documentation limits job authentication tokens to 30 days, which aligns with
the normal maximum job runtime.

## Endpoint Safety

For normal external clients, DNAnexus uses official hosts such as:

- `api.dnanexus.com` for API calls
- `auth.dnanexus.com` for authentication
- `platform.dnanexus.com` for the web interface

Inside jobs, the platform may supply a private API address. Accept onl

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

