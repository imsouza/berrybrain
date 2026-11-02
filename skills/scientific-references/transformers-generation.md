---
id: sciref-transformers-generation
name: "Scientific Ref: Text Generation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (transformers): Text Generation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "transformers generation"
  - "text generation"
keywords:
  - "transformers"
  - "generation"
  - "specialized"
  - "scientific"
  - "reference"
  - "text"
---

# Text Generation

Targets Transformers 5.18.0. Hub examples are illustrative; greedy, sampling, beam search, chat dictionaries, streaming, and static cache are tested with tiny local models. See [review evidence](review.md).

## Overview

Generate text with language models using the `generate()` method. Control output quality and style through generation strategies and parameters.

For quick prototyping, the [Pipeline API](pipelines.md) wraps tokenization and `generate()`; use `model.generate()` directly when you need custom preprocessing or decoding control.

## Basic Generation

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("openai-community/gpt2")
tokenizer = AutoTokenizer.from_pretrained("openai-community/gpt2")

# Tokenize input
inputs = tokenizer("Once upon a time", return_tensors="pt").to(model.device)

# Generate
outputs = model.generate(**inputs, max_new_tokens=50)

# Decode
text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(text)
```

## Generation Strategies

### Greedy Decoding

Select highest probability token at each step (deterministic):

```python
outputs = model.generate(
    **inputs,
    max_new_tokens=50,
    do_sample=False,  # Explicitly override any checkpoint sampling default
    num_beams=1
)
```

**Use for**: A non-sampling baseline. Greedy decoding does not make content factual, and exact reproducibility also depends on kernels, hardware, versions, and seeds.

### Sampling

Randomly sample from probability distribution:

```python
outputs = model.generate(
    **inputs,
    max_new_tokens=50,
    do_sample=True,
    temperature=0.7,
    top_k=50,
    top_p=0.95
)
```

**Use for**: Creative writing, diverse outputs, open-ended generation.

### Beam Search

Explore multiple hypotheses in parallel:

```python
outputs = model.generate(
    **inputs,
    max_new_tokens=50,
    num_beams=5,
    do_sample=False,
    early_stopping=True
)
```

**Use for**: Comparing candidate seq2seq translations or summaries. More beams do not guarantee better factuality or task quality.

### Former built-in decoding strategies

Contrastive and constrained beam search moved to Hub custom-generation repositories. Legacy `penalty_alpha` / `force_words_ids` settings are not a self-contained offline implementation. Prefer the built-in greedy/sampling/beam paths unless you intentionally review the external implementation and dependencies, pin its code revision, and authorize custom code. See the [current generation strategy guide](https://huggingface.co/docs/transformers/en/generation_strategies); this skill does not execute Hub custom-generation code.

## Key Parameters

### Length Control

**max_new_tokens**: Maximum tokens to generate
```python
max_new_tokens=100  # Generate up to 100 new tokens
```

**max_length**: Total decoder sequence length (prompt + output for decoder-only models; decoder-side length for encoder-decoder models). `max_new_tokens` takes precedence.
```python
max_length=512  # Total sequence length
```

**min_new_tokens**: Minimum tokens to generate
```python
min_new_tokens=50  # Force at least 50 tokens
```

**min_length**: Minimum total length
```python
min_length=100
```

### Temperature

Controls randomness (only with sampling):

```python
temperature=1.0   # Default, balanced
temperature=0.7   # More focused, less random
temperature=1.5   # More creative, more random
```

Lower temperature → more deterministic
Higher temperature → more random

### Top-K Sampling

Consider only top K most likely tokens:

```python
do_sample=True
top_k=50  # Sample from top 50 tokens
```

**Common values**: 40-100 for balanced output, 10-20 for focused output.

### Top-P (Nucleus) Sampling

Consider tokens with cumulative probability ≥ P:

```python
do_sample=True
top_p=0.95  # Sample from smallest set with 95% cumulative probability
```

**Common values**: 0.9-0.95 for balanced, 0.7-0.85 for focused.

### Repetition Penalty

Discourage repetition:

```python
repetition_penalty=1.2  # Penalize repeated tokens
```

**Values**: 1.0 = no penalty, 1.2-1.5 = moderate, 2.0+ = strong penalty.

### Beam Search Parameters

**num_beams**: Number of beams
```python
num_beams=5  # Keep 5 hypotheses
```

**early_stopping**: Stop when num_beams sentences are finished
```python
early_stopping=True
```

**no_repeat_ngram_size**: Prevent n-gram repetition
```python
no_repeat_ngram_size=3  # Don't repeat any 3-gram
```

### Output Control

**num_return_sequences**: Generate multiple outputs
```python
outputs = model.generate(
    **inputs,
    max_new_tokens=50,
    num_beams=5,
    do_sample=False,
    num_return_sequences=3  # Must not exceed num_beams here; uniqueness is not guaranteed
)
```

**pad_token_id**: Specify padding token
```python
pad_token_id=tokenizer.eos_token_id
```

**eos_token_id**: Stop generation at specific token
```python
eos_token_id=tokenizer.eos_token_id
```

## Advanced Features

### Batch Generation

Generate for multiple prompts:

```python
prompts = ["Hello, my name is", "Once upon a time"]
# Decoder-only batch generation uses left padding; this is not a training rule.
tokenizer.padding_side = "left"
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
inputs = tokenizer(prompts, return_tensors="pt", padding=True).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=50, pad_token_id=tokenizer.pad_token_id)

for i, output in enumerate(outputs):
    text = tokenizer.decode(output[inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    print(f"Prompt {i}: {text}\n")
```

### Streaming Generation

`TextStreamer` writes decoded chunks synchronously:

```python
from transformers import TextStreamer

streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
outputs = model.generate(**inputs, streamer=streamer, max_new_tokens=32, num_beams=1)
```

For UI iteration, `TextIteratorStreamer(tokenizer, timeout=30.0, skip_prompt=True)` is consumed concurrently with `generate()` in a worker thread. A timeout raises `queue.Empty`; capture and propagate the worker exception, join/clean up the worker, and do not treat timeout as a completed answer. Streamers do not support beam search. Chunk boundaries are not guaranteed to equal token boundaries.

### Guidance and Control

**Prevent bad words:**
```python
bad_words = ["offensive", "inappropriate"]
bad_words_ids = [tokenizer.encode(word, add_special_tokens=False) for word 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

