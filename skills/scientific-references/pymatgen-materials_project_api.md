---
id: sciref-pymatgen-materials-project-api
name: "Scientific Ref: Materials Project API: bounded queries, provenance, and computed-data limits"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pymatgen): Materials Project API: bounded queries, provenance, and computed-data limits"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pymatgen materials project api"
  - "materials project api: bounded queries, provenance, and computed-data limits"
keywords:
  - "pymatgen"
  - "materials"
  - "project"
  - "api"
  - "specialized"
  - "scientific"
  - "reference"
---

# Materials Project API: bounded queries, provenance, and computed-data limits

This reference targets `mp-api==0.46.5` (released 2026-08-18) with
`pymatgen==2026.9.24` and `pymatgen-core==2026.9.23`. `mp-api` requires Python
3.11+ and depends on `pymatgen>2024.2.20`.

Use the separate official client:

```python
from mp_api.client import MPRester
```

Do not use a legacy Materials Project client import from older pymatgen
examples.

Verification on 2026-09-30 used current official guides, the current OpenAPI
schema captured during this review, installed 0.46.5 SDK source and mocked
transports. A repeat OpenAPI request returned HTTP 403; protected endpoints were
not exercised with credentials. Network examples in
this reference are illustrative, not authenticated end-to-end tests.

## Installation

Pin the tested client and materials stack:

```bash
uv add "pymatgen==2026.9.24" "pymatgen-core==2026.9.23" "mp-api==0.46.5"
uv lock
uv sync --frozen
```

The 0.46.5 package metadata declares direct dependencies including
`pymatgen>2024.2.20`, `monty>=2024.12.10`, `emmet-core>=0.87.1`,
`requests>=2.23.0`, `orjson>=3.10,<4`, `pyarrow>=20`, and
`deltalake>=1.4,<1.6`, plus boto3 and typing extensions. A lockfile is needed
to freeze transitive artifacts.

## Authentication: one named secret

An API key is required and is available from the logged-in Materials Project
[dashboard](https://next-gen.materialsproject.org/dashboard).

The approved pattern is:

```python
from mp_api.client import MPRester

# Inject MP_API_KEY before execution; keep this workflow on the official host.
with MPRester(endpoint="https://api.materialsproject.org/") as rester:
    pass
```

Operational rules:

- use only the environment variable `MP_API_KEY`
- inject it through the user's shell/session secret manager
- never accept it as a command-line argument
- never embed it in code, notebooks, URLs, cache files, or manifests
- never traverse dot-env files or dump the environment
- never print the key or unredacted exceptions that might contain it
- do not send it anywhere except the official Materials Project API endpoint

The bundled query CLI follows these rules and reads the variable only after
`--execute`.

## Query contract before network

Before any request, disclose:

1. endpoint and `mp-api` version
2. all filters
3. exact response fields
4. `num_chunks`, `chunk_size`, and maximum serialized bytes
5. cache reads/writes
6. output path and no-overwrite behavior
7. API-key source by name, never value
8. data license, citation, provenance, and scientific limitations

The dry-run planner:

```bash
python scripts/mp_query.py \
  --chemsys Li-Fe-O \
  --energy-above-hull 0 0.05 \
  --fields formula_pretty,energy_above_hull,band_gap,origins \
  --limit 25
```

Only an explicit execution permits the disclosed network workflow:

```bash
python scripts/mp_query.py \
  --material-id mp-149 \
  --fields formula_pretty,structure,origins,last_updated \
  --limit 1 --output mp-149.json --execute
```

The CLI has no implicit result cache. The explicit bounded JSON output is the
reusable artifact. `MPRester` initialization performs compatibility and
heartbeat/database-version metadata requests before the bounded summary
search. The CLI discloses those requests, disables the platform-detail user
agent and local database-version notification log, and records the server's
database version.

The CLI pins `endpoint` explicitly so SDK endpoint configuration cannot redirect
its credential. Initialization makes separate unauthenticated `GET /heartbeat`
calls for server/emmet version, database version and controlled-dataset metadata.
Those calls do not use the session retry/timeout mechanism; apply a process
deadline for automation. If heartbeat is denied, the SDK may report an empty
database version; retain that limitation rather than invent a release.

## Summary searches

The official docs identify summary data as the main property overview for a
material:

```python
from mp_api.client import MPRester

with MPRester() as rester:
    docs = rester.materials.summary.search(
        material_ids=["mp-149", "mp-13"],
        fields=[
            "material_id",
            "formula_pretty",
            "energy_above_hull",
            "band_gap",
            "origins",
            "last_updated",
        ],
        all_fields=False,
        num_chunks=1,
        chunk_size=25,
    )
```

`material_ids` accepts one ID or a list in the current signature. Both numeric
IDs (`mp-149`) and alphabetical AlphaIDs (`mp-aaaaaaft`) are supported. The SDK
normalizes them through emmet; these two examples identify the same record.
Preserve the user's query and returned identifier instead of enforcing a
digits-only pattern. The result is a list of Pydantic document objects based
on `SummaryDoc`; selected-field results can use a reduced `MPDataDoc` model.

### Property filters

Verified public `SummaryRester.search` parameters include:

```python
with MPRester() as rester:
    docs = rester.materials.summary.search(
        chemsys="Li-Fe-O",
        elements=["Li", "O"],
        exclude_elements=["F"],
        energy_above_hull=(0.0, 0.05),
        band_gap=(0.5, 3.0),
        is_stable=None,
        fields=["material_id", "formula_pretty", "energy_above_hull", "band_gap"],
        all_fields=False,
        num_chunks=1,
        chunk_size=25,
    )
```

Other current filters include formula, crystal system, density, deprecation,
dielectric ranges, elastic ranges, metal/direct-gap flags, property
availability, magnetic ordering, element/site counts, space group, theoretical
status, energy ranges, volume, and surface-property ranges. Consult the exact
installed signature instead of passing guessed keywords.

`exclude_elements` is a list of element symbols; it is not a Boolean flag.

`available_fields` lists fields the endpoint can return. It does not mean every
field is a valid filter:

```python
with MPRester() as rester:
    returnable_fields = rester.materials.summary.available_fields
```

Requesting all fields is the documented default and can be expensive. Always
pass a short `fields` list and bound chunks.

The REST search is a `GET /materials/summary/` with `x-api-key` authentication
and URL query parameters, not a JSON POST. The SDK joins lists (for example
`material_ids`, `elements`, `exclude_elements`) with commas and expands range
tuples to endpoint-specific `_min`/`_max` parameters. Responses contain a
`data` array and `meta.total_doc`; 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

