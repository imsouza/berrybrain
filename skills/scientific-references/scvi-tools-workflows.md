---
id: sciref-scvi-tools-workflows
name: "Scientific Ref: Training, persistence and reference mapping"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scvi-tools): Training, persistence and reference mapping"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scvi tools workflows"
  - "training, persistence and reference mapping"
keywords:
  - "scvi"
  - "tools"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
  - "training"
---

# Training, persistence and reference mapping

Targets scvi-tools 1.5.1. Examples are source-verified, illustrative workflows.
Short CPU tests exercised core fitting, metric access, save/load and minification;
GPU, distributed, large-data, query-transfer and interpretability paths were not run.

## Prepare data before registration

Start with the count-preserving example in [SKILL.md](../SKILL.md). QC thresholds
are experiment-specific. Scanpy's `seurat_v3` HVG flavor takes counts; its default
`seurat` flavor expects log-normalized data. Never copy an unknown `.X` into a
layer called `counts` and assume the name proves provenance. Keep full-feature
counts separately if later gene testing needs more than the selected HVGs.

For QC, define mitochondrial genes before `calculate_qc_metrics`, select a naming
convention appropriate to the organism, and set `percent_top=None` for tiny feature
panels. Current Scanpy exposes `sc.pp.scrublet`; doublet thresholds require
capture-specific validation. Finish subsetting with `.copy()` before setup.
Register only justified nuisance covariates. Concatenating study and sample IDs
creates a composite category, not a hierarchical statistical model.

```python
scvi.model.SCVI.setup_anndata(
    adata, layer="counts", batch_key="sequencing_batch",
)
model = scvi.model.SCVI(adata, n_latent=20, n_layers=2, gene_likelihood="nb")
model.view_anndata_setup()
model.train(
    max_epochs=400, batch_size=128, train_size=0.9,
    early_stopping=True, check_val_every_n_epoch=1,
    plan_kwargs={"lr": 1e-3},
)
```

For SCVI, optimizer parameters such as `lr` belong in `plan_kwargs` (or the 1.5
training-plan configuration interface), not arbitrary Lightning Trainer kwargs.
Some specialized models define `lr` directly; check that model's signature.
`view_anndata_setup()` is an instance method.

## Training diagnostics and model selection

```python
# These logged metrics are losses: lower is better.
train_loss = model.history["elbo_train"]
validation_loss = model.history["elbo_validation"]
last_validation_loss = float(validation_loss.iloc[-1, 0])
# This method returns the ELBO with the opposite sign: higher is better.
heldout_elbo = float(model.get_elbo(indices=model.validation_indices))
```

Use identical train/validation splits and feature universes when tuning. Random
cell splits share donors and do not estimate performance on new donors; use an
external biological-sample split for that estimand. If an Optuna study minimizes
`elbo_validation`, its direction must be `minimize`; use `maximize` only for the
actual `get_elbo()` value. A history DataFrame is indexed with `.iloc`, not `[-1]`.
Record the selected epoch and whether final or best weights were evaluated.

```python
from scvi.train import SaveCheckpoint

model.train(
    max_epochs=400, early_stopping=True, check_val_every_n_epoch=1,
    enable_checkpointing=True,
    callbacks=[SaveCheckpoint(
        monitor="elbo_validation", mode="min", load_best_on_end=True,
    )],
)
```

Validation must actually run and log the monitored key. The default scvi logger
is an in-memory `SimpleLogger`; `logger=False` removes history and can conflict
with TOTALVI's learning-rate monitor. Repeating `train` on an
already trained model continues fitting; create a fresh model for each candidate.
Report seeds, model parameters, split definition, stopping rule, package versions
and hardware. A short fit with finite loss proves only mechanics.

## Save and reload

```python
model.save("scvi_model", save_anndata=True)
restored = scvi.model.SCVI.load("scvi_model")
# Alternatively save_anndata=False (the default), then supply the matching data:
model.save("weights_and_registry")
restored = scvi.model.SCVI.load("weights_and_registry", adata=adata)
```

Use a new directory for each model unless replacement is intended. Keep the exact
registered genes/order, counts, batch encodings and covariates. A saved inference
model is not automatically a full optimizer/scheduler checkpoint for faithful
training resume. Load only trusted artifacts and record scvi/PyTorch versions.

## Query-to-reference mapping (scArches)

Assumes a trained, saved reference and query counts using compatible gene IDs and
measurement units. Inspect reference coverage and duplicates before preparation.

```python
scvi.model.SCVI.prepare_query_anndata(query_adata, "scvi_model")
query_model = scvi.model.SCVI.load_query_data(query_adata, "scvi_model")
query_model.train(max_epochs=200, plan_kwargs={"weight_decay": 0.0})
query_adata.obsm["X_scVI"] = query_model.get_latent_representation()
```

`prepare_query_anndata` pads/reorders features to the reference. Report missing
features and stop when coverage is scientifically inadequate; zero padding cannot
recover unmeasured genes. `load_query_data` transfers the registry and performs
model-specific freezing. Do not manually call query setup with guessed categories
or silently train a joint reference model instead. For labels, prefer a validated
SCANVI reference or evaluate a classifier on reference embeddings with rejection
for unsupported cell types. KNN labels are predictions, not verified identities.

## Minification for supported RNA models

Minification stores posterior parameters and can omit counts. It is not weight
quantization and does not shrink every model. Preserve the full count dataset and
model first. The method replaces `model.adata` and returns `None`:

```python
qzm, qzv = model.get_latent_representation(return_dist=True)
model.adata.obsm["X_latent_qzm"] = qzm
model.adata.obsm["X_latent_qzv"] = qzv
model.minify_adata()
model.save("minified_scvi", save_anndata=True)
mini_model = scvi.model.SCVI.load("minified_scvi")
```

Do not pass `adata` as the first positional argument; that argument is a
minification-type string. Default minification removes counts, so full training,
raw-count statistics and methods needing counts may be unavailable. Verify the
specific downstream method before replacing a full-data artifact.

## Data loading and memory

```python
from scvi.dataloaders import AnnDataLoader
loader = AnnDataLoader(model.adata_manager, batch_size=128, shuffle=False)
for tensors in loader:
    # A dictionary of registered tensors, for a custom model/training loop.
    break
```

`AnnDataLoader` takes an `AnnDataManager`, not an unregistered AnnData object,
and lives in `scvi.dataloaders`, not `scvi.data`. Backed H5AD can support certain
access patterns, but a model/setup/preprocessing step can still mat

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

