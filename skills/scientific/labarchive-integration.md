---
id: sci-labarchive-integration
name: "Scientific: labarchive-integration"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Integrates with the official LabArchives ELN REST-like API and Inventory API v1. Supports regional endpoint selection, signed-request construction, user authorization and UID flows, local LA container validation, and verified LabArchives integration workflows."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "labarchive integration"
  - "labarchive-integration"
keywords:
  - "labarchive"
  - "integration"
  - "integrates"
  - "official"
  - "labarchives"
  - "rest"
  - "like"
  - "inventory"
---

# LabArchives Integration

Use LabArchives APIs only from current, official method pages. The public
documentation is a shared notebook, not a versioned SDK reference, so verify the
specific page immediately before implementing a remote operation.

## Choose the Correct Surface

Do not combine these interfaces:

- **Legacy ELN API:** notebook trees, entries, attachments, users, searches,
  exports, and site-license functions. It uses regional `*api.labarchives.com`
  hosts, `/api/<class>/<method>` paths, XML for many responses, and signed query
  parameters.
- **Inventory API v1:** inventory, item types, orders, storage locations, and
  vendors. It documents relative `/public/v1/...` paths, JSON response schemas,
  and signed `X-LabArchives-*` request headers.
- **Product integrations:** Jupyter, REDCap, Protocols.io, GraphPad Prism,
  SnapGene, Geneious, and others are product-specific UI or file workflows.
  They are not evidence of a general LabArchives OAuth 2.0 API.

Read [`references/api_reference.md`](references/api_reference.md) before writing
API code and [`references/integrations.md`](references/integrations.md) before
automating an advertised integration.

## Access and Credentials

LabArchives ELN developer API access is an Enterprise capability. The current
Inventory FAQ limits Inventory API access to Enterprise and Enterprise Plus
licensees and requires an Inventory account with API permission. Contact the
institution's LabArchives team or LabArchives support for access and the
development documentation supplied with it.

The environment names below are conventions of this skill, not vendor-defined
standards:

- `LABARCHIVES_ELN_API_URL` — one exact regional ELN API URL ending in `/api`
- `LABARCHIVES_ACCESS_KEY_ID` — LabArchives-issued Access Key ID (`akid`)
- `LABARCHIVES_ACCESS_PASSWORD` — HMAC signing secret
- `LABARCHIVES_USER_ID` — optional persistent UID bound to that Access Key ID
- `LABARCHIVES_INVENTORY_LAB_ID` — required for lab-scoped Inventory requests;
  omitted during `GET /public/v1/users/me` lab discovery

Keep secrets in the process environment or an approved secret manager. Do not
put them in YAML, source code, command-line arguments, prompts, logs, notebooks,
or committed `.env` files. The bundled tools never search for `.env` files.

From this skill directory:

```bash
uv run scripts/setup_config.py regions
uv run scripts/setup_config.py check --require-user-id
```

`setup_config.py` validates only endpoint structure and named-variable presence;
it does not authenticate, persist, or print credentials. See
[`references/authentication_guide.md`](references/authentication_guide.md).

## Regional Endpoints

Browser login hosts and API hosts are different. The official ELN API overview
currently lists US/rest of world, Australia/New Zealand, UK, Europe outside the
UK, and Canada API hosts. The help center separately lists the five regional
browser login hosts.

Use `setup_config.py regions` for the current allowlist and the complete table in
the authentication guide. Never build an API URL from a browser login URL.

The Inventory overview publishes `https://iapi.labarchives.com` as its API base
URL; append the documented `/public/v1/...` route. No regional base-URL table is
published there. Confirm any regional deployment with the institution/vendor;
do not transform an Inventory browser login host into an API hostname.

## Authentication Model

### ELN requests

The official algorithm is fully documented:

1. Set `expires` to the current Unix epoch time in milliseconds, adjusted for
   server clock difference if necessary. Despite its name, it is not a future
   expiry time.
2. Concatenate, with no separators:
   `<Access Key ID><API method name><expires>`.
3. Compute HMAC-SHA-512 using the Access Password as the key.
4. Base64-encode the digest.
5. URI-encode that signature and send `akid`, `expires`, and `sig` as the
   documented query parameters.

For ordinary ELN calls, the signature input is the method name only, not the API
class. User authorization is a documented special case: signing the
`api_user_login` redirect uses the unencoded redirect URI in place of a method
name.

### Inventory API v1 requests

Inventory shares the HMAC algorithm but signs the exact relative route, including
resolved path parameters and excluding the query string. Its authentication page
documents these headers:

- `X-LabArchives-UId`
- `X-LabArchives-AKId`
- `X-LabArchives-LabId`
- `X-LabArchives-Signature`
- `X-LabArchives-Expires`

The `GET /public/v1/users/me` method explicitly exempts `X-LabArchives-LabId`
and ignores it if supplied. Call it with the other four headers, select an
authorized `labs[].labId`, then include that Lab ID for lab-scoped calls. Its
numeric `userId` is Inventory-specific; do not substitute it for the ELN UID.

Create a fresh signature for every request. Do not move ELN query authentication
into Inventory headers or Inventory headers into ELN calls.

## Local Request Planning

`scripts/entry_operations.py` is deliberately network-free. It implements the
documented signature primitive and emits redacted JSON plans, never a live
request or reusable signature:

```bash
uv run scripts/entry_operations.py self-test
uv run scripts/entry_operations.py eln-plan \
  --api-class entries --api-method entry_info
uv run scripts/entry_operations.py inventory-plan \
  --path /public/v1/users/me
```

Import its `create_signature`, `build_eln_auth_params`, or
`build_inventory_headers` functions into institution-reviewed code when needed.
Pass returned authentication material directly to the HTTP client; never print
or persist it.

Before any remote write:

1. Open the exact official method page and verify verb, path, parameters, body,
   and response schema.
2. Produce a dry-run plan with identifiers and sensitive values redacted.
3. Confirm the target region, notebook/lab, and user-visible effect.
4. Require explicit approval before sending.
5. Re-read and verify the resulting object; do not infer success from HTTP 200
   alone when the method documents a response body.

The bundled scripts perform no remote writes.

## Local LA Container Inspection

An **LA container** is a ZIP file with `lamanifest.xml`, an application file,
a preview file, and a UTF-8 index file. The manifest marks `caption` and
`change_description` optional. It is not synonymous with a notebook backup.
Inspect one without extracting it:

```bash
uv run scripts/notebook_operations.

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

