---
id: sciref-qiskit-primitives
name: "Scientific Ref: V2 Primitives and PUBs"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (qiskit): V2 Primitives and PUBs"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "qiskit primitives"
  - "v2 primitives and pubs"
keywords:
  - "qiskit"
  - "primitives"
  - "specialized"
  - "scientific"
  - "reference"
  - "pubs"
---

# V2 Primitives and PUBs

Cloud authentication, QPU, session, and batch snippets are illustrative and were not executed in this refresh. Local evidence is listed in [sources.md](sources.md).
Qiskit primitives standardize two core tasks:

- **Sampler** executes measured circuits and returns shot-resolved classical data.
- **Estimator** computes expectation values of observables for states prepared by circuits.

Use V2 interfaces. Their unit of work is a **Primitive Unified Bloc (PUB)**.

## Implementations

| Implementation | Use |
|---|---|
| `StatevectorSampler` | Exact statevector evolution plus finite-shot sampling on the local CPU |
| `StatevectorEstimator` | Local statevector expectation values |
| Aer `SamplerV2` / `EstimatorV2` | High-performance and noisy local simulation |
| Runtime client-side `Sampler` / `Estimator` (V2 API) | IBM QPUs and IBM Runtime services |
| `BackendSamplerV2` / `BackendEstimatorV2` | Adapt a `BackendV2` that lacks native primitives |

The V2 `run()` structure is shared, but options are implementation-specific. Do not pass Runtime resilience options to statevector or Aer primitives.

## Sampler PUBs

A Sampler PUB contains:

1. One circuit with measurements.
2. Optional parameter values.
3. Optional per-PUB shots: `(circuit, values, shots)`.

The core SDK supports per-PUB shots. Runtime 0.50 client-side primitives require equal shot budgets across PUBs in one call; split unequal budgets into separate jobs.

Pass shots at the `run()` level unless a specific current API requires otherwise.

### One Circuit

```python
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler

circuit = QuantumCircuit(2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure_all()

sampler = StatevectorSampler(seed=11)
primitive_result = sampler.run([circuit], shots=1024).result()
pub_result = primitive_result[0]

counts = pub_result.data.meas.get_counts()
bitstrings = pub_result.data.meas.get_bitstrings()
metadata = pub_result.metadata
```

`meas` is the name of the classical register created by `measure_all()`.

### Multiple Circuits

```python
circuit_x = QuantumCircuit(1)
circuit_x.x(0)
circuit_x.measure_all()

circuit_h = QuantumCircuit(1)
circuit_h.h(0)
circuit_h.measure_all()

result = sampler.run([circuit_x, circuit_h], shots=512).result()
counts_x = result[0].data.meas.get_counts()
counts_h = result[1].data.meas.get_counts()
```

Each input PUB produces one `PubResult`.

### Parameter Sweep

```python
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.primitives import StatevectorSampler

theta = Parameter("theta")
circuit = QuantumCircuit(1)
circuit.ry(theta, 0)
circuit.measure_all()

values = [[0.0], [np.pi / 2], [np.pi]]
sampler = StatevectorSampler(seed=11)
pub_result = sampler.run(
    [(circuit, values)],
    shots=256,
).result()[0]

for index, value in enumerate(values):
    counts = pub_result.data.meas.get_counts(index)
    print(value[0], counts)
```

For a shaped `BitArray`, pass an index to `get_counts()` when results must remain separated by parameter point. Calling it without an index can aggregate over axes.

## Multiple Classical Registers

Sampler data fields use register names:

```python
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.primitives import StatevectorSampler

qubits = QuantumRegister(2, "q")
left = ClassicalRegister(1, "left")
right = ClassicalRegister(1, "right")
circuit = QuantumCircuit(qubits, left, right)
circuit.h(qubits[0])
circuit.cx(qubits[0], qubits[1])
circuit.measure(qubits[0], left[0])
circuit.measure(qubits[1], right[0])

pub_result = StatevectorSampler(seed=11).run(
    [circuit],
    shots=256,
).result()[0]

left_counts = pub_result.data.left.get_counts()
right_counts = pub_result.data.right.get_counts()
```

Do not assume every result has `.data.meas`. Inspect `circuit.cregs` or `pub_result.data`. Register counts are marginals. Preserve their paired shots with:

```python
joint_counts = pub_result.join_data(["left", "right"]).get_counts()
# Qiskit 2.5.2 BitArray: first listed register occupies least-significant bits.
assert set(joint_counts) <= {"00", "11"}
```

Do not multiply marginal frequencies to estimate cross-register correlations. In executed Qiskit 2.5.2, `left=1`, `right=0` with `join_data(["left", "right"])` yields `"01"`. The current API docstring claims the opposite displayed order; the released implementation calls `BitArray.concatenate_bits`, which puts the first input in the least-significant bits. Keep an asymmetric known-state test when upgrading; Bell `00`/`11` alone cannot detect reversal.

## Estimator PUBs

An Estimator PUB contains:

1. One circuit, normally without final measurements.
2. One observable or an array of observables.
3. Optional parameter values.
4. Optional per-PUB precision: `(circuit, observables, values, precision)`.

Use one precision per Runtime call; heterogeneous budgets are implementation-specific.

### One Circuit and Observable

```python
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp

circuit = QuantumCircuit(2)
circuit.h(0)
circuit.cx(0, 1)

observable = SparsePauliOp.from_list(
    [
        ("ZZ", 1.0),
        ("XX", 0.5),
    ]
)

estimator = StatevectorEstimator()
pub_result = estimator.run(
    [(circuit, observable)]
).result()[0]

expectation_values = pub_result.data.evs
standard_deviations = pub_result.data.stds
```

`SparsePauliOp` labels are little-endian with respect to qubit indices: the rightmost label character acts on qubit 0.

### Parameter Sweep

```python
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp

theta = Parameter("theta")
circuit = QuantumCircuit(2)
circuit.ry(theta, 0)
circuit.cx(0, 1)

observable = SparsePauliOp.from_list([("ZI", 1.0), ("XX", 0.5)])
values = [[0.0], [np.pi / 4], [np.pi / 2]]

pub_result = StatevectorEstimator().run(
    [(circuit, observable, values)]
).result()[0]

print(pub_result.data.evs)
```

The final axis of `values` corresponds to `list(circuit.parameters)`.

### Multiple Observables

```python
observables = [
    [SparsePauliOp.from_list([("ZZ", 1.0)])],
    [SparsePauliOp.from_list([("XX", 1.0)])],
]

pub_result = StatevectorEstimator().run(
    [(circuit, observables, values)]
).resul

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

