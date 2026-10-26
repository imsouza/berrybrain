---
id: sciref-geopandas-crs-management
name: "Scientific Ref: CRS, units, and reprojection"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (geopandas): CRS, units, and reprojection"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "geopandas crs management"
  - "crs, units, and reprojection"
keywords:
  - "geopandas"
  - "crs"
  - "management"
  - "specialized"
  - "scientific"
  - "reference"
  - "units"
  - "reprojection"
---

# CRS, units, and reprojection

A CRS is part of the data model, not display metadata. An incorrect or missing
CRS can make numerically plausible results geographically wrong.

## Require authoritative CRS metadata

```python
from pyproj import CRS

if gdf.crs is None:
    raise ValueError("CRS is missing; recover it from authoritative source metadata")

crs = CRS.from_user_input(gdf.crs)
```

Do not infer EPSG:4326 because values resemble longitude/latitude. Coordinate
ranges are not evidence of datum, axis interpretation, units, or epoch.

### `set_crs` versus `to_crs`

```python
# Assign metadata only; coordinate numbers do not change.
gdf = gdf.set_crs("EPSG:4326")

# Transform coordinates; the source CRS must already be set.
projected = gdf.to_crs("EPSG:32631")
```

- Use `set_crs()` only when the coordinate values are already expressed in that
  CRS and metadata is absent or demonstrably wrong.
- Replacing existing metadata requires `allow_override=True`; record why.
- Use `to_crs()` to transform the active geometry column. Transform each
  additional geometry column explicitly.
- Do not assign `gdf.crs = ...`; manual override is deprecated.

## Axis order

EPSG definitions can be latitude/longitude while GIS coordinate arrays are
normally x/y (longitude/latitude). Inspect the authority axes:

```python
for axis in crs.axis_info:
    print(axis.name, axis.abbrev, axis.direction, axis.unit_name)
```

For explicit pyproj transformations, request traditional GIS x/y order:

```python
from pyproj import Transformer

transformer = Transformer.from_crs(
    source_crs,
    target_crs,
    always_xy=True,
    allow_ballpark=False,
    only_best=True,
)
x_out, y_out = transformer.transform(x_in, y_in, errcheck=True)
```

Record `always_xy=True`; it changes the API coordinate order, not the CRS
definition. GeoParquet 1.1 explicitly stores WKB/native coordinates as x/y even
when the CRS authority uses another axis order.

## Units and planar operations

GeoPandas and Shapely compute planar Cartesian geometry and ignore Z:

- geographic longitude/latitude axes are angular, usually degrees;
- projected axes may be metres, US survey feet, feet, or another linear unit;
- `.area` returns squared coordinate units;
- `.length`, `.distance`, `.buffer`, `sjoin_nearest(max_distance=...)`,
  `sjoin(predicate="dwithin", distance=...)`, precision grids, simplify
  tolerances, and gap widths use coordinate units.

```python
axis_units = [(axis.unit_name, axis.unit_conversion_factor) for axis in crs.axis_info]
if crs.is_geographic:
    raise ValueError("Planar measurement on angular coordinates is not accepted")
```

Do not label an output metres merely because a CRS is projected. Convert units
using the CRS axis metadata and document the conversion. Web Mercator
(`EPSG:3857`) is for web display, not general area/distance analysis.

### Choosing a measurement CRS

Choose based on the operation, study extent, datum, and required accuracy:

- local UTM or another local conformal CRS for local distances/angles;
- an equal-area CRS for area totals and areal normalization;
- an equidistant/azimuthal design for a specified distance origin;
- geodesic methods for large/global geographic extents.

`estimate_utm_crs()` is a convenience based on dataset bounds, not a proof of
suitability. It can be poor for multi-zone, polar, antimeridian-crossing, or
very large datasets.

## Geodesic measurements

When projection distortion is unacceptable, use the ellipsoid associated with
the CRS through `pyproj.Geod`, not Shapely's planar distance:

```python
geod = crs.get_geod()
azimuth_fwd, azimuth_back, metres = geod.inv(lon1, lat1, lon2, lat2)
area_m2, perimeter_m = geod.geometry_area_perimeter(polygon)
```

Ensure inputs are longitude/latitude on the intended geodetic datum. Geodesic
area is signed according to ring orientation and has documented limitations for
very large polygons; normalize orientation and test known controls.

## Datum transformations and operation selection

The same source/target CRS pair can have several operations. Selection depends
on area of interest, installed grids, authority, and accuracy:

```python
from pyproj.aoi import AreaOfInterest
from pyproj.transformer import TransformerGroup
from pyproj import network

network.set_network_enabled(False)
group = TransformerGroup(
    source_crs,
    target_crs,
    always_xy=True,
    area_of_interest=AreaOfInterest(west, south, east, north),
    allow_ballpark=False,
)

if not group.best_available or not group.transformers:
    raise RuntimeError("Best transformation unavailable; inspect missing grids")

candidate = group.transformers[0]
print(candidate.description, candidate.accuracy, candidate.area_of_use)
```

`AreaOfInterest` always takes geographic longitude/latitude **degrees**, never
projected metres/feet. The bundled planner accepts `--bbox` only for a source
CRS with geographic degree axes; omit it for projected sources. Its bounds and
transform descriptions are planning metadata, not transformed coordinates.

Privacy note: an exact area of interest can reveal a sensitive study location.
Do not log it; retain only an approved coarse region or protected audit record.

Operational rules:

1. Set `allow_ballpark=False` for accuracy-sensitive work.
2. Use `only_best=True` with `Transformer.from_crs()` when failure is preferable
   to silently selecting a lower-quality operation.
3. Verify `accuracy` (`-1` means unknown) and `area_of_use`.
4. Inspect `TransformerGroup.unavailable_operations` for missing grids.
5. Keep PROJ network disabled by default. pyproj wheels do not include all
   transformation grids; downloading grids is a separate, explicit network and
   supply-chain action.
6. Record PROJ database/native versions and the selected operation description.
7. For dynamic CRS, record coordinate epoch. A CRS alone may be insufficient.

The bundled `scripts/crs_reprojection_plan.py` performs this inspection without
transforming coordinates or enabling network access.

## Geometry transformation caveat

`GeoDataFrame.to_crs()` transforms every existing vertex. It does not interpret
a segment as a geodesic arc:

```python
out = gdf.to_crs(target_crs)
```

If source linework is sparse, densify according to a documented geodesic or
source-space tolerance before projection when shape fidelity matters. Validate
the resulting topology and bounds.

## Antimeridian and projection boundaries

`to_crs()` warns that objects crossing the dateline

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

