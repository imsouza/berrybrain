---
id: sciref-qutip-analysis
name: "Scientific Ref: QuTiP 5.3 Analysis, Steady States, and Spectra"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (qutip): QuTiP 5.3 Analysis, Steady States, and Spectra"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "qutip analysis"
  - "qutip analise"
  - "qutip 5.3 analysis, steady states, and spectra"
keywords:
  - "qutip"
  - "analysis"
  - "analise"
  - "specialized"
  - "scientific"
  - "reference"
---

# QuTiP 5.3 Analysis, Steady States, and Spectra

Research and API verification date: **2026-10-01**. Examples target
`qutip==5.3.1`.

## Analysis starts with invariants

For every reported state, record quantitative checks before interpreting an
observable:

```python
import numpy as np

def density_audit(rho, tolerance=1e-9):
    if not rho.isoper:
        raise ValueError("density_audit requires an operator")
    hermitian = bool(rho.isherm)
    eigenvalues = np.linalg.eigvalsh(rho.full()) if hermitian else None
    trace = complex(rho.tr())
    return {
        "is_hermitian": hermitian,
        "trace_error": float(abs(trace - 1.0)),
        "minimum_eigenvalue": float(eigenvalues.min()) if hermitian else None,
        "positive_within_tolerance": hermitian and bool(eigenvalues.min() >= -tolerance),
    }
```

Also check:

- `state.dims` matches every observable and the declared subsystem order;
- ket norm or density-matrix trace stays stable over time;
- Hermitian observables have negligible imaginary expectation;
- populations remain within tolerance of `[0, 1]`;
- symmetry, conserved quantity, or analytic-limit checks hold where applicable;
- numerical tolerance is smaller than the effect being claimed.

Do not repair a state by clipping eigenvalues or renormalizing unless that
post-processing is part of a documented method and its impact is reported.

## Expectations and uncertainty

```python
from qutip import expect, num, variance

n_op = num(N)
mean_n = expect(n_op, rho)
variance_n = variance(n_op, rho)
```

For solver output, dict-form `e_ops` gives named `result.e_data`:

```python
result = mesolve(
    H,
    rho0,
    tlist,
    c_ops=c_ops,
    e_ops={"number": n_op, "energy": H},
)
number_vs_time = result.e_data["number"]
```

For Monte Carlo/stochastic results, report both ensemble means and sampling
uncertainty. `std_expect` is trajectory spread, not automatically the standard
error; a simple independent-trajectory standard error scales as
`std / sqrt(ntraj)`, subject to the solver's sampling design.

## Entropy, purity, and distances

```python
from qutip import entropy_linear, entropy_vn, fidelity, tracedist

von_neumann_nats = entropy_vn(rho)          # default natural-log base
von_neumann_bits = entropy_vn(rho, base=2)
linear_entropy = entropy_linear(rho)
purity = float((rho * rho).tr().real)
state_fidelity = fidelity(rho, sigma)
trace_distance = tracedist(rho, sigma)
```

Always state the logarithm base. QuTiP `fidelity` returns root fidelity
`Tr(sqrt(sqrt(rho) * sigma * sqrt(rho)))`; for two kets this is absolute
overlap. Square it only when the comparison uses the squared convention.

For bipartite entropy:

```python
rho_A = rho_AB.ptrace(0)  # keep subsystem 0
entanglement_entropy = entropy_vn(rho_A, base=2)
```

This is an entanglement entropy only when the global bipartite state and the
chosen measure meet the necessary assumptions. For mixed states, reduced-state
entropy also contains classical mixture.

Common specialized functions include `concurrence`, `negativity`,
`entropy_mutual`, and `partial_transpose`. Verify their supported dimensions and
argument definitions in the current API before applying them.

## Steady-state calculation

Current signature:

```text
steadystate(A, c_ops=[], *, method="direct", solver=None, **kwargs)
```

`A` may be a Hamiltonian or a Liouvillian. Available high-level methods include
`direct`, `eigen`, `svd`, `power`, and `propagator`; linear-system solver choices
are separate.

```python
from qutip import liouvillian, operator_to_vector, steadystate

rho_ss = steadystate(H, c_ops, method="direct")
L = liouvillian(H, c_ops)
residual = (L * operator_to_vector(rho_ss)).norm()
```

Report:

- residual norm and normalization error;
- Hermiticity and minimum eigenvalue;
- method and linear solver;
- matrix/data representation and relevant tolerances;
- whether the zero eigenvalue is unique;
- comparison with long-time evolution from more than one initial state when
  uniqueness matters.

A small residual does not prove uniqueness or physicality. Degenerate steady
spaces require analysis of the Liouvillian nullspace and initial-state
dependence.

The `svd` method is dense and intended for small systems. Sparse/direct methods
can still be memory intensive; monitor fill-in and compare methods on a reduced
model.

For periodically driven systems, a static `steadystate` call is generally not
the desired asymptotic object. Use an appropriate periodic/Floquet approach.
In QuTiP 5.3, `steadystate_fourier` is the current name for the specialized
cosine-driven Fourier solver; `steadystate_floquet` is deprecated.

## Two-time correlations

Current stationary/transient two-operator API:

```python
from qutip import correlation_2op_1t, correlation_2op_2t

corr_1t = correlation_2op_1t(
    H,
    rho0,
    taulist,
    c_ops,
    a_op,
    b_op,
    solver="me",
    options={"atol": 1e-10, "rtol": 1e-8},
)

corr_2t = correlation_2op_2t(
    H,
    rho0,
    tlist,
    taulist,
    c_ops,
    a_op,
    b_op,
)
```

For `correlation_2op_1t`, the quantity is ordered according to the function's
documented \(A(\tau)B(0)\)-style convention. Do not infer operator order from a
variable name.

Passing `state0=None` requests a steady-state initial condition only for
supported constant systems with collapse operators. Compute and audit the
steady state explicitly when provenance matters.

Current three-operator entry points include:

```python
from qutip import correlation_3op, correlation_3op_1t, correlation_3op_2t
```

QuTiP 5.3 added `max_t_plus_tau` and mapping controls to selected two-time and
three-operator routines. The old `correlation_4op_1t` recipe is not a current
public API; express a four-operator quantity through the documented
three-operator interfaces when mathematically appropriate, or derive a tested
regression workflow.

Correlation checks:

- operator ordering and adjoints;
- transient versus stationary definition;
- normalized versus unnormalized coherence;
- regression-theorem assumptions;
- convergence of both `tlist` and `taulist`;
- tail decay before finite-window transforms.

## Direct stationary spectrum

Current signature:

```text
spectrum(H, wlist, c_ops, a_op, b_op, solver="es")
```

```python
import numpy as np
from qutip import spectrum

wlist = np.linspace(-5.0, 5.0, 1001)
S = spectrum(H, wlist, c_ops, a_op, b_op, solver="es")
```

The function computes the Fourier transform of a **steady-state** correlation.


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

