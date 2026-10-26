---
id: sciref-qiskit-transpilation
name: "Scientific Ref: Target-Aware Transpilation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (qiskit): Target-Aware Transpilation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "qiskit transpilation"
  - "target-aware transpilation"
keywords:
  - "qiskit"
  - "transpilation"
  - "specialized"
  - "scientific"
  - "reference"
  - "target"
  - "aware"
---

# Target-Aware Transpilation

Transpilation rewrites an abstract circuit into an **instruction set architecture (ISA) circuit** that satisfies a specific backend `Target`:

- only supported instructions,
- valid qubit operands and connectivity,
- backend timing and control-flow constraints,
- an explicit virtual-to-physical qubit layout.

IBM Runtime V2 primitives require ISA circuits. They do not perform layout, routing, and basis translation automatically.

## Recommended Entry Point

Use a preset staged pass manager:

```python
from qiskit.transpiler import generate_preset_pass_manager

pass_manager = generate_preset_pass_manager(
    backend=backend,
    optimization_level=1,
    seed_transpiler=17,
)
isa_circuit = pass_manager.run(circuit)
```

The pass manager can be reused for circuits targeting the same backend snapshot:

```python
isa_circuits = pass_manager.run(circuits)
```

`qiskit.transpile()` remains a convenient wrapper, but a pass manager is easier to reuse, inspect, and customize.

## The BackendV2 Target

`backend.target` is the source of supported operations and constraints:

```python
print("backend:", backend.name)
print("qubits:", backend.num_qubits)
print("operations:", sorted(backend.operation_names))
print("coupling map:", backend.coupling_map)
print("target:", backend.target)
```

Do not use these removed or legacy BackendV1 access patterns:

```python
# Do not use in Qiskit 2.x code:
# backend.configuration().basis_gates
# backend.properties()
# BackendProperties
```

For a synthetic target:

```python
from qiskit.transpiler import CouplingMap, Target

target = Target.from_configuration(
    basis_gates=["cz", "sx", "rz"],
    coupling_map=CouplingMap.from_line(5),
)
pass_manager = generate_preset_pass_manager(
    target=target,
    optimization_level=1,
    seed_transpiler=17,
)
isa_circuit = pass_manager.run(circuit)
```

Prefer one coherent `backend` or `target`. Combining a backend with separate `basis_gates` or `coupling_map` inputs creates competing sources of truth and is discouraged.

## Preset Optimization Levels

| Level | Typical intent |
|---:|---|
| 0 | Minimal transformation needed to satisfy the target |
| 1 | Light optimization with relatively low compilation cost |
| 2 | More optimization and search |
| 3 | Heavier optimization and search; highest classical cost |

Higher does not guarantee a better experimental result. Compare levels using the same circuit, target snapshot, and seed:

```python
compiled = {}
for level in (0, 1, 2, 3):
    manager = generate_preset_pass_manager(
        backend=backend,
        optimization_level=level,
        seed_transpiler=17,
    )
    compiled[level] = manager.run(circuit)
```

Start with levels 1 and 3 for a bounded comparison. Evaluate target-native two-qubit operations, depth, estimated duration when available, and downstream result quality.

## Transpiler Stages

A preset `StagedPassManager` has six conceptual stages:

1. **init**: validate and synthesize high-level operations.
2. **layout**: map virtual qubits to physical qubits.
3. **routing**: add routing operations to satisfy connectivity.
4. **translation**: convert to target-supported instructions.
5. **optimization**: simplify and resynthesize the target circuit.
6. **scheduling**: apply hardware-aware timing passes when configured.

Qiskit 2.x scheduling does not restore `qiskit.pulse`; that module was removed.

Inspect the generated manager:

```python
print(pass_manager)
print(pass_manager.property_set)
```

The property set is primarily a pass-development and debugging interface; do not build long-term application logic around undocumented keys.

## Layouts and Observables

Transpilation can permute logical qubits. Estimator observables must be mapped to the final physical layout:

```python
from qiskit.quantum_info import SparsePauliOp

observable = SparsePauliOp.from_list([("ZZ", 1.0)])
isa_circuit = pass_manager.run(circuit)
isa_observable = observable.apply_layout(isa_circuit.layout)
```

Submit the mapped observable:

```python
pub = (isa_circuit, isa_observable, parameter_values)
```

Do not manually guess the permutation from a circuit drawing. Use `isa_circuit.layout`.

For a list of observables:

```python
isa_observables = [
    observable.apply_layout(isa_circuit.layout)
    for observable in observables
]
```

## Parameterized Workloads

Transpile the parameterized circuit once:

```python
parameterized_isa = pass_manager.run(parameterized_circuit)
isa_observable = observable.apply_layout(parameterized_isa.layout)

for values in optimizer_values:
    pub = (parameterized_isa, isa_observable, [values])
    result = estimator.run([pub], precision=0.03).result()[0]
```

This avoids repeated layout and routing. Retranspile only when the circuit structure, target, selected backend feature set, or compilation strategy changes.

## Initial Layouts

Use an explicit layout only when calibration analysis or a reproducibility requirement justifies it:

```python
pass_manager = generate_preset_pass_manager(
    backend=backend,
    optimization_level=2,
    initial_layout=[3, 5, 8],
    seed_transpiler=17,
)
```

An explicit layout bypasses the preset layout-selection logic. Confirm every physical qubit and interaction is supported by the target.

## Approximate Synthesis

`approximation_degree` trades unitary fidelity for potentially cheaper circuits:

```python
pass_manager = generate_preset_pass_manager(
    backend=backend,
    optimization_level=3,
    approximation_degree=0.99,
    seed_transpiler=17,
)
```

Treat approximation as an experimental parameter. Compare ideal-unitary error, native two-qubit count, and hardware outcome. Do not describe `0.99` as a universal one-percent error bound for the whole algorithm.

## Reproducibility

Set the transpiler seed explicitly:

```python
pass_manager = generate_preset_pass_manager(
    backend=backend,
    optimization_level=3,
    seed_transpiler=17,
)
```

Qiskit 2.5 also supports `QISKIT_TRANSPILER_SEED`, but an explicit argument is clearer in reproducible code.

Record:

- Qiskit version,
- backend name and target/calibration timestamp if available,
- optimization level,
- seed,
- all non-default pass-manager arguments,
- input and output QPY artifacts,
- output layout and structural metrics.

A fixed seed stabilizes stochastic compiler choices; it does not freeze changing backend calibration data or package behavior across releases.

## Analyze Compiled Circuits

```python


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

