---
id: sciref-dask-futures
name: "Scientific Ref: Dask Futures"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dask): Dask Futures"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dask futures"
keywords:
  - "dask"
  - "futures"
  - "specialized"
  - "scientific"
  - "reference"
---

# Dask Futures

Reviewed with Dask/distributed 2026.8.0. File paths, deployment settings, and undefined application functions are illustrative; executed local checks and current official sources are in [review.md](review.md).

## Overview

Dask futures extend Python's `concurrent.futures` interface, enabling immediate (non-lazy) task execution. Unlike delayed computations (used in DataFrames, Arrays, and Bags), futures provide more flexibility in situations where computations may evolve over time or require dynamic workflow construction.

## Core Concept

Futures represent real-time task execution:
- Tasks are scheduled immediately when submitted; execution waits for dependencies and resources
- Each future represents a remote computation result
- Automatic dependency tracking between futures
- Enables dynamic, evolving workflows
- Direct control over task scheduling and data placement

## Key Capabilities

### Real-Time Execution
- Submission schedules work without a separate compute call
- No need for explicit `.compute()` call
- Get results with `.result()` method

### Automatic Dependency Management
When you submit tasks with future inputs, Dask automatically handles dependency tracking. Once all input futures have completed, they will be moved onto a single worker for efficient computation.

### Dynamic Workflows
Build computations that evolve based on intermediate results:
- Submit new tasks based on previous results
- Conditional execution paths
- Iterative algorithms with varying structure

## When to Use Futures

**Use Futures When**:
- Building dynamic, evolving workflows
- Need immediate task execution (not lazy)
- Computations depend on runtime conditions
- Require fine control over task placement
- Implementing custom parallel algorithms
- Need stateful computations (with actors)

**Use Other Collections When**:
- Static, predefined computation graphs (use delayed, DataFrames, Arrays)
- Simple data parallelism on large collections (use Bags, DataFrames)
- Standard array/dataframe operations suffice

## Setting Up Client

Futures require a distributed client:

```python
from dask.distributed import Client

# Local cluster (on single machine)
client = Client()

# Or specify resources
client = Client(n_workers=4, threads_per_worker=2)

# Or connect to existing cluster
client = Client('scheduler-address:8786')
```

## Submitting Tasks

### Basic Submit
```python
from dask.distributed import Client

client = Client()

# Submit single task
def add(x, y):
    return x + y

future = client.submit(add, 1, 2)

# Get result
result = future.result()  # Blocks until complete
print(result)  # 3
```

### Multiple Tasks
```python
# Submit multiple independent tasks
futures = []
for i in range(10):
    future = client.submit(add, i, i)
    futures.append(future)

# Gather results
results = client.gather(futures)  # Efficient parallel gathering
```

### Map Over Inputs
```python
# Apply function to multiple inputs
def square(x):
    return x ** 2

# Submit batch of tasks
futures = client.map(square, range(100))

# Gather results
results = client.gather(futures)
```

**Note**: Each task carries ~1ms overhead, making `map` less suitable for millions of tiny tasks. For massive datasets, use Bags or DataFrames instead.

## Working with Futures

### Check Status
```python
future = client.submit(expensive_function, arg)

# Check if complete
print(future.done())  # False or True

# Check status
print(future.status)  # e.g. pending, finished, error, cancelled, or lost
# Use client.processing() for tasks executing on workers.
```

### Non-Blocking Result Retrieval
```python
# Non-blocking check
if future.done():
    result = future.result()
else:
    print("Still computing...")

# Or use callbacks
def handle_result(future):
    print(f"Result: {future.result()}")

future.add_done_callback(handle_result)
```

### Error Handling
```python
def might_fail(x):
    if x < 0:
        raise ValueError("Negative value")
    return x ** 2

future = client.submit(might_fail, -5)

try:
    result = future.result()
except ValueError as e:
    print(f"Task failed: {e}")
```

## Task Dependencies

### Automatic Dependency Tracking
```python
# Submit task
future1 = client.submit(add, 1, 2)

# Use future as input (creates dependency)
future2 = client.submit(add, future1, 10)  # Depends on future1

# Chain dependencies
future3 = client.submit(add, future2, 100)  # Depends on future2

# Get final result
result = future3.result()  # 113
```

### Complex Dependencies
```python
# Multiple dependencies
a = client.submit(func1, x)
b = client.submit(func2, y)
c = client.submit(func3, a, b)  # Depends on both a and b

result = c.result()
```

## Data Movement Optimization

### Scatter Data
Pre-scatter important data to avoid repeated transfers:

```python
# Upload data to cluster once
[large_dataset] = client.scatter([big_data])  # One future, even for a list/dict

# Use scattered data in multiple tasks
futures = [client.submit(process, large_dataset, i) for i in range(100)]

# Dask transfers dependencies to workers that need them; scatter is not zero-copy.
results = client.gather(futures)
```

### Efficient Gathering
Use `client.gather()` for concurrent result collection:

```python
# Better: Gather all at once (parallel)
results = client.gather(futures)

# Worse: Sequential result retrieval
results = [f.result() for f in futures]
```

## Fire-and-Forget

For side-effect tasks without needing the result:

```python
from dask.distributed import fire_and_forget

def log_to_database(data):
    # Write to database, no return value needed
    database.write(data)

# Submit without keeping reference
future = client.submit(log_to_database, data, pure=False)
fire_and_forget(future)

# Retains interest after this Future is released; this is not exactly-once delivery.
# External writes must be idempotent because tasks can be re-executed.
```

## Performance Characteristics

### Task Overhead
- ~1ms overhead per task
- Good for: Thousands of tasks
- Not suitable for: Millions of tiny tasks

### Worker-to-Worker Communication
- Direct worker-to-worker data transfer
- Roundtrip latency depends on hardware, serialization, and network
- Efficient for task dependencies

### Memory Management
Dask tracks active futures locally. When a future is garbage collected by your local Python session, Dask will feel free to delete that data.

**Keep References**:
```python
# Keep reference to prevent deletion
important_result = client.submit(

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

