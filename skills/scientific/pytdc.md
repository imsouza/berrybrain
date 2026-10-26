---
id: sci-pytdc
name: "Scientific: pytdc"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Provides Therapeutics Data Commons workflows through PyTDC for registry discovery, dataset access, task-aware splits, evaluator metrics, benchmark groups, and bounded molecular-oracle scoring. Use when working with TDC therapeutic ML datasets or benchmarks."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "pytdc"
keywords:
  - "pytdc"
  - "provides"
  - "therapeutics"
  - "commons"
  - "workflows"
  - "through"
---

# PyTDC (Therapeutics Data Commons)

Use the official `PyTDC` distribution (`import tdc`) to discover therapeutic ML
tasks, load approved datasets, apply task-appropriate splits, evaluate predictions,
and work with curated benchmark groups. Prefer package metadata over copied dataset
lists, and plan network/storage effects before constructing any loader.

## Verified snapshot

- Research date: **2026-10-01**
- PyPI stable: **PyTDC 1.1.15**, released 2025-03-31
- Package/source repository: `mims-harvard/TDC`
- Code license: MIT
- PyPI supplies only a source distribution and declares no `Requires-Python`
- The dependency graph makes **CPython 3.11** the reproducible target used here:
  `cellxgene-census==1.15.0` excludes Python 3.12, and PyTDC's constrained
  RDKit release has no CPython 3.13 wheel
- PyTDC imports deprecated `pkg_resources` at runtime. Setuptools 82 removed that
  module; pin the verified compatibility release **setuptools 80.9.0**.
- `tdc.readthedocs.io` still identifies itself as TDC 0.4.1; use it as API
  cross-reference, not as release-version evidence
- Upstream publishes no GitHub tags/releases or maintained changelog. Treat
  undocumented migration claims as uncertainty and verify against the installed
  1.1.15 source/metadata.

See [references/sources.md](references/sources.md) for dated evidence and known
documentation conflicts.

## Installation

Use an isolated CPython 3.11 environment and pin the reviewed snapshot:

```bash
uv venv --python 3.11 .venv-pytdc
uv pip install --dry-run --python .venv-pytdc/bin/python \
  "setuptools==80.9.0" "PyTDC==1.1.15"
uv pip install --python .venv-pytdc/bin/python \
  "setuptools==80.9.0" "PyTDC==1.1.15"
```

The current macOS ARM64 test resolution installed 128 packages, including large
scientific/ML dependencies, so the environment itself can transfer and occupy
hundreds of megabytes before any dataset is downloaded. Review the dry run and
available disk first. The direct pins identify the reviewed API snapshot; generate
a platform-specific `uv.lock` in the user's project when every transitive version
must also be frozen.

For an ephemeral command:

```bash
uv run --no-project --isolated --python 3.11 \
  --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/discover_metadata.py --kind tasks
```

To check for a newer release, inspect the PyPI release history at
<https://pypi.org/project/pytdc/>. Before changing the pin, compare its source
distribution, dependencies, official repository, task registries, and smoke tests;
do not silently substitute the separate `pytdc-nextml` package.

## Non-negotiable data and network policy

1. **Discover first.** Reading `tdc.metadata` or using
   `scripts/discover_metadata.py` does not instantiate a loader or download data.
2. **Plan second.** Record the exact task/dataset, official task page, license,
   expected size, cache directory, split, metric, and reproducibility seed.
3. **Confirm the authorized scope before downloading.** Loader constructors fetch missing data.
   Some datasets and benchmark-group archives are large; model-backed oracles can
   fetch checkpoints; remote/docking oracles can transmit molecular structures.
4. **Execute within that scope.** In bundled CLIs, `--execute` acknowledges
   execution and `--download` is additionally required for MolGen corpora or
   supported oracle checkpoints.
5. **Keep outputs bounded.** Emit counts, schema, and small previews rather than
   full datasets, sequences, prediction arrays, or molecule corpora.

### Cache and cost behavior

- Ordinary loaders default to `path="./data"` and save files beneath that path.
  The bundled scripts instead default to explicit `.pytdc-*` directories.
- Core downloads use Harvard Dataverse file endpoints when a local filename is
  absent. Newer resource classes may use other upstream services.
- `admet_group(path=...)` and other benchmark-group constructors download and
  extract the group archive when `<path>/<group>` is absent.
- Download-backed `Oracle(...)` construction uses `./oracle` internally. The
  bundled oracle CLI changes into a safe runtime directory before approved calls.
- PyTDC 1.1.15 does not provide a universal cache quota, eviction policy, or
  dataset-wide checksum manifest. Use `scripts/cache_audit.py` and manage disk
  retention explicitly.
- Network transfer, local storage, decompression, parsing, feature generation,
  docking, and external service calls can all incur time or monetary cost.

The PyTDC **code** is MIT. Dataset/task licenses are heterogeneous: official task
pages include per-dataset terms ranging from Creative Commons licenses to
non-commercial restrictions or “Not Specified.” Verify the exact dataset's page and
original source terms before download, redistribution, publication, or commercial
use. Cite both TDC and the original dataset.

## Start with metadata-only discovery

From this skill directory:

```bash
uv run --no-project --isolated --python 3.11 --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/discover_metadata.py --kind datasets --task ADME --limit 50

uv run --no-project --isolated --python 3.11 --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/discover_metadata.py --kind benchmarks --limit 50

uv run --no-project --isolated --python 3.11 --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/discover_metadata.py --kind evaluators --limit 100
```

The package API is also metadata-only:

```python
from tdc.utils import retrieve_dataset_names, retrieve_benchmark_names

adme_names = retrieve_dataset_names("ADME")
admet_benchmarks = retrieve_benchmark_names("admet_group")
```

Use exact returned names. PyTDC performs fuzzy matching internally, but explicit
matching avoids silently selecting the wrong dataset/oracle.

## Dataset workflow

Plan a split without downloading:

```bash
uv run --no-project --isolated --python 3.11 --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/load_and_split_data.py \
  --task ADME --dataset Caco2_Wang --method scaffold \
  --seed 42 --data-dir .pytdc-data
```

After the user approves the dataset, license, transfer, and storage:

```bash
uv run --no-project --isolated --python 3.11 --with "setuptools==80.9.0" --with "PyTDC==1.1.15" \
  python scripts/load_and_split_data.py \
  --task ADME --dataset Caco2_Wang --method scaffold \
  --seed 42 --data-dir .pytdc-data --execute
```

Verified public import patterns include:

```py

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

