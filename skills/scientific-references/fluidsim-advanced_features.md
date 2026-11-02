---
id: sciref-fluidsim-advanced-features
name: "Scientific Ref: Forcing, operators, MPI, extensions, and migrations"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (fluidsim): Forcing, operators, MPI, extensions, and migrations"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "fluidsim advanced features"
  - "forcing, operators, mpi, extensions, and migrations"
keywords:
  - "fluidsim"
  - "advanced"
  - "features"
  - "specialized"
  - "scientific"
  - "reference"
  - "forcing"
  - "operators"
---

# Forcing, operators, MPI, extensions, and migrations

## Forcing architecture

FluidSim assembles forcing classes through the selected solver's registry.
NS2D 0.9 advertises:

- `in_script`
- `in_script_coarse`
- `pseudo_spectral`
- `proportional`
- `tcrandom`
- `tcrandom_anisotropic`

Availability and default forced variable are solver-specific.

Base fields:

```python
params.forcing.enable = True
params.forcing.type = "tcrandom"
params.forcing.forcing_rate = 1.0
params.forcing.key_forced = None
params.forcing.nkmin_forcing = 4
params.forcing.nkmax_forcing = 5
params.forcing.tcrandom.time_correlation = "based_on_forcing_rate"
```

Current source converts `nkmin_forcing`/`nkmax_forcing` to dimensional
wave-number bounds using the operator's wave-number spacing. Inspect the
resulting forced region; the integers are not necessarily physical wave
numbers.

### Normalization

Current normalized-forcing fields include:

```python
params.forcing.normalized.constant_rate_of = None
params.forcing.normalized.type = "2nd_degree_eq"
params.forcing.normalized.which_root = "minabs"
```

The implementation can solve a quadratic normalization so the time-step-mean
injection of a quadratic quantity matches `forcing_rate`. The exact quadratic
quantity and key depend on the solver/forced field. Therefore:

- State the intended injected invariant and units.
- Confirm `key_forced`.
- Measure forcing power in output.
- Check the global/spectral budget using the same convention.
- Test time-step sensitivity of the measured injection.

Do not call `forcing_rate` “energy input” without verifying the selected class.

### Time-correlated random forcing

The 0.9 field is:

```python
params.forcing.tcrandom.time_correlation = "based_on_forcing_rate"
```

or a positive finite time value. The rate-derived setting requires positive
`forcing_rate`. Current source derives the default period as a power of
the forcing rate and stores two random seeds plus the last-change time in state
parameters under `/state_params/forcing` (`seed0`, `seed1`, `t_last_change`).
FluidSim 0.9.0 writes these state parameters into restart files;
0.8.6 fixed a time-correlated forcing restart bug.

For reproducibility, preserve:

- Initial random seed strategy.
- Saved forcing state parameters.
- MPI rank count/decomposition and package versions.
- Correlation-time setting and measured autocorrelation.
- Restart boundary diagnostics.

### In-script forcing

Use the solver's registered `InScriptForcing*` interface and documented
`compute_forcing_fft_each_time` or coarse equivalent. Do not monkey-patch a
method with a lambda copied from an old example:

- State keys have changed in some solvers.
- Local spectral layout depends on FFT/MPI backend.
- Hermitian/reality constraints and normalization must be preserved.
- A literal global Fourier index is not portable across decompositions.

Implement a reviewed subclass/extension with unit tests on tiny sequential and
MPI layouts. Validate zero-net/target injection, symmetry, and budget effects.

## Operators and array ownership

`sim.oper` provides solver-selected grids, FFT/IFFT, differentiation, vector
calculus, projections, spectra, dealiasing, and distributed-array helpers.
Method names and array layouts depend on operator class.

Never assume:

- Axis order from `nx`, `ny`, `nz`.
- Full global arrays on every rank.
- A Fourier mode has the same local index under another backend/rank count.
- All FFT backends use the same spectral shape.
- A gathered array fits rank-0 memory.
- Direct NumPy sums have the same normalization as
  `oper.sum_wavenumbers`.

Use documented operator methods and inspect:

```python
print(type(sim.oper))
print(sim.oper.axes)
print(sim.params.oper)
```

For custom diagnostics, test sequential and distributed shapes and compare
against analytical transforms at tiny resolution.

## Dealiasing

The common Cartesian field is:

```python
params.oper.coef_dealiasing = 2 / 3
params.oper.truncation_shape = "cubic"
```

FluidSim also implements phase-shift time schemes. A coefficient or scheme name
does not prove alias removal for a custom nonlinearity. Verify:

- Polynomial/nonlinear form and expected alias interactions.
- Where dealiasing is applied.
- Truncation geometry.
- Spectral tails and invariant transfer.
- Results under stricter truncation or exact phase-shift method.

Do not combine an aggressive cutoff and high-order dissipation merely to obtain
a visually smooth spectrum.

## Time schemes

Documented pseudospectral names:

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

The implementation treats linear terms with exact coefficients in its
pseudospectral stepper and evaluates nonlinear tendencies according to the
named scheme. Verify source and solver coupling before making an order/stability
claim.

Always check:

- Advective CFL.
- Wave frequency limits (stratification, rotation, shallow-water waves).
- Diffusive/hyperdiffusive limits.
- Forcing correlation and output cadence relative to `deltat`.
- Smaller `cfl_coef`/`deltat_max` comparison.

`USE_CFL=True` only activates the solver's CFL logic; it does not guarantee all
accuracy/stability constraints are resolved.

## Custom initial conditions

`in_script` gives direct control, but use current state keys:

1. Construct `Simul` with `init_fields.type = "in_script"`.
2. Inspect the solver's state documentation/keys.
3. Fill canonical physical or spectral variables.
4. Call the documented conversion in the correct direction.
5. Apply projection/dealiasing/constraints as required.
6. Save an initialization checkpoint and verify budgets before stepping.

Old examples that fill `vx`/`vy` and then call a
spectral-to-physical conversion can overwrite the intended state. NS2D 0.9
documentation shows physical keys including `ux`, `uy`, and `rot`; use the
selected solver's actual keys.

## Extending a solver

FluidSim's `InfoSolver`/class registry supports extensions. For a research
extension:

- Pin FluidSim/FluidSim Core source and version.
- Subclass the closest solver and extend default parameters through the current
  class mechanism.
- Register state variables, operators, initialization, forcing, outputs, and
  restart state explicitly.
- Define nonlinear tendencies with documented sign and normalization.
- Add unit/manufactured-solution tests and budget identiti

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

