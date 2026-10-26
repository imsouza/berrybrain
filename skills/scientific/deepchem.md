---
id: sci-deepchem
name: "Scientific: deepchem"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Builds molecular property prediction and MoleculeNet workflows with DeepChem, including SMILES featurization, scaffold or grouped holdouts, masked labels, graph models and explicit pretrained encoder transfer. Used for ADMET, toxicity, solubility and chemistry ML when DeepChem da"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "deepchem"
keywords:
  - "deepchem"
  - "builds"
  - "molecular"
  - "property"
  - "prediction"
  - "moleculenet"
  - "workflows"
---

# DeepChem

## When to use

Use for molecular property prediction, SMILES/graph featurization, MoleculeNet
benchmarks and explicitly configured encoder transfer. The workflow also covers
DeepChem materials and sequence adapters when their data/model contracts are met.

Targets **DeepChem 2.8.0**, still the stable PyPI release at review. Nightly 2.8.1
builds have additional APIs and different constraints; do not mix `latest` docs
with a stable installation. The tested CPU stack and optional-backend limitations
are in [references/review.md](references/review.md).

## Workflow

1. Define compound identity, assay conditions, target units and missing labels.
   Parse SMILES and retain a record of rejected rows. Audit duplicate structures
   and repeated measurements before splitting.
2. Match the representation to the model using the table below. Fit a numeric
   baseline first; dataset size alone does not select the best architecture.
3. Choose a scaffold, temporal or grouped holdout for the deployment question.
   Preserve exact split IDs, inspect scaffold overlap and per-task class support,
   and reject empty splits. Scaffold splitting does not eliminate all leakage.
4. Fit preprocessing on training data only. Preserve `dataset.w` masks. Normalize
   continuous targets only, and invert those transforms for metrics/predictions.
5. Select model settings/epochs on validation data and evaluate the final holdout
   once. Report per-task support, uncertainty across planned repeats and baseline
   comparisons. AUC requires both observed classes.
6. Predict using the training representation and transforms. Preserve identifiers,
   original target units and applicability limits. Successful fitting is not
   evidence of prospective scientific performance.

## Essential model contracts

| Model path | Input |
|---|---|
| Fingerprint baseline or `MultitaskRegressor` | Explicit `CircularFingerprint(size=2048)` |
| Torch GCN/GAT | `MolGraphConvFeaturizer()` |
| Torch AttentiveFP/MPNN | `MolGraphConvFeaturizer(use_edges=True)` |
| DMPNN | `DMPNNFeaturizer()`; binary tasks need `n_classes=2` |
| GROVER | `GroverFeaturizer` plus matching encoder checkpoint/configuration |
| HF wrapper | SMILES strings, actual network object and tokenizer object |

MoleculeNet's `'ECFP'` alias is **1024** bits, while the fingerprint class defaults
to **2048**. `'GraphConv'` is legacy `ConvMolFeaturizer`, incompatible with Torch
GCN. `'Raw'` defaults to RDKit Mol objects; use `DummyFeaturizer()` for raw strings.
Import Torch MPNN/GROVER from `deepchem.models.torch_models`.

Stable `HuggingFaceModel` returns logits and its training loss ignores sample
weights. The bundled HF transfer script accepts one fully observed, unweighted
binary/regression task and rejects sparse multitask datasets. A model ID or
`model_dir` is not itself a loaded pretrained model.

## Installation

Use an isolated Python 3.11 environment, outside any repository environment whose
Python requirement conflicts. This tested core stack supports the fingerprint,
DMPNN, local HF and GROVER smoke paths:

```bash
uv venv --python 3.11 .venv-deepchem
uv pip install --python .venv-deepchem/bin/python \
  'deepchem==2.8.0' 'torch==2.14.1' 'transformers==5.18.0' \
  'torch-geometric==2.8.0.post1'
```

The CPU smoke checks used these versions, not GPU builds. For GPU training install
the correct framework build according to its official platform instructions.
GCN/GAT/AttentiveFP/Torch MPNN additionally require mutually compatible **DGL and
DGL-LifeSci**; those backends were not available in this audit. Installing Torch
alone, or importing DeepChem successfully, does not establish those model paths.

The stable distribution exposes `torch`, `tensorflow`, `jax`, and `dqc` extras,
with historical optional dependency requirements; they are not an assurance that
every modern platform/backend combination resolves or executes. No `[all]` extra
exists. The TensorFlow, JAX and quantum-chemistry routes were source-reviewed only.
Check [release installation docs](https://deepchem.readthedocs.io/en/2.8.0/get_started/installation.html)
and [requirements](https://deepchem.readthedocs.io/en/2.8.0/get_started/requirements.html).
DeepChem attempts optional imports at package import time and can log skipped
modules; it does not promise all classes are available after that import.

## Bundled scripts

The primary executable end-to-end example is `predict_solubility.py` with a custom
CSV and query SMILES: validate complete continuous targets, create 2048-bit
fingerprints, scaffold-split, fit training-target normalization, train a Torch
`MultitaskRegressor`, then print original-unit metrics and predictions. Its Python
training function returns `(model, test, transformers)`. It does not invoke the
separate random-forest reference baseline or `GridHyperparamOpt` template.

The command prints results; it does not export split IDs, rejected-row tables or a
prediction file. Bad custom rows stop loading rather than becoming a saved rejection
audit. Persist data provenance, split IDs and outputs explicitly when adapting it
for research. Qualitative assay/applicability assessment remains the agent's work.

Run from this skill directory with the selected environment's Python. These
external-data commands are illustrative; offline synthetic fits are documented
in the review. All scripts use CPU, a scaffold split, fixed epochs, and report metrics;
they do not perform automatic early stopping or a hyperparameter search.

```bash
# ESOL log10(mol/L), or custom continuous targets in their declared input units.
python scripts/predict_solubility.py --epochs 50
python scripts/predict_solubility.py --data measured.csv \
  --smiles-col smiles --target-col logS --predict CCO c1ccccc1

# Model-specific graph features, including bonds where required.
python scripts/graph_neural_network.py --model dmpnn --dataset bbbp --epochs 20

# Explicit HF network + tokenizer; single complete task only.
python scripts/transfer_learning.py --model chemberta --dataset bbbp --epochs 10
```

The CSV guard rejects duplicate headers, non-finite labels, invalid SMILES and
featurization row loss. Empty labels remain masked for compatible graph losses;
custom solubility and HF training require complete targets. The shared scorer
reports original-unit regression metrics and excludes undefined AUC tasks from
macro means while reporting the contributing task count.

MoLFormer uses the current `ibm-research/MoLFormer-XL-b

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

