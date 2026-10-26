---
id: sciref-uncertainty-and-units-plausibility-scales
name: "Scientific Ref: Plausibility: dimensionless groups, characteristic scales, and magnitude bands"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (uncertainty-and-units): Plausibility: dimensionless groups, characteristic scales, and magnitude bands"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "uncertainty units plausibility scales"
  - "plausibility: dimensionless groups, characteristic scales, and magnitude bands"
keywords:
  - "uncertainty"
  - "units"
  - "plausibility"
  - "scales"
  - "specialized"
  - "scientific"
  - "reference"
---

# Plausibility: dimensionless groups, characteristic scales, and magnitude bands

Dimensional analysis proves a calculation is *consistent*. It cannot prove the answer is
*possible*. A cell 2 m across, a Reynolds number of 4×10⁷ in a capillary, and a diffusion
time of 300 years across a lipid bilayer are all dimensionally impeccable, and a
unit-checking library will pass every one of them.

The three checks below provide screens for that gap, conditional on the model. `scripts/check_plausibility.py` runs all of them
and verifies dimensional consistency of each formula before reporting a number.

---

## 1. Choose the characteristic length first

The single most common error in this whole area is not an arithmetic slip — it is using
the wrong length. The dimensionless groups are only meaningful with the length the
correlation was fitted against.

| Geometry | Characteristic length |
| --- | --- |
| Flow in a circular pipe | inside **diameter**, not radius |
| Flow in a non-circular duct | hydraulic diameter `4A/P` |
| External flow over a plate | distance from the leading edge |
| Flow past a sphere or cylinder | diameter |
| Conduction in an irregular body (Biot) | volume / surface area |
| Packed bed | particle diameter |
| Open channel | state convention: `A/P` or hydraulic diameter `4A/P`, with matching thresholds |

Using radius where the correlation wants diameter puts every threshold out by a factor of
two, which is exactly the size of error that survives review.

## 2. Dimensionless groups and what they gate

These are ratios of physical scales. Listed thresholds are context-dependent heuristics,
not universal points at which an assumption automatically becomes false.

| Group | Definition | Threshold | What stops being true past it |
| --- | --- | --- | --- |
| Reynolds `Re` | `ρvL/μ` | 2300 / 4000 (pipe) | laminar solutions; above 4000 you need a turbulence model |
| Péclet `Pe` | `vL/D` | ≈ 1 | relative importance of advection and diffusion at the chosen scale |
| Damköhler `Da_I` | `kL/v` | 0.1 / 10 | small Da means slow reaction during transit; large Da permits high ideal conversion |
| Knudsen `Kn` | `λ/L` | 0.01 | the no-slip boundary condition, then the continuum assumption itself |
| Mach `Ma` | `v/c` | 0.3 | incompressibility, at about 5% density change |
| Womersley `Wo` | `R√(ωρ/μ)` | 1 / 10 | quasi-steady parabolic approximation; large Wo gives a flatter oscillatory core |
| Capillary `Ca` | `μv/σ` | ≈ 10⁻³ | viscous/capillary balance; 1e-3 is illustrative, not a universal onset |
| Weber `We` | `ρv²L/σ` | ≈ 12 | possible bag breakup for low-Oh droplets; use ambient density and relative speed |
| Bond `Bo` | `Δρ g L²/σ` | 1 | surface tension holding a drop against gravity |
| Stokes `Stk` | `ρ_p d² v / (18 μ L)` | 0.1 | inertial following; also check buoyancy, size and Stokes-drag validity |
| Biot `Bi` | `hL/k` | 0.1 | lumped-capacitance (uniform internal temperature) |
| Fourier `Fo` | `αt/L²` | 0.05 / 1 | internal diffusion time; equilibrium also depends on Bi and boundary conditions |
| Schmidt `Sc` | `μ/(ρD)` | — | ≈ 1 for gases, ≈ 10³ for small molecules in water |
| Deborah `De` | `t_relax/t_obs` | 1 | whether the material is a liquid or a solid *on your timescale* |

**Womersley takes angular frequency.** Pass `2πf`, not `f`. A resting human heart at
1.2 Hz gives `ω ≈ 7.5 rad/s`, and in the aorta `Wo ≈ 20` — firmly plug-like, which is why
Poiseuille's law is the wrong model for arterial flow while microvascular rheology, discrete cells and vessel compliance can still invalidate
a Newtonian rigid-tube capillary model even at low Wo.

**The Reynolds thresholds are pipe-flow values.** Transition over a flat plate is around
`Re ≈ 5×10⁵`; sphere wakes and boundary layers have different geometry-specific transitions. The tool
reports the pipe classification and says so.

## 3. Characteristic scales

| Scale | Formula | Sanity anchor |
| --- | --- | --- |
| Diffusion time | `L²/D` | 10 µm at 10⁻⁹ m²/s → 0.1 s |
| Thermal diffusion time | `L²/α` | same form, thermal diffusivity |
| Thermal energy | `k_B T` | 4.14×10⁻²¹ J at 300 K |
| Molar thermal energy | `RT` | 2.49 kJ/mol at 300 K |
| Stokes settling velocity | `Δρ g d²/(18μ)` | 1 µm bead, Δρ = 1000 kg/m³, μ = 1 mPa·s → 0.545 µm/s |
| Mean free path (gas) | `k_BT/(√2 π d² p)` | air at 1 atm → ≈ 68 nm |
| Debye length | `√(ε₀ε_r k_B T / (2 N_A e² I))` | 100 mM ionic strength in water at 25 °C → 0.96 nm |
| Capillary length | `√(σ/(Δρg))` | water → 2.7 mm |

**L² gives a characteristic diffusion scaling, not a complete transport model.** Ten micrometres takes
0.1 s; one millimetre takes 1000 s; one centimetre takes 10⁵ s ≈ 28 hours. These values assume D = 10⁻⁹ m²/s. Geometry, dimensionality, binding, membrane
partitioning and reaction change actual first-passage/equilibration times. The scale
alone cannot infer a biological size limit or tissue viability.

**Stokes settling is valid only while the particle Reynolds number stays below ≈ 0.1.**
Compute the settling velocity, then feed it back into the `reynolds` group with the
particle diameter as the length. If `Re_p > 0.1`, creeping-flow drag needs review, including finite-Re corrections, walls and shape.

## 4. Magnitude bands

These are **illustrative screening bands**, not validated reference intervals or
precise ranges extracted from each cited textbook. Their endpoints are curated choices.
Verify the relevant organism, phase, temperature, pressure, composition and definition
before interpreting a flag. Historical textbook sources below are retained as background
and were not all independently reread in this refresh. A value outside one is worth a second
look, not automatically wrong — the tool reports `questionable` inside one decade and
`implausible` beyond it.

| Band | Range | Source |
| --- | --- | --- |
| Bacterial cell diameter | 0.2–10 µm | Milo & Phillips, *Cell Biology by the Numbers*, ch. 1 |
| Eukaryotic cell diameter | 5–100 µm | Milo & Phillips, ch. 1 |
| Cell membrane thickness | 3–5 nm | Alberts et al., *MBoC* 7th ed., ch. 10 |
| DNA base-pair rise | 0.32–0.36 nm | Bloomfield et al., *Nucleic Acids* |
| Ribosome diameter | 20–30 nm | Milo & Phillips, ch. 1 |
| Protein molar mass | 5–1000 kg/mol (numerically comparable to kDa molecular mass) | Milo & Phillips, ch. 1 |
| Human capillary diameter | 5–10 µm | Guyton & Hall, 14th ed., ch. 16 |
| Mammalian body temperature | 306–315 K | Guyton & Hall, ch. 74 |
| Resting heart rate | 0.7–3 Hz 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

