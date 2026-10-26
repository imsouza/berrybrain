---
id: sciref-transformers-training
name: "Scientific Ref: Training and Fine-Tuning"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (transformers): Training and Fine-Tuning"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "transformers training"
  - "training and fine-tuning"
keywords:
  - "transformers"
  - "training"
  - "specialized"
  - "scientific"
  - "reference"
  - "fine"
---

# Training and Fine-Tuning

Targets Transformers 5.18.0 / Datasets 5.0.1 / Accelerate 1.15.0 / PEFT 0.21.2. Tiny CPU training, evaluation, checkpoint resume, collators, and LoRA are tested locally; Hub dataset/model downloads, distributed runs, trackers, and hyperparameter services are illustrative. See [review evidence](review.md).

## Overview

Fine-tune pre-trained models on custom datasets using the Trainer API. The Trainer handles training loops, gradient accumulation, mixed precision, logging, and checkpointing.

**Metrics:** `datasets.load_metric` is removed. Compute simple metrics locally; optional `evaluate.load("accuracy")` loads an external metric implementation, requires the Evaluate package/network or cache, and should be reviewed/pinned for reproducibility.

**Hub uploads:** `trainer.push_to_hub()` requires authentication (`hf auth login` or `HF_TOKEN`).

## Basic Fine-Tuning Workflow

### Step 1: Load and Preprocess Data

```python
from datasets import load_dataset

# Load dataset
dataset = load_dataset("Yelp/yelp_review_full")
# Tune only on a validation partition of training data, keeping test untouched.
split = dataset["train"].train_test_split(test_size=0.1, seed=42, stratify_by_column="label")
train_dataset = split["train"]
eval_dataset = split["test"]
test_dataset = dataset["test"]

# Tokenize
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-uncased")

def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=512
    )

train_dataset = train_dataset.map(tokenize_function, batched=True)
eval_dataset = eval_dataset.map(tokenize_function, batched=True)
```

### Step 2: Load Model

```python
from transformers import AutoModelForSequenceClassification

model = AutoModelForSequenceClassification.from_pretrained(
    "google-bert/bert-base-uncased",
    num_labels=5  # Number of classes
)
```

### Step 3: Define Metrics

```python
import numpy as np

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return {"accuracy": float(np.mean(predictions == labels))}
```

### Step 4: Configure Training

```python
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./results",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
    report_to="none",  # Opt in to external trackers explicitly.
    logging_steps=10,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
)
```

### Step 5: Create Trainer and Train

```python
from transformers import Trainer, DataCollatorWithPadding

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    compute_metrics=compute_metrics,
    processing_class=tokenizer,
    data_collator=DataCollatorWithPadding(tokenizer),
)

# Start training
trainer.train()

# Evaluate
results = trainer.evaluate()
print(results)
```

### Step 6: Save Model

```python
trainer.save_model("./fine_tuned_model")
tokenizer.save_pretrained("./fine_tuned_model")

# Optional external upload, only when intended:
# Set hub_model_id="username/my-finetuned-model" in TrainingArguments first.
# trainer.push_to_hub(commit_message="Upload fine-tuned model")
```

## TrainingArguments Parameters

### Essential Parameters

**output_dir**: Directory for checkpoints and logs
```python
output_dir="./results"
```

**num_train_epochs**: Number of training epochs
```python
num_train_epochs=3
```

**per_device_train_batch_size**: Batch size per GPU/CPU
```python
per_device_train_batch_size=8
```

**learning_rate**: Optimizer learning rate
```python
learning_rate=2e-5  # Common for BERT-style models
learning_rate=5e-5  # Common for smaller models
```

**weight_decay**: Optimizer weight decay (AdamW decouples this from the gradient; it is not generally equivalent to adding an L2 loss penalty)
```python
weight_decay=0.01
```

### Evaluation and Saving

**eval_strategy**: When to evaluate ("no", "steps", "epoch")
```python
eval_strategy="epoch"  # Evaluate after each epoch
eval_strategy="steps"  # Evaluate every eval_steps
```

**save_strategy**: When to save checkpoints
```python
save_strategy="epoch"
save_strategy="steps"
save_steps=500
```

**load_best_model_at_end**: Load best checkpoint after training
```python
load_best_model_at_end=True
metric_for_best_model="accuracy"  # Metric to compare
```

### Optimization

**gradient_accumulation_steps**: Accumulate gradients over multiple steps
```python
gradient_accumulation_steps=4  # Effective batch = per-device batch * accumulation * data-parallel workers (except partial final groups)
```

**fp16**: Enable mixed precision (NVIDIA GPUs without native bfloat16)
```python
fp16=True
```

**bf16**: Enable bfloat16 (preferred on Ampere+ and newer GPUs when supported)
```python
bf16=True
```

**gradient_checkpointing**: Trade compute for memory
```python
gradient_checkpointing=True  # Slower but uses less memory
```

**optim**: Optimizer choice
```python
optim="adamw_torch"  # Explicit portable choice; current Torch>=2.8 default is adamw_torch_fused
optim="adamw_8bit"    # 8-bit Adam (requires bitsandbytes)
optim="adafactor"     # Memory-efficient alternative
```

### Learning Rate Scheduling

**lr_scheduler_type**: Learning rate schedule
```python
lr_scheduler_type="linear"       # Linear decay
lr_scheduler_type="cosine"       # Cosine annealing
lr_scheduler_type="constant"     # No decay
lr_scheduler_type="constant_with_warmup"
```

**warmup_steps**: Integer step count or fractional ratio in [0, 1). `warmup_ratio` was removed in v5.
```python
warmup_steps=500
# Or
warmup_steps=0.1  # 10% of total steps
```

### Logging

**TensorBoard directory**: `logging_dir` was removed from TrainingArguments. Set `TENSORBOARD_LOGGING_DIR=./logs` in the environment before creating Trainer and install TensorBoard if using it.

**logging_steps**: Log every N steps
```python
logging_steps=10
```

**report_to**: Logging integrations
```python
report_to="none"  # Local-only default used here
report_to=["tensorboard"]
report_to=["wandb"]
report_to=["tensorboard", "wandb"]
```

### Distributed Training

**ddp_backend**: Distributed backend
```python
ddp_backend="nccl"  # For multi-GPU
```

**deepspeed**: DeepSpeed confi

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

