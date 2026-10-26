---
id: sci-openpiv
name: "Scientific: openpiv"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Performs Particle Image Velocimetry (PIV) analysis with OpenPIV. Use when extracting velocity fields from PIV image pairs, analyzing fluid dynamics or flow visualization experiments, cross-correlating interrogation windows, validating and replacing spurious PIV vectors, or comput"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "openpiv"
keywords:
  - "openpiv"
  - "performs"
  - "particle"
  - "image"
  - "velocimetry"
  - "analysis"
---

# OpenPIV

## Overview

OpenPIV (Open Particle Image Velocimetry) analyzes fluid flow from PIV image pairs. It covers
preprocessing, cross-correlation, vector validation, outlier replacement, smoothing, and scaling to
physical units.

Targets **openpiv 0.26.1**. Synthetic checks ran on Python 3.13, NumPy 2.5.3, SciPy 1.18.1,
scikit-image 0.26.0, and Matplotlib 3.11.2. Rust was not installed; use `backend="scipy"` for the
tested path. See [review evidence](references/advanced_algorithms.md#review-sources-and-verification).

## When to use

Use this skill when working with experimental PIV or flow-visualization image pairs: measuring 2D
velocity fields, tuning interrogation-window parameters, validating vectors, or deriving vorticity,
strain rate, and turbulence statistics. For *simulating* flow rather than measuring it, use a CFD
skill instead.

## Quick Start

Install OpenPIV:

```bash
uv pip install openpiv

# Pin it when the analysis needs to be reproducible -- this is the version every
# snippet below was checked against.
uv pip install "openpiv==0.26.1"
```

Run PIV analysis on an image pair:

```python
import numpy as np
from openpiv import tools, pyprocess, validation, filters, scaling

frame_a = tools.imread("image_a.bmp")
frame_b = tools.imread("image_b.bmp")

# Always returns (u, v, s2n); s2n is all NaN if sig2noise_method=None.
u, v, s2n = pyprocess.extended_search_area_piv(
    frame_a.astype(np.float32),
    frame_b.astype(np.float32),
    window_size=32,
    overlap=12,
    dt=0.02,
    search_area_size=38,
    correlation_method="linear",   # circular also supports extended search
    normalized_correlation=True,
    backend="scipy",
    sig2noise_method="peak2peak",
)

x, y = pyprocess.get_coordinates(
    image_size=frame_a.shape,
    search_area_size=38,
    overlap=12,
    center_on_field=False,         # matches sliding-window positions
)

# flags is a boolean array: True marks a spurious vector.
flags = validation.sig2noise_val(s2n, threshold=1.05) | ~np.isfinite(s2n)
flags |= ~np.isfinite(u) | ~np.isfinite(v)
u, v = filters.replace_outliers(u, v, flags, method="localmean", max_iter=3, kernel_size=2)

# Scale, then convert to right-handed image-boundary coordinates.
x, y, u, v = scaling.uniform(x, y, u, v, scaling_factor=96.52)
y, v = frame_a.shape[0] / 96.52 - y, -v

tools.save("vectors.txt", x, y, u, v, flags)
```

Or use the bundled CLI, which also checks inputs and preserves masks and processing parameters:

```bash
python skills/openpiv/scripts/runner.py \
    --image frame_a.bmp --image frame_b.bmp --output_dir results --verbose
```

## Core Concepts

### PIV Fundamentals

Particle Image Velocimetry is an optical method for measuring fluid velocity by tracking illuminated
tracer particles between two images.

**Process flow:**

1. Capture an image pair (`frame_a`, `frame_b`) separated by a known time `dt`.
2. Divide the images into interrogation windows.
3. Cross-correlate matching windows to find peak displacement.
4. Validate vectors (signal-to-noise, global range, local median).
5. Replace spurious vectors with interpolated values.
6. Scale pixel displacements to physical units.

### Interrogation Window Parameters

**`window_size`** — correlation window in pixels (typically 16–128). Larger windows give better
correlation but coarser spatial resolution.

**`overlap`** — pixels shared between adjacent windows (typically 50–75% of `window_size`). Higher
overlap raises vector density and cost, but adjacent vectors become correlated rather than
independent.

**`search_area_size`** — the window searched in the second frame. Must be ≥ `window_size`; a few
pixels larger accommodates larger displacements. Both `"circular"` and `"linear"` support extended
search. The CLI chooses zero-padded `"linear"` with `normalized_correlation=True` for it; this
does not recover arbitrary displacement or eliminate spurious peaks. Grid stride is
`search_area_size - overlap`, so overlap must be smaller than the search area.

Rules of thumb: keep the largest displacement under about a quarter of `window_size`, and aim for
5–10 particles per window.

### Signal-to-Noise Ratio

`s2n` measures how distinct the correlation peak is. `sig2noise_method` controls how it is computed —
`"peak2mean"` (the function default) or `"peak2peak"`. **The two are on different scales**, so a
threshold tuned for one is meaningless for the other. Typical `peak2peak` thresholds are 1.05–1.3.

```python
flags = validation.sig2noise_val(s2n, threshold=1.05)
# flags is bool: True == spurious. `~flags` selects the good vectors.
```

## Common Operations

### Dynamic Masking

Masking lives in `openpiv.preprocess` and returns `(image, mask)`. Use floating-point copies
to avoid unsigned subtraction artifacts. Inspect masks on both frames before analysis.

```python
from openpiv import preprocess

# Intensity masking uses Otsu; the threshold argument is for edges.
frame_a_masked, mask_a = preprocess.dynamic_masking(
    frame_a.astype(np.float64), method="intensity", filter_size=7, threshold=0.005
)
frame_b_masked, mask_b = preprocess.dynamic_masking(
    frame_b.astype(np.float64), method="intensity", filter_size=7, threshold=0.005
)
```

Preserve the union `mask_a | mask_b` as excluded physical regions. The CLI samples it at
interrogation centers, saves it, and keeps those velocities NaN after replacement. Windows
straddling an object can still be biased: inspect/dilate masks for the experiment. In 0.26.1
`method="edges"` indexes with uint8 instead of bool, potentially corrupting the image or failing.
The CLI refuses it; use intensity masking or a verified boolean mask in a custom workflow.

### Multi-Pass Processing

Multi-pass (window deformation) lives in `openpiv.windef`, driven by a `PIVSettings` dataclass.
`pyprocess` has no multi-pass entry point.

```python
import numpy as np
from openpiv import scaling, windef

settings = windef.PIVSettings(
    windowsizes=(64, 32, 16), overlap=(32, 16, 8), num_iterations=3,
    backend="scipy", sig2noise_method="peak2peak", sig2noise_threshold=1.05,
)

x, y, u, v, flags = windef.simple_multipass(
    frame_a.astype(np.float32), frame_b.astype(np.float32), settings
)

# Output is in PIXELS PER FRAME -- convert yourself. scaling.uniform only divides
# by scaling_factor, so apply dt separately.
dt = 0.02
x, y, u, v = scaling.uniform(x, y, u, v, scaling_factor=96.52)
u, v = u / dt, v / dt
```

`simple_multipass` validates, replaces outliers, fills remaining NaNs w

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

