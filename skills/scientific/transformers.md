---
id: sci-transformers
name: "Scientific: transformers"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Hugging Face Transformers for loading Hub models, running pipeline inference, text generation, and Trainer fine-tuning on NLP, vision, audio, and multimodal tasks. Applies when working with AutoModel, pipelines, tokenizers, generation configs, or TrainingArguments within Transfor"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "transformers"
keywords:
  - "transformers"
  - "hugging"
  - "face"
  - "loading"
  - "models"
  - "running"
---

# Transformers

## Overview

The Hugging Face Transformers library provides access to thousands of pre-trained models for tasks across NLP, computer vision, audio, and multimodal domains. Use this skill to load models, perform inference, and fine-tune on custom data.

## Installation

Targets **Transformers 5.18.0**, verified against its released source on 2026-10-01. Native CPU checks use Python 3.11, Torch 2.14.1, Datasets 5.0.1, Accelerate 1.15.0, PEFT 0.21.2, and Hub 1.33.0. The Torch extra requires Torch >=2.5. Install in a dedicated environment:

```bash
uv venv --python 3.11 .venv-transformers
uv pip install --python .venv-transformers/bin/python "transformers[torch]==5.18.0" "torch==2.14.1" "huggingface-hub==1.33.0" "datasets==5.0.1" "accelerate==1.15.0" "peft==0.21.2"
```

Use `.venv-transformers/Scripts/python.exe` on Windows. Select an appropriate Torch build for the target hardware before installation. Hub 2.1.1 is newer, but Datasets 5.0.1 requires Hub <2; upgrading every package independently makes this training stack unsatisfiable. The separate `esm` SDK currently requires Transformers <5 and belongs in another environment.

Optional dependencies (install only for the selected workflow): Pillow 12.3.0 for images; torchvision matched to Torch and timm 1.0.30 for models that require them; librosa 1.0.0 and soundfile 0.14.0 for audio preprocessing (librosa requires Python >=3.12); FFmpeg for encoded audio file inputs; pytesseract plus Tesseract for OCR document pipelines; bitsandbytes 0.50.2 for supported quantization backends. See [model loading](references/models.md) before choosing precision or quantization.

Verification used tiny random models, synthetic input, and local save/reload only. Hub pretrained examples throughout this skill are **illustrative**: public checkpoint metadata and configurations were reviewed, but no weights or datasets were downloaded and no hosted inference or uploads were run. Optional export/distributed/hardware paths are source-checked, not end-to-end tested. See [review evidence](references/review.md).

Check your version:

```python
import transformers
print(transformers.__version__)
```

## Authentication

Many models on the Hugging Face Hub are gated or private. Authenticate before loading them.

**Recommended:** CLI login (uses `$HF_TOKEN_PATH`, defaulting to `$HF_HOME/token`, normally `~/.cache/huggingface/token`):

```bash
hf auth login
```

**Python:**

```python
from huggingface_hub import login
login()  # Interactive prompt; do not hardcode tokens in scripts
```

**Servers / CI:** set `HF_TOKEN` in the environment (never commit tokens to git or shell profiles):

```bash
export HF_TOKEN="..."  # Read token from a secret manager, not source code
```

Get tokens at: https://huggingface.co/settings/tokens

**Security:** Never paste tokens into notebooks, repos, or shared configs. Prefer `hf auth login` over exporting tokens in `.bashrc` or `.zshrc`.

Use the narrowest token scope that works: `read` for private or gated model downloads, `write` only for uploads. If a long-running environment should not send the stored token on every Hub request, set `HF_HUB_DISABLE_IMPLICIT_TOKEN=1` and pass a token only where authentication is required.

## Transformers v5

Transformers v5 is **PyTorch-only** (TensorFlow and JAX backends were removed). For upgrades from v4, see the [v5 migration guide](https://github.com/huggingface/transformers/blob/v5.18.0/MIGRATION_GUIDE_V5.md). Transformers 5.18.0 accepts Hub >=1.31,<3; preserve the tighter constraint of Datasets when training.

**Gated or custom architectures:** accept the model license on the Hub, then load with `trust_remote_code=True` only when required custom code has been reviewed; pin its full immutable commit with `revision` (and `code_revision` for a separate code repository). Gating and custom code are independent: a gated built-in architecture does not require remote code.

**Cache location:** set `HF_HOME` for all Hugging Face caches, or `HF_HUB_CACHE` just for Hub files. Use `HF_HUB_OFFLINE=1` only after required model snapshots are already cached.

## Quick Start

Use the Pipeline API for fast inference without manual configuration:

```python
from transformers import pipeline

# Text generation (prefer max_new_tokens for causal LMs)
generator = pipeline("text-generation", model="Qwen/Qwen2.5-1.5B")
result = generator("The future of AI is", max_new_tokens=50)

# Text classification
classifier = pipeline("text-classification", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
result = classifier("This movie was excellent!")

# Generative question answering: verify responses against the supplied context.
qa = pipeline("text-generation", model="Qwen/Qwen2.5-0.5B-Instruct")
result = qa([{ "role": "user", "content": "Context: AI means artificial intelligence. What does AI mean?" }], max_new_tokens=32, do_sample=False)
```

## Core Capabilities

### 1. Pipelines for Quick Inference

Use for simple, optimized inference across many tasks. Supports text generation, classification, NER, image classification, object detection, audio classification, and more. In v5, `question-answering`, `summarization`, `translation*`, `text2text-generation`, `image-to-text`, and `visual-question-answering` pipelines are removed. Use direct task models when exact extractive/seq2seq semantics are needed; generative text/VLM pipelines are different tasks, not equivalent replacements.

**When to use**: Quick prototyping, simple inference tasks, no custom preprocessing needed.

See `references/pipelines.md` for comprehensive task coverage and optimization.

### 2. Model Loading and Management

Load pre-trained models with fine-grained control over configuration, device placement, and precision.

**When to use**: Custom model initialization, advanced device management, model inspection.

See `references/models.md` for loading patterns and best practices.

### 3. Text Generation

Generate text with LLMs using various decoding strategies (greedy, beam search, sampling) and control parameters (temperature, top-k, top-p).

**When to use**: Creative text generation, code generation, conversational AI, text completion.

For chat or instruction-tuned checkpoints, format messages with that checkpoint's `tokenizer.apply_chat_template` rather than hand-written role delimiters. Prefer `tokenize=True`; if formatting with `tokenize=False` and tokenizing afterward, set `add_special_tokens=False` to avoid d

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

