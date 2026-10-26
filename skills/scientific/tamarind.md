---
id: sci-tamarind
name: "Scientific: tamarind"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Provides access to a collection of open-source molecular design and structural biology tools on the Tamarind Bio platform, via its REST API or MCP server — no local GPUs required. Tamarind bundles popular open-source models for structure prediction (AlphaFold, Boltz, Chai, ESMFol"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "tamarind"
keywords:
  - "tamarind"
  - "provides"
  - "access"
  - "collection"
  - "open"
  - "source"
  - "molecular"
---

# Tamarind Bio

Tamarind runs molecular-design and structural-biology tools on managed compute:
structure prediction, protein and antibody design, docking, binding-affinity
prediction, MSA generation, and molecular dynamics. Use it when the user requests
Tamarind, its REST API/MCP server, or cloud execution of these scientific tools.
For local sequence processing or molecular descriptors, use a local library.

## Sources and review scope

The REST contracts and public catalog were reviewed on **2026-09-30**. Examples are
illustrative until validated against the user's account; this review did not run
authenticated jobs or establish scientific accuracy for any model.

- [API index](https://app.tamarind.bio/llms.txt) and
  [complete guide](https://app.tamarind.bio/llms-full.txt).
- [Current OpenAPI](https://app.tamarind.bio/api/openapi.json) includes discovery,
  validation, jobs, files, and newer pipeline/custom-tool surfaces.
  [openapi.yaml](https://app.tamarind.bio/openapi.yaml) is also available. Check that
  needed paths exist: the merged spec can return HTTP 200 with only its classic
  surface when the backend spec cannot be fetched.
- [Public catalog](https://app.tamarind.bio/tools.json) needs no key; query `?type=`
  or `?tag=`. It documents public tools and conditional required settings, not
  every optional parameter or account entitlement.
- [Product documentation index](https://docs.tamarind.bio/llms.txt) links to
  Markdown pages, including the [MCP guide](https://docs.tamarind.bio/tamarind/mcp-server.md).

Fetch the account's current schemas before composing a run. Where the prose guide
and OpenAPI differ, prefer the operation/schema for field shapes, and record any
unresolved difference rather than guessing.

## Access

1. Use the user's Tamarind deployment. The shared base is
   `https://app.tamarind.bio/api`; a dedicated organization deployment has its own
   host and account data. Every relative REST path below is under `/api`.
2. Obtain a key from the deployment's API settings and read it from
   `TAMARIND_API_KEY`; send it as `x-api-key`. Keep keys out of files and logs.
3. Check the account's current allowance and compute budget before scaling up.
   Free usage is a monthly allowance, not an unconditional promise of ten jobs
   forever; billing and entitlements can change.

```bash
# Public discovery requires no credential.
curl --fail-with-body 'https://app.tamarind.bio/tools.json?type=alphafold'
# Account-scoped discovery:
curl --fail-with-body 'https://app.tamarind.bio/api/tools' \
  -H "x-api-key: $TAMARIND_API_KEY"
```

For REST examples install `requests` in the execution environment. The official
CLI distribution is **`tamarind-cli`**, and its Custom Tools Python client imports
as `from tamarind import Tamarind`; the unrelated package named `tamarind` is not
this client. See the [SDK reference](https://app.tamarind.bio/api-docs/custom-tools-sdk-reference).
Core job recipes below use HTTP directly.

## Workflow

1. **Discover.** Read `GET /tools` and match the user's scientific task to the tool
   description. Built-ins return an array; `?custom=true` lists legacy custom
   tools only. Current custom deployments can be missing from this list: use the
   known deployed name and its schema before concluding that it is unavailable.
2. **Read the schema.** `GET /tools/{name}/schema` returns a JSON Schema for the
   `settings` object. `GET /tools` also supplies a trimmed `settings` parameter
   list. Check task-dependent fields, file extensions, list values, and defaults.
3. **Validate.** Send `POST /validate-job` with `type`, `settings`, and optional
   `jobName`. Check HTTP status first, then JSON `valid`. On success, inspect and
   use `normalized` as the settings to submit. Address `unrecognized_settings`
   if returned, even alongside `valid: true`: an optional-field typo can otherwise
   silently leave the default in effect. Validation checks fields, not all submit
   policies, queue limits, or deployment readiness.
4. **Submit once.** `POST /submit-job` takes `jobName`, `type`, `settings`, optional
   `version` for a custom-tool build, and optional/organization-required
   `projectTag`. Persist the submitted name and settings. A successful response
   is plain text, not a JSON receipt. Use the returned stored name.
5. **Poll.** `GET /jobs?jobName=...` returns a row directly. Single-job terminal
   states are `Complete`, `Stopped`, and `Failed`; handle legacy `Deleted` or an
   exact-lookup error without looping indefinitely. Poll batch parents using
   `batchStatus`, and poll newer pipelines on their own run endpoint.
6. **Download and inspect.** `POST /result` returns a JSON string URL on **200**,
   or **202** with `status: "preparing"`. Retry result retrieval after 202, without
   resubmitting compute. GET the signed URL without the Tamarind API-key header.
   Download the archive only for successful runs; request `fileName: "output.log"`
   for stopped/failed jobs. Verify the scientific outputs after downloading.

[Workflow recipes](references/workflows.md) implement validation, stored names,
bounded polling, 202 handling, batch validation, and pagination. They are locally
smoke-tested with simulated responses; authenticated execution remains untested.

## Picking tools and interpreting results

Select by inputs, intended output, and modeling assumptions, then confirm the
candidate in the live catalog. These are anchors, not a guaranteed catalog:

| Task | Candidates and decisions |
|---|---|
| Protein/complex structure | `alphafold` for AF2 monomers/multimers; `boltz`, `chai`, or `protenix` for cofolding including ligands/nucleic acids; `esmfold` for fast single-sequence protein folding. Check `esmfold2` separately: its current catalog includes protein, DNA, RNA, and ligand complexes. |
| Binder/motif design | `bindcraft`, `boltzgen`, `rfdiffusion`; choose by target type, scaffold constraints, and required structure inputs. |
| Inverse folding | `proteinmpnn`/`ligandmpnn` consume structures and design sequences. Re-fold designs and compare to the intended backbone/interface. |
| Small-molecule docking | `autodock-vina` for a fixed receptor and search box; `diffdock` for diffusion docking; `boltz`/`chai` for cofolding. Choose the modeling approach for the task, not to avoid supplying a required input. |
| Antibody/developability/MSA/MD | Filter descriptions and schemas for the specific task; availability and inputs differ by tool. |

Confidence s

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

