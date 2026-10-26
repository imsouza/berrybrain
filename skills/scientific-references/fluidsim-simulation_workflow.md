---
id: sciref-fluidsim-simulation-workflow
name: "Scientific Ref: Bounded simulation, pilot, and restart workflow"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (fluidsim): Bounded simulation, pilot, and restart workflow"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "fluidsim simulation workflow"
  - "bounded simulation, pilot, and restart workflow"
keywords:
  - "fluidsim"
  - "simulation"
  - "workflow"
  - "specialized"
  - "scientific"
  - "reference"
  - "bounded"
---

# Bounded simulation, pilot, and restart workflow

## 1. Define the scientific contract

Before code, record:

- Equations, dependent variables, approximations, and solver key.
- Units for every dimensional quantity, or reference scales and a complete
  nondimensionalization map.
- Domain lengths, geometry, periodic boundary conditions, and symmetries.
- Initial-condition construction, constraints, amplitude/spectrum, and seed.
- Forcing field, band, normalization, correlation, and expected/measured input.
- Dissipation and any hypo-/hyper-viscosity.
- Observables and acceptance thresholds.
- Conservation/budget identities and expected numerical residual behavior.
- Grid, dealiasing, timestep/CFL, and refinement plan.
- Independent benchmark or verification target.

Do not proceed from a prompt that only says “simulate turbulence” or supplies a
Reynolds number without its definition and scaling.

## 2. Declare operational bounds

Every plan must explicitly bound:

- CPU cores.
- MPI ranks and threads/rank.
- Total and per-rank RAM envelope.
- Disk bytes and file/inode count.
- Wall time and FluidSim `max_elapsed`.
- Grid dimensions and total points.
- State snapshot and diagnostic save periods.
- Safe output root and subdirectory.

The bundled JSON schema requires these fields. Start from:

```bash
python3 scripts/solver_config_validator.py --example
```

Save the reviewed JSON locally, then:

```bash
python3 scripts/solver_config_validator.py --config config.json
python3 scripts/grid_resource_estimator.py --config config.json
python3 scripts/simulation_dry_run.py --config config.json --output run.py
```

The resource estimator reports an approximate allocation/storage model, not
measured peaks or enforced quotas. Save records are counted independently of
the declared file limit; exceeding a limit is a failure, never a truncated
estimate. Enabled diagnostics outside physical fields, spectra, spectral budget,
and spatial means require a separate estimate. Iteration-only termination does
not provide the time horizon this storage model needs.

The generator does not import FluidSim or run anything. The generated script
prints a JSON dry run by default. Execution requires both `--execute` and the
exact reviewed config ID. An MPI plan is only a command preview; the tool never
invokes a launcher or scheduler.

## 3. Verify the locked environment

In an isolated exact environment:

```python
from importlib.metadata import version
from fluidfft import get_methods

assert version("fluidsim") == "0.9.0"
assert version("fluidfft") == "0.4.5"
print(sorted(get_methods()))
```

Record registered FFT methods, then load and exercise the chosen method.
`get_methods()` lists entry points even when an optional dependency is absent
(for example Dask). Importing a package is not enough: construct the selected
solver's defaults and run its tiny transform/solver smoke.

## 4. Tiny no-output serial smoke

After approval, use a trivial, bounded state:

```python
from fluidsim.solvers.ns2d.solver import Simul

params = Simul.create_default_params()
params.oper.nx = params.oper.ny = 8
params.oper.Lx = params.oper.Ly = 2.0
params.oper.coef_dealiasing = 2 / 3
params.time_stepping.USE_CFL = False
params.time_stepping.deltat0 = 0.001
params.time_stepping.deltat_max = 0.001
params.time_stepping.t_end = 0.001
params.time_stepping.max_elapsed = "00:01:00"
params.init_fields.type = "constant"
params.init_fields.constant.value = 0.0
params.output.HAS_TO_SAVE = False
params.output.ONLINE_PLOT_OK = False

sim = Simul(params)
sim.time_stepping.start()
```

This checks import, FFT construction, initialization, and one bounded step. It
does not test the intended physics, forcing, conservation, convergence,
performance, output, or restart.

## 5. Tiny output/restart smoke

Use a dedicated empty output root under a quota. Keep:

- `params.output.sub_directory` a safe one-component study identifier.
- `ONLINE_PLOT_OK = False` for unattended runs.
- Short `t_end`, short `max_elapsed`, and low resolution.
- One or two physical-state saves and a bounded scalar diagnostic.
- Spectra/budget outputs disabled unless they are the feature being tested.

Inspect before analysis:

```bash
python3 scripts/output_inventory.py --path fluidsim-runs
python3 scripts/budget_summary.py --path fluidsim-runs
```

Confirm exact filenames and growth. FluidSim 0.9 defaults to
`state_phys_t*.nc` for physical states; spectra remain HDF5.

## 6. Representative scientific pilot

Increase only enough to exercise the intended:

- Initial-condition path.
- Forcing type and injection normalization.
- Solver-specific state and outputs.
- FFT backend.
- Checkpoint and restart.
- Analysis code.

During and after the pilot, check:

- CFL and `deltat` history against all relevant wave/advection/diffusion limits.
- Divergence or other constraints.
- Energy/enstrophy/scalar/potential-energy budgets as appropriate.
- Measured forcing input and dissipation.
- Spectral tails and dealiasing contamination.
- Runtime, peak RSS, per-rank imbalance, file count, and disk growth.
- NaN/Inf, stalled advancement, unexpected truncation, and incomplete files.

A passing pilot permits planning a refinement study; it does not validate a
production run.

## 7. Running a reviewed serial plan

The generated script is deliberately gated:

```bash
python3 run.py
python3 run.py --execute --acknowledge-config-id REVIEWED_CONFIG_ID
```

At execution, it verifies the installed FluidSim/FluidFFT versions, assigns
reviewed thread limits before NumPy import, and checks the actual MPI size.
Restart paths are anchored to the script directory and rehashed before loading;
use a matching `provenance.restart.path` and `init_fields.from_file.path`.
These are preflight checks, not RAM/disk/CPU quota enforcement.

The first command is dry-run only. The second is a real simulation and must be
issued by the user or approved operator after reviewing limits and output
destination.

Never silently increase resolution, duration, save frequency, rank count, or
wall time after approval.

## 8. Read-only loading

Use the lightweight loader:

```python
from fluidsim import load_sim_for_plot

sim = load_sim_for_plot(
    "run-directory",
    merge_missing_params=False,
    hide_stdout=True,
)
```

Use native loaders only on trusted run metadata: they import the recorded
solver/extension modules. For untrusted files, start with the bounded metadata
helpers instead.

Official 0.9 source shows that it:

- Loa

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

