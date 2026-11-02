---
id: sci-omero-integration
name: "Scientific: omero-integration"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Inspects and automates microscopy data workflows against OMERO.server with omero-py, BlitzGateway, OMERO CLI, tables, annotations, ROIs, rendering, and documented OMERO.web APIs. Use this skill for scoped OMERO inventory, metadata export, import/export planning, or reviewed write"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "omero integration"
  - "omero-integration"
keywords:
  - "omero"
  - "integration"
  - "inspects"
  - "automates"
  - "microscopy"
  - "workflows"
  - "against"
---

# OMERO Integration

Use current OME documentation and the smallest explicit data scope. OMERO data
may contain unpublished images, identifiers, annotations, original files, and
derived measurements.

## Verified Baseline

This skill was refreshed on **2026-09-30**:

- **OMERO.server 5.6.18** (May 2026) is the current documented stable server.
- It was tested by OME with **OMERO.py/omero-py 5.22.1** and
  **OMERO.web 5.31.0**.
- `omero-py==5.22.1` requires Python 3.10 or newer. The OMERO support matrix
  supports 3.10 and 3.11, recommends 3.12, and still labels 3.13/3.14
  “upcoming.”
- OMERO 5.6 uses **IcePy 3.6**, with 3.6.5 prebuilt client wheels documented
  for Python versions through 3.12.

**Latest client releases:** OMERO.py **5.23.0** (2026-07-30) and OMERO.web
**5.33.2** are newer than the server history’s tested pairing. The bundled
helpers were checked locally with OMERO.py 5.22.1 and 5.23.0, IcePy 3.6.5,
and Python 3.12; this did not connect to an OMERO server. Remote snippets in this skill
and its references are illustrative, verified against official docs/source,
and require adaptation to an authorized server and its object IDs.

The pin above is a reproducible skill snapshot, not a promise that every
OMERO.server release accepts that client. For another server version, consult
its release entry and use the OMERO.py version tested with it. See
[`references/sources.md`](references/sources.md).

## Operating Contract

1. Start with local validation or a dry run. Do not connect until the user has
   selected the host, group, object type, IDs, and result limit.
2. Read credentials only from the named `OMERO_*` variables in the frontmatter.
   Never search parent directories or load `.env` files.
3. Never place a password or session key in command arguments, source code,
   output JSON, logs, tracebacks, or chat. A session key is a bearer credential.
4. Default to `secure=True`. OMERO encrypts login by default, but post-login
   data and the session ID may otherwise travel unencrypted. `secure=True` does
   not by itself guarantee certificate hostname verification.
5. Bound every list, page, ROI, shape, annotation, table row, pixel plane, and
   local file scan. Do not turn an object request into a group-wide or
   cross-group export without explicit approval.
6. Treat all writes separately: annotation/link creation, rendering-default
   saves, image creation, imports, script uploads, table writes, ownership or
   group changes, and deletion require an exact reviewed target.
7. Close `BlitzGateway`, table handles, raw stores, thumbnail stores, rendering
   engines, script clients, and other stateful services in `finally` blocks or
   documented context-manager patterns.
8. Never connect to a real server merely to “test” examples.

## Choose the Interface

- **BlitzGateway (`omero-py`)**: primary Python client for object traversal,
  pixels, annotations, ROIs, rendering, and services.
- **OMERO CLI**: sessions, import scanning/import, OME-TIFF or XML export,
  scripts, and administrative plugins. Most client commands are remote; import
  also needs the matching server-side Java libraries through `OMERODIR`.
- **OMERO.web `api` and `webgateway`**: the only OMERO.web apps that official
  documentation calls stable public APIs. The documented JSON API is
  version-discovered and has limited object coverage; it is not evidence that
  every webclient URL is a supported REST endpoint.
- **OMERO.server scripts**: uploaded plugins executed by server infrastructure.
  They are different from the bundled local client helpers in `scripts/`.

## Install a Reproducible Client

Create a Python 3.12 environment:

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
```

Install the exact IcePy 3.6.5 wheel matching the interpreter, OS, architecture,
and wheel tags, then OMERO.py:

```bash
# Download the matching 3.6.5 wheel from the official OMERO-linked matrix.
uv pip install "/absolute/path/to/zeroc_ice-3.6.5-<matching-tags>.whl"
uv pip install "omero-py==5.22.1"
```

Do not substitute Ice 3.7: the OMERO 5.6 support matrix marks Ice 3.6 as
recommended and 3.7 as unsupported. A plain install may attempt to compile
IcePy from source; prefer a reviewed matching wheel. The upstream package is
GPL-2.0-or-later; this skill’s own files are MIT.

For import/admin commands only, `OMERODIR` must point to a compatible extracted
OMERO.server directory. A normal remote BlitzGateway client does not require
that server tree. Read [`references/connection.md`](references/connection.md)
before installation or authentication work.

## Credentials and Connection

Set named variables in the calling environment or secret manager. Do not put
the password on an `omero` CLI command:

```bash
export OMERO_HOST="omero.example.org"
export OMERO_PORT="4064"
export OMERO_USER="researcher"
export OMERO_SECURE="true"
# Supply OMERO_PASSWORD through the environment/secret manager, or use
# OMERO_SESSION_KEY as an alternative. Do not echo either value.
```

The following password-authenticated read pattern uses the session's current
group. Before adapting it for a requested group, check that group against the
session context and set that explicit group as described in
[`references/connection.md`](references/connection.md). An empty result in the
current group does not prove that an object is absent from other groups. See
[OME's group-context documentation](https://omero.readthedocs.io/en/stable/developers/Python.html).

```python
import os
from omero.gateway import BlitzGateway

conn = None
try:
    conn = BlitzGateway(
        os.environ["OMERO_USER"],
        os.environ["OMERO_PASSWORD"],
        host=os.environ["OMERO_HOST"],
        port=int(os.environ.get("OMERO_PORT", "4064")),
        secure=True,
    )
    if not conn.connect():
        raise RuntimeError("OMERO connection failed")

    images = conn.getObjects(
        "Image",
        opts={"limit": 25, "offset": 0, "order_by": "obj.id"},
    )
    for image in images:
        print(image.getId())  # Do not print names unless requested.
finally:
    if conn is not None:
        conn.close()
```

For existing-session and CLI prompt patterns, certificate verification,
group context, and cleanup details, read
[`references/connection.md`](references/connection.md).

## Bundled Safe Helpers

All helpers use `argparse`; `--help` works without OMERO installed. Remote
helpers are dry-run by default and require `--execute`.

```bash
python -B scripts/valid

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

