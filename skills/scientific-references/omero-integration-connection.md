---
id: sciref-omero-integration-connection
name: "Scientific Ref: Connection, Sessions, and Transport Security"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (omero-integration): Connection, Sessions, and Transport Security"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "omero integration connection"
  - "connection, sessions, and transport security"
keywords:
  - "omero"
  - "integration"
  - "connection"
  - "specialized"
  - "scientific"
  - "reference"
---

# Connection, Sessions, and Transport Security

This reference is current for the skill snapshot dated 2026-09-30. It uses
`omero-py==5.22.1` and the OMERO.server 5.6.18 documentation.

## Compatibility Before Credentials

OMERO.server and its Python, web, Java, Bio-Formats, and Ice components have
independent release numbers. Do not compare their version strings as if they
were one package.

For the current stable pairing:

- OMERO.server 5.6.18 was tested with OMERO.py 5.22.1 and OMERO.web 5.31.0.
- `omero-py==5.22.1` declares Python `>=3.10`.
- The OMERO matrix supports Python 3.10/3.11 and recommends 3.12.
- Python 3.13/3.14 are listed as upcoming, not supported.
- Ice 3.6 is recommended; Ice 3.7 is unsupported.
- The OMERO-linked Glencoe wheel matrix provides IcePy 3.6.5 wheels through
  Python 3.12 for documented platforms.

OMERO.py 5.23.0 is the newer client release; local API checks for this refresh
used it with IcePy 3.6.5. The historical server-tested pairing above remains
5.22.1; a local import or CLI help check does not establish server compatibility.

For a different server release, read that release's history entry and use its
tested OMERO.py version. A newest-client/old-server pairing may appear to work
but is not the documented compatibility guarantee.

## Installation

Use an isolated Python 3.12 environment and a platform-matched Ice wheel:

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate

# Obtain the matching wheel from the OMERO-linked Ice binary matrix.
uv pip install "/absolute/path/to/zeroc_ice-3.6.5-<matching-tags>.whl"
uv pip install "omero-py==5.22.1"
```

Wheel tags must match all of:

- CPython version (`cp310`, `cp311`, or `cp312`)
- operating system
- architecture
- platform compatibility tags

Do not silently fall back to compiling IcePy if the wheel is rejected. Inspect
the interpreter and platform first. Do not install Ice 3.7 as a substitute.

`OMERODIR` is required for some CLI configuration and must point to a
compatible extracted OMERO.server tree to enable import and admin commands.
It is not required merely to use BlitzGateway against a remote server.

## Named Configuration

The bundled helpers read exactly these variables:

- `OMERO_HOST`: required hostname, without `http://`, `https://`, or path
- `OMERO_PORT`: optional integer, default `4064`
- `OMERO_USER`: username for password authentication
- `OMERO_PASSWORD`: password for password authentication
- `OMERO_SESSION_KEY`: existing session key, alternative to user/password
- `OMERO_SECURE`: boolean, default `true`

Rules:

1. Never crawl for `.env` files or read unrelated environment variables.
2. Never accept a password/session key as a command argument.
3. Never print an environment dump, password, or session key.
4. Treat a session key as a bearer credential and expire/logout when finished.
5. Prefer a secret manager or process-scoped environment over shell history.

## Password Connection

Use `try/finally` when connection success must be checked explicitly:

```python
import os
from omero.gateway import BlitzGateway

conn = BlitzGateway(
    os.environ["OMERO_USER"],
    os.environ["OMERO_PASSWORD"],
    host=os.environ["OMERO_HOST"],
    port=int(os.environ.get("OMERO_PORT", "4064")),
    secure=True,
)

try:
    if not conn.connect():
        raise RuntimeError("OMERO connection failed")

    # Keep reads bounded and group-scoped.
    for image in conn.getObjects(
        "Image",
        opts={"limit": 25, "offset": 0, "order_by": "obj.id"},
    ):
        print(image.getId())
finally:
    conn.close()
```

BlitzGateway can also be a context manager. Its context manager calls
`connect()` and closes the underlying client:

```python
import os
from omero.gateway import BlitzGateway

with BlitzGateway(
    os.environ["OMERO_USER"],
    os.environ["OMERO_PASSWORD"],
    host=os.environ["OMERO_HOST"],
    port=int(os.environ.get("OMERO_PORT", "4064")),
    secure=True,
) as conn:
    for project in conn.getObjects(
        "Project",
        opts={"limit": 10, "offset": 0, "order_by": "obj.id"},
    ):
        print(project.getId())
```

Do not catch an exception merely to print its full representation: connection
errors may include endpoint or identity details. Report the exception class
and a scrubbed message; never include credential values.

## Existing Session

`BlitzGateway.connect()` accepts `sUuid`, the existing session UUID:

```python
import os
from omero.gateway import BlitzGateway

conn = BlitzGateway(
    host=os.environ["OMERO_HOST"],
    port=int(os.environ.get("OMERO_PORT", "4064")),
    secure=True,
)

try:
    if not conn.connect(sUuid=os.environ["OMERO_SESSION_KEY"]):
        raise RuntimeError("Could not join the OMERO session")
    print(conn.getEventContext().groupId)
finally:
    conn.close(hard=False)  # Release this client without killing a shared session.
```

`close()` defaults to `hard=True`, which kills the session regardless of
reference count. Use `close(hard=False)` for a joined session and reserve hard
closure for a session this client created. The gateway context manager uses
hard closure, so it is unsuitable for a borrowed session.

Joining a session does not make it safe to log the key. If a low-level
`omero.client` is supplied through `BlitzGateway(client_obj=client)`, the
gateway does not necessarily own every other use of that client. Close it only
when ownership is clear; the official context-manager example is appropriate
when nothing else uses the client.

## CLI Login Without a Password Argument

The CLI stores sessions locally. Let it prompt:

```bash
omero login -s "$OMERO_HOST" -p "$OMERO_PORT" -u "$OMERO_USER"
omero sessions list
omero sessions file
omero logout
```

Do not use `-w` or `--password`. Although the CLI supports
`OMERO_PASSWORD`, avoid putting the secret in a persistent shell profile.

The CLI also supports joining a session with `-k`, but entering a session key
on the command line exposes it in shell history and process listings. Prefer a
short-lived, protected workflow and never paste the key into logs.

By default, session files are under `~/omero/sessions`. `OMERO_USERDIR` or
`OMERO_SESSIONDIR` can change the location. Protect any custom directory with
user-only permissions and remove stale sessions with `omero logout`.

## Group Context

The default connection group comes from the session event context:

```python
ctx = conn.getEventContext()
print(ctx.groupId)  # Avoid printing the session ID.
```

Set

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

