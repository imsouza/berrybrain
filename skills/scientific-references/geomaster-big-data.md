---
id: sciref-geomaster-big-data
name: "Scientific Ref: Big data and cloud geospatial computing"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (geomaster): Big data and cloud geospatial computing"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "geomaster big"
  - "big data and cloud geospatial computing"
keywords:
  - "geomaster"
  - "big"
  - "specialized"
  - "scientific"
  - "reference"
  - "cloud"
  - "geospatial"
---

# Big data and cloud geospatial computing

Core local array/storage recipes are tested. Remote clusters, cloud uploads and GPU
examples below are illustrative and require their own runtime/access. See [review.md](review.md).

## Dask-GeoPandas

```python
import dask_geopandas

points = dask_geopandas.read_file('points.gpkg', npartitions=5)
zones = dask_geopandas.read_file('zones.gpkg', npartitions=3)
if points.crs is None or zones.crs is None:
    raise ValueError('CRS must be known')
points = points.to_crs(zones.crs)
points = points.spatial_shuffle()
zones = zones.spatial_shuffle()
joined = points.sjoin(zones, how='inner', predicate='within')
result = joined.compute()
```

`spatial_shuffle` computes spatial partitioning; `set_index(calculate_spatial_partitions=True)`
is not that API. The current distributed spatial join supports inner joins. Its
result can multiply rows for overlapping zones. Perform area/buffer calculations only
after projecting to a justified metric CRS. Partition count alone is not a memory cap.

## Lazy rasters

Dask has no `array.from_rasterio`. Rioxarray constructs chunked arrays and manages file
access; do not close a Rasterio handle that deferred tasks still depend on.

```python
import rioxarray
import numpy as np

cube = rioxarray.open_rasterio('stack.tif', masked=True,
                             chunks={'band': 1, 'x': 1024, 'y': 1024})
# Caller has verified a common-grid four-band B02/B03/B04/B08 reflectance stack.
red, nir = cube.isel(band=2), cube.isel(band=3)
denominator = nir + red
ndvi = ((nir - red) / denominator).where(denominator != 0)
# Global reduction, not a different normalization for each chunk.
low, high = ndvi.min(skipna=True), ndvi.max(skipna=True)
normalized = ((ndvi - low) / (high - low)).where(high > low)
normalized.rio.to_raster('normalized.tif', dtype='float32')
cube.close()
```

Per-chunk min/max creates seams and changes the statistic with chunk layout. Focal
filters need a halo via `map_overlap` or equivalent. Cloud/nodata masks must be applied
before reductions. Clip early; `compute()` on the whole cube can exceed RAM.

Use `with Client(...)`/`with LocalCluster(...)` to close cluster resources. In scripts,
put process-based cluster creation under `if __name__ == '__main__':`. Do not serialize
open HDF5/GDAL handles into process workers; each task should open its own input.

## Cloud platforms

### Earth Engine

Use the SCL-mask template in [remote-sensing.md](remote-sensing.md). For a year,
`filterDate(f'{year}-01-01', f'{year+1}-01-01')` includes all days because the end is
exclusive. A valid-pixel mask goes to `updateMask(mask)`, not `updateMask(mask.Not())`.
Median mosaics are not guaranteed cloud-free and need QA/support inspection.
`ee.batch.Export.image.toDrive` requires image, region, scale/CRS and output settings;
starting the task writes to an external destination and may consume service quota.

### Planetary Computer / ODC

Search with a small bbox and `max_items`; use `list(search.items())`. `odc.stac.load`
accepts `chunks={'x': 1024, 'y': 1024}`, not `chunkx`/`chunky`. Supply the output bbox
as well as resolution to avoid loading full intersecting scenes. Inspect NAIP band
metadata rather than assuming a multi-band `image` asset becomes one scalar band.
Use a common `geobox` or `like=` when independent loads must align exactly. Calibration
and provider-specific asset names are described in the remote-sensing reference.

### S3 and Google Cloud Storage

Rasterio authentication sessions belong to `rasterio.Env`, not an `open(..., session=...)`
keyword. Prefer the environment's credential chain; do not embed keys.

```python
import rasterio
from rasterio.session import AWSSession

# Requires boto3 and existing authorized AWS credential configuration.
with rasterio.Env(AWSSession()):
    with rasterio.open('s3://your-bucket/path.tif') as src:
        subset = src.read(1, window=((0, 128), (0, 128)), masked=True)
```

GCS uses a `GSSession` and configured Google credentials in the same Env pattern.
`google.cloud.storage.Client().bucket(name).blob(key).upload_from_filename(path)`
performs an external upload; validate bucket/key/overwrite intent first. COG range
reads still incur requests/egress and may fail when SAS credentials expire mid-job.

## GPU paths (illustrative, not executed)

CuPy needs compatible GPU/CUDA software; transferring arrays can dominate small work.
Cast to floating point before subtraction and keep the same QA mask/denominator policy
as CPU processing. Do not normalize integer arrays in place.

cuSpatial's `point_in_polygon(points.geometry, polygons.geometry)` returns a boolean
point-by-polygon table, not a joined GeoDataFrame. For larger data use its documented
quadtree workflow. Both inputs need the same coordinate system; output indices require
explicit reconciliation. `join_polygon_points` is not the current documented API.

PyTorch datasets need `__len__`, `__getitem__`, aligned image/label grids and explicit
nodata label handling. Training batches require `optimizer.zero_grad(set_to_none=True)`.
Current AMP APIs are `torch.amp.GradScaler('cuda')` and
`torch.autocast(device_type='cuda')`; the older `torch.cuda.amp` namespace is deprecated.
Keep preprocessing, band order and normalization consistent across training/inference.
See [machine-learning.md](machine-learning.md) for spatial holdouts and tensor shapes.

## Storage

### COG

```python
from rasterio.shutil import copy as rio_copy
from rio_cogeo.cogeo import cog_validate
rio_copy('input.tif', 'output.tif', driver='COG', compress='DEFLATE',
         overview_resampling='NEAREST')  # categorical data; choose appropriately
valid, errors, warnings = cog_validate('output.tif')
assert valid, errors
```

The COG driver constructs the layout; tiled/compressed TIFF alone does not guarantee it.
Use average/bilinear only for suitable continuous data, nearest/mode for classes.
Create overviews as part of conversion. Updating the output afterward can break layout.

### Zarr / Xarray

```python
# ds is an Xarray Dataset with explicit chunks and spatial/time metadata.
ds.to_zarr('data.zarr', mode='w-', zarr_format=2, consolidated=True)
import xarray as xr
restored = xr.open_zarr('data.zarr', consolidated=True)
```

`w-` rejects an existing store; choose replacement explicitly. This selects v2 for
interoperability rather than depending on default format. Zarr 3 uses
`zarr.storage.LocalStore`, not the removed `DirectoryStore`. Verify dataset coordina

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

