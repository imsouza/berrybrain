---
id: sci-qutip
name: "Scientific: qutip"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Simulate and audit closed and open quantum-system models with QuTiP 5, including deterministic, trajectory, steady-state, spectral, and phase-space workflows. Use for local quantum-dynamics work where physical assumptions, dimensions, and numerical convergence must be explicit."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "qutip"
keywords:
  - "qutip"
  - "simulate"
  - "audit"
  - "closed"
  - "open"
  - "quantum"
  - "models"
---

# QuTiP 5

## Scope

Use QuTiP for finite-dimensional quantum mechanics, quantum optics, Lindblad
dynamics, trajectories, weak-coupling Bloch-Redfield models, and specialized
Floquet, HEOM, and permutational-invariance methods. It is not a hardware
execution SDK. Circuit and control functionality moved to separate QuTiP family
packages.

This skill targets **QuTiP 5.3.1**, released 2026-08-04. QuTiP 5.3 requires
Python 3.11 or newer. Its required distributions are NumPy (`>=1.23.2`), SciPy
(`>=1.9.2`, excluding `1.16.0` and `1.17.0`), and `packaging`.

## Reproducible uv snapshot

Create a dedicated environment and pin every direct distribution:

```bash
uv venv --python 3.11
uv pip install "qutip==5.3.1"
```

For plots:

```bash
uv pip install "qutip[graphics]==5.3.1"
```

Optional QuTiP family packages are independently versioned:

```bash
uv pip install "qutip-qip==0.4.2"
uv pip install "qutip-qtrl==0.2.0"
uv pip install "qutip-jax==0.1.1"
```

- `qutip-qip` 0.4.2 (2026-06-23) is the production/stable circuit, gate, and
  noisy-device simulation package. Import from `qutip_qip`, not `qutip.qip`.
- `qutip-qtrl` 0.2.0 (2026-06-23) provides GRAPE and CRAB **quantum optimal
  control**. It is not a trajectory viewer. Import from `qutip_qtrl`, not
  `qutip.control`; PyPI still classifies it pre-alpha.
- `qutip-jax` 0.1.1 (2025-05-29) is the official JAX data backend for GPU and
  automatic-differentiation experiments. It is explicitly pre-alpha.
- `qutip-cupy` is an official QuTiP-organization repository, but it has no PyPI
  release and its own README says it is not officially released. Do not put an
  unreleased Git install into a reproducible workflow.

Use a project lockfile or a hash-generating `uv pip compile` workflow when
transitive dependency identity must also be frozen.

Core tests cover small native CPU systems with known solutions. Optional JAX
checks cover CPU conversion/evolution and differentiation only; GPU/MPI,
large HEOM hierarchies, and experimentally realistic physics are unvalidated.
Snippets with placeholders such as `H`, `rho0`, or `c_ops` are illustrative
fragments to adapt after defining a consistent model.

## Non-negotiable model contract

Before solving, record:

1. **Units and convention.** QuTiP equations normally set \(\hbar=1\).
   Hamiltonian entries are angular frequencies and rates have reciprocal-time
   units. A decay rate specified as `1/T1` needs no `2*pi` factor. Convert
   cyclic frequency with \(2\pi f\); never mix Hz and rad/s.
2. **Subsystem order.** `tensor(A, B, C)` fixes subsystem indices `0, 1, 2`.
   Preserve that order in every state, operator, collapse channel, and partial
   trace. `obj.ptrace([0, 2])` keeps those subsystems; it does not trace them.
3. **State validity.** Check ket norm or density-matrix Hermiticity, unit trace,
   and eigenvalues above a stated negative tolerance. Tiny negative values may
   be numerical; material negativity invalidates a claimed state.
4. **Generator meaning.** A Lindblad channel with rate `gamma` is represented
   by `sqrt(gamma) * A`, not `gamma * A`. Define what each rate measures. For
   example, `sqrt(gamma_phi / 2) * sigmaz()` gives coherence decay
   `exp(-gamma_phi * t)`.
5. **Approximations.** State rotating-wave, Born-Markov, secular, weak-coupling,
   bath-equilibrium, truncation, symmetry, and initial-factorization assumptions
   wherever used.
6. **Numerics.** Justify Hilbert truncation, output grid, integration method,
   tolerances, trajectory count, and random seeds. Report `result.stats`.
7. **Convergence.** Sweep every artificial cutoff: Fock dimension, time/frequency
   window and spacing, ODE tolerances, trajectories, Floquet harmonics, HEOM
   depth and bath exponents, or PIQS representation as applicable.

## Qobj, dimensions, and tensor order

Prefer explicit imports and inspect both shape and structured dimensions:

```python
from qutip import basis, qeye, sigmaz, tensor

psi = tensor(basis(2, 0), basis(3, 1))
z_on_first = tensor(sigmaz(), qeye(3))

assert psi.shape == (6, 1)
assert psi.dims == [[2, 3], [1]]
assert z_on_first.dims == [[2, 3], [2, 3]]
rho_first = psi.proj().ptrace(0)  # keep subsystem 0
```

Matrix shape alone is insufficient: two objects can both be 6-by-6 but encode
different tensor factorizations. Read `references/core_concepts.md` before
building composite, superoperator, or channel models.

## Choose the solver by physics

| Model | Current API | Required justification |
|---|---|---|
| Closed, pure, unitary | `sesolve` | Hermitian Hamiltonian; no dissipation |
| Lindblad/open or mixed | `mesolve` | Markovian completely positive model and channel rates |
| Quantum jumps | `mcsolve` | Unravelling, trajectory convergence, seeds |
| Microscopic weak bath | `brmesolve` | Born-Markov/weak coupling, spectra, secular choice |
| Diffusive measurement | `ssesolve`, `smesolve` | monitored versus unmonitored channels |
| Periodic drive | `FloquetBasis`, `fsesolve`, `fmmesolve` | verified period and Floquet convergence |
| Structured non-Markovian bath | `qutip.solver.heom` | bath expansion and hierarchy convergence |
| Symmetric spin ensemble | `qutip.piqs` | permutation symmetry and basis choice |

Do not select a more specialized solver merely because it exists.

## Deterministic open-system example

QuTiP 5.3 uses ordinary option dictionaries. `e_ops`, `args`, and
`options` are keyword-only; the old mutable options object is gone.

```python
import numpy as np
from qutip import basis, mesolve, sigmam, sigmaz

omega = 2.0
gamma = 0.15
tlist = np.linspace(0.0, 20.0, 401)
excited = basis(2, 0)

result = mesolve(
    0.5 * omega * sigmaz(),
    excited,
    tlist,
    c_ops=[np.sqrt(gamma) * sigmam()],
    e_ops={"sigma_z": sigmaz(), "excited": excited.proj()},
    options={
        "method": "adams",
        "atol": 1e-10,
        "rtol": 1e-8,
        "store_final_state": True,
        "normalize_output": False,
        "progress_bar": "",
    },
)

population = np.asarray(result.e_data["excited"])
assert np.max(np.abs(population - np.exp(-gamma * tlist))) < 2e-6
assert isinstance(result.stats, dict)
```

If the problem is stiff, compare `bdf` or `lsoda`; do not change an integrator
without rerunning tolerance and invariant checks. QuTiP 5.3 also supports
`options={"matrix_form": True}` in `mesolve`; benchmark and validate it before
using it as a default.

## Time-dependent systems

Prefer trusted Pythonic callables or numeric coefficient arrays. Do not crea

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

