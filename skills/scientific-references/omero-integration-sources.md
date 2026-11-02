---
id: sciref-omero-integration-sources
name: "Scientific Ref: Official Sources and Version Snapshot"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (omero-integration): Official Sources and Version Snapshot"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "omero integration sources"
  - "official sources and version snapshot"
keywords:
  - "omero"
  - "integration"
  - "sources"
  - "specialized"
  - "scientific"
  - "reference"
  - "official"
---

# Official Sources and Version Snapshot

Research date: **2026-09-30**

This file records the authoritative basis for skill version 1.6. The snapshot
must not replace checking the target server's own version and discovery
endpoints.

## Versions and Tested Pairing

- **OMERO.server 5.6.18** — May 2026 bug-fix release.
- **OMERO.py / `omero-py` 5.23.0** — latest PyPI release, 2026-07-30.
  The server history still records testing with **5.22.1** (2026-03-25).
- **OMERO.web 5.33.2** — latest PyPI release. **5.31.0** remains the version
  recorded as tested with OMERO.server 5.6.18.
- **Bio-Formats 8.5.0** — bundled by OMERO.server 5.6.18.
- **ZeroC IcePy 3.6.5** — exact client binding version in current official
  installation examples and OMERO-linked wheel matrix.

The OMERO.server history explicitly says 5.6.18 was tested with OMERO.py
5.22.1 and OMERO.web 5.31.0. That tested pairing is stronger evidence than
assuming compatibility from package version numbers.

## Release and Package Metadata

- OMERO version history
  https://omero.readthedocs.io/en/stable/users/history.html
  Basis for server 5.6.18, tested client/web pairing, and Bio-Formats 8.5.0.

- `omero-py` on PyPI
  https://pypi.org/project/omero-py/
  Basis for latest 5.23.0, its 2026-07-30 release, Python `>=3.10`, IcePy 3.6,
  NumPy/Pillow requirements, OMERODIR notes, and GPL-2.0-or-later package
  license.

- Official OME `omero-py` repository and changelog
  https://github.com/ome/omero-py
  https://github.com/ome/omero-py/releases/tag/v5.23.0
  https://github.com/ome/omero-py/blob/v5.23.0/src/omero/gateway/__init__.py
  Source check for gateway signatures, session lifecycle, context forwarding,
  annotation materialization, channel inversion, and ROI/model handling.
  The 5.23.0 release adds default-group CLI support and shape externalInfo
  loading; it does not announce IRoi removal.

- Current OMERO.web package and API implementation
  https://pypi.org/project/omero-web/
  https://github.com/ome/omero-web/blob/v5.33.2/omeroweb/api/urls.py
  https://github.com/ome/omero-web/blob/v5.33.2/omeroweb/api/views.py
  https://github.com/ome/omero-web/blob/v5.33.2/omeroweb/webgateway/views.py
  Cross-check for discovery, ROI routes, list defaults, login body/cookies,
  version 0.2 and Project/Dataset/Screen save support.

- Official OME OMERO.server component releases
  https://github.com/ome/omero-server/releases
  Cross-check for current server component releases.

## Installation and Compatibility

- OMERO Python language bindings
  https://omero.readthedocs.io/en/stable/developers/Python.html
  Basis for the current `omero-py==5.22.1` examples, IcePy 3.6.5 ordering,
  BlitzGateway patterns, objects, annotations, tables, ROIs, pixels, and
  rendering.

- OMERO version requirements
  https://omero.readthedocs.io/en/stable/sysadmins/version-requirements.html
  Basis for Python 3.10/3.11 support, Python 3.12 recommendation,
  Python 3.13/3.14 “upcoming” status, Ice 3.6 recommendation, Ice 3.7
  unsupported status, and server platform/runtime matrix.

- OMERO-linked Glencoe Ice binary matrix
  https://www.glencoesoftware.com/blog/2023/12/08/ice-binaries-for-omero.html
  Basis for exact prebuilt IcePy 3.6.5 wheel coverage through Python 3.12.
  Glencoe is identified in OME's Python installation page as its commercial
  partner. Select the exact wheel from the linked release repositories.

- OMERO CLI installation
  https://omero.readthedocs.io/en/stable/users/cli/installation.html
  Basis for client installation and import/admin prerequisites.

## Connection and Security

- BlitzGateway documentation
  https://omero.readthedocs.io/en/stable/developers/PythonBlitzGateway.html
  Basis for context-manager closure, wrappers/lazy loading, stateless versus
  stateful service reuse, and stale stateful proxies after reconnection.

- Server security and firewalls
  https://omero.readthedocs.io/en/stable/sysadmins/server-security.html
  Basis for login encryption, optional full transport encryption, session-ID
  exposure on insecure post-login traffic, and default router ports 4063/4064.

- Client/server SSL verification
  https://omero.readthedocs.io/en/stable/sysadmins/client-server-ssl.html
  Basis for the warning that standard clients do not automatically verify the
  host and for the documented IceSSL verification properties.

- CLI session management
  https://omero.readthedocs.io/en/stable/users/cli/sessions.html
  Basis for prompted login, session files, `omero sessions`, group switching,
  `-k` session reuse, and logout.

## Data, Metadata, ROIs, and Tables

- OMERO Python examples
  https://omero.readthedocs.io/en/stable/developers/Python.html
  Primary current examples for bounded `getObjects`, annotations, pixels,
  rendering, tables, and ROI model operations.

- OMERO.tables
  https://omero.readthedocs.io/en/stable/developers/Tables.html
  Basis for current column signatures, reads, queries, paging, global locking,
  and HDF implementation details.

- Structured annotations
  https://omero.readthedocs.io/en/stable/developers/Model/StructuredAnnotations.html
  Basis for annotation type hierarchy, namespaces, and link semantics.

- OME ROI model 5.6.3
  https://docs.openmicroscopy.org/ome-model/5.6.3/developers/roi.html
  Basis for the eight shape types, optional TheZ/TheT/TheC, RGBA fields, and
  union-of-2D-shapes representation. The page itself was last updated in 2018
  but documents the June 2016 schema still used by OMERO 5.6.

- Current generated `IRoi` API
  https://docs.openmicroscopy.org/omero-blitz/5.8.5/slice2html/omero/api/IRoi.html
  Basis for the explicit `IRoi` deprecation warning.

- OMERO application services
  https://omero.readthedocs.io/en/stable/developers/Modules/Api.html
  Basis for service categories and current `IRoi`/`IShare` deprecation status.

## CLI Import, Export, and Download

- Import images
  https://omero.readthedocs.io/en/stable/users/cli/import.html
  Basis for `omero import`, `-f` serverless scanning, target syntax,
  depth/output options, experimental parallelism warning, and diagnostic
  upload disclosure.

- Import targets
  https://omero.readthedocs.io/en/stable/users/cli/import-target.html
  Basis for current-group target behavior and target syntax.

- Export images
  https://omero.readthedocs.io/en/stable/users/cli/export.html
  Basis for OME-TIFF/XML-only export and experimental Dataset iteration.

- Current `omero-py==5.23.0` CLI help (`omero download -h`)
  Verified in an

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

