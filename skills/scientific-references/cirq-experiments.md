---
id: sciref-cirq-experiments
name: "Scientific Ref: Running quantum experiments"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (cirq): Running quantum experiments"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "cirq experiments"
  - "running quantum experiments"
keywords:
  - "cirq"
  - "experiments"
  - "specialized"
  - "scientific"
  - "reference"
  - "running"
  - "quantum"
---

# Running quantum experiments

These examples target Cirq 1.7.0 and small local circuits. Keep circuit generation,
execution, and analysis separate. Record the question, observable, units, qubit
order, seed, shot count, package version, parameters, and calibration provenance
before interpreting an optimizer or benchmark result.

## Sweeps and reproducible data collection

```python
import cirq
import numpy as np
import sympy
import scipy.optimize
import networkx as nx

q0, q1 = qubits = list(cirq.LineQubit.range(2))
theta, phi = sympy.symbols("theta phi")
circuit = cirq.Circuit(
    cirq.ry(theta)(q0), cirq.rx(phi)(q1), cirq.CNOT(q0, q1),
    cirq.measure(*qubits, key="result"),
)
sweep = cirq.Product(cirq.Linspace("theta", 0, np.pi, 3),
                     cirq.Linspace("phi", 0, np.pi, 3))
sampler = cirq.Simulator(seed=42)
results = sampler.run_sweep(circuit, params=sweep, repetitions=100)
# Cirq JSON preserves result measurement arrays and ParamResolvers.
archive = cirq.to_json({"circuit": circuit, "results": results,
                        "qubit_order": qubits, "cirq_version": cirq.__version__})
restored = cirq.read_json(json_text=archive)
assert len(restored["results"]) == 9
```

Write the archive to a chosen output path after the experiment; retain raw data
alongside summaries. CSV cells containing a printed Counter are not a robust
lossless result format. For shot estimates include binomial/multinomial sampling
uncertainty and independent repeats when drift or optimizer noise matters.

## VQE with explicit observable ordering

A local state-vector expectation is exact up to numerical precision and does not
include finite-shot or hardware error. This is a **toy Pauli Hamiltonian**, not
an H2 electronic-structure calculation or a UCC chemistry ansatz.

```python
def toy_ansatz(params, qubits):
    return cirq.Circuit(cirq.ry(params[0])(qubits[0]),
                        cirq.ry(params[1])(qubits[1]),
                        cirq.CNOT(qubits[0], qubits[1]))

def vqe_experiment(hamiltonian, ansatz_func, initial_params, qubit_order):
    simulator = cirq.Simulator(dtype=np.complex128)
    history = []
    def objective(params):
        preparation = ansatz_func(params)
        if preparation.has_measurements():
            raise ValueError("VQE expectation requires a measurement-free ansatz")
        energy = simulator.simulate_expectation_values(
            preparation, observables=[hamiltonian], qubit_order=qubit_order
        )[0]
        energy = float(np.real(energy))
        history.append({"params": np.array(params, copy=True), "energy": energy})
        return energy
    optimum = scipy.optimize.minimize(
        objective, initial_params, method="COBYLA", options={"maxiter": 100}
    )
    return optimum, history

hamiltonian = cirq.Z(q0) + cirq.Z(q1) + cirq.Z(q0)*cirq.Z(q1)
optimum, history = vqe_experiment(
    hamiltonian, lambda params: toy_ansatz(params, qubits), [0.2, 0.3], qubits
)
exact_ground = np.linalg.eigvalsh(hamiltonian.matrix(qubits=qubits)).min()
assert optimum.fun >= exact_ground - 1e-8
print(optimum.fun, optimum.success, optimum.message)
```

Use the optimizer's `x` and `fun`, not the last history entry, as its returned
optimum. Inspect convergence and multiple starts. For a manually evaluated
`expectation_from_state_vector`, construct `qubit_map` from exactly the
`qubit_order` passed to simulation; `circuit.all_qubits()` is a set. The variational
bound only holds for a valid state and the intended Hamiltonian, not arbitrary
mitigated estimates or an incorrect qubit map.

## QAOA for unweighted MaxCut

Use `C = sum_edges (I-Z_i Z_j)/2` and the convention
`exp(-i gamma C)` followed by `exp(-i beta sum X)`, with angles in **radians**.
Cirq's `ZZPowGate` exponent is a half-turn parameter, so its exponent here is
`-gamma/pi` (up to global phase). Record this sign/unit convention with results.

```python
def qaoa_circuit(graph, params, p_layers, *, measure=True):
    if graph.is_directed() or graph.is_multigraph() or nx.number_of_selfloops(graph):
        raise ValueError("Expected a simple undirected graph without self-loops")
    if p_layers < 1 or len(params) != 2*p_layers:
        raise ValueError("Expected gamma then beta for each layer")
    nodes = list(graph.nodes())
    qubits = list(cirq.LineQubit.range(len(nodes)))
    node_qubit = dict(zip(nodes, qubits))
    circuit = cirq.Circuit(cirq.H.on_each(*qubits))
    for layer in range(p_layers):
        gamma, beta = params[layer], params[p_layers+layer]
        circuit.append(cirq.ZZPowGate(exponent=-gamma/np.pi)(node_qubit[u], node_qubit[v])
                       for u, v in graph.edges())
        circuit.append(cirq.rx(2*beta).on_each(*qubits))
    if measure:
        circuit.append(cirq.measure(*qubits, key="result"))
    return circuit, nodes, qubits

def mean_maxcut(result, graph, nodes):
    columns = {node: i for i, node in enumerate(nodes)}
    bits = result.measurements["result"]
    if bits.shape[1] != len(nodes) or len(bits) == 0:
        raise ValueError("Measurement dimensions do not match the graph")
    cut_per_shot = np.zeros(len(bits))
    for u, v in graph.edges():
        cut_per_shot += bits[:, columns[u]] != bits[:, columns[v]]
    return float(np.mean(cut_per_shot))

graph = nx.Graph([("left", "center"), ("center", "right")])
qaoa, nodes, order = qaoa_circuit(graph, [0.4, 0.2], p_layers=1)
qaoa_result = cirq.Simulator(seed=42).run(qaoa, repetitions=1000)
cut = mean_maxcut(qaoa_result, graph, nodes)
assert 0 <= cut <= graph.number_of_edges()
```

Raw measurement columns avoid accidentally reversing big-endian histogram bits.
Node labels need not be consecutive integers. The example treats every edge as
weight 1; implement both weighted cost evolution and weighted scoring if weights
are scientifically relevant. For optimization minimize `-mean_maxcut(...)` and
validate the chosen parameters on independent shots. A noisy optimizer result
alone does not establish superiority over a classical baseline.

## Quantum phase estimation

This example accepts a one-qubit unitary gate and a one-qubit eigenstate
preparation. Counting qubits are ordered most-significant first; the measured
integer k estimates the eigenphase as `k / 2**n` for eigenvalue `exp(2*pi*i*phase)`.

```python
def qpe_circuit(unitary, eigenstate_prep, n_counting_qubits):
    if n_counting_qubits < 1 or cirq.num_qubits(unitary) != 1 or not cirq.has_unitary(unitary):
        raise ValueError("Expected a one-qubit

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

