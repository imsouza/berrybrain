---
id: sciref-qiskit-sources
name: "Scientific Ref: Upstream Sources and Version Provenance"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (qiskit): Upstream Sources and Version Provenance"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "qiskit sources"
  - "upstream sources and version provenance"
keywords:
  - "qiskit"
  - "sources"
  - "specialized"
  - "scientific"
  - "reference"
  - "upstream"
---

# Upstream Sources and Version Provenance

## Verification Snapshot

Reviewed **2026-10-01** using current official IBM Quantum documentation, tagged Qiskit source, released installed packages, and PyPI metadata. All skill and supporting files were reviewed. Hardware, account setup, and optional application workflows remain illustrative where stated.

PyPI versions observed:

| Distribution | Version | PyPI |
|---|---:|---|
| Qiskit SDK | 2.5.2 | [qiskit](https://pypi.org/project/qiskit/) |
| Qiskit IBM Runtime | 0.50.0 | [qiskit-ibm-runtime](https://pypi.org/project/qiskit-ibm-runtime/) |
| Qiskit Aer | 0.17.2 | [qiskit-aer](https://pypi.org/project/qiskit-aer/) |
| Qiskit Algorithms | 0.4.0 | [qiskit-algorithms](https://pypi.org/project/qiskit-algorithms/) |
| Qiskit Nature | 0.8.0 | [qiskit-nature](https://pypi.org/project/qiskit-nature/) |
| Qiskit Nature PySCF | 0.4.0 | [qiskit-nature-pyscf](https://pypi.org/project/qiskit-nature-pyscf/) |
| Qiskit Machine Learning | 0.9.1 | [qiskit-machine-learning](https://pypi.org/project/qiskit-machine-learning/) |
| Qiskit Optimization | 0.7.0 | [qiskit-optimization](https://pypi.org/project/qiskit-optimization/) |

The executable core baseline is Qiskit 2.5.2, Runtime 0.50.0, Aer 0.17.2, and Algorithms 0.4.0 on Python 3.13. The table also lists documentation-reviewed optional packages; it does not claim they were all installed together.

## Canonical Qiskit SDK Sources

- [IBM Quantum documentation](https://quantum.cloud.ibm.com/docs/)
- [Qiskit quickstart](https://quantum.cloud.ibm.com/docs/guides/quick-start)
- [Install Qiskit](https://quantum.cloud.ibm.com/docs/guides/install-qiskit)
- [Qiskit SDK API reference](https://quantum.cloud.ibm.com/docs/api/qiskit)
- [Qiskit SDK release notes](https://quantum.cloud.ibm.com/docs/api/qiskit/release-notes)
- [Qiskit 2.5 release notes](https://quantum.cloud.ibm.com/docs/api/qiskit/release-notes/2.5)
- [Qiskit GitHub repository](https://github.com/Qiskit/qiskit)
- [Qiskit GitHub releases](https://github.com/Qiskit/qiskit/releases)

Use `quantum.cloud.ibm.com/docs` for current guides. Old `qiskit.org/learn`, `qiskit.org/ecosystem/...`, and legacy documentation URLs can be stale or redirect.

## Core User Guides

### Circuits and quantum information

- [Construct circuits](https://quantum.cloud.ibm.com/docs/guides/construct-circuits)
- [Circuit library API](https://quantum.cloud.ibm.com/docs/api/qiskit/circuit_library)
- [Quantum information API](https://quantum.cloud.ibm.com/docs/api/qiskit/quantum_info)
- [QPY serialization API](https://quantum.cloud.ibm.com/docs/api/qiskit/qpy)
- [OpenQASM 2 API](https://quantum.cloud.ibm.com/docs/api/qiskit/qasm2)
- [OpenQASM 3 API](https://quantum.cloud.ibm.com/docs/api/qiskit/qasm3)

### Primitives

- [Introduction to primitives](https://quantum.cloud.ibm.com/docs/guides/primitives)
- [Primitive input and output](https://quantum.cloud.ibm.com/docs/guides/primitive-input-output)
- [Exact simulation with SDK primitives](https://quantum.cloud.ibm.com/docs/guides/simulate-with-qiskit-sdk-primitives)
- [Primitives API](https://quantum.cloud.ibm.com/docs/api/qiskit/primitives)

### Transpilation

- [Introduction to transpilation](https://quantum.cloud.ibm.com/docs/guides/transpile)
- [Compare transpiler settings](https://quantum.cloud.ibm.com/docs/guides/circuit-transpilation-settings)
- [Transpiler API](https://quantum.cloud.ibm.com/docs/api/qiskit/transpiler)
- [Preset pass managers API](https://quantum.cloud.ibm.com/docs/api/qiskit/transpiler_preset)

### Visualization

- [Visualization API](https://quantum.cloud.ibm.com/docs/api/qiskit/visualization)

## Migration Sources

- [Qiskit 2.0 migration guide](https://quantum.cloud.ibm.com/docs/migration-guides/qiskit-2.0)
- [Qiskit 1.0 feature changes](https://quantum.cloud.ibm.com/docs/guides/qiskit-1.0-features)
- [Qiskit package-structure migration](https://quantum.cloud.ibm.com/docs/guides/metapackage-migration)
- [Migrate BackendV1 to BackendV2](https://quantum.cloud.ibm.com/docs/guides/qiskit-backendv1-to-v2)
- [Migrate to V2 Runtime primitives](https://quantum.cloud.ibm.com/docs/guides/v2-primitives)
- [Migrate Qiskit Pulse to fractional gates](https://quantum.cloud.ibm.com/docs/guides/pulse-migration)
- [Migrate from IBM Quantum Platform Classic](https://quantum.cloud.ibm.com/docs/migration-guides/classic-iqp-to-cloud-iqp)

Qiskit 2.0 removed `qiskit.pulse`, legacy instruction conditions, V1 reference primitive implementations, and several BackendV1-era interfaces. Runtime V1 primitive support was removed earlier. Read both SDK and Runtime migration guides because they version independently.

## IBM Quantum Runtime Sources

- [Qiskit IBM Runtime repository](https://github.com/Qiskit/qiskit-ibm-runtime)
- [Runtime client release notes](https://quantum.cloud.ibm.com/docs/api/qiskit-ibm-runtime/release-notes)
- [QiskitRuntimeService API](https://quantum.cloud.ibm.com/docs/api/qiskit-ibm-runtime/qiskit-runtime-service)
- [Client-side Sampler API](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/executor-sampler-sampler)
- [Client-side Estimator API](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/executor-estimator-estimator)
- [Client-side option models](https://quantum.cloud.ibm.com/docs/en/api/qiskit-ibm-runtime/options-models)
- [Set up IBM Quantum Platform](https://quantum.cloud.ibm.com/docs/guides/cloud-setup)
- [Runtime execution modes](https://quantum.cloud.ibm.com/docs/guides/execution-modes)
- [Run jobs in a batch](https://quantum.cloud.ibm.com/docs/guides/run-jobs-batch)
- [Run jobs in a session](https://quantum.cloud.ibm.com/docs/guides/run-jobs-session)
- [Runtime local testing mode](https://quantum.cloud.ibm.com/docs/guides/local-testing-mode)
- [Sampler options](https://quantum.cloud.ibm.com/docs/guides/sampler-options)
- [Estimator options](https://quantum.cloud.ibm.com/docs/guides/estimator-options)
- [Error mitigation and suppression](https://quantum.cloud.ibm.com/docs/guides/error-mitigation-and-suppression-techniques)

Runtime 0.50 deprecates top-level `SamplerV2`/`EstimatorV2` in favor of the client-side modules above. V2 PUBs, `mode=...`, and explicit target compilation remain relevant. Options moved to Pydantic `options_models` in 0.49; use `model_dump()`.

## Simulation

- [Qiskit Aer documentation](https://qiskit.github.io/qiskit-aer/)
- [Aer simulator API](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.AerSimulator.html)
- [Aer primitives API](https://q

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

