---
id: sciref-pennylane-devices-backends
name: "Scientific Ref: Devices and backend boundaries"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pennylane): Devices and backend boundaries"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pennylane devices backends"
  - "devices and backend boundaries"
keywords:
  - "pennylane"
  - "devices"
  - "backends"
  - "specialized"
  - "scientific"
  - "reference"
  - "backend"
---

# Devices and backend boundaries

PennyLane 0.45.1 is the tested core. Provider integrations below were checked
against official docs/released source, **not authenticated hardware jobs**.
Install each provider/compiler in a separate environment and resolve its declared
requirements; a plugin version number does not guarantee all current backend APIs.

## Local simulators and reusable circuits

```python
import pennylane as qml
from pennylane import numpy as np

def quantum_function(theta):
    qml.RY(theta, wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.Z(1))

results = {}
for name in ["default.qubit", "lightning.qubit", "default.mixed"]:
    dev = qml.device(name, wires=2)
    circuit = qml.QNode(quantum_function, dev, diff_method="parameter-shift")
    theta = np.array(0.3, requires_grad=True)
    results[name] = float(circuit(theta))
    assert np.allclose(results[name], np.cos(theta))
    assert np.allclose(qml.grad(circuit)(theta), -np.sin(theta))
```

`default.mixed` supports explicit channels; changing to it does not automatically
apply a realistic hardware noise model. Lightning speedups depend on circuit size
and overhead. `lightning.gpu` requires its separate CUDA/cuQuantum-compatible
plugin and hardware; no GPU fallback should silently change a reported benchmark.
`default.clifford` needs Stim and accepts only its supported Clifford operations
and measurements (some Pauli rotations at Clifford angles may be supported).
There is no universal fixed qubit limit or provider noise ranking.

Use `dev.name`, `dev.wires` and `len(dev.wires)` when wires are allocated. New
Device API objects do not universally expose legacy `num_wires`, `operations`,
`observables` or `apply`. Some use dynamic wires or optional capabilities objects.
Inspect each device's documented preprocessing and derivative support; run a tiny
representative circuit. For custom devices implement the current execution and
preprocessing protocol, not an obsolete `DefaultQubit.apply` override. A custom
operator can implement `compute_decomposition`; registering an arbitrary attribute
on `qml.ops` is not plugin registration.

## Provider installation targets

These released versions were source/metadata checked on 2026-10-01. Commands are
illustrative dependency setup, not a tested combined environment:

```bash
# Choose one provider per environment.
uv pip install "pennylane==0.45.1" "pennylane-qiskit==0.45.0"
uv pip install "pennylane==0.45.1" "amazon-braket-pennylane-plugin==1.35.2"
uv pip install "pennylane==0.45.1" "pennylane-cirq==0.44.0"
uv pip install "pennylane==0.45.1" "pennylane-ionq==0.45.0"
```

Rigetti's last published plugin is 0.40.0, with `pyquil<4` and `networkx<3`;
resolve and validate it in its own legacy stack instead of installing it into the
current core/ML environment. Current QCS hardware availability requires provider
verification. Strawberry Fields' plugin documentation targets 0.29.1; an old
`strawberryfields.remote`/Borealis recipe is not evidence of compatibility or a
currently accessible backend with PennyLane 0.45.1.

## IBM Quantum: backend object and finite shots

`qiskit.aer` is a local simulator plugin. `qiskit.remote` accepts a Qiskit backend
object and uses EstimatorV2/SamplerV2. Allocate only the logical wires needed,
within backend capacity. Its execution is sampled; do not promise analytic results.

Illustrative authenticated setup, not executed:

```python
import os
import pennylane as qml
from qiskit_ibm_runtime import QiskitRuntimeService

service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token=os.environ["IBM_QUANTUM_API_KEY"],
    instance=os.environ["IBM_QUANTUM_INSTANCE"],
)
backend = service.least_busy(operational=True, simulator=False, min_num_qubits=2)
dev = qml.device("qiskit.remote", wires=2, backend=backend)
@qml.set_shots(1024)
@qml.qnode(dev, diff_method="parameter-shift")
def hardware_circuit(theta):
    qml.RY(theta, wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.expval(qml.Z(1))
# Calling hardware_circuit submits work; record backend, calibration, shots and job metadata.
```

The environment variable names here are application-defined inputs, not automatic
SDK credential discovery. Saved credentials are another option:
`QiskitRuntimeService.save_account(...)` saves configuration; then construct
`QiskitRuntimeService()` separately. Do not assign `save_account`'s return value as
the service. The SDK resolves the IBM platform URL and handles authentication;
this skill does not implement a parallel REST client. Source docs and released
plugin source differ on the behavior of unspecified shots, so set an explicit
finite integer. Shot vectors are not supported by this plugin release.

## Amazon Braket

The plugin provides `braket.local.qubit` for local execution and
`braket.aws.qubit` for cloud tasks. Cloud construction uses `device_arn`, `wires`
and optional `s3_destination_folder=(bucket, prefix)`; use a bucket the account
owns/accesses. AWS SDK credentials and correct region are required for cloud use.
Discover the currently available device ARN with the Braket console/SDK and check
status, supported operations, shots and result types before selecting it. Do not
copy a historical Harmony ARN or an example bucket name into a live request.
The documented SV1 ARN is `arn:aws:braket:::device/quantum-simulator/amazon/sv1`;
a cloud simulator can still incur cost. No Braket task was submitted here.

## Cirq, Rigetti and photonics

The Cirq 0.44.0 plugin registers `cirq.simulator`, `cirq.mixedsimulator`,
`cirq.qsim`, `cirq.qsimh` and `cirq.pasqal`. qsim requires its optional native
package. **`cirq.pasqal` describes Pasqal neutral-atom devices, not Google's
Rainbow hardware.** Google Quantum Engine access needs an appropriate current
provider integration and access; do not infer it from installing the Cirq plugin.

Rigetti's legacy entry points include `rigetti.qvm`, `rigetti.qpu` and wavefunction
simulators. A QVM needs its runtime/services; a QPU needs current QCS credentials
and a currently accessible processor. Do not hardcode retired Aspen targets or
assume a QPU's number of qubits from an old example. Photonic workflows use different
state spaces/operations; confirm the dedicated plugin/runtime instead of swapping
a qubit QNode's device string to Borealis.

## IonQ: explicit current backend target

The released `pennylane-ionq==0.45.0` package registers `ionq.simulator` and
`ionq.qpu`. It reads an explicit `api_key`, t

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

