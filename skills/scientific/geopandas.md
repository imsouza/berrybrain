---
id: sci-geopandas
name: "Scientific: geopandas"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Guidance and local audit tools for Python workflows that directly use GeoPandas GeoSeries, GeoDataFrame, spatial operations, or vector-data I/O."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "geopandas"
keywords:
  - "geopandas"
  - "guidance"
  - "local"
  - "audit"
  - "tools"
  - "python"
  - "workflows"
---

# GeoPandas

Use GeoPandas for planar vector data represented as pandas-like `GeoSeries` and
`GeoDataFrame` objects. This skill targets stable **GeoPandas 1.2.0** (released
2026-09-28). The stable website currently carries a development build label;
release-specific behavior below was checked against the v1.2.0 source and wheel.

## Reproducible environment

GeoPandas 1.2.0 requires Python 3.11+, NumPy >=2, pandas >=2.2,
Shapely >=2.1, pyproj >=3.7, pyogrio >=0.8, and `packaging`. The current
pyproj wheel below requires Python 3.12+. This exact Python 3.12 snapshot was
smoke-tested on 2026-10-01:

```bash
uv venv --python 3.12
uv pip install \
  "geopandas==1.2.0" \
  "numpy==2.5.3" \
  "pandas==3.0.6" \
  "shapely==2.1.2" \
  "pyproj==3.8.0" \
  "pyogrio==0.13.0" \
  "pyarrow==25.0.1" \
  "packaging==26.3"
```

Keep optional plotting and PostGIS packages pinned in the project lock as well.
Do not mix binary geospatial packages from incompatible package channels.

## Workflow

1. Inspect a vetted local layer with `vector_inventory.py`; retain source hashes.
2. Use `crs_reprojection_plan.py` to inspect candidate transformations. It plans
   only: execute an appropriate `to_crs()`/pyproj transformation separately.
3. Audit geometry with `geometry_validity_report.py`; compare simulated repair
   changes before requesting its optional new GeoPackage output.
4. Run the intended analysis with explicit predicates, CRS units, precision,
   and aggregation rules. `spatial_join_audit.py` measures join cardinality;
   it does not export joined features or perform a dissolve.
5. Use `export_plan.py` to inspect the proposed contract, then write and reopen
   the actual output separately. A successful plan has not written a file.
6. Review disclosure and generalization before sharing derived geodata/maps,
   using `sensitive_coordinates_checklist.py` when sensitive locations occur.

Examples below use synthetic or placeholder local inputs. File/database examples
need the named dataset or service; PostGIS and tile-provider calls were reviewed
against upstream contracts but were not exercised against a live service.

## Safety and privacy contract

- Treat exact coordinates, addresses, parcel boundaries, trajectories, and
  small-area joins as sensitive. Default reports to counts, categories, coarse
  extents, and redacted identifiers. Generalize before publication.
- Never automatically load a URL, cloud URI, GDAL `/vsi*` path, archive, or
  geocode an address. Obtain explicit approval, validate provenance and hashes,
  then stage an unpacked local file in an isolated workspace.
- GDAL/OGR drivers, GEOS, PROJ, pyogrio, Shapely, pyproj, and their wheels are a
  native-code trust boundary. Prefer official wheels/conda-forge, record native
  versions, restrict drivers, and process untrusted data in a sandbox.
- Do not open macro-enabled office files or nested archives through permissive
  GDAL drivers. The bundled CLIs use an extension allowlist and reject archives.
- Read only named database secrets such as `GEOPANDAS_POSTGIS_PASSWORD`; use a
  secret manager or scoped environment variable. Never embed a password in a
  URL or source, print an engine/URL, or dump the environment.
- Every derived artifact needs source hashes/versions, CRS, operation parameters,
  predicate, join cardinality, precision/repair choices, and row-count checks.

## Correctness gates

Apply these gates before trusting a result:

1. **Identity and provenance** — identify the source layer, stable feature key,
   duplicate IDs, row count, geometry column, parser/driver, and content hash.
2. **Geometry state** — count null, empty, invalid, mixed, Z/M, and collapsed
   geometries separately. `None` is missing; an empty Shapely geometry is real.
3. **CRS semantics** — require CRS metadata. `set_crs()` assigns metadata;
   `to_crs()` transforms coordinates. Never guess a CRS from coordinate ranges.
4. **Units and operation** — GeoPandas is planar. Geographic coordinates are
   angular; do not use them directly for buffer, distance, area, nearest joins,
   precision grids, or tolerances. Choose a fit-for-purpose local/equal-area CRS
   or a geodesic method.
5. **Transform quality** — inspect axis order, area of use, datum pipeline,
   expected accuracy, ballpark status, and missing grids. Keep PROJ network
   disabled unless the user explicitly approves grid retrieval.
6. **Topology and precision** — validate before and after repair/overlay. Pick a
   precision grid from source accuracy and CRS units; arbitrary snapping can
   collapse features or create bias.
7. **Cardinality** — state expected one-to-one, one-to-many, or many-to-many
   behavior before `merge`, `sjoin`, or `sjoin_nearest`; audit unmatched and
   multiplied rows afterward.
8. **Output contract** — use a new output path, preserve a stable feature ID,
   document schema/CRS/encoding, reopen the artifact, and compare counts/types.

## CRS and antimeridian rules

GeoPandas stores CRS as `pyproj.CRS`. Coordinate arrays use traditional GIS
`(x, y)` order, while authority definitions can advertise latitude-first axes.
Use `Transformer(..., always_xy=True)` for explicit coordinate-array pipelines,
and record that choice.

`to_crs()` transforms vertices and assumes each segment is straight in the
source CRS; it does not transform geodesic arcs. Geometries crossing ±180° or a
projection boundary can be badly wrapped. Detect crossings, split/unwrap and
densify in a documented geographic representation, transform parts, then
validate. Do not use Web Mercator as a general measurement CRS.

```python
crs = gdf.crs  # a pyproj.CRS when present
if crs is None or crs.is_geographic:
    raise ValueError("Choose a justified projected CRS before planar measurement")

unit_names = [axis.unit_name for axis in crs.axis_info]
areas = gdf.geometry.area  # square CRS units, not automatically square metres
```

See [CRS management](references/crs-management.md).

## Core API decisions

### Data structures

- A `GeoDataFrame` can hold multiple geometry columns, each with CRS metadata,
  but only `active_geometry_name` drives frame-level spatial operations.
- Binary `GeoSeries` methods are row-wise and align by index by default. Use
  `align=False` only when positional pairing is explicitly intended and lengths
  and order were verified.
- Duplicate column names and duplicate feature IDs are ambiguous; reject or
  resolve them before joins and exports.

See [data structures](references/d

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

