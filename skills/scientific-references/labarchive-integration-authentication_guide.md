---
id: sciref-labarchive-integration-authentication-guide
name: "Scientific Ref: LabArchives Authentication and Regions"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (labarchive-integration): LabArchives Authentication and Regions"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "labarchive integration authentication guide"
  - "labarchives authentication and regions"
keywords:
  - "labarchive"
  - "integration"
  - "authentication"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
  - "labarchives"
---

# LabArchives Authentication and Regions

Verified against official public sources on **2026-09-30**. LabArchives may
provide additional institution-specific development documentation with API
credentials; that documentation controls when it differs from this summary.

## Access prerequisites

### ELN

The official ELN subscription guide (updated 2026-08-27) lists developer API
access as an Enterprise capability. An Access Key ID and Access Password are
issued by LabArchives for a specific organization/vendor and intended purpose.
They are not ordinary account credentials.

Official source:
https://help.labarchives.com/hc/en-us/articles/11723701830676-ELN-for-Research-Introduction-and-Subscription-Plans

### Inventory API v1

The Inventory FAQ (updated 2026-05-19) states that API access is available only
to Enterprise and Enterprise Plus licensees. The caller must:

- have a LabArchives account,
- have an Inventory account,
- be given API access, and
- remain subject to Inventory application access rights.

An eligible Inventory license member can request access through
`support@labarchives.com`.

Official source:
https://help.labarchives.com/hc/en-us/articles/11811035048212-Inventory-FAQs

## Credential types

Keep these values distinct:

- **Access Key ID (`akid`)** — identifies the API client.
- **Access Password** — secret HMAC-SHA-512 key; it is never sent as an API
  parameter or request-body field.
- **UID** — user ID scoped to the Access Key ID that obtained it. It is
  persistent until revoked, but it is not portable across API keys.
- **Authorization code** — short-lived value returned by the API user-login
  flow and redeemed promptly through `users::user_access_info`.
- **Temporary password token** — user-generated alternative accepted as the
  `password` parameter by `users::user_access_info`.
- **Inventory Lab ID** — identifies the current Inventory lab and is documented
  as `X-LabArchives-LabId`; the `/public/v1/users/me` bootstrap endpoint does
  not require this header and ignores it if supplied.

Do not use a normal LabArchives account password in API scripts.

## Regional browser and ELN API hosts

The two host types are intentionally shown in separate columns. Login URLs come
from the help-center SSO article updated **2025-11-04**; API URLs come from the
official ELN API overview updated **2025-11-03**.

| Region | Browser login | ELN API URL |
|---|---|---|
| US and rest of world | `https://mynotebook.labarchives.com` | `https://api.labarchives.com/api` |
| Canada | `https://ca-mynotebook.labarchives.com` | `https://caapi.labarchives.com/api` |
| Australia/New Zealand | `https://au-mynotebook.labarchives.com` | `https://auapi.labarchives.com/api` |
| United Kingdom | `https://uk-mynotebook.labarchives.com` | `https://ukapi.labarchives.com/api` |
| Europe outside the UK | `https://eu-mynotebook.labarchives.com` | `https://euapi.labarchives.com/api` |

Official sources:

- https://help.labarchives.com/hc/en-us/articles/11728160845332-Using-an-Institutional-Single-Sign-on-for-LabArchives-Access
- https://mynotebook.labarchives.com/share/LabArchives%20API/NS4yfDI3LzQvVHJlZU5vZGUvMTF8MTMuMg

The official ELN overview recommends `utilities::api_base_urls` for distributed
applications so they can discover future regional API additions. The bundled
validator intentionally pins the five hosts documented at this refresh date.

### Inventory absolute base URLs

The official notebook's **Inventory > Overview** publishes
`https://iapi.labarchives.com` as the base URL for current endpoints. Append the
exact `/public/v1/...` route. It specifies `Content-Type: application/json` for
requests; responses can be JSON or ZIP depending on the method. A regional
absolute base-URL table is not provided. Confirm any region-specific deployment
with LabArchives rather than deriving a host from a browser login URL.

### Inventory lab discovery

`GET /public/v1/users/me` explicitly does not require `X-LabArchives-LabId`
(and ignores it if supplied). Sign `/public/v1/users/me` and send the UID,
Access Key ID, signature, and expires headers. The JSON response contains
`userId`, `userName`, `status`, and `labs` entries with `labId` and `name`. Select
an authorized lab before issuing lab-scoped requests. The numeric Inventory
`userId` is not the Access-Key-scoped ELN UID used for authentication.

Official method page:
https://mynotebook.labarchives.com/share/LabArchives%20API/MTQ4LjIwMDAwMDAwMDAwMDAyfDI3LzExNC9UcmVlTm9kZS8zODc0Mjc0OTI5fDM3Ni4y

## Named environment variables

These names are conventions used by this skill's local helpers:

```text
LABARCHIVES_ELN_API_URL
LABARCHIVES_ACCESS_KEY_ID
LABARCHIVES_ACCESS_PASSWORD
LABARCHIVES_USER_ID
LABARCHIVES_INVENTORY_LAB_ID
```

Use a shell session, OS keychain, workload secret store, or institution-approved
secret manager to populate them. The scripts:

- inspect only these exact names,
- never walk parent directories for `.env`,
- never write secret files, and
- never print credential values.

Validate presence and endpoint selection:

```bash
uv run scripts/setup_config.py check
uv run scripts/setup_config.py check \
  --require-user-id --require-inventory-lab-id
```

`--prompt-missing-secret` uses `getpass` for a missing Access Password and keeps
the value in memory only. It does not save or authenticate it.

## ELN API user authorization

The official page describes an **OAuth-like** redirect flow. It does not
document generic OAuth 2.0 client credentials, `/oauth/authorize`, or
`/oauth/token` endpoints.

1. Select the user's correct regional API host.
2. Redirect the user to the host's `/api_user_login` path with `akid`,
   `expires`, `sig`, and `redirect_uri`.
3. For this special signature, use the exact **unencoded redirect URI** in place
   of the normal API method name.
4. LabArchives performs account/SSO login and redirects back with `auth_code`
   and `email`.
5. Promptly call the documented `users::user_access_info`, passing the
   authorization code as its `password` parameter and the returned email as
   `login_or_email`. The method uses GET query parameters, so redact the whole
   query and any echoed authentication fields in the XML response.
6. Store the resulting UID only in approved secure state. It remains bound to
   the Access Key ID and can be revoked. Respect `<auto-login-allowed>` and
   institutional restrictions; `user_info_via_id` documents `authenticated=true`
   only for an explicit user request to extend the 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

