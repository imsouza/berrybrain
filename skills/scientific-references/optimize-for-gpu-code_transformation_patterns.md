---
id: sciref-optimize-for-gpu-code-transformation-patterns
name: "Scientific Ref: Code Transformation Patterns"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): Code Transformation Patterns"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu code transformation patterns"
  - "optimize gpu codigo transformation patterns"
  - "code transformation patterns"
keywords:
  - "optimize"
  - "gpu"
  - "code"
  - "transformation"
  - "patterns"
  - "codigo"
  - "specialized"
  - "scientific"
  - "reference"
---

# Code Transformation Patterns

Before/after conversions: NumPy to CuPy, pandas to cuDF, a custom loop to a Numba CUDA
kernel, NetworkX to cuGraph, scikit-learn to cuML, a simulation loop to a Warp kernel,
file IO to KvikIO, maintained GPU-backed dashboards, scikit-image to cuCIM, legacy
GeoPandas-to-cuSpatial point-in-polygon, exact Faiss to exact cuVS search, and
`scipy.sparse.linalg` to RAFT.

These are illustrative patterns, not executed GPU benchmarks. Reuse the same inputs and
validate outputs before timing; independently generated CPU/GPU random arrays are not
a correctness comparison. Installation targets and hardware limits are in `installation.md`.

When converting existing CPU code, apply these patterns:

### NumPy to CuPy
```python
# Before (CPU)
import numpy as np
a = np.random.rand(10_000_000)
b = np.fft.fft(a)
c = np.sort(b.real)

# After (GPU) — often just change the import
import cupy as cp
a = cp.random.rand(10_000_000)
b = cp.fft.fft(a)
c = cp.sort(b.real)
```

### pandas to cuDF
```python
# Before (CPU)
import pandas as pd
df = pd.read_parquet("large_data.parquet")
result = df.groupby("category")["value"].mean()

# After (GPU) — change the import
import cudf
df = cudf.read_parquet("large_data.parquet")
result = df.groupby("category")["value"].mean()

# Or zero-code-change: python -m cudf.pandas your_script.py
```

### Custom loop to Numba CUDA kernel
```python
# Before (CPU) — slow Python loop
def process(data, out):
    for i in range(len(data)):
        out[i] = math.sin(data[i]) * math.exp(-data[i])

# After (GPU) — Numba kernel
from numba import cuda
import math

@cuda.jit
def process(data, out):
    i = cuda.grid(1)
    if i < data.size:
        out[i] = math.sin(data[i]) * math.exp(-data[i])

d_data = cuda.to_device(data)
d_out = cuda.device_array(d_data.shape, dtype=d_data.dtype)
threads = 256
blocks = (len(data) + threads - 1) // threads
process[blocks, threads](d_data, d_out)
out = d_out.copy_to_host()
```

### NetworkX to cuGraph
```python
# Before (CPU)
import networkx as nx
G = nx.read_edgelist("edges.csv", delimiter=",", nodetype=int)
pr = nx.pagerank(G)
bc = nx.betweenness_centrality(G)

# After (GPU) — direct cuGraph API
import cugraph
import cudf
edges = cudf.read_csv("edges.csv", names=["src", "dst"], dtype=["int32", "int32"])
G = cugraph.Graph()
G.from_cudf_edgelist(edges, source="src", destination="dst")
pr = cugraph.pagerank(G)
bc = cugraph.betweenness_centrality(G)

# Or zero-code-change: NX_CUGRAPH_AUTOCONFIG=True python your_script.py
```

### scikit-learn to cuML
```python
# Before (CPU)
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# After (GPU) — match parameters and held-out quality; algorithms need not be identical
from cuml.ensemble import RandomForestClassifier
from cuml.preprocessing import StandardScaler
from cuml.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Or zero-code-change: python -m cuml.accel your_script.py
```

### Simulation loop to Warp kernel
```python
# Before (CPU) — slow Python loop over particles
import numpy as np

def integrate(positions, velocities, forces, dt):
    for i in range(len(positions)):
        velocities[i] += forces[i] * dt  # Unit mass, or forces stores accelerations
        positions[i] += velocities[i] * dt

# After (GPU) — Warp kernel, JIT-compiled to CUDA
import warp as wp

@wp.kernel
def integrate(positions: wp.array(dtype=wp.vec3),
              velocities: wp.array(dtype=wp.vec3),
              forces: wp.array(dtype=wp.vec3),
              dt: float):
    tid = wp.tid()
    velocities[tid] = velocities[tid] + forces[tid] * dt
    positions[tid] = positions[tid] + velocities[tid] * dt

wp.launch(integrate, dim=num_particles,
          inputs=[positions, velocities, forces, 0.01], device="cuda")
```

### File IO to GPU with KvikIO
```python
# Before — CPU staging (disk → CPU → GPU)
import numpy as np
import cupy as cp

data = np.fromfile("data.bin", dtype=np.float32)
gpu_data = cp.asarray(data)  # Extra copy through CPU memory

# After — device destination (local GDS only when configured and eligible)
import cupy as cp
import kvikio

gpu_data = cp.empty(1_000_000, dtype=cp.float32)
with kvikio.CuFile("data.bin", "r") as f:
    f.read(gpu_data)  # May use host staging in compatibility mode

# Reading from S3 directly to GPU
with kvikio.RemoteFile.open_s3_url("s3://bucket/data.bin") as f:
    buf = cp.empty(f.nbytes() // 4, dtype=cp.float32)
    f.read(buf)
```

### GPU-backed dashboard with maintained libraries

cuxfilter ended with RAPIDS 26.06. Do not start a new application with it. Keep large
transformations and aggregations in cuDF, then transfer only the compact display data at an
explicit visualization boundary:

```python
# Before — static matplotlib/seaborn plots, no interactivity
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_parquet("large_dataset.parquet")
fig, axes = plt.subplots(1, 2)
df.plot.scatter(x="feature1", y="feature2", ax=axes[0])
df["category"].value_counts().plot.bar(ax=axes[1])
plt.show()

# After — GPU data preparation plus a maintained dashboard stack
import cudf
import hvplot.pandas  # Registers .hvplot on pandas objects
import panel as pn

gpu_df = cudf.read_parquet("large_dataset.parquet")
gpu_summary = (
    gpu_df.groupby("category", as_index=False)
    .agg({"value_col": "mean"})
)
display_summary = gpu_summary.to_pandas()  # Transfer only the reduced result
dashboard = pn.Column(
    "# Interactive Explorer",
    display_summary.hvplot.bar(x="category", y="value_col"),
)
dashboard.servable()
```

For linked selections over detailed points, use HoloViews/hvPlot with Datashader and Panel.
Keep filter/aggregation callbacks on the GPU where practical, and document every conversion to
pandas. Read the cuxfilter reference only when maintaining an existing 26.06 application.

### scikit-image to cuCIM
```python
# Before (CPU)
from skimage.filters import gaussian, sobel, threshold_otsu
from skimage.morphology impor

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

