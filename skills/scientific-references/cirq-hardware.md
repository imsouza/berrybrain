---
id: sciref-cirq-hardware
name: "Scientific Ref: Hardware integration"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (cirq): Hardware integration"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "cirq hardware"
  - "hardware integration"
keywords:
  - "cirq"
  - "hardware"
  - "specialized"
  - "scientific"
  - "reference"
  - "integration"
---

# Hardware integration

Reviewed against Cirq 1.7.0 and current provider documentation on 2026-09-30.
Cloud snippets are **illustrative, not authenticated end-to-end tests**. They may
submit chargeable work, including remote simulators. Use a specifically selected
provider, assigned target, and shot budget. Local validation is demonstrated
separately and does not establish credentials or hardware availability.

## Device preparation and calibration

A `cirq.Circuit` does not accept `device=`. Choose physical qubits, compile to the
advertised target gateset, then validate. Sorted adjacent entries in a qubit list
need not be physically connected. This helper uses one actual device edge:

```python
import cirq
import cirq_google as cg
import numpy as np
import networkx as nx

def prepare_google_bell(device):
    a, b = next(iter(device.metadata.nx_graph.edges))
    circuit = cirq.Circuit(
        cirq.H(a), cirq.CNOT(a, b), cirq.measure(a, b, key="result")
    )
    target = device.metadata.compilation_target_gatesets[0]
    compiled = cirq.optimize_for_target_gateset(circuit, gateset=target)
    device.validate_circuit(compiled)
    return compiled

# Local topology/compiler check, no remote execution.
local_device = cg.engine.create_device_from_processor_id("willow_pink")
local_circuit = prepare_google_bell(local_device)
local_result = cirq.Simulator(seed=42).run(local_circuit, repetitions=100)
```

For larger logical circuits, use `cirq.RouteCQC(device.metadata.nx_graph)` and
preserve the returned initial and final permutations before compiling. See
[transformation.md](transformation.md). A connected set is not necessarily a path
or a grid; route to its actual induced graph.

```python
def select_connected_qubits(device, n_qubits):
    if n_qubits < 1:
        raise ValueError("Expected a positive qubit count")
    graph = device.metadata.nx_graph.to_undirected()
    for component in nx.connected_components(graph):
        if len(component) >= n_qubits:
            # A BFS prefix is connected, unlike an arbitrary node-list slice.
            root = min(component)
            return list(nx.bfs_tree(graph.subgraph(component), root))[:n_qubits]
    raise ValueError("No sufficiently large connected component")

def single_qubit_errors(calibration, metric="single_qubit_rb_average_error_per_gate"):
    if metric not in calibration:
        raise KeyError(f"Missing calibration metric: {metric}")
    # Metric -> {(qubit,): [value]}, not qubit -> metric -> value.
    return {qs[0]: float(values[0]) for qs, values in calibration[metric].items()
            if len(qs) == 1 and len(values) == 1 and np.isfinite(values[0])}
```

Use real available metric names and units. Lowest single-qubit error alone does
not select a good connected subgraph; include two-qubit errors and readout, and
record calibration timestamp. Missing metrics are missing data, not zero error.

## Google Quantum Engine

Requires a project and user approved for Quantum Computing Service, the
`quantum.googleapis.com` API enabled, appropriate IAM roles, and Application
Default Credentials. This uses Google's generated Quantum Engine client and
its resource names, not hand-built REST paths.

```bash
gcloud auth application-default login
# Set GOOGLE_CLOUD_PROJECT and GOOGLE_QUANTUM_PROCESSOR to assigned values.
```

Illustrative authenticated workflow:

```python
import os
import cirq_google as cg

engine = cg.Engine(project_id=os.environ["GOOGLE_CLOUD_PROJECT"])
print([p.processor_id for p in engine.list_processors()])
processor_id = os.environ["GOOGLE_QUANTUM_PROCESSOR"]
processor = engine.get_processor(processor_id)
device = processor.get_device()
circuit = prepare_google_bell(device)
sampler = engine.get_sampler(processor_id=processor_id)
# Submission; requires approved access and an intentional shot budget.
result = sampler.run(circuit, repetitions=100)
```

Do not default to `weber`, `willow`, or a bundled QVM processor name for cloud
submission. For an offline hardware-like workflow use the
[QVM example](simulation.md). Engine processor/program/job objects have distinct
interfaces; use provider job objects if you need durable job IDs and resumption,
not the generic `Sampler.run` result as if it were a job.

## IonQ API v0.4

`cirq-ionq==1.7.0` defaults to `https://api.ionq.co/v0.4` and reads `IONQ_API_KEY`.
The SDK sends `Authorization: apiKey ...`; do not substitute Bearer auth. A
configured `IONQ_REMOTE_HOST` overrides the default, so confirm its intended
host without printing credentials.

Illustrative submission:

```python
import os
import cirq_ionq as ionq

q0, q1 = cirq.LineQubit.range(2)
circuit = cirq.Circuit(cirq.H(q0), cirq.CNOT(q0, q1), cirq.measure(q0, q1, key="result"))
service = ionq.Service(api_version="v0.4")
# Set an available concrete backend from the IonQ console/API; "simulator" is remote.
target = os.environ["IONQ_TARGET"]
job = service.create_job(circuit, repetitions=100, target=target)
print(job.job_id(), job.status())
provider_result = job.results(timeout_seconds=300, polling_seconds=2)
result = provider_result.to_cirq_result()  # single-circuit job
```

Use `service.run(circuit, repetitions=100, target=target)` when only a Cirq result
is needed. The SDK's `target` argument becomes v0.4 `backend` in `POST /jobs`;
`repetitions` becomes `shots`, and the payload includes `type`, `input`, and
measurement metadata. `Job.results` polls `GET /jobs/{id}` and downloads
`/jobs/{id}/results/probabilities` (aggregated route for batch jobs). Simulator
probabilities may be sampled locally by the adapter; record this when interpreting
returned counts. `wait_until_complete()` is not a Cirq IonQ Job method.

Current v0.4 provider docs use `GET /backends` and backend-specific
`/backends/{backend}/characterizations/{characterization}`. The released
`Service.get_current_calibration()` still requests `/calibrations/current`, a
legacy path not listed in the current v0.4 contract. **Do not rely on that helper**
for current characterization; use the provider's documented backend/characterization
workflow. A successful SDK import does not verify that legacy endpoint. Discover
actual backend IDs rather than assuming the generic `qpu` alias is available.

The job list (`GET /jobs`) paginates using `limit` and a `next` cursor; stop when
response `next` is null. Do not apply job pagination assumptions to `/backends`. This guide submits a selected backend and does not implement custom
list pagination or assume an SDK help

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

