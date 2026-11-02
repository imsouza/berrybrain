---
id: sciref-dnanexus-integration-sources
name: "Scientific Ref: Sources and Version Baseline"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dnanexus-integration): Sources and Version Baseline"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dnanexus integration sources"
  - "sources and version baseline"
keywords:
  - "dnanexus"
  - "integration"
  - "sources"
  - "specialized"
  - "scientific"
  - "reference"
---

# Sources and Version Baseline

## Verification

Last verified: **2026-09-30**

| Component | Verified baseline |
|---|---|
| DNAnexus Platform docs | 2026 documentation and release notes through 2026-09-22 |
| dx-toolkit / dxpy | 0.415.0, released 2026-09-22 |
| Python requirement | Python 3.8+ on PyPI |
| App Execution Environment | Ubuntu 24.04 and 20.04, version `0` |
| dxCompiler | 2.18.0 (released 2026-08-05) |
| Upload Agent | 1.5.33 |
| Download Agent | 0.6.4 |
| dxFUSE | 1.6.1 |
| Nextaur | 1.16.0 (toolkit release notes) |
| Nextflow engines exposed by dx-toolkit 0.415.0 | 25.10 and 24.10 |
| Nextflow 25.10 asset baseline | Nextflow 25.10.4 with nf-amazon 3.4.4 |

The dxpy symbols/signatures, CLI help, and bundled offline helpers were executed
locally against the pinned SDK. Platform contracts and the remaining release
versions were reviewed in current official documentation/source. Transfers,
builds, launches, and compiler/Nextflow execution examples are illustrative;
no authenticated or billable end-to-end run was performed. The current
dxCompiler release is established by its tagged release, because the `develop`
changelog still labels the 0.6.4 download-agent change as unreleased.

Version-specific examples in this skill are pinned for reproducibility. Before
upgrading, inspect release notes, run `scripts/inspect_dxpy.py`, and rebuild/test
apps in a non-production project.

## Documentation Index and Releases

- [DNAnexus documentation index (`llms.txt`)](https://documentation.dnanexus.com/llms.txt)
- [DNAnexus 2026 release notes](https://documentation.dnanexus.com/release-notes.md)
- [Downloads](https://documentation.dnanexus.com/downloads.md)
- [Index of `dx` commands](https://documentation.dnanexus.com/user/helpstrings-of-sdk-command-line-utilities.md)
- [dx-toolkit GitHub repository](https://github.com/dnanexus/dx-toolkit)
- [dx-toolkit changelog](https://github.com/dnanexus/dx-toolkit/blob/master/CHANGELOG.md)
- [dxpy on PyPI](https://pypi.org/project/dxpy/)
- [Generated Python API reference](https://autodoc.dnanexus.com/bindings/python/current/)

The release notes are date-versioned by platform deployment. The skill
baseline incorporates:

- 2026-09-22: dx-toolkit 415.0 Nextflow offline mode
- 2026-09-15: CLI login default expiration aligned to 18 hours
- 2026-08-18: normal login sessions shortened to two hours idle, 18 hours absolute
- 2026-08-11: user API tokens blocked for UKB RAP; dxCompiler 2.18.0 / dxda 0.6.4
- 2026-08-04: rebuild Nextflow applets to pick up upload-recovery fixes
- 2026-07-21: dx-toolkit 410.0 malicious-file download warning
- 2026-07-14: strengthened session/password controls
- 2026-06-23: dxCompiler 2.17.0 authenticated WDL imports
- 2026-06-09: file download API `securityStatus`
- 2026-05-19: dxCompiler resource-retry support
- 2026-03-17: automatic upgrade on insufficient-resource retry
- 2026-02-03: retired instance type validation
- 2026-01-27: dynamic instance type selection

## Authentication

- [Login and Logout](https://documentation.dnanexus.com/user/login-and-logout.md)
- [Environment Variables](https://documentation.dnanexus.com/user/environment-variables.md)
- [dx-toolkit environment bootstrap](https://github.com/dnanexus/dx-toolkit/blob/master/environment)
- [API Authentication](https://documentation.dnanexus.com/developer/api/authentication.md)
- [API Protocols and Errors](https://documentation.dnanexus.com/developer/api/protocols.md)

Key current points:

- Environment variables override saved CLI configuration.
- `dx env` displays token material.
- Tokens without explicit expiry default to one month.
- Token revocation terminates associated active jobs/transfers.
- New normal-policy login sessions expire after two hours idle and at most
  18 hours after issuance; org policies may be stricter.
- User API tokens can be scoped to selected projects and access levels.
- User-generated API tokens cannot access UKB RAP resources.

## Apps and Applets

- [Introduction to Building Apps](https://documentation.dnanexus.com/developer/apps/intro-to-building-apps.md)
- [Developer Quickstart](https://documentation.dnanexus.com/getting-started/developer-quickstart.md)
- [App Metadata (`dxapp.json`)](https://documentation.dnanexus.com/developer/apps/app-metadata.md)
- [I/O and Run Specifications](https://documentation.dnanexus.com/developer/api/running-analyses/io-and-run-specifications.md)
- [App Execution Environment](https://documentation.dnanexus.com/developer/apps/execution-environment.md)
- [Apps API](https://documentation.dnanexus.com/developer/api/running-analyses/apps.md)
- [Applets, Jobs, and Entry Points API](https://documentation.dnanexus.com/developer/api/running-analyses/applets-and-entry-points.md)
- [App Permissions](https://documentation.dnanexus.com/developer/apps/app-permissions.md)
- [Types of Errors](https://documentation.dnanexus.com/developer/apps/error-information.md)
- [Developing Apps and Applets FAQ](https://documentation.dnanexus.com/faqs/developing-apps-and-applets.md)

Dependencies:

- [Dependency management](https://documentation.dnanexus.com/developer/apps/dependency-management.md)
- [Python packages in Ubuntu 24.04 AEE](https://documentation.dnanexus.com/developer/apps/dependency-management/python-package-installation-in-ubuntu-24-04-aee.md)
- [Asset Build Process](https://documentation.dnanexus.com/developer/apps/dependency-management/asset-build-process.md)
- [Docker Images](https://documentation.dnanexus.com/developer/apps/dependency-management/using-docker-images.md)

## Data and Projects

- [Uploading and Downloading Files](https://documentation.dnanexus.com/user/objects/uploading-and-downloading-files.md)
- [`dx upload`](https://documentation.dnanexus.com/user/objects/uploading-and-downloading-files/small-sets-of-files/uploading-using-dx.md)
- [`dx download`](https://documentation.dnanexus.com/user/objects/uploading-and-downloading-files/small-sets-of-files/downloading-using-dx.md)
- [Upload Agent](https://documentation.dnanexus.com/user/objects/uploading-and-downloading-files/batch/upload-agent.md)
- [Download Agent](https://documentation.dnanexus.com/user/objects/uploading-and-downloading-files/batch/download-agent.md)
- [Download Agent repository](https://github.com/dnanexus/dxda)
- [Download Agent 0.6.4 release](https://github.com/dnanexus/dxda/releases/tag/v0.6.4)
- [dxFUSE 1.6.1 release](https://github.com/dnanexus/dxfuse/releases/tag/v1.6.1)
- [Data Object Lifecycle](https://documentation.d

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

