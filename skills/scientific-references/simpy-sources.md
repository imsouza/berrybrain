---
id: sciref-simpy-sources
name: "Scientific Ref: Sources and verification record"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (simpy): Sources and verification record"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "simpy sources"
  - "sources and verification record"
keywords:
  - "simpy"
  - "sources"
  - "specialized"
  - "scientific"
  - "reference"
  - "verification"
---

# Sources and verification record

Current API/source/runtime review: **2026-10-01**, SimPy **4.1.2**, Python **3.13.3**.
Official PyPI metadata still identifies 4.1.2 as the latest release. The 410,129-byte
official source distribution and the cached installed release were inspected;
core/event/resource/real-time signatures and implementation behavior agree.
Versioned documentation is preferred over the moving `latest` build.

The release and bibliographic notes below retain their original 2026-07-23 access
dates where that historical review was not repeated. They are not fresh live-probe
claims. On this refresh, the core/events/resources/rt/util/exceptions API pages,
monitoring guide, and Law/L'Ecuyer/Sargent proceedings were opened directly.
Several topical pages were inaccessible through the browser extraction tool;
the corresponding official 4.1.2 sdist documentation/source supplied the fallback.

## Current audit findings

| Surface | Verified behavior / correction |
|---|---|
| `Environment(initial_time)`, `run`, `step`, `peek`, `schedule`, `now`, `active_process` | Queue minimum chosen at each step; callbacks can insert urgent same-time work. Numeric horizon excludes ordinary boundary events. Stop callback reschedules remaining callbacks at priority -1. |
| `Event`, `Timeout`, `Process`, `AnyOf`, `AllOf`, `ConditionValue`, `Interrupt` | Values, failure propagation, conditions and interrupt lifecycle reproduced. `Event.trigger()` returns None despite an inconsistent prose docstring; `fail()` source accepts BaseException despite its Exception annotation. |
| Resource/Priority/Preemptive, Request/Release, `Preempted`, Put/Get cancellation | Resource request key includes `(priority, time, not preempt)`; context exit cancels pending requests and releases acquired slots. |
| Container/Store/FilterStore/PriorityStore/`PriorityItem` | Blocked requests wait; filtering can bypass earlier unmatched gets. PriorityStore is a heap and equal-priority items are not FIFO without an explicit tie-breaker. |
| `RealtimeEnvironment`, `factor`, `strict`, `sync` | Mapping and lag check inspected in released `rt.py`. Constructor does not enforce positive finite factor. `sync` resets wall origin, not the initial simulation origin. |
| Monitoring | Native deterministic checks cover urgent trace insertion, final time weighting, warm-up windows, cancellation, and monitor non-interference. |
| Queue/replication helpers | Schema 1.2 counts throughput by window departures and loss by window arrivals; arrival-cohort completed customer means remain censored. Runtime version and metric definitions are recorded. |

There are **no service/API endpoints, credentials, request bodies, pagination, or
remote mutations** in these helpers. The URLs here are package documentation,
source, and methodological references. Native discrete-event fixtures verify
software mechanics, not a calibrated operational system. Real-time strict/sync
unit checks use a controlled clock; a short wall-clock smoke is only a timing
sanity check, not a hardware-in-the-loop performance claim.

The isolated suite is under repository-level `tests/simpy/`. CLI round trips use
tiny local JSON/JSONL/CSV files; no user data or live service was exercised.
The complete minimal model in `SKILL.md` and ten CLI workflows were executed.
All 46 Python documentation fragments parsed; context-dependent reference snippets
are illustrative patterns, with representative behaviors exercised by the native
suite rather than every fragment executed independently.

## Release, packaging, and source

- [SimPy on PyPI](https://pypi.org/project/simpy/) — **4.1.2**, released
  **2026-05-24**; `Requires-Python >=3.8`; classifiers list Python 3.8-3.14,
  CPython, and PyPy; MIT; no runtime dependencies. Verified 2026-07-23.
- [GitLab source project](https://gitlab.com/team-simpy/simpy/) — canonical
  repository, MIT license, tagged source, tests, and documentation. Accessed
  2026-07-23.
- [GitLab tag 4.1.2](https://gitlab.com/team-simpy/simpy/-/tags/4.1.2) —
  protected/verified tag, commit `f43816490c6f76f336ad6e457d3cab9f386894af`,
  dated **2026-05-24**.
- [Tagged CHANGES.rst](https://gitlab.com/team-simpy/simpy/-/blob/4.1.2/CHANGES.rst)
  — 4.1.2 entry dated **2026-05-23**: Python 3.13/3.14 support,
  modern-interpreter test/doc fixes, `ConditionValue` explicitly unhashable,
  lint/type cleanup.
- [Tagged pyproject.toml](https://gitlab.com/team-simpy/simpy/-/blob/4.1.2/pyproject.toml)
  — Python requirement/classifiers, no dependencies, setuptools build, pytest,
  mypy, and ruff configuration. Dated 2026-05-23; accessed 2026-07-23.
- [Tagged tox.ini](https://gitlab.com/team-simpy/simpy/-/blob/4.1.2/tox.ini) and
  [tagged tests](https://gitlab.com/team-simpy/simpy/-/tree/4.1.2/tests) —
  upstream test matrix and behavior tests. Accessed 2026-07-23.
- [Tagged `simpy/core.py`](https://gitlab.com/team-simpy/simpy/-/blob/4.1.2/src/simpy/core.py)
  — authoritative `Environment.run()`, `step()`, queue tuple, and
  `StopSimulation` implementation. Accessed 2026-07-23.

PyPI file hashes observed 2026-07-23:

- wheel `simpy-4.1.2-py3-none-any.whl` SHA-256
  `43071f84b6512c9b4fcb33ef057f240ccb1d1f3b263f9b4f9229d072e310b372`;
- sdist `simpy-4.1.2.tar.gz` SHA-256
  `76ef36b71e0436ba94e55febc001c78879e493a323f045bbcfbb0b216e9b1fbc`.

Use the pinned package command in `SKILL.md`; hashes are recorded for provenance,
not embedded into `uv pip install` syntax.

## Official SimPy 4.1.2 documentation

### Entry points

- [4.1.2 documentation contents](https://simpy.readthedocs.io/en/4.1.2/contents.html)
- [4.1.2 tutorial](https://simpy.readthedocs.io/en/4.1.2/simpy_intro/index.html)
- [4.1.2 topical guides](https://simpy.readthedocs.io/en/4.1.2/topical_guides/index.html)
- [4.1.2 examples](https://simpy.readthedocs.io/en/4.1.2/examples/index.html)
- [4.1.2 API reference](https://simpy.readthedocs.io/en/4.1.2/api_reference/index.html)
- [history/change log](https://simpy.readthedocs.io/en/4.1.2/about/history.html)
- [license](https://simpy.readthedocs.io/en/4.1.2/about/license.html)

All accessed 2026-07-23. The examples index covers condition events, interrupts,
Resource, PreemptiveResource, Container, Store, shared events, and process waiting.

### Core topical guides

- [SimPy basics](https://simpy.readthedocs.io/en/4.1.2/topical_guides/simpy_basics.html)
- [Environments](https://simpy.readthedocs.io/en/4.1.2/topical_guides/environments.html)
- [Events](https://simpy.readthedocs

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

