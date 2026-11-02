---
id: sciref-opentrons-integration-liquid-handling
name: "Scientific Ref: Liquid Handling Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (opentrons-integration): Liquid Handling Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "opentrons integration liquid handling"
  - "liquid handling guide"
keywords:
  - "opentrons"
  - "integration"
  - "liquid"
  - "handling"
  - "specialized"
  - "scientific"
  - "reference"
---

# Liquid Handling Guide

Choose commands from the physical behavior the assay needs, not from which call
is shortest to write. Every command still depends on correct liquid volumes,
labware geometry, pipette range, tips, and contamination controls.

## Command Layers

### Building-block commands

Use when aspiration and dispensing need independent control:

```python
pipette.pick_up_tip()
pipette.aspirate(50, source.bottom(z=1), flow_rate=25)
protocol.delay(seconds=1)
pipette.dispense(50, destination.bottom(z=2), flow_rate=20, push_out=5)
pipette.blow_out(destination.top(z=-1))
pipette.drop_tip()
```

Advantages:

- Explicit position and order.
- Independent flow rates and delays.
- Fine control for viscous, volatile, foaming, low-volume, or bead workflows.

Costs:

- The author owns tip state and volume state.
- More opportunities to aspirate with no tip, overfill the pipette, or leave
  residual volume.

### Standard complex commands

Use for conventional source-to-destination mappings:

```python
pipette.transfer(
    volume=50,
    source=source_plate.wells()[:8],
    dest=destination_plate.wells()[:8],
    new_tip="always",
    mix_after=(3, 30),
)
```

- `transfer()`: one or more source-to-destination transfers.
- `distribute()`: one source to many destinations, normally with an excess
  disposal volume.
- `consolidate()`: many sources into one destination.

Inspect the simulation run log. Complex commands expand into many building
blocks, and their expansion changes with parameters and API level.

### Liquid-class complex commands, Flex API 2.24+

Use an Opentrons-verified class when the pipette/tip combination is supported
and the liquid resembles the verified model:

```python
viscous = protocol.get_liquid_class("glycerol_50")

pipette.transfer_with_liquid_class(
    liquid_class=viscous,
    volume=50,
    source=reservoir["A1"],
    dest=plate["A1"],
    new_tip="always",
    trash_location=trash,
)
```

Related methods:

- `distribute_with_liquid_class()`
- `consolidate_with_liquid_class()`

Verified classes include water, 80% ethanol, and 50% glycerol. A liquid class
controls multiple coupled properties such as flow rate, submerge and retract
behavior, delays, air gaps, positions, and push-out. Do not casually override
one property without testing the full result.

Opentrons-verified liquid classes are for supported Flex pipette and tip
combinations, not OT-2 pipettes.

## Source and Destination Mapping

Complex commands accept a single well or a sequence. Make the intended mapping
explicit:

- One source, one destination: one transfer.
- One source, many destinations: repeated transfers or a distribution.
- Many sources, one destination: repeated transfers or a consolidation.
- Equal-length source and destination lists: pairwise transfers.

Do not assume row-major ordering:

```python
# Explicit sample order is easier to audit.
sample_wells = [plate[name] for name in ("A1", "B1", "C1", "D1")]
```

For multi-channel pipettes, the referenced well anchors the pipette's primary
channel:

- A full 8-channel pipette normally targets an entire column by referencing its
  A-row well.
- A full 96-channel pipette addresses an entire 96-well rack or plate.
- A partial-column layout has a different primary channel; follow the layout
  documentation rather than reusing full-column assumptions.

## Tip Policy

`new_tip` is a contamination decision.

For standard `distribute()` and `consolidate()`, `new_tip="always"` still uses
one tip for the entire command, including refills. The isolation behavior below
applies to `transfer()`; use explicit transfers or building blocks for
independent samples. Liquid-class commands have their own policies.

| Policy | Typical use | Primary risk |
| --- | --- | --- |
| `"always"` | Independent samples, controls, or source-destination pairs | Higher tip consumption |
| `"once"` | Reagent distribution within one contamination domain | Returning a contaminated tip to a shared source |
| `"never"` | Explicit surrounding `pick_up_tip()` and `drop_tip()` | Hidden or invalid tip state |

For a shared reagent:

- Aspirating repeatedly from the same source with one tip may be acceptable only
  if the tip never contacts incompatible destination liquid.
- A submerged dispense can wet the exterior or interior of the tip.
- Touch tip, mix, or bottom-contact dispense increases contamination risk.
- Controls and samples generally require separate tips.

Calculate tips for every conditional path. Multi-channel operations consume
sets, not individual command calls.

## Flow Rate, Position, and Delays

### Flex 50 µL volume modes

The nominal 1–50 µL range spans two modes. With an empty Flex 1- or 8-channel
50 µL pipette, call `configure_for_volume()` before pickup:

```python
pipette.configure_for_volume(1)
pipette.pick_up_tip()
pipette.aspirate(1, source)
pipette.dispense(1, destination)
pipette.drop_tip()
```

Inputs 1–4.9 µL select a 1–30 µL mode; inputs 5–50 µL select a 5–50 µL mode.
Tips may further limit capacity. Reconfigure while empty when changing modes,
and requalify low-volume delivery for the actual liquid. Simulation validates
the mode/range contract, not accuracy at 1 µL.

The 10.0.0 simulator reports `min_volume=0.5` in low-volume mode, below the
official guide's 1 µL lower limit. Keep the documented 1 µL limit unless
Opentrons explicitly qualifies a lower range for the exact hardware and tips;
the property alone is not evidence of accuracy below 1 µL. Mode changes also
reset flow rates, so apply any validated custom rate after changing mode.

### Relative and absolute rates

`rate=` multiplies the configured flow rate:

```python
pipette.aspirate(50, source, rate=0.5)
```

Supported modern APIs also accept absolute flow-rate arguments:

```python
pipette.aspirate(50, source, flow_rate=25)
```

Use one form per action. Absolute units are µL/s. Establish values through
liquid-specific testing rather than copying another pipette's settings.

### Positions

```python
source.bottom(z=1)
source.top(z=-2)
destination.center()
```

- Bottom aspiration reduces residual volume but increases collision and pellet
  disturbance risk.
- Top or near-top dispensing can reduce contact contamination but may splash.
- Side offsets can reduce foaming but require known well geometry.
- `touch_tip()` can be unsafe in large wells and reservoirs; API 2.28+ rejects
  certain large-space uses.

### Air gaps and push out

Air gaps can reduce dripping but occupy pipette 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

