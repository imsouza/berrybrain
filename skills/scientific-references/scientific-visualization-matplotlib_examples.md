---
id: sciref-scientific-visualization-matplotlib-examples
name: "Scientific Ref: Current Matplotlib, Seaborn, and Plotly Patterns"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-visualization): Current Matplotlib, Seaborn, and Plotly Patterns"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific visualization matplotlib examples"
  - "cientifico visualization matplotlib examples"
  - "current matplotlib, seaborn, and plotly patterns"
keywords:
  - "scientific"
  - "visualization"
  - "matplotlib"
  - "examples"
  - "cientifico"
  - "specialized"
  - "reference"
  - "current"
---

# Current Matplotlib, Seaborn, and Plotly Patterns

Verified 2026-10-01 against Matplotlib 3.11.2, Seaborn 0.13.2, Plotly 7.1.0, Kaleido 1.4.0, Pillow 12.3.0, and pypdf 6.19.0. Source IDs resolve in `sources.md`.

Run examples from the skill directory with pinned direct dependencies:

```bash
uv run --isolated --no-project --python 3.13 \
  --with "matplotlib==3.11.2" \
  --with "seaborn==0.13.2" \
  --with "plotly==7.1.0" \
  --with "kaleido==1.4.0" \
  --with "pillow==12.3.0" \
  --with "pypdf==6.19.0" \
  python your_figure.py
```

These pins are a dated direct-dependency snapshot, not a lock of all transitive artifacts. Keep a lock in the consuming project for exact replay. The snippets share imports/variables: supply your scientific `frame`, `x`, and `y`. They were exercised with synthetic fixtures; they do not validate an analysis of your data.

Start `your_figure.py` with this bootstrap when running from the skill directory:

```python
from pathlib import Path
import sys

skill_root = Path.cwd()
sys.path[:0] = [str(skill_root / "scripts"), str(skill_root / "assets")]
Path("outputs").mkdir(exist_ok=True)
```

## Rendering and hardcopy backends

Matplotlib separates interactive display backends from hardcopy renderers. The current built-ins include PDF (`pdf`), PS (`ps`, `eps`), SVG (`svg`), PGF (`pgf`, `pdf` through TeX), and optional Cairo (`png`, `ps`, `pdf`, `svg`); Agg is the common raster renderer [MPL-BACKENDS]. JPEG, TIFF, and WebP saving uses Pillow through the raster path.

Available output depends on the active backend/build:

```python
supported = fig.canvas.get_supported_filetypes()
print(supported)
```

`Figure.savefig(..., backend="cairo")` or `backend="pgf"` can select another renderer, but Matplotlib documents the default as normally sufficient [MPL-SAVE]. PGF requires a working TeX setup; Cairo requires pycairo or cairocffi. Inspect output because a vector container can still contain rasterized artists.

## Scoped style and exact dimensions

Prefer temporary style contexts to global state:

```python
import matplotlib.pyplot as plt

from style_presets import style_context

with style_context("default", palette_name="okabe_ito_on_white"):
    fig, ax = plt.subplots(
        figsize=(89 / 25.4, 60 / 25.4),
        layout="constrained",
    )
    ax.plot([0, 1, 2], [1, 3, 2], marker="o", label="Observed")
    ax.set(xlabel="Time (hours)", ylabel="Response (unit)")
    ax.legend()
```

`layout="constrained"` handles labels, legends, nested layouts, and colorbars more flexibly than `tight_layout`; calling `tight_layout()` turns constrained layout off [MPL-LAYOUT].

If exact page dimensions matter, do not export with `bbox_inches="tight"`; it recalculates the bounding box and changes the physical output size [MPL-SAVE].

You can also use the bundled parseable style:

```python
from pathlib import Path
import matplotlib.pyplot as plt

skill_root = Path(".")  # run from the skill directory
with plt.style.context(skill_root / "assets" / "publication.mplstyle"):
    fig, ax = plt.subplots(layout="constrained")
```

## Preserve raw observations and define uncertainty

```python
import numpy as np
import matplotlib.pyplot as plt

rng = np.random.default_rng(20260723)
groups = {
    "Control": rng.normal(0.0, 1.0, 24),
    "Treatment": rng.normal(0.7, 1.1, 24),
}

fig, ax = plt.subplots(figsize=(3.5, 2.8), layout="constrained")
for position, (label, values) in enumerate(groups.items()):
    jitter = rng.uniform(-0.08, 0.08, len(values))
    ax.scatter(
        position + jitter,
        values,
        alpha=0.65,
        label=label,
    )
    mean = values.mean()
    sem = values.std(ddof=1) / np.sqrt(len(values))
    ax.errorbar(position, mean, yerr=sem, color="black", capsize=3)

ax.set(
    xticks=range(len(groups)),
    xticklabels=list(groups),
    ylabel="Response (unit)",
)
```

Caption the error bars as mean ± one SEM and state `n=24` independent observations per group. If independence is false, use an analysis and interval that respects the design.

## Missing data and no silent interpolation

```python
import numpy as np

time = np.arange(8)
signal = np.array([1.0, 1.4, np.nan, np.nan, 2.1, 2.0, 2.4, 2.7])

fig, ax = plt.subplots(layout="constrained")
ax.plot(time, signal, marker="o", label="Observed")  # gaps remain gaps
ax.scatter(
    [2, 3], [0.04, 0.04], transform=ax.get_xaxis_transform(),
    marker="x", color="0.35", label="Missing (axis strip)",
)
ax.set(xlabel="Time (days)", ylabel="Signal (unit)")
ax.legend()
```

If a model estimates the missing interval, plot the model separately with its uncertainty and identify it as modeled, not observed.

## Log axes and explicit nonpositive policy

```python
import numpy as np
import matplotlib.pyplot as plt

concentration = np.array([0.1, 1.0, 10.0, 100.0])
response = np.array([0.4, 0.9, 2.1, 4.3])

fig, ax = plt.subplots(layout="constrained")
ax.plot(concentration, response, marker="o")
ax.set_xscale("log", base=10)
ax.set(xlabel="Concentration (µM; log10 axis)", ylabel="Response (unit)")
```

Do not silently omit zeros or negatives. State the measurement-domain rule or use another representation.

## Centered heatmap and missing-value color

```python
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

values = np.array([
    [-2.0, -0.5, 0.1],
    [-1.1, np.nan, 1.8],
    [-0.2, 0.7, 3.0],
])
norm = mpl.colors.TwoSlopeNorm(vmin=-2, vcenter=0, vmax=3)
cmap = mpl.colormaps["RdBu_r"].with_extremes(bad="#777777")

fig, ax = plt.subplots(layout="constrained")
image = ax.imshow(values, norm=norm, cmap=cmap, interpolation="nearest")
colorbar = fig.colorbar(image, ax=ax)
colorbar.set_label("Change from baseline (unit)")
ax.set(xlabel="Sample", ylabel="Feature")
```

`TwoSlopeNorm` gives each side of the center a different linear mapping. Use `CenteredNorm` when symmetric treatment around a center is appropriate, `LogNorm` for strictly positive orders of magnitude, and `BoundaryNorm` for declared classes [MPL-NORM].

## Multi-panel layout

```python
import matplotlib.pyplot as plt

fig = plt.figure(figsize=(7.0, 4.0), layout="constrained")
subfigures = fig.subfigures(1, 2, width_ratios=[2, 1])
left_axes = subfigures[0].subplots(2, 1, sharex=True)
right_ax = subfigures[1].subplots()

for label, ax in zip("ABC", [*left_axes, right_ax]):
    ax.text(
        -0.12,
        1.05,
        label,
        transform=ax.transAxes,
        fontweight="bold",
        va="top",
    )
```

`GridSpec

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

