---
id: sciref-astropy-time
name: "Scientific Ref: Time Handling (astropy.time)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (astropy): Time Handling (astropy.time)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "astropy time"
  - "time handling (astropy.time)"
keywords:
  - "astropy"
  - "time"
  - "specialized"
  - "scientific"
  - "reference"
  - "handling"
---

# Time Handling (astropy.time)

The `astropy.time` module provides robust tools for manipulating times and dates with support for various time scales and formats.

## Creating Time Objects

### Basic Creation

```python
from astropy.time import Time
import astropy.units as u

# ISO format (automatically detected)
t = Time('2023-01-15 12:30:45')
t = Time('2023-01-15T12:30:45')

# Specify format explicitly
t = Time('2023-01-15 12:30:45', format='iso', scale='utc')

# Julian Date
t = Time(2460000.0, format='jd')

# Modified Julian Date
t = Time(59945.0, format='mjd')

# Unix time (seconds since 1970-01-01)
t = Time(1673785845.0, format='unix')
```

### Array of Times

```python
# Multiple times
times = Time(['2023-01-01', '2023-06-01', '2023-12-31'])

# From arrays
import numpy as np
jd_array = np.linspace(2460000, 2460100, 100)
times = Time(jd_array, format='jd')
```

## Time Formats

### Supported Formats

```python
# ISO 8601
t = Time('2023-01-15 12:30:45', format='iso')
t = Time('2023-01-15T12:30:45.123', format='isot')

# Julian dates
t = Time(2460000.0, format='jd')          # Julian Date
t = Time(59945.0, format='mjd')           # Modified Julian Date

# Decimal year
t = Time(2023.5, format='decimalyear')
t = Time(2023.5, format='jyear')          # Julian year
t = Time(2023.5, format='byear')          # Besselian year

# Year and day-of-year
t = Time('2023:046', format='yday')       # 46th day of 2023

# FITS format
t = Time('2023-01-15T12:30:45', format='fits')

# GPS seconds
t = Time(1000000000.0, format='gps')

# Unix time
t = Time(1673785845.0, format='unix')

# Matplotlib dates
t = Time(738521.0, format='plot_date')

# datetime objects
from datetime import datetime
dt = datetime(2023, 1, 15, 12, 30, 45)
t = Time(dt)
```

## Time Scales

### Available Time Scales

```python
# UTC - Coordinated Universal Time (default)
t = Time('2023-01-15 12:00:00', scale='utc')

# TAI - International Atomic Time
t = Time('2023-01-15 12:00:00', scale='tai')

# TT - Terrestrial Time
t = Time('2023-01-15 12:00:00', scale='tt')

# TDB - Barycentric Dynamical Time
t = Time('2023-01-15 12:00:00', scale='tdb')

# TCG - Geocentric Coordinate Time
t = Time('2023-01-15 12:00:00', scale='tcg')

# TCB - Barycentric Coordinate Time
t = Time('2023-01-15 12:00:00', scale='tcb')

# UT1 - Universal Time
t = Time('2023-01-15 12:00:00', scale='ut1')
```

### Converting Time Scales

```python
t = Time('2023-01-15 12:00:00', scale='utc')

# Convert to different scales
t_tai = t.tai
t_tt = t.tt
t_tdb = t.tdb
t_ut1 = t.ut1

# These are the same instant, so their elapsed-time difference is zero.
print((t.tai - t.utc).sec)  # 0.0
print(t.utc.iso, t.tai.iso)  # 12:00:00 UTC and 12:00:37 TAI on this date

# UTC contains leap seconds: this wall-clock interval spans two SI seconds.
before = Time("2016-12-31 23:59:59", scale="utc")
after = Time("2017-01-01 00:00:00", scale="utc")
print((after - before).to_value(u.s))  # approximately 2
```

## Format Conversions

### Change Output Format

```python
t = Time('2023-01-15 12:30:45')

# Access in different formats
print(t.jd)           # Julian Date
print(t.mjd)          # Modified Julian Date
print(t.iso)          # ISO format
print(t.isot)         # ISO with 'T'
print(t.unix)         # Unix time
print(t.decimalyear)  # Decimal year

# Change default format
t.format = 'mjd'
print(t)  # Displays as MJD
```

### High-Precision Output

```python
# Use subfmt for precision control
t.to_value('mjd', subfmt='float')    # Standard float
t.to_value('mjd', subfmt='long')     # Extended precision
t.to_value('mjd', subfmt='decimal')  # Decimal (highest precision)
t.to_value('mjd', subfmt='str')      # String representation
```

## Time Arithmetic

### TimeDelta Objects

```python
from astropy.time import TimeDelta

# Create time difference
dt = TimeDelta(1.0, format='jd')      # 1 day
dt = TimeDelta(3600.0, format='sec')  # 1 hour

# Subtract times
t1 = Time('2023-01-15')
t2 = Time('2023-02-15')
dt = t2 - t1
print(dt.jd)   # 31 days
print(dt.sec)  # 2678400 seconds
```

### Adding/Subtracting Time

```python
t = Time('2023-01-15 12:00:00')

# Add TimeDelta
t_future = t + TimeDelta(7, format='jd')  # Add 7 days

# Add Quantity
t_future = t + 1*u.hour
t_future = t + 30*u.day
t_future = t + 1*u.year

# Subtract
t_past = t - 1*u.week
```

A `u.day` is 86400 SI seconds and a `u.year` is a Julian year; neither
guarantees a fixed local wall-clock hour across UTC leap seconds or DST.

### Time Ranges

```python
# Create range of times
start = Time('2023-01-01', scale='utc')
end = Time('2023-12-31', scale='utc')
times = start + np.linspace(0, 1, 100) * (end - start)
# This includes both endpoints; 365 days after Jan 1 would reach Jan 1, 2024.
```

## Observing-Related Features

Some high-precision time and coordinate operations use IERS Earth-rotation data. Astropy uses `astropy-iers-data` by default, but may auto-download fresher IERS-A data when required for UT1 or polar-motion values. Disable auto-download for offline or privacy-sensitive runs:

```python
from astropy.utils import iers

iers.conf.auto_download = False
```

### Sidereal Time

```python
from astropy.coordinates import EarthLocation

# Define observer location
location = EarthLocation(lat=40*u.deg, lon=-120*u.deg, height=1000*u.m)

# Create time with location
t = Time('2023-06-15 23:00:00', location=location)

# Calculate sidereal time
lst_apparent = t.sidereal_time('apparent')
lst_mean = t.sidereal_time('mean')

print(f"Local Sidereal Time: {lst_apparent}")
```

### Light Travel Time Corrections

```python
from astropy.coordinates import SkyCoord, EarthLocation

# Define target and observer
target = SkyCoord(ra=10*u.deg, dec=20*u.deg)
# Synthetic site for a self-contained example; use surveyed coordinates in research.
location = EarthLocation(lat=40*u.deg, lon=-120*u.deg, height=1000*u.m)

# Observation times
times = Time(['2023-01-01', '2023-06-01', '2023-12-31'],
             location=location, scale='utc')

# Calculate light travel time to solar system barycenter
ltt_bary = times.light_travel_time(target, kind='barycentric')
ltt_helio = times.light_travel_time(target, kind='heliocentric')

# Apply correction
times_barycentric = times.tdb + ltt_bary
```

### Earth Rotation Angle

```python
# Earth rotation angle (for celestial to terrestrial transformations)
era = t.earth_rotation_angle()
```

For reproducible barycentric times, record the input scale, site, target frame/epoch
and ephemeris (`builtin` is the default).

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

