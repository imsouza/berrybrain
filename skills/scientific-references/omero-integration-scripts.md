---
id: sciref-omero-integration-scripts
name: "Scientific Ref: Bundled Helpers and OMERO.server Scripts"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (omero-integration): Bundled Helpers and OMERO.server Scripts"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "omero integration scripts"
  - "bundled helpers and omero.server scripts"
keywords:
  - "omero"
  - "integration"
  - "scripts"
  - "specialized"
  - "scientific"
  - "reference"
  - "bundled"
---

# Bundled Helpers and OMERO.server Scripts

The local files in this skill's `scripts/` directory are client-side safety
helpers. They are not OMERO.server scripts and are never uploaded
automatically.

## Shared Safety Model

Every bundled executable:

- uses `argparse`;
- supports `--help` without OMERO installed;
- imports `omero` only after argument parsing and only for `--execute`;
- reads only named `OMERO_*` variables;
- never loads `.env`;
- never accepts or prints a password/session key;
- defaults to local validation or dry-run output;
- applies hard limits;
- refuses unsafe output collisions/symlinks;
- closes remote connections in `finally`.

Remote helpers require `--execute`. That flag authorizes a read-only
connection, not broader scope or mutation.

## Local Endpoint Validation

```bash
python -B scripts/validate_config.py
python -B scripts/validate_config.py --require-auth --json
```

By default it performs only local syntax checks. `--resolve-host` performs DNS
resolution but does not connect to an OMERO port.

Output reports which named variables are present and the authentication mode.
It never displays credential values.

Examples of failures:

- host contains `http://`, a path, whitespace, or a leading hyphen;
- port is not in `1..65535`;
- `OMERO_SECURE` is not a recognized boolean;
- only one of `OMERO_USER`/`OMERO_PASSWORD` is present;
- `--require-auth` is used without either a session key or complete password
  authentication.

## Read-Only Inventory

Dry run:

```bash
python -B scripts/inventory.py \
  --object-type Image \
  --limit 50 \
  --page-size 25
```

Execute after reviewing endpoint/group/scope:

```bash
python -B scripts/inventory.py \
  --object-type Image \
  --limit 50 \
  --page-size 25 \
  --group-id 42 \
  --execute \
  --output ./image-inventory.json
```

Properties:

- allowlisted object types only;
- overall cap at 1000 and page cap at 200;
- stable `obj.id` ordering request;
- one optional explicit group, never cross-group `-1`;
- object names redacted unless `--include-names`;
- JSON output written atomically with owner-only permissions;
- existing output refused unless `--overwrite`.

`limit_reached` means the requested cap was filled; it does not assert that
more server rows exist.

## Annotation and ROI Export

Dry run:

```bash
python -B scripts/export_image_metadata.py \
  --image-id 101 \
  --image-id 102 \
  --max-annotations-per-image 100 \
  --max-rois-per-image 100 \
  --max-shapes-per-roi 500 \
  --output ./selected-image-metadata.json
```

Execute:

```bash
python -B scripts/export_image_metadata.py \
  --image-id 101 \
  --image-id 102 \
  --group-id 42 \
  --execute \
  --output ./selected-image-metadata.json
```

Default redactions:

- annotation values
- owner names
- FileAnnotation filenames
- ROI/shape labels
- mask bytes

Optional inclusion flags are independent. The helper never retrieves pixels or
FileAnnotation bytes. It uses the currently documented `IRoi.findByImage`
pattern and records that `IRoi` is deprecated.

Because `findByImage` has no page argument, the ROI caps bound serialization
but not server-side assembly. `listAnnotations()` likewise loads annotations
and values before local caps/redaction. ROI mask payloads can arrive in the
service response even though their bytes are excluded from JSON. Do not run it on a known extreme image
without reviewing the ROI count or using a site-approved paginated API.

## Import/Export Planner

The planner is always local and has no `--execute`.

Import scan plan:

```bash
python -B scripts/plan_transfer.py import \
  --target Dataset:id:42 \
  --max-files 100 \
  --scan-depth 4 \
  ./explicit-input
```

It walks only explicit paths, does not follow directory symlinks, caps depth
and file count, and proposes `omero import --depth N -f` plus a future import
using the same depth. A depth cutoff or skipped symlink prevents marking the
plan ready. Bio-Formats may discover related files beyond the local scan, so
review the actual `-f` fileset list before importing. Local file counts are
estimates, not an importer file limit. The planner invokes neither command.

Per-image export plan:

```bash
python -B scripts/plan_transfer.py export \
  --format ome-tiff \
  --output-dir ./reviewed-existing-directory \
  Image:101 Image:102
```

It accepts explicit `Image:<id>` selectors only, proposes one output per image,
and reports collisions. Dataset iteration is intentionally excluded because
the official export mode is experimental and too easy to broaden.

Global `--output` and `--overwrite` arguments must precede the subcommand:

```bash
python -B scripts/plan_transfer.py \
  --output ./transfer-plan.json \
  import ./explicit-input
```

No proposed command includes `-w`, `--password`, `-k`, or a session value.

## Running Local Tests

No real OMERO server is needed:

```bash
uv run --with pytest python -m pytest tests/omero-integration -q
python tests/run_all.py --isolated omero-integration
```

The tests use temporary directories and fake gateway objects.

## OMERO.server Script Model

OMERO.server scripts are Python plugins registered with the Script Service.
Clients can launch them and receive typed outputs. Inputs often include an
explicit data type, object IDs, thresholds, or options.

A minimal structure:

```python
import omero
import omero.scripts as scripts
from omero.gateway import BlitzGateway
from omero.rtypes import rlong, rstring


def main():
    client = scripts.client(
        "Bounded_Image_Summary.py",
        "Returns IDs for an explicit bounded image list.",
        scripts.List(
            "Image_IDs",
            optional=False,
            description="Explicit image IDs (maximum enforced by script)",
        ).ofType(rlong(0)),
        namespaces=[omero.constants.namespaces.NSDYNAMIC],
        version="1.0",
    )

    try:
        inputs = client.getInputs(unwrap=True)
        image_ids = list(inputs["Image_IDs"])
        if not 1 <= len(image_ids) <= 25:
            raise ValueError("Image_IDs must contain 1..25 IDs")

        conn = BlitzGateway(client_obj=client)
        found = []
        for image_id in image_ids:
            image = conn.getObject("Image", image_id)
            if image is not None:
                found.append(image.getId())

        client.setOutput("Message", rstring(f"Found {len(found)} images"))
    finally:
        client.closeSession()


if __name__ == "__main__":
    main()
```

The script session is supplied by OM

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

