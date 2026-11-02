---
id: sciref-astropy-wcs-and-other-modules
name: "Scientific Ref: WCS and Other Astropy Modules"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (astropy): WCS and Other Astropy Modules"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "astropy wcs other modules"
  - "wcs and other astropy modules"
keywords:
  - "astropy"
  - "wcs"
  - "other"
  - "modules"
  - "specialized"
  - "scientific"
  - "reference"
---

# WCS and Other Astropy Modules

## World Coordinate System (astropy.wcs)

The WCS module manages transformations between pixel coordinates in images and world coordinates.
Examples here assume a two-dimensional celestial WCS. Cubes can return multiple
world objects; inspect `world_axis_physical_types` and select/slice axes explicitly.
High-level methods use zero-based `(x, y)` pixels; NumPy indexes `(row, column)`
or `(y, x)`. FITS `CRPIX` remains one-based. Low-level `all_pix2world` and
`all_world2pix` require explicit `origin=0` or `1`. Preserve distortion HDUs
with `WCS(header, fobj=hdul)` where needed and check warnings and round trips.
User-file and GUI snippets are illustrative; synthetic numerical coverage is
listed in [review evidence](review.md).

### Reading WCS from FITS

```python
from astropy.wcs import WCS
from astropy.io import fits

# Read WCS from FITS header
with fits.open('image.fits') as hdul:
    wcs = WCS(hdul[0].header)
```

### Pixel to World Transformations

```python
# Single pixel to world coordinates
world = wcs.pixel_to_world(100, 200)  # Returns SkyCoord
print(f"RA: {world.ra}, Dec: {world.dec}")

# Arrays of pixels
import numpy as np
x_pixels = np.array([100, 200, 300])
y_pixels = np.array([150, 250, 350])
world_coords = wcs.pixel_to_world(x_pixels, y_pixels)
```

### World to Pixel Transformations

```python
from astropy.coordinates import SkyCoord
import astropy.units as u

# Single coordinate
coord = SkyCoord(ra=10.5*u.degree, dec=41.2*u.degree)
x, y = wcs.world_to_pixel(coord)

# Array of coordinates
coords = SkyCoord(ra=[10, 11, 12]*u.degree, dec=[41, 42, 43]*u.degree)
x_pixels, y_pixels = wcs.world_to_pixel(coords)
```

### WCS Information

```python
# Print WCS details
print(wcs)

# Access key properties
print(wcs.wcs.crpix)  # Reference pixel
print(wcs.wcs.crval)  # Reference value (world coords)
print(wcs.pixel_scale_matrix)  # Works with either CD or PC/CDELT representation
print(wcs.wcs.ctype)  # Coordinate types

# Pixel scale
pixel_scale = wcs.proj_plane_pixel_scales()  # List of axis Quantities at CRPIX
# Projection-plane scales are not a global angular scale for a distorted image.
```

### Creating WCS

```python
from astropy.wcs import WCS

# Create new WCS
wcs = WCS(naxis=2)
wcs.wcs.crpix = [512.0, 512.0]  # One-based; reference is pixel (511, 511) here
wcs.wcs.crval = [10.5, 41.2]     # RA, Dec at reference pixel
wcs.wcs.ctype = ['RA---TAN', 'DEC--TAN']  # Projection type
wcs.wcs.cdelt = [-0.0001, 0.0001]  # Pixel scale (degrees/pixel)
wcs.wcs.cunit = ['deg', 'deg']
wcs.array_shape = (1024, 1024)  # (rows, columns), needed for footprint/bounds
```

### Footprint and Coverage

```python
# Calculate image footprint (corner coordinates)
footprint = wcs.calc_footprint()
# Returns [RA, Dec] corners for this celestial WCS; shape must be known.

# Round trip and safe array indexing
world = wcs.pixel_to_world(511, 511)
x, y = wcs.world_to_pixel(world)
assert np.allclose([x, y], [511, 511], atol=1e-7)
row, col = wcs.world_to_array_index(world)
assert 0 <= row < wcs.array_shape[0] and 0 <= col < wcs.array_shape[1]
```

## NDData (astropy.nddata)

Container for n-dimensional datasets with metadata, uncertainty, and masking.

### Creating NDData

```python
from astropy.nddata import NDData
import numpy as np
import astropy.units as u

# Basic NDData
data = np.random.random((100, 100))
ndd = NDData(data)

# With units
ndd = NDData(data, unit=u.electron/u.s)

# With an illustrative uncertainty array; replace with a calibrated noise model.
# sqrt(data) is not a general uncertainty model for calibrated rates.
from astropy.nddata import StdDevUncertainty
uncertainty = StdDevUncertainty(np.sqrt(data))
ndd = NDData(data, uncertainty=uncertainty, unit=u.electron/u.s)

# With mask
mask = data < 0.1  # Mask low values
ndd = NDData(data, mask=mask)

# With WCS
from astropy.wcs import WCS
ndd = NDData(data, wcs=wcs)
```

### CCDData for CCD Images

```python
from astropy.nddata import CCDData

# Create CCDData
ccd = CCDData(data, unit=u.adu, meta={'object': 'M31'})

# Read from FITS
ccd = CCDData.read('image.fits', unit=u.adu)

# Write to FITS
ccd.write('output.fits', overwrite=True)
```

## Modeling (astropy.modeling)

Framework for creating and fitting models to data.

### Common Models

```python
from astropy.modeling import models, fitting
import numpy as np

# 1D Gaussian
gauss = models.Gaussian1D(amplitude=10, mean=5, stddev=1)
x = np.linspace(0, 10, 100)
y = gauss(x)

# 2D Gaussian
gauss_2d = models.Gaussian2D(amplitude=10, x_mean=50, y_mean=50,
                              x_stddev=5, y_stddev=3)

# Polynomial
poly = models.Polynomial1D(degree=3)

# Power law
power_law = models.PowerLaw1D(amplitude=10, x_0=1, alpha=2)
```

### Fitting Models to Data

```python
# Generate noisy data
true_model = models.Gaussian1D(amplitude=10, mean=5, stddev=1)
x = np.linspace(0, 10, 100)
y_true = true_model(x)
rng = np.random.default_rng(42)
y_noisy = y_true + rng.normal(0, 0.5, x.shape)

# Fit model
fitter = fitting.TRFLSQFitter()  # Current recommended bounded nonlinear fitter
initial_model = models.Gaussian1D(amplitude=8, mean=4, stddev=1.5)
fitted_model = fitter(initial_model, x, y_noisy)

print(f"Fitted amplitude: {fitted_model.amplitude.value}")
print(f"Fitted mean: {fitted_model.mean.value}")
print(f"Fitted stddev: {fitted_model.stddev.value}")
```

### Compound Models

```python
# Add models
double_gauss = models.Gaussian1D(amplitude=5, mean=3, stddev=1) + \
               models.Gaussian1D(amplitude=8, mean=7, stddev=1.5)

# Compose models
composite = models.Gaussian1D(amplitude=10, mean=5, stddev=1) | \
            models.Scale(factor=2)  # Scale output
```

## Visualization (astropy.visualization)

Tools for visualizing astronomical images and data.

### Image Normalization

```python
from astropy.visualization import simple_norm
import matplotlib.pyplot as plt

# Load image
from astropy.io import fits
data = fits.getdata('image.fits')

# Normalize for display
norm = simple_norm(data, 'sqrt', percent=99)

# Display
plt.imshow(data, norm=norm, cmap='gray', origin='lower')
plt.colorbar()
plt.show()
```

Check finite pixels and `vmin <= vmax` before plotting. Nearly constant images
can produce degenerate ZScale limits; use an explicit scientifically appropriate
display range in that case. Display normalization never calibrates the data.

### Stretching and Intervals

```python
from astropy.visualization import (MinMaxInterval, AsinhStretch,
           

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

