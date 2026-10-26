---
id: sci-pylabrobot
name: "Scientific: pylabrobot"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Develops and reviews PyLabRobot lab-automation resources, liquid-handling plans, offline simulations, and supported-device integrations. Supports PyLabRobot protocols and API questions; keep physical execution behind an explicit operator safety gate."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "pylabrobot"
keywords:
  - "pylabrobot"
  - "develops"
  - "reviews"
  - "automation"
  - "resources"
  - "liquid"
---

# PyLabRobot

Use PyLabRobot's hardware-agnostic frontends, resource tree, trackers, and
device-specific backends to develop laboratory automation. Default to local
manifest validation, bookkeeping, and the software-only chatterbox backend.

## Verified snapshot

- PyPI stable: **`PyLabRobot==0.2.2`**, released **2026-07-30**.
- Upstream requirement: **Python >=3.9**; runtime checks here used **Python 3.13**.
- Hosted `/stable/` pages mix 0.2.1 API pages with development documentation.
  GitHub has no `v0.2.2` tag and its changelog has no 0.2.2 section. Use the
  released wheel/source distribution for the tested contract, not the URL label.
- Released liquid-handler backends include `STARBackend`, `VantageBackend`,
  `EVOBackend`, `OpentronsOT2Backend`, and the software-only
  `LiquidHandlerChatterboxBackend`.
- MicroSpin and `Plate.stacking_z_height` **are present in 0.2.2**, despite
  being listed under `Unreleased` in the current changelog. Newer development
  APIs, including the `track=` Hamilton deck keyword, are not this release.
- See the [release and transport review](references/review.md) for source
  hashes, tested behavior, and the known OT-2 cancellation mismatch.

## Non-negotiable hardware boundary

Never connect to, initialize, home, move, heat, shake, spin, pump, open/close,
or otherwise command physical equipment automatically. Do not turn a simulation
plan into a live backend merely by changing an environment variable, config
value, or import.

Before any separately authorized live run, require a trained human to:

1. Explicitly confirm the exact backend, device identity, firmware, transport,
   deck, and protocol revision.
2. Reconcile the physical deck against the resource tree, including carriers,
   adapters, lids, plates, tip racks, waste, labware orientation, barcodes, and
   every occupied coordinate.
3. Verify calibration, teaching, motion envelopes, collision risks, gripper or
   channel clearances, and all aspiration/dispense coordinates.
4. Review source identity and actual fill volume, dead volume, destination
   capacity, tip type/capacity/filter compatibility, channel mapping, units,
   heights, rates, liquid class, blowout/mixing, and contamination boundaries.
5. Confirm guards, doors, waste capacity, containment, emergency stop readiness,
   PPE, biosafety/chemical controls, and a safe abort/recovery procedure.
6. Approve a slow dry run or nonhazardous commissioning run when anything is
   new or changed.

Tracker state is **bookkeeping**, not sensing. It cannot prove that liquid or a
tip is physically present. After a backend error, tracker rollback describes
software state; it does not reverse a physical aspiration, dispense, or tip
movement that partly completed. Preserve the error/channel details and have the
operator reconcile tips and source/destination volumes before resuming. Do not
blindly retry the failed operation from the pre-error plan. The
[0.2.2 liquid-handler implementation](https://pypi.org/project/PyLabRobot/0.2.2/#files)
commits or rolls back trackers according to reported operation success. The Visualizer renders resource/tracker events; it
does not model physics. Chatterbox prints planned operations; it does not prove
calibration, reachability, collision freedom, liquid behavior, or device state.

## Required intake

Do not guess any of these:

- Exact device model, installed options, firmware, computer/OS, and transport.
- Stable PyLabRobot version and required extras.
- Deck/deck origin, carriers, adapters, resource definitions, dimensions,
  coordinates, orientations, and motion clearances.
- Plate/tube/reservoir capacities and dead volumes; initial physical volumes.
- Tip model, filter, fitting, capacity, rack state, channel count, and channel
  mapping.
- Transfer units (`uL`, `mm`, `uL/s`, `s`), heights, rates, mixing, air gaps,
  blowout, liquid properties, and validated vendor liquid class.
- Contamination policy, controls, waste handling, operator interventions,
  acceptance criteria, and recovery procedure.

If information is missing, produce an assumptions/blockers list and an offline
draft only.

## Reproducible install

For offline API inspection and chatterbox simulation:

```bash
uv venv --python 3.13 .venv-pylabrobot
uv pip install --python .venv-pylabrobot/bin/python "PyLabRobot==0.2.2"
```

On Windows, use `.venv-pylabrobot\Scripts\python.exe`. Do not install hardware
extras until the user names the device and explicitly approves its transport
dependencies. Then inspect the matching release source and device page before considering a
pin such as `"PyLabRobot[serial]==0.2.2"` or `"PyLabRobot[usb]==0.2.2"`.

## Offline-first workflow

Run from the repository root. Every bundled CLI uses strict, bounded UTF-8
JSON/CSV, local non-symlink paths, fixed allowlists, and JSON output. None can
select a live backend.

```bash
python3 skills/pylabrobot/scripts/validate_manifest.py \
  --input tests/pylabrobot/fixtures/protocol_manifest.json

python3 skills/pylabrobot/scripts/check_deck_geometry.py \
  --input tests/pylabrobot/fixtures/protocol_manifest.json

python3 skills/pylabrobot/scripts/plan_transfers.py \
  --manifest tests/pylabrobot/fixtures/protocol_manifest.json \
  --transfers tests/pylabrobot/fixtures/transfers.csv

python3 skills/pylabrobot/scripts/generate_simulation_plan.py \
  --manifest tests/pylabrobot/fixtures/protocol_manifest.json \
  --transfers tests/pylabrobot/fixtures/transfers.csv

python3 skills/pylabrobot/scripts/inspect_backends.py \
  --expected-version 0.2.2 --strict
```

The geometry checker uses conservative static axis-aligned boxes; it is not a
motion planner. The transfer planner requires one new tip per row and checks
explicit source and destination starting volumes, dead volume, tip capacity, wells, channels, heights, rates,
units, and allowlists. Review
`assets/protocol-manifest.schema.json` and the synthetic fixtures before making
a project-specific manifest.

## Verified software-only example

The exact backend below is software-only. Do not substitute a hardware backend.
This example uses notebook top-level `await`; in a script, wrap it in
`async def main()` and call `asyncio.run(main())`. The round trip returns an
empty simulated tip to its original spot; production tip disposal follows the
reviewed contamination policy, and the planner uses a new tip for every row.

```python
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

