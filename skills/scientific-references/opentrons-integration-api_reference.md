---
id: sciref-opentrons-integration-api-reference
name: "Scientific Ref: Opentrons Protocol API v2 Quick Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (opentrons-integration): Opentrons Protocol API v2 Quick Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "opentrons integration api reference"
  - "opentrons protocol api v2 quick reference"
keywords:
  - "opentrons"
  - "integration"
  - "api"
  - "reference"
  - "specialized"
  - "scientific"
---

# Opentrons Protocol API v2 Quick Reference

Verified against `opentrons==10.0.0` and the official documentation on
2026-10-01. This is a curated authoring reference, not a replacement for the
[ProtocolContext API reference](https://docs.opentrons.com/python-api/reference/protocols/)
and its linked class references.

## Version Baseline

| Robot | Supported API range on current software | Documented robot maximum |
| --- | --- | --- |
| Flex | 2.15–2.30 | 2.30 |
| OT-2 | 2.0–2.28 | 2.28 |

API versions are independent of the installed Python package and robot software.
Choose the lowest API level that includes every required feature. A protocol
specifying a higher level than the robot supports will fail analysis.

```python
metadata = {
    "protocolName": "Example",
    "author": "Your Name",
    "description": "Purpose and scope.",
}
requirements = {"robotType": "Flex", "apiLevel": "2.29"}
```

Rules:

- Flex always requires `requirements`.
- `requirements` is recommended for OT-2 protocols using API 2.15+.
- Put `apiLevel` in exactly one place. When using `requirements`, remove it from
  `metadata`.
- `run(protocol: protocol_api.ProtocolContext)` is the required entry point.

## Features Added After API 2.19

| API | High-value additions |
| --- | --- |
| 2.20 | CSV runtime parameters; liquid presence detection; row, single, and partial-column nozzle layouts |
| 2.21 | `AbsorbanceReaderContext` and `absorbanceReaderV1` |
| 2.22 | `Labware.load_liquid()`, `load_liquid_by_well()`, and `load_empty()`; robot motor control |
| 2.23 | `Well.meniscus()`; labware lids and lid moves |
| 2.24 | Liquid classes; advanced liquid-class complex commands; absolute flow-rate options |
| 2.25 | `FlexStackerContext`; `flexStackerModuleV1`; `flex_96channel_200` |
| 2.26 | Liquid-class support for `flex_96channel_200` |
| 2.27 | Concurrent module actions; dynamic aspirate, dispense, and mix; `capture_image()`; explicit liquid-class tips |
| 2.28 | Flex 20 µL tips; partial-tip return; thermocycler ramp rate; empty tip-rack tracking |
| 2.29 | Protocol step grouping |
| 2.30 | Start-only meniscus aspiration without an end location |

See
[Versioning](https://docs.opentrons.com/python-api/versioning/) for complete
behavior changes and robot-software mappings.

## Pipette Load Names

### Flex

| Pipette | Nominal range | Load name |
| --- | ---: | --- |
| 1-Channel 50 µL | 1–50 µL | `flex_1channel_50` |
| 1-Channel 1000 µL | 5–1000 µL | `flex_1channel_1000` |
| 8-Channel 50 µL | 1–50 µL | `flex_8channel_50` |
| 8-Channel 1000 µL | 5–1000 µL | `flex_8channel_1000` |
| 96-Channel 200 µL | 1–200 µL | `flex_96channel_200` |
| 96-Channel 1000 µL | 5–1000 µL | `flex_96channel_1000` |

Flex 50 µL pipettes need `configure_for_volume(1)` (or the intended 1–4.9 µL
volume) before low-volume handling. Call it while empty, preferably before tip
pickup. That mode permits 1–30 µL; normal mode permits 5–50 µL. Tip capacity
can impose a lower maximum. These are documented ranges; the simulator's
lower `min_volume` value does not qualify sub-1 µL dispensing. Changing mode
resets flow rates. See the
[volume-mode guide](https://docs.opentrons.com/python-api/pipettes/volume-modes/).

The 96-channel pipette occupies both mounts. From API 2.16 onward its `mount`
argument is optional.

### OT-2 GEN2

| Pipette | Nominal range | Load name |
| --- | ---: | --- |
| P20 single | 1–20 µL | `p20_single_gen2` |
| P20 multi | 1–20 µL | `p20_multi_gen2` |
| P300 single | 20–300 µL | `p300_single_gen2` |
| P300 multi | 20–300 µL | `p300_multi_gen2` |
| P1000 single | 100–1000 µL | `p1000_single_gen2` |

GEN1 OT-2 pipettes have different load names. Check
[Loading Pipettes](https://docs.opentrons.com/python-api/pipettes/loading/)
instead of guessing.

## Flex Tip Compatibility

| Pipette family | Compatible Flex tip-rack capacities |
| --- | --- |
| `flex_1channel_50`, `flex_8channel_50` | 20 µL, 50 µL |
| `flex_96channel_200` | 20 µL, 50 µL, 200 µL |
| `flex_1channel_1000`, `flex_8channel_1000`, `flex_96channel_1000` | 50 µL, 200 µL, 1000 µL |

Filter-tip load names insert `_filtertiprack_`, for example
`opentrons_flex_96_filtertiprack_200ul`.

Full-rack pickup by a Flex 96-channel pipette requires the Flex tip-rack
adapter. Partial pickup by that pipette must use a rack directly on the deck,
without the adapter.

## ProtocolContext

### Hardware and deck

```python
labware = protocol.load_labware(load_name, location, label=None)
adapter = protocol.load_adapter(load_name, location)
module = protocol.load_module(module_name, location=None)
pipette = protocol.load_instrument(
    instrument_name,
    mount,
    tip_racks=[tiprack],
)
trash = protocol.load_trash_bin("A3")  # Flex, API 2.16+
chute = protocol.load_waste_chute()     # Flex, fixed at D3
```

Useful methods:

- `load_labware_from_definition(definition, location, label=None)`
- `move_labware(labware, new_location, use_gripper=...)`
- `load_lid_stack(load_name, location, quantity)`
- `move_lid(source_location, new_location, use_gripper=...)`
- `define_liquid(name, description=None, display_color=None)`
- `get_liquid_class(name, version=None)` — API 2.24+
- `define_liquid_class(name, properties, base_liquid_class=None, display_name=None)` — API 2.24+

### Execution and organization

- `comment(msg)` — adds analysis-time text to the run log.
- `pause(msg=None)` — waits for the operator to resume in the App/touchscreen.
- `delay(seconds=0, minutes=0, msg=None)` — blocking delay.
- `home()` — homes robot axes.
- `is_simulating()` — identify local or App analysis.
- `group_steps(name, description=None)` — context manager, API 2.29.
- `create_and_start_step_group(name, description=None)` — returns a group whose
  `end_group()` method closes it, API 2.29.
- `capture_image()` — captures from the built-in camera, API 2.27.

Step groups only organize source and visualization; they do not change
execution.

## InstrumentContext

### Tips

```python
pipette.pick_up_tip()
pipette.drop_tip()
pipette.return_tip()
pipette.reset_tipracks()
```

In API 2.28+, `tiprack.set_empty()` can mark a rack empty so returned tips may be
tracked there. Only return tips when the protocol's contamination policy allows
it.

### Building-block commands

```python
pipette.aspirate(volume, source)
pipette.dispense(volume, destination, push_out=5)
pipette.air_gap(volume)
pipette.blow_out(destination.top())
pipette.touch_tip(destination)
pipette.mix(repetitions, volume, destination)
pipette.move_to(destination.to

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

