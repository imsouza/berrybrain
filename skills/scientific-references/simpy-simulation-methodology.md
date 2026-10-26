---
id: sciref-simpy-simulation-methodology
name: "Scientific Ref: Simulation-study methodology (not SimPy API)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (simpy): Simulation-study methodology (not SimPy API)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "simpy simulation methodology"
  - "simulation-study methodology (not simpy api)"
keywords:
  - "simpy"
  - "simulation"
  - "methodology"
  - "specialized"
  - "scientific"
  - "reference"
  - "study"
---

# Simulation-study methodology (not SimPy API)

Verified 2026-07-23. This guide applies established discrete-event simulation
methods to SimPy models. SimPy schedules events; it does not perform these study
design decisions automatically.

## 1. Start with the conceptual model

Before code, specify:

- purpose, decision context, stakeholders, and intended domain;
- system boundary, entities, resources, queues, routes, state, and termination;
- input data provenance and fitted/assumed distributions;
- initial conditions and time units;
- performance measures/estimands;
- assumptions, simplifications, exclusions, and known limits;
- required accuracy and validation evidence.

Robinson defines conceptual modeling as abstraction from a real or proposed system
and emphasizes validity, credibility, utility, feasibility, and the simplest model
adequate for purpose. Sargent frames validity relative to the intended application
and domain, not as a universal property.

Use a unit table:

| Quantity | Unit | Convention |
|---|---|---|
| `env.now` | minutes | starts at opening |
| interarrival | minutes/entity | strictly positive |
| service | minutes | sampled at service start |
| throughput | entities/hour | convert from minute horizon |

SimPy time is unitless. Unit inconsistency can produce a perfectly executable but
invalid model.

## 2. Terminating versus steady-state studies

### Terminating

A terminating simulation has a natural, predeclared endpoint: closing time,
completion of an order, end of a mission, or another event relevant to the purpose.
Initial conditions are part of the estimand and should normally be identical across
replications.

Decide how to handle entities still present at a fixed clock horizon:

- stop and report/censor unfinished paths;
- stop arrivals at closing but drain the system;
- terminate on an explicit completion event.

These answer different questions. Numeric `env.run(until=horizon)` is half-open and
does not drain.

### Nonterminating / steady state

A nonterminating system has no natural endpoint and targets a long-run parameter.
Arbitrary initialization creates transient bias. A finite warm-up deletion may
reduce that bias, but neither a warm-up nor a long run proves stationarity or
convergence.

Use a declared replication/deletion design:

1. estimate/justify warm-up in a pilot study;
2. make independent production replications;
3. apply the same deletion rule to each;
4. make the post-deletion run much longer than warm-up;
5. assess sensitivity to longer warm-up and run length.

Do not label a finite-horizon operating-day model "steady state" merely because it
has many events.

## 3. Random seeds and streams

Pseudo-random generation is deterministic given algorithm, state, and consumption
order. Reproducibility requires recording:

- RNG implementation and Python/package versions;
- base seed and derived per-replication seeds;
- mapping of streams to stochastic sources;
- replication index and configuration;
- any common-random-number pairing.

Use separate local RNG objects for distinct sources:

```python
arrival_rng = random.Random(arrival_seed)
service_rng = random.Random(service_seed)
```

Avoid module-global `random.seed()` in reusable models: unrelated code can consume
or reset the shared stream.

L'Ecuyer recommends independent streams/substreams, often one stream per stochastic
source and one substream per replication. Distinct hash-derived seeds, as used by
the bundled scripts, provide deterministic separation for a compact standard-library
example; they do **not** mathematically prove stream independence. For high-stakes
or large parallel experiments, use a generator/package with explicit tested stream
and jump/substream facilities and document it.

### Common random numbers

For paired alternatives, intentionally using the same source-specific random
numbers can reduce variance of differences. Keep replication pairs aligned and use
separate source streams so a demand draw in one alternative does not become a
service draw in another. Analyze paired replication differences. Common random
numbers are a designed variance-reduction method, not independent streams across
alternatives.

## 4. Independent replications

Within-run entity outcomes are usually dependent: customers share queues and system
state. The basic independent unit is a complete replication using an independent
stream set.

For each replication:

- reset model state and statistical counters;
- use the same scenario/configuration and intended initial-condition rule;
- use new independent random streams;
- produce one estimate per performance measure.

Law's output-analysis tutorial stresses that one run does not produce "the answer."
Use at least two replications to estimate variance; practical counts should be
chosen from desired precision, distribution shape, computational cost, and a pilot,
not a universal magic number.

The bundled replication runner caps counts and records every derived seed. It does
not automatically choose a sufficient replication count.

## 5. Confidence intervals

Given independent replication estimates `X_1, ..., X_n`, a common two-sided
Student-t interval for their mean is:

`mean(X) +/- t_(n-1, 1-alpha/2) * s(X) / sqrt(n)`.

State:

- estimand and unit;
- number of independent replications;
- confidence level and method;
- point estimate, interval, and half-width;
- warm-up/run length and missing/unfinished handling.

Conditions and caveats:

- replication estimates must be independent and comparably generated;
- the t interval is exact under normal replication estimates and approximate under
  suitable large-sample behavior;
- a tiny `n` gives unstable variance and distribution diagnostics;
- a narrow interval around a biased/invalid model result is still wrong;
- optional stopping based on observed precision needs a valid sequential procedure.

### Never make a naive single-run CI

Do not feed all customer waits from one run to an IID t interval. Positive serial
dependence can severely understate variance. Law (2020) illustrates dramatic
undercoverage from this approach.

For one long steady-state run, use a justified output-analysis method such as batch
means, spectral methods, or regenerative analysis with diagnostics. The bundled
CLI deliberately implements independent replications, not a naive single-run CI.

## 6. Warm-up and transient bias

Warm-up is an estimand/study-design issue, not an `Environment` option. SimPy has no
automatic 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

