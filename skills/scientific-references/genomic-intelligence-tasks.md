---
id: sciref-genomic-intelligence-tasks
name: "Scientific Ref: Tasks Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (genomic-intelligence): Tasks Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "genomic intelligence tasks"
  - "tasks reference"
keywords:
  - "genomic"
  - "intelligence"
  - "tasks"
  - "specialized"
  - "scientific"
  - "reference"
---

# Tasks Reference

Six DNA-sequence tasks, each its own published REST operation —
`POST /v1/tasks/promoter/predict`, `/v1/tasks/splice/predict`,
`/v1/tasks/enhancer/predict`, `/v1/tasks/chromatin/predict`,
`/v1/tasks/annotation/predict`, `/v1/tasks/expression/predict` — with body
`{sequence, sequence_name?, model?, options?}`, returning a `{data, meta}`
envelope. Each path is a literal string, and each carries its own request schema,
its own `minLength`, and its own closed `options` object; there is no shared
`PredictRequest`. On MCP, use `predict_<task>(sequence_ref=...)`, except annotation is
`find_genes(sequence_ref=...)`.

**Omit `model` to get the task's default** — the API resolves it server-side
(`model` is optional: *"If omitted, the task's default model is used."*). Default
model **IDs are deliberately not listed here**: defaults change and old IDs are
retired, so a hardcoded ID is a future hard failure. Discover them at call time
with `GET /v1/tasks/{task}/models` (REST) or `list_models(task)` (MCP), and
**never invent one**.

Source of truth for bounds: the live OpenAPI at
<https://api.genomicintelligence.ai/v1/openapi.json>.

| Task | Recommended mode | Accepted length | `context_window_bp` | Default architecture |
|---|---|---|---|---|
| promoter | sync | 300–500,000 bp | 2,000 bp | sliding-window; human/mammalian |
| splice | sync | 100–500,000 bp | 15,000 bp | BigBird (long-context) |
| enhancer | sync | 50–500,000 bp | 249 bp | DeepSTARR — ***Drosophila*** |
| chromatin | sync | 200–500,000 bp | 1,000 bp | DeepSEA — hundreds of tracks |
| expression | sync | **9,198–500,000 bp** (scores one 9,198 bp window) | n/a (`trained_window_bp` 9,198) | log(TPM+1) |
| annotation | async | 1,000–500,000 bp | n/a | de-novo transcripts; sync JSON above 200,000 bp (`x-sync-limit-bp`) is `413 sync_too_large` |

`Recommended mode` is guidance, not a constraint — every task accepts both. Omit `Prefer` for a synchronous `200`; send `Prefer: respond-async` for a `202` plus `GET /v1/tasks/jobs/{job_id}`. The one enforced limit is per operation: where `/v1/openapi.json` publishes `x-sync-limit-bp` on a `POST`, a synchronous JSON request above that length is `413 sync_too_large` — 200,000 bp on `annotation` and 50,000 bp on the composite workflow in contract revision 16. Read the field rather than memorising the numbers. Annotation BED/GFF3 remains synchronous above its JSON cap and can time out; the other five predict tasks have no hard sync cap.

The minimum is published as `minLength` on each task's request schema and enforced
before any model loads. There are **no per-model floors**: a task's floor is the
strictest its models need, and every model stays listed and loadable.

**Floor ≠ regime.** A request above the floor but shorter than the selected
model's `bio_spec.context_window_bp` is accepted and scored — against a window
padded out to the context window. Enhancer is the sharp case: the floor is 50 bp
while the context window is 249 bp, so 50–248 bp is scored mostly on padding.
Compare your length against `context_window_bp` to know whether the model saw
real sequence.
Longer-than-context input is fine — the scanner steps a prediction window at a
time and pads only the final partial window.

Under the floor and over the cap are both `422 validation_failed` at
`loc ["body","sequence"]`; over-length is **not** a `413`. All lengths are
measured after whitespace is stripped.

`options` is typed and closed (`additionalProperties: false`) per task — an
unknown key is a hard `422` (`type: "extra_forbidden"`), never ignored:

| Task | `options` keys |
|---|---|
| promoter | `threshold` (0–1, default 0.5) |
| splice | `threshold` (0–1, default 0.5), `site_types` (subset of `["donor","acceptor"]`, default both) |
| enhancer | *(none)* |
| chromatin | `threshold` (0–1, default 0.5) |
| annotation | `batch_size` (1–128, default 8), `shift_coordinates`, `reverse_complement` (default true) |
| expression | `description` — **required**, and the only key |
| composite | `description`, `annotation_model`, `expression_model`, `batch_size`, `shift_coordinates` |

Per-task output `format` values (an unsupported one is `415 unsupported_format`,
never a silent fallback to JSON; text formats are synchronous-only): promoter
`json|bed|bedgraph`, splice `json|bed|gff3`, enhancer `json|bedgraph`, chromatin
`json|bed`, annotation `json|bed|gff3`, expression JSON only.

## Reading outputs

Narrow on `data.task`. The six tasks declare `data.model`, `data.input`, and
`data.summary`; **summary keys are deliberately outside the stable contract**.
Nested region/window/site records are open objects, so inspect actual records
instead of assuming every record has `name` or `strand`. Preserve input
coordinates and orientation separately. Stable counts live in
`meta.task_specific_counts`, not summary aliases:

| Task | Declared data fields | Declared counts |
|---|---|---|
| promoter | `regions`, `window_details` | `windows_processed`, `regions_found` |
| splice | `sites`, `tracks`, `window_details` | `windows_processed`, `sites_found` |
| enhancer | `windows`, `tracks` | `windows_processed` |
| chromatin | `windows`, `tracks` | `windows_processed`, `total_annotations` |
| annotation | `transcripts` | `transcripts_found` |
| expression | `prediction` | `tss_index`, `scored_window` (schema permits null; check before use) |

## promoter

Sliding-window classification, with promoter regions and individual window scores.
Current public discovery includes human, Drosophila, yeast, and Arabidopsis
models. Check the chosen model's organism and window; the default is human.
A predicted region is a model output, not experimentally established promoter
activity or a transcription start site annotation.

## splice

The default BigBird model is strand-specific. Submit transcript orientation;
reverse-complement a minus-strand locus before scoring. The official contract
warns that wrong-strand input still yields plausible, high-scoring sites.
Neither confidence, count, nor the presence of GT/AG motifs validates orientation.
There is no promised strand field on a site; track orientation caller-side.

`start`/`end` bound a scored BPE **token span**, typically 4–8 bases, with
`token_index` identifying the token. They do not identify a base-resolution
junction. GFF3 exports retain this span semantics. Do not report an invented
single-base donor/acceptor coordinate or treat overlap with a reference junction
as exact localization.



*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

