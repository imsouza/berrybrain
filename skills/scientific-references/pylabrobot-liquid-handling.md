---
id: sciref-pylabrobot-liquid-handling
name: "Scientific Ref: Liquid handling"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pylabrobot): Liquid handling"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pylabrobot liquid handling"
  - "liquid handling"
keywords:
  - "pylabrobot"
  - "liquid"
  - "handling"
  - "specialized"
  - "scientific"
  - "reference"
---

# Liquid handling

Verified against **PyLabRobot 0.2.2** on **2026-10-01**. Examples in this
reference are planning or chatterbox-only. They are not authorization to connect
to a robot.

## Stable frontend and backend

```python
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import LiquidHandlerChatterboxBackend
from pylabrobot.resources.hamilton import STARLetDeck

lh = LiquidHandler(
    backend=LiquidHandlerChatterboxBackend(num_channels=8),
    deck=STARLetDeck(),
)
await lh.setup()  # prints operations; no hardware transport
```

For 0.2.2, the important frontend signatures are:

```text
pick_up_tips(tip_spots, use_channels=None, offsets=None, **backend_kwargs)
drop_tips(tip_spots, use_channels=None, offsets=None,
          allow_nonzero_volume=False, **backend_kwargs)
return_tips(use_channels=None, allow_nonzero_volume=False, offsets=None,
            **backend_kwargs)
aspirate(resources, vols, use_channels=None, flow_rates=None, offsets=None,
         liquid_height=None, blow_out_air_volume=None, spread="wide",
         mix=None, **backend_kwargs)
dispense(resources, vols, use_channels=None, flow_rates=None, offsets=None,
         liquid_height=None, blow_out_air_volume=None, spread="wide",
         mix=None, **backend_kwargs)
```

Volumes are microlitres (`uL`), coordinates/heights are millimetres (`mm`), and
flow rates are `uL/s` unless the exact backend page says otherwise. Use lists
whose lengths agree with selected resources/channels; do not rely on scalar
broadcasting copied from an older example.

## Safe operation shape

With the software-only backend and already assigned resources:

```python
source.get_well("A1").tracker.set_volume(100.0)  # bookkeeping only
destination.get_well("A1").tracker.set_volume(0.0)

await lh.pick_up_tips(tips["A1"])
await lh.aspirate(
    source["A1"],
    vols=[25.0],
    use_channels=[0],
    flow_rates=[50.0],
    liquid_height=[1.0],
)
await lh.dispense(
    destination["A1"],
    vols=[25.0],
    use_channels=[0],
    flow_rates=[75.0],
    liquid_height=[2.0],
)
await lh.return_tips()
```

Before translating this to any physical system, verify:

- resource and well identity, actual position, orientation, dimensions, and
  reachability;
- source fill volume **and dead volume**; destination capacity and headspace;
- tip model, fitting, filter, capacity, rack state, liquid compatibility, and
  channel compatibility;
- 0-based `use_channels` mapping against the physical head and mounted tools;
- volume, length, rate, and time units;
- aspiration/dispense height, offset, rate, settling, blowout, mixing, air gaps,
  surface behavior, and validated liquid class;
- contamination grouping, filtered-tip requirement, tip reuse prohibition or
  validated policy, waste route, and carryover controls.

The bundled transfer planner makes the conservative choice of one new tip per
CSV row.

## `transfer()` is not the old plate-copy API

In 0.2.2 the verified signature is:

```text
transfer(source: Well, targets: List[Well], source_vol=None, ratios=None,
         target_vols=None, aspiration_flow_rate=None,
         dispense_flow_rates=None, **backend_kwargs)
```

It represents distribution from one source to multiple targets. Old examples
that pass parallel `source=source_plate["A1:H12"]`, `dest=...`, and `vols=...`
do not match this stable signature. For one-to-one transfers, plan explicit
aspirate/dispense pairs and validate channel/tip state.

## Tip tracking

Enable tracking before operations:

```python
from pylabrobot.resources import set_tip_tracking

set_tip_tracking(True)
```

Tip racks normally start populated; supported factories accept
`with_tips=False`, and `TipRack.fill()`, `empty()`, and `set_tip_state(...)`
modify planned state. `return_tips()` depends on operation history. Tip tracking
can catch inconsistent planned operations, but it cannot detect whether a tip
is physically present, seated, blocked, damaged, or the expected type.

Never disable tracking merely to bypass `NoTipError` or `HasTipError`. Reconcile
the physical deck and planned state instead.

## Volume tracking is bookkeeping

```python
from pylabrobot.resources import set_volume_tracking

set_volume_tracking(True)
well.tracker.set_volume(200.0)
used_uL = well.tracker.get_used_volume()
free_uL = well.tracker.get_free_volume()
```

`set_volume()` and `load_state()` do not validate the initial physical value
against capacity. Validate finite, nonnegative starting volumes and capacity
before seeding trackers. The tracker does not track chemical composition:
deprecated `get_liquids()` returns unknown liquid identity.

The `VolumeTracker` updates planned volumes and can reject under-aspiration,
tip overfill, or well overfill. It does **not** measure a meniscus or confirm
liquid identity. Initial state must come from a trusted preparation record and
human reconciliation.

Keep dead volume separate from geometric capacity. The tracker may allow a
withdrawal that is physically unreliable because of vessel shape, tilt,
surface tension, foam, viscosity, or required submersion.

### Physical liquid detection is backend-specific

Hamilton STAR liquid-level detection is a separate physical feature. Stable
STAR docs expose backend kwargs such as `lld_mode`, `immersion_depth`, and
`surface_following_distance`. It is not portable to all backends and is not
enabled by volume tracking. Validate the model, sensors, consumables, conductive
properties, firmware behavior, failure handling, and channel-specific values
before considering it.

## Liquid classes

There is no stable generic import:

```python
# Invalid in 0.2.2:
# from pylabrobot.liquid_handling import LiquidClass
```

Hamilton liquid classes are vendor-specific:

```python
from pylabrobot.liquid_handling.liquid_classes.hamilton import HamiltonLiquidClass
from pylabrobot.liquid_handling.liquid_classes.hamilton.star import (
    HighVolumeFilter_Water_DispenseSurface_Part,
)

await lh.aspirate(
    source["A1"],
    vols=[100.0],
    hamilton_liquid_classes=[
        HighVolumeFilter_Water_DispenseSurface_Part
    ],
)
```

This STAR example is **illustrative and source-verified only**; it was not
executed on hardware. The keyword is not a universal frontend contract.
`TecanLiquidClass` and `get_liquid_class` exist under
`pylabrobot.liquid_handling.liquid_classes.tecan`, but are a different
vendor-specific system.

Do not select a class from its name alone. Review liquid, tip, h

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

