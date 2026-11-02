---
id: sciref-tamarind-api-reference
name: "Scientific Ref: Tamarind Bio REST API reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (tamarind): Tamarind Bio REST API reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "tamarind api reference"
  - "tamarind bio rest api reference"
keywords:
  - "tamarind"
  - "api"
  - "reference"
  - "specialized"
  - "scientific"
  - "rest"
---

# Tamarind Bio REST API reference

Reviewed 2026-09-30 against the [current OpenAPI](https://app.tamarind.bio/api/openapi.json),
[REST guide](https://app.tamarind.bio/llms-full.txt), and
[public catalog](https://app.tamarind.bio/tools.json). These are documentation
checks, not authenticated endpoint tests.

All paths below are relative to `https://app.tamarind.bio/api`, or the user's
organization deployment's `/api` base. Requests use `x-api-key` except public
catalog discovery. Do not send the key when downloading a signed storage URL.

## Endpoint map

| Method | Path | Request and response |
|---|---|---|
| GET | `/tools-catalog` | Public catalog; also at host-level `/tools.json`. Optional `type`/`tag` filters; `tools` contains public types and conditional required settings. |
| GET | `/tools` | Account-scoped array with `name`, descriptions, trimmed `settings`, and optional output metadata. `custom=true` selects legacy custom tools only. |
| GET | `/tools/{name}/schema` | JSON Schema for the settings object. Optional `version` pins a custom build. 404 covers missing, inaccessible, and mid-deploy tools. |
| POST | `/validate-job` | `type`, object/array `settings`; optional `jobName` (single), `jobNames` (array), `version`. HTTP 200 contains a `valid` verdict. |
| POST | `/submit-job` | `jobName`, `type`, object `settings`; optional `version`, `projectTag`. 200 is a **plain-text** confirmation. |
| POST | `/submit-batch` | `batchName`, `type`, array `settings`; optional parallel `jobNames`, `version`, `projectTag`. 200 schema has `batchName`, `jobs`, `totalJobs`. |
| GET | `/jobs` | Exact lookup or cursor-paginated listing; shapes below. |
| POST | `/jobs/search` | `jobNames` (up to 1,000), optional `organization`, `includeSubjobs`, `jobEmail`. Returns `jobs`, `notFound`, `statuses`. |
| POST | `/result` | `jobName`; optional `fileName`, `pdbsOnly`, `jobEmail`, `noAsync`. 200 JSON string URL or 202 preparing object. |
| POST | `/stop-job` | `jobName`; stops queued/running work, including stoppable batch children. Returns `message`, `stoppedCount`. |
| DELETE | `/delete-job` | `jobName`; soft-deletes the job/batch children from listings. Result files remain. Unknown name: 400. |
| PUT | `/upload/{filename}` | Binary body; optional `folder`. This route redirects to the upload service; follow redirects. |
| GET | `/files` | Optional `folder`, `includeFolders=true`; complete array of name strings for that folder, no pagination. |
| DELETE | `/delete-file` | Query `filePath` **or** `folder`. A folder request removes its files. |
| GET | `/usage-statistics` | `statistic=hours\|weighted_hours\|jobs`, `scope=user\|organization`; details below. |
| POST | `/submit-pipeline` | Legacy inline execution: `jobName`, `stages`, conditional `initialInputs`, optional `projectTag`. |
| POST | `/run-pipeline` | Legacy saved execution: `jobName`, `pipelineName`, nonempty `initialInputs` array, optional `version`. |

## Discovery and validation

`/tools` is an array, not `{"tools": [...]}`. Each trimmed parameter has `name`
and `required`; optional metadata includes `type`, `description`, `default`,
`options`, `extension`, and `list`. Filter built-ins client-side; arbitrary search
query parameters are not documented. `/tools?custom=true` does not discover
current custom deployments: use the deployed name and `/tools/{name}/schema`.

The latter is a **JSON Schema document**, not the trimmed parameter array and not
an MCP `parameters` envelope. Domain strings may carry `x-tamarind-type`. Numeric
strings and sequence normalization are not fully checked by JSON Schema bounds;
use `/validate-job` for domain validation and file existence. Keep `version`
consistent across schema, validate, and submit for a pinned custom build.

For valid credentials, `/validate-job` returns 200 whether valid or invalid:

- Single success: `{"valid": true, "normalized": {...}}`. Current `normalized`
  contains cleaned settings and defaults intended for submission. Inspect these
  defaults for model/sample-count changes, then submit that settings object.
- Single failure: `valid: false`, `error`, possibly `missing_fields` and `code`.
  `missing_fields` may be empty despite failure. Do not interpret quota/policy
  codes as sequence-format errors.
- `job_name` reflects name normalization when `jobName` was supplied;
  `job_name_changed` indicates a change. Persist this stored name.
- The guide additionally documents `unrecognized_settings`: correct every typo,
  even if `valid` is true. Unknown settings sent directly to submit are carried
  through and may silently leave the intended optional field at its default.
- For array input, inspect **presence of `results`**, not just `valid`.
  `results` holds one verdict per row, with its `index`, and top-level `valid`
  aggregates all rows. If `results` is absent, the whole request was rejected and
  top-level `error` explains why. Array validation supports at most 1,000 rows
  per call and approximately 4.5 MB; large normalized responses can also require
  smaller chunks. Validate all rows, not a representative sample.

Field validation does not reserve compute or re-check every organization policy,
queue constraint, or custom-tool deployment state. A valid verdict can still be
rejected at submission. Do not manually add internal routing settings.

## Names, projects, and batches

Names are sanitized: whitespace becomes `_` and characters outside
`[A-Za-z0-9_.-]` are removed. Send an already-clean, nonempty name of at most 200
characters so exact job lookup works; this is a compatibility limit, not a
100-character submit validator. Parse the actual name from the successful
`<stored-name> submitted to queue.` response. On a lost response, check that
persisted clean name before retrying.

`projectTag` accepts an organization project ID or name. It is normally optional
but required under an organization's project policy. A refusal may include
`availableProjects`; absence does not establish that no projects exist.

Batch `settings` must be a nonempty array. If `jobNames` is supplied it must have
the same length, with no duplicates or child name equal to the parent. Stored
child names may be prefixed/rewritten; enumerate `/jobs?batch=...` rather than
assuming names. The batch cap is **30,000 jobs after design fan-out**, plus a
separate approximately **4.5 MB** request cap. The older `{tool, jobs:[...]}`
alternative is not the current documented contract. Do not rely on undocumented
`w

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

