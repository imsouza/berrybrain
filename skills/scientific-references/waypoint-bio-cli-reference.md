---
id: sciref-waypoint-bio-cli-reference
name: "Scientific Ref: `waypoint` CLI reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (waypoint-bio): `waypoint` CLI reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "waypoint bio cli reference"
  - "`waypoint` cli reference"
keywords:
  - "waypoint"
  - "bio"
  - "cli"
  - "reference"
  - "specialized"
  - "scientific"
---

# `waypoint` CLI reference

Reviewed 2026-10-01 against `waypoint-bio` 1.0.2 (PyPI wheel) and GitHub main
1.0.4 (`f45eee6d07a480bfc90f84ab8082bbc969dec15d`). Flags below are shared;
export/logging differences and known failures are recorded in `upstream-review.md`.
Hub-backed training examples are illustrative, without authenticated scientific execution.

```
waypoint {pretrain,benchmark,finetune,embed,prepare-dataset} ...
```

Config paths are resolved first against the working directory, then against the bundled
`waypoint_bio/configs/` tree inside the installed wheel. So `--config configs/benchmark.yaml`
works from anywhere without cloning the repo. The same fallback applies to the bundled example
data (`examples/abundance_matrix.tsv`, `examples/finetune_classification.parquet`, …).

---

## `waypoint prepare-dataset`

Converts a sample × taxa abundance matrix into waypoint format.

| Flag | Default | Notes |
| --- | --- | --- |
| `--input` | *required* | `.csv` / `.tsv` abundance matrix. |
| `--output` | *required* | `.parquet` recommended; `.csv` supported. |
| `--orientation` | `auto` | `auto`, `samples_as_rows`, `taxa_as_rows`. |
| `--taxonomy_format` | `full` | `full` for lineage strings; a rank name (`genus`, `species`, …) to prefix bare names. |
| `--no_normalize` | off | Skip row-normalisation to relative abundances. |
| `--keep_zeros` | off | Keep zero-abundance entries in each sample's lists. |
| `--metadata` | none | CSV/TSV/parquet of per-sample metadata, indexed by sample ID, merged in as extra columns. |

`auto` treats the file as taxa-as-rows when the first column header is `taxonomy`, `lineage`,
`taxon`, `otu`, or `#otu id` (case-insensitive); otherwise samples-as-rows with the first column
as the sample ID.

`--taxonomy_format genus` prefixes bare column names with `g__`. It disables higher-rank fallback,
because a bare name carries no lineage to fall back to — prefer real lineage strings.

---

## `waypoint embed`

One fixed-size vector per sample from a pretrained checkpoint. No fine-tuning, no labels needed.

| Flag | Default | Notes |
| --- | --- | --- |
| `--model` | `outpost-bio/Waypoint-6m` | Hub id or local checkpoint directory. |
| `--data` | *required* | Waypoint-format `.parquet` / `.csv` / `.tsv`. |
| `--output` | *required* | `.parquet`, or `.csv` if the path ends in `.csv`. |
| `--pooling` | `last_token` | `last_token`, `mean`, `first_token`, `cls_token`. |
| `--batch_size` | `32` | |
| `--max_length` | `512` | Keeps at most max_length - 2 ordered entries; no guarantee discarded taxa are uninformative. |
| `--device` | auto | `cuda`, `mps`, or `cpu`; auto-detects in that order. |

Output columns are `dim_0 … dim_{H-1}`, indexed by sample ID. Hidden size `H` is 256 (6m),
512 (45m), 768 (170m).

**Behaviour worth knowing:** tokens that map to `<unk>` are *dropped* before ordering, not encoded.
A row with no in-vocabulary taxa still produces an output row, but its sequence is `[BOS][EOS]` and
the embedding is meaningless. Run `scripts/vocab_coverage.py` first.

Ordering: by descending abundance z-score when `token_std_means.parquet` is present (it ships with
every published checkpoint and with `waypoint pretrain` output), otherwise by descending raw
relative abundance.

---

## `waypoint finetune`

Fine-tunes a checkpoint on your own labelled waypoint-format data.

| Flag | Default | Notes |
| --- | --- | --- |
| `--model` | *required* | Hub id or local checkpoint. |
| `--data` | *required* | Waypoint-format file containing `--target`. |
| `--output_dir` | *required* | |
| `--task_type` | *required* | `classification` or `regression`. |
| `--target` | *required* | Target column name. |
| `--covariate_column` | none | Categorical column, one-hot encoded and concatenated to the pooled embedding before the head. |
| `--config` | task default | Flat YAML; defaults to the bundled classification/regression config. |

### Fine-tuning config keys

```yaml
split_column: null        # column holding train/validation/test; null = random split
val_fraction: 0.1
test_fraction: 0.1

max_length: 512           # 2 <= max_length <= checkpoint n_positions
pooling_strategy: last_token
filter_unk_taxa: true     # drop out-of-vocabulary taxa rather than feed <unk>

seed: 42
learning_rate: 0.00003
num_epochs: 1             # raise this; early stopping is what should terminate training
batch_size: 64
warmup_steps: 1000        # lower to ~50 for small datasets
weight_decay: 0.001
eval_strategy: steps
eval_steps: 400
logging_steps: 5
patience: 5               # eval steps without improvement before early stopping
save_total_limit: 1

use_lora: false
lora_r: 8
lora_alpha: 16            # convention: 2 * r
lora_dropout: 0.05
lora_target_modules: [c_attn, c_proj]   # GPT-2 fused QKV and output projection
lora_bias: none
lora_fan_in_fan_out: true               # required for GPT-2 Conv1D layouts
```

The shipped configs use `num_epochs: 1`, whereas the paper describes up to 300 fine-tuning
epochs with early stopping. The default CLI config does not reproduce that training budget.
On small datasets, choose enough epochs and a suitable evaluation interval for validation
and early stopping to occur. Likewise `eval_steps: 400` may never fire; lower it so early stopping
and best-checkpoint selection can actually work.

GitHub 1.0.4 merges LoRA adapters before export. PyPI 1.0.2 saves an adapter-only model when
`use_lora: true`; plain `AutoModel.from_pretrained` cannot load that export. Keep LoRA disabled
for the released-package workflow, or explicitly load/merge via PEFT with the original base model.
Both versions also require a tokenizer that actually implements vocabulary serialization.

The fine-tuning config `seed` affects initial RNG setup and random splits, but its value is
not passed to `TrainingArguments` either. Explicitly wire trainer seeds for controlled repeats.

### Outputs

These describe successful exports; see the tokenizer/LoRA limitations above.

| Path | Contents |
| --- | --- |
| `best_model/` | Fine-tuned base transformer in standard HF format, plus tokenizer and `token_std_means.parquet`. |
| `best_model/finetuned_model_state.pt` | Full torch state dict: transformer + head + covariate embedding. |
| `validation_metrics.json`, `test_metrics.json` | Per-split scores, benchmark-equivalent. |
| `training_log.csv`, `training_log.html` | GitHub 1.0.4 only, when log rows exist; HTML uses Plotly from a CDN. |
| `validation_predictions.csv`, `test_predictions.csv` | G

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

