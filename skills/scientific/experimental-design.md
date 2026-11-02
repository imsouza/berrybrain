---
id: sci-experimental-design
name: "Scientific: experimental-design"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Designs experiments and studies BEFORE data is collected — choosing a design, randomizing, blocking, and laying out treatment combinations so results are interpretable. Use whenever someone is planning a study, asks how to assign subjects/samples to groups, mentions randomization"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "experimental design"
  - "experimental-design"
keywords:
  - "experimental"
  - "design"
  - "designs"
  - "experiments"
  - "studies"
  - "before"
  - "collected"
  - "choosing"
---

# Experimental Design

## Overview

The design of a study — how units are assigned to conditions, what is held constant, what is varied, and in what structure — determines what questions the data can answer. No analysis can rescue a confounded or pseudoreplicated design after the fact. This skill is about the decisions made *before* data collection: picking a design that isolates the effect of interest, randomizing to license causal claims, blocking to remove known nuisance variation, and structuring multi-factor experiments so effects are estimable rather than tangled together.

The three ideas behind almost every good design (Fisher's principles):
- **Randomization** — assign treatments at random so that confounders, known and unknown, are balanced in expectation. This is what turns a comparison into a causal claim.
- **Replication** — independent repetition at the right level, so you can estimate variability and your effects aren't artifacts of a single unit. The most common fatal error is **pseudoreplication**: counting repeated measurements on the same unit as independent replicates.
- **Blocking / local control** — group similar units (by batch, day, site, litter) and randomize within blocks, removing that nuisance variation from the error term instead of letting it inflate noise.

This skill helps you choose among design types, generate the actual randomization or DOE layout (with reproducible scripts), and avoid the structural mistakes that make data uninterpretable.

## When to Use This Skill

- Planning any comparative experiment or trial and deciding how to assign units
- Randomizing subjects/samples to arms (simple, blocked, stratified, or cluster)
- Removing nuisance variation by blocking or stratification
- Designing multi-factor experiments: full or fractional factorial, screening designs
- Optimizing a response over continuous factors (response-surface designs)
- Within-subject / repeated-measures, crossover, split-plot, or Latin-square designs
- Cluster- or group-randomized designs (sites, clinics, classrooms, litters)
- Deciding the number and level of replicates and avoiding pseudoreplication
- Sequential, group-sequential, or adaptive designs with interim analyses
- Laying out plates/batches and randomizing run order to defeat drift

## Installation

```bash
uv venv --python 3.13 .venv-design
uv pip install --python .venv-design/bin/python "numpy==2.5.3" "pandas==3.0.6" "pydoe==1.5.0"
```

`pyDOE3` was [archived in May 2026](https://github.com/relf/pyDOE3); active
development returned to [pydoe](https://pydoe.github.io/pydoe/). The bundled
wrappers target `pydoe==1.5.0`, imported as lowercase `pydoe`, and return
designs in real factor units. All seven DOE wrappers and both script demos were
executed with Python 3.13, NumPy 2.5.3, pandas 3.0.6, and SciPy 1.18.1. On
Windows, the environment interpreter is `.venv-design/Scripts/python.exe`.
Archive the environment versions and exported schedules: a seed alone does not
promise identical output across package or script upgrades.

---

## Choosing a design

Start from the question and the structure of your units, not from a favorite design.

```
What are you trying to learn?
│
├─ Compare a few predefined conditions (A vs B vs C)?
│   ├─ Units independent, possibly with a known nuisance factor (day, batch, site)?
│   │     → Completely randomized (no nuisance) or RANDOMIZED BLOCK design.
│   ├─ Each unit can receive every condition in sequence (washout possible)?
│   │     → CROSSOVER / repeated-measures design (watch carry-over and correlation).
│   └─ You can only randomize groups, not individuals (schools, clinics)?
│         → CLUSTER-randomized design (account for clustering; see pseudoreplication).
│
├─ Screen MANY factors (5+) to find the few that matter?
│     → FRACTIONAL FACTORIAL or PLACKETT-BURMAN screening design.
│
├─ Quantify main effects AND interactions among a handful of factors?
│     → FULL 2^k FACTORIAL design.
│
├─ Find the settings that OPTIMIZE a response (curvature matters)?
│     → RESPONSE-SURFACE design: central composite or Box-Behnken.
│
└─ Explore a simulation/computer model over a continuous space?
      → SPACE-FILLING design: Latin hypercube.
```

Detailed guidance per branch:
- **Randomization, blocking, stratification, controls** → `references/randomization_and_blocking.md`
- **Factorial, fractional-factorial, screening, response-surface, DOE concepts (aliasing, resolution)** → `references/factorial_and_doe.md`
- **Crossover, repeated-measures, split-plot, Latin-square, cluster, nested designs** → `references/design_types.md`
- **Sequential, group-sequential, and adaptive designs (interim analyses)** → `references/sequential_and_adaptive.md`

---

## Generating the design

Two scripts produce ready-to-use, reproducible layouts. Run them from the skill's
`scripts/` directory or add it to `sys.path`. Seeds support reproducible layouts
within the recorded software environment.
The default seed is for demonstrations; choose and securely record a study-specific
seed for a real allocation. These helpers do not implement an enrollment system
or conceal future assignments from recruiters.

### Randomization / allocation schedules — `scripts/randomization.py`

```python
from randomization import (
    simple_randomization, block_randomization,
    stratified_block_randomization, cluster_randomization,
    assign_factorial_runs, arm_balance,
)

# Permuted blocks balance at completed-block boundaries.
# A partial final block or interim prefix need not have the requested ratio.
sched = block_randomization(n=60, arms=["treatment", "control"], seed=42)

# Balance a prognostic variable across arms by randomizing within each stratum
sched = stratified_block_randomization({"siteA": 30, "siteB": 30},
                                       arms=["drug", "placebo"], ratio=(2, 1), seed=42)

# Randomize whole clusters, not individuals (the cluster is the unit)
sched = cluster_randomization(["clinic1", "clinic2", "clinic3", "clinic4"], seed=42)

arm_balance(sched)            # sanity-check the counts per arm
sched.to_csv("allocation_schedule.csv", index=False)
```

Choosing among them: **simple** is fine for large n but can produce imbalance with
small n; **block** enforces the ratio within each complete block; **stratified block**
does this independently within each stratum; **cluster** is mandatory when the intervention
is delivered at a group level. See `references/randomization_and_blocking.md`.

F

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

