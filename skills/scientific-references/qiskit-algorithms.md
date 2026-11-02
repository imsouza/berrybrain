---
id: sciref-qiskit-algorithms
name: "Scientific Ref: Algorithms, Addons, and Application Packages"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (qiskit): Algorithms, Addons, and Application Packages"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "qiskit algorithms"
  - "algorithms, addons, and application packages"
keywords:
  - "qiskit"
  - "algorithms"
  - "specialized"
  - "scientific"
  - "reference"
  - "addons"
---

# Algorithms, Addons, and Application Packages

The core `qiskit` distribution provides circuits, operators, primitives, synthesis, transpilation, and quantum-information tools. High-level algorithms and domain applications live in separate packages.

## Reviewed Package Matrix

Release metadata and official API documentation checked on **2026-10-01**. The VQE example was executed against a dense exact reference, and the two-variable Optimization/QAOA example returned the known optimum. Nature, Machine Learning, and addon workflows are illustrative and were not rerun in this refresh:

| Package | Version | Primary role |
|---|---:|---|
| `qiskit-algorithms` | 0.4.0 | VQE, QAOA, Grover, phase estimation, eigensolvers, optimizers |
| `qiskit-nature` | 0.8.0 | Electronic structure, second quantization, mappers |
| `qiskit-nature-pyscf` | 0.4.0 | PySCF electronic-structure driver integration |
| `qiskit-machine-learning` | 0.9.1 | Kernels, QNNs, classifiers/regressors, Torch connector |
| `qiskit-optimization` | 0.7.0 | Quadratic programs, converters, quantum optimization wrappers |
| `qiskit-addon-cutting` | 0.10.0 | Circuit and operator cutting |
| `qiskit-addon-sqd` | 0.13.1 | Sample-based quantum diagonalization |
| `qiskit-addon-obp` | 0.3.0 | Operator backpropagation |
| `qiskit-addon-mpf` | 0.3.0 | Multi-product formulas |
| `qiskit-addon-aqc-tensor` | 0.3.1 | Approximate quantum compilation with tensor networks |

Install exact pins together in a fresh environment:

```bash
uv pip install \
  "qiskit==2.5.2" \
  "qiskit-algorithms==0.4.0" \
  "qiskit-optimization==0.7.0"
```

For chemistry:

```bash
uv pip install \
  "qiskit==2.5.2" \
  "qiskit-algorithms==0.4.0" \
  "qiskit-nature[pyscf]==0.8.0"
```

Resolve application packages together; their Qiskit compatibility windows can differ.

## Decide Between Manual and Library Implementations

Use a manual circuit when:

- teaching or inspecting a small algorithm,
- testing a new circuit construction,
- controlling every primitive PUB and compilation step,
- avoiding an application package dependency.

Use an application package when:

- it provides tested problem transformations,
- the result object and domain post-processing are valuable,
- the implementation accepts current V2 primitives,
- its release supports the installed Qiskit version.

Do not copy a pre-1.0 algorithm tutorial without checking constructors and primitive requirements.

## VQE with Qiskit Algorithms 0.4

This verified local example uses the V2 `StatevectorEstimator`:

```python
from qiskit.circuit.library import efficient_su2
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP

hamiltonian = SparsePauliOp.from_list(
    [
        ("ZI", 1.0),
        ("IZ", 1.0),
        ("XX", 0.2),
    ]
)
ansatz = efficient_su2(
    num_qubits=2,
    reps=1,
    entanglement="linear",
)

vqe = VQE(
    estimator=StatevectorEstimator(),
    ansatz=ansatz,
    optimizer=SLSQP(maxiter=100),
    initial_point=[0.0] * ansatz.num_parameters,
)
result = vqe.compute_minimum_eigenvalue(hamiltonian)
energy = float(result.eigenvalue.real)
# Tiny diagnostic only: dense diagonalization is exponential.
import numpy as np
exact_energy = float(np.linalg.eigvalsh(hamiltonian.to_matrix())[0])
assert abs(energy - exact_energy) < 1e-5
print(energy, exact_energy)
```

For hardware:

1. Use the Runtime client-side `Estimator`.
2. Provide a transpiler adapter or manage the parameterized ISA circuit explicitly.
3. Bound optimizer iterations and requested precision.
4. Store each job ID and convergence record.

Do not transpile a newly bound circuit from scratch in every cost-function call.

## QAOA and Qiskit Optimization

Model a binary problem with `QuadraticProgram`:

```python
from qiskit.primitives import StatevectorSampler
from qiskit_optimization.minimum_eigensolvers import QAOA
from qiskit_optimization.optimizers import COBYLA
from qiskit_optimization.utils import algorithm_globals
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer

problem = QuadraticProgram("binary_demo")
problem.binary_var("x")
problem.binary_var("y")
problem.maximize(
    linear={"x": 1, "y": 1},
    quadratic={("x", "y"): -2},
)

algorithm_globals.random_seed = 5  # optimizer initialization is separate from sampler seed
qaoa = QAOA(
    sampler=StatevectorSampler(seed=5),
    optimizer=COBYLA(maxiter=100),
    reps=1,
)
solver = MinimumEigenOptimizer(qaoa)
result = solver.solve(problem)

print(result.x, result.fval, result.status)
```

Qiskit Optimization 0.7 ships its own `minimum_eigensolvers`, optimizers, and utilities; use those types with `MinimumEigenOptimizer` instead of mixing `qiskit_algorithms.QAOA` results. Use optimizer objects such as `COBYLA(...)`, not old string-valued optimizer arguments.

Before claiming a quantum result:

- compare with a classical solver for small instances,
- verify variable-to-bitstring ordering,
- report feasibility and objective value,
- separate optimizer stochasticity from quantum sampling,
- quantify total circuit evaluations and shot cost.

## Grover and Phase Estimation

Qiskit Algorithms 0.4 constructors accept V2 Sampler implementations:

```python
from qiskit.primitives import StatevectorSampler
from qiskit_algorithms import Grover, PhaseEstimation

sampler = StatevectorSampler(seed=5)
grover = Grover(sampler=sampler)
phase_estimation = PhaseEstimation(
    num_evaluation_qubits=4,
    sampler=sampler,
)
```

The old `quantum_instance=` argument is not current.

Use `QFTGate` in custom phase-estimation circuits:

```python
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFTGate

inverse_qft = QFTGate(4).inverse()
circuit = QuantumCircuit(4)
circuit.append(inverse_qft, range(4))
```

The `QFT` blueprint class is deprecated and scheduled for removal in Qiskit 3.0.

## Qiskit Nature

Qiskit Nature converts domain problems into second-quantized operators and qubit operators.

```python
from qiskit_nature.units import DistanceUnit
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper

driver = PySCFDriver(
    atom="H 0 0 0; H 0 0 0.735",
    unit=DistanceUnit.ANGSTROM,
    basis="sto3g",
    charge=0,
    spin=0,
)
problem = driver.run()

fermionic_hamiltonian = problem.hamiltonian.second_q_op()
mappe

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

