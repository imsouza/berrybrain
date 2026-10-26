---
id: sciref-adaptyv-api-endpoints
name: "Scientific Ref: Adaptyv Foundry endpoint reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (adaptyv): Adaptyv Foundry endpoint reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "adaptyv api endpoints"
  - "adaptyv foundry endpoint reference"
keywords:
  - "adaptyv"
  - "api"
  - "endpoints"
  - "specialized"
  - "scientific"
  - "reference"
  - "foundry"
---

# Adaptyv Foundry endpoint reference

Reviewed 2026-09-30 against the deployed
[OpenAPI 0.0.2 schema](https://devs.adaptyvbio.com/api/v1/openapi.json), the
[API guide](https://docs.adaptyvbio.com/api-reference/api-introduction), and
[official SDK source](https://github.com/adaptyvbio/adaptyv-sdk/tree/cdf207819ed5a58e0c127453626d2bce125c8064).
All paths below are relative to `https://devs.adaptyvbio.com/api/v1`.

## Endpoint inventory

These are the 43 operations in the reviewed schema. Schema names refer to
`components.schemas` in the linked OpenAPI document. `Page<T>` means
`{items: T[], total, count, offset}`. Most pages use inline item schemas;
use the operation's response definition when a name is not provided.
The table lists success responses; detailed constraints follow it.

| Method and path | JSON request schema | Success response |
|---|---|---|
| `GET /experiments` | `None` | `200 Page<inline item>` |
| `POST /experiments` | `CreateExpRequest` | `200 ConfirmQuoteResponse`; `201 CreateExpResponse` |
| `POST /experiments/cost-estimate` | `CostEstimateRequest` | `200 CostEstimateResponse` |
| `GET /experiments/{experiment_id}` | `None` | `200 ExpInfo` |
| `PATCH /experiments/{experiment_id}` | `ModifyExpRequest` | `200 ModifyExpResponse` |
| `GET /experiments/{experiment_id}/invoice` | `None` | `200 ExperimentInvoiceResponse` |
| `GET /experiments/{experiment_id}/quote` | `None` | `200 ExperimentQuoteResponse` |
| `POST /experiments/{experiment_id}/quote/confirm` | `ConfirmQuoteRequest` | `200 ConfirmQuoteResponse` |
| `GET /experiments/{experiment_id}/quote/pdf` | `None` | `200 PDF bytes` |
| `GET /experiments/{experiment_id}/results` | `None` | `200 Page<inline item>` |
| `GET /experiments/{experiment_id}/sequences` | `None` | `200 Page<inline item>` |
| `POST /experiments/{experiment_id}/submit` | `None` | `200 ExperimentConfirmationResponse` |
| `GET /experiments/{experiment_id}/updates` | `None` | `200 Page<inline item>` |
| `POST /feedback/submit` | `SubmitFeedbackRequest` | `201 SubmitFeedbackResponse` |
| `GET /info/health` | `None` | `200 HealthResponse` |
| `GET /info/health-db` | `None` | `200 HealthDbResponse` |
| `GET /invoices` | `None` | `200 Page<inline item>` |
| `GET /invoices/{invoice_id}` | `None` | `200 InvoiceDetailResponse` |
| `POST /invoices/{invoice_id}/pay` | `None` | `200 PayInvoiceResponse` |
| `GET /invoices/{invoice_id}/pdf` | `None` | `307 Redirect to PDF` |
| `GET /quotes` | `None` | `200 Page<inline item>` |
| `GET /quotes/{quote_id}` | `None` | `200 QuoteInfo` |
| `POST /quotes/{quote_id}/confirm` | `ConfirmQuoteRequest` | `200 ConfirmQuoteResponse` |
| `POST /quotes/{quote_id}/reject` | `RejectQuoteRequest` | `200 RejectQuoteResponse` |
| `GET /results` | `None` | `200 Page<inline item>` |
| `GET /results/{result_id}` | `None` | `200 ResultInfo` |
| `GET /sequences` | `None` | `200 Page<inline item>` |
| `POST /sequences` | `SequenceAddRequest` | `201 SequenceAddResponse` |
| `GET /sequences/{sequence_id}` | `None` | `200 SequenceInfo` |
| `GET /targets` | `None` | `200 Page<inline item>` |
| `GET /targets/request-custom` | `None` | `200 Page<inline item>` |
| `POST /targets/request-custom` | `CreateCustomTargetRequest` | `201 CreateCustomTargetResponse` |
| `GET /targets/request-custom/{request_id}` | `None` | `200 CustomTargetRequestInfo` |
| `GET /targets/{target_id}` | `None` | `200 TargetInfo` |
| `GET /tokens` | `None` | `200 Page<inline item>` |
| `POST /tokens/attenuate` | `AttenuateTokenRequest` | `201 AttenuateTokenResponse` |
| `POST /tokens/revoke` | `None` | `200 RevokeTokenResponse` |
| `GET /updates` | `None` | `200 Page<inline item>` |
| `GET /webhooks` | `None` | `200 OrgWebhook[]` |
| `POST /webhooks` | `CreateOrgWebhookRequest` | `201 OrgWebhook` |
| `DELETE /webhooks/{webhook_id}` | `None` | `204 No body` |
| `PATCH /webhooks/{webhook_id}` | `UpdateOrgWebhookRequest` | `200 OrgWebhook` |
| `GET /whoami` | `None` | `200 WhoAmIResponse` |

## Authentication and request scope

Send `Authorization: Bearer <token>` to resource endpoints and
`Content-Type: application/json` for JSON bodies. Obtain tokens through Foundry;
`GET /whoami` returns `organizations`, `permissions`, optional `user_id`,
`active_organization_id`, and `token_expires_at`. Each organization entry marks
whether it is active. Do not invent an `organization_id` create-body field from
the SDK's legacy optional argument: it is absent from current `CreateExpRequest`.
Use a token scoped to the intended organization and inspect `whoami`.

`GET /openapi.json` (schema discovery, not counted above) and the liveness probe
`GET /info/health` are public. The database probe reports 200 or 503; its
operation does not explicitly override the schema's global bearer security,
so do not rely on anonymous database-probe access.

## Pagination and query parameters

| GET endpoint | Query parameters |
|---|---|
| `/experiments` | `limit`, `offset`, `filter`, `search`, `sort` |
| `/experiments/{experiment_id}/results` | `limit`, `offset`, `filter`, `search`, `sort` |
| `/experiments/{experiment_id}/sequences` | `limit`, `offset`, `search`, `sort` |
| `/experiments/{experiment_id}/updates` | `limit`, `offset`, `filter`, `sort` |
| `/invoices` | `limit`, `offset`, `filter`, `sort` |
| `/quotes` | `limit`, `offset`, `filter`, `sort` |
| `/results` | `limit`, `offset`, `filter`, `search`, `sort` |
| `/sequences` | `limit`, `offset`, `search`, `sort`, `experiment_id` |
| `/targets` | `limit`, `offset`, `search`, `filter`, `sort`, `selfservice_only`, `show_conjugated`, `detailed` |
| `/targets/request-custom` | `limit`, `offset`, `filter`, `sort` |
| `/tokens` | `limit`, `offset` |
| `/updates` | `limit`, `offset`, `filter`, `sort` |

`limit` is 1–100 (default 50); `offset` starts at zero. Advance by the number of
returned items and stop at `total` or an empty page. `count` is the current page
size, not the total. Organization webhook listing is an array without pagination.
Search, filters, and sorting are not universal; only use listed parameters.

For filters use `filter=eq(status,draft)` or
`filter=and(gte(created_at,2026-01-01),eq(status,done))`. Canonical sort syntax is
`desc(created_at),asc(name)`; prefix and suffix forms also work. Targets support
filter/sort on `name`, `vendor_name`, `catalog_number`, and `purity` (e.g.
`gte(purity,90)`). The reviewed SDK `targets.list()` does not expose `filter`;
use REST for that parameter. Global updates are newest first; the experiment

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

