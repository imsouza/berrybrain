---
id: sciref-optimize-for-gpu-kvikio
name: "Scientific Ref: KvikIO Reference — High-Performance GPU File IO"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): KvikIO Reference — High-Performance GPU File IO"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu kvikio"
  - "kvikio reference — high-performance gpu file io"
keywords:
  - "optimize"
  - "gpu"
  - "kvikio"
  - "specialized"
  - "scientific"
  - "reference"
---

# KvikIO Reference — High-Performance GPU File IO

> Review: 2026-10-01. Code below is illustrative unless explicitly described as CPU-tested.
> GPU execution, performance, GDS, and multi-GPU behavior require validation on target hardware.

KvikIO is a Python and C++ library for high-performance file IO. It provides bindings to NVIDIA cuFile, enabling GPUDirect Storage (GDS) — eligible local reads and writes between supported storage and GPU memory. When GDS isn't available, KvikIO falls back gracefully to POSIX IO while still handling both host and device data seamlessly.

KvikIO is part of the RAPIDS ecosystem and interoperates with CuPy, cuDF, Numba, and other GPU libraries.

## Table of Contents

1. [Installation](#installation)
2. [When to Use KvikIO](#when-to-use-kvikio)
3. [CuFile — Local File IO](#cufile--local-file-io)
4. [RemoteFile — S3, HTTP, WebHDFS](#remotefile--s3-http-webhdfs)
5. [Zarr Integration](#zarr-integration)
6. [Memory-Mapped Files](#memory-mapped-files)
7. [Runtime Settings](#runtime-settings)
8. [Performance Optimization](#performance-optimization)
9. [Interoperability](#interoperability)
10. [Common Patterns](#common-patterns)
11. [Common Pitfalls](#common-pitfalls)

---

## Installation

```bash
# CUDA 12.x
uv add "kvikio-cu12==26.8.*"

# CUDA 13.x
uv add "kvikio-cu13==26.8.*"

# For Zarr support (optional)
uv add "zarr==3.*"
```

Verify installation:

```python
import kvikio
# Check if GDS is available
import kvikio.cufile_driver
print(kvikio.cufile_driver.get("is_gds_available"))  # True if GDS is set up
```

---

## When to Use KvikIO

Use KvikIO when:
- **Loading large binary data directly to GPU** — avoids the CPU-memory copy that standard `open()` or NumPy's `fromfile()` would require
- **Writing GPU arrays to disk** — saves directly from device memory without copying to host first
- **Reading from remote storage (S3, HTTP, WebHDFS) into GPU memory** — convenient device destinations; libcurl uses host bounce buffers
- **Working with Zarr arrays on GPU** — the GDSStore backend reads chunks directly into CuPy arrays
- **IO is the bottleneck** — compare the actual storage, filesystem, access pattern and GDS eligibility
- **Overlapping IO and compute** — non-blocking reads/writes let you pipeline data loading with GPU computation

KvikIO is a poor fit when:
- Small transfers whose setup costs dominate measured latency
- You're reading structured formats (CSV, Parquet, JSON) — use cuDF instead, which has its own optimized readers
- You only need host memory — standard Python IO is simpler

---

## CuFile — Local File IO

`kvikio.CuFile` is the primary interface for local file IO. It replaces Python's `open()` for GPU workloads.

### Basic Usage

```python
import cupy as cp
import kvikio

# Write a GPU array to disk
a = cp.arange(1_000_000, dtype=cp.float32)
with kvikio.CuFile("data.bin", "w") as f:
    f.write(a)

# Read it back
b = cp.empty(1_000_000, dtype=cp.float32)
with kvikio.CuFile("data.bin", "r") as f:
    f.read(b)

assert cp.all(a == b)
```

### API Methods

| Method | Blocking | Description |
|--------|----------|-------------|
| `read(buf, size, file_offset)` | Yes | Read into device or host buffer |
| `write(buf, size, file_offset)` | Yes | Write from device or host buffer |
| `pread(buf, size, file_offset)` | No | Non-blocking parallel read, returns `IOFuture` |
| `pwrite(buf, size, file_offset)` | No | Non-blocking parallel write, returns `IOFuture` |
| `raw_read(buf, size, file_offset)` | Yes | Low-level single-thread read (device only) |
| `raw_write(buf, size, file_offset)` | Yes | Low-level single-thread write (device only) |
| `raw_read_async(buf, stream, size, file_offset)` | No | CUDA-stream async read (device only) |
| `raw_write_async(buf, stream, size, file_offset)` | No | CUDA-stream async write (device only) |

File modes: `"r"` (read), `"w"` (write/truncate), `"a"` (append), `"+"` (read+write).

### Non-Blocking IO with Futures

`pread` and `pwrite` split the operation into tasks executed in a thread pool and return an `IOFuture`:

```python
import cupy as cp
import kvikio

data = cp.empty(10_000_000, dtype=cp.float32)

with kvikio.CuFile("data.bin", "r") as f:
    # Launch two non-blocking reads for different sections
    future1 = f.pread(data[:5_000_000])
    future2 = f.pread(data[5_000_000:], file_offset=5_000_000 * 4)

    # Do other work while IO happens...

    # Wait for completion
    bytes_read1 = future1.get()
    bytes_read2 = future2.get()
```

### Partial Reads and Writes

```python
import cupy as cp
import kvikio

# Read only a portion of a file
buf = cp.empty(1000, dtype=cp.float32)
with kvikio.CuFile("data.bin", "r") as f:
    # Read 1000 floats starting at byte offset 4000
    f.read(buf, size=4000, file_offset=4000)
```

### Host Memory Support

KvikIO handles host memory transparently — no special API needed:

```python
import numpy as np
import kvikio

# Write from host memory
a = np.arange(1_000_000, dtype=np.float32)
with kvikio.CuFile("data.bin", "w") as f:
    f.write(a)

# Read into host memory
b = np.empty_like(a)
with kvikio.CuFile("data.bin", "r") as f:
    f.read(b)
```

### GDS Alignment

GDS works best with page-aligned IO. The relevant GDS I/O alignment is 4 KiB (4096 bytes); this is not a universal GPU memory-page size:
- **File offset**: should be a multiple of 4096
- **Transfer size**: should be a multiple of 4096

KvikIO handles unaligned IO correctly but splits it into aligned and unaligned parts, so aligned IO will be faster.

---

## RemoteFile — S3, HTTP, WebHDFS

`kvikio.RemoteFile` reads remote files directly into GPU or host memory.

### HTTP/HTTPS

```python
import cupy as cp
import kvikio

buf = cp.empty(1_000_000, dtype=cp.float32)
with kvikio.RemoteFile.open_http("https://example.com/data.bin") as f:
    print(f.nbytes())  # File size
    f.read(buf)
```

### AWS S3

```python
import cupy as cp
import kvikio

# Using bucket + object name (requires AWS env vars or explicit credentials)
with kvikio.RemoteFile.open_s3("my-bucket", "data/file.bin") as f:
    buf = cp.empty(f.nbytes(), dtype=cp.uint8)
    f.read(buf)

# Using S3 URL
with kvikio.RemoteFile.open_s3_url("s3://my-bucket/data/file.bin") as f:
    buf = cp.empty(f.nbytes(), dtype=cp.uint8)
    f.read(buf)

# Public S3 (no credentials needed)
with kvikio.RemoteFile.open_s3_public("s3://public-bucket/data.bin") as f:
    buf = cp.empty(f.nbytes(), dtype=cp.uint8)
    f.read(buf)

# Presigned URL
with kvikio.RemoteFile

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

