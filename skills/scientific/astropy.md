---
id: sci-astropy
name: "Scientific: astropy"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Core Python library for astronomy and astrophysics workflows that need Astropy APIs, including units/quantities, coordinates, FITS I/O, tables, time systems, WCS, and cosmology. Use when implementing or debugging astronomical data analysis code with Astropy."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "astropy"
keywords:
  - "astropy"
  - "core"
  - "python"
  - "library"
  - "astronomy"
  - "astrophysics"
  - "workflows"
---

# Astropy

## Overview

Astropy is the core Python package for astronomy, providing essential functionality for astronomical research and data analysis. Use astropy for coordinate transformations, unit and quantity calculations, FITS file operations, cosmological calculations, precise time handling, tabular data manipulation, and astronomical image processing.

## When to Use This Skill

Use astropy when tasks involve:
- Converting between celestial coordinate systems (ICRS, Galactic, FK5, AltAz, etc.)
- Working with physical units and quantities (converting Jy to mJy, parsecs to km, etc.)
- Reading, writing, or manipulating FITS files (images or tables)
- Cosmological calculations (luminosity distance, lookback time, Hubble parameter)
- Precise time handling with different time scales (UTC, TAI, TT, TDB) and formats (JD, MJD, ISO)
- Table operations (reading catalogs, cross-matching, filtering, joining)
- WCS transformations between pixel and world coordinates
- Astronomical constants and calculations

## Quick Start

Targets Astropy 8.0.1. Numerical and small synthetic file examples were executed;
blocks using observation/catalog filenames, online services or a GUI are illustrative
and require those inputs. See [review evidence and sources](references/review.md).

```python
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
from astropy.io import fits
from astropy.table import Table
from astropy.cosmology import Planck18

# Units and quantities
distance = 100 * u.pc
distance_km = distance.to(u.km)

# Coordinates
coord = SkyCoord(ra=10.5*u.degree, dec=41.2*u.degree, frame='icrs')
coord_galactic = coord.galactic

# Time
t = Time('2023-01-15 12:30:00', scale='utc')
jd = t.jd  # Julian Date

# FITS files
data, header = fits.getdata('image.fits', ext=0, header=True)  # Select actual image HDU

# Tables
table = Table.read('catalog.fits')

# Cosmology
d_L = Planck18.luminosity_distance(1.0)
```

## Core Capabilities

### 1. Units and Quantities (`astropy.units`)

Handle physical quantities with units, perform unit conversions, and ensure dimensional consistency in calculations.

**Key operations:**
- Create quantities by multiplying values with units
- Convert between units using `.to()` method
- Perform arithmetic with automatic unit handling
- Use equivalencies for domain-specific conversions (spectral, doppler, parallax)
- Work with logarithmic units (magnitudes, decibels)

**See:** `references/units.md` for comprehensive documentation, unit systems, equivalencies, performance optimization, and unit arithmetic.

### 2. Coordinate Systems (`astropy.coordinates`)

Represent celestial positions and transform between different coordinate frames.

**Key operations:**
- Create coordinates with `SkyCoord` in any frame (ICRS, Galactic, FK5, AltAz, etc.)
- Transform between coordinate systems
- Calculate angular separations and position angles
- Match coordinates to catalogs
- Include distance for 3D coordinate operations
- Handle proper motions and radial velocities
- Query named objects from online databases

**See:** `references/coordinates.md` for detailed coordinate frame descriptions, transformations, observer-dependent frames (AltAz), catalog matching, and performance tips.

### 3. Cosmological Calculations (`astropy.cosmology`)

Perform cosmological calculations using standard cosmological models.

**Key operations:**
- Use built-in cosmologies (Planck18, WMAP9, etc.)
- Create custom cosmological models
- Calculate distances (luminosity, comoving, angular diameter)
- Compute ages and lookback times
- Determine Hubble parameter at any redshift
- Calculate density parameters and volumes
- Perform inverse calculations (find z for given distance)

**See:** `references/cosmology.md` for available models, distance calculations, time calculations, density parameters, and neutrino effects.

### 4. FITS File Handling (`astropy.io.fits`)

Read, write, and manipulate FITS (Flexible Image Transport System) files.

**Key operations:**
- Open FITS files with context managers
- Access HDUs (Header Data Units) by index or name
- Read and modify headers (keywords, comments, history)
- Work with image data (NumPy arrays)
- Handle table data (binary and ASCII tables)
- Create new FITS files (single or multi-extension)
- Use memory mapping for large files
- Access remote FITS files (S3, HTTP)

**See:** `references/fits.md` for comprehensive file operations, header manipulation, image and table handling, multi-extension files, and performance considerations.

### 5. Table Operations (`astropy.table`)

Work with tabular data with support for units, metadata, and various file formats.

**Key operations:**
- Create tables from arrays, lists, or dictionaries
- Read/write tables in multiple formats (FITS, CSV, HDF5, VOTable)
- Access and modify columns and rows
- Sort, filter, and index tables
- Perform database-style operations (join, group, aggregate)
- Stack and concatenate tables
- Work with unit-aware columns (QTable)
- Handle missing data with masking

**See:** `references/tables.md` for table creation, I/O operations, data manipulation, sorting, filtering, joins, grouping, and performance tips.

### 6. Time Handling (`astropy.time`)

Precise time representation and conversion between time scales and formats.

**Key operations:**
- Create Time objects in various formats (ISO, JD, MJD, Unix, etc.)
- Convert between time scales (UTC, TAI, TT, TDB, etc.)
- Perform time arithmetic with TimeDelta
- Calculate sidereal time for observers
- Compute light travel time corrections (barycentric, heliocentric)
- Work with time arrays efficiently
- Handle masked (missing) times

**See:** `references/time.md` for time formats, time scales, conversions, arithmetic, observing features, and precision handling.

### 7. World Coordinate System (`astropy.wcs`)

Transform between pixel coordinates in images and world coordinates.

**Key operations:**
- Read WCS from FITS headers
- Convert pixel coordinates to world coordinates (and vice versa)
- Calculate image footprints
- Access WCS parameters (reference pixel, projection, scale)
- Create custom WCS objects

**See:** `references/wcs_and_other_modules.md` for WCS operations and transformations.
High-level WCS pixel methods use zero-based `(x, y)` coordinates, while NumPy
images index `[row, column]`, or `[y, x]`. Use `world_to_array_index` for array
indexing, check bounds, and verify a pixel → world → pixel round trip before


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

