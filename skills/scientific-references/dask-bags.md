---
id: sciref-dask-bags
name: "Scientific Ref: Dask Bags"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dask): Dask Bags"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dask bags"
keywords:
  - "dask"
  - "bags"
  - "specialized"
  - "scientific"
  - "reference"
---

# Dask Bags

Reviewed with Dask/distributed 2026.8.0. File paths, deployment settings, and undefined application functions are illustrative; executed local checks and current official sources are in [review.md](review.md).

## Overview

Dask Bag implements functional operations including `map`, `filter`, `fold`, and `groupby` on generic Python objects. It processes data in parallel while maintaining a small memory footprint through Python iterators. Bags function as "a parallel version of PyToolz or a Pythonic version of the PySpark RDD."

## Core Concept

A Dask Bag is a collection of Python objects distributed across partitions:
- Each partition contains generic Python objects
- Operations use functional programming patterns
- Processing uses streaming/iterators for memory efficiency
- Ideal for unstructured or semi-structured data

## Key Capabilities

### Functional Operations
- `map`: Transform each element
- `filter`: Select elements based on condition
- `fold`: Reduce elements with combining function
- `groupby`: Group elements by key
- `pluck`: Extract fields from records
- `flatten`: Flatten nested structures

### Use Cases
- Text processing and log analysis
- JSON record processing
- ETL on unstructured data
- Data cleaning before structured analysis

## When to Use Dask Bags

**Use Bags When**:
- Working with general Python objects requiring flexible computation
- Data doesn't fit structured array or tabular formats
- Processing text, JSON, or custom Python objects
- Initial data cleaning and ETL is needed
- Memory-efficient streaming is important

**Use Other Collections When**:
- Data is structured (use DataFrames instead)
- Numeric computing (use Arrays instead)
- Operations require complex groupby or shuffles (use DataFrames)

**Key Recommendation**: Use Bag to clean and process data, then transform it into an array or DataFrame before embarking on more complex operations that require shuffle steps.

## Important Limitations

Bags sacrifice performance for generality:
- Default to the processes scheduler when no distributed client/config overrides it; threads are supported
- Remain immutable (create new bags for changes)
- Operate slower than array/DataFrame equivalents
- Handle `groupby` inefficiently (use `foldby` when possible)
- Operations requiring substantial inter-worker communication are slow

## Creating Bags

### From Sequences
```python
import dask.bag as db

# From Python list
bag = db.from_sequence([1, 2, 3, 4, 5], partition_size=2)

# From range
bag = db.from_sequence(range(10000), partition_size=1000)
```

### From Text Files
```python
# Single file
bag = db.read_text('data.txt')

# Multiple files with glob
bag = db.read_text('data/*.txt')

# With encoding
bag = db.read_text('data/*.txt', encoding='utf-8')

# Custom line processing
bag = db.read_text('logs/*.log', blocksize='64MB')
```

### From Delayed Objects
```python
import dask

@dask.delayed
def load_data(filename):
    with open(filename) as f:
        return [line.strip() for line in f]

files = ['file1.txt', 'file2.txt', 'file3.txt']
partitions = [load_data(f) for f in files]
bag = db.from_delayed(partitions)
```

### From Custom Sources
```python
import glob
import json

def read_json_file(filename):
    with open(filename, encoding='utf-8') as f:
        return json.load(f)  # One complete JSON object per file

# Pass only filenames locally; loading occurs in worker tasks.
# from_sequence eagerly materializes an iterable, so do not pass a data loader.
bag = db.from_sequence(sorted(glob.glob('data/*.json')), partition_size=10)
bag = bag.map(read_json_file)
```

## Common Operations

### Map (Transform)
```python
import dask.bag as db

bag = db.read_text('data/*.json')

# Parse JSON
import json
parsed = bag.map(json.loads)

# Extract field
values = parsed.map(lambda x: x['value'])

# Complex transformation
def process_record(record):
    return {
        'id': record['id'],
        'value': record['value'] * 2,
        'category': record.get('category', 'unknown')
    }

processed = parsed.map(process_record)
```

### Filter
```python
# Filter by condition
valid = parsed.filter(lambda x: x['status'] == 'valid')

# Multiple conditions
filtered = parsed.filter(lambda x: x['value'] > 100 and x['year'] == 2024)

# Filter with custom function
def is_valid_record(record):
    return record.get('status') == 'valid' and record.get('value') is not None

valid_records = parsed.filter(is_valid_record)
```

### Pluck (Extract Fields)
```python
# Extract single field
ids = parsed.pluck('id')

# Extract multiple fields (creates tuples)
key_pairs = parsed.pluck(['id', 'value'])
```

### Flatten
```python
# Flatten nested lists
nested = db.from_sequence([[1, 2], [3, 4], [5, 6]])
flat = nested.flatten()  # [1, 2, 3, 4, 5, 6]

# Flatten after map
bag = db.read_text('data/*.txt')
words = bag.map(str.split).flatten()  # All words from all files
```

### GroupBy (Expensive)
```python
# Group by key (requires shuffle)
grouped = parsed.groupby(lambda x: x['category'])

# Aggregate after grouping
counts = grouped.map(lambda key_items: (key_items[0], len(list(key_items[1]))))
result = counts.compute()
```

### FoldBy (Preferred for Aggregations)
```python
# FoldBy is more efficient than groupby for aggregations
def add(acc, item):
    return acc + item['value']

def combine(acc1, acc2):
    return acc1 + acc2

# Sum values by category
sums = parsed.foldby(
    key='category',
    binop=add,
    initial=0,
    combine=combine
)

result = sums.compute()
```

### Reductions
```python
# Count elements
count = bag.count().compute()

# Get all distinct values (requires memory)
distinct = bag.distinct().compute()

# Take first n elements
first_ten = bag.take(10, npartitions=-1)  # Default inspects only first partition

# Fold/reduce
total = bag.fold(
    lambda acc, x: acc + x['value'],
    initial=0,
    combine=lambda a, b: a + b
).compute()
```

## Converting to Other Collections

Supply explicit `meta` when possible: without it `to_dataframe()` computes a sample, can miss rare types, and fails on an empty bag. Validate/cast each record; meta is not a general data-cleaning policy.

### To DataFrame
```python
import dask.bag as db
import dask.dataframe as dd

# Bag of dictionaries
bag = db.read_text('data/*.json').map(json.loads)

# Convert to DataFrame
ddf = bag.to_dataframe()

# With explicit columns
ddf = bag.to_dataframe(meta={'id': int, 'value': float, 'category': str})
```

### To List/Compute
```python
# Compute

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

