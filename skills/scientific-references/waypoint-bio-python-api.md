---
id: sciref-waypoint-bio-python-api
name: "Scientific Ref: Using Waypoint from Python"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (waypoint-bio): Using Waypoint from Python"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "waypoint bio python api"
  - "using waypoint from python"
keywords:
  - "waypoint"
  - "bio"
  - "python"
  - "api"
  - "specialized"
  - "scientific"
  - "reference"
---

# Using Waypoint from Python

The CLI covers the standard paths. Drop to Python when you need a custom training loop, a different
head, or embeddings inside a larger pipeline. Hub examples are source-checked templates;
the review ran tiny random CPU models and local synthetic taxa, without gated weights or data.
Use the compatibility stack in `SKILL.md`; see `upstream-review.md` for release limitations.

## Package surface

`waypoint_bio` lazily re-exports:

```python
from waypoint_bio import (
    TaxonomicTokenizer,             # the tokenizer class
    load_tokenizer,                 # load one from a Hub id or local dir
    MicrobiomePretrainingDataset,   # causal-LM dataset
    MicrobiomeBenchmarkDataset,     # supervised dataset with targets/covariates
    load_waypoint_dataframe,        # read waypoint-format parquet/csv/tsv
    load_abundance_matrix,          # read a sample x taxa matrix
    matrix_to_waypoint_df,          # matrix -> waypoint format
)
```

Imports are deferred, so `import waypoint_bio` does not pull in torch.

## Loading a checkpoint directly with transformers

The tokenizer is custom and ships as remote code, so `trust_remote_code=True` is required for it.
The model itself is a stock GPT-2 and does not need it.

```python
from transformers import AutoTokenizer, AutoModel

model_id = "outpost-bio/Waypoint-45m"
revision = "1664ab5ec88b4bdf571f2512968f99dc222ce0ac"  # Hub metadata checked 2026-10-01
tok = AutoTokenizer.from_pretrained(model_id, revision=revision, trust_remote_code=True)
model = AutoModel.from_pretrained(model_id, revision=revision)  # requires approved access
```

Review the repository's `tokenization_taxonomic.py` before executing it. The upstream
`load_tokenizer(model_path)` and `try_load_token_std_means(model_path)` do not accept a
`revision`, and CLI commands do not expose one. To keep tokenizer, weights and statistics
at the same revision, download a snapshot after access approval and use its local path:

```python
from huggingface_hub import snapshot_download

checkpoint = snapshot_download(repo_id=model_id, revision=revision)
# Pass checkpoint to --model, load_tokenizer and try_load_token_std_means.
```

This downloads model artifacts; it was not executed during the bounded review. A public Hub
model card or metadata response does not grant access to its gated files.

`AutoModelForCausalLM` also works if you want the LM head for likelihood scoring or generation —
generation samples taxa, which is occasionally useful for probing what the model learned about
co-occurrence, but is not a validated use.

## Tokenizing by hand

```python
from waypoint_bio import load_tokenizer

tok = load_tokenizer("outpost-bio/Waypoint-6m")

lineage = "k__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Lactobacillaceae; g__Lactobacillus"
print(tok.tokenize(lineage))                    # ['g__Lactobacillus']
print(tok.convert_tokens_to_ids(["g__Lactobacillus"]))

# One sample = newline-separated lineages
sample = "\n".join([lineage, "k__Bacteria; p__Bacteroidota; g__Bacteroides"])
print(tok(sample)["input_ids"])
```

Checking whether a taxon is in vocabulary:

```python
vocab = tok.get_vocab()
"g__Lactobacillus" in vocab          # inspect the exact checkpoint vocabulary
tok.convert_tokens_to_ids("g__Nonesuch") == tok.unk_token_id
```

`tok._extract(lineage)` applies rank extraction and higher-rank fallback, returning a token
string or `None`. It is private and source-checked only for the reviewed versions; the bundled
coverage helper instead uses `convert_tokens_to_ids`. `tok(sample)` alone does not reproduce
the dataset encoding: it does not sort by abundance or explicitly add BOS/EOS. Use the dataset
or `tokenize_for_embedding` for the model's sample representation.

## Building a dataset

```python
import pandas as pd
from waypoint_bio import MicrobiomePretrainingDataset, load_tokenizer, load_waypoint_dataframe
from waypoint_bio.dataset import try_load_token_std_means

df = load_waypoint_dataframe("dataset.parquet")
tok = load_tokenizer("outpost-bio/Waypoint-6m")
stats = try_load_token_std_means("outpost-bio/Waypoint-6m")   # None if absent

ds = MicrobiomePretrainingDataset(df, tok, max_length=512, token_std_means=stats)
ds[0]["input_ids"].shape        # torch.Size([512])
```

Each item is `[BOS] + ordered token ids + [EOS]`, right-padded. With no statistics it uses raw
abundance order. `MicrobiomePretrainingDataset` drops rows with no known taxa, so its row count
can differ from `df`. Its raw `labels` include pad IDs; use `DataCollatorForLanguageModeling`
with `mlm=False` to mask pad labels, as the CLI does.

Computing the ordering statistics for a corpus of your own:

```python
from waypoint_bio.dataset import compute_token_std_means

train_df = df  # replace with the training subset only when holding out validation/test data
stats = compute_token_std_means(train_df, tok, show_progress=True)
stats.to_parquet("token_std_means.parquet")   # index name "token", columns mean/std
```

For a newly trained model, store these statistics beside its checkpoint. For an existing
pretrained model, retain its original statistics: replacing them changes token ordering and
the input distribution. Upstream catches every Hub statistics-download exception and falls
back to raw abundance order, including authorization/network errors; require the expected
local file for reproducible comparisons.

## Embeddings without the CLI

```python
import torch
from transformers import AutoModel
from waypoint_bio.dataset import load_waypoint_dataframe, try_load_token_std_means
from waypoint_bio.embed import tokenize_for_embedding
from waypoint_bio.models import _pool
from waypoint_bio.tokenizer import load_tokenizer

model_path = checkpoint  # reviewed local snapshot from above
df = load_waypoint_dataframe("dataset.parquet")
tok = load_tokenizer(model_path)
model = AutoModel.from_pretrained(model_path).eval()

samples = tokenize_for_embedding(df, tok, max_length=512,
                                 token_std_means=try_load_token_std_means(model_path))

# This small example materializes the whole batch; use a DataLoader for large datasets.
input_ids = torch.stack([s["input_ids"] for s in samples])
attn = torch.stack([s["attention_mask"] for s in samples])

with torch.no_grad():
    hidden = model(input_ids=input_ids, attention_mask=attn).last_hidden_state
    emb = _pool(hidden, attn, "last_token")     # [n_samples, hidden_size]
```

`tokenize_for_embedding` preserv

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

