---
id: sciref-pytdc-sources
name: "Scientific Ref: Sources and verification record"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pytdc): Sources and verification record"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pytdc sources"
  - "sources and verification record"
keywords:
  - "pytdc"
  - "sources"
  - "specialized"
  - "scientific"
  - "reference"
  - "verification"
---

# Sources and verification record

Reviewed **2026-10-01** against current official documentation, PyPI metadata,
and a freshly fetched, SHA-256-verified PyTDC 1.1.15 source distribution. Current
upstream `main` was also inspected at commit
`c310c35f27e3f506411018ac43d97b8ba23ca652`. Executed checks used the installed
PyTDC runtime with small local synthetic files and blocked HTTP calls, except
separate explicitly bounded public Dataverse probes. No full dataset, checkpoint,
remote oracle, docking, or authenticated scientific workflow was run.

## Release and package metadata

1. [PyTDC on PyPI](https://pypi.org/project/pytdc/)
   - Stable release: **1.1.15**
   - Uploaded: **2025-03-31**
   - Distribution: source tarball only, 154,168 bytes
   - SHA-256:
     `cd6164859af7b9b6f60e0c6d6e50679eacaffd09cfdea1acfc8bb7360e8e2205`
   - License metadata: MIT
   - No `Requires-Python` or Python classifiers
2. [PyPI JSON for 1.1.15](https://pypi.org/pypi/PyTDC/1.1.15/json)
   - Used to verify exact `Requires-Dist`, artifact metadata, and absence of
     `Requires-Python`.
3. [Official setup.py](https://github.com/mims-harvard/TDC/blob/main/setup.py)
   - Package name `pytdc`; version loaded from `tdc/version.py`; dependencies loaded
     from `requirements.txt`; no `python_requires`.
4. [Official requirements.txt](https://github.com/mims-harvard/TDC/blob/main/requirements.txt)
   - 1.1.15 pins/constrains a large dependency graph, including
     `cellxgene-census==1.15.0`, NumPy `<2`, RDKit `<2024.3.1`, Hugging Face
     packages, and TileDB-SOMA.
5. [cellxgene-census 1.15.0 JSON](https://pypi.org/pypi/cellxgene-census/1.15.0/json)
   - Declares `Requires-Python: >=3.8,<3.12`.
6. [RDKit 2023.9.6 JSON](https://pypi.org/pypi/rdkit/2023.9.6/json)
   - Provides CPython 3.8–3.12 wheels for common platforms, including macOS ARM64,
     but no CPython 3.13 wheel.
7. [Setuptools release history](https://setuptools.pypa.io/en/stable/history.html)
   - `pkg_resources` was deprecated long before this snapshot and removed in
     setuptools 82.0.0 (2026-02-08).
   - PyTDC 1.1.15 still imports it at runtime. The isolated smoke test therefore
     pins the verified compatibility release `setuptools==80.9.0`.

The pinned smoke environment uses CPython 3.11. PyTDC itself does not publish a
supported Python range, so this skill describes Python 3.11 plus setuptools 80.9.0
as the verified target rather than claiming broader upstream support. On the current tested
macOS ARM64 resolver, the test environment contained 128 packages (including pytest) and included large
Torch, RDKit, TileDB, Arrow, and scientific-Python artifacts.

## Official source used for API verification

1. [Package metadata registry](https://github.com/mims-harvard/TDC/blob/main/tdc/metadata.py)
   - Task/dataset names, evaluator names, oracle categories, benchmark names,
     benchmark metrics, and split metadata.
2. [Top-level public imports](https://github.com/mims-harvard/TDC/blob/main/tdc/__init__.py)
   - `Evaluator`, `Oracle`, and deprecated generic `BenchmarkGroup`.
3. [Single-prediction imports](https://github.com/mims-harvard/TDC/blob/main/tdc/single_pred/__init__.py)
4. [Multi-prediction imports](https://github.com/mims-harvard/TDC/blob/main/tdc/multi_pred/__init__.py)
5. [Generation imports](https://github.com/mims-harvard/TDC/blob/main/tdc/generation/__init__.py)
6. [Base loader](https://github.com/mims-harvard/TDC/blob/main/tdc/base_dataset.py)
7. [Single-prediction loader](https://github.com/mims-harvard/TDC/blob/main/tdc/single_pred/single_pred_dataset.py)
8. [Pair-prediction loader](https://github.com/mims-harvard/TDC/blob/main/tdc/multi_pred/bi_pred_dataset.py)
9. [General multi-prediction loader](https://github.com/mims-harvard/TDC/blob/main/tdc/multi_pred/multi_pred_dataset.py)
10. [Generation loader](https://github.com/mims-harvard/TDC/blob/main/tdc/generation/generation_dataset.py)
11. [Split implementations](https://github.com/mims-harvard/TDC/blob/main/tdc/utils/split.py)
12. [Evaluator implementation](https://github.com/mims-harvard/TDC/blob/main/tdc/evaluator.py)
13. [Oracle implementation](https://github.com/mims-harvard/TDC/blob/main/tdc/oracles.py)
14. [Download/load implementation](https://github.com/mims-harvard/TDC/blob/main/tdc/utils/load.py)
15. [Metadata retrieval helpers](https://github.com/mims-harvard/TDC/blob/main/tdc/utils/retrieve.py)
16. [Specialized BenchmarkGroup base](https://github.com/mims-harvard/TDC/blob/main/tdc/benchmark_group/base_group.py)
17. [Deprecated generic BenchmarkGroup](https://github.com/mims-harvard/TDC/blob/main/tdc/benchmark_deprecated.py)

The stable PyPI source distribution was inspected directly rather than assuming
that `main` or old generated documentation exactly matched 1.1.15.

## Official user documentation

1. [TDC quick start](https://tdcommons.ai/start/)
   - Problem/task/dataset hierarchy and constructor/get-data/get-split workflow.
2. [Dataset splits](https://tdcommons.ai/functions/data_split/)
   - Random defaults, documented scaffold scope, `cold_split` plus `column_name`,
     and combination split.
3. [Model evaluation](https://tdcommons.ai/functions/data_evaluation/)
   - Exact evaluator examples, input types, thresholds, and metric definitions.
4. [Benchmark/leaderboard guide](https://tdcommons.ai/benchmark/overview/)
   - `get`, `get_train_valid_split`, `evaluate`, `evaluate_many`, fixed test set,
     and at least five independent runs.
5. [ADMET benchmark group](https://tdcommons.ai/benchmark/admet_group/overview)
   - Dataset-specific benchmark metrics and scaffold protocol.
6. [Oracle documentation](https://tdcommons.ai/functions/oracles/)
   - Local, checkpoint, synthesis-service, and docking examples/requirements.
7. [Molecule generation task](https://tdcommons.ai/generation_tasks/molgen)
   - Stable MolGen names and random split examples.
8. [ADME task](https://tdcommons.ai/single_pred_tasks/adme)
   - Dataset-specific descriptions, splits, citations, and heterogeneous license
     labels.
9. [DTI task](https://tdcommons.ai/multi_pred_tasks/dti/)
   - DTI datasets, cold-drug/protein intent, and per-dataset licenses.
10. [Trial outcome task](https://tdcommons.ai/multi_pred_tasks/trialoutcome/)
    - Evidence that some TDC datasets carry non-commercial terms.
11. [TDC 0.4.1 ReadTheDocs](https://tdc.readthedocs.io/)
    - Generated API signatures and source links used only as a cross-check. Its
      displayed release is behind PyPI 1.1.15.
12. [

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

