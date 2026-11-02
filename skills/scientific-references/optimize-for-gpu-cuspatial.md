---
id: sciref-optimize-for-gpu-cuspatial
name: "Scientific Ref: cuSpatial Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (optimize-for-gpu): cuSpatial Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "optimize gpu cuspatial"
  - "cuspatial reference"
keywords:
  - "optimize"
  - "gpu"
  - "cuspatial"
  - "specialized"
  - "scientific"
  - "reference"
---

# cuSpatial Reference

> Review: 2026-10-01. Code below is illustrative unless explicitly described as CPU-tested.
> GPU execution, performance, GDS, and multi-GPU behavior require validation on target hardware.

cuSpatial is a GPU-accelerated GIS library that provides spatial indexing, spatial joins, distance calculations, trajectory analysis, and GeoPandas-compatible geometry types. It integrates with cuDF for tabular data and GeoPandas for geometry interoperability, enabling you to accelerate geospatial workflows by moving the compute-heavy parts to GPU.

> **Full documentation:** https://docs.rapids.ai/api/cuspatial/stable/

> **⚠️ Project status: archived.** cuSpatial development is paused and the GitHub repository was archived (read-only) on July 28, 2025. The **final release is v25.04** — no packages are published for RAPIDS v25.06 or later (see [RSN 45](https://docs.rapids.ai/notices/rsn0045/)). The archived package can still be installed on its supported legacy platforms, but it pins RAPIDS 25.04-era dependencies (e.g., `cudf-cu12==25.4.*`), so it cannot be combined with current RAPIDS releases in the same environment. RAPIDS names no official successor; for actively maintained geospatial work use GeoPandas/Shapely (CPU), and reserve cuSpatial for existing pipelines that can stay on the 25.04 dependency stack.

## Table of Contents

1. [Installation and Setup](#installation-and-setup)
2. [GeoPandas Interoperability](#geopandas-interoperability)
3. [GeoSeries and GeoDataFrame](#geoseries-and-geodataframe)
4. [Spatial Joins — Point in Polygon](#spatial-joins--point-in-polygon)
5. [Spatial Indexing — Quadtree](#spatial-indexing--quadtree)
6. [Distance Functions](#distance-functions)
7. [Nearest Points](#nearest-points)
8. [Bounding Boxes](#bounding-boxes)
9. [Projections](#projections)
10. [Spatial Filtering](#spatial-filtering)
11. [Trajectory Analysis](#trajectory-analysis)
12. [Binary Predicates](#binary-predicates)
13. [Performance Tips](#performance-tips)
14. [Common Pitfalls](#common-pitfalls)

---

## Installation and Setup

Use `uv add` in standalone examples; follow the user's existing project package manager when one
is already configured.

```bash
uv add --extra-index-url=https://pypi.nvidia.com "cuspatial-cu12==25.4.*"   # Final 25.04 release
```

The `--extra-index-url=https://pypi.nvidia.com` index is **required** here — the `cuspatial-cu12` entry on PyPI itself is only a stub sdist; the real wheels live on pypi.nvidia.com. There are no CUDA 13 (`-cu13`) packages — the project was archived before CUDA 13 wheels were introduced. Installing cuSpatial pulls in `cudf-cu12==25.4.*` and related 25.04 pins.

Verify:
```python
import cuspatial
from shapely.geometry import Point
gs = cuspatial.GeoSeries([Point(0, 0), Point(1, 1)])
print(gs)
```

---

## GeoPandas Interoperability

cuSpatial's primary on-ramp is converting from GeoPandas. Any `GeoSeries` or `GeoDataFrame` can be moved to GPU:

```python
import geopandas as gpd
import cuspatial

# GeoPandas -> cuSpatial (CPU -> GPU)
gdf = gpd.read_file("my_shapefile.shp")
cu_gdf = cuspatial.from_geopandas(gdf)

# cuSpatial -> GeoPandas (GPU -> CPU)
gdf_back = cu_gdf.to_geopandas()
```

You can also construct a `GeoDataFrame` directly:
```python
cu_gdf = cuspatial.GeoDataFrame(geopandas_dataframe)
```

---

## GeoSeries and GeoDataFrame

`cuspatial.GeoSeries` is a GPU-backed series that holds shapely-compatible geometry objects (Point, MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon).

### Creating GeoSeries from Shapely objects

```python
from shapely.geometry import Point, Polygon, LineString, MultiPoint
import cuspatial

points = cuspatial.GeoSeries([Point(0, 0), Point(1, 1), Point(2, 2)])
polys = cuspatial.GeoSeries([
    Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
    Polygon([(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)])
])
```

### Creating GeoSeries from coordinate arrays (faster for large data)

```python
import cudf

# Points from interleaved xy coordinates
xy = cudf.Series([0.0, 0.0, 1.0, 1.0, 2.0, 2.0])  # x0, y0, x1, y1, ...
points = cuspatial.GeoSeries.from_points_xy(xy)

# MultiPoints from interleaved xy + geometry offsets
multipoints = cuspatial.GeoSeries.from_multipoints_xy(
    multipoints_xy=cudf.Series([0.0, 0.0, 1.0, 1.0, 2.0, 2.0, 3.0, 3.0]),
    geometry_offset=cudf.Series([0, 2, 4])  # 2 multipoints, each with 2 points
)
```

### GeoSeries properties

```python
gs = cuspatial.GeoSeries([Point(0, 0), Point(1, 1)])
gs.points.xy        # Access raw interleaved coordinates
gs.sizes             # Number of points per geometry
gs.iloc[0]           # Access single geometry
```

### GeoDataFrame

```python
cu_gdf = cuspatial.GeoDataFrame({
    "geometry": cuspatial.GeoSeries([Point(0, 0), Point(1, 1)]),
    "value": cudf.Series([10, 20])
})
```

---

## Spatial Joins — Point in Polygon

The most common operation: test which points are inside which polygons.

### Simple point-in-polygon

```python
from shapely.geometry import Point, Polygon
import cuspatial

points = cuspatial.GeoSeries([Point(1, 1), Point(-8, -8), Point(6, 6)])
polygons = cuspatial.GeoSeries([
    Polygon([(-10, -10), (5, -10), (5, 5), (-10, 5), (-10, -10)]),
    Polygon([(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)])
])

result = cuspatial.point_in_polygon(points, polygons)
# Returns a DataFrame of booleans: rows=points, columns=polygons
#   polygon_0  polygon_1
# 0     True      True     <- (1,1) is strictly inside both
# 1     True     False     <- (-8,-8) is in first only
# 2    False      True     <- (6,6) is in second only
```

### Quadtree-accelerated point-in-polygon (for large datasets)

For millions of points, use the quadtree pipeline — it dramatically reduces the number of point-polygon tests:

```python
import cuspatial
import cudf

# 1. Build quadtree on points
key_to_point, quadtree = cuspatial.quadtree_on_points(
    points,              # GeoSeries of points
    x_min, x_max,        # Bounding box
    y_min, y_max,
    scale=scale,         # Usually (max_extent) / (2^max_depth)
    max_depth=7,         # Max tree depth (< 16)
    max_size=125         # Max points per leaf before splitting
)

# 2. Compute polygon bounding boxes
poly_bboxes = cuspatial.polygon_bounding_boxes(polygons)

# 3. Join quadtree with bounding boxes
intersections = cuspatial.join_quadtree_and_bounding_boxes(
    quadtree, poly_bboxes, x_min, x_max, y_min, y_max, scale, max_depth
)

# 4. Test point-in-polygon only for relevant quadran

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

