---
id: sciref-optimize-for-gpu-cuxfilter
name: "Scientific Ref: cuxfilter Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): cuxfilter Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu cuxfilter"
  - "cuxfilter reference"
keywords:
  - "optimize"
  - "gpu"
  - "cuxfilter"
  - "specialized"
  - "scientific"
  - "reference"
---

# cuxfilter Reference

> Review: 2026-10-01. Code below is illustrative unless explicitly described as CPU-tested.
> GPU execution, performance, GDS, and multi-GPU behavior require validation on target hardware.

cuxfilter is a GPU-accelerated cross-filtering dashboard library from the NVIDIA RAPIDS ecosystem. It enables interactive, multi-chart exploratory data analysis dashboards from Jupyter notebooks in just a few lines of Python. All filtering, groupby, and aggregation operations happen on the GPU via cuDF, with only the visualization results sent to the browser.

> **Full documentation:** https://docs.rapids.ai/api/cuxfilter/stable/
> **Version (stable):** 26.06.00 (final release)
> **Repository:** https://github.com/rapidsai/cuxfilter

> **⚠️ Project status: sunset.** cuxfilter has been sunset — **v26.06 is the final release** and no packages will be published for later RAPIDS releases (see [RSN 60](https://docs.rapids.ai/notices/rsn0060/)). The examples below target the isolated 26.06 API and are not a guarantee of compatibility with current dependencies; for new projects RAPIDS recommends composing dashboards directly from maintained libraries instead: **cuDF** for GPU data loading/aggregation plus **HoloViews / hvPlot / Datashader** for linked cross-filtering visualizations, served with **Panel**, Plotly Dash, Streamlit, or Bokeh.

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [Core Concepts](#core-concepts)
3. [DataFrame: Loading Data](#dataframe-loading-data)
4. [Charts](#charts)
5. [Widgets](#widgets)
6. [Dashboard Creation](#dashboard-creation)
7. [Layouts](#layouts)
8. [Themes](#themes)
9. [Dashboard Display and Export](#dashboard-display-and-export)
10. [Graph Visualization](#graph-visualization)
11. [Multi-GPU with Dask-cuDF](#multi-gpu-with-dask-cudf)
12. [Interoperability](#interoperability)
13. [Performance Tips](#performance-tips)
14. [Common Patterns](#common-patterns)

---

## Installation and Setup

Use `uv add` in standalone examples; follow the user's existing project package manager when one
is already configured.

```bash
uv add --extra-index-url=https://pypi.nvidia.com "cuxfilter-cu12==26.6.*"   # For CUDA 12.x
uv add --extra-index-url=https://pypi.nvidia.com "cuxfilter-cu13==26.6.*"   # For CUDA 13.x
```

Both install the final 26.06 release — no further updates will be published. cuxfilter wheels are also on PyPI directly, so the extra index is optional. cuxfilter depends on matching cuDF 26.06. Keep the entire legacy stack isolated from RAPIDS 26.08 and pandas 3.

**Platform:** Linux and WSL2 only (no native macOS or Windows).
**Requires:** NVIDIA GPU with CUDA 12.x or 13.x support, Python 3.11+.

Verify:
```python
import cuxfilter
import cudf

df = cudf.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
cux_df = cuxfilter.DataFrame.from_dataframe(df)
print(cux_df.data.head())  # Should print GPU dataframe
```

---

## Core Concepts

cuxfilter has five main modules:

1. **`cuxfilter.DataFrame`** — Wraps a cuDF DataFrame for dashboard use. Entry point for creating dashboards.
2. **`cuxfilter.DashBoard`** — The interactive dashboard object. Created from a DataFrame with charts.
3. **`cuxfilter.charts`** — Chart factory functions (bar, scatter, line, heatmap, choropleth, graph, widgets).
4. **`cuxfilter.layouts`** — Preset and custom layout configurations for chart arrangement.
5. **`cuxfilter.themes`** — Visual themes for dashboards (default, dark, rapids, rapids_dark).

The workflow is always: **Load data → Create charts → Build dashboard → Display**.

---

## DataFrame: Loading Data

The `cuxfilter.DataFrame` is the starting point. It wraps a cuDF or dask_cudf DataFrame.

### From a cuDF DataFrame (most common)
```python
import cudf
import cuxfilter

cudf_df = cudf.DataFrame({
    "x": [0, 1, 2, 3, 4],
    "y": [10.0, 11.0, 12.0, 13.0, 14.0],
    "category": ["A", "B", "A", "B", "A"]
})
cux_df = cuxfilter.DataFrame.from_dataframe(cudf_df)
```

### From an Arrow file on disk
```python
cux_df = cuxfilter.DataFrame.from_arrow("data/my_dataset.arrow")
```

### From a graph (nodes + edges)
```python
import cugraph

edges = cudf.DataFrame({"source": [0, 1, 2], "target": [1, 2, 3], "weight": [1.0, 2.0, 3.0]})
G = cugraph.Graph()
G.from_cudf_edgelist(edges, source="source", destination="target", edge_attr="weight")
positions = cugraph.force_atlas2(G)
cux_df = cuxfilter.DataFrame.load_graph((positions, edges))
```

Or directly from cuDF DataFrames:
```python
nodes = cudf.DataFrame({"vertex": [0, 1, 2, 3], "x": [0, 1, 2, 3], "y": [4, 4, 2, 6], "attr": [0, 1, 1, 1]})
edges = cudf.DataFrame({"source": [0, 1, 2], "target": [1, 2, 3], "weight": [1.0, 2.0, 3.0]})
cux_df = cuxfilter.DataFrame.load_graph((nodes, edges))
```

### Accessing the underlying data
```python
cux_df.data  # The cuDF DataFrame
cux_df.data["new_col"] = cux_df.data["x"] * 2  # Add columns before creating dashboard
```

---

## Charts

All chart functions are accessed via `cuxfilter.charts`. They use the top-level shorthand — you do NOT need to import submodules like `cuxfilter.charts.bokeh` or `cuxfilter.charts.datashader` directly.

### Bar Chart (Bokeh)
```python
chart = cuxfilter.charts.bar(
    x="column_name",           # Required: x-axis column
    y=None,                    # Optional: y-axis column (defaults to count)
    data_points=None,          # Number of bins (None = nunique)
    add_interaction=True,      # Enable cross-filtering interaction
    aggregate_fn="count",      # 'count' or 'mean'
    step_size=None,            # Step size for range slider
    title="",                  # Chart title
    autoscaling=True,          # Auto-scale y-axis on data update
)
```

### Line Chart (Bokeh)
```python
chart = cuxfilter.charts.line(
    x="x_col",
    y="y_col",
    data_points=100,
    add_interaction=True,
)
```

### Scatter Plot (Datashader — handles millions of points)
```python
chart = cuxfilter.charts.scatter(
    x="x_col",
    y="y_col",
    aggregate_col=None,              # Column for color aggregation
    aggregate_fn="count",            # 'count', 'mean', 'max', 'min'
    color_palette=None,              # Bokeh palette or list of hex colors
    point_size=15,
    pixel_shade_type="eq_hist",      # 'eq_hist', 'linear', 'log', 'cbrt'
    pixel_density=0.5,               # [0, 1], higher = denser
    pixel_spread="dynspread",        # 'dynspread' or 'spread'
    tile_provider=None,              # Map tile (e.g., "CartoLight" for geo data)
    ti

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

