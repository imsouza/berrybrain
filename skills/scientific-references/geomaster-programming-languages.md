---
id: sciref-geomaster-programming-languages
name: "Scientific Ref: Multi-Language Geospatial Programming"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (geomaster): Multi-Language Geospatial Programming"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "geomaster programming languages"
  - "multi-language geospatial programming"
keywords:
  - "geomaster"
  - "programming"
  - "languages"
  - "specialized"
  - "scientific"
  - "reference"
  - "multi"
  - "language"
---

# Multi-Language Geospatial Programming

Geospatial programming across R, Julia, JavaScript, C++, Java, Go, Rust and Python.
Reviewed 2026-10-01 against upstream sources listed below. These are illustrative
language-specific fragments, not compiled/executed cross-language coverage. Python
runtime coverage is recorded separately in [review.md](review.md).

## R Geospatial

### sf (Simple Features)

```r
library(sf)
library(dplyr)
library(ggplot2)

# Read spatial data
roads <- st_read("roads.shp")
zones <- st_read("zones.geojson")

# Basic operations
st_crs(roads)  # Check CRS
roads_utm <- st_transform(roads, 32610)  # Reproject

# Geometric operations
roads_buffer <- st_buffer(roads_utm, dist = 100)  # Buffer
roads_simplify <- st_simplify(roads_utm, dTolerance = 1)  # Simplify
roads_centroid <- st_centroid(roads)  # Centroid

# Spatial joins
joined <- st_join(roads, zones, join = st_intersects)

# Overlay
intersection <- st_intersection(roads, zones)

# Plot
ggplot() +
  geom_sf(data = zones, fill = NA) +
  geom_sf(data = roads, color = "blue") +
  theme_minimal()

# Calculate area
zones$area <- st_area(zones)  # sf returns units; geographic data can use geodesic/S2 area
zones$area_km2 <- units::set_units(st_area(zones), km^2)  # Convert to km2
```

### terra (Raster Processing)

```r
library(terra)

# Load raster
r <- rast("elevation.tif")

# Basic info
r
ext(r)  # Extent
crs(r)  # CRS
res(r)  # Resolution

# Raster calculations
slope <- terrain(r, v = "slope")
aspect <- terrain(r, v = "aspect")

# Multi-raster operations
ndvi <- (nir - red) / (nir + red)  # named, aligned, masked reflectance SpatRasters

# Focal operations
focal_mean <- focal(r, w = matrix(1, 3, 3), fun = mean)
focal_sd <- focal(r, w = matrix(1, 5, 5), fun = sd)

# Zonal statistics
zones <- vect("zones.shp")
zonal_mean <- extract(r, zones, fun = mean, na.rm = TRUE)

# Extract values at points
points <- vect("points.shp")
values <- extract(r, points)

# Write output
writeRaster(slope, "slope.tif", overwrite = TRUE)
```

### R Workflows

```r
# Complete land cover classification
library(sf)
library(terra)
library(randomForest)
library(caret)

# 1. Load data
training <- st_read("training.shp")
s2 <- rast("sentinel2.tif")

# 2. Extract training data
training_points <- st_centroid(training)
training_points <- st_transform(training_points, crs(s2))
values <- extract(s2, vect(training_points), ID = FALSE)

# 3. Combine with labels
df <- data.frame(values)
df$class <- as.factor(training$class_id)

# 4. Train model
set.seed(42)
# Use independently assigned spatial folds from the training table.
train_index <- which(training$fold != "holdout")
train_data <- df[train_index, ]
test_data <- df[-train_index, ]

rf_model <- randomForest(class ~ ., data = train_data, ntree = 100)

# 5. Predict
predicted <- predict(s2, model = rf_model)

# 6. Accuracy
conf_matrix <- confusionMatrix(predict(rf_model, test_data), test_data$class)
print(conf_matrix)

# 7. Export
writeRaster(predicted, "classified.tif", overwrite = TRUE)
```

## Julia Geospatial

### ArchGDAL.jl

```julia
using ArchGDAL

# Work inside the dataset lifetime; do not return borrowed feature geometries.
ArchGDAL.read("countries.shp") do dataset
    layer = ArchGDAL.getlayer(dataset, 0)
    for feature in layer
        geometry = ArchGDAL.getgeom(feature)
        println(ArchGDAL.toWKT(geometry))
    end
end

# Synthetic planar coordinates in chosen map units:
point = ArchGDAL.createpoint(0.0, 0.0)
buffered = ArchGDAL.buffer(point, 100.0)
```

GeoInterface defines interfaces; it is not a general constructor/geometry-operation
namespace. Use an actual geometry backend. Clone borrowed geometries if they must
outlive their owning dataset/feature.

### GeoStats.jl

```julia
using GeoStats
samples = georef((; value=[1., 2., 1.5]), [(0., 0.), (10., 0.), (5., 10.)])
grid = CartesianGrid(10, 10)
result = samples |> Interpolate(grid, model=Kriging(GaussianVariogram(range=10.)))
```

Current GeoStats uses interpolation transforms, not the former `SimulationProblem`
and `solve(OrdinaryKriging(...))` sketches. This uses synthetic Cartesian coordinates
and a chosen variogram, not a fitted geostatistical model. Fit/check an empirical
variogram, validate spatially and define units/support before a scientific result.

## JavaScript (Node.js & Browser)

### Turf.js (Browser/Node)

```javascript
// npm install @turf/turf
const turf = require('@turf/turf');

// Create features
const pt1 = turf.point([-122.4, 37.7]);
const pt2 = turf.point([-122.3, 37.8]);

// Distance (in kilometers)
const distance = turf.distance(pt1, pt2, { units: 'kilometers' });

// Buffer
const buffered = turf.buffer(pt1, 5, { units: 'kilometers' });

// Bounding box
const bbox = turf.bbox(buffered);

// Along a line
const line = turf.lineString([[-122.4, 37.7], [-122.3, 37.8]]);
const along = turf.along(line, 2, { units: 'kilometers' });

// Within
const points = turf.points([
  [-122.4, 37.7],
  [-122.35, 37.75],
  [-122.3, 37.8]
]);
const polygon = turf.polygon([[[-122.4, 37.7], [-122.3, 37.7], [-122.3, 37.8], [-122.4, 37.8], [-122.4, 37.7]]]);
const ptsWithin = turf.pointsWithinPolygon(points, polygon);

// Nearest point
const nearest = turf.nearestPoint(pt1, points);

// Area
const area = turf.area(polygon); // square meters

```

### Leaflet (Web Mapping)

```javascript
// Initialize map
const map = L.map('map').setView([37.7, -122.4], 13);

// Add tile layer
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Add GeoJSON layer
fetch('data.geojson')
  .then(response => response.json())
  .then(data => {
    L.geoJSON(data, {
      style: function(feature) {
        return { color: feature.properties.color };
      },
      onEachFeature: function(feature, layer) {
        const label = document.createElement('span');
        label.textContent = String(feature.properties.name ?? '');
        layer.bindPopup(label);
      }
    }).addTo(map);
  });

// Add markers
const marker = L.marker([37.7, -122.4]).addTo(map);
marker.bindPopup("Hello!").openPopup();

// Draw circles
const circle = L.circle([37.7, -122.4], {
  color: 'red',
  fillColor: '#f03',
  fillOpacity: 0.5,
  radius: 500
}).addTo(map);
```

## C++ Geospatial

### GDAL C++ API

```cpp
#include "gdal_priv.h"
#include "ogr_api.h"
#include "ogr_spatialref.h"
#include "ogrsf_frmts.h"
#include <stdexcept>

// Inside an application entry point, after GDALAllRegister():
// Open raster

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

