---
id: sciref-database-lookup-materials-project
name: "Scientific Ref: Materials Project API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): Materials Project API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup materials project"
  - "materials project api"
keywords:
  - "database"
  - "lookup"
  - "materials"
  - "project"
  - "specialized"
  - "scientific"
  - "reference"
---

# Materials Project API

## Base URL

```
https://api.materialsproject.org
```

## Authentication

Requires a free API key. Register at https://materialsproject.org (free account).

| Env Variable | Header |
|---|---|
| `MP_API_KEY` | `X-API-KEY: your_key_here` |

Data endpoint requests must include the API key header. The client's
`GET /heartbeat` service check is unauthenticated.

## API Version

Use the current API at `api.materialsproject.org` with the `mp-api` client. The legacy API used `/rest/v2/`; that path is not the version label for the current API. The authoritative endpoint schema is https://api.materialsproject.org/openapi.json.

## Key Endpoints

### Search materials by formula or elements

```
GET /materials/summary/?formula=Fe2O3&_fields=material_id,formula_pretty,band_gap,formation_energy_per_atom
```

```
GET /materials/summary/?elements=Si,O&_fields=material_id,formula_pretty,band_gap
```

Query parameters:
- `formula` — exact chemical formula (e.g., `Fe2O3`, `SiO2`)
- `chemsys` — chemical system, dash-separated (e.g., `Fe-O`, `Li-Fe-P-O`)
- `elements` — comma-separated elements that must be present
- `band_gap_min` / `band_gap_max` — filter by band gap (eV)
- `is_stable` — `true` to return only thermodynamically stable phases
- `_fields` — comma-separated list of fields to return
- `_limit` — max results (default 100, max 1000)
- `_skip` — offset for pagination
- `_page` / `_per_page` — alternative page-based pagination, which takes
  precedence over `_limit` / `_skip`; `_per_page` defaults to 100 and is capped
  at 1000. Use one pagination style consistently.

### Get material by ID

```
GET /materials/summary/?material_ids=mp-149&_fields=material_id,formula_pretty,band_gap,formation_energy_per_atom,symmetry
```

Legacy material IDs such as `mp-149` remain accepted. The current schema also supports padded alphabetic AlphaIDs and `id_format=legacy|alpha`; preserve returned identifiers rather than validating only digits.

### Available fields (summary)

`material_id`, `formula_pretty`, `formula_anonymous`, `chemsys`, `volume`, `density`, `density_atomic`, `symmetry`, `band_gap`, `cbm`, `vbm`, `is_gap_direct`, `is_metal`, `is_magnetic`, `ordering`, `total_magnetization`, `formation_energy_per_atom`, `energy_above_hull`, `is_stable`, `equilibrium_reaction_energy_per_atom`, `nsites`, `elements`, `nelements`, `composition`, `structure`

### Crystal structure

```
GET /materials/summary/?material_ids=mp-149&_fields=structure
```

Returns the structure as a pymatgen-compatible JSON dict with lattice parameters and atomic sites.

### Elastic properties

```
GET /materials/elasticity/?material_ids=mp-149&_fields=material_id,bulk_modulus,shear_modulus,elastic_tensor
```

### Electronic structure (band structure / DOS)

The current schema has collection routes `/materials/electronic_structure/`,
`/materials/electronic_structure/bandstructure/` and `/materials/electronic_structure/dos/`,
not a material ID appended to those paths. Retrieve full band structures/DOS
through `MPRester.get_bandstructure_by_material_id()` or
`MPRester.get_dos_by_material_id()` with the current `mp-api` client. Version
0.46.5 resolves metadata and retrieves electronic-structure data from Delta
tables; do not reconstruct obsolete task/blob download URLs. These authenticated
examples are illustrative.

### Thermodynamic properties

```
GET /materials/thermo/?formula=Fe2O3&_fields=material_id,formation_energy_per_atom,energy_above_hull
```

### Example: Find stable oxides with band gap > 2 eV

```
GET /materials/summary/?elements=O&band_gap_min=2&is_stable=true&_fields=material_id,formula_pretty,band_gap,formation_energy_per_atom&_limit=10
```

## Response Format

```json
{
  "data": [
    {
      "material_id": "mp-149",
      "formula_pretty": "Si",
      "band_gap": 0.6105,
      "formation_energy_per_atom": 0.0
    }
  ],
  "meta": {
    "total_doc": 1
  }
}
```

## Rate Limits

- Official guidance describes limits starting at 25 requests/second, not a guaranteed account quota; honor HTTP 429 and returned retry guidance. See https://docs.materialsproject.org/downloading-data/using-the-api/tips-for-large-downloads.
- Batch requests preferred over many individual calls
- Use `_fields` to reduce payload size and improve performance
- The Python client `mp-api` handles pagination and retries automatically

## Error Format

```json
{
  "detail": "Not authenticated"
}
```

HTTP 401 indicates an authentication failure; HTTP 429 indicates rate limiting.
A collection search with no matching materials can return HTTP 200 with
`data: []`; do not require HTTP 404 to detect an empty result. The structure
convenience helper can return `None`, while band-structure/DOS helpers raise
`MPRestError` when required metadata or calculation data is absent. A 404 alone
does not distinguish an unknown route from missing data.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

