---
id: sci-cirq
name: "Scientific: cirq"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Google quantum computing framework. Use when targeting Google Quantum AI hardware, designing noise-aware circuits, or running quantum characterization experiments. Best for Google hardware, noise modeling, and low-level circuit design. For IBM hardware use qiskit; for quantum ML "
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "cirq"
keywords:
  - "cirq"
  - "google"
  - "quantum"
  - "computing"
  - "framework"
  - "targeting"
---

# Cirq - Quantum Computing with Python

Cirq is Google Quantum AI's open-source framework for designing, simulating, and running quantum circuits on quantum computers and simulators.

## When to Use This Skill

Use this skill when:
- Building, simulating, or optimizing NISQ circuits in Python
- Running jobs on Google Quantum AI processors (via `cirq-google`) or partner backends (IonQ, Azure Quantum, AQT, Pasqal)
- Modeling noise, compiling to hardware gatesets, or designing characterization experiments
- Using parameter sweeps, transformers, or the ReCirq experiment patterns

For IBM hardware use **qiskit**; for quantum ML with autodiff use **pennylane**; for physics simulations use **qutip**.

## Installation

Examples target **Cirq 1.7.0** on Python 3.11+. Keep Cirq vendor packages on the matching release; independently versioned integrations such as Azure Quantum need their own compatibility check.

```bash
uv pip install "cirq-core==1.7.0"
# Optional OpenQASM import dependency
uv pip install ply
```

For hardware integration (pin matching versions for reproducibility):
```bash
# Google Quantum Engine (requires approved GCP project access)
uv pip install "cirq-google==1.7.0"

# IonQ
uv pip install "cirq-ionq==1.7.0"

# AQT (Alpine Quantum Technologies)
uv pip install "cirq-aqt==1.7.0"

# Pasqal
uv pip install "cirq-pasqal==1.7.0"

# Azure: use a SEPARATE environment; its current extras require Cirq <1.7.
uv pip install "qdk[azure,cirq]==1.32.3" "azure-quantum==3.13.0"
```

Pin all `cirq-*` packages in an environment to the same release. The Azure
example targets its supported Cirq 1.6.1 stack separately; do not force Cirq 1.7.0
into it. Cirq 1.7.0 updates the IonQ adapter to API v0.4.

Local examples were checked with synthetic circuits. Hardware examples are
illustrative and were checked against released source and provider documentation,
without submitting cloud jobs. See [review evidence](references/review.md).

## Quick Start

### Basic Circuit

```python
import cirq
import numpy as np

# Create qubits
q0, q1 = cirq.LineQubit.range(2)

# Build circuit
circuit = cirq.Circuit(
    cirq.H(q0),              # Hadamard on q0
    cirq.CNOT(q0, q1),       # CNOT with q0 control, q1 target
    cirq.measure(q0, q1, key='result')
)

print(circuit)

# Simulate
simulator = cirq.Simulator(seed=42)
result = simulator.run(circuit, repetitions=1000)

# Display results
print(result.histogram(key='result'))
```

### Parameterized Circuit

```python
import sympy

# Define symbolic parameter
theta = sympy.Symbol('theta')

# Create parameterized circuit
circuit = cirq.Circuit(
    cirq.ry(theta)(q0),
    cirq.measure(q0, key='m')
)

# Sweep over parameter values
sweep = cirq.Linspace('theta', start=0, stop=2*np.pi, length=20)
results = simulator.run_sweep(circuit, params=sweep, repetitions=1000)

# Process results
for params, result in zip(sweep, results):
    theta_val = params['theta']
    counts = result.histogram(key='m')
    print(f"θ={theta_val:.2f}: {counts}")
```

## Core Capabilities

### Circuit Building
For comprehensive information about building quantum circuits, including qubits, gates, operations, custom gates, and circuit patterns, see:
- **[references/building.md](references/building.md)** - Complete guide to circuit construction

Common topics:
- Qubit types (GridQubit, LineQubit, NamedQubit)
- Single and two-qubit gates
- Parameterized gates and operations
- Custom gate decomposition
- Circuit organization with moments
- Standard circuit patterns (Bell states, GHZ, QFT)
- Import/export (OpenQASM, JSON)
- Working with qudits and observables

### Simulation
For detailed information about simulating quantum circuits, including exact simulation, noisy simulation, parameter sweeps, and the Quantum Virtual Machine, see:
- **[references/simulation.md](references/simulation.md)** - Complete guide to quantum simulation

Common topics:
- Exact simulation (state vector, density matrix)
- Sampling and measurements
- Parameter sweeps (single and multiple parameters)
- Noisy simulation
- State histograms and visualization
- Quantum Virtual Machine (QVM)
- Expectation values and observables
- Performance optimization

### Circuit Transformation
For information about optimizing, compiling, and manipulating quantum circuits, see:
- **[references/transformation.md](references/transformation.md)** - Complete guide to circuit transformations

Common topics:
- Transformer framework
- Gate decomposition
- Circuit optimization (merge gates, eject Z gates, drop negligible operations)
- Circuit compilation for hardware
- Qubit routing and SWAP insertion
- Custom transformers
- Transformation pipelines

### Hardware Integration
For information about running circuits on real quantum hardware from various providers, see:
- **[references/hardware.md](references/hardware.md)** - Complete guide to hardware integration

Supported providers:
- **Google Quantum AI** (`cirq-google`) — assigned processors via Quantum Engine; discover IDs from your approved project. Bundled virtual processor names are not proof of live access.
- **IonQ** (`cirq-ionq`) — trapped-ion QPUs and simulators
- **Azure Quantum** (`qdk[azure,cirq]`) — discover Cirq-compatible targets in your workspace, in its separate supported environment
- **AQT** (`cirq-aqt`) — Alpine Quantum Technologies
- **Pasqal** (`cirq-pasqal`) — local device modeling; the legacy remote sampler is not a verified current Pasqal Cloud integration

Topics include device representation, qubit selection, authentication, job management, and circuit optimization for hardware. See [Access and authentication](https://quantumai.google/cirq/google/access) for Google Cloud setup.

### Noise Modeling
For information about modeling noise, noisy simulation, characterization, and error mitigation, see:
- **[references/noise.md](references/noise.md)** - Complete guide to noise modeling

Common topics:
- Noise channels (depolarizing, amplitude damping, phase damping)
- Noise models (constant, gate-specific, qubit-specific, thermal)
- Adding noise to circuits
- Readout noise
- Noise characterization (randomized benchmarking, XEB)
- Noise visualization (heatmaps)
- Error mitigation techniques

### Quantum Experiments
For information about designing experiments, parameter sweeps, data collection, and using the ReCirq framework, see:
- **[references/experiments.md](references/experiments.md)** - Complete guide to quantum experiments

Common topics:
- Experiment design patterns
- P

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

