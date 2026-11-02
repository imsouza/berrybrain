---
id: sciref-benchling-integration-api-endpoints
name: "Scientific Ref: Benchling REST API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (benchling-integration): Benchling REST API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "benchling integration api endpoints"
  - "benchling rest api reference"
keywords:
  - "benchling"
  - "integration"
  - "api"
  - "endpoints"
  - "specialized"
  - "scientific"
  - "reference"
---

# Benchling REST API Reference

Reviewed 2026-09-30 against the [official reference](https://benchling.com/api/reference),
platform guides, and generated **benchling-api-client 2.0.434**, resolved alongside SDK **1.25.0**.
The public reference is a JavaScript application; the published Python client supplied
the endpoint/parameter/model definitions for this audit. Check your tenant's interactive
reference before executing writes, especially on a validated/restricted release.
No authenticated endpoint calls were made. Payloads below are illustrative.

## Version and authentication

This reference covers `https://{tenant}.benchling.com/api/v2`. V3 also exists;
consult its [availability/stability guide](https://docs.benchling.com/docs/v3-api-overview)
and tenant documentation rather than replacing `/v2` with `/v3` in these paths.

Use HTTPS and either Basic auth (API key as username, empty password) or OAuth Bearer
auth. JSON writes use `Content-Type: application/json`. Token exchanges are form encoded
at `/oauth/token`; the SDK's legacy `/api/v2/token` path still works. See
[authentication](authentication.md) for identity, expiry, and token acquisition.

## Responses, pagination, and filters

Single-resource endpoints generally return a resource object; `GET /entries/{id}` is an
exception with an `entry` wrapper. Creation usually returns HTTP 201 and the created
resource. List responses use a **resource-specific collection key**, never a universal `results` key:

```json
{
  "dnaSequences": [{"id": "seq_example", "name": "Construct 001", "bases": "ATCG"}],
  "nextToken": "opaque-token"
}
```

Most paginated lists accept `pageSize` (default 50, maximum 100) and `nextToken`. Preserve
filters when requesting the next page; stop on an empty token. Some lists differ:
`GET /registries` returns `registries` without the standard pagination arguments.
`GET /events` has additional polling semantics described below.

Filters are endpoint-specific. On DNA sequences, `name` matches the full name;
`nameIncludes` supports substring search. `modifiedAt` and `createdAt` are string filters;
consult the tenant reference for their comparison syntax rather than assuming every
timestamp filter is inclusive. Use `archiveReason` for archival filtering according to
the endpoint definition; `archived=false` is not a supported replacement.

### Collection and resource routes

All paths in this table are relative to `/api/v2`. A `GET` collection returns the named
collection; `POST` creates one resource with the type's create model. A resource `GET`
returns one object (with the entry wrapper noted above) and `PATCH` applies its update model.

| Collection | Collection methods | Collection key | Resource path and methods |
|---|---|---|---|
| `/dna-sequences` | GET, POST | `dnaSequences` | `/dna-sequences/{dnaSequenceId}` GET, PATCH |
| `/rna-sequences` | GET, POST | `rnaSequences` | `/rna-sequences/{rnaSequenceId}` GET, PATCH |
| `/aa-sequences` | GET, POST | `aaSequences` | `/aa-sequences/{aaSequenceId}` GET, PATCH |
| `/custom-entities` | GET, POST | `customEntities` | `/custom-entities/{customEntityId}` GET, PATCH |
| `/mixtures` | GET, POST | `mixtures` | `/mixtures/{mixtureId}` GET, PATCH |
| `/containers` | GET, POST | `containers` | `/containers/{containerId}` GET, PATCH |
| `/boxes` | GET, POST | `boxes` | `/boxes/{boxId}` GET, PATCH |
| `/locations` | GET, POST | `locations` | `/locations/{locationId}` GET, PATCH |
| `/plates` | GET, POST | `plates` | `/plates/{plateId}` GET, PATCH |
| `/entries` | GET, POST | `entries` | `/entries/{entryId}` GET, PATCH |
| `/workflow-tasks` | GET, POST | `workflowTasks` | `/workflow-tasks/{workflowTaskId}` GET, PATCH |
| `/folders` | GET, POST | `folders` | `/folders/{folderId}` GET |
| `/projects` | GET | `projects` | `/projects/{projectId}` GET |
| `/users` | GET | `users` | `/users/{userId}` GET |
| `/teams` | GET | `teams` | `/teams/{teamId}` GET |
| `/registries` | GET | `registries` | `/registries/{registryId}` GET |

This is a task-oriented subset, not a claim that these are each service's only methods.
There is no documented `/users/me` endpoint; test auth against an accessible resource.

### Schema routes

Use `GET` on each collection or append `/{schemaId}` for one schema:

| Collection | Collection key |
|---|---|
| `/entity-schemas` | `entitySchemas` |
| `/entry-schemas` | `entrySchemas` |
| `/container-schemas` | `containerSchemas` |
| `/box-schemas` | `boxSchemas` |
| `/location-schemas` | `locationSchemas` |
| `/plate-schemas` | `plateSchemas` |
| `/workflow-task-schemas` | `workflowTaskSchemas` |

There is no generic stable-v2 `/schemas?entityType=...` route. The SDK exposes these as
`benchling.schemas.list_entity_schemas()`, `get_entity_schema_by_id(id)`, and analogous
resource-specific methods. Schema definitions determine field names, value types,
required values, units, and valid workflow statuses.

## Entity create/update/archive

A registered DNA sequence create body for `POST /dna-sequences`:

```json
{
  "name": "Construct 001",
  "bases": "ATCGATCG",
  "isCircular": true,
  "folderId": "lib_example",
  "schemaId": "ts_example",
  "registryId": "src_example",
  "namingStrategy": "NEW_IDS",
  "fields": {"gene_name": {"value": "GFP"}}
}
```

Omit registration arguments to create an unregistered entity. To assign a human registry
identifier explicitly, supply `entityRegistryId` **instead of** `namingStrategy`, together
with `registryId`. These are different concepts, not interchangeable IDs.

`POST /rna-sequences` uses `bases` (RNA alphabet) and `isCircular`.
`POST /aa-sequences` uses `aminoAcids`. `POST /custom-entities` uses `name`, `schemaId`,
`folderId`, and applicable fields. Do not coerce numeric fields to strings globally.
A partial update uses the same field-value envelope, for example:

```json
{"fields": {"passage_number": {"value": 16}}}
```

Sequence filters include `folderId`, `schemaId`, `name`, `nameIncludes`, `modifiedAt`,
`createdAt`, `registryId`, and `archiveReason`; `schemaId` is an optional custom-entity
filter rather than a requirement to list all accessible entities.

Archival endpoints are `POST /dna-sequences:archive`, `/rna-sequences:archive`,
`/aa-sequences:archive`, `/custom-entities:archive`, and `/mixtures:archive`.
Use the appropriate array key (`dnaSequenceIds`, `rnaSequenceIds`, `aaSequenceIds`,
`customEntityIds`, or `mixtureIds`) and an allowed reason:

```json
{"dnaSequenceIds": ["seq_example"], "reason": "Ret

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

