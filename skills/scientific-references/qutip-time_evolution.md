---
id: sciref-qutip-time-evolution
name: "Scientific Ref: QuTiP 5.3 Time Evolution"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (qutip): QuTiP 5.3 Time Evolution"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "qutip time evolution"
  - "qutip 5.3 time evolution"
keywords:
  - "qutip"
  - "time"
  - "evolution"
  - "specialized"
  - "scientific"
  - "reference"
---

# QuTiP 5.3 Time Evolution

Research and API verification date: **2026-10-01**. All signatures and examples
target `qutip==5.3.1`.

## Solver selection

| Solver | State/model | Main uncertainty |
|---|---|---|
| `sesolve` | Schrödinger equation, pure state, no collapse channels | ODE and model approximation |
| `mesolve` | Lindblad master equation, mixed state, or Liouvillian | channel validity and ODE error |
| `mcsolve` | quantum-jump trajectories | ODE error plus sampling error |
| `brmesolve` | microscopic weak-coupling bath spectra | Born-Markov/secular approximation and positivity |
| `ssesolve` | stochastic Schrödinger equation | diffusive record sampling |
| `smesolve` | stochastic master equation with monitored/unmonitored channels | diffusive record sampling |
| `fsesolve`/`fmmesolve` | periodic Floquet dynamics | period, basis, harmonic and bath approximations |

Do not use `mcsolve` merely to make a deterministic calculation parallel. Do
not use `brmesolve` as a generic replacement for a Lindblad model.

## Current function signatures

The important QuTiP 5.3 call boundaries are:

```text
sesolve(H, psi0, tlist, *, e_ops=None, args=None, options=None)
mesolve(H, rho0, tlist, c_ops=None, *, e_ops=None, args=None, options=None)
mcsolve(H, state, tlist, c_ops=(), *, e_ops=None, ntraj=500,
        args=None, options=None, seeds=None, target_tol=None, timeout=None)
brmesolve(H, psi0, tlist, a_ops=None, sec_cutoff=0.1, *,
          c_ops=None, e_ops=None, args=None, options=None)
ssesolve(H, psi0, tlist, sc_ops=(), heterodyne=False, *,
         e_ops=None, args=None, ntraj=500, options=None, seeds=None,
         target_tol=None, timeout=None)
smesolve(H, rho0, tlist, c_ops=(), sc_ops=(), heterodyne=False, *,
         e_ops=None, args=None, ntraj=500, options=None, seeds=None,
         target_tol=None, timeout=None)
```

In 5.3, `e_ops`, `args`, and `options` are keyword-only. Passing solver options
as arbitrary solver keyword arguments was removed. The old `qutip.Options`
export is no longer present; pass an ordinary dictionary.

## `sesolve`: closed unitary evolution

```python
import numpy as np
from qutip import basis, sesolve, sigmax, sigmaz

H = 0.5 * sigmax()
psi0 = basis(2, 0)
tlist = np.linspace(0.0, 10.0, 201)

result = sesolve(
    H,
    psi0,
    tlist,
    e_ops={"z": sigmaz()},
    options={"atol": 1e-10, "rtol": 1e-8, "progress_bar": ""},
)
z = np.asarray(result.e_data["z"])
```

For an ODE norm/trace audit, set `options["normalize_output"] = False`:
`sesolve`/`mesolve` normally normalize an initially normalized state on output,
which can conceal integrator drift. Quantum-jump trajectory normalization is
part of the unravelling and is a different operation.

Audit Hamiltonian Hermiticity and state norm. If norm drift is material, tighten
tolerances or investigate the model; do not normalize away unexplained error.

## `mesolve`: Lindblad or explicit Liouvillian evolution

```python
import numpy as np
from qutip import basis, mesolve, sigmam, sigmaz

gamma = 0.2
excited = basis(2, 0)
tlist = np.linspace(0.0, 12.0, 241)

result = mesolve(
    0.5 * sigmaz(),
    excited,
    tlist,
    c_ops=[np.sqrt(gamma) * sigmam()],
    e_ops={"p_excited": excited.proj()},
    options={
        "method": "adams",
        "atol": 1e-10,
        "rtol": 1e-8,
        "store_final_state": True,
        "progress_bar": "",
    },
)
```

When no collapse operators are supplied and `H` is not a superoperator,
`mesolve` may defer to `sesolve`. If `H` is an explicit Liouvillian, document
whether it is in valid Lindblad form or represents a deliberate approximation.

## `mcsolve`: quantum jumps

```python
result = mcsolve(
    0.5 * sigmaz(),
    excited,
    tlist,
    [np.sqrt(gamma) * sigmam()],
    e_ops=[excited.proj()],
    ntraj=500,
    seeds=20260723,
    options={
        "keep_runs_results": False,
        "progress_bar": "",
    },
)

mean_population = result.average_expect[0]
trajectory_spread = result.std_expect[0]
seed_manifest = result.seeds
```

`seeds` may be one integer/`SeedSequence` used to spawn trajectory seeds, or a
list with one seed per trajectory. QuTiP stores the realized seeds in the
result. Reusing them enables a paired comparison, but paired runs are not
independent replicates.

Trajectory rigor:

- increase `ntraj` and report stabilization or a target uncertainty;
- distinguish trajectory standard deviation from standard error of the mean;
- set `options={"keep_runs_results": True}` only when individual trajectories
  are actually required, because memory scales with trajectories and time
  points;
- collapse records are available per trajectory through result attributes such
  as `collapse`; do not print unbounded records by default;
- `target_tol` may stop before `ntraj`, so report the number actually run;
- report timeout termination and solver stats.

For mixed initial conditions, current QuTiP can sample the initial mixture; the
result then includes initial-state accounting. State this extra source of
sampling explicitly.

## `brmesolve`: Bloch-Redfield evolution

```python
import numpy as np
from qutip import basis, brmesolve, sigmax, sigmaz

def one_sided_spectrum(w):
    return 0.03 * w if w > 0.0 else 0.0

tlist = np.linspace(0.0, 30.0, 601)
result = brmesolve(
    0.5 * sigmaz(),
    basis(2, 0),
    tlist,
    a_ops=[(sigmax(), one_sided_spectrum)],
    e_ops={"z": sigmaz()},
    sec_cutoff=0.1,
    options={"atol": 1e-10, "rtol": 1e-8, "progress_bar": ""},
)
```

The coupling operator in each `a_ops` pair is normally Hermitian, and the
spectrum is a function of **angular frequency**. Prefer a current QuTiP
Environment object when it represents the bath more clearly.

Required checks:

- weak system-bath coupling (Born approximation);
- short bath memory compared with system dynamics (Markov approximation);
- stationary bath and correct positive/negative-frequency convention;
- secular choice: `sec_cutoff=-1` disables secularization and can worsen
  positivity;
- density-matrix trace, Hermiticity, and minimum eigenvalue over time.

See `advanced.md` for the physical boundaries.

## Stochastic Schrödinger and master equations

Use these for diffusive continuous-measurement unravellings, not jump
trajectories:

```python
result = smesolve(
    H,
    rho0,
    tlist,
    c_ops=unmonitored_channels,
    sc_ops=monitored_channels,
    heterodyne=False,  # homodyne
    e_ops={"signal": measured_quadrature},
    ntraj=200,
    seeds=20260723,


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

