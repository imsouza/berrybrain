---
id: sciref-simpy-cli-guide
name: "Scientific Ref: Bundled CLI guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (simpy): Bundled CLI guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "simpy cli guide"
  - "bundled cli guide"
keywords:
  - "simpy"
  - "cli"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
  - "bundled"
---

# Bundled CLI guide

Reviewed 2026-10-01 for skill version 1.6 and SimPy 4.1.2.

The scripts implement one transparent finite-horizon exponential
arrival/exponential service multi-server queue. They are examples and diagnostics,
not a generic model execution platform.

## Safety contract

All scripts:

- use only SimPy and the Python standard library;
- build `--help` when SimPy is absent, so options remain inspectable before
  installation;
- make no network or external-service calls;
- accept only local regular files with fixed suffixes;
- reject URLs, symlinks, duplicate JSON keys, `NaN`/infinity, unknown keys, and
  oversized inputs;
- never evaluate configuration text, run user Python, resolve callables, or import
  plugins;
- enforce time, event, entity, queue, trace, and replication caps;
- emit strict deterministic JSON (`allow_nan=False`);
- write explicit outputs atomically with mode `0600`;
- refuse overwrite unless `--force` is supplied.

Run from the repository root after the pinned install:

```bash
uv pip install "simpy==4.1.2"
```

Commands that execute a simulation gate SimPy through a shared dependency loader.
If it is absent, they exit without a traceback and print the pinned installation
command above. They also reject a different installed version because scheduler
instrumentation is release-specific. Configuration validation and artifact summarization remain usable
without SimPy.

## Queue configuration schema

Every field is optional; defaults are shown:

```json
{
  "analysis_mode": "terminating",
  "base_seed": 20260723,
  "horizon": 480.0,
  "max_entities": 10000,
  "max_events": 200000,
  "mean_interarrival": 4.0,
  "mean_service": 6.0,
  "queue_capacity": 20,
  "servers": 2,
  "warm_up": 0.0
}
```

Semantics:

- arrival and service durations are exponential means in the declared model time
  unit;
- there are `servers` simultaneous slots and at most `queue_capacity` waiting
  entities;
- an arrival seeing `servers + queue_capacity` admitted entities is rejected;
- arrivals and services use separate deterministic stream seeds;
- arrivals occur strictly before `horizon`;
- numeric horizon excludes ordinary events exactly at that time;
- completed-customer metrics exclude unfinished entities and disclose their count.

Bounds:

- `0 < horizon <= 1,000,000`;
- `1 <= servers <= 10,000`;
- `0 <= queue_capacity <= 100,000`;
- positive finite means no greater than 1,000,000;
- `1 <= max_entities <= 100,000`;
- `10 <= max_events <= 1,000,000`;
- base seed from 0 through `2^63 - 1`.

For `analysis_mode="terminating"`, `warm_up` must be zero. For
`analysis_mode="steady_state"`, warm-up must be positive and less than horizon.
This validates consistency only; it does not establish that steady state was
reached.

Report schema 1.2 separates the measurement rules:

- `window_arrivals` and `window_rejected` count events in `[warm_up, horizon)`;
  `loss_probability` is their ratio (null when there are no window arrivals).
- `window_departures` counts **all** completions in that time window, including
  customers arriving before warm-up; throughput divides this by `horizon - warm_up`.
- `observed_completed` and customer means use customers arriving at/after warm-up
  and completed before the horizon; unfinished customer paths are excluded.
- Queue length and utilization are time-weighted over `[warm_up, horizon)`.
- The original arrivals/admitted/rejected/completed counters span the full run.
- `event_processing.processed` includes the step whose callback stops the run.

These synthetic exponential inputs demonstrate event mechanics; they are not
calibrated estimates of a real queue. Record the time unit and justify inputs before
using scenario contrasts. The report records `simpy_version` and `metric_windows`.

## Basic template

```bash
python skills/simpy/scripts/basic_simulation_template.py --help
python skills/simpy/scripts/basic_simulation_template.py
python skills/simpy/scripts/basic_simulation_template.py \
  --config queue.json --output run.json
```

`--replication INDEX` selects deterministic derived arrival/service seeds. It does
not itself create a confidence interval.

Library use:

```python
from basic_simulation_template import QueueConfig, run_simulation

config = QueueConfig.from_mapping({"horizon": 120, "servers": 3})
report = run_simulation(config, replication=0)
```

## Bounded queue scenario and trace

```bash
python skills/simpy/scripts/bounded_queue_scenario.py \
  --config queue.json \
  --output scenario.json \
  --trace-output trace.jsonl \
  --trace-max-records 50000
```

The trace is capped and contains no event `repr`:

```json
{
  "event_id": 0,
  "event_type": "Initialize",
  "priority": 0,
  "queue_size_before": 1,
  "time": 0.0
}
```

The `.jsonl` file has one compact object per line. A trace can truncate while the
bounded simulation completes; the report discloses `trace.truncated`.

## Replication configuration schema

```json
{
  "confidence": 0.95,
  "model": {
    "analysis_mode": "terminating",
    "base_seed": 20260723,
    "horizon": 480,
    "max_entities": 10000,
    "max_events": 200000,
    "mean_interarrival": 4,
    "mean_service": 6,
    "queue_capacity": 20,
    "servers": 2,
    "warm_up": 0
  },
  "replications": 20
}
```

Additional experiment bounds:

- 2-1,000 replications; one-run confidence intervals are rejected;
- confidence strictly greater than 0.50 and at most 0.999;
- `replications * max_events <= 5,000,000`;
- `replications * max_entities <= 2,000,000`.

```bash
python skills/simpy/scripts/replication_runner.py --help
python skills/simpy/scripts/replication_runner.py \
  --config experiment.json --output intervals.json
```

The runner makes a two-sided Student-t interval from independent
replication-level estimates. A metric undefined in any run is marked unavailable
instead of dropping that run. It never constructs a CI from individual customers
within one run.

The seed manifest uses stable BLAKE2b derivation for separate arrival/service RNG
objects. This is deterministic stream separation for the bundled example, not a
formal proof of independent substreams. See `simulation-methodology.md`.

## Configuration validator

Validation performs no simulation:

```bash
python skills/simpy/scripts/validate_simulation_config.py queue.json
python skills/simpy/scripts/validate_simulation_config.py \
  experiment.json --schema replication
```

Schemas are `queue`, `replication`, or `auto`. Auto identifies the replic

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

