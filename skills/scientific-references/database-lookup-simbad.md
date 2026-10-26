---
id: sciref-database-lookup-simbad
name: "Scientific Ref: SIMBAD Astronomical Database (CDS Strasbourg)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): SIMBAD Astronomical Database (CDS Strasbourg)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup simbad"
  - "simbad astronomical database (cds strasbourg)"
keywords:
  - "database"
  - "lookup"
  - "simbad"
  - "specialized"
  - "scientific"
  - "reference"
---

# SIMBAD Astronomical Database (CDS Strasbourg)

SIMBAD contains data on astronomical objects beyond the Solar System, including identifications, coordinates, photometry, proper motions, parallaxes, radial velocities, spectral types, and bibliographic references.

## Base URLs

**TAP endpoint (recommended):**
```
https://simbad.cds.unistra.fr/simbad/sim-tap/sync
```

**Script interface:**
```
https://simbad.cds.unistra.fr/simbad/sim-script
```

**Simple query endpoints:**
```
https://simbad.cds.unistra.fr/simbad/sim-id
https://simbad.cds.unistra.fr/simbad/sim-coo
```

## Authentication

No API key required. All endpoints are public.

## Key Endpoints

### 1. TAP Queries (ADQL — recommended for programmatic use)

```
POST /simbad/sim-tap/sync
Content-Type: application/x-www-form-urlencoded

Parameters:
  REQUEST=doQuery
  LANG=ADQL
  QUERY=<adql query>
  FORMAT=json|votable|csv|tsv
  MAXREC=<max rows>
```

| Parameter | Type   | Description |
|-----------|--------|-------------|
| `REQUEST` | string | `doQuery` |
| `LANG`    | string | `ADQL` |
| `FORMAT`  | string | `json`, `votable`, `csv`, `tsv`. |
| `QUERY`   | string | **Required.** ADQL query. |
| `MAXREC`  | int    | Max rows returned. Always set to avoid downloading millions of rows. |

**Example — look up object by name:**
```
https://simbad.cds.unistra.fr/simbad/sim-tap/sync?request=doQuery&lang=adql&format=json&query=SELECT basic.OID, ra, dec, main_id, otype FROM basic JOIN ident ON oid = ident.oidref WHERE id = 'M31'
```

**Example — cone search (objects within 5 arcmin of coordinates):**
```
https://simbad.cds.unistra.fr/simbad/sim-tap/sync?request=doQuery&lang=adql&format=json&query=SELECT TOP 50 main_id, ra, dec, otype FROM basic WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 10.684, 41.269, 0.083)) = 1
```
Note: radius in CIRCLE is in degrees (5 arcmin = 0.083 deg).

**Example — objects by type (e.g., all pulsars):**
```
https://simbad.cds.unistra.fr/simbad/sim-tap/sync?request=doQuery&lang=adql&format=json&query=SELECT TOP 100 main_id, ra, dec, otype FROM basic WHERE otype = 'Psr'
```

### 2. Identifier Query (simple lookup)

```
GET /simbad/sim-id?Ident={name}&output.format=votable
```

| Parameter        | Type   | Description |
|------------------|--------|-------------|
| `Ident`          | string | **Required.** Object name (e.g., `M31`, `Sirius`, `NGC 1275`). |
| `output.format`  | string | `votable`, `html`. |

### 3. Coordinate Query

```
GET /simbad/sim-coo?Coord={coords}&Radius={radius}&Radius.unit={unit}&output.format=votable
```

| Parameter      | Type   | Description |
|----------------|--------|-------------|
| `Coord`        | string | **Required.** Coordinates, e.g., `10.684 +41.269` or `00 42 44 +41 16 09`. |
| `Radius`       | float  | Search radius. Default: 2. |
| `Radius.unit`  | string | `arcmin`, `arcsec`, `deg`. Default: `arcmin`. |
| `output.format`| string | `votable`, `html`. |

### 4. Script Interface (for multi-command queries)

```
POST /simbad/sim-script
Content-Type: application/x-www-form-urlencoded

Body: script=<script text>
```

A script consists of configuration lines followed by query commands:

```
output console=off script=off
format object "<format string>"
query id <object name>
```

**Query commands:**
- `query id <name>` — lookup by name (e.g., `query id M31`)
- `query coo <ra> <dec> radius=<value><unit>` — cone search (units: `d`=deg, `m`=arcmin, `s`=arcsec)
- `query id wildcard <pattern>` — wildcard search (e.g., `query id wildcard NGC 10*`)
- `query sample <criteria>` — criteria search (e.g., `query sample otype='*' & Vmag < 5.0`)

**Multi-object queries** — include multiple `query id` lines in a single script:
```
output console=off script=off
format object "%IDLIST(1) | %COO(s;A D;ICRS) | %OTYPE"
query id M31
query id M42
query id M101
```

## Script Format Codes

Format codes define which fields appear in script output. Use inside `format object "..."`.

### Identification

| Code | Description | Example Output |
|------|-------------|----------------|
| `%IDLIST(1)` | Primary identifier | `M  31` |
| `%IDLIST` | All identifiers | `M  31, NGC  224, UGC  454, ...` |
| `%MAIN_ID` | Main identifier | `M  31` |

### Coordinates

| Code | Description | Example Output |
|------|-------------|----------------|
| `%COO(s;A D;ICRS)` | RA Dec ICRS (sexagesimal) | `00 42 44.330 +41 16 07.50` |
| `%COO(d;A D;ICRS)` | RA Dec decimal degrees | `10.6847083 +41.2687500` |
| `%COO(d;A D;GAL)` | Galactic coordinates | `121.1743 -21.5733` |

### Object Properties

| Code | Description | Example Output |
|------|-------------|----------------|
| `%OTYPE` | Object type (short code) | `G` |
| `%SP` | Spectral type | `A1V` |
| `%MT` | Morphological type | `SA(s)b` |

### Photometry

| Code | Description |
|------|-------------|
| `%FLUXLIST(V)` | V-band magnitude |
| `%FLUXLIST(B)` | B-band magnitude |
| `%FLUXLIST(U,B,V,R,I)` | Multiple bands |
| `%FLUXLIST(J,H,K)` | Near-infrared bands |

### Kinematics

| Code | Description |
|------|-------------|
| `%PM` | Proper motion (mas/yr) |
| `%PLX` | Parallax (mas) |
| `%RV` | Radial velocity (km/s) |

### Predefined Format Levels

```
Basic:    "%IDLIST(1) | %COO(s;A D;ICRS) | %OTYPE"
Detailed: "%IDLIST(1) | %COO(s;A D;ICRS) | %OTYPE | %SP | %FLUXLIST(V)"
Full:     "%IDLIST(1) | %COO(s;A D;ICRS;J2000) | %OTYPE | %SP | %FLUXLIST(U,B,V,R,I,J,H,K) | %PM | %PLX | %RV | %MT"
```

## Key TAP Tables

### `basic` — Main Object Table

| Column | Type | Description |
|--------|------|-------------|
| `oid` | BIGINT | Internal object identifier (primary key) |
| `main_id` | VARCHAR | Primary object identifier |
| `ra` | DOUBLE | Right Ascension in degrees (ICRS) |
| `dec` | DOUBLE | Declination in degrees (ICRS) |
| `otype` | VARCHAR | Condensed object type code |
| `sp_type` | VARCHAR | Spectral type |
| `plx_value` | DOUBLE | Parallax in milliarcseconds |
| `plx_err` | DOUBLE | Parallax error |
| `pmra` | DOUBLE | Proper motion in RA (mas/yr) |
| `pmdec` | DOUBLE | Proper motion in Dec (mas/yr) |
| `rvz_radvel` | DOUBLE | Radial velocity (km/s) |
| `rvz_err` | DOUBLE | Radial velocity error |
| `galdim_majaxis` | DOUBLE | Galaxy major axis (arcmin) |
| `galdim_minaxis` | DOUBLE | Galaxy minor axis (arcmin) |
| `galdim_angle` | DOUBLE | Galaxy position angle (degrees) |

### `ident` — Identifier Table

| Column | Type | Description |
|--------|------|-------------|
| `oidref` | BIGINT | Reference to `basic.oid` |
| `id` | VARCHAR | Identifi

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

