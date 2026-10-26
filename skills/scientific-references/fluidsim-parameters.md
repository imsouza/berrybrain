---
id: sciref-fluidsim-parameters
name: "Scientific Ref: Parameter surface and validation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (fluidsim): Parameter surface and validation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "fluidsim parameters"
  - "parameter surface and validation"
keywords:
  - "fluidsim"
  - "parameters"
  - "specialized"
  - "scientific"
  - "reference"
  - "parameter"
  - "surface"
---

# Parameter surface and validation

## Source of truth

Create parameters from the exact selected class:

```python
from fluidsim.solvers.ns2d.solver import Simul

params = Simul.create_default_params()
print(params)
```

FluidSim composes parameters from registered operator, state, time-stepping,
initialization, forcing, and output classes. The tree is solver- and
extension-specific. There is no universal flat FluidSim parameter schema.

`ParamContainer` rejects assignment to undeclared attributes, which catches many
typos. It does not check units, physical interpretation, numerical convergence,
or whether a valid option is appropriate.

The following snapshot was introspected from a pinned
`fluidsim[fft]==0.9.0`/`fluidfft==0.4.5` NS2D environment on 2026-09-30 and reviewed on 2026-10-01.

## Top-level controls

Common pseudospectral fields:

```python
params.NEW_DIR_RESULTS = True
params.ONLY_COARSE_OPER = False
params.short_name_type_run = ""

params.nu_2 = 1e-3
params.nu_4 = 0.0
params.nu_8 = 0.0
params.nu_m4 = 0.0
```

- `NEW_DIR_RESULTS` primarily controls loading/restart output behavior. Official
  docs say a loaded simulation creates a new directory when true and appends to
  the old directory when false. Choose explicitly and preserve the parent.
- `ONLY_COARSE_OPER` is for fast loading/plotting and cannot process full fields.
- `nu_2`, `nu_4`, `nu_8`, and `nu_m4` are solver dissipation coefficients. Their
  dimensions depend on derivative order and nondimensionalization.

Do not use higher-order dissipation merely to hide insufficient resolution.
State its definition and verify budgets/tails/refinement.

Solver-specific top-level examples include:

- `N` for constant stratification in `.strat` solvers.
- `f` for rotation where implemented.
- `beta`, `c2`, projections, and other fields in specific solvers.

Inspect the selected solver documentation rather than copying these blindly.

## Operators

NS2D defaults:

```python
params.oper.nx = 48
params.oper.ny = 48
params.oper.Lx = 8
params.oper.Ly = 8
params.oper.coef_dealiasing = 2 / 3
params.oper.truncation_shape = "cubic"
params.oper.type_fft = "default"
params.oper.NO_KY0 = False
params.oper.NO_SHEAR_MODES = False
```

NS3D adds `nz`/`Lz` and solver-specific options. Never infer physical spacing
without the domain convention. Record:

- `nx`, `ny`, `nz` and `Lx`, `Ly`, `Lz`.
- Grid spacing and maximum represented/dealiased wave numbers.
- `coef_dealiasing`, truncation shape, and phase-shift scheme if used.
- Actual selected FluidFFT method and decomposition.
- Removed modes/symmetries.

Powers of two are not a universal requirement or guarantee of fastest FFT.
Benchmark representative allowed shapes on the target backend.

`type_fft="default"` delegates selection. For provenance-critical runs, inspect
and record the actual method; set an explicit tested method if the environment
supports it.

## Time stepping

NS2D 0.9.0 defaults:

```python
params.time_stepping.USE_CFL = True
params.time_stepping.USE_T_END = True
params.time_stepping.cfl_coef = None
params.time_stepping.deltat0 = 0.2
params.time_stepping.deltat_max = 0.2
params.time_stepping.it_end = 10
params.time_stepping.max_elapsed = None
params.time_stepping.t_end = 10.0
params.time_stepping.type_time_scheme = "RK4"
```

The current field is `cfl_coef`, **not** `CFL`.

For reproducible bounded plans, set explicitly:

```python
params.time_stepping.USE_CFL = True
params.time_stepping.cfl_coef = 0.5
params.time_stepping.deltat0 = 1e-3
params.time_stepping.deltat_max = 1e-2
params.time_stepping.USE_T_END = True
params.time_stepping.t_end = 0.1
params.time_stepping.max_elapsed = "00:05:00"
```

`cfl_coef=0.5` here is an explicit pilot choice, not a universal recommendation.
The acceptable value depends on equations, scheme, waves, dissipation, and
resolution. Check recorded `deltat` and refine.

Current pseudospectral scheme names documented in 0.9:

- `Euler`
- `Euler_phaseshift`
- `Euler_phaseshift_random`
- `RK2`
- `RK2_trapezoid`
- `RK2_phaseshift`
- `RK2_phaseshift_random`
- `RK2_phaseshift_random_split`
- `RK2_phaseshift_exact`
- `RK4`

Random phase-shift schemes also expose:

```python
params.time_stepping.phaseshift_random.nb_pairs = 1
params.time_stepping.phaseshift_random.nb_steps_compute_new_pair = None
```

Do not infer exact dealiasing or convergence from a scheme name. Verify its
implementation and test a smaller time step.

## Initial fields

NS2D advertises:

```python
params.init_fields.type = "constant"
params.init_fields.modif_after_init = False
```

Available types in the pinned NS2D profile:

- `constant`
- `noise`
- `jet`
- `dipole`
- `from_file`
- `from_simul`
- `in_script`

Nested fields include:

```python
params.init_fields.constant.value = 0.0
params.init_fields.noise.velo_max = 1.0
params.init_fields.noise.length = 0.0
params.init_fields.from_file.path = "state_phys_t001.000.nc"
```

Other solvers advertise different types/variables. For random initial fields,
record seed, process count, backend, generated spectrum/amplitude, and resulting
constraints. A seed alone may not guarantee bitwise identity across MPI
decompositions or versions.

For in-script initialization:

1. Inspect `sim.state.keys_state_phys`/solver state documentation.
2. Fill the solver's canonical variables.
3. Use the solver's documented physical-to-spectral conversion method.
4. Enforce divergence/constraints and dealias if required.
5. Save and inspect the initialized state before advancement.

Do not reuse old examples with guessed keys such as `vx` versus `ux`, or call a
spectral-to-physical method after modifying physical fields.

## Forcing

Base fields:

```python
params.forcing.enable = False
params.forcing.type = ""
params.forcing.forcing_rate = 1.0
params.forcing.key_forced = None
params.forcing.nkmin_forcing = 4
params.forcing.nkmax_forcing = 5
```

NS2D advertises `in_script`, `in_script_coarse`, `pseudo_spectral`,
`proportional`, `tcrandom`, and `tcrandom_anisotropic`.

Nested current fields:

```python
params.forcing.normalized.constant_rate_of = None
params.forcing.normalized.type = "2nd_degree_eq"
params.forcing.normalized.which_root = "minabs"
params.forcing.random.only_positive = False
params.forcing.tcrandom.time_correlation = "based_on_forcing_rate"
```

The old flat field `tcrandom_time_correlation` is not current.

For a time-correlated random plan:

```python
params.forcing.enable = True
params.forcing.type = "tcrandom"
params.forcing.forcing_rat

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

