---
id: sci-fluidsim
name: "Scientific: fluidsim"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Plans, configures, inspects, restarts, and analyzes bounded FluidSim computational-fluid-dynamics simulations with explicit numerical-validity and HPC safety checks. Use for FluidSim solver selection, parameter review, FFT/MPI setup, output diagnostics, or restart compatibility."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "fluidsim"
keywords:
  - "fluidsim"
  - "plans"
  - "configures"
  - "inspects"
  - "restarts"
  - "analyzes"
  - "bounded"
---

# FluidSim

Use FluidSim 0.9.0 as a framework for Python-defined numerical solvers, especially
periodic Cartesian pseudospectral CFD. Upstream FluidSim is CeCILL-2.1; the MIT
frontmatter license applies only to this skill.

This skill does **not** treat a completed run, a stable time step, a smooth plot,
or a closed program exit as evidence of numerical convergence or physical
validity.

## Required workflow

1. State equations, units or nondimensionalization, geometry, boundaries,
   initial conditions, forcing, observables, and acceptance criteria.
2. Select a verified solver and inspect its generated default parameters.
3. Create a strict JSON plan with explicit CPU, RAM, disk, wall-time, output-file,
   timestep, CFL, resolution, and dealiasing bounds.
4. Run the bundled validator and resource estimator.
5. Generate and review a dry-run script. It does nothing unless executed with an
   explicit config-ID acknowledgement.
6. Run one tiny serial pilot. Inspect budgets, divergence/constraints, spectral
   tails, CFL/time-step history, and output growth.
7. Refine grid and time step independently. Check conservation/budget residuals
   and observable sensitivity.
8. Only then prepare a site-specific MPI job. Never submit or launch MPI
   automatically.
9. Preserve config, script, `uv.lock`, package/platform/backend versions, logs,
   output inventory, checksums, and restart lineage.

Stop if physical assumptions, units, boundary conditions, forcing semantics,
resolution criteria, resource limits, or acceptance criteria are missing.

## Version and installation

As verified on 2026-10-01:

- Latest stable PyPI release: `fluidsim==0.9.0` (2025-12-04).
- Package metadata requires Python `>=3.11` and lists Python 3.11–3.14.
- Pseudospectral parameter creation needs FluidFFT; bare `fluidsim` imported in
  the smoke test, but `ns2d.create_default_params()` failed until the `fft` extra
  was installed.
- Current companion versions tested here: `fluidfft==0.4.5` and
  `pyFFTW==0.15.1`.

Prefer a project lock:

```bash
uv init --python 3.12
uv add "fluidsim[fft]==0.9.0" "fluidfft==0.4.5" "pyFFTW==0.15.1"
uv lock
uv sync --frozen
```

For an isolated disposable environment:

```bash
uv venv --python 3.12
uv pip install "fluidsim[fft]==0.9.0" "fluidfft==0.4.5" "pyFFTW==0.15.1"
```

The project lock is the reproducibility record; direct pins alone do not freeze
all transitive artifacts. Do not reuse a lock across incompatible platforms or
MPI ABIs.

MPI is optional and native:

```bash
uv add "mpi4py==4.1.2" "fluidfft-mpi-with-fftw==0.0.1" "fluidfft-fftwmpi==0.0.1"
uv lock
```

Those packages still require a compatible MPI runtime and FFTW development
libraries. The optional native plugins are:

- `fluidfft-fftw==0.0.1`: sequential
  `fft2d.with_fftw1d`, `fft2d.with_fftw2d`, `fft3d.with_fftw3d`.
- `fluidfft-mpi-with-fftw==0.0.1`: MPI
  `fft2d.mpi_with_fftw1d`, `fft3d.mpi_with_fftw1d`.
- `fluidfft-fftwmpi==0.0.1`: MPI-enabled FFTW
  `fft2d.mpi_with_fftwmpi2d`, `fft3d.mpi_with_fftwmpi3d`.
- `fluidfft-p3dfft==0.0.1`: `fft3d.mpi_with_p3dfft`; requires P3DFFT.
- FluidFFT also declares PFFT and P3DFFT extras; audit and pin their native
  stacks for the target cluster.

FluidFFT documents cuFFT historically, but FluidFFT 0.4.5 declares no CUDA extra
or installed GPU plugin in its package metadata, and its CUDA installation page
is unfinished. Do not claim GPU acceleration or install an unrelated CUDA wheel
as a FluidSim backend. Treat GPU work as source-level experimental integration
requiring separate validation.

See [installation](references/installation.md) for system dependencies, MPI ABI,
HDF5-MPI, backend discovery, and verification.

## API snapshot

Use direct, versioned imports:

```python
from fluidsim.solvers.ns2d.solver import Simul

params = Simul.create_default_params()
params.oper.nx = params.oper.ny = 32
params.oper.Lx = params.oper.Ly = 2 * 3.141592653589793
params.oper.coef_dealiasing = 2 / 3
params.time_stepping.USE_CFL = True
params.time_stepping.cfl_coef = 0.5
params.time_stepping.deltat0 = 0.001
params.time_stepping.deltat_max = 0.01
params.time_stepping.t_end = 0.1
params.time_stepping.max_elapsed = "00:05:00"
params.init_fields.type = "noise"
params.init_fields.noise.velo_max = 0.01
params.output.HAS_TO_SAVE = False
params.output.ONLINE_PLOT_OK = False
```

Important 0.9 corrections:

- CFL field: `params.time_stepping.cfl_coef`, not `CFL`.
- Time-correlated forcing:
  `params.forcing.tcrandom.time_correlation`, not a flat
  `tcrandom_time_correlation`.
- NS2D default initial types include `constant`, `noise`, `jet`, `dipole`,
  `from_file`, `from_simul`, and `in_script`; do not invent a universal list for
  every solver.
- Output state files default to `state_phys_t*.nc`; spectra use
  `spectra1D.h5`/`spectra2D.h5`; scalar means are solver-dependent
  `spatial_means.txt` or JSON-lines.
- `params.output.sub_directory` is relative under `FLUIDSIM_PATH`.

`ParamContainer` rejects undeclared attributes. Always generate defaults from the
selected `Simul` class and inspect them before changing values. See
[parameters](references/parameters.md).

## Solvers

Primary Cartesian CFD keys and imports:

```python
from fluidsim.solvers.ns2d.solver import Simul       # ns2d
from fluidsim.solvers.ns2d.bouss.solver import Simul # ns2d.bouss
from fluidsim.solvers.ns2d.strat.solver import Simul # ns2d.strat
from fluidsim.solvers.ns3d.solver import Simul       # ns3d
from fluidsim.solvers.ns3d.bouss.solver import Simul # ns3d.bouss
from fluidsim.solvers.ns3d.strat.solver import Simul # ns3d.strat
```

The 0.9 registry also includes `plate2d`, `sw1l` variants, `waves2d`, 1D models,
0D models, spherical solvers, and framework adapters. Availability in the
registry does not make a solver appropriate for a scientific question. Verify
equations, variables, geometry, boundaries, and diagnostics in the solver
source. See [solvers](references/solvers.md).

## Forcing and time advancement

Forcing is solver-specific. A current normalized random example is:

```python
params.forcing.enable = True
params.forcing.type = "tcrandom"
params.forcing.forcing_rate = 1.0
params.forcing.nkmin_forcing = 4
params.forcing.nkmax_forcing = 5
params.forcing.tcrandom.time_correlation = "based_on_forcing_rate"
```

Record the forced variable, normalization definition, wave-number band, random
seed/state, injection target, and measured injection. FluidSim 0.9 saves state
parameters for restart; 0.8.6 fixed time-corre

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

