---
id: sciref-geopandas-data-io
name: "Scientific Ref: Vector I/O, GeoParquet, Arrow, and PostGIS"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (geopandas): Vector I/O, GeoParquet, Arrow, and PostGIS"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "geopandas"
  - "vector i/o, geoparquet, arrow, and postgis"
keywords:
  - "geopandas"
  - "specialized"
  - "scientific"
  - "reference"
  - "vector"
  - "geoparquet"
---

# Vector I/O, GeoParquet, Arrow, and PostGIS

GeoPandas 1.x defaults to pyogrio for vector-file I/O. pyogrio and Fiona are
bindings to GDAL/OGR; actual formats, options, and behavior depend on the
installed native GDAL and drivers.

## Local-only intake policy

Do not automatically pass any of these to GeoPandas/GDAL:

- `http://`, `https://`, `s3://`, `gs://`, Azure, or another remote URI;
- GDAL `/vsicurl/`, `/vsis3/`, `/vsizip/`, chained virtual filesystems, or
  pyogrio `zip+...` paths;
- ZIP/KMZ/TAR/GZ/7z/RAR or nested archives;
- macro-enabled office files or an untrusted permissive driver;
- a user-supplied PostGIS connection string.

GeoPandas officially supports URLs and GDAL supports network/archive virtual
filesystems, but that capability crosses network, decompression, parser, and
credential trust boundaries. Obtain explicit approval, verify source/hash and
size out of band, unpack in a sandbox with resource limits, then process an
allowlisted local regular file.

The bundled CLIs reject URL/VSI/archive syntax, symlinks, path traversal, and
non-allowlisted suffixes.

## Inspect before reading features

For GDAL-backed formats:

```python
from pathlib import Path
import pyogrio
import geopandas

path = Path("approved/input.gpkg")
if not path.is_file() or path.is_symlink():
    raise ValueError("Expected a vetted local regular file")

layers = pyogrio.list_layers(path)
info = pyogrio.read_info(
    path, layer="approved_layer", force_feature_count=False, force_total_bounds=False
)
drivers = pyogrio.list_drivers()
```

GeoPandas 1.2 adds `geopandas.read_file_info(path, layer=...)`, a small wrapper
with only those two parameters. Use `pyogrio.read_info` directly for options
such as `force_feature_count` and `force_total_bounds`; the wrapper rejects them.

Record:

- primary-file hash and byte size (a Shapefile hash does not cover sidecars);
- driver, layer, declared feature count, fields/dtypes, encoding, geometry type;
- CRS and whether bounds were present, but redact precise bounds by default;
- `pyogrio.__gdal_version__`, `pyogrio.__gdal_geos_version__`, Shapely GEOS,
  pyproj PROJ, package versions, and enabled driver capabilities.

In pyogrio 0.13, `list_drivers()` reports capabilities containing `r`, `w`,
and/or `a` (append, GDAL >=3.11); `list_drivers(append=True)` filters for known
append support. A listed driver is not proof every field/geometry is supported. Treat drivers as
an allowlist, not merely a discovered list.

## `read_file`

Stable signature:

```python
gdf = geopandas.read_file(
    filename,
    bbox=None,
    mask=None,
    columns=None,
    rows=None,
    engine="pyogrio",
    use_arrow=True,
)
```

Rules:

- `bbox` and `mask` are mutually exclusive.
- With pyogrio, a bbox tuple must already be in the dataset CRS. Fiona can
  reproject a GeoSeries/GeoDataFrame bbox; do not depend on engine-specific
  implicit behavior.
- A mask must have an explicit CRS compatible with the source.
- `columns=[]` reads geometry without attributes; `ignore_geometry=True`
  returns a pandas DataFrame.
- `rows=n` reads the first n rows; `rows=slice(a, b)` reads a slice.
- `where=` is evaluated by a driver SQL dialect. Do not concatenate untrusted
  expressions.
- Encoding auto-detection can fail; set a verified encoding explicitly.
- `use_arrow=True` requires PyArrow and speeds pyogrio bulk transfer, but does
  not change parser trust or correctness requirements.
- Bound both file bytes and features. Some drivers cannot cheaply report a
  count; read at most `limit + 1` and fail closed when the limit is exceeded.

GeoPandas may use HTTP range requests or download an entire URL in memory.
This skill therefore does not include remote-read examples.

## Filters are not always exact

pyogrio documents:

- `bbox`/`mask` coordinates must use the dataset CRS;
- when GDAL is built with GEOS, geometry intersection filtering is exact;
- without GEOS, filters can return features whose **bounding boxes** intersect,
  requiring a second exact predicate check;
- Arrow reads involving skip/max may read batches beyond the requested slice
  before slicing;
- feature IDs are driver-specific and may start at 0, 1, or another value.

Do not treat driver FID as a portable stable feature ID.

## Writing traditional vector formats

Write a new path and reopen it:

```python
output = Path("derived/result.gpkg")
if output.exists() or output.is_symlink():
    raise FileExistsError("Choose a new output path")

gdf.to_file(
    output,
    layer="result",
    driver="GPKG",
    engine="pyogrio",
    index=False,
    use_arrow=True,
)

roundtrip = geopandas.read_file(output, layer="result", engine="pyogrio")
```

Never use implicit overwrite/append. Driver behavior varies and multi-file
formats complicate atomic writes.

### Format tradeoffs

- **GeoPackage**: good general local interchange; multiple layers, one geometry
  column per layer, SQL-backed metadata.
- **GeoJSON**: broadly interoperable but normally WGS84 longitude/latitude,
  limited type fidelity, text-heavy, and easy to leak precise coordinates.
- **Shapefile**: legacy multi-file format with field-name, type, null, encoding,
  geometry, and size constraints. Avoid for new work.
- **FlatGeobuf**: efficient stream/spatial-index format, but interoperability
  still depends on driver versions.
- **GeoParquet**: efficient columnar storage with multiple geometry columns and
  explicit geospatial metadata.

Traditional formats often cannot store lists, structs, arbitrary objects, or
multiple geometry columns. Plan conversions and reject silent loss.

## GeoParquet and Feather

```python
gdf.to_parquet(
    "derived/result.parquet",
    index=False,
    compression="snappy",
    geometry_encoding="WKB",
    write_covering_bbox=False,
    schema_version="1.1.0",
)

roundtrip = geopandas.read_parquet(
    "derived/result.parquet",
    columns=["feature_id", "geometry"],
)
```

GeoPandas 1.2.0 write semantics:

- all geometry columns are preserved;
- default `geometry_encoding="WKB"` maximizes interoperability;
- default supported stable schema is **1.1.0**; request 1.0.0 explicitly for
  consumers that require the older metadata contract;
- `geometry_encoding="geoarrow"` requires GeoParquet 1.1.0, supports
  single-geometry native encodings, and is still described as experimental;
- `write_covering_bbox=True` adds a per-row `bbox` column and 1.1 covering
  metadata. It costs compute and may reveal precise extents;
- `schema_version` replaces

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

