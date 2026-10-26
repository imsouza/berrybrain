---
id: sciref-qiskit-setup
name: "Scientific Ref: Setup, Versions, and Authentication"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (qiskit): Setup, Versions, and Authentication"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "qiskit setup"
  - "setup, versions, and authentication"
keywords:
  - "qiskit"
  - "setup"
  - "specialized"
  - "scientific"
  - "reference"
  - "versions"
---

# Setup, Versions, and Authentication

## Reviewed Version Baseline

Checked against PyPI and official release notes on **2026-10-01**:

| Distribution | Reviewed version | Purpose | Python requirement |
|---|---:|---|---|
| `qiskit` | 2.5.2 | Core circuits, operators, transpiler, local statevector primitives | Python 3.10+ |
| `qiskit-ibm-runtime` | 0.50.0 | IBM Quantum Platform service and Runtime primitives | Python 3.10+ |
| `qiskit-aer` | 0.17.2 | High-performance and noisy simulation | See its PyPI metadata |
| `qiskit-algorithms` | 0.4.0 | VQE, QAOA, Grover, phase estimation, optimizers | Python 3.9+ |
| `qiskit-nature` | 0.8.0 | Quantum chemistry and second-quantized problems | Python 3.10+ |
| `qiskit-nature-pyscf` | 0.4.0 | PySCF integration for Qiskit Nature | Python 3.8+ |
| `qiskit-machine-learning` | 0.9.1 | Quantum kernels, QNNs, Torch integration | Python 3.10+ |
| `qiskit-optimization` | 0.7.0 | Quadratic programs and quantum optimizers | Python 3.9+ |

Local core, Runtime/Aer, Algorithms, Optimization, and visualization checks used these releases. Nature, Machine Learning, and addons were checked against official documentation and release metadata; their workflows below are illustrative and were not executed in this refresh.

## Create an Environment

The repository recommends Python 3.13. Qiskit 2.5 supports CPython 3.10 and newer on supported 64-bit platforms.

```bash
uv venv --python 3.13
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
uv venv --python 3.13
.venv\Scripts\Activate.ps1
```

Install the smallest useful set:

```bash
# Core SDK
uv pip install "qiskit==2.5.2"

# Core plus Matplotlib/LaTeX visualization dependencies
uv pip install "qiskit[visualization]==2.5.2"

# IBM QPUs and Runtime primitives
uv pip install "qiskit-ibm-runtime==0.50.0"

# High-performance and noisy simulation
uv pip install "qiskit-aer==0.17.2"
```

For a project, declare the same exact pins with `uv add`:

```bash
uv add "qiskit[visualization]==2.5.2"
uv add "qiskit-ibm-runtime==0.50.0"
uv add "qiskit-aer==0.17.2"
```

Do not install `qiskit-terra`. Since Qiskit 1.0, the `qiskit` distribution owns the complete `qiskit` package namespace. Aer and application packages remain separate distributions.

## Optional Application Packages

Install these only for the corresponding workflow:

```bash
uv pip install "qiskit-algorithms==0.4.0"
uv pip install "qiskit-nature[pyscf]==0.8.0"
# Optional reverse integration: PySCF calls a Qiskit Nature solver
uv pip install "qiskit-nature-pyscf==0.4.0"
uv pip install "qiskit-machine-learning==0.9.1"
uv pip install "qiskit-optimization==0.7.0"
```

Resolve all selected packages together in a fresh environment. Do not force-install incompatible distributions with dependency checks disabled.

## Verify the Environment

Use the bundled checker:

```bash
python scripts/check_environment.py
python scripts/check_environment.py --require-runtime --require-aer
python scripts/check_environment.py --json
```

Or inspect versions directly:

```python
from importlib.metadata import version

for distribution in ("qiskit", "qiskit-ibm-runtime", "qiskit-aer"):
    try:
        print(distribution, version(distribution))
    except Exception:
        print(distribution, "not installed")
```

Run the local smoke test before configuring cloud access:

```bash
python scripts/run_local_primitives.py --shots 256 --seed 7
```

## IBM Quantum Platform Setup

IBM QPU access requires:

1. An IBM Cloud account.
2. An IBM Quantum Platform instance or access to an organization's instance.
3. An IBM Cloud API key.
4. `qiskit-ibm-runtime`.

Use the current channel name, `ibm_quantum_platform`. The old `ibm_quantum` channel is no longer supported. `ibm_cloud` currently reaches the upgraded platform but is a legacy alias; use `ibm_quantum_platform` in new code.

Create and manage API keys through the [IBM Cloud API keys page](https://cloud.ibm.com/iam/apikeys). Find instance names and Cloud Resource Names (CRNs) on the [IBM Quantum Platform Instances page](https://quantum.cloud.ibm.com/instances).

### Trusted Workstation: Save an Account

Put only the named values into the process environment. Never hardcode, print, log, or commit an API key.

```bash
export IBM_QUANTUM_API_KEY="set-this-outside-source-control"
# Optional: restrict access to one instance
export IBM_QUANTUM_INSTANCE="instance-name-or-crn"
```

Then save the account from a trusted machine:

```python
import os
from qiskit_ibm_runtime import QiskitRuntimeService

api_key = os.environ["IBM_QUANTUM_API_KEY"]
instance = os.environ.get("IBM_QUANTUM_INSTANCE")

QiskitRuntimeService.save_account(
    channel="ibm_quantum_platform",
    token=api_key,
    instance=instance,
    name="default-platform",
    set_as_default=True,
    overwrite=True,
)
```

The SDK stores saved credentials in `$HOME/.qiskit/qiskit-ibm.json`. Do not manually edit, print, upload, or commit this file. Restrict local file access to the current user.

Load saved credentials without putting a token in source:

```python
from qiskit_ibm_runtime import QiskitRuntimeService

service = QiskitRuntimeService(name="default-platform")
```

If only one default account exists, `QiskitRuntimeService()` is sufficient. Pin the intended instance CRN for reproducible hardware work: selecting across instances can change the active billing allocation. `instance="auto"` explicitly opts into automatic selection; `plans_preference=["open"]` can restrict automatic discovery to Open Plan. The public alias `IBMQuantumComputeService` is also available since Runtime 0.49.

`channel="local"` creates a local service without cloud credentials. Never infer cloud access from a successful local service test.

### CI or Ephemeral Machine: Do Not Persist

Inject the two named secrets through the CI secret store and instantiate the service directly:

```python
import os
from qiskit_ibm_runtime import QiskitRuntimeService

service = QiskitRuntimeService(
    channel="ibm_quantum_platform",
    token=os.environ["IBM_QUANTUM_API_KEY"],
    instance=os.environ["IBM_QUANTUM_INSTANCE"],
)
```

Do not call `save_account()` on a shared runner. Do not dump the environment, the service account object, or exception payloads that may contain request details.

If an API key is exposed, revoke it immediately in IBM Cloud and replace it everywhere it was used.

## Confirm Access Without Submitting a Job

The bundled inspector uses saved credentials, performs read-only serv

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

