---
id: sciref-qiskit-testing
name: "Scientific Ref: Testing, Reproducibility, and Troubleshooting"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (qiskit): Testing, Reproducibility, and Troubleshooting"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "qiskit testing"
  - "testing, reproducibility, and troubleshooting"
keywords:
  - "qiskit"
  - "testing"
  - "specialized"
  - "scientific"
  - "reference"
  - "reproducibility"
---

# Testing, Reproducibility, and Troubleshooting

Quantum workflows combine deterministic program transformations, stochastic sampling, changing hardware, and classical post-processing. Test each layer separately.

## Testing Pyramid

1. **Pure classical tests**: bit ordering, objective functions, post-processing.
2. **Circuit semantic tests**: small statevectors, operators, and measurement bases.
3. **Primitive contract tests**: PUB shapes, result registers, metadata handling.
4. **Transpilation tests**: target compatibility, layout propagation, structural budgets.
5. **Noisy simulation tests**: robustness under a recorded model.
6. **Bounded hardware smoke tests**: smallest useful QPU job.

Do not use QPU jobs as unit tests.

## Run the Bundled Smoke Test

```bash
python scripts/check_environment.py
python scripts/run_local_primitives.py --shots 256 --seed 43
```

Machine-readable output:

```bash
python scripts/check_environment.py --json
python scripts/run_local_primitives.py --json
```

## Deterministic Seeds

Use separate explicit seeds:

```python
seed_transpiler = 43
seed_simulator = 44

pass_manager = generate_preset_pass_manager(
    backend=backend,
    optimization_level=1,
    seed_transpiler=seed_transpiler,
)

sampler = StatevectorSampler(seed=seed_simulator)
```

Record both. A simulator seed does not make real hardware deterministic. A transpiler seed does not freeze calibration changes or behavior across package versions.

## Test Circuit Semantics

For small unitary circuits:

```python
from qiskit.quantum_info import Operator, Statevector

reference_state = Statevector.from_instruction(reference_circuit)
candidate_state = Statevector.from_instruction(candidate_circuit)
assert reference_state.equiv(candidate_state)

reference_operator = Operator(reference_circuit)
candidate_operator = Operator(candidate_circuit)
assert reference_operator.equiv(candidate_operator)
```

`equiv()` accounts for global phase. Only construct dense operators for small circuits; memory grows as \(4^n\).

Remove final measurements before statevector comparison:

```python
unitary_part = measured_circuit.remove_final_measurements(
    inplace=False
)
```

Circuits with resets, measurements, or classical control need behavior-specific tests rather than unitary equivalence.

## Test Bit Ordering Explicitly

```python
def qiskit_bitstring_to_values(bitstring):
    return [
        int(bit)
        for bit in reversed(bitstring.replace(" ", ""))
    ]

assert qiskit_bitstring_to_values("10") == [0, 1]
```

Also test Pauli-label mapping:

```python
from qiskit.quantum_info import SparsePauliOp

operator = SparsePauliOp.from_list([("ZI", 1.0)])
assert operator.num_qubits == 2
# "ZI" means Z on qubit 1 and I on qubit 0.
```

This is especially important for optimization variables and graph vertices. The reversal above decodes classical bits; qubit interpretation additionally requires the measurement map. Use asymmetric states and reversed measurement operands, plus unequal named registers, to detect errors that Bell/GHZ symmetry hides.

## Test Parameter Order and Shapes

```python
parameter_order = list(circuit.parameters)
assert parameter_values.shape[-1] == len(parameter_order)

stored_names = [parameter.name for parameter in parameter_order]
assert stored_names == expected_parameter_names
```

For every nontrivial PUB broadcast, assert the result shape:

```python
pub_result = estimator.run(
    [(circuit, observables, parameter_values)]
).result()[0]

assert pub_result.data.evs.shape == expected_shape
```

Do not rely on a visual reading of nested lists.

## Test Sampled Results Statistically

Never assert an exact count split from finite shots:

```python
counts = pub_result.data.meas.get_counts()
shots = sum(counts.values())

p_zero = counts.get("0", 0) / shots
assert abs(p_zero - 0.5) < 0.1
```

Choose tolerance from the expected binomial uncertainty and desired failure probability, not an arbitrary constant copied into every test.

For exact probability assertions, use `Statevector.probabilities_dict()` on a small unitary circuit:

```python
from qiskit.quantum_info import Statevector

probabilities = Statevector.from_instruction(
    unitary_circuit
).probabilities_dict()
```

## Test Estimator Values

```python
import numpy as np

actual = np.asarray(pub_result.data.evs)
np.testing.assert_allclose(
    actual,
    expected,
    rtol=1e-10,
    atol=1e-12,
)
```

Use tight tolerances only for exact local simulation. For noisy or hardware estimates, use a statistical test and report uncertainty.

## Test Transpilation

Check invariants, not a full textual snapshot:

```python
isa_circuit = pass_manager.run(circuit)

assert isa_circuit.num_qubits <= backend.num_qubits
assert isa_circuit.layout is not None
target_operations = set(backend.operation_names)
circuit_operations = set(isa_circuit.count_ops()) - {
    "barrier",
}
assert circuit_operations.issubset(
    target_operations
)
```

Control-flow and directive names may require target-aware handling; use target APIs for rigorous compatibility checks.

Track bounded structural regressions:

```python
def two_qubit_instruction_count(circuit):
    return sum(
        len(item.qubits) == 2
        for item in circuit.data
    )

assert isa_circuit.depth() <= depth_budget
assert (
    two_qubit_instruction_count(isa_circuit)
    <= two_qubit_budget
)
```

Compiler improvements can legitimately change exact circuit text and layout. Snapshot stable application metrics and broad budgets instead.

## Test Observable Layout

```python
isa_observable = observable.apply_layout(
    isa_circuit.layout
)
assert isa_observable.num_qubits == isa_circuit.num_qubits
```

For a small target, compare the logical expectation value and the compiled/mapped expectation value using a local Estimator.

Never submit a logical observable with a physically laid-out circuit.

## QPY Round-Trip Test

```python
from io import BytesIO
from qiskit import qpy

buffer = BytesIO()
qpy.dump(circuit, buffer)
buffer.seek(0)
loaded = qpy.load(buffer)[0]

assert loaded == circuit
```

Also test required metadata and parameter names. Newer Qiskit normally loads QPY written by older versions; older Qiskit is not expected to load newer QPY.

Do not use pickle as a fallback for untrusted data.

## Runtime Code Without QPU Jobs

Use:

- fake backends for `Target` and compilation tests,
- Aer for ideal/noisy execution,
- Runtime primitives in local-testing mode,
- `scripts/inspec

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

