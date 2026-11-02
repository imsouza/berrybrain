---
id: sciref-pycalphad-model-and-validation
name: "Scientific Ref: Composition basis and equilibrium validation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pycalphad): Composition basis and equilibrium validation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pycalphad model validation"
  - "composition basis and equilibrium validation"
keywords:
  - "pycalphad"
  - "model"
  - "validation"
  - "specialized"
  - "scientific"
  - "reference"
  - "composition"
  - "basis"
---

# Composition basis and equilibrium validation

## Original pedagogical database

`assets/ideal-cu-ni.tdb` was written for this skill and is released under the skill's
MIT license. Cu and Ni are labels for a hypothetical ideal binary; there are no fitted
experimental data. The file defines one substitutional sublattice in FCC_A1 and LIQUID,
with no excess mixing terms or pressure dependence. Its functions span 298.15–2000 K.

With x = X(Ni), energies in J/mol, and R in J/(mol K):

- G(FCC_A1) = R T [x ln x + (1-x) ln(1-x)].
- G(LIQUID) = G(FCC_A1) + (1-x)(10000-10T) + x(12000-10T).

At T=1100 K the liquid endmember offsets are -1000 and +1000 J/mol. Equality of both
component chemical potentials gives x_liquid = 1/(1+exp(1000/(RT))) and
x_solid = 1-x_liquid. The phase fraction of solid at bulk x between those endpoints is
(x_bulk-x_liquid)/(x_solid-x_liquid). This is an independent analytic check of the
numerical common tangent, phase compositions, and lever rule. The tests use pycalphad's
R=8.3145 J/(mol K); the listed decimal values are package/model-specific regression values.

The database intentionally lacks realistic heat capacities, lattice stabilities, excess
mixing, magnetic terms, and pressure effects. Its apparent transitions are synthetic.
Do not fit a real experiment to it or replace an assessed database with this example.

## Basis conversions

For measured elemental mass fractions w_i and molar masses M_i, calculate
x_i = (w_i/M_i) / sum_j(w_j/M_j), including the dependent element. Weight percent is
first divided by 100. Store the original composition, molar masses, and converted values
with the run. The helper accepts only the resulting mole fractions and rejects a
`mass_fraction` basis instead of treating weight percent as atomic fraction.

`NP` is a molar phase fraction at total N=1. A mass phase fraction requires each phase's
composition-weighted molar mass: w_phase = NP_phase*M_phase / sum(NP_j*M_j).
Volume fractions require appropriate phase densities or molar volumes as well. Do not
compare molar fractions directly to microscopy area fractions without explaining the
conversion and sampling assumptions.

For this elemental workflow, molar energies and amounts use a mole of non-vacancy
atoms, not a mole of an arbitrary compound formula unit. `Model.GM` is normalized on
that basis; `Model.G` is formula energy and can differ with sublattice site ratios.
Site fractions `v.Y(phase, sublattice_index, species)` are internal degrees of freedom,
not bulk mole fractions. Sublattice indices are zero-based.

The tested conversion API is `v.get_mole_fractions({v.W('NI'): 0.5}, 'CU', db)`;
it uses the TDB elemental masses and returns a condition mapping keyed by `v.X('NI')`.
For the bundled masses, 50 wt% Ni is X(Ni)=0.5198487558, not 0.5. No conversion is
performed by the JSON helper itself.

## Native model, property, and plotting contracts

These examples were executed with pycalphad 0.11.2. Paths below are relative to the
collection root. `Database(path)` parses local thermodynamic data; successful parsing
does not establish that the assessment or every model feature is suitable. Review TDB
warnings rather than suppressing all warnings. `db.elements`, `db.phases`, and each
phase's `constituents`, `sublattices`, and `model_hints` expose the modeled system.

`Model(db, components, phase)` builds a symbolic energy model, not an equilibrium.
`calculate(..., output='GM', T=..., P=..., pdens=...)` samples its phase-constitution
surface. Its `points` columns are ordered internal site fractions: use the model's
`site_fractions` order; do not pass overall alloy compositions as points for a
multisublattice model. In the one-sublattice teaching FCC model only, `[0.5, 0.5]`
coincides with 50:50 bulk composition. `calculate` does not minimize across phases.
Pass sampling options to `equilibrium` or `Workspace` through `calc_opts`, not as
top-level `pdens`; unused equilibrium keyword arguments merely produce a warning.

```python
import numpy as np
from pycalphad import Database, Workspace, variables as v

db = Database('skills/pycalphad/assets/ideal-cu-ni.tdb')
components = ['CU', 'NI', 'VA']
phases = ['FCC_A1', 'LIQUID']
conditions = {v.T: [900, 1100, 1300], v.P: 101325, v.N: 1, v.X('NI'): 0.5}
wks = Workspace(db, components, phases, conditions, calc_opts={'pdens': 500})
temperature = wks.get(v.T)
phase_amounts = wks.get_dict('NP(*)')
gm = wks.get('GM')                  # system molar Gibbs energy, J/mol
x_solid = wks.get(v.X('FCC_A1', 'NI'))
assert np.allclose(temperature, [900, 1100, 1300])
assert np.isfinite(gm).all()
assert np.isnan(x_solid[-1])         # absent solid; NaN is not a failed equilibrium
```

Use `get_dict` when phase multiplicity can change. A request such as `NP(FCC_A1)`
or `X(FCC_A1,NI)` expands to `#1`, `#2`, ... properties for a miscibility gap; `get`
can consequently return a list of arrays rather than one array. Preserve those sets
and only sum their amounts when a total phase-name fraction is intended. Suffixes
identify solver composition sets, not permanent ordered/disordered identities.
Inspect compositions and site fractions before assigning physical labels. Property
arrays squeeze singleton condition axes; use `wks.condition_axis_order` for grids.

`GM` and `HM` are J/mol; `SM` and `CPM` are J/(mol K). A phase-qualified property,
such as `GM(FCC_A1)`, is that stable composition set's property, whereas unqualified
`GM` is phase-amount-weighted. `CPM` differentiates the model at fixed constitution;
`wks.get('HM.T')` differentiates equilibrium enthalpy as temperature changes, including
phase amounts and internal relaxation. They need not agree. At 1100 K the hypothetical
two-phase example has `CPM=0` but `HM.T` approximately 1005.08 J/(mol K), matching a
small central difference of equilibrium enthalpy. Derivatives at phase boundaries or
invariant points require special care; a finite derivative is not a latent-heat integral.

For a small binary phase diagram, the current top-level `binplot` uses the mapping API:

```python
import matplotlib.pyplot as plt
from pycalphad import binplot

ax, strategy = binplot(
    db, components, phases,
    {v.T: (900, 1300, 100), v.P: 101325, v.N: 1, v.X('NI'): (0.3, 0.7, 0.1)},
    return_strategy=True,
)
ax.set_title('Hypothetical ideal binary; not assessed Cu-Ni')
ax.figure.savefig('hypothetical-binary.png', dpi=150, bbox_inches='tight')
plt.close(ax.figure)
```

The default return is an Axes; `return_strategy=True`

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

