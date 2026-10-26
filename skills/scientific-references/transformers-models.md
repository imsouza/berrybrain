---
id: sciref-transformers-models
name: "Scientific Ref: Model Loading and Management"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (transformers): Model Loading and Management"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "transformers models"
  - "model loading and management"
keywords:
  - "transformers"
  - "models"
  - "specialized"
  - "scientific"
  - "reference"
  - "model"
  - "loading"
---

# Model Loading and Management

Targets Transformers 5.18.0. Hub/accelerator/export examples are illustrative; tiny local model APIs are exercised by `tests/transformers/`. See [review evidence](review.md).

## Overview

The transformers library provides flexible model loading with automatic architecture detection, device management, and configuration control.

## Loading Models

### AutoModel Classes

Use AutoModel classes for automatic architecture selection:

```python
from transformers import AutoModel, AutoModelForSequenceClassification, AutoModelForCausalLM

# Base model (no task head)
model = AutoModel.from_pretrained("google-bert/bert-base-uncased")

# Sequence classification
model = AutoModelForSequenceClassification.from_pretrained("distilbert/distilbert-base-uncased")

# Causal language modeling (GPT-style)
model = AutoModelForCausalLM.from_pretrained("openai-community/gpt2")

# Masked language modeling (BERT-style)
from transformers import AutoModelForMaskedLM
model = AutoModelForMaskedLM.from_pretrained("google-bert/bert-base-uncased")

# Sequence-to-sequence (T5-style)
from transformers import AutoModelForSeq2SeqLM
model = AutoModelForSeq2SeqLM.from_pretrained("google-t5/t5-small")
```

### Common AutoModel Classes

**NLP Tasks:**
- `AutoModelForSequenceClassification`: Text classification, sentiment analysis
- `AutoModelForTokenClassification`: NER, POS tagging
- `AutoModelForQuestionAnswering`: Extractive QA
- `AutoModelForCausalLM`: Text generation (GPT, Llama)
- `AutoModelForMaskedLM`: Masked language modeling (BERT)
- `AutoModelForSeq2SeqLM`: Translation, summarization (T5, BART)

**Vision Tasks:**
- `AutoModelForImageClassification`: Image classification
- `AutoModelForObjectDetection`: Object detection
- `AutoModelForImageSegmentation`: Image segmentation

**Audio Tasks:**
- `AutoModelForAudioClassification`: Audio classification
- `AutoModelForSpeechSeq2Seq`: Speech recognition

**Multimodal:**
- `AutoModelForImageTextToText`: Generative image captioning and visual chat, paired with `AutoProcessor`
- `AutoModelForVisualQuestionAnswering`: Architecture-specific direct VQA models

## Loading Parameters

### Basic Parameters

**pretrained_model_name_or_path**: Model identifier or local path
```python
model = AutoModel.from_pretrained("google-bert/bert-base-uncased")  # From Hub
model = AutoModel.from_pretrained("./local/model/path")  # From disk
```

**num_labels**: Number of output labels for classification
```python
model = AutoModelForSequenceClassification.from_pretrained(
    "google-bert/bert-base-uncased",
    num_labels=3
)
```

**cache_dir**: Custom cache location
```python
model = AutoModel.from_pretrained("model-id", cache_dir="./my_cache")
```

### Device Management

**device_map**: Automatic device allocation for large models
```python
# Automatically distribute across GPUs and CPU
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B",
    device_map="auto"
)

# Accelerate device maps are for inference, not distributed Trainer training.
# Sequential placement
model = AutoModelForCausalLM.from_pretrained(
    "model-id",
    device_map="sequential"
)

# A complete one-device map; split maps must name real model modules and cover all weights.
model = AutoModel.from_pretrained("model-id", device_map={"": "cpu"})
```

Manual device placement:
```python
import torch
model = AutoModel.from_pretrained("model-id")
model.to("cuda:0")  # Move to GPU 0
model.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
```

### Precision Control

**dtype**: Set model precision (preferred in v5; `torch_dtype` still works but is deprecated)
```python
import torch

# Float16 (half precision)
model = AutoModel.from_pretrained("model-id", dtype=torch.float16)

# BFloat16 (better range than float16)
model = AutoModel.from_pretrained("model-id", dtype=torch.bfloat16)

# Auto (use original dtype)
model = AutoModel.from_pretrained("model-id", dtype="auto")
```

### Attention Implementation

**attn_implementation**: Choose attention mechanism
```python
# SDPA (supported architectures; backend/shape determine speed)
model = AutoModel.from_pretrained("model-id", attn_implementation="sdpa")

# Flash Attention 2 (requires flash-attn package)
model = AutoModel.from_pretrained("model-id", attn_implementation="flash_attention_2")

# Eager (explicit reference implementation; SDPA is often selected by default)
model = AutoModel.from_pretrained("model-id", attn_implementation="eager")
```

### Memory Optimization

Transformers v5 manages efficient loading internally; legacy `low_cpu_mem_usage` is ignored. `device_map="auto"` can dispatch to accelerators/CPU/disk according to available memory; supply `max_memory` and `offload_folder` when needed, inspect `model.hf_device_map`, and keep inputs on the entry device. Do not call `.to(...)` on an already dispatched model.

**BitsAndBytesConfig**: 8-bit and 4-bit quantization (requires optional `bitsandbytes`; `uv pip install bitsandbytes==0.50.2`)
```python
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(load_in_8bit=True)

model = AutoModelForCausalLM.from_pretrained(
    "model-id",
    device_map="auto",
    quantization_config=quantization_config
)
```

Bitsandbytes is not CUDA-only: release 0.50.2 supplies Linux, Windows, and macOS ARM64 wheels, with backend/feature-specific support. CPU quantization was smoke-tested on this review host; CUDA, ROCm, XPU, Gaudi, and MPS paths were not. Check the [release installation matrix](https://huggingface.co/docs/bitsandbytes/v0.50.2/installation). Quantized inference does not itself train adapters.

**4-bit QLoRA-style loading**: use `BitsAndBytesConfig` instead of direct `load_in_4bit` arguments
```python
import torch
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_quant_type="nf4"
)

model = AutoModelForCausalLM.from_pretrained(
    "model-id",
    quantization_config=quantization_config,
    device_map="auto"
)
```

## Model Configuration

### Loading with Custom Config

```python
from transformers import AutoConfig, AutoModel

# Load and modify config
config = AutoConfig.from_pretrained("google-bert/bert-base-uncased")
config.hidden_dropout_prob = 0.2
config.attention_probs_dropout_prob = 0.2

# Initialize model with custom config
model = AutoModel.from_pretrained("google-bert/bert-base-uncased", config=config)
`

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

