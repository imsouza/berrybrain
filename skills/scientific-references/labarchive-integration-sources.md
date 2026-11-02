---
id: sciref-labarchive-integration-sources
name: "Scientific Ref: Sources and Verification Notes"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (labarchive-integration): Sources and Verification Notes"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "labarchive integration sources"
  - "sources and verification notes"
keywords:
  - "labarchive"
  - "integration"
  - "sources"
  - "specialized"
  - "scientific"
  - "reference"
---

# Sources and Verification Notes

Research date: **2026-09-30**.

Official LabArchives help pages were read through the web tool. The shared API
notebook was read with fresh `parallel-cli extract` requests and by navigating
its public tree in Chrome, because basic extraction returned an empty shell
and one container-page extraction redirected to login. Browser reading resolved
that gap without authentication. PyPI and GitHub public metadata were checked
for optional community clients. No authenticated API requests, remote writes,
or product-integration transfers were performed.

## Official API sources

### ELN overview and regional API hosts

https://mynotebook.labarchives.com/share/LabArchives%20API/NS4yfDI3LzQvVHJlZU5vZGUvMTF8MTMuMg

- Page revision: **2025-11-03**
- Describes the ELN API as REST-like.
- Lists API hosts for US/rest of world, Australia/New Zealand, UK, Europe
  outside the UK, and Canada.
- Requires HTTPS.
- States that many responses are XML and child-element order is not fixed.

### Requirements and best practices

https://mynotebook.labarchives.com/share/LabArchives%20API/MTM2LjV8MjcvMTA1L1RyZWVOb2RlLzM2MzY3OTM2NjF8MzQ2LjU=

- Page revision: **2024-06-28**
- Credentials are issued for a specific organization/vendor and purpose.
- Large batches must be serialized or staggered by at least one second.
- HTTP 4xx responses must not be automatically retried.
- Eligible retries must wait at least one second, back off, and stop at a
  bounded count/duration.
- `expires` should represent current epoch milliseconds, with server-clock
  adjustment, not a future expiry.

### Call authentication

https://mynotebook.labarchives.com/share/LabArchives%20API/Ny44fDI3LzYvVHJlZU5vZGUvMTE1MzU5MTAyNXwxOS44

- Page revision: **2023-05-10**
- Defines Base64(HMAC-SHA-512) over the concatenation of Access Key ID, method
  input, and `expires`, using the Access Password as the HMAC key.
- Documents `akid`, `expires`, and URI-encoded `sig` query parameters.
- The published dummy test vector is reproduced by
  `scripts/entry_operations.py self-test`.

### API user login and UID

https://mynotebook.labarchives.com/share/LabArchives%20API/ODEuOXwyNy82My05My9UcmVlTm9kZS8yMjYyMTU0MTg3fDIwNy44OTk5OTk5OTk5OTk5OA==

- Page revision: **2023-03-03**
- Documents the signed `/api_user_login` redirect, returned `auth_code` and
  email, and redemption through `users::user_access_info`.
- Defines the user-generated temporary password token alternative.
- States that UIDs are bound to the Access Key ID and persist until revoked.

### ELN API class tree

https://mynotebook.labarchives.com/share/LabArchives%20API/MS4zfDI3LzEvVHJlZU5vZGUvODYxMDc1MjB8My4z

- Current tree includes entries, search tools, utilities, users, tree tools,
  notifications, notebooks, and site-license tools.
- Method pages, not names inferred from other clients, are the source of truth.

### ELN entry response elements

https://mynotebook.labarchives.com/share/LabArchives%20API/NjguOXwyNy81My9UcmVlTm9kZS8xODUxMDkwNDk2fDE3NC45

- Documents common `<entry>` XML fields and optional entry/comment data.
- Distinguishes attachment metadata from retrieval of attachment bytes.

### LA container file

https://mynotebook.labarchives.com/share/LabArchives%20API/Ni41fDI3LzUvVHJlZU5vZGUvNDQ3MDk3MTI0fDE2LjU=

- Original page revision shown as **2014-11-10**; the public page also contained
  an example-file revision dated **2026-03-02** at research time.
- Defines an LA container as a ZIP with `lamanifest.xml`, an application file,
  preview file, and UTF-8 index file.
- This format is not the same thing as a notebook-backup response.

### Inventory authentication

https://mynotebook.labarchives.com/share/LabArchives%20API/MTQ0LjN8MjcvMTExL1RyZWVOb2RlLzM5NjYzNjc4MjJ8MzY2LjI5OTk5OTk5OTk5OTk1

- Page revision: **2025-11-24**
- Inventory uses the shared LabArchives authentication flow.
- Requires a new signature for each exact relative route.
- Lists `X-LabArchives-UId`, `X-LabArchives-AKId`,
  `X-LabArchives-LabId`, `X-LabArchives-Signature`, and
  `X-LabArchives-Expires`.
- Route parameters are included in the signature input; query parameters are
  excluded. The method-specific `users/me` exception omits the Lab ID header.

### Inventory API v1 item creation

https://mynotebook.labarchives.com/share/LabArchives%20API/MTg4LjV8MjcvMTQ1L1RyZWVOb2RlLzEyOTcxODY5ODF8NDc4LjU=

- Page revision: **2026-04-02**
- The public navigation labels the Inventory surface **APIs (v1)**.
- Explicitly documents `POST /public/v1/inventory` and its JSON body fields.
- The navigation also exposes read/update item routes and sections for item
  types, orders, storage locations, and vendors.

### Method-level audit

Opened every endpoint named by this skill through **ELN API Classes** or
**Inventory > APIs (v1)** in the official notebook:

- `entries/entry_info`: GET, `uid`/`eid`, optional data/comment flags; XML.
- `entries/entry_attachment`: GET, `uid`/`eid`, raw application file and
  `Content-Disposition`, not an LA container ZIP.
- `notebooks/notebook_backup`: GET, owner `uid`/`nbid`, optional `json` and
  `no_attachments`; `.7z` archive. Internal archive schema remains access-gated.
- `users/user_access_info`: GET, `login_or_email` and authorization-code/token
  `password`, signed query; returns UID and auto-login permission in XML.
- `users/user_info_via_id`: GET with UID; honor auto-login permission and the
  documented restricted purpose of `authenticated=true`.
- `utilities/epoch_time`: GET with `akid`, no `sig`/`expires`; epoch milliseconds.
- `utilities/api_base_urls`: signed GET; XML region URL/description list. Its
  older example uses browser hosts, inconsistent with the newer API overview.
- Inventory `GET /public/v1/users/me`: lab discovery, no Lab ID needed;
  https://mynotebook.labarchives.com/share/LabArchives%20API/MTQ4LjIwMDAwMDAwMDAwMDAyfDI3LzExNC9UcmVlTm9kZS8zODc0Mjc0OTI5fDM3Ni4y
- Inventory `GET /public/v1/inventory`: JSON array, `pageSize` at most 1000,
  `pageNumber`, optional filters; out-of-stock items excluded by default.
  Page-number origin/default and stable ordering are not specified.
- Inventory `GET /public/v1/inventory/{itemId}`: one item JSON object, no query;
  https://mynotebook.labarchives.com/share/LabArchives%20API/MTg0LjZ8MjcvMTQyLTIyMC9UcmVlTm9kZS8zMzkzMTkwNjY5fDQ2OC41OTk5OTk5OTk5OTk5Nw==
- Inventory `GET /public/v1/inventory/{itemId}/attachments`: ZIP bytes.
- Inventory POST create and update: `name` and `typeId` marked r

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

