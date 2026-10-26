---
id: sciref-transformers-tokenizers
name: "Scientific Ref: Tokenizers"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (transformers): Tokenizers"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "transformers tokenizers"
  - "tokenizers"
keywords:
  - "transformers"
  - "tokenizers"
  - "specialized"
  - "scientific"
  - "reference"
---

# Tokenizers

Targets Transformers 5.18.0. Tokenizer behavior was exercised with a local BERT vocabulary and a local chat template; Hub examples remain illustrative. See [review evidence](review.md).

## Overview

Tokenizers convert text into numerical representations (tokens) that models can process. They handle special tokens, padding, truncation, and attention masks.

## Loading Tokenizers

### AutoTokenizer

Automatically load the correct tokenizer for a model:

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-uncased")
```

Load from local path:
```python
tokenizer = AutoTokenizer.from_pretrained("./local/tokenizer/path")
```

## Basic Tokenization

### Encode Text

```python
# Simple encoding
text = "Hello, how are you?"
tokens = tokenizer.encode(text)
print(tokens)  # [101, 7592, 1010, 2129, 2024, 2017, 1029, 102]

# With text tokenization
tokens = tokenizer.tokenize(text)
print(tokens)  # ['hello', ',', 'how', 'are', 'you', '?']
```

### Decode Tokens

```python
token_ids = [101, 7592, 1010, 2129, 2024, 2017, 1029, 102]
text = tokenizer.decode(token_ids)
print(text)  # Includes [CLS]/[SEP] unless skip_special_tokens=True

# Skip special tokens
text = tokenizer.decode(token_ids, skip_special_tokens=True)
print(text)  # "hello, how are you?"
```

## The `__call__` Method

Primary tokenization interface:

```python
# Single text
inputs = tokenizer("Hello, how are you?")

# Returns BatchEncoding: input_ids, attention_mask, and tokenizer-dependent fields
# (BERT also emits token_type_ids).
print(inputs)
# {
#   'input_ids': [101, 7592, 1010, 2129, 2024, 2017, 1029, 102],
#   'attention_mask': [1, 1, 1, 1, 1, 1, 1, 1]
# }
```

Multiple texts:
```python
texts = ["Hello", "How are you?"]
inputs = tokenizer(texts, padding=True, truncation=True)
```

## Key Parameters

### Return Tensors

**return_tensors**: Output format (`"pt"` for PyTorch, `"np"` for NumPy)
```python
# PyTorch tensors (without return_tensors, the default output is Python lists)
inputs = tokenizer("text", return_tensors="pt")

# NumPy arrays
inputs = tokenizer("text", return_tensors="np")
```

### Padding

**padding**: Pad sequences to same length
```python
# Pad to longest sequence in batch
inputs = tokenizer(texts, padding=True)

# Pad to specific length
inputs = tokenizer(texts, padding="max_length", max_length=128)

# No padding
inputs = tokenizer(texts, padding=False)
```

**pad_to_multiple_of**: Pad to multiple of specified value
```python
inputs = tokenizer(texts, padding=True, pad_to_multiple_of=8)
```

### Truncation

**truncation**: Limit sequence length
```python
# Truncate to max_length
inputs = tokenizer(text, truncation=True, max_length=512)

# Truncate first sequence in pairs
inputs = tokenizer(text1, text2, truncation="only_first")

# Truncate second sequence
inputs = tokenizer(text1, text2, truncation="only_second")

# Truncate longest first (default for pairs)
inputs = tokenizer(text1, text2, truncation="longest_first", max_length=512)
```

### Max Length

**max_length**: Maximum sequence length
```python
inputs = tokenizer(text, max_length=512, truncation=True)
```

### Additional Outputs

**return_attention_mask**: Include attention mask (default True)
```python
inputs = tokenizer(text, return_attention_mask=True)
```

**return_token_type_ids**: Segment IDs for sentence pairs
```python
inputs = tokenizer(text1, text2, return_token_type_ids=True)
```

**return_offsets_mapping**: Character position mapping (Fast tokenizers only)
```python
inputs = tokenizer(text, return_offsets_mapping=True)
```

**return_length**: Include sequence lengths
```python
inputs = tokenizer(texts, padding=True, return_length=True)
```

## Special Tokens

### Predefined Special Tokens

Access special tokens:
```python
print(tokenizer.cls_token)      # [CLS] or <s>
print(tokenizer.sep_token)      # [SEP] or </s>
print(tokenizer.pad_token)      # [PAD]
print(tokenizer.unk_token)      # [UNK]
print(tokenizer.mask_token)     # [MASK]
print(tokenizer.eos_token)      # End of sequence
print(tokenizer.bos_token)      # Beginning of sequence

# Get IDs
print(tokenizer.cls_token_id)
print(tokenizer.sep_token_id)
```

### Add Special Tokens

Manual control:
```python
# Automatically add special tokens (default True)
inputs = tokenizer(text, add_special_tokens=True)

# Skip special tokens
inputs = tokenizer(text, add_special_tokens=False)
```

### Custom Special Tokens

```python
special_tokens_dict = {
    "extra_special_tokens": ["<CUSTOM>", "<SPECIAL>"]
}

num_added = tokenizer.add_special_tokens(special_tokens_dict)
print(f"Added {num_added} tokens")

# Resize model embeddings after adding tokens
model.resize_token_embeddings(len(tokenizer))
```

## Sentence Pairs

Tokenize text pairs:

```python
text1 = "What is the capital of France?"
text2 = "Paris is the capital of France."

# Automatically handles separation
inputs = tokenizer(text1, text2, padding=True, truncation=True)

# Results in: [CLS] text1 [SEP] text2 [SEP]
```

## Batch Encoding

Process multiple texts:

```python
texts = ["First text", "Second text", "Third text"]

# Basic batch encoding
batch = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")

# Access individual encodings
for i in range(len(texts)):
    input_ids = batch["input_ids"][i]
    attention_mask = batch["attention_mask"][i]
```

## Tokenizer Backends

v5 uses one implementation per model backed by `TokenizersBackend`, `SentencePieceBackend`, `PythonBackend`, or `MistralCommonBackend`. `AutoTokenizer` selects based on files/dependencies. In 5.18.0 its old `use_fast` argument is ignored; `use_fast=False` does not force the former Python tokenizer. Inspect `tokenizer.is_fast` before using offset/word alignment, and use the checkpoint's actual backend rather than substituting a tokenizer.

```python
print(type(tokenizer).__name__, tokenizer.is_fast)
```

### Fast Tokenizer Features

**Offset mapping** (character positions):
```python
inputs = tokenizer("Hello world", return_offsets_mapping=True)
print(inputs["offset_mapping"])
# [(0, 0), (0, 5), (6, 11), (0, 0)]  # [CLS], "Hello", "world", [SEP]
```

**Token to word mapping**:
```python
encoding = tokenizer("Hello world")
word_ids = encoding.word_ids()
print(word_ids)  # [None, 0, 1, None]  # [CLS]=None, "Hello"=0, "world"=1, [SEP]=None
```

## Saving Tokenizers

Save locally:
```python
tokenizer.save_pretrained("./my_tokenizer")
```

Push to Hub:
```python
tokenizer

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

