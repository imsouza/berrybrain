---
id: sci-modal
name: "Scientific: modal"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Modal is a serverless cloud platform for running Python on demand, including on-demand GPUs. Use when deploying or serving AI/ML models, running GPU-accelerated workloads (training, fine-tuning, inference), serving web endpoints, scheduling batch jobs, or scaling Python code to c"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "modal"
keywords:
  - "modal"
  - "serverless"
  - "cloud"
  - "platform"
  - "running"
  - "python"
---

# Modal

## Overview

Modal is a cloud platform for running Python code serverlessly, with a focus on AI/ML workloads. Key capabilities:
- **GPU compute** on demand (including H100, H200, B200 and B300)
- **Serverless functions** with autoscaling from zero to thousands of containers
- **Custom container images** built entirely in Python code
- **Persistent storage** via Volumes for model weights and datasets
- **Web endpoints** for serving models and APIs
- **Scheduled jobs** via cron or fixed intervals
- **Container reuse** and warm pools to reduce cold starts (model loading still takes time)

Modal Apps and Images are defined in Python; existing Dockerfiles are also supported.

## When to Use This Skill

Use this skill when:
- Deploy or serve AI/ML models in the cloud
- Run GPU-accelerated computations (training, inference, fine-tuning)
- Create serverless web APIs or endpoints
- Scale batch processing jobs in parallel
- Schedule recurring tasks (data pipelines, retraining, scraping)
- Need persistent cloud storage for model weights or datasets
- Want to run code in custom container environments
- Build job queues or async task processing systems

## Installation and Authentication

### Install

```bash
uv pip install "modal==1.6.0"
```

Reviewed against SDK 1.6.0 and current [release notes](https://modal.com/docs/sdk/py/releases).
Local SDK construction and selected handlers were tested; remote builds, deployments,
GPU inference and cloud limits were not executed. Snippets using model/data placeholders
or third-party workloads are illustrative and require their stated dependencies.

### Authenticate

Prefer existing credentials before creating new ones. Only the two Modal-specific
variables below are relevant — do not read, load, or expose any other environment
variables or `.env` file contents:

1. Reuse an existing Modal profile, or check whether both `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` are set; report presence only.
2. If not, look up only those two keys in a local `.env` file (ignore all other entries) and load them if appropriate for the workflow.
3. Only fall back to interactive `modal setup` if no usable profile or token pair exists. The SDK supports profiles in `.modal.toml`; environment tokens are optional when a profile authenticates.

```bash
modal setup
```

This opens a browser for authentication. For CI/CD or headless environments, use environment variables:

```bash
export MODAL_TOKEN_ID=<your-token-id>
export MODAL_TOKEN_SECRET=<your-token-secret>
```

If neither an existing profile nor a token pair is available, create credentials at https://modal.com/settings

Check [current pricing](https://modal.com/pricing) and workspace quotas before sizing a run. GPU use requires a payment method even when credits remain.

**Reference**: See `references/getting-started.md` for detailed setup and first app walkthrough.

## Core Concepts

### App and Functions

A Modal `App` groups related functions. Functions decorated with `@app.function()` run remotely in the cloud:

```python
import modal

app = modal.App("my-app")

@app.function()
def square(x):
    return x ** 2

@app.local_entrypoint()
def main():
    # .remote() runs in the cloud
    print(square.remote(42))
```

Run with `modal run script.py`. Deploy with `modal deploy script.py`.

**Reference**: See `references/functions.md` for lifecycle hooks, classes, `.map()`, `.spawn()`, and more.

### Container Images

Modal builds container images from Python code. The recommended package installer is `uv`:

```python
image = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_pip_install("torch==2.12.0", "transformers==5.9.0", "accelerate==1.13.0")
    .apt_install("git")
)

@app.function(image=image, gpu="L40S")
def inference(prompt):
    from transformers import pipeline
    pipe = pipeline("text-generation", model="openai-community/gpt2", device=0)
    return pipe(prompt)
```

Key image methods:
- `.uv_pip_install()` — Install Python packages with uv (recommended)
- `.pip_install()` — Install with pip (fallback)
- `.apt_install()` — Install system packages
- `.run_commands()` — Run shell commands during build
- `.run_function()` — Run Python during build (e.g., download model weights)
- `.add_local_python_source()` — Add local modules
- `.env()` — Set environment variables

**Reference**: See `references/images.md` for Dockerfiles, micromamba, caching, GPU build steps.

### GPU Compute

Request GPUs via the `gpu` parameter:

```python
@app.function(gpu="H100")
def train_model():
    import torch
    device = torch.device("cuda")
    # GPU training code here

# Multiple GPUs
@app.function(gpu="H100:4")
def distributed_training():
    ...

# GPU fallback chain
@app.function(gpu=["H100", "A100-80GB", "A100-40GB"])
def flexible_inference():
    ...
```

Available GPU strings include T4, L4, A10, L40S, A100, A100-40GB, A100-80GB, RTX-PRO-6000, H100, H200, B200, B200+ and B300.

- GPUs are always specified as **strings** (e.g. `gpu="H100"`, `gpu="H100:4"`). The old `modal.gpu.*` objects are deprecated as of v0.73.31.
- Up to 8 GPUs per container (except A10: up to 4)
- L40S is recommended for inference (cost/performance balance, 48 GB VRAM)
- H100/A100 can be auto-upgraded to H200/A100-80GB at no extra cost; explicit A100-40GB selects 40 GB
- Use `gpu="H100!"` to prevent auto-upgrade
- B300 and B200+ require CUDA 13.1+ compatibility; RTX-PRO-6000 has 96 GB VRAM

**Reference**: See `references/gpu.md` for GPU selection guidance and multi-GPU training.

### Volumes (Persistent Storage)

Volumes provide distributed, persistent file storage:

```python
vol = modal.Volume.from_name("model-weights", create_if_missing=True)

@app.function(volumes={"/data": vol})
def save_model():
    import torch
    model = train_model()  # Application-defined training code
    # Write to the mounted path
    with open("/data/model.pt", "wb") as f:
        torch.save(model.state_dict(), f)
    vol.commit()

@app.function(volumes={"/data": vol})
def load_model():
    import torch
    vol.reload()
    model = MyModel()  # Application-defined architecture
    model.load_state_dict(torch.load("/data/model.pt", weights_only=True))
```

- Optimized for write-once, read-many workloads (model weights, datasets)
- CLI access: `modal volume ls`, `modal volume put`, `modal volume get`
- Background auto-commits every few seconds
- For a producer/consumer handoff, close output files and explicitly `vol.commit()`
  before signaling completion; 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

