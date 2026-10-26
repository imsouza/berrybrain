---
id: sci-lab-hardware-cad
name: "Scientific: lab-hardware-cad"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Designs custom laboratory hardware as parametric build123d models and exports fabrication artifacts as STEP, STL, and DXF files - microfluidic chips and molds, optomechanical mounts and breadboard adapters, cuvette and microplate holders, tube racks, animal-behavior rigs, and 3D-"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "lab hardware cad"
  - "lab-hardware-cad"
keywords:
  - "lab"
  - "hardware"
  - "cad"
  - "designs"
  - "custom"
  - "laboratory"
  - "parametric"
  - "build"
---

# Lab Hardware CAD

Design physical research hardware as **parametric Python source**, export STEP as the
authoritative artifact, and verify the result both numerically and visually before anything
is fabricated.

The hard part of lab hardware is almost never the geometry. It is that the part must mate with
equipment whose dimensions are fixed by a published standard or a vendor drawing. A holder that
is 0.5 mm too wide does not fit the plate reader; a channel with the wrong aspect ratio collapses
during bonding; a mount whose bolt pattern is 25.4 mm instead of 25.0 mm will not reach the
optical table. This skill exists to keep those numbers correct and checked.

## When to use

Use for any request to design, model, or fabricate a physical part for a lab: chip, mold, mount,
adapter, holder, rack, bracket, enclosure, jig, fixture, arena, or maze. Also use to inspect or
modify an existing STEP file.

Do **not** use for finite-element analysis, computational fluid dynamics, molecular structure,
or scientific plotting. Those are different skills.

## Setup

```bash
uv venv --python 3.12 .venv-labcad
uv pip install --python .venv-labcad/bin/python "build123d==0.13.0" "matplotlib>=3.8"
```

build123d 0.13.0 requires Python >=3.11,<3.15 and pulls in the OpenCascade kernel through
`cadquery-ocp-novtk`. The wheel is large; install once per project and reuse it.

All bundled scripts take `--help`. `check.py standards` runs without build123d installed.

**Model files are executed, not parsed.** `gen.py`, `check.py`, and `snapshot.py` import a
`*_model.py` and call its `build()`, which runs arbitrary Python in the current environment. That
is inherent to parametric CAD — the source is the design. Only run model files authored in this
session or supplied by the user from a trusted location. If a model came from the internet, a
shared drive, or an untrusted colleague, read it before running it and say that you did.

## Required workflow

Follow these steps in order. Steps 5 and 6 are not optional, and step 6 is not waived by step 5
passing.

### 1. Route to a device family

Read the request, classify it, and load **exactly one** family reference. Do not load all four —
they are long, and mixing conventions between families is a common source of error.

| If the part is | Load |
| --- | --- |
| A chip, mold, channel network, flow cell, gasket, or anything with fluid ports | `references/microfluidics.md` |
| A mount, post, breadboard adapter, cage-system part, filter or sample holder in a beam path | `references/optomechanics.md` |
| An adapter, insert, rack, or holder for plates, cuvettes, tubes, slides, or dishes | `references/labware-adapters.md` |
| An arena, maze, head-fixation part, spout, tether, or extrusion-mounted enclosure for animal work | `references/behavior-rigs.md` |

If the part genuinely spans two families — a microfluidic chip that bolts to an optical table —
load the family that owns the **critical interface**, then read only the interface section of the
second. State in your response which family you routed to.

### 2. Establish the interface dimensions before any geometry

Every part has at least one mating interface. Before writing code, write down for each interface:

- the **source** of the dimension: a published standard, a vendor drawing, or a user measurement;
- the **nominal value and tolerance**;
- the **clearance or interference** you intend, and why.

Look the number up in `assets/standards.json` or the family reference. **Never write an interface
dimension from memory.** If the number is not in the standards file or the reference, ask the user
for the vendor drawing or the measurement rather than guessing. A guessed interface dimension is
the single most expensive failure mode in this skill.

A pocket receiving an external component is sized against that component's
**maximum material envelope** — nominal plus its plus-tolerance — and only then given clearance.
A shaft entering a hole instead uses the hole's minimum diameter; `envelope` does not model that case.

```bash
python scripts/check.py standards --list
python scripts/check.py standards --show slas-microplate-footprint
```

The bundled standard IDs (exact strings; do not guess variants): `slas-microplate-footprint`,
`slas-microplate-height`, `slas-microplate-flange`, `slas-well-positions-96`,
`slas-well-positions-384`, `slas-well-positions-1536`, `cuvette-standard-10mm`,
`optical-breadboard-metric`, `optical-breadboard-imperial`, `cage-system-30mm`,
`sm1-lens-tube-thread`.

If the part mates with nothing in this list, that is common and fine: declare no interfaces,
and name every interface dimension with its source (user spec, vendor drawing, measurement) as
**unchecked** in the report. Never declare against an unrelated standard to fill the gap — a
fabricated declaration is worse than an honest "nobody checked this".

### 3. Choose the process before choosing the geometry

Read `references/fabrication-limits.md`. Process determines minimum wall, minimum feature,
achievable tolerance, and whether the part survives autoclaving or contact with your solvent.
Do not assume FDM can hold ±0.05 mm without calibration. Cell-contact SLA parts need
a validated material and post-processing workflow plus assay-specific testing. Record the process and material in the model docstring.

### 4. Author a parametric model

Write `<part>_model.py`. The source is the authoritative artifact — **never hand-edit an exported
STEP file**, and never regenerate from a mesh.

Requirements:

- Every dimension that a user might change is a **module-level named constant** with units in the
  name: `bore_d_mm`, `wall_t_mm`, `post_h_mm`. No bare numbers in the body except 0, 1, and 2.
- Expose `build() -> Part`. `gen.py` calls it.
- Group parameters into an `INTERFACE` block (dimensions fixed by a standard, annotated with the
  standard ID) and a `DESIGN` block (dimensions you are free to choose).
- **Derive every computed dimension inside a function**, never at module level, so `--param`
  overrides actually reach it.
- Declare an `interfaces()` function returning the dimensions the part must fit, each with its
  standard ID and intent. This is what makes the interface machine-checkable in step 5.
  `intent` is `"envelope"` when the feature must **accept** any conforming part (a pocket, bore,
  or slot — checked one-sided at maximum material condition plus your clearance) and `"match"`
  when comparing against the nominal band, expand

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

