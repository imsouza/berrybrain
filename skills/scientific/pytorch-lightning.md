---
id: sci-pytorch-lightning
name: "Scientific: pytorch-lightning"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Deep learning framework (PyTorch Lightning / lightning package). Organize PyTorch code into LightningModules, configure Trainers for multi-GPU/TPU, implement data pipelines, callbacks, logging (W&B, TensorBoard, MLflow), distributed training (DDP, FSDP, DeepSpeed), for scalable n"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "pytorch lightning"
  - "pytorch-lightning"
keywords:
  - "pytorch"
  - "lightning"
  - "deep"
  - "learning"
  - "framework"
---

# PyTorch Lightning

## Overview

PyTorch Lightning is a deep learning framework that organizes PyTorch code to eliminate boilerplate while maintaining full flexibility. Automate training workflows, multi-device orchestration, and implement best practices for neural network training and scaling across multiple GPUs/TPUs.

**Reviewed release:** [Lightning 2.6.6](https://github.com/Lightning-AI/pytorch-lightning/releases/tag/2.6.6), including its checkpoint-loading security fixes. CPU tests use Python 3.11, Torch 2.14.1 and Lightning 2.6.6. Use `import lightning as L` with the `lightning` distribution. The alternative `pytorch-lightning` distribution exposes `import pytorch_lightning as pl`; do not mix class namespaces within one application. GPU, TPU, multi-node and online logger examples are source-verified illustrations, not executed training validation.

## Installation

```bash
uv pip install "lightning==2.6.6"
```

Optional extras:

```bash
uv pip install "lightning[extra]==2.6.6"    # loggers, strategies, etc.
uv pip install wandb mlflow        # specific loggers as needed
```

## When to Use This Skill

This skill should be used when:
- Building, training, or deploying neural networks using PyTorch Lightning
- Organizing PyTorch code into LightningModules
- Configuring Trainers for multi-GPU/TPU training
- Implementing data pipelines with LightningDataModules
- Working with callbacks, logging, and distributed training strategies (DDP, FSDP, DeepSpeed)
- Structuring deep learning projects professionally

## Core Capabilities

### 1. LightningModule - Model Definition

Organize PyTorch models into six logical sections:

1. **Initialization** - `__init__()` and `setup()`
2. **Training Loop** - `training_step(batch, batch_idx)`
3. **Validation Loop** - `validation_step(batch, batch_idx)`
4. **Test Loop** - `test_step(batch, batch_idx)`
5. **Prediction** - `predict_step(batch, batch_idx)`
6. **Optimizer Configuration** - `configure_optimizers()`

**Quick template reference:** See `scripts/template_lightning_module.py` for a complete boilerplate.

**Detailed documentation:** Read `references/lightning_module.md` for comprehensive method documentation, hooks, properties, and best practices.

### 2. Trainer - Training Automation

The Trainer automates the training loop, device management, gradient operations, and callbacks. Key features:

- Multi-GPU/TPU support with strategy selection (DDP, FSDP, DeepSpeed)
- Automatic mixed precision training
- Gradient accumulation and clipping
- Checkpointing and early stopping
- Progress bars and logging

**Quick setup reference:** See `scripts/quick_trainer_setup.py` for common Trainer configurations.

**Detailed documentation:** Read `references/trainer.md` for all parameters, methods, and configuration options.

### 3. LightningDataModule - Data Pipeline Organization

Encapsulate all data processing steps in a reusable class:

1. `prepare_data()` - Download/cache on local rank zero per node by default; use global rank zero with shared storage when configured
2. `setup()` - Create datasets and apply transforms (per-GPU)
3. `train_dataloader()` - Return training DataLoader
4. `val_dataloader()` - Return validation DataLoader
5. `test_dataloader()` - Return test DataLoader

**Quick template reference:** See `scripts/template_datamodule.py` for a complete boilerplate.

**Detailed documentation:** Read `references/data_module.md` for method details and usage patterns.

### 4. Callbacks - Extensible Training Logic

Add custom functionality at specific training hooks without modifying your LightningModule. Built-in callbacks include:

- **ModelCheckpoint** - Save best/latest models
- **EarlyStopping** - Stop when metrics plateau
- **LearningRateMonitor** - Track LR scheduler changes
- **BatchSizeFinder** - Auto-determine optimal batch size

**Detailed documentation:** Read `references/callbacks.md` for built-in callbacks and custom callback creation.

### 5. Logging - Experiment Tracking

Integrate with multiple logging platforms:

- CSV locally; TensorBoard is the default only when its optional package is installed
- Weights & Biases (WandbLogger)
- MLflow (MLFlowLogger)
- Comet (CometLogger)
- CSV (CSVLogger)

`NeptuneLogger` was removed in Lightning 2.6.4; the Neptune service shut down March 5, 2026. The bundled helpers use local CSV logging; cloud tracking and model artifact uploads require an intentional choice.

Log metrics with `self.log("metric_name", value)` in supported LightningModule hooks; specify epoch/step reduction and batch size when they matter.

**Detailed documentation:** Read `references/logging.md` for logger setup and configuration.

### 6. Distributed Training - Scale to Multiple Devices

Choose the right strategy based on model size:

- **DDP** - When each device can hold the full model, optimizer state and activations
- **FSDP** - When sharding training state addresses measured memory pressure
- **DeepSpeed** - When its ZeRO/offload features fit the measured workload and CUDA stack

Choose from peak memory and throughput measurements, not a fixed parameter-count threshold.

Configure with: `Trainer(strategy="ddp", accelerator="gpu", devices=4)`

**Detailed documentation:** Read `references/distributed_training.md` for strategy comparison and configuration.

### 7. Best Practices

- Device agnostic code - Use `self.device` instead of `.cuda()`
- Hyperparameter saving - Use `self.save_hyperparameters()` in `__init__()`
- Metric logging - For scalar tensors, cross-device reduction requires `self.log(..., sync_dist=True)`; the default is `False`. Have all ranks participate in synchronized calls. For non-additive metrics such as AUROC, use a stateful TorchMetrics object with its own distributed synchronization instead of averaging per-rank AUROCs. See the [Lightning logging contract](https://lightning.ai/docs/pytorch/stable/extensions/logging.html) and [TorchMetrics integration](https://lightning.ai/docs/torchmetrics/stable/pages/lightning.html).
- Reproducibility - Use `seed_everything()` and `Trainer(deterministic=True)`
- Debugging - Use `Trainer(fast_dev_run=True)` to test with 1 batch

**Detailed documentation:** Read `references/best_practices.md` for common patterns and pitfalls.

## Quick Workflow

Copy the three scripts into a working directory, then run this CPU smoke there:

```python
import lightning as L
from template_datamodule import TemplateDataModule
from template_lightning_module import TemplateLightningMod

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

