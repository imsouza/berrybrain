---
id: sciref-dask-schedulers
name: "Scientific Ref: Dask Schedulers"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dask): Dask Schedulers"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dask schedulers"
keywords:
  - "dask"
  - "schedulers"
  - "specialized"
  - "scientific"
  - "reference"
---

# Dask Schedulers

Reviewed with Dask/distributed 2026.8.0. File paths, deployment settings, and undefined application functions are illustrative; executed local checks and current official sources are in [review.md](review.md).

## Overview

Dask provides multiple task schedulers, each suited to different workloads. The scheduler determines how tasks are executed: sequentially, in parallel threads, in parallel processes, or distributed across a cluster.

## Scheduler Types

In scripts, guard process scheduler execution and local process-cluster creation with `if __name__ == "__main__":`. Array/DataFrame defaults below apply when no active distributed client or explicit configuration overrides them. Close both client and any separately created cluster when finished.

### Single-Machine Schedulers

#### 1. Local Threads (Default)

**Description**: The threaded scheduler executes computations with a local `concurrent.futures.ThreadPoolExecutor`.

**When to Use**:
- Numeric computations in NumPy, Pandas, scikit-learn
- Libraries that release the GIL (Global Interpreter Lock)
- Operations benefit from shared memory access
- Default for Dask Arrays and DataFrames

**Characteristics**:
- Low overhead
- Shared memory between threads
- Best for GIL-releasing operations
- Poor for pure Python code (GIL contention)

**Example**:
```python
import dask.array as da

# Uses threads by default
x = da.random.random((10000, 10000), chunks=(1000, 1000))
result = x.mean().compute()  # Computed with threads
```

**Explicit Configuration**:
```python
import dask

# Set globally
dask.config.set(scheduler='threads')

# Or per-compute
result = x.mean().compute(scheduler='threads')
```

#### 2. Local Processes

**Description**: Multiprocessing scheduler that uses `concurrent.futures.ProcessPoolExecutor`.

**When to Use**:
- Pure Python code with GIL contention
- Text processing and Python collections
- Operations that benefit from process isolation
- CPU-bound Python code

**Characteristics**:
- Bypasses GIL limitations
- Incurs data transfer costs between processes
- Higher overhead than threads
- Ideal for linear workflows with small inputs/outputs

**Example**:
```python
import dask.bag as db

# Good for Python object processing
bag = db.read_text('data/*.txt')
result = bag.map(complex_python_function).compute(scheduler='processes')
```

**Explicit Configuration**:
```python
import dask

# Set globally
dask.config.set(scheduler='processes')

# Or per-compute
result = computation.compute(scheduler='processes')
```

**Limitations**:
- Data must be serializable (pickle)
- Overhead from process creation
- Memory overhead from data copying

#### 3. Single Thread (Synchronous)

**Description**: The single-threaded synchronous scheduler executes all computations in the local thread with no parallelism at all.

**When to Use**:
- Debugging with pdb
- Profiling with standard Python tools
- Understanding errors in detail
- Development and testing

**Characteristics**:
- No parallelism
- Easy debugging
- Low scheduler overhead
- Serial execution; random functions and side effects still need reproducibility controls

**Example**:
```python
import dask

# Enable for debugging
dask.config.set(scheduler='synchronous')

# Now can use pdb
result = computation.compute()  # Runs in single thread
```

**Debugging with IPython**:
```python
# In IPython/Jupyter
%pdb on

dask.config.set(scheduler='synchronous')
result = problematic_computation.compute()  # Drops into debugger on error
```

### Distributed Schedulers

#### 4. Local Distributed

**Description**: Despite its name, this scheduler runs effectively on personal machines using the distributed scheduler infrastructure.

**When to Use**:
- Need diagnostic dashboard
- Asynchronous APIs
- Better data locality handling than multiprocessing
- Development before scaling to cluster
- Want distributed features on single machine

**Characteristics**:
- Provides dashboard for monitoring
- Better memory management
- More overhead than threads/processes
- Can scale to cluster later

**Example**:
```python
from dask.distributed import Client
import dask.dataframe as dd

# Create local cluster
client = Client(n_workers=2, threads_per_worker=2)  # Explicit resource budget

# Use distributed scheduler
ddf = dd.read_csv('data.csv')
result = ddf.groupby('category')['value'].mean().compute()

# View dashboard
print(client.dashboard_link)

# Clean up
client.close()
```

**Configuration Options**:
```python
# Control resources
client = Client(
    n_workers=4,
    threads_per_worker=2,
    memory_limit='4GB'
)
```

#### 5. Cluster Distributed

**Description**: For scaling across multiple machines using the distributed scheduler.

**When to Use**:
- Data exceeds single machine capacity
- Need computational power beyond one machine
- Production deployments
- Cluster computing environments (HPC, cloud)

**Characteristics**:
- Scales to hundreds of machines
- Requires cluster setup
- Network communication overhead
- Advanced features (adaptive scaling, task prioritization)

**Example with Dask-Jobqueue (HPC)**:
```python
from dask_jobqueue import SLURMCluster
from dask.distributed import Client

# Create cluster on HPC with SLURM
cluster = SLURMCluster(
    cores=24,
    memory='100GB',
    walltime='02:00:00',
    queue='regular'
)

# Scale to 10 jobs
cluster.scale(jobs=10)

# Connect client
client = Client(cluster)

# Run computation
result = computation.compute()

client.close()
cluster.close()  # Release the jobs owned by this cluster
```

**Example with Dask on Kubernetes**:
```python
from dask_kubernetes.operator import KubeCluster
from dask.distributed import Client

# Illustrative: requires installed Dask Operator/CRDs and authorized kubeconfig.
# Use an image with matching dask/distributed and workload dependencies.
cluster = KubeCluster(name='research-dask', image=validated_worker_image)
cluster.scale(20)  # 20 workers

client = Client(cluster)
result = computation.compute()

client.close()
cluster.close()
```

Both deployment recipes require site-specific configuration and were not deployed in this review.

## Scheduler Configuration

### Global Configuration

```python
import dask

# Set scheduler globally for session
dask.config.set(scheduler='threads')
dask.config.set(scheduler='processes')
dask.config.set(scheduler='synchronous')
```

### Context Manager

```python
import dask

# Temporarily use different scheduler
with dask.config.set(scheduler='processes'):
    result = c

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

