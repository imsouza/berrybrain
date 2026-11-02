---
id: sciref-qiskit-circuits
name: "Scientific Ref: Circuits, Parameters, Control Flow, and Serialization"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (qiskit): Circuits, Parameters, Control Flow, and Serialization"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "qiskit circuits"
  - "circuits, parameters, control flow, and serialization"
keywords:
  - "qiskit"
  - "circuits"
  - "specialized"
  - "scientific"
  - "reference"
  - "parameters"
---

# Circuits, Parameters, Control Flow, and Serialization

## Circuit Data Model

`QuantumCircuit` stores ordered quantum bits, classical bits, instructions, parameters, global phase, metadata, and optional real-time classical control flow.

```python
from qiskit import QuantumCircuit

circuit = QuantumCircuit(3, 3, name="ghz")
circuit.h(0)
circuit.cx(0, 1)
circuit.cx(1, 2)
circuit.measure([0, 1, 2], [0, 1, 2])

print(circuit.num_qubits)
print(circuit.num_clbits)
print(circuit.depth())
print(circuit.count_ops())
```

Use explicit registers when result names or control-flow operands matter:

```python
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister

qubits = QuantumRegister(2, "q")
syndrome = ClassicalRegister(1, "syndrome")
readout = ClassicalRegister(2, "readout")
circuit = QuantumCircuit(qubits, syndrome, readout)
```

Sampler V2 returns one data field per classical register, so meaningful register names improve result handling.

## Bit and Pauli Ordering

Qiskit uses little-endian conventions:

- Qubit 0 is conventionally the least-significant qubit.
- Count strings are printed most-significant classical bit first.
- The rightmost character of a Pauli label acts on qubit 0.
- Circuit diagrams normally draw qubit 0 at the top.

For a two-qubit operator, `"ZI"` applies `Z` to qubit 1 and identity to qubit 0. Never reverse strings based only on visual circuit order.

When translating a bitstring into graph vertices or variables, write and test an explicit conversion:

```python
def qiskit_bitstring_to_classical_values(bitstring: str) -> list[int]:
    """Decode one register in classical-bit order 0, 1, ..."""
    return [int(bit) for bit in reversed(bitstring.replace(" ", ""))]
```

This yields classical-bit order, not qubit order. Map through each `measure(qubit, clbit)` instruction before interpreting variables. For multiple registers or `join_data`, decode with the recorded register order; blindly stripping spaces does not establish the qubit mapping.

## Gates and Instructions

```python
from math import pi
from qiskit import QuantumCircuit

circuit = QuantumCircuit(3)

# One-qubit gates
circuit.x(0)
circuit.h(1)
circuit.s(1)
circuit.t(2)
circuit.rx(pi / 3, 0)
circuit.ry(pi / 4, 1)
circuit.rz(pi / 5, 2)

# Two- and three-qubit gates
circuit.cx(0, 1)
circuit.cz(1, 2)
circuit.swap(0, 2)
circuit.ccx(0, 1, 2)
```

Prefer high-level gates while constructing the algorithm. Let a target-aware transpiler translate them to the selected backend's instruction set.

Barriers are directives that constrain some transpiler reordering and optimization. Use them only when the experimental boundary matters, not as visual decoration:

```python
circuit.barrier(label="logical-boundary")
```

## Measurements and Resets

```python
from qiskit import QuantumCircuit

circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure([0, 1], [0, 1])
```

`measure_all()` defaults to `add_bits=True`, adding a new register even when classical bits already exist (a name collision can change `meas`). Use `add_bits=False` only when sufficient classical bits exist and their ordering is intended:

```python
circuit = QuantumCircuit(2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure_all()
print([register.name for register in circuit.cregs])
```

Sampler requires measurement instructions for sampled classical output. Estimator generally uses circuits without final measurements.

Use `reset()` only when the execution target supports it:

```python
circuit.reset(0)
```

## Parameterized Circuits

Primitive PUBs are the preferred way to evaluate one parameterized circuit at many values.

```python
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector

theta = ParameterVector("theta", 3)
circuit = QuantumCircuit(3)
for qubit, parameter in enumerate(theta):
    circuit.ry(parameter, qubit)
circuit.cx(0, 1)
circuit.cx(1, 2)

parameter_order = list(circuit.parameters)
parameter_values = np.array(
    [
        [0.0, 0.0, 0.0],
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]
)

assert parameter_values.shape[-1] == len(parameter_order)
```

Do not assume that creation order and `circuit.parameters` order are interchangeable for arbitrary named parameters. Print or persist the order:

```python
print([parameter.name for parameter in circuit.parameters])
```

For debugging or APIs that require a bound circuit:

```python
bound = circuit.assign_parameters(
    dict(zip(parameter_order, parameter_values[0], strict=True))
)
```

For iterative primitive workloads, keep the circuit parameterized and pass values in the PUB instead of producing and transpiling a bound circuit on every iteration.

## Composition and Reuse

```python
from qiskit import QuantumCircuit

prepare = QuantumCircuit(2, name="prepare")
prepare.h(0)

entangle = QuantumCircuit(2, name="entangle")
entangle.cx(0, 1)

combined = prepare.compose(entangle)
```

Map qubits explicitly when composing circuits with different widths:

```python
larger = QuantumCircuit(4)
larger.compose(combined, qubits=[1, 3], inplace=True)
```

Convert a reusable unitary subcircuit to a gate or instruction:

```python
bell_prep = combined.to_gate(label="Bell prep")
outer = QuantumCircuit(2)
outer.append(bell_prep, [0, 1])
```

Circuits containing measurements or other non-unitary instructions cannot be converted to a `Gate`.

## Current Circuit-Library Constructors

Qiskit 2.x is moving from mutable blueprint classes to functions and gates that build concrete objects immediately.

```python
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFTGate, efficient_su2, real_amplitudes

ansatz = efficient_su2(
    num_qubits=4,
    reps=2,
    entanglement="linear",
)

real_ansatz = real_amplitudes(
    num_qubits=4,
    reps=2,
    entanglement="reverse_linear",
)

qft = QuantumCircuit(4)
qft.append(QFTGate(4), range(4))
```

The old `QFT` blueprint class is deprecated as of Qiskit 2.1 and is scheduled for removal in Qiskit 3.0. Use `QFTGate` or `qiskit.synthesis.qft.synth_qft_full`.

Other current constructors include:

```python
from qiskit.circuit.library import (
    grover_operator,
    n_local,
    pauli_feature_map,
    zz_feature_map,
)
```

Check the current API before using a class copied from an older tutorial; several blueprint classes have function replacements.

## Dynamic Circuits and Classical Control

Qiskit expresses structured real-time control flow with context managers:

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

