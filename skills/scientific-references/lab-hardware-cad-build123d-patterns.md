---
id: sciref-lab-hardware-cad-build123d-patterns
name: "Scientific Ref: build123d 0.13.0 patterns"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (lab-hardware-cad): build123d 0.13.0 patterns"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "lab hardware cad build123d patterns"
  - "build123d 0.13.0 patterns"
keywords:
  - "lab"
  - "hardware"
  - "cad"
  - "build123d"
  - "patterns"
  - "specialized"
  - "scientific"
  - "reference"
  - "build"
---

# build123d 0.13.0 patterns

An API cookbook for the geometry this skill needs, reviewed against build123d 0.13.0
on Python 3.12 with OCCT 8.0.1. The complete carrier, cage model, exports, selectors,
counterbore and native gauges are exercised in the repository suite. Snippets with
undefined surrounding variables are illustrative fragments to adapt to the model.

## Builder mode or algebra mode

build123d offers two equivalent APIs.

```python
# Builder mode: a context manager collects operations. mode= controls the boolean.
with BuildPart() as ex:
    Box(80.0, 60.0, 10.0)
    Cylinder(radius=11.0, height=10.0, mode=Mode.SUBTRACT)
part = ex.part

# Algebra mode: plain objects and operators.
part = Box(80.0, 60.0, 10.0) - Cylinder(radius=11.0, height=10.0)
```

**Use builder mode for parts in this skill.** Selectors (`ex.edges()`, `ex.faces()`) read naturally
from the builder, which is what you need for fillets and for placing features on found faces.
Algebra mode is a good fit for short, purely constructive shapes.

Do not mix the two styles inside one `build()`.

## The model file contract

`gen.py` imports the module, calls `build()`, and then reads `interfaces()`. Parameters must be
module-level so they can be overridden with `--param`.

```python
"""One-line description of the part.

Process: SLA, tough resin.  Orientation: bore axis vertical.
Interfaces:
  - Rod bores: 30 mm cage system, Thorlabs ER series (cage-system-30mm).
"""
from build123d import *

# --- INTERFACE (fixed; do not tune) ---
rod_spacing_mm = 30.0     # cage-system-30mm
rod_bore_d_mm = 6.4       # rod_diameter 6.0 + 2 x 0.20 SLA free-sliding (fabrication-limits.md)
# --- DESIGN (free) ---
plate_t_mm = 8.9
aperture_d_mm = 25.4


def interfaces() -> list[dict]:
    return [
        {"feature": "cage rod bore spacing", "standard": "cage-system-30mm",
         "dimension": "rod_spacing", "value": rod_spacing_mm, "intent": "match"},
        {"feature": "cage rod bore diameter", "standard": "cage-system-30mm",
         "dimension": "rod_diameter", "value": rod_bore_d_mm,
         "intent": "envelope", "clearance": 0.4},
    ]


def build() -> Part:
    half = rod_spacing_mm / 2
    with BuildPart() as plate:
        Box(rod_spacing_mm + 12.0, rod_spacing_mm + 12.0, plate_t_mm)
        with Locations((half, half), (-half, half), (half, -half), (-half, -half)):
            Hole(radius=rod_bore_d_mm / 2)
        Hole(radius=aperture_d_mm / 2)
    return plate.part
```

## Declaring interfaces

Most lab-hardware interfaces are **internal features** — a pocket, a bore, a slot — and none of
them appear in the part's outer bounding box. So `check.py fit` cannot find them by measuring the
STEP, and hand-copying the number into `--value` reintroduces exactly the transcription error the
skill exists to prevent. Declaring them closes the loop: `gen.py` records the declaration in the
manifest, and `check.py interfaces` verifies every entry.

Each entry needs `standard`, `dimension`, and `value`; `feature`, `intent`, and `clearance` are
optional:

| Key | Meaning |
| --- | --- |
| `standard` | ID from `check.py standards --list` |
| `dimension` | a dimension name inside that standard |
| `value` | the number **this model computed**, in mm |
| `feature` | human label for the check output (default: the dimension name) |
| `intent` | `match` if this part must itself conform; `envelope` if the feature must accept any conforming part (default: `match`) |
| `clearance` | total intended clearance in mm, both sides (default: 0) |

**Write `interfaces()` as a function, and compute derived dimensions inside functions.** A
module-level `INTERFACES = [...]` list is also accepted, but it is evaluated at import — before
`--param` is applied — so any value derived from an overridden parameter is recorded wrong. The same
applies to the geometry: derive inside `build()` or a helper, never at module level.

```python
# Wrong: --param plate_tol_mm=0 silently leaves pocket_l_mm at the old value
pocket_l_mm = plate_l_mm + plate_tol_mm + 2 * pocket_clearance_mm

# Right: recomputed on every call, so overrides land
def pocket_l_mm() -> float:
    return plate_l_mm + plate_tol_mm + 2 * pocket_clearance_mm
```

`gen.py` warns when it sees a static `INTERFACES` list together with `--param`.

## Declaring geometry checks

`interfaces()` compares declared numbers against the standards database; it never touches the
solid. `checks()` is its measured counterpart: a list of **go/no-go gauges** evaluated by boolean
intersection against the part `build()` actually produced. `gen.py` runs them on every
generation and fails the build if one fails; `check.py geometry` re-runs them against an
exported STEP.

The principle: **every geometric requirement in the request maps to one entry.** Something must
pass through (a screw, a beam, a probe) → a `clear` region. Something must fit into a void (a
plate into a pocket) → a `clear` box the size of the mating part at maximum material condition.
Something must remain (a ridge, a ledge, a screw seat) → a `material` region. A stated size
limit → a `bbox_*` bound. These are exactly the errors `is_valid`, the bounding box, and a
declared-number check cannot see.

```python
def checks() -> list[dict]:
    top = plate_t_mm / 2
    return [
        # a clear region: no material may intrude (screw shafts, through the part)
        {"feature": "M6 screws pass all four bores",
         "clear": {"cylinder": 6.0, "axis": "z", "at": bolt_xy()}},
        # a keep-out with an explicit span (a beam corridor along x at height z)
        {"feature": "beam clear at 15 mm above the bench",
         "clear": {"cylinder": 5.0, "axis": "x", "at": [(0.0, 15.0)]}},
        # a gauge part that must drop into a pocket: the mating part at MMC
        {"feature": "SLAS plate at MMC drops into the pocket",
         "clear": {"box": (128.26, 85.98, pocket_depth_mm()),
                   "at": [(0.0, 0.0, floor_t_mm + pocket_depth_mm() / 2)]}},
        # a counterbore that really is a counterbore: recess open, seat present.
        # The second entry is what catches a recess that punched through.
        {"feature": "counterbore recess open at the top",
         "clear": {"cylinder": cbore_d_mm - 0.2, "axis": "z", "at": bolt_xy(),
                   "span": (top - cbore_depth_mm + 0.1, top + 0.1)}},
        {"feature": "screw seat present below the recess",
         "material": {"cylinder": cbore_d_mm - 0.2, "axis": "z", "at": bolt_xy(),
       

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

