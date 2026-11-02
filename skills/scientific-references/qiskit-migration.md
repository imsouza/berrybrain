---
id: sciref-qiskit-migration
name: "Scientific Ref: Migration to Qiskit 2.5 and Runtime 0.50"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (qiskit): Migration to Qiskit 2.5 and Runtime 0.50"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "qiskit migration"
  - "migration to qiskit 2.5 and runtime 0.50"
keywords:
  - "qiskit"
  - "migration"
  - "specialized"
  - "scientific"
  - "reference"
---

# Migration to Qiskit 2.5 and Runtime 0.50

Cloud authentication, QPU, session, and batch snippets are illustrative and were not executed in this refresh. Local evidence is listed in [sources.md](sources.md).
Use this guide when adapting code written for Qiskit 0.x, Qiskit 1.x, or early Qiskit Runtime releases.

## Runtime 0.50 client-side primitives

The top-level `qiskit_ibm_runtime.SamplerV2`/`EstimatorV2` and their aliases are deprecated, not removed. Replace their imports with:

```python
from qiskit_ibm_runtime.executor_sampler import Sampler
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.options_models import SamplerOptions, EstimatorOptions
```

PUBs and result fields remain V2. The new implementations prepare and process Executor workloads locally. Recheck option defaults with `finalize_options().model_dump()`, keep ISA compilation and observable layout mapping, and test local noise-management behavior. Server `dry_run=True` returns mock values and does not establish circuit correctness.

## Start with a Clean Environment

Do not upgrade an environment containing both old `qiskit-terra` and modern `qiskit`.

```bash
uv venv --python 3.13 .venv-qiskit-2
source .venv-qiskit-2/bin/activate
uv pip install \
  "qiskit==2.5.2" \
  "qiskit-ibm-runtime==0.50.0" \
  "qiskit-aer==0.17.2"
```

Run:

```bash
python scripts/check_environment.py --require-runtime --require-aer
```

## High-Level API Map

| Legacy pattern | Qiskit 2.5 pattern |
|---|---|
| Install `qiskit-terra` | Install `qiskit` |
| `from qiskit import Aer` | `from qiskit_aer import AerSimulator` |
| `execute(circuit, backend)` | V2 primitive, or provider-specific backend only when necessary |
| `QuantumInstance` | Primitive implementation plus explicit transpilation |
| `qiskit.opflow` | `qiskit.quantum_info.SparsePauliOp` and primitive PUBs |
| `circuit.bind_parameters(...)` | `circuit.assign_parameters(...)`, or pass values in PUBs |
| V1 `Sampler` / `Estimator` | `StatevectorSampler` / `StatevectorEstimator`, Runtime client-side `Sampler` / `Estimator` (V2 API) |
| Parallel V1 input lists | One or more PUB tuples |
| `result.quasi_dists` | `result[i].data.<register>.get_counts()` |
| `result.values` | `result[i].data.evs` |
| Runtime shared `Options()` | `SamplerOptions`, `EstimatorOptions`, dict, or `.options.update()` |
| Primitive `backend=` / `session=` | Primitive `mode=` |
| Runtime auto-transpilation | Explicit backend-specific ISA circuit |
| Logical observable submitted unchanged | `observable.apply_layout(isa_circuit.layout)` |
| `backend.configuration()` / `.properties()` | BackendV2 direct attributes and `backend.target` |
| `channel="ibm_quantum"` | `channel="ibm_quantum_platform"` |
| `qiskit.pulse` | IBM fractional gates for hardware; isolated legacy simulation for archived Dynamics |
| `QFT(...)` blueprint class | `QFTGate(...)` or `synth_qft_full(...)` |
| Blueprint ansatz classes | Function constructors such as `efficient_su2(...)` |
| `instruction.c_if(...)` | Structured circuit control flow such as `if_test(...)` |

## Migrate V1 Sampler

Legacy shape:

```python
# Legacy; do not use
# sampler = Sampler()
# result = sampler.run(circuits, parameter_values).result()
# quasi_distribution = result.quasi_dists[0]
```

Current local V2:

```python
from qiskit.primitives import StatevectorSampler

sampler = StatevectorSampler(seed=41)
pub_result = sampler.run(
    [(measured_circuit, parameter_values)],
    shots=1024,
).result()[0]

counts = pub_result.data.meas.get_counts(0)
```

Key changes:

- measured shot data replace V1 quasi-distributions,
- output is organized by classical register,
- parameter sweeps retain array shape,
- a PUB contains one circuit and its parameter values.

## Migrate V1 Estimator

Legacy shape:

```python
# Legacy; do not use
# estimator = Estimator()
# result = estimator.run(circuits, observables, values).result()
# expectation_value = result.values[0]
```

Current local V2:

```python
from qiskit.primitives import StatevectorEstimator

estimator = StatevectorEstimator()
pub_result = estimator.run(
    [(circuit, observable, parameter_values)]
).result()[0]

expectation_values = pub_result.data.evs
standard_deviations = pub_result.data.stds
```

## Migrate Runtime Execution

Legacy Runtime:

```python
# Legacy; do not use
# options = Options()
# options.resilience_level = 2
# estimator = Estimator(session=session, options=options)
```

Current Runtime:

```python
from qiskit_ibm_runtime.executor_estimator import Estimator

estimator = Estimator(
    mode=session,
    options={"resilience_level": 2},
)
```

Use current mode syntax:

```python
sampler = Sampler(mode=backend)
sampler = Sampler(mode=batch)
sampler = Sampler(mode=session)
```

The old `backend=` constructor keyword is unsupported. Use `mode=backend` for job mode or `mode=session` / `mode=batch` explicitly.

## Migrate to ISA Circuits

Legacy Runtime examples often submitted logical circuits and relied on service-side transpilation. V2 Runtime requires ISA circuits:

```python
from qiskit.transpiler import generate_preset_pass_manager

pass_manager = generate_preset_pass_manager(
    backend=backend,
    optimization_level=1,
    seed_transpiler=41,
)
isa_circuit = pass_manager.run(logical_circuit)
```

Estimator observables must follow the layout:

```python
isa_observable = logical_observable.apply_layout(
    isa_circuit.layout
)
```

Failing to map observables can silently change the physical qubits being measured or produce a width error.

## Migrate BackendV1 Access

Legacy:

```python
# Legacy; do not use
# basis_gates = backend.configuration().basis_gates
# coupling_map = backend.configuration().coupling_map
# properties = backend.properties()
```

Current:

```python
basis_operations = backend.operation_names
coupling_map = backend.coupling_map
target = backend.target
num_qubits = backend.num_qubits
```

Query gate errors, durations, and qubit support through the `Target` entries. Do not combine a backend with manually copied basis and coupling data unless constructing a deliberately synthetic target.

## Migrate IBM Account Configuration

The IBM Quantum Platform Classic channel is retired.

Current trusted-machine setup:

```python
import os
from qiskit_ibm_runtime import QiskitRuntimeService

QiskitRuntimeService.save_account(
    channel="ibm_quantum_platform",
    token=os.environ["IBM_QUANTUM_API_KEY"],
    instance=os.environ.get("IBM_QUANTUM_INSTANCE"),
 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

