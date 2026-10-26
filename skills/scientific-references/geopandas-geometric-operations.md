---
id: sciref-geopandas-geometric-operations
name: "Scientific Ref: Geometric operations, validity, and precision"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (geopandas): Geometric operations, validity, and precision"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "geopandas geometric operations"
  - "geometric operations, validity, and precision"
keywords:
  - "geopandas"
  - "geometric"
  - "operations"
  - "specialized"
  - "scientific"
  - "reference"
---

# Geometric operations, validity, and precision

GeoPandas delegates geometry work to Shapely/GEOS. Operations are planar,
two-dimensional, and expressed in CRS coordinate units. Z/M ordinates may be
carried but are not part of topology.

## Preflight state

Count missing, empty, invalid, and mixed geometries separately before any
constructive or set operation:

```python
geometry = gdf.geometry
missing = geometry.isna()
empty = geometry.is_empty
invalid = (~missing) & (~empty) & (~geometry.is_valid)

state = {
    "rows": len(gdf),
    "missing": int(missing.sum()),
    "empty": int(empty.sum()),
    "invalid": int(invalid.sum()),
    "types": geometry.geom_type.value_counts(dropna=False).to_dict(),
}
```

`is_valid` concerns polygon/ring topology; points and lines are generally valid
unless malformed. `is_simple`, `is_ring`, and `minimum_clearance` answer
different questions.

### Redacted validity diagnostics

`is_valid_reason()` can include the coordinate of a defect, for example a
self-intersection. Precise coordinates can be sensitive. Aggregate only the
reason category before `[` and retain detailed diagnostics in a protected local
artifact:

```python
reason_category = (
    geometry[invalid]
    .is_valid_reason()
    .str.split("[", n=1)
    .str[0]
    .value_counts()
)
```

## Repair is a model change

GeoPandas 1.1 exposes Shapely 2.1 repair controls:

```python
repaired = geometry.make_valid(
    method="structure",
    keep_collapsed=True,
)
```

Methods:

- `linework` preserves every edge/vertex, nodes all rings, and reconstructs
  areas with even/odd parity. It can produce complex `GeometryCollection`
  output and requires `keep_collapsed=True`.
- `structure` repairs rings, merges shells, and subtracts holes. It assumes
  shell/hole categorization is meaningful, requires GEOS >=3.10, and can drop
  collapsed parts when `keep_collapsed=False`.

Repair can turn a polygon into a multipolygon, line, point, collection, or empty
geometry. Never replace source data in place. Create a new artifact and compare:

1. valid/invalid/null/empty counts;
2. geometry-type and dimensionality transitions;
3. component counts and collapsed outputs;
4. area/length changes in appropriate units;
5. stable feature IDs and row count;
6. downstream predicate/coverage behavior.

`overlay(make_valid=True)` also repairs invalid inputs, but that convenience can
hide type changes. Audit and repair explicitly for traceable work.

## Precision models

`set_precision(grid_size, mode=...)` rounds x/y to a grid in **CRS units**:

```python
snapped = geometry.set_precision(
    grid_size=0.01,
    mode="valid_output",
)
```

Shapely 2.1 modes:

- `valid_output` removes collapsed polygonal/linear elements and duplicate
  vertices while producing valid output;
- `pointwise` rounds independently, retains duplicate vertices, and may produce
  invalid output;
- `keep_collapsed` preserves collapsed linear elements but removes collapsed
  polygonal elements.

Consequences:

- features narrower/shorter than the grid may become empty;
- spikes and narrow sections can disappear or split polygons;
- duplicate vertices are normally removed;
- Z is not rounded;
- vertex/ring/order is canonicalized and must not be used as identity;
- inputs should be valid first;
- later operations use the higher precision (smaller grid size) of inputs.

Choose the grid from documented source resolution and error—not decimal
aesthetics. `0.001` degrees is not a universal metric tolerance.

For one union/dissolve, `grid_size=` can apply fixed precision without first
attaching a precision model:

```python
merged = geometry.union_all(method="unary", grid_size=0.01)
```

GeoPandas 1.2 also accepts `grid_size=` on row-wise `intersection`, `union`,
`difference`, and `symmetric_difference`. This does not add a `grid_size`
argument to `overlay`; snap valid inputs explicitly for that workflow.
`buffer(resolution=...)` is deprecated in 1.2; use `quad_segs=`.

Record whether precision was attached to inputs or applied only to an operation.

## `union_all` algorithms

GeoPandas 1.2.0 signature:

```python
geometry.union_all(method="unary", grid_size=None)
```

- `unary`: robust general-purpose algorithm; the only method supporting
  `grid_size`.
- `coverage`: optimized for non-overlapping edge-matched polygon coverages; it
  can return invalid geometry if polygons overlap.
- `disjoint_subset`: optimized when input can be divided into non-intersecting
  subsets; requires Shapely >=2.1 and may be slower when there is one subset.

Do not use `coverage` based on visual inspection:

```python
if not geometry.is_valid_coverage(gap_width=0.0):
    edges = geometry.invalid_coverage_edges(gap_width=0.0)
    raise ValueError("Not an edge-matched non-overlapping coverage")

merged = geometry.union_all(method="coverage")
```

`is_valid_coverage()` ignores non-polygon geometry and requires Shapely >=2.1.
If narrow gaps matter, select `gap_width` in justified projected units.
`simplify_coverage()` preserves shared boundaries for a valid coverage; ordinary
element-wise `simplify()` does not.

The old `unary_union` attribute is deprecated. Use `union_all()`.

## Constructive operations

All distance/tolerance arguments are CRS units:

```python
buffered = geometry.buffer(50, quad_segs=16)
simplified = geometry.simplify(5, preserve_topology=True)
densified = geometry.segmentize(max_segment_length=10)
centroids = geometry.centroid
inside_points = geometry.representative_point()
```

Correctness notes:

- Buffering geographic degrees does not create a fixed-metre buffer.
- Negative polygon buffers can collapse to empty.
- `centroid` may fall outside a concave polygon; `representative_point()` is
  guaranteed within the geometry but is not a centroid.
- `preserve_topology=True` protects each geometry's validity, not shared
  boundaries between adjacent features.
- `segmentize()` inserts vertices along planar segments; it does not create
  geodesic densification.
- Affine rotate/scale/translate/skew operations are coordinate-space transforms,
  not CRS transformations.

## Binary predicates

Predicates implement DE-9IM relationships and are directional:

| Predicate | Practical meaning |
|---|---|
| `intersects` | Boundaries or interiors share any point |
| `disjoint` | Share no point |
| `within` | Left geometry lies in right interior/boundary under DE-9IM |
| `contains` | Inverse direction of `within`; boundary-only point is not contained |
| `covers` | No 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

