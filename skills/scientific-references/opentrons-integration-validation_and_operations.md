---
id: sciref-opentrons-integration-validation-and-operations
name: "Scientific Ref: Validation and Operations"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (opentrons-integration): Validation and Operations"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "opentrons integration validation operations"
  - "validation and operations"
keywords:
  - "opentrons"
  - "integration"
  - "validation"
  - "operations"
  - "specialized"
  - "scientific"
  - "reference"
---

# Validation and Operations

Use layered validation. A protocol is not ready for live samples merely because
it compiles or simulates.

## Reproducible Local Environment

The skill pins separate compatibility environments:

- `requirements-flex.txt`: `opentrons==10.0.0`, tested Flex templates at API 2.29
  plus an API 2.30 meniscus regression. Documented robot maximum is 2.30.
- `requirements-ot2.txt`: `opentrons==9.0.0`, OT-2 API 2.28.

One-shot simulation:

```bash
# Flex
uv run --no-project --isolated --python 3.12 --with "opentrons==10.0.0" opentrons_simulate protocol.py

# OT-2
uv run --no-project --isolated --python 3.12 --with "opentrons==9.0.0" opentrons_simulate protocol.py
```

Dedicated Flex environment:

```bash
uv venv --python 3.12 .venv-opentrons
uv pip install --python .venv-opentrons/bin/python -r skills/opentrons-integration/requirements-flex.txt
.venv-opentrons/bin/opentrons_simulate protocol.py
```

Use `requirements-ot2.txt` instead for the OT-2 compatibility environment.
`opentrons==10.0.0` intentionally rejects OT-2 protocols after the release-line
split; the current OT-2 App remains the authoritative OT-2 analyzer.

Check the package and maximum API implemented by the local library:

```bash
uv run --no-project --isolated --python 3.12 --with "opentrons==10.0.0" python -c \
  "import opentrons; from opentrons import protocol_api; print(opentrons.__version__, protocol_api.MAX_SUPPORTED_VERSION)"
```

For released package 10.0.0 this command prints `10.0.0 2.31`, although the
official robot versioning page documents Flex only through API 2.30. That
constant describes the library, not permission to target 2.31 on a robot.

The local package does not update robot software. A protocol can simulate
locally and still request an API level unavailable on the target robot.

## Validation Ladder

### 1. Syntax and import

```bash
python -m py_compile protocol.py
```

This catches Python syntax errors only. It does not instantiate Protocol API
objects or validate deck geometry.

### 2. Local simulation

```bash
# Flex
uv run --no-project --isolated --python 3.12 --with "opentrons==10.0.0" opentrons_simulate protocol.py

# OT-2
uv run --no-project --isolated --python 3.12 --with "opentrons==9.0.0" opentrons_simulate protocol.py
```

Review:

- Robot type and API level.
- Every loaded labware, adapter, fixture, pipette, and module.
- Expanded command order.
- Tip pickup and disposal.
- Source and destination wells.
- Mix, air-gap, blowout, delay, and pause placement.
- Module state transitions.
- Gripper and labware moves.
- Unexpected warnings.

Useful simulator options:

```bash
# More diagnostic logs
opentrons_simulate -l info protocol.py

# Custom labware directory; repeat -L as needed
opentrons_simulate -L custom_labware protocol.py

# Add only named data files; repeat -d as needed
opentrons_simulate -d plate_map.csv protocol.py

# Experimental estimate
opentrons_simulate -e protocol.py
```

Prefer `-d` over `-D` for data because `-D` loads every file in a directory
into memory. Never point `-D` at a directory containing credentials, unrelated
data, or large files.

The current directory is searched for custom labware implicitly, but explicit
`-L` paths make validation more reproducible.

### 3. Resource audit

Independently calculate:

- Individual tips or multi-channel tip sets.
- Source volume, disposal volume, dead volume, mixing loss, and reserve.
- Maximum intermediate volume of every destination.
- Pipette capacity including air gaps.
- Module, adapter, staging, trash, and waste positions.
- Lids and Gripper paths.
- Runtime under worst-case parameters.

Simulation does not prove that the liquid budget is sufficient.

### 4. Opentrons App analysis

Use the App appropriate for the target robot. At API 2.29 and newer, Flex and
OT-2 use separate software and App release lines.

1. Connect to the intended robot.
2. Import the Python protocol and required custom labware or data.
3. Require successful protocol analysis.
4. Review analysis warnings and errors; do not bypass them.
5. Check the starting deck and module setup.
6. Set runtime parameters and inspect the resulting protocol.
7. Review protocol visualization and run preview.
8. Verify labware offsets or Labware Position Check results.
9. Confirm installed pipettes, mounts, modules, and firmware.

App analysis is closer to the target robot than local simulation, but it still
does not verify actual liquids, tips, caps, seals, or calibration.

### 5. Operator review

Use a second-person check for:

- Correct protocol revision.
- Correct robot.
- Deck map against physical deck.
- Labware identity and orientation.
- Tip type and sufficient count.
- Source identity and volume.
- Destination capacity.
- Runtime parameter values.
- Required manual steps.
- Waste capacity.
- Safety controls and emergency stop access.

### 6. Dry run

For a new or materially changed method:

- Use water or another validated nonhazardous surrogate.
- Remove valuable samples and hazardous reagents.
- Start with low-risk geometry and reduced speed where feasible.
- Check pickup, aspiration depth, dispense depth, mixing, and disposal.
- Observe every Gripper, lid, Stacker, and partial-nozzle move.
- Verify module transitions and operator prompts.
- Measure delivered volumes when accuracy matters.

A tip-only dry run is appropriate for new partial-nozzle layouts.

### 7. Controlled release

Keep:

- Protocol file hash or version.
- `opentrons` package version used in local simulation.
- Robot software and App versions.
- Custom labware definitions and versions.
- Runtime parameter record.
- Dry-run and qualification results.
- Operator and reviewer sign-off as required by the lab's quality system.

## What Simulation Does Not Validate

- Pipette calibration or mechanical wear.
- Labware manufacturing variation or placement error.
- Physical caps, seals, lids, warped plates, or obstructions.
- Actual liquid volume or identity.
- Viscosity, volatility, surface tension, foaming, or aerosols.
- Bead settling, pellet location, or cell sedimentation.
- Reliable liquid-level sensing with the chosen liquid.
- Gripper friction and every collision scenario.
- Module thermal equilibration inside the sample.
- Plate-reader optical performance; simulated readings are zeros.
- Operator compliance with a pause message.

## Runtime Parameter Testing

The default value should always produce a meaningful local simulation.

For each parameter:

- Test mi

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

