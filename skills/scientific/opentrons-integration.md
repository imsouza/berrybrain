---
id: sci-opentrons-integration
name: "Scientific: opentrons-integration"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Authors, reviews, migrates, simulates, and troubleshoots official Opentrons Python Protocol API v2 protocols for Flex and OT-2 robots. Use for robot-specific liquid handling, deck and labware setup, pipettes, modules, runtime parameters, liquid classes, and Opentrons App analysis"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "opentrons integration"
  - "opentrons-integration"
keywords:
  - "opentrons"
  - "integration"
  - "authors"
  - "reviews"
  - "migrates"
  - "simulates"
  - "troubleshoots"
  - "official"
---

# Opentrons Integration

## Overview

Create production-minded Python Protocol API v2 protocols for Opentrons Flex and
OT-2. This skill covers protocol structure, hardware and deck configuration,
liquid handling, runtime customization, module control, simulation, and safe
deployment.

The verified baseline as of **2026-10-01** is:

- `opentrons==10.0.0` for reproducible Flex simulation.
- `opentrons==9.0.0` for local OT-2 API 2.28 compatibility simulation.
- Flex supports API levels 2.15 through 2.30 on current software.
- OT-2 supports API levels 2.0 through 2.28 on current software.
- API 2.29 and later are Flex-only at this baseline. Keep OT-2 at 2.28 or lower.
- Bundled Flex templates retain API 2.29 because step grouping is their newest
  required feature. API 2.30 fixes start-only meniscus aspiration.
- The 10.0.0 library reports a local maximum of 2.31, ahead of the documented
  robot maximum 2.30. Do not infer robot support from that constant.

Read `references/sources.md` for the upstream documentation used for this
snapshot. Recheck the official versioning page before targeting newer robot
software.

## Safety Boundary

Opentrons protocols control physical equipment. Never treat successful Python
syntax or local simulation as permission to run on a robot.

Before live execution:

1. Simulate locally with the same pinned `opentrons` version used for authoring.
2. Import the protocol into the correct Opentrons App and require successful
   analysis.
3. Verify robot model, software, pipettes, mounts, modules, adapters, labware
   definitions, deck fixtures, tip count, source volumes, dead volumes, and
   destination capacity.
4. Review the run preview and deck map with the operator.
5. Perform a slow dry run with nonhazardous liquid when geometry, custom
   labware, partial tip pickup, or gripper moves are new.
6. Keep the emergency stop accessible and follow site-specific biosafety,
   chemical-safety, and contamination-control procedures.

Simulation cannot verify physical calibration, liquid properties, meniscus
behavior, labware manufacturing tolerances, cap or seal removal, tubing, or all
possible collisions.

## Choose the Right Interface

Use this skill for Python files imported into the Opentrons App and run through
the Protocol API.

- Use **Protocol Designer** for supported no-code workflows.
- Use **PyLabRobot** for a hardware-agnostic workflow spanning vendors.
- Treat the robot's HTTP API as a separate integration surface. If direct HTTP
  control is explicitly required, use the OpenAPI document served by the target
  robot and do not infer endpoints from Protocol API methods.

## Required Intake

Do not write final protocol code until these facts are known:

- Robot: Flex or OT-2, plus installed robot software.
- Pipette model, volume range, channel count, and mount.
- Modules and generations; Flex Gripper or Stacker availability.
- Exact labware API load names and custom definition files, if any.
- Deck fixtures: Flex trash bin, waste chute, staging slots, or Stackers.
- Source volumes, destination volumes, dead volume, mixing needs, and liquid
  characteristics.
- Tip policy: contamination boundaries, reuse policy, filters, partial pickup,
  and total tips.
- Operator interventions, incubation timing, runtime parameters, and output
  files.
- Acceptance criteria: tolerated volume error, required controls, and dry-run
  plan.

If any physical configuration is uncertain, produce a parameterized draft and
an explicit assumptions list rather than guessing.

## Install and Simulate

Flex:

```bash
uv run --no-project --isolated --python 3.12 --with "opentrons==10.0.0" opentrons_simulate protocol.py
```

OT-2 API 2.28:

```bash
uv run --no-project --isolated --python 3.12 --with "opentrons==9.0.0" opentrons_simulate protocol.py
```

The 10.0.0 package rejects OT-2 protocols after the Flex/OT-2
release-line split. Always complete OT-2 analysis in the current OT-2 App.

For a dedicated Flex environment:

```bash
uv venv --python 3.12 .venv-opentrons
uv pip install --python .venv-opentrons/bin/python -r skills/opentrons-integration/requirements-flex.txt
.venv-opentrons/bin/opentrons_simulate protocol.py
```

Use `requirements-ot2.txt` instead for an OT-2 compatibility environment. On
Windows, invoke the executable from `.venv-opentrons\Scripts\opentrons_simulate.exe`.
Local simulation is for Python protocols; import Protocol Designer JSON files
into the appropriate Opentrons App instead.

## Protocol Skeletons

### Flex, API 2.29

For Flex, `requirements` is mandatory. Put `apiLevel` only in `requirements`,
not in both `metadata` and `requirements`.

```python
from opentrons import protocol_api

metadata = {
    "protocolName": "Flex transfer",
    "author": "Your Name",
    "description": "Transfer buffer into a plate.",
}
requirements = {"robotType": "Flex", "apiLevel": "2.29"}


def run(protocol: protocol_api.ProtocolContext) -> None:
    tips = protocol.load_labware(
        "opentrons_flex_96_tiprack_200ul", "D1"
    )
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "D2")
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "C2")
    protocol.load_trash_bin("A3")
    pipette = protocol.load_instrument(
        "flex_1channel_1000", "left", tip_racks=[tips]
    )

    pipette.transfer(
        100,
        reservoir["A1"],
        plate["A1"],
        new_tip="always",
    )
```

### OT-2, API 2.28

For OT-2 API 2.15 and later, a `requirements` block is recommended. OT-2 has a
fixed trash in slot 12; do not call `load_trash_bin()`.

```python
from opentrons import protocol_api

metadata = {
    "protocolName": "OT-2 transfer",
    "author": "Your Name",
}
requirements = {"robotType": "OT-2", "apiLevel": "2.28"}


def run(protocol: protocol_api.ProtocolContext) -> None:
    tips = protocol.load_labware("opentrons_96_tiprack_300ul", "1")
    reservoir = protocol.load_labware("nest_12_reservoir_15ml", "2")
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "3")
    pipette = protocol.load_instrument(
        "p300_single_gen2", "left", tip_racks=[tips]
    )
    pipette.transfer(100, reservoir["A1"], plate["A1"])
```

Use the lowest API level that provides every required feature when a protocol
must run across a mixed software fleet. Use the current maximum only when the
workflow needs its behavior or capabilities.

## Authoring Workflow

### 1. Select robot and API level

Check the maximum supported API in the App unde

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

