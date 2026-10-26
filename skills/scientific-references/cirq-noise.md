---
id: sciref-cirq-noise
name: "Scientific Ref: Noise modeling and mitigation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (cirq): Noise modeling and mitigation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "cirq noise"
  - "noise modeling and mitigation"
keywords:
  - "cirq"
  - "noise"
  - "specialized"
  - "scientific"
  - "reference"
  - "modeling"
---

# Noise modeling and mitigation

Examples target Cirq 1.7.0 and small local systems. Noise assumptions are part of
the scientific model: specify gate durations, idle evolution, readout, qubit
order, and calibration date. A phenomenological channel is not a complete
hardware characterization.

## Channels and their parameters

```python
import cirq
import numpy as np
from scipy.optimize import curve_fit

q = cirq.LineQubit(0)
simulator = cirq.DensityMatrixSimulator(dtype=np.complex128, seed=42)
channels = [
    cirq.depolarize(p=0.01),
    cirq.amplitude_damp(gamma=0.1),
    cirq.phase_damp(gamma=0.1),
    cirq.bit_flip(p=0.01),
    cirq.phase_flip(p=0.01),
    cirq.generalized_amplitude_damp(p=0.8, gamma=0.2),
]
for channel in channels:
    rho = simulator.simulate(cirq.Circuit(cirq.H(q), channel(q))).final_density_matrix
    assert np.isclose(np.trace(rho), 1)
    assert np.linalg.eigvalsh(rho).min() >= -1e-10
```

- `depolarize(p)` applies a nonidentity Pauli with total probability p; p is not
  directly the average gate infidelity. With `n_qubits=2` it is a joint channel,
  different from independent one-qubit channels on the pair.
- `amplitude_damp(gamma)` decays |1> to |0> with probability gamma.
- `phase_damp(gamma)` multiplies off-diagonal entries by `sqrt(1-gamma)`.
- `generalized_amplitude_damp(p, gamma)` has decay probability `p*gamma` and
  excitation probability `(1-p)*gamma`; p weights the relaxation branch.
- `cirq.reset(q)` resets to |0>. To prepare |1>, reset and then apply X.

## Gate-specific and qubit-specific noise

```python
class GateNoise(cirq.NoiseModel):
    def noisy_operation(self, op):
        if cirq.is_measurement(op):
            return op  # model readout separately
        n = len(op.qubits)
        if n in (1, 2) and cirq.has_unitary(op):
            p = 0.001 if n == 1 else 0.01
            return [op, cirq.depolarize(p, n_qubits=n).on(*op.qubits)]
        return op

class QubitSpecificNoise(cirq.NoiseModel):
    def __init__(self, qubit_noise_map):
        self.qubit_noise_map = qubit_noise_map

    def noisy_operation(self, op):
        if cirq.is_measurement(op):
            return op
        return [op, [self.qubit_noise_map[q](q) for q in op.qubits
                     if q in self.qubit_noise_map]]

circuit = cirq.Circuit(cirq.H(q), cirq.measure(q, key="result"))
noisy_circuit = circuit.with_noise(GateNoise())
result = simulator.run(noisy_circuit, repetitions=1000)
```

`with_noise` handles the returned operation tree and time ordering. Do not collect
an operation and its following noise on the same qubit into one `Moment` (overlap
is invalid). Gate-based models above omit idle-qubit noise. A constant model
`cirq.ConstantQubitNoiseModel(cirq.depolarize(0.01))` instead adds a layer to every
system qubit after every nonvirtual moment, including measurement moments.

## Relaxation with T1 and T2

For zero-temperature Markovian relaxation, `1/Tphi = 1/T2 - 1/(2*T1)` and the
phase-damping parameter is `1-exp(-2*t/Tphi)`. Using `1-exp(-t/T2)` as phase damping
in addition to amplitude damping double counts relaxation and gives the wrong
coherence decay. The following fixed-duration model is deliberately local to each
operation; a scheduled hardware model must also account for idle intervals.

```python
class ThermalNoise(cirq.NoiseModel):
    def __init__(self, T1, T2, gate_time):
        values = np.asarray([T1, T2, gate_time], dtype=float)
        if not np.all(np.isfinite(values)) or T1 <= 0 or T2 <= 0 or gate_time < 0:
            raise ValueError("Use finite positive T1/T2 and nonnegative duration")
        if T2 > 2*T1:
            raise ValueError("This relaxation model requires T2 <= 2*T1")
        self.gamma_amp = -np.expm1(-gate_time/T1)
        inverse_Tphi = max(0.0, 1/T2 - 1/(2*T1))
        self.gamma_phase = -np.expm1(-2*gate_time*inverse_Tphi)

    def noisy_operation(self, op):
        if cirq.is_measurement(op):
            return op
        return [op, [
            [cirq.amplitude_damp(self.gamma_amp)(q), cirq.phase_damp(self.gamma_phase)(q)]
            for q in op.qubits
        ]]

thermal = ThermalNoise(T1=50e-6, T2=30e-6, gate_time=25e-9)
thermal_circuit = cirq.Circuit(cirq.I(q)).with_noise(thermal)
plus = np.array([1, 1], dtype=complex) / np.sqrt(2)
thermal_rho = simulator.simulate(thermal_circuit, initial_state=plus).final_density_matrix
np.testing.assert_allclose(thermal_rho[0, 1], 0.5*np.exp(-25e-9/30e-6), atol=1e-12)
```

## Asymmetric classical readout errors

Cirq's confusion matrix has **rows = true state, columns = recorded state**.
Do not average asymmetric errors into one bit-flip probability.

```python
p1_given_0, p0_given_1 = 0.01, 0.20
confusion = np.array([[1-p1_given_0, p1_given_0], [p0_given_1, 1-p0_given_1]])
measurement = cirq.measure(q, key="result", confusion_map={(0,): confusion})
readout_result = cirq.Simulator(seed=42).run(
    cirq.Circuit(cirq.X(q), measurement), repetitions=2000
)
```

The tuple `(0,)` selects a position within the measurement, not the numerical
coordinate of a qubit. For column probability vectors, observed = confusion.T @
true. Correlated readout needs a joint matrix, and full n-qubit calibration scales
as `2**n` prepared states.

```python
def mitigate_readout_probabilities(measured_probs, confusion):
    measured_probs = np.asarray(measured_probs, dtype=float)
    confusion = np.asarray(confusion, dtype=float)
    if confusion.shape != (len(measured_probs), len(measured_probs)):
        raise ValueError("Confusion matrix and outcome vector dimensions differ")
    if (not np.all(np.isfinite(confusion)) or np.any(confusion < 0)
            or not np.allclose(confusion.sum(axis=1), 1)):
        raise ValueError("Expected a row-stochastic confusion matrix")
    if (not np.all(np.isfinite(measured_probs)) or np.any(measured_probs < 0)
            or not np.isclose(measured_probs.sum(), 1)):
        raise ValueError("Expected normalized measured probabilities")
    if np.linalg.cond(confusion) > 1e8:
        raise ValueError("Readout correction is ill-conditioned")
    # May contain negative entries from shot noise; retain as quasi-probabilities.
    return np.linalg.solve(confusion.T, measured_probs)

true_probs = np.array([0.25, 0.75])
corrected = mitigate_readout_probabilities(confusion.T @ true_probs, confusion)
np.testing.assert_allclose(corrected, true_probs)
```

Do not silently clip negatives, round to integer counts, or discard mass. Report
uncertainty from both experim

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

