---
id: sciref-pylabrobot-material-handling
name: "Scientific Ref: Material handling, pumps, and environmental devices"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pylabrobot): Material handling, pumps, and environmental devices"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pylabrobot material handling"
  - "material handling, pumps, and environmental devices"
keywords:
  - "pylabrobot"
  - "material"
  - "handling"
  - "specialized"
  - "scientific"
  - "reference"
---

# Material handling, pumps, and environmental devices

Verified against **PyLabRobot 0.2.2** on **2026-10-01**. Every operation in
this domain can create physical motion, pressure, heat, or stored energy. The
snippets below identify APIs only; they do not connect to devices.

## Pumps

Stable frontend and one stable backend export:

```python
from pylabrobot.pumps import MasterflexBackend, Pump
```

Verified `Pump` methods:

```text
run_revolutions(num_revolutions)
run_continuously(speed)
run_for_duration(speed, duration)
pump_volume(speed, volume)
halt()
```

`pump_volume()` requires a `PumpCalibration`, converting requested volume to
time or revolutions. It is an open-loop estimate, not a measured delivery.
`start` and `calibrate(duration=..., speed=..., volume=...)` are not these
frontend methods. `stop()` closes the backend; `halt()` requests halted flow.
`run_for_duration()` does not halt in a `finally` block if its sleep is
cancelled. Review interruption handling with the exact backend before live use.

`MasterflexBackend(com_port)` is transport-specific. Do not instantiate it
during discovery. The current development machine table labels listed Masterflex L/S models
and Agrowtek Pump Array **Full**; this is separate from release/firmware support.

### Pump safety

Before a separately authorized run, verify:

- exact pump/head/tubing model, material, inner diameter, direction, occlusion,
  fittings, valves, clamps, and destination;
- calibrated relationship among command speed/revolutions/time and delivered
  volume for the current fluid, tubing age, backpressure, and temperature;
- prime/purge route, bubbles, siphoning, dead volume, residual volume, maximum
  pressure/flow, leak containment, and waste capacity;
- chemical/biological compatibility, cross-contamination controls, and tubing
  change policy;
- an accessible stop and safe behavior on disconnect, timeout, or partial
  delivery.

A time/speed command is not a measured volume. Record the calibration and
uncertainty; use a validated scale/flow sensor if closed-loop confirmation is
required.

## Heater shakers and shakers

Stable frontend imports:

```python
from pylabrobot.heating_shaking import (
    HamiltonHeaterShakerBackend,
    HeaterShaker,
    InhecoThermoshakeBackend,
)
from pylabrobot.shaking import Shaker
```

The stable class is `InhecoThermoshakeBackend` (lowercase `s` in
`Thermoshake`), not the stale `InhecoThermoShakeBackend`.

Verified `HeaterShaker` methods:

```text
set_temperature(temperature, passive=False)
get_temperature()
shake(speed, duration=None, **backend_kwargs)
stop_shaking(**backend_kwargs)
lock_plate(**backend_kwargs)
unlock_plate(**backend_kwargs)
```

The old names `set_shake_rate` and `set_temperature(None)` are not the verified
0.2.2 frontend signatures. Use the exact device page for deactivation/cooling
and do not substitute zero/`None` unless documented for that backend.

`HeaterShaker` construction requires `name`, dimensions, backend, and a
`child_location`. Backend construction is also device topology-specific:
`HamiltonHeaterShakerBackend(index, interface)` and
`InhecoThermoshakeBackend(index, control_box)` require approved shared
interfaces/controllers.

The current hosted development inventory labels Inheco Thermoshake variants
**WIP**, Hamilton Heater Shaker and QInstruments BioShake **Full**, and the
Opentrons Heater-Shaker Module **Full**. The old blanket **Full** claim for
Inheco was stale. A 0.2.2 import does not establish current device support.

### Heater/shaker safety

Confirm plate compatibility, mass, balance, lid/seal, locking, condensation,
spillage containment, orbit/speed limits, thermal limits, ramp/equilibration,
sensor calibration, and safe unlock temperature. Never unlock or move a plate
while shaking. Treat a requested setpoint as a command, not proof that the
sample has reached that temperature.

## Temperature controllers

Stable frontend:

```python
from pylabrobot.temperature_controlling import TemperatureController
```

Verified methods:

```text
set_temperature(temperature, passive=False)
get_temperature()
deactivate()
```

The current development inventory includes Inheco CPAC and the Opentrons
Temperature Module; these support labels do not establish 0.2.2 compatibility. Validate active cooling, condensation,
plate/adapter contact, setpoint range, ramp, sensor placement, overshoot, and
sample-versus-block temperature. `set_temperature()` does not await thermal
equilibration; use `wait_for_temperature(timeout=..., tolerance=...)` for the
block sensor. In 0.2.2 `passive=True` below the current temperature only skips a
new setpoint command: it does not deactivate prior heating. Do not equate it
with a verified safe cooling action.

## Centrifuges

Stable imports:

```python
from pylabrobot.centrifuge import Access2Backend, Centrifuge, VSpinBackend
```

Verified frontend:

```text
open_door()
close_door()
lock_door()
unlock_door()
spin(g, duration, **backend_kwargs)
```

The stable method takes relative centrifugal force `g`, not the stale
`speed=...` RPM argument. Converting RPM to RCF requires the correct rotor
radius; never guess it.

The current development table labels both Agilent VSpin and its Access2 loader
**Full**; older tables called VSpin **Mostly**. Released constructors are:

`VSpinBackend(device_id=None)` and `Access2Backend(device_id, timeout=60)` are
device-specific. Do not use placeholder IDs in a live script.

The released 0.2.2 wheel includes `MicroSpin(name, host, port=1000, timeout=30.0,
backend=None)` and `pylabrobot.centrifuge.highres.MicroSpinBackend`. The changelog
still lists them under `Unreleased`, so it cannot decide release availability.
The driver speaks ASCII over TCP; `setup()` opens a connection and `stop()`
closes it without stopping a spinning rotor. `status` can block until spin-down.
These contracts were source-inspected only; the [review ledger](review.md)
records framing and limits. No factory or hardware backend was instantiated.

### Centrifuge safety

Require human verification of rotor/bucket/adapter model, plate rating,
orientation, balance, maximum RCF, duration, acceleration/deceleration, lid/door
interlocks, loading position, clearance, maintenance, and emergency procedure.
Never open/unlock while rotating or issue movement merely to test a connection.
On timeout or disconnect, assume the rotor may still be moving until physically
verified safe.

## Storage/incubation

The current development invent

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

