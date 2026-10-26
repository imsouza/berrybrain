---
id: sci-torchdrug
name: "Scientific: torchdrug"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Builds and troubleshoots TorchDrug 0.2.1 workflows for molecular graphs, property prediction, self-supervised pretraining, molecule generation, retrosynthesis, protein representation learning, and knowledge graph reasoning. Use when code imports torchdrug or needs its datasets, m"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "torchdrug"
keywords:
  - "torchdrug"
  - "builds"
  - "troubleshoots"
  - "workflows"
  - "molecular"
  - "graphs"
---

# TorchDrug

Use TorchDrug as a modular PyTorch graph-learning stack:

1. load a `datasets.*` dataset,
2. choose a `models.*` representation model,
3. wrap it in a `tasks.*` objective,
4. train and evaluate it with `core.Engine`.

The current official documentation and latest published release are both **0.2.1**
(released July 2023; rechecked October 1, 2026). Treat
newer Python or PyTorch combinations as unverified rather than silently assuming
compatibility.

## Start with the version guard

Before generating or debugging code, inspect the environment:

```bash
python --version
python -c "import torch; print(torch.__version__)"
python -c "import torchdrug; print(torchdrug.__version__)"
```

The supported matrix for TorchDrug 0.2.1 is:

- Python 3.7 through 3.10
- PyTorch 1.8 through 2.0
- Linux, Windows, or macOS
- Apple Silicon: PyTorch 1.13 or later, CPU only; no MPS support

If the project uses Python 3.11+ or PyTorch 2.1+, create a compatible environment
or explicitly test a source build. Do not present such combinations as supported.

## Installation

Prefer a dedicated Python 3.10 environment and pin the TorchDrug release:

```bash
uv venv --python 3.10
source .venv/bin/activate
uv pip install "torch==2.0.0" "numpy==1.26.4" "setuptools<81" wheel
```

Install `torch-scatter` and `torch-cluster` wheels matched to the exact PyTorch
and CUDA pair, following the
[official installation page](https://torchdrug.ai/docs/installation.html). For a
CPU-only PyTorch 2.0 environment on a platform listed in that wheel index, use:

```bash
uv pip install --only-binary :all: "torch-scatter==2.1.2" "torch-cluster==1.6.3" \
  --find-links "https://data.pyg.org/whl/torch-2.0.0+cpu.html"
uv pip install "torchdrug==0.2.1" "numpy==1.26.4" "scipy==1.13.1" \
  "rdkit-pypi==2022.9.5" "fair-esm==2.0.0" "decorator==5.1.1"
```

Do not copy a CUDA wheel URL between environments. Match the PyTorch version,
CUDA build, Python ABI, and platform. On Apple Silicon, the official docs require
building `torch-scatter` and `torch-cluster` from source; the wheel index above
has no macOS ARM64 wheels. Install PyTorch before building with
`--no-build-isolation`. A working compiler/SDK is also required; having PyTorch
installed alone does not guarantee a successful native build. See
[review and environment evidence](references/review.md) for the exact audit stack.
Use the **fair-esm** distribution, which imports as `esm`; the newer distribution
named `esm` is a different SDK. Do not install both RDKit distributions (`rdkit`
and `rdkit-pypi`) into one environment. NumPy 1.x avoids the old binary stack's
NumPy 2 ABI incompatibility; `setuptools<81` retains `pkg_resources` for PyTorch 2.0.

## Canonical property-prediction workflow

Use the documented ClinTox → GIN → `PropertyPrediction` → `Engine` pattern. The random split below is a tutorial baseline. For generalization to new molecular scaffolds, use `data.scaffold_split` or the benchmark's specified split, keep duplicate molecules in one partition, and record the actual split sizes and class counts. Scaffold-group allocation may not match the requested lengths exactly.

First run the [ClinTox cache preparation](references/datasets.md#clintox-download-repair).
The release's old HTTP download URL fails; the current official HTTPS asset has
the identical release MD5. The full training examples are illustrative and were
not run to convergence during this review.

```python
import torch
from torchdrug import core, datasets, models, tasks

dataset = datasets.ClinTox("~/molecule-datasets/")
lengths = [int(0.8 * len(dataset)), int(0.1 * len(dataset))]
lengths.append(len(dataset) - sum(lengths))
train_set, valid_set, test_set = torch.utils.data.random_split(
    dataset, lengths, generator=torch.Generator().manual_seed(1)
)

model = models.GIN(
    input_dim=dataset.node_feature_dim,
    hidden_dims=[256, 256, 256, 256],
    short_cut=True,
    batch_norm=True,
    concat_hidden=True,
)
task = tasks.PropertyPrediction(
    model,
    task=dataset.tasks,
    criterion="bce",
    metric=("auprc", "auroc"),
)

optimizer = torch.optim.Adam(task.parameters(), lr=1e-3)
solver = core.Engine(
    task,
    train_set,
    valid_set,
    test_set,
    optimizer,
    batch_size=1024,
)
solver.train(num_epoch=100)
solver.evaluate("valid")
```

Add `gpus=[0]` only when a supported CUDA device is available. Omit `gpus` for
CPU execution.

For binary classification, `task.predict(batch)` returns logits; apply
`torch.sigmoid` when probabilities are needed. In 0.2.1, normalized regression
predictions are returned on the original target scale, which is a breaking change
from older releases.

## Choose the official workflow

### Molecular property prediction

- Dataset: `datasets.ClinTox`, `BBBP`, `Tox21`, `QM9`, or another documented
  molecule dataset.
- Model: start with `models.GIN`; use `edge_input_dim` when the selected feature
  configuration supplies edge features.
- Task: `tasks.PropertyPrediction`.
- Read [molecular property prediction](references/molecular_property_prediction.md).

### Self-supervised molecular pretraining

- InfoGraph: `models.InfoGraph(gin_model, separate_model=False)` wrapped by
  `tasks.Unsupervised`.
- Attribute masking: `tasks.AttributeMasking(model, mask_rate=0.15)`.
- Recreate the same encoder for fine-tuning. AttributeMasking and InfoGraph
  checkpoints have different encoder key prefixes; verify transferred weights
  as described in the reference before training `tasks.PropertyPrediction`.
- Read [molecular property prediction](references/molecular_property_prediction.md).

### Molecule generation

- Dataset: `datasets.ZINC250k(..., kekulize=True, atom_feature="symbol")`.
- GCPN: an `models.RGCN` encoder wrapped by `tasks.GCPNGeneration`.
- GraphAF: node and edge `models.GraphAF` flows wrapped by
  `tasks.AutoregressiveGeneration`.
- Supported optimization tasks in the tutorial are `"qed"` and `"plogp"`;
  criteria are `"nll"` and/or `"ppo"`.
- Read [molecular generation](references/molecular_generation.md).

### Retrosynthesis

- Create two synchronized `datasets.USPTO50k` views: reaction mode for center
  identification and `as_synthon=True` for synthon completion.
- Train `tasks.CenterIdentification` and `tasks.SynthonCompletion` separately.
- Combine the trained tasks with `tasks.Retrosynthesis`; do not pass raw models
  directly to the end-to-end task.
- Read [retrosynthesis](references/retrosynthesis.md).

### Knowledge graph reasoning

- Embedd

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

