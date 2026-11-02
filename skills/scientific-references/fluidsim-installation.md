---
id: sciref-fluidsim-installation
name: "Scientific Ref: Installation, native dependencies, and backends"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (fluidsim): Installation, native dependencies, and backends"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "fluidsim installation"
  - "installation, native dependencies, and backends"
keywords:
  - "fluidsim"
  - "installation"
  - "specialized"
  - "scientific"
  - "reference"
  - "native"
---

# Installation, native dependencies, and backends

## Supported baseline

Verified 2026-10-01:

- `fluidsim==0.9.0`, released on PyPI 2025-12-04.
- FluidSim package metadata requires Python `>=3.11` and classifies Python
  3.11–3.14.
- `fluidsim-core==0.9.0`, released 2025-12-03.
- `fluidfft==0.4.5`, released on PyPI 2025-10-14, requires Python `>=3.11`.
- `pyFFTW==0.15.1`, released 2025-10-22, requires Python `>=3.11`.
- `mpi4py==4.1.2`, released 2026-05-16, requires Python `>=3.8`.

The FluidSim installation page still says Python `>=3.9`; current PyPI and
`pyproject.toml` metadata say `>=3.11`. Use the package metadata for 0.9.0.

FluidSim 0.9.0 declares:

- Core: `fluidsim-core>=0.8.6,<0.9.1`, `h5py`, `h5netcdf`,
  `transonic>=0.6.2`, `xarray`, `rich`, `matplotlib>=3.3`, and `scipy`.
- `fft`: `pyfftw>=0.10.4`, `fluidfft>=0.4.0`.
- `mpi`: `mpi4py`.
- Other extras: `test`, `test-mpi`, and `pulp`.

The broad upstream constraints are compatibility ranges, not a reproducible
environment. Record the generated lock and artifact hashes.

## Reproducible uv environment

Preferred project workflow:

```bash
uv init --python 3.12
uv add "fluidsim[fft]==0.9.0" "fluidfft==0.4.5" "pyFFTW==0.15.1"
uv lock
uv sync --frozen
```

Check the lock into the study repository. Record:

- `uv.lock` SHA-256 and target platform.
- Python implementation/build.
- FluidSim, FluidSim Core, FluidDyn, FluidFFT, Transonic, Pythran, NumPy,
  SciPy, h5py, h5netcdf, xarray, and pyFFTW versions.
- Wheel/sdist hashes and package index.
- Compiler and native-library versions if any package builds locally.

For an isolated smoke environment:

```bash
uv venv --python 3.12
uv pip install "fluidsim[fft]==0.9.0" "fluidfft==0.4.5" "pyFFTW==0.15.1"
```

This pins direct dependencies but does not replace a lock for transitive
reproducibility.

Bare `fluidsim==0.9.0` supports parts of the framework and analysis stack, but a
verified local smoke test found that importing NS2D succeeded while
`Simul.create_default_params()` failed without `fluidfft`. Install the `fft`
extra for pseudospectral solvers.

Runtime coverage on 2026-10-01: Python 3.12.10, FluidDyn 0.9.0, NumPy 2.5.3,
SciPy 1.18.1, h5py 3.16.0, h5netcdf 1.8.1, Transonic 0.8.0, and xarray 2026.9.0.
Sequential pyFFTW construction, transforms, state serialization, output classes,
and restart were executed. Native-plugin/MPI installation commands below are
illustrative; no compiler, distributed allocation, or GPU was exercised.

## Sequential FFT choices

The non-compiling path is:

```bash
uv add "fluidsim[fft]==0.9.0" "fluidfft==0.4.5" "pyFFTW==0.15.1"
```

FluidFFT 0.4.5 registers:

- `fft2d.with_pyfftw`
- `fft3d.with_pyfftw`
- `fft2d.with_dask` is advertised by the core distribution even when the
  optional Dask dependency is absent; an advertised method can fail to import.

The native FFTW plugin is separately versioned:

```bash
uv add "fluidfft-fftw==0.0.1"
```

The `0.0.1` plugin versions are stable PyPI releases from February 2024 and are
versioned independently from FluidFFT 0.4.5; they are not proof of compatibility
with a particular native stack. Before installation, verify that each PyPI
project links to the official `fluiddyn/fluidfft` monorepo, review the plugin
source, resolve through `uv.lock`, retain artifact hashes, and use
`uv sync --frozen`. Do not trust a familiar distribution name alone.

It provides:

- `fft2d.with_fftw1d`
- `fft2d.with_fftw2d`
- `fft3d.with_fftw3d`

It requires discoverable FFTW headers/libraries and a working native build
toolchain. pyFFTW wheels bundle supported binaries on many 64-bit platforms;
source builds require FFTW `>=3.3`, Cython, and a compiler.

Discover registered plugin entry points on the current host:

```bash
fluidfft-get-methods
```

`get_methods()`/`fluidfft-get-methods` list entry points without importing their
implementations. In the reviewed environment `fft2d.with_dask` was listed but
`import_fft_class("fft2d.with_dask")` failed because Dask was absent. Do not
equate discovery with a usable dependency stack or ABI. Run a tiny transform
and FluidSim pilot, then record the selected method.

## MPI and distributed FFT

Nothing in this skill launches MPI or submits a scheduler job. First identify:

- Site MPI implementation and version: Open MPI, MPICH derivative, Intel MPI,
  Cray MPICH, or another vendor stack.
- Compiler wrappers and ABI.
- FFTW and `fftw3_mpi` versions/build options.
- Scheduler, process placement, cores/rank, threads/rank, memory/rank, wall time,
  filesystem, and module/container environment.

Then lock Python packages:

```bash
uv add "mpi4py==4.1.2" \
  "fluidfft-mpi-with-fftw==0.0.1" \
  "fluidfft-fftwmpi==0.0.1"
uv lock
```

Plugin methods:

- `fluidfft-mpi-with-fftw==0.0.1`:
  `fft2d.mpi_with_fftw1d`, `fft3d.mpi_with_fftw1d`.
- `fluidfft-fftwmpi==0.0.1`:
  `fft2d.mpi_with_fftwmpi2d`, `fft3d.mpi_with_fftwmpi3d`.
- `fluidfft-p3dfft==0.0.1`:
  `fft3d.mpi_with_p3dfft`, requiring P3DFFT.
- FluidFFT also declares `pfft` and `p3dfft` extras. Both require separately
  installed native MPI FFT libraries.

The package names use hyphens on PyPI; FluidFFT's optional dependency keys map
to distributions such as `fluidfft-mpi_with_fftw`. Let the lock resolve the
canonical distribution and preserve it.

`mpi4py` wheels still need a compatible MPI runtime. Convenience MPI wheels can
lack GPU awareness or site fabric support; mpi4py recommends system/vendor MPI
for production. Never mix an `mpi4py` build from one implementation with a
different launcher/runtime. Verify import and rank identity inside a manually
allocated tiny job before FluidSim.

The primary FluidFFT paper shows that the fastest backend depends on array
shape, machine, and process count; one-dimensional decomposition can be useful
at low rank count, while pencil/two-dimensional decomposition is needed to
avoid decomposition limits at high rank count. These are benchmark-context
claims, not universal backend recommendations.

## GPU status

The 2019 FluidFFT paper describes a cuFFT path, and the repository README still
lists cuFFT. However:

- FluidFFT 0.4.5 `pyproject.toml` declares no CUDA dependency/extra or cuFFT
  plugin entry point.
- The current supported-library page's CUDA section is an unfinished TODO.
- FluidSim 0.9.0 declares no GPU extra.

Therefore there is no supported one-line GPU installation in this skill. Do not
install `nvidia-cufft-*` and claim FluidSim acceleration: a runtime library alone
does not provide 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

