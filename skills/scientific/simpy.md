---
id: sci-simpy
name: "Scientific: simpy"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Builds, inspects, tests, and analyzes bounded process-based discrete-event simulations with SimPy. Use for event scheduling, resource queues, interrupts, monitoring, independent replications, warm-up, and reproducible output analysis."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "simpy"
keywords:
  - "simpy"
  - "builds"
  - "inspects"
  - "tests"
  - "analyzes"
  - "bounded"
  - "process"
---

# SimPy

## Scope

Use this skill for process-based discrete-event models where active entities yield
events and contend for resources: queues, production systems, logistics, networks,
service operations, inventory, and other event-driven systems.

SimPy supplies an event scheduler and modeling primitives. It does **not** choose a
scientifically valid conceptual model, input distribution, warm-up, run length,
replication count, estimand, or causal interpretation. Treat those as simulation-study
methodology, not SimPy API behavior.

## Current release and installation

Reviewed **2026-10-01** against current official documentation and the released source:

- Latest stable: **SimPy 4.1.2**, released on PyPI 2026-05-24; source tag
  `4.1.2` points to commit `f4381649`.
- Package metadata requires Python **>=3.8** and classifies CPython 3.8-3.14
  plus PyPy. SimPy has no runtime dependencies.
- 4.1.2 adds Python 3.13/3.14 support and modern-interpreter test fixes.
- Upstream and this skill are MIT-licensed.

Create a reproducible environment:

```bash
uv venv --python 3.13
source .venv/bin/activate
uv pip install "simpy==4.1.2"
python -c "import importlib.metadata; print(importlib.metadata.version('simpy'))"
```

Do not silently substitute the `latest` documentation build: it may describe an
unreleased development revision. Use the versioned 4.1.2 links in
`references/sources.md`.

## Model workflow

1. **Define purpose and estimands.** State the decision/question, system boundary,
   entities, resources, state, outputs, time units, and terminating event or
   steady-state target.
2. **Write a conceptual model first.** Record assumptions, distributions,
   routing, priorities, initial conditions, and omitted mechanisms.
3. **Implement generators.** A SimPy process is an event-yielding Python generator.
   Register the generator object with `env.process(...)`.
4. **Bound execution.** Give every production run explicit time, entity, event, and
   replication caps. Never call `env.run()` on a model containing an endless process.
   A time horizon alone cannot stop an endless `yield env.timeout(0)` loop: events
   keep running at the same simulation time. Add an event-count or no-time-progress
   guard, and wait on state-change events instead of zero-delay busy polling.
5. **Separate random streams.** Use local RNG instances for logically distinct
   stochastic sources; retain a seed manifest.
6. **Instrument deliberately.** Observe state after the transition of interest,
   close time-weighted intervals at the horizon, and test that monitoring does not
   alter event order.
7. **Verify and validate.** Test deterministic edge cases, conservation identities,
   traces, queue discipline, and analytical benchmarks; compare against system or
   expert evidence for the stated purpose.
8. **Run independent replications.** Make intervals from replication-level
   estimates, not correlated entities within one run.
9. **Report limitations.** Include initialization, unfinished entities, run length,
   seeds/streams, precision, sensitivity, and validation evidence. Never convert
   simulation association into a causal claim.

Read `references/simulation-methodology.md` before making inferential claims.

## Minimal bounded model

```python
import random
import simpy

HORIZON = 480.0
arrival_rng = random.Random(101)
service_rng = random.Random(202)
env = simpy.Environment()
server = simpy.Resource(env, capacity=2)
completed = []

def customer(arrival):
    with server.request() as request:
        yield request
        wait = env.now - arrival
        yield env.timeout(service_rng.expovariate(1 / 6.0))
    completed.append((env.now, wait))

def arrivals():
    for _ in range(10_000):  # Entity cap.
        delay = arrival_rng.expovariate(1 / 4.0)
        if env.now + delay >= HORIZON:
            return
        yield env.timeout(delay)
        env.process(customer(env.now))

env.process(arrivals())
env.run(until=HORIZON)
```

The numeric horizon is half-open: normal events scheduled exactly at `480.0` are
not processed. Report unfinished entities rather than silently treating them as
completed observations.

## Core semantics

### Environment and deterministic ordering

`Environment` is single-threaded. The queue is ordered by simulation time, event
priority, then a strictly increasing event ID. Same-time, same-priority events are
therefore processed FIFO in scheduling order. Model processes may represent
concurrency, but callbacks execute sequentially and deterministically.

This orders the events currently queued. A callback can insert an urgent event at
the current time, so a valid processing trace need not have globally increasing
priority or event IDs within a timestamp.

- `env.now`: unitless simulation clock; choose and document one unit.
- `env.peek()`: next event time or infinity.
- `env.step()`: process one event; raises `EmptySchedule` when empty.
- `env.active_process`: currently executing process, otherwise `None`.
- `env.run()`: drain the queue; unsafe with recurring or endless processes.

`env.run(until=number)` and `env.run(until=event)` are not interchangeable at
boundaries:

- A numeric value schedules an urgent stop event and excludes ordinary events at
  that exact time.
- An Event criterion returns that event's value when its stop callback fires.
  Other same-time ordering depends on priority and scheduling order.
- In 4.1.2, `Environment.step()` preserves callbacks remaining after
  `StopSimulation` by rescheduling the target. Consequently, after
  `env.run(until=target)`, `target.processed` can remain `False` until one more
  `step()`/`run()` even though its value was returned. Do not use `processed` as the
  sole post-run completion test.

See `references/events.md` and `references/monitoring.md`.

### Event, Timeout, Process, and Condition

- An `Event` moves once through not-triggered -> triggered/scheduled -> processed.
  `succeed(value)` or `fail(exception)` triggers it once.
- A `Timeout` triggers when created, is scheduled for `now + delay`, and cannot be
  manually succeeded again.
- `env.process(generator)` creates a `Process`; the generator resumes with the
  yielded event value. Returning from the generator succeeds the Process with that
  return value. Uncaught exceptions fail it.
- `AnyOf` / `a | b` and `AllOf` / `a & b` yield a `ConditionValue`: an ordered,
  dict-like mapping from **event objects** to their values. Test membership using
  the original event obj

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

