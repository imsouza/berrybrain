---
id: sciref-opentrons-integration-modules-and-deck
name: "Scientific Ref: Modules and Deck Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (opentrons-integration): Modules and Deck Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "opentrons integration modules deck"
  - "modules and deck guide"
keywords:
  - "opentrons"
  - "integration"
  - "modules"
  - "deck"
  - "specialized"
  - "scientific"
  - "reference"
---

# Modules and Deck Guide

Module compatibility is both an API question and a physical hardware question.
Confirm the robot model, module generation, caddy or adapter, firmware, deck
location, and labware before authoring commands.

## Robot Compatibility

| Hardware | Flex | OT-2 | Protocol API load name |
| --- | --- | --- | --- |
| Absorbance Plate Reader | Yes | No | `absorbanceReaderV1` |
| Flex Stacker | Yes | No | `flexStackerModuleV1` |
| Heater-Shaker GEN1 | Yes | Yes | `heaterShakerModuleV1` |
| Magnetic Block GEN1 | Yes | No | `magneticBlockV1` |
| Magnetic Module GEN1/GEN2 | No | Yes | `magnetic module` / `magnetic module gen2` |
| Temperature Module GEN2 | Yes | Yes | `temperature module gen2` |
| Thermocycler GEN2 | Yes | Yes | `thermocyclerModuleV2` |

Notes:

- Flex uses the passive Magnetic Block. The powered OT-2 Magnetic Module is not
  supported on Flex.
- Flex requires Thermocycler GEN2 for gripper-compatible operation.
- Older module generations may be supported only on OT-2. Match the load name
  to the exact hardware label.
- The HEPA/UV accessory is part of Flex operations but is not loaded and
  controlled as a Protocol API module.

See the current
[Flex module list](https://docs.opentrons.com/flex/modules/) and
[OT-2 module list](https://docs.opentrons.com/ot-2/modules/) before relying on
this snapshot.

## Deck Models

### Flex

- Working deck: A1–D3.
- Staging area: A4–D4; pipettes cannot reach it, but the Gripper can.
- Trash bins are loaded explicitly in supported column-1 or column-3 slots.
- The waste chute is loaded with `protocol.load_waste_chute()` and occupies D3.
- Powered module caddies and staging slots can conflict in the same row.
- Column-4 hardware can reserve or move through the corresponding column-3
  position.

```python
trash = protocol.load_trash_bin("A3")
chute = protocol.load_waste_chute()  # D3 only; do not load both into D3
```

Load only the fixtures physically installed for the run.

### OT-2

- User deck slots: 1–11.
- Fixed trash: slot 12.
- Do not call `load_trash_bin()` for the fixed trash.
- No Gripper or staging area.
- Labware moves are manual operator actions.

## Module Loading

```python
heater_shaker = protocol.load_module(
    module_name="heaterShakerModuleV1",
    location="D1",
)
```

Loading a powered module makes it a run requirement. The App will prevent the
run from starting unless the expected connected module is available.

Load labware through the module:

```python
hs_adapter = heater_shaker.load_adapter("opentrons_96_flat_bottom_adapter")
plate = hs_adapter.load_labware(
    "nest_96_wellplate_200ul_flat",
    label="Mixing Plate",
)
```

For a separate adapter:

```python
temperature_module = protocol.load_module(
    "temperature module gen2",
    "D3",
)
adapter = temperature_module.load_adapter(
    "opentrons_96_well_aluminum_block"
)
plate = adapter.load_labware(
    "opentrons_96_wellplate_200ul_pcr_full_skirt"
)
```

The API generally cannot prove that every unusual module, adapter, and labware
combination is physically valid. Check the official compatibility list.

## Temperature Module

```python
temperature_module.set_temperature(celsius=4)
# Pipetting or incubation commands...
temperature_module.deactivate()
```

`set_temperature()` blocks until the target is reached. In API 2.27+,
`start_set_temperature()` can run concurrently and returns a task. Wait for the
task before relying on the target temperature.

Operational checks:

- Use the correct aluminum block or adapter.
- Include condensation and cold-surface effects in the wet-lab method.
- Deactivate when the method no longer requires control.
- Do not assume the liquid itself instantly reaches the module temperature.

## Heater-Shaker

Typical sequence:

```python
heater_shaker.close_labware_latch()
heater_shaker.set_and_wait_for_temperature(37)
heater_shaker.set_and_wait_for_shake_speed(1000)
protocol.delay(minutes=5)
heater_shaker.deactivate_shaker()
heater_shaker.deactivate_heater()
```

Current context methods include `set_target_temperature()`,
`set_and_wait_for_temperature()`, `wait_for_temperature()`,
`set_and_wait_for_shake_speed()`, `deactivate_shaker()`, and
`deactivate_heater()`.

Always:

- Close the latch before shaking.
- Stop shaking before opening the latch or moving labware.
- Check maximum speed for the exact labware and fill volume.
- Account for clearance restrictions in neighboring slots.

API 2.27+ provides nonblocking shake and temperature operations for concurrent
work. Keep task handles and wait before a dependent step.

## Thermocycler

```python
thermocycler = protocol.load_module("thermocyclerModuleV2")
plate = thermocycler.load_labware(
    "opentrons_96_wellplate_200ul_pcr_full_skirt"
)

thermocycler.open_lid()
# Pipette into plate.
thermocycler.close_lid()
thermocycler.set_lid_temperature(temperature=105)
thermocycler.set_block_temperature(
    temperature=95,
    hold_time_seconds=180,
    block_max_volume=25,
)
thermocycler.execute_profile(
    steps=[
        {"temperature": 95, "hold_time_seconds": 15},
        {"temperature": 60, "hold_time_seconds": 30},
        {"temperature": 72, "hold_time_seconds": 30},
    ],
    repetitions=35,
    block_max_volume=25,
)
thermocycler.set_block_temperature(
    temperature=4,
    block_max_volume=25,
)
thermocycler.deactivate_lid()
```

API 2.28 adds an optional `ramp_rate` to block-temperature commands.

Checks:

- Correct plate and seal for the thermocycler.
- Before cycling, pause to confirm the compatible sealing setup. A reusable
  GEN2 automation seal attaches to the module lid, while a disposable Tough
  auto-sealing lid covers a compatible PCR plate. Never combine those two;
  follow the [lid-seal instructions](https://docs.opentrons.com/thermocycler/lid-seals/).
  Closing the heated lid does not itself establish correct seal installation.
- Lid closed before heating and cycling.
- `block_max_volume` matches the actual per-well reaction volume.
- Final hold behavior is intentional.
- Lid and block are deactivated or left active according to the method.
- No deck item conflicts with the thermocycler footprint.

## Magnetic Block, Flex

The Magnetic Block is passive. It has no engage or disengage methods.
Separation happens by moving compatible labware onto and off the block:

```python
magnetic_block = protocol.load_module("magneticBlockV1", "D1")

protocol.move_labware(
    labware=plate,
    new_location=magnetic_block,
    use_gripper=True,
)
protoc

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

