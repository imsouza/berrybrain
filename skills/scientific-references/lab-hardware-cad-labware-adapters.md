---
id: sciref-lab-hardware-cad-labware-adapters
name: "Scientific Ref: Labware adapters, holders, and racks"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (lab-hardware-cad): Labware adapters, holders, and racks"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "lab hardware cad labware adapters"
  - "labware adapters, holders, and racks"
keywords:
  - "lab"
  - "hardware"
  - "cad"
  - "labware"
  - "adapters"
  - "specialized"
  - "scientific"
  - "reference"
---

# Labware adapters, holders, and racks

Parts that receive standard consumables: microplates, cuvettes, tubes, slides, dishes.

The governing principle: **where a published standard exists, design to the standard; where it
does not, require a measurement.** Microplate footprints are standardised. Well geometry, skirt
profiles, tube dimensions, and lid fits are not.

Verified dimensions live in `assets/standards.json`. Query them rather than copying numbers:

```bash
python scripts/check.py standards --show slas-microplate-footprint
```

## Microplates (ANSI/SLAS 1-4)

The four dimensions references below are the R2012 PDFs currently linked by SLAS.
They are subsets of the specification; read the relevant section and drawing for datum rules.

| Document | Governs | Key numbers |
| --- | --- | --- |
| ANSI/SLAS 1-2004 | Footprint | 127.76 x 85.48 mm ±0.50 overall, ±0.25 near corners; corner radius 3.18 ±1.6 mm |
| ANSI/SLAS 2-2004 | Height | 14.35 ±0.25 mm at perimeter wells; ±0.76 mm overall |
| ANSI/SLAS 3-2004 | Bottom outside flange | Short 2.41, medium 6.10, tall 7.62 mm, each ±0.38 |
| ANSI/SLAS 4-2004 | Well positions | 96-well: 9.0 mm pitch, A1 at 14.38 mm from left, 11.24 mm from top |

### Designing a plate pocket

Three traps, in the order people fall into them.

**1. Use the tolerance for the full interface.** The ±0.25 mm band applies only
within 12.7 mm of the corners. A continuous pocket needs the ±0.50 mm overall band.
The standard covers the base footprint; obtain the vendor body/draft envelope for a deep pocket.
Size to the maximum envelope, then add clearance and your process allowance. A plate at the top of tolerance is
127.76 + 0.50 = 128.26 mm. A pocket cut at 127.76 + clearance can bind on conforming plates. Compute:

```python
plate_l_mm = 127.76      # ANSI/SLAS 1-2004 nominal
plate_tol_mm = 0.50      # ANSI/SLAS 1-2004
fit_clearance_mm = 0.40  # per side; FDM, see fabrication-limits.md
pocket_l_mm = plate_l_mm + plate_tol_mm + 2 * fit_clearance_mm   # 129.06
```

**2. The corner radius tolerance is enormous — and it bounds the pocket radius from above,
not below.** 3.18 ±1.6 mm means a real plate corner is anywhere from 1.58 to 4.78 mm. Get the
direction right: a plate corner is **convex**, a pocket fillet is **concave material bulging
inward**, so a *sharp* internal pocket corner always clears a rounded plate — the unused corner is
empty space. It is a pocket fillet *larger* than the plate's corner radius that binds: the bulge
occupies space the plate needs. Sizing the fillet to the plate's maximum corner radius is
therefore exactly backwards — it binds every plate except those at the top of the corner
tolerance.

The safe options, best first:

- **Corner relief** (a small slot or bore cut past each corner) — always clears, prints and mills
  cleanly, and is the standard fix.
- **Fillet no larger than the plate's minimum corner radius** (1.58 mm for SLAS plates) — clears
  every conforming plate in every position.
- A larger fillet only if `R ≤ r_min + ~3.4 × per-side clearance` — the geometry only recovers the
  intrusion when the plate stays roughly centred, so treat this as a last resort and say so.

```python
with BuildPart() as pocket:
    # ... pocket geometry ...
    # relief bores just outside each pocket corner: clears any conforming corner radius
    with Locations(*corner_relief_centres()):
        Hole(radius=2.0)
```

**3. Height depends on the flange, not just the plate.** ANSI/SLAS 3 includes three uniform flange
heights, plus interrupted short flanges and dual-height variants. A carrier that grips the flange must be told which one. Ask; do not assume medium.

### Well grid

For a part that must reach individual wells — a magnet block, a lid with access holes, a light
guide — lay out from the plate's outline corner, not from the plate centre:

```python
a1_x_mm, a1_y_mm, pitch_mm = 14.38, 11.24, 9.0   # ANSI/SLAS 4-2004, 96-well
locations = [
    (a1_x_mm + pitch_mm * col, a1_y_mm + pitch_mm * row)
    for row in range(8) for col in range(12)
]
```

The standard's positional tolerance is a **0.70 mm diameter zone** around each nominal centre, not
a ±0.70 mm band. A feature that must clear every well needs at least 0.35 mm of radial margin on
top of your own process tolerance.

Directly verified in ANSI/SLAS 4 sections 4.2 and 4.3: 384-well pitch is 4.5 mm,
A1 offsets (12.13, 8.99) mm, position zone diameter 0.70 mm; 1536-well pitch is
2.25 mm, A1 offsets (11.005, 7.865) mm, position zone diameter 0.50 mm. Datum edges
are the near-corner zones, not a bowed side midpoint. These basic coordinates do
not imply zero manufacturing tolerance.

### What the standards do not fix

Well diameter, well depth, well bottom shape (flat, round, conical), skirt height, lid geometry,
optical bottom thickness, and deep-well plate height. All vary by manufacturer and product line.
If the part touches any of these, get the vendor drawing or measure it.

## Cuvettes

A common 10 mm path-length rectangular cuvette has a **12.5 x 12.5 mm external
footprint and 45 mm body height**, as illustrated by Hellma's catalogue. This is not
a universal standard. No shared ±0.1 mm envelope tolerance or uniform wall thickness
is established here; the database marks those nominal dimensions unverified for fit.

Design notes:

- Holders should be generous or compliant. Because no document fixes the tolerance, a 0.1 mm
  interference fit designed against nominal will fail on some suppliers' cuvettes.
- Semi-micro and micro cuvettes keep the 12.5 mm external footprint but change internal geometry
  and often height. Confirm the exact external envelope, cap and optical-window height; a common
  footprint alone does not establish interchangeability.
- Cuvettes are usually held with a spring or leaf on one face so the two optical faces register
  against fixed datums. Copy that: locate on two adjacent faces, preload from the opposite corner.
  A four-sided pocket with clearance lets the cuvette rotate and shifts the path length.
- **Never print the optical path.** Printed surfaces scatter. The cuvette provides the optical
  faces; the holder provides position only, and must not obstruct the beam window.

## Tubes

Tube dimensions are **not standardised** and differ measurably between suppliers, and often
between product lines from the same supplier. Approximate outside diameters near the tube rim:

| Tube | Approximate OD | Note |
| --- | --- | --- |
| 0.2 mL PCR | 6 mm | Often sup

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

