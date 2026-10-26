---
id: sciref-qutip-advanced
name: "Scientific Ref: QuTiP 5.3 Advanced Methods and Package Boundaries"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (qutip): QuTiP 5.3 Advanced Methods and Package Boundaries"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "qutip advanced"
  - "qutip 5.3 advanced methods and package boundaries"
keywords:
  - "qutip"
  - "advanced"
  - "specialized"
  - "scientific"
  - "reference"
---

# QuTiP 5.3 Advanced Methods and Package Boundaries

Research and API verification date: **2026-10-01**. Examples target
`qutip==5.3.1`.

Specialized methods add assumptions and convergence parameters. Use them only
when the physical model requires them.

## Bloch-Redfield

`brmesolve` derives dissipative dynamics from system coupling operators and bath
noise-power spectra:

```python
import numpy as np
from qutip import basis, brmesolve, sigmax, sigmaz

def bath_spectrum(w):
    return 0.02 * w if w > 0.0 else 0.0

result = brmesolve(
    0.5 * sigmaz(),
    basis(2, 0),
    np.linspace(0.0, 30.0, 601),
    a_ops=[(sigmax(), bath_spectrum)],
    e_ops={"z": sigmaz()},
    sec_cutoff=0.1,
    options={"atol": 1e-10, "rtol": 1e-8, "progress_bar": ""},
)
```

Required assumptions:

- weak system-environment coupling (Born approximation);
- initially factorized system/bath state where the derivation requires it;
- bath correlations decay faster than system evolution (Markov approximation);
- stationary bath spectra with the correct angular-frequency and
  positive/negative-frequency convention;
- a justified secular or partial-secular cutoff.

`sec_cutoff=-1` disables secularization. QuTiP's documentation warns that the
non-secular equation may produce negativity. Inspect trace, Hermiticity, and
minimum density-matrix eigenvalue through the entire run.

Environment objects can express thermal and fitted spectra more clearly than
callbacks. When using a callback, test it over every transition frequency and
near zero.

## Diffusive stochastic evolution

Use `ssesolve` for conditioned pure states and `smesolve` for density matrices:

```python
result = smesolve(
    H,
    rho0,
    tlist,
    c_ops=unmonitored_channels,
    sc_ops=monitored_channels,
    heterodyne=False,
    e_ops={"signal": measured_quadrature},
    ntraj=300,
    seeds=20260723,
    options={
        "dt": 0.001,
        "store_measurement": "end",
        "progress_bar": "",
    },
)
```

`heterodyne=False` selects homodyne and `True` selects heterodyne. Legacy
integer noise selectors are stale.

Converge:

- stochastic integration `dt`;
- output grid;
- trajectory count;
- seed sensitivity;
- monitored efficiency/model choices;
- measurement timing (`"start"` versus default end-of-step semantics when
  relevant).

`SMESolver.run_from_experiment` can replay known numeric noise or measurement
records. Treat records as bounded numeric data; do not accept executable
callbacks from untrusted configuration.

## Non-Markovian Monte Carlo with time-local rates

`nm_mcsolve` is for time-local master equations whose decay rates can become
negative. Its current input is a collection of operator/rate pairs, not a
generic two-time bath-correlation callback:

```python
import numpy as np
from qutip import basis, nm_mcsolve, sigmam, sigmaz

def rate(t):
    return 0.1 * np.sin(t)

result = nm_mcsolve(
    0.5 * sigmaz(),
    basis(2, 0),
    np.linspace(0.0, 5.0, 101),
    [(sigmam(), rate)],
    e_ops=[basis(2, 0).proj()],
    ntraj=400,
    seeds=20260723,
    options={"progress_bar": ""},
)
```

Here the integrated rate is `0.1 * (1 - cos(t)) >= 0`, so the exact
excited population `exp(-0.1 * (1 - cos(t)))` stays in `[0, 1]` even
when the instantaneous rate becomes negative. A cosine rate instead would
produce population above one after pi for this initially excited state.

This method does not make an arbitrary non-Markovian model valid. Verify that
the time-local generator and influence-martingale construction apply, report
sampling uncertainty, and audit completeness/positivity behavior.

## Floquet theory

For \(H(t+T)=H(t)\), the current QuTiP 5 abstraction is `FloquetBasis`:

```python
import numpy as np
from qutip import FloquetBasis, QobjEvo, sigmax, sigmaz

drive_frequency = 2.0
period = 2.0 * np.pi / drive_frequency

def drive(t, amplitude, omega):
    return amplitude * np.cos(omega * t)

H = QobjEvo(
    [0.5 * sigmaz(), [sigmax(), drive]],
    args={"amplitude": 0.2, "omega": drive_frequency},
)
floquet = FloquetBasis(H, period)
quasienergies = floquet.e_quasi
modes_at_zero = floquet.mode(0.0)
```

Before using Floquet dynamics:

1. numerically check `H(t + period) - H(t)` over representative times;
2. state the quasi-energy branch convention;
3. sweep Hilbert truncation and any precomputation grid;
4. inspect near-degenerate quasi-energies;
5. compare one-period propagation with direct evolution.

`fsesolve` handles closed periodic dynamics. `fmmesolve` handles a
Floquet-Markov construction:

```python
result = fmmesolve(
    floquet,
    rho0,
    tlist,
    c_ops=coupling_operators,
    spectra_cb=spectrum_callbacks,
    e_ops={"z": sigmaz()},
    w_th=temperature,
)
```

The coupling operators and spectrum callbacks are paired by position. They are
not ordinary Lindblad channels. Spectrum callbacks must accept and return
NumPy arrays (use `np.where`, not scalar `if w > 0`). Use `FMESolver`
directly to sweep its `kmax` sideband cutoff and `nT` quadrature count.
Verify weak-coupling, bath, and thermal
assumptions. QuTiP 5 result states are in the lab basis by default; the
`store_floquet_states` option controls additional Floquet-basis storage.

Old free-function mode workflows may remain for compatibility, but new work
should use `FloquetBasis`.

## HEOM

Import from the current namespace:

```python
from qutip.solver.heom import DrudeLorentzBath, HEOMSolver
```

The legacy QuTiP 4 nonmarkov HEOM namespace is stale.

Example:

```python
import numpy as np
from qutip import basis, sigmax, sigmaz
from qutip.solver.heom import DrudeLorentzBath, HEOMSolver

H_system = 0.5 * sigmaz()
rho0 = basis(2, 0).proj()

bath = DrudeLorentzBath(
    sigmax(),
    lam=0.05,
    gamma=1.0,
    T=0.5,
    Nk=3,
)
solver = HEOMSolver(
    H_system,
    bath,
    max_depth=4,
    options={
        "atol": 1e-10,
        "rtol": 1e-8,
        "store_states": True,
        "store_ados": False,
        "progress_bar": "",
    },
)
result = solver.run(rho0, np.linspace(0.0, 10.0, 201))
reduced_states = result.states
```

For arbitrary exponential expansions, the full current constructor is:

```text
BosonicBath(Q, ck_real, vk_real, ck_imag, vk_imag,
             combine=True, tag=None)
```

Do not omit the imaginary coefficient/frequency lists; use empty lists only
when the modeled correlation genuinely has no imaginary expansion.

HEOM convergence requires independent sweeps of:

- hierarchy `max_depth`;
- bath expansion count (`Nk

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

