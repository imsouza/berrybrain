---
id: sciref-geomaster-coordinate-systems
name: "Scientific Ref: Coordinate Reference Systems (CRS)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (geomaster): Coordinate Reference Systems (CRS)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "geomaster coordinate systems"
  - "coordinate reference systems (crs)"
keywords:
  - "geomaster"
  - "coordinate"
  - "systems"
  - "specialized"
  - "scientific"
  - "reference"
---

# Coordinate Reference Systems (CRS)

Coordinate-system reference, reviewed 2026-10-01 against PyProj/PROJ. Code with external data is illustrative. CRS names were checked against the installed PROJ database; a numerical round trip does not establish datum accuracy or grid availability.

## Table of Contents

1. [Fundamentals](#fundamentals)
2. [Common CRS Codes](#common-crs-codes)
3. [Projected vs Geographic](#projected-vs-geographic)
4. [UTM Zones](#utm-zones)
5. [Transformations](#transformations)
6. [Best Practices](#best-practices)

## Fundamentals

### What is a CRS?

A Coordinate Reference System defines how coordinates relate to positions on Earth:

- **Geographic CRS**: Uses angular latitude/longitude; usually degrees, but inspect axis units
- **Projected CRS**: Uses Cartesian coordinates (meters, feet)
- **Vertical CRS**: Defines height/depth (e.g., ellipsoidal heights)

### Components

1. **Datum**: Mathematical model of Earth's shape
   - WGS 84 (EPSG:4326) - Global GPS
   - NAD 83 (EPSG:4269) - North America
   - ETRS89 (EPSG:4258) - Europe

2. **Projection**: Transformation from curved to flat surface
   - Cylindrical (Mercator)
   - Conic (Lambert Conformal)
   - Azimuthal (Polar Stereographic)

3. **Units**: Degrees, meters, feet, etc.

## Common CRS Codes

### Geographic CRS (Lat/Lon)

| EPSG | Name | Area | Notes |
|------|------|------|-------|
| 4326 | WGS 84 | Global | GPS default, use for storage |
| 4269 | NAD83 | North America | USGS data, slightly different from WGS84 |
| 4258 | ETRS89 | Europe | European reference frame |
| 4283 | GDA94 | Australia | Australian datum |

### Projected CRS (Meters)

| EPSG | Name | Area | Distortion | Notes |
|------|------|------|------------|-------|
| 3857 | Web Mercator | Global (85°S-85°N) | High near poles | Web maps (Google, OSM) |
| 32601-32660 | UTM Zone N | 6° longitude zones | Check area of use | Metric calculations |
| 32701-32760 | UTM Zone S | 6° longitude zones | Check area of use | Southern hemisphere |
| 3395 | World Mercator | World | Increases toward poles | Conformal, not equal-area |
| 5070 | CONUS Albers | USA (conterminous) | Low | US national mapping |
| 2154 | Lambert-93 | France | Very low | French national projection |

### Regional Projections

**United States:**
- EPSG:5070 - NAD83 / Conus Albers
- EPSG:3338 - NAD83 / Alaska Albers
- ESRI:102003 - USA Contiguous Albers Equal Area
- EPSG:2227 - California Zone 3 (US Feet)

**Europe:**
- EPSG:3035 - Europe Equal Area 2001
- EPSG:3857 - Web Mercator (web mapping)
- EPSG:2154 - Lambert 93 (France)
- EPSG:25832-25836 - UTM zones (ETRS89)

**Other:**
- EPSG:3112 - GDA94 / Geoscience Australia Lambert (Australia)
- EPSG:2056 - CH1903+ / LV95 (Switzerland)
- EPSG:4326 - WGS 84 (global default)

## Projected vs Geographic

### When to Use Geographic (EPSG:4326)

✅ Storing data (databases, files)
✅ Global datasets
✅ Web APIs (GeoJSON, KML)
✅ Latitude/longitude queries
✅ GPS coordinates

```python
# Bad: Distance calculation in geographic CRS
# Assume gdf already has a verified geographic CRS
distance = gdf.geometry.length  # WRONG! Returns degrees, not meters

# Good: Calculate distance in projected CRS
gdf_projected = gdf.to_crs("EPSG:32633")  # UTM Zone 33N
distance_m = gdf_projected.geometry.length  # Correct: meters
```

### When to Use Projected

✅ Area/distance calculations
✅ Buffer operations
✅ Spatial analysis
✅ High-resolution mapping
✅ Engineering applications

```python
import geopandas as gpd

# Project to appropriate UTM zone
gdf = gdf.to_crs(gdf.estimate_utm_crs())

# Now area and distance are accurate
area_sqm = gdf.geometry.area
buffer_1km = gdf.geometry.buffer(1000)  # 1000 meters
```

### Web Mercator Warning

⚠️ **EPSG:3857 (Web Mercator) for visualization only**

```python
# DON'T use Web Mercator for area calculations
gdf_web = gdf.to_crs("EPSG:3857")
area = gdf_web.geometry.area  # WRONG! Significant distortion

# DO use appropriate projection
gdf_utm = gdf.to_crs("EPSG:32633")  # or estimate_utm_crs()
area = gdf_utm.geometry.area  # Correct
```

## UTM Zones

### Understanding UTM Zones

Earth is divided into 60 zones (6° longitude each):
- Zones 1-60: West to East
- Each zone divided into North (326xx) and South (327xx)

### Finding Your UTM Zone

```python
def get_utm_zone(longitude, latitude):
    """Nominal 6-degree zone only; special Norway/Svalbard zones need registry lookup."""
    import math

    if not (-180 <= longitude <= 180 and -80 <= latitude <= 84):
        raise ValueError('Outside the nominal UTM domain')
    zone = min(60, math.floor((longitude + 180) / 6) + 1)

    if latitude >= 0:
        epsg = 32600 + zone  # Northern hemisphere
    else:
        epsg = 32700 + zone  # Southern hemisphere

    return f"EPSG:{epsg}"

# Example
get_utm_zone(-122.4, 37.7)  # Returns 'EPSG:32610' (Zone 10N)
```

### Auto-Detect UTM Zone with GeoPandas

```python
import geopandas as gpd

# Load data
gdf = gpd.read_file('data.geojson')

# Estimate best UTM zone
utm_crs = gdf.estimate_utm_crs()
print(f"Best UTM CRS: {utm_crs}")

# Reproject
gdf_projected = gdf.to_crs(utm_crs)
```

### Special UTM Cases

**UPS (Universal Polar Stereographic):**
- EPSG:5041 - UPS North (Arctic)
- EPSG:5042 - UPS South (Antarctic)

**Other national grids (not UTM):**
- EPSG:31466-31469 - German Gauss-Krüger zones
- EPSG:2056 - Swiss LV95 (oblique Mercator)

## Transformations

### Basic Transformation

```python
from pyproj import Transformer

# Create transformer
transformer = Transformer.from_crs(
    "EPSG:4326",  # WGS 84 (lat/lon)
    "EPSG:32610", # UTM Zone 10N for this California point
    always_xy=True  # Input: x=lon, y=lat (not y=lat, x=lon)
)

# Transform single point
lon, lat = -122.4, 37.7
x, y = transformer.transform(lon, lat)
print(f"Easting: {x:.2f}, Northing: {y:.2f}")
```

### Batch Transformation

```python
import numpy as np
from pyproj import Transformer

# Arrays of coordinates
lon_array = [-122.4, -122.3]
lat_array = [37.7, 37.8]

transformer = Transformer.from_crs("EPSG:4326", "EPSG:32610", always_xy=True)
xs, ys = transformer.transform(lon_array, lat_array)
```

### Transformation with PyProj CRS

```python
from pyproj import CRS

# Get CRS information
crs = CRS.from_epsg(32633)

print(f"Name: {crs.name}")
print(f"Type: {crs.type_name}")
print(f"Area of use: {crs.area_of_use.name}")
print(f"Datum: {crs.datum.name}")
print(f"Ellipsoid: {crs.ellipsoid.name}")
```

## Best Practices

### 1. Always Know Your CRS

```python
imp

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

