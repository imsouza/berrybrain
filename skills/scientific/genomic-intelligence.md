---
id: sci-genomic-intelligence
name: "Scientific: genomic-intelligence"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Predicts regulatory features, gene structure, and expression directly from DNA sequence using Genomic Intelligence's hosted transformer DNA language models — no local GPU or model weights. Six tasks over a REST API and a hosted MCP server (keyless public demo): promoter regions, "
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "genomic intelligence"
  - "genomic-intelligence"
keywords:
  - "genomic"
  - "intelligence"
  - "predicts"
  - "regulatory"
  - "features"
  - "gene"
  - "structure"
  - "expression"
---

# Genomic Intelligence — DNA Sequence Models

Genomic Intelligence (GI) serves transformer DNA language models over six
sequence-analysis tasks on managed GPUs. Give it a **gene symbol**, a **genomic
region**, or a **DNA/FASTA sequence**; it returns structured predictions —
promoter regions, splice sites, enhancer activity, chromatin state, expression
(log TPM), and de-novo gene annotation. Nothing runs locally: no model weights,
no GPU, no heavy Python stack. It is a thin client over a hosted, versioned
inference API.

**Official docs:** [docs.genomicintelligence.ai](https://docs.genomicintelligence.ai) ·
REST contract at [api.genomicintelligence.ai/v1/openapi.json](https://api.genomicintelligence.ai/v1/openapi.json) ·
hosted MCP server at `https://mcp.genomicintelligence.ai/mcp`

## When to use this skill

Use GI when the user has DNA and wants a model prediction:

- **Find promoters** in a genomic region (`promoter`)
- **Predict splice** donor/acceptor sites (`splice`)
- **Score enhancer activity** — developmental & housekeeping (`enhancer`)
- **Annotate chromatin state** across hundreds of tracks (`chromatin`)
- **Predict expression** as log(TPM+1) from a sequence + cell-type context (`expression`)
- **Annotate genes/transcripts** de novo, no reference needed (`annotation`)
- **Find the genes in a region and predict each one's expression** (composite)

Not for local alignment, variant calling, or file I/O — use a local tool
(BioPython, bcftools) for those. GI is for **model inference from sequence**.

> Research and development use. Not for clinical or diagnostic decisions.

## Two ways to call GI

### Hosted MCP server (keyless; preferred on MCP hosts)

GI hosts an MCP server at `https://mcp.genomicintelligence.ai/mcp` (Streamable
HTTP). When your agent host supports MCP, prefer it: it works **keyless** against
a rate- and concurrency-limited public demo tier, and an optional `gi_` bearer
key raises those limits. It exposes acquisition tools that return a **sequence handle**
(`sequence_ref`) and `predict_*` tools that take that handle, so large sequences
stay out of the context. See [MCP workflow](#mcp-workflow-handle-based) below and
`references/mcp.md`.

### REST API (universal)

Plain HTTP with `requests` against `https://api.genomicintelligence.ai/v1`. The
REST path **requires** a `GI_API_KEY` (a `gi_` bearer). Use it on any host, in
scripts, or when you need the raw envelope. See [Core REST workflow](#core-rest-workflow).

## Access and authentication

1. The **hosted MCP demo is keyless** — try it with nothing set.
2. REST prediction and job operations need a key, sent as `Authorization: Bearer <key>`.
   Public `GET /v1/tasks/{task}/models` discovery needs no key and is rate-limited
   by source IP; inspect model windows and bounds before requesting access.
   See the [current authentication contract](https://docs.genomicintelligence.ai/).
   Request a prediction key at [contact@genomicintelligence.ai](mailto:contact@genomicintelligence.ai).
3. **Never hardcode the key.** Read it from the `GI_API_KEY` environment variable
   (or a `.env` via `python-dotenv`). Never commit keys.

```bash
export GI_API_KEY="gi_yourkeyhere"     # optional for MCP; required for REST
export GI_BASE_URL="https://api.genomicintelligence.ai"   # override for staging
```

Keys are scoped to a partner tier with concurrency and per-minute caps. A `429`
means you hit a cap — back off and retry, or ask GI to raise your tier.

## The six tasks

Each task is **its own published operation** with its own request schema, its own
minimum length, and its own closed `options` object — `POST
/v1/tasks/promoter/predict`, `/v1/tasks/splice/predict`,
`/v1/tasks/enhancer/predict`, `/v1/tasks/chromatin/predict`,
`/v1/tasks/annotation/predict`, `/v1/tasks/expression/predict`. Each path is a
literal string, so nothing needs to be constructed, and there is no shared
`PredictRequest` schema. Body is `{sequence, sequence_name?, model?,
options?}`, returning a `{data, meta}` envelope. What differs per task:

| Task | Recommended mode | Accepted length | `context_window_bp` | Notes |
|---|---|---|---|---|
| `promoter` | sync | 300–500,000 bp | 2,000 bp | sliding-window promoter regions |
| `splice` | sync | 100–500,000 bp | 15,000 bp | donor/acceptor sites (long-context BigBird); strand-specific — feed transcript orientation |
| `enhancer` | sync | 50–500,000 bp | 249 bp | dev + housekeeping scores (DeepSTARR, *Drosophila*) |
| `chromatin` | sync | 200–500,000 bp | 1,000 bp | hundreds of tracks (DeepSEA) |
| `expression` | sync | **9,198–500,000 bp** | n/a (`trained_window_bp` 9,198) | log(TPM+1); needs `tss_index` unless exactly 9,198 bp, plus a cell-type `description` |
| `annotation` | async | 1,000–500,000 bp | n/a | de-novo transcripts; submit + poll; sync JSON above 200,000 bp is `413 sync_too_large` |

`Recommended mode` is guidance, not a constraint — every task accepts both. Omit `Prefer` for a synchronous `200`; send `Prefer: respond-async` for a `202` plus `GET /v1/tasks/jobs/{job_id}`. The one enforced limit is per operation: where `/v1/openapi.json` publishes `x-sync-limit-bp` on a `POST`, a synchronous JSON request above that length is `413 sync_too_large` — 200,000 bp on `annotation` and 50,000 bp on the composite workflow in contract revision 16. Read the field rather than memorising the numbers. Annotation BED/GFF3 stays synchronous at any admitted length and can time out; the other five predict tasks have no hard sync cap.

**The minimum is admission control, not regime.** A request above the floor but
shorter than the selected model's `bio_spec.context_window_bp` is *accepted and
scored* — against a window padded out to the context window. Enhancer is the
sharp case: the floor is 50 bp but the context window is 249 bp, so 50–248 bp is
scored mostly on padding. Compare your length against
`context_window_bp` from `GET /v1/tasks/{task}/models` to know whether the model
saw real sequence. Longer-than-context input is fine — the scanner steps a
prediction window at a time and pads only the final partial window.

Under the floor and over the 500,000 bp cap are **both `422 validation_failed`**
at `loc ["body","sequence"]`; over-length is *not* a `413`. All lengths are
measured after whitespace is stripped, so a line-wrapped FASTA body can be pasted
verbatim (a `>` header line still fails the alphabet check).

`options` is typed and **closed** (`additionalProperties: false`) per task — an
unknown key is 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

