---
id: sci-pyhealth
name: "Scientific: pyhealth"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Builds and validates PyHealth clinical machine-learning pipelines for EHR, signals, imaging, and medical codes. Use for PyHealth dataset loading, MIMIC-III/IV, eICU or OMOP prediction tasks, patient-level evaluation, mortality/readmission/length-of-stay modeling, medication recom"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "pyhealth"
keywords:
  - "pyhealth"
  - "builds"
  - "validates"
  - "clinical"
  - "machine"
  - "learning"
---

# PyHealth

Targets **PyHealth 2.0.2**, verified against its released wheel, current official
documentation, and CPU execution on Python 3.12/Torch 2.7.1. PyHealth's pipeline is
`Dataset -> Task -> Model -> Trainer -> Metrics`; its 1.x and 2.x interfaces differ.
Do not combine legacy `Visit` examples with the 2.x event/processor API.

## When to use

Use for clinical prediction with PyHealth, including EHR sequences, physiological
signals, imaging tasks, or medical-code lookup. Establish the cohort, prediction
time, observation window, outcome horizon, and unit of evaluation before modeling.
For general tabular learning without a PyHealth dataset/task, this skill is optional.

## Install and smoke-test

```bash
uv run --no-project --isolated --python 3.12 --with pyhealth==2.0.2 python assets/starter_pipeline.py --demo --epochs 1
```

Run that command from the skill directory, or use the absolute path to the asset.
It trains on invented in-memory records and exercises patient splitting, metrics,
and best-checkpoint restoration. It provides no evidence of clinical performance.
See [installation](references/installation.md) for project setup and device options.

## Workflow

1. **Inspect the installed version and dataset configuration.** Both MIMIC-III and
   MIMIC-IV use lowercase table selectors in 2.0.2. MIMIC-III files remain uppercase.
2. **Check task semantics and required tables.** `MortalityPredictionMIMIC3` predicts
   death in the *next admission*, excludes the last admission, and requires diagnoses,
   procedures and prescriptions in the current admission. It is not a current-stay
   early-warning model. Missing/invalid next-admission mortality flags are assigned
   zero upstream; audit this before using real data.
3. **Create supervised samples.** `base.set_task(task)` returns a processed dataset
   with input/output schemas. Inspect raw task output as well as processed samples.
4. **Partition by patient and verify overlap, class counts and observation windows.**
   `split_by_patient(..., seed=42)` is random, not chronological or stratified.
   It does not prevent within-visit temporal leakage or preprocessing leakage.
5. **Choose a schema-compatible model and run one batch before training.** Construct
   it from the training sample dataset. Transformer uses `embedding_dim`, not
   `hidden_dim`; arguments are model-specific.
6. **Declare validation metrics and the exact monitor.** Supply `metrics=[...]` to
   `Trainer`; the monitor must be a returned key. An absent key raises an error.
   Use `monitor_criterion="min"` for loss, `"max"` for AUC/accuracy.
7. **Evaluate the held-out test set once the model choice is fixed.** Report prevalence,
   patient counts, discrimination, calibration, threshold policy and uncertainty as
   appropriate. PR-AUC's no-skill reference depends on prevalence, not a universal 0.5.

## MIMIC-III prototype

This is the 2.0.2 interface shape; the starter adds partition and label checks.
Use a local authorized root for real data. The public bucket is synthetic data.

```python
from pyhealth.datasets import MIMIC3Dataset, get_dataloader, split_by_patient
from pyhealth.tasks import MortalityPredictionMIMIC3
from pyhealth.models import Transformer
from pyhealth.trainer import Trainer

base = MIMIC3Dataset(
    root="https://storage.googleapis.com/pyhealth/Synthetic_MIMIC-III/",
    tables=["diagnoses_icd", "procedures_icd", "prescriptions"],
    cache_dir="./cache/mimic3", num_workers=1, dev=True,
)
samples = base.set_task(MortalityPredictionMIMIC3())
train, val, test = split_by_patient(samples, [0.6, 0.2, 0.2], seed=42)
loaders = [get_dataloader(part, batch_size=16, shuffle=(i == 0))
           for i, part in enumerate((train, val, test))]
model = Transformer(dataset=train, embedding_dim=8)
trainer = Trainer(model=model, metrics=["accuracy"], device="cpu")
trainer.train(train_dataloader=loaders[0], val_dataloader=loaders[1],
              epochs=1, monitor="accuracy", monitor_criterion="max")
print(trainer.evaluate(loaders[2]))
```

The public synthetic task with `dev=True` (up to 1000 patients) produced only
20 samples (18 negative, 2 positive) in the review run. Accuracy here checks execution only; random splits can lack a
class, so this is unsuitable for reliable AUC estimation.

`set_task` fits processors before this split. This prototype therefore learns its
vocabulary from the whole cohort. For strict held-out evaluation, partition raw
patients first, fit processors on training samples only, then reuse them for
validation/test; see [examples](references/examples.md). Learned adjacency matrices
(e.g. GAMENet) must also use training records only.

## Critical API and scientific checks

- **MIMIC-IV:** `MIMIC4Dataset(ehr_root=..., ehr_tables=[...])`; the simpler
  `MIMIC4EHRDataset(root=..., tables=[...])` is also available. The root contains both
  `hosp/` and `icu/`, not just `hosp/`.
- **Caches exist by default.** `cache_dir=None` selects the user cache directory;
  a supplied path selects its root. Cache identity does not hash raw file contents
  or custom task source. Use a fresh cache root after changing data/config/task code.
- **Patient access:** `patient.get_events(event_type=..., filters=[(...)])`, not
  `patient.visits` or `visit.get_code_list(...)`.
- **Patient independence:** visit-level random splitting can put one patient's
  admissions in multiple partitions. Choose the split to match the deployment claim.
- **Outcome availability:** discharge diagnoses and notes are unavailable for many
  early prediction times. Feature timestamps and recording/store times both matter.
- **Clinical interpretation:** attention weights and DDI penalties are modeling tools;
  they do not establish causal explanation, prescribing safety or deployment readiness.
- **Network resources:** medical-code tables download on first use and are cached.
  Mapping may be one-to-many or empty; retain coding-system version and provenance.

## Reference files

| Need | Read |
|---|---|
| Dependencies, devices, restricted data and caches | [installation](references/installation.md) |
| Dataset classes, constructors, event access and splitting | [datasets](references/datasets.md) |
| Task schemas, label semantics and custom tasks | [tasks](references/tasks.md) |
| Model compatibility and training contracts | [models](references/models.md) |
| Code lookup, mappings and tokenizer shapes | [medical codes](references/medcode.md) |
| Adaptable recipes and train-only pr

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

