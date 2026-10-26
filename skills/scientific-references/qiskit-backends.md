---
id: sciref-qiskit-backends
name: "Scientific Ref: Backends, Runtime Modes, Simulation, and Noise Management"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (qiskit): Backends, Runtime Modes, Simulation, and Noise Management"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "qiskit backends"
  - "backends, runtime modes, simulation, and noise management"
keywords:
  - "qiskit"
  - "backends"
  - "specialized"
  - "scientific"
  - "reference"
  - "runtime"
---

# Backends, Runtime Modes, Simulation, and Noise Management

Cloud authentication, QPU, session, and batch snippets are illustrative and were not executed in this refresh. Local evidence is listed in [sources.md](sources.md).
## BackendV2

Qiskit 2.x providers expose hardware and simulators through `BackendV2`. Important public attributes include:

```python
print(backend.name)
print(backend.num_qubits)
print(backend.operation_names)
print(backend.coupling_map)
print(backend.target)
print(backend.status())
```

The `Target` describes operation support, qubit operands, connectivity, and available timing/error metadata.

Do not use `backend.configuration()`, `BackendProperties`, or other BackendV1 patterns in new code.

## Connect to IBM Quantum

Use a securely saved account:

```python
from qiskit_ibm_runtime import QiskitRuntimeService

service = QiskitRuntimeService()
```

New account configurations use `channel="ibm_quantum_platform"`. See [setup.md](setup.md) for secure credential setup. Never embed or print an API key.

## Discover Backends

Select by requirements, not by a system name copied from a tutorial:

```python
backends = service.backends(
    operational=True,
    simulator=False,
    min_num_qubits=20,
)

for candidate in backends:
    status = candidate.status()
    print(
        candidate.name,
        candidate.num_qubits,
        status.pending_jobs,
    )
```

For exploratory work:

```python
backend = service.least_busy(
    operational=True,
    simulator=False,
    min_num_qubits=20,
)
```

Least busy is not necessarily best. For a production experiment, compare:

- required qubit count,
- connectivity and native two-qubit operations,
- calibration quality on candidate subgraphs,
- control-flow or fractional-gate requirements,
- plan and region,
- queue and expected execution time.

The bundled read-only inspector summarizes one selected backend:

```bash
python scripts/inspect_runtime.py --min-qubits 20
python scripts/inspect_runtime.py --backend BACKEND_NAME --json
```

## Inspect Target Capabilities

```python
target = backend.target

print("operations:", sorted(backend.operation_names))
print("supports if_else:", "if_else" in backend.operation_names)
print("supports reset:", "reset" in backend.operation_names)
print("coupling edges:", list(backend.coupling_map.get_edges()))
```

Operation support can vary by qubit tuple. A name appearing in `operation_names` does not imply every qubit or pair supports it.

## Prepare ISA Circuits

```python
from qiskit.transpiler import generate_preset_pass_manager

pass_manager = generate_preset_pass_manager(
    backend=backend,
    optimization_level=1,
    seed_transpiler=23,
)
isa_circuit = pass_manager.run(circuit)
```

For Estimator:

```python
isa_observable = observable.apply_layout(isa_circuit.layout)
```

Runtime V2 primitives do not perform this conversion automatically.

## Job Mode

Use job mode for independent one-off primitive calls:

```python
from qiskit_ibm_runtime.executor_sampler import Sampler

sampler = Sampler(mode=backend)
job = sampler.run([isa_circuit], shots=1024)

job_id = job.job_id()
print("job_id:", job_id)
result = job.result()
```

Persist the ID before blocking. Retrieve later:

```python
service = QiskitRuntimeService()
job = service.job(job_id)
print(job.status())
result = job.result()
```

Cancel only if the experiment should no longer consume allocation:

```python
job.cancel()
```

## Batch Mode

Batch mode is for independent jobs that can be submitted together. It is available to Open Plan users.

```python
from qiskit_ibm_runtime import Batch
from qiskit_ibm_runtime.executor_sampler import Sampler

with Batch(backend=backend, max_time="10m") as batch:
    sampler = Sampler(mode=batch)
    jobs = [
        sampler.run([isa_circuit], shots=1024)
        for isa_circuit in isa_circuits
    ]

# The batch accepts no new jobs; submitted jobs can still finish.
results = [job.result() for job in jobs]
```

Batch jobs are scheduled as a group, but do not assume an application-level result order beyond the job list you preserve.

## Session Mode

Session mode is for iterative workloads such as VQE parameter updates:

```python
from qiskit_ibm_runtime import Session
from qiskit_ibm_runtime.executor_estimator import Estimator

with Session(backend=backend, max_time="20m") as session:
    estimator = Estimator(mode=session)
    jobs = [
        estimator.run([pub], precision=0.03)
        for pub in iterative_pubs
    ]
```

Open Plan users cannot submit session jobs; use job or batch mode. Sessions have maximum and interactive time-to-live limits. Close them as soon as submission is complete.

Creating `Estimator(mode=backend)` inside a session context still selects job mode. Use `mode=session`.

## Ideal Local Primitives

For small ideal circuits:

```python
from qiskit.primitives import StatevectorEstimator, StatevectorSampler

sampler = StatevectorSampler(seed=23)
estimator = StatevectorEstimator(seed=23)
```

These implementations use local statevector simulation and do not model backend noise. Sampler is finite-shot; zero-precision Estimator is exact only for unitary state preparation.

Memory for a dense statevector grows as \(2^n\). Use an algorithm-appropriate Aer method or tensor-network tooling for larger circuits.

## Aer Simulation

Install the pinned Aer distribution:

```bash
uv pip install "qiskit-aer==0.17.2"
```

Create an ideal Aer backend:

```python
from qiskit_aer import AerSimulator

aer = AerSimulator(method="automatic")
```

Run through Runtime's local-testing primitive interface:

```python
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_sampler import Sampler

pass_manager = generate_preset_pass_manager(
    backend=aer,
    optimization_level=1,
    seed_transpiler=23,
)
isa_circuit = pass_manager.run(circuit)

sampler = Sampler(
    mode=aer,
    options={"simulator": {"seed_simulator": 23}},
)
result = sampler.run([isa_circuit], shots=1024).result()
```

The Runtime 0.50 client-side primitives perform preprocessing and postprocessing locally, including enabled mitigation/twirling paths. This differs from deprecated server-side primitives whose local mode ignored many options. Use `resilience_level=0` for an unmitigated Estimator baseline and inspect finalized options. Local results still do not verify service limits, scheduling, costs, or QPU mitigation effectiveness. `dry_run=True` on a remote backend is a server 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

