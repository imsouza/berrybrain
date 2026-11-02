---
id: sciref-pathml-machine-learning
name: "Scientific Ref: Machine learning, inference batching, and model trust"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pathml): Machine learning, inference batching, and model trust"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pathml machine learning"
  - "machine learning, inference batching, and model trust"
keywords:
  - "pathml"
  - "machine"
  - "learning"
  - "specialized"
  - "scientific"
  - "reference"
---

# Machine learning, inference batching, and model trust

This reference targets **PathML 3.0.8 from PyPI**, reviewed 2026-10-01.
The architecture/inference examples are illustrative and checked against the
released source; no model weights or native inference stack were run.

## Stable ML exports

```python
from pathml.ml import (
    GNNLayer,
    HACTNet,
    HoVerNet,
    TileDataset,
    loss_hovernet,
    post_process_batch_hovernet,
)
```

The documented dataset import is usually:

```python
from pathml.datasets import TileDataset
```

PathML provides model architectures and helpers. Stable constructors do not
accept `pretrained=True`, do not expose `mode="fast"`, and do not download
official HoVer-Net/HACTNet checkpoints automatically.

## HoVer-Net

Stable constructor:

```python
from pathml.ml import HoVerNet

model = HoVerNet(n_classes=6)
```

- `n_classes=None` creates nucleus-pixel (NP) and horizontal/vertical (HV)
  branches for segmentation.
- An integer adds a nucleus-classification (NC) branch.
- Forward output is a list `[np_logits, hv]` or
  `[np_logits, hv, nc_logits]`.
- The architecture initializes weights; it is not a pretrained model loader.

Use the class count and label order from the exact dataset schema. PanNuke's
stable PathML representation can use five nucleus categories plus background;
do not silently map labels from another implementation.

Training helpers:

```python
from pathml.ml import loss_hovernet, post_process_batch_hovernet

outputs = model(images)
loss = loss_hovernet(
    outputs=outputs,
    ground_truth=[nucleus_mask, horizontal_vertical_map],
    n_classes=6,
)

instances, classified_instances = post_process_batch_hovernet(
    outputs=outputs,
    n_classes=6,
    small_obj_size_thresh=10,
    kernel_size=21,
    h=0.5,
    k=0.5,
)
```

Verify tensor shapes from the stable API:

```text
NP logits: (batch, 2, height, width)
HV maps:   (batch, 2, height, width)
NC logits: (batch, n_classes, height, width)
```

For `n_classes=6`, `nucleus_mask` above is a six-channel target with background
in the **last** channel, matching PathML's PanNuke representation. A single
binary mask is only appropriate when `n_classes=None`. Preserve the label
ordering; the loss derives foreground by inverting the final target channel.

`post_process_batch_hovernet` returns instance maps with 0 as background and
positive object IDs. The classification output uses one channel per class with
instance IDs in the selected class channel.

## Evaluation mode is not dynamic evaluation

PyTorch's `model.eval()` method switches module behavior such as dropout and
batch normalization to evaluation mode. It is **not** Python's dangerous built-in
expression evaluator and does not execute a string.

To avoid ambiguity in executable examples, the equivalent explicit form is:

```python
import torch

model.train(False)
with torch.inference_mode():
    outputs = model(images)
```

Never use Python dynamic evaluation or execution to load a model, transform,
configuration, metric, or class name. Use an allowlist and normal constructors.

## PanNuke training data

```python
from pathml.datasets import PanNukeDataModule

data = PanNukeDataModule(
    data_dir="approved_data/pannuke",
    download=False,
    shuffle=True,
    nucleus_type_labels=True,
    split=1,
    batch_size=8,
    hovernet_preprocess=True,
)

train_loader = data.train_dataloader
validation_loader = data.valid_dataloader
test_loader = data.test_dataloader
```

The dataloaders are properties, not methods. `hovernet_preprocess=True` adds the
HV target. Set `download=True` only after explicit consent to the Warwick
download, storage estimate, license review, and endpoint disclosure.

Do not assume the published folds satisfy every patient/source-slide grouping
claim. Audit the dataset's provenance and duplicates for the intended study.

## HACTNet

Stable signature:

```python
from pathml.ml import HACTNet

model = HACTNet(
    cell_params=cell_gnn_parameters,
    tissue_params=tissue_gnn_parameters,
    classifier_params=classifier_parameters,
)
```

HACTNet consumes a batched `HACTPairData` object with cell and tissue features,
their edge indices, a cell-to-tissue assignment, and a target. Parameter
dictionaries configure PathML `GNNLayer` and its classifier; use the v3.0.8
tutorial/API rather than copying a configuration from another PyG release.

Before training, validate:

- feature dimensions match each dictionary;
- assignment indices are valid tissue-node indices;
- graph batches carry the expected `x_cell_batch`/`x_tissue_batch`;
- targets are slide/patient-level as intended;
- all graphs from a patient remain in one split.

`pathml.datasets.EntityDataset` loads `.pt` graph objects with unrestricted
PyTorch deserialization. Use it only for trusted project-generated artifacts.

## Checkpoint trust

Never load an untrusted `.pt`, `.pth`, `.ckpt`, pickle, joblib, or saved pipeline.
Such formats can execute code during deserialization.

For a trusted checkpoint:

1. obtain it from the model owner or an approved registry;
2. verify exact SHA-256/signature before opening;
3. record architecture source revision, dependency lock, license, training data,
   preprocessing, class order, and expected tensor schema;
4. inspect in a disposable network-disabled environment;
5. load only the minimal weights-only representation when the producing PyTorch
   version supports it;
6. enforce file, tensor, RAM, time, and device limits; and
7. validate on synthetic tensors before any pathology data.

The bundled planner refuses checkpoint/model extensions and never imports Torch,
ONNX, PathML, or a model class.

## Local ONNX inference

Stable exports:

```python
from pathml.inference import (
    HaloAIInference,
    Inference,
    check_onnx_clean,
    convert_pytorch_onnx,
    remove_initializer_from_input,
)
```

For a reviewed local model:

```python
import numpy as np
from pathml.inference import Inference

inference = Inference(
    model_path="models/reviewed_model.onnx",
    input_name="data",
    num_classes=4,
    model_type="segmentation",
    local=True,
)
# Illustrative: supply a reviewed model expecting [1, 3, 256, 256] float32.
# Real preprocessing/range must come from that model's card.
image_hwc = np.zeros((256, 256, 3), dtype=np.float32)
prediction = inference.F(image_hwc)
assert prediction.shape == (1, 4, 256, 256)
```

Stable `Inference.apply()` replaces `tile.image` with model output. If the raw
imag

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

