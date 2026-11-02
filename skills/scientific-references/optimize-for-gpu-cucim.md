---
id: sciref-optimize-for-gpu-cucim
name: "Scientific Ref: cuCIM Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): cuCIM Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu cucim"
  - "cucim reference"
keywords:
  - "optimize"
  - "gpu"
  - "cucim"
  - "specialized"
  - "scientific"
  - "reference"
---

# cuCIM Reference

> Review: 2026-10-01. Code below is illustrative unless explicitly described as CPU-tested.
> GPU execution, performance, GDS, and multi-GPU behavior require validation on target hardware.

cuCIM (CUDA Clara IMage) is NVIDIA's GPU-accelerated computer vision and image processing library
within the RAPIDS ecosystem. Its `cucim.skimage` module mirrors a substantial part of scikit-image
on CuPy arrays, and `cucim.CuImage` reads tiled whole-slide images. Verify function coverage and
benchmark the actual image sizes, storage path, and processing chain.

> **Full documentation:** https://docs.nvidia.com/cucim/26.08/
> **GitHub:** https://github.com/rapidsai/cucim

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [Core Concept: CuPy Arrays](#core-concept-cupy-arrays)
3. [cucim.skimage — GPU scikit-image](#cucimskimage)
4. [Color Operations](#color-operations)
5. [Exposure and Histogram](#exposure-and-histogram)
6. [Feature Detection](#feature-detection)
7. [Filters](#filters)
8. [Measure and Region Properties](#measure-and-region-properties)
9. [Morphology](#morphology)
10. [Segmentation](#segmentation)
11. [Registration](#registration)
12. [Restoration](#restoration)
13. [Transform](#transform)
14. [Metrics](#metrics)
15. [Utility Functions](#utility-functions)
16. [cucim.core.operations — NVIDIA-Specific](#cucimcoreoperations)
17. [Whole-Slide Image Reading (cucim.clara)](#whole-slide-image-reading)
18. [Performance Characteristics](#performance-characteristics)
19. [Interoperability](#interoperability)
20. [Known Limitations vs scikit-image](#known-limitations-vs-scikit-image)
21. [Common Migration Patterns](#common-migration-patterns)

---

## Installation and Setup

Use `uv add` in standalone examples; follow the user's existing project package manager when one
is already configured.

```bash
uv add --extra-index-url=https://pypi.nvidia.com "cucim-cu12==26.8.*"    # For CUDA 12.x
uv add --extra-index-url=https://pypi.nvidia.com "cucim-cu13==26.8.*"    # For CUDA 13.x
```

cuCIM wheels are also published directly to PyPI, so the extra index is optional.

**Platform:** Linux only (x86-64 and aarch64) — no Windows or macOS GPU support.
**Requires:** NVIDIA GPU with CUDA 12.x or 13.x, Python 3.11+, CuPy, NumPy, SciPy, scikit-image.

Verify:
```python
import cucim
print(cucim.__version__)

import cupy as cp
from cucim.skimage.filters import gaussian
img = cp.random.rand(512, 512).astype(cp.float32)
result = gaussian(img, sigma=3)
print(f"Filtered image shape: {result.shape}")  # Should work on GPU
```

---

## Core Concept: CuPy Arrays

cuCIM operates natively on **CuPy arrays**. Many image operations consume and return CuPy arrays. Some return scalars, tuples, dictionaries, or region objects and can synchronize; device residency does not imply zero allocation or zero host work.

```python
import cupy as cp
import numpy as np
from cucim.skimage.filters import gaussian

# Transfer image to GPU once
image_gpu = cp.asarray(numpy_image)

# All processing stays on GPU — zero-copy between cuCIM calls
blurred = gaussian(image_gpu, sigma=3)
# ... more processing on GPU ...

# Transfer back to CPU only when needed (for display, save, etc.)
result_cpu = cp.asnumpy(blurred)
```

**Best practice:** Move data to GPU once at the start, chain all cuCIM operations on GPU, then transfer back to CPU only at the end.

---

## cucim.skimage

The `cucim.skimage` module mirrors scikit-image's module structure. In most cases, replace `from skimage` with `from cucim.skimage` and pass CuPy arrays instead of NumPy arrays.

```python
# Before (CPU — scikit-image)
from skimage.filters import gaussian
import numpy as np
result = gaussian(numpy_image, sigma=3)

# After (GPU — cuCIM)
from cucim.skimage.filters import gaussian
import cupy as cp
result = gaussian(cp.asarray(numpy_image), sigma=3)
```

---

## Color Operations

`cucim.skimage.color` — 42 GPU-accelerated color space conversion functions.

```python
from cucim.skimage.color import rgb2gray, rgb2hsv, rgb2lab, label2rgb
from cucim.skimage.color import separate_stains, combine_stains

# Color space conversions
gray = rgb2gray(rgb_image_gpu)
hsv = rgb2hsv(rgb_image_gpu)
lab = rgb2lab(rgb_image_gpu)

# Stain separation (for H&E histology)
stains = separate_stains(rgb_image_gpu, stain_matrix)
```

**Available conversions:** `rgb2gray`, `rgb2hsv`, `hsv2rgb`, `rgb2lab`, `lab2rgb`, `rgb2xyz`, `xyz2rgb`, `rgb2luv`, `luv2rgb`, `rgb2ycbcr`, `ycbcr2rgb`, `rgb2yuv`, `yuv2rgb`, `rgb2yiq`, `yiq2rgb`, `rgb2hed`, `hed2rgb`, `rgb2rgbcie`, `rgbcie2rgb`, `gray2rgb`, `gray2rgba`, `rgba2rgb`, `convert_colorspace`, `label2rgb`

**Color difference:** `deltaE_cie76`, `deltaE_ciede94`, `deltaE_ciede2000`, `deltaE_cmc`

---

## Exposure and Histogram

`cucim.skimage.exposure` — histogram equalization, contrast adjustment.

```python
from cucim.skimage.exposure import (
    equalize_hist, equalize_adapthist,
    rescale_intensity, adjust_gamma, adjust_log, adjust_sigmoid,
    histogram, match_histograms, is_low_contrast
)

# CLAHE (Contrast Limited Adaptive Histogram Equalization)
enhanced = equalize_adapthist(image_gpu, clip_limit=0.03)

# Gamma correction
brightened = adjust_gamma(image_gpu, gamma=0.5)

# Rescale intensity to [0, 1]
normalized = rescale_intensity(image_gpu)

# Histogram matching between two images
matched = match_histograms(source_gpu, reference_gpu)
```

---

## Feature Detection

`cucim.skimage.feature` — edge, corner, and blob detection.

```python
from cucim.skimage.feature import (
    canny, corner_harris, corner_peaks,
    blob_dog, blob_doh, blob_log,
    structure_tensor, hessian_matrix, hessian_matrix_det,
    match_template, peak_local_max, daisy, multiscale_basic_features
)

# Canny edge detection
edges = canny(gray_image_gpu, sigma=2.0)

# Harris corner detection
corners = corner_harris(gray_image_gpu)
corner_coords = corner_peaks(corners, min_distance=5)

# Blob detection (Difference of Gaussian)
blobs = blob_dog(gray_image_gpu, max_sigma=30, threshold=0.1)

# Template matching
result = match_template(image_gpu, template_gpu)
```

---

## Filters

`cucim.skimage.filters` — 47 GPU-accelerated filter functions. This is one of the most commonly used modules.

```python
from cucim.skimage.filters import (
    gaussian, median, sobel, laplace, unsharp_mask,
    frangi, hessian, meijering, sato,
    threshold_otsu, threshold_multiotsu, threshold_sauvola,
    gabor, difference_of_gaussians, butterworth
)

# G

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

