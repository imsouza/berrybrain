---
id: sci-molfeat
name: "Scientific: molfeat"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Featurizes small molecules with Molfeat for QSAR/QSPR, chemical similarity, virtual screening, and molecular ML. Covers ECFP/MACCS fingerprints, RDKit descriptors, pharmacophores, pretrained embeddings, configuration persistence, and molecule-to-label alignment."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "molfeat"
keywords:
  - "molfeat"
  - "featurizes"
  - "small"
  - "molecules"
  - "qsar"
  - "qspr"
---

# Molfeat — Small-molecule featurization

## When to use

Use this skill to turn SMILES or RDKit molecules into fingerprints, descriptors,
pharmacophores, or pretrained embeddings for molecular machine learning and similarity
search. Compare representations on the same molecular split and assay endpoint.

This skill targets **Molfeat 1.0.0**. The previous 0.11 runtime guidance is obsolete:
1.x supports modern Python and removes DGL/DGLLife, legacy Graphormer, and protein
adapters. Historical model-store cards can still name removed adapters. The tagged
[1.0 migration guide](https://github.com/datamol-io/molfeat/blob/1.0.0/docs/migration.md)
and source take precedence over older pages still served at the documentation's
`stable` URL.

## Installation

Create an isolated environment. Core examples were executed on Python 3.13.3/macOS
Apple Silicon with Molfeat 1.0.0, datamol 0.13.0, RDKit 2026.03.6, and PyTorch 2.14.1.

```bash
uv venv --python 3.13 .venv-molfeat
uv pip install --python .venv-molfeat/bin/python "molfeat==1.0.0"
```

On Windows use `.venv-molfeat\Scripts\python.exe` as the interpreter path. Upstream
supports Python 3.11–3.14; macOS Intel uses Python 3.11–3.12, PyTorch 2.2.x, NumPy<2,
and Transformers<5. Other platforms require PyTorch>=2.5. Let Molfeat's platform
markers resolve these constraints; do not copy Apple Silicon pins to Intel.

Install only needed extras with the same interpreter: `molfeat[transformer]==1.0.0`
for Hugging Face models, `[mordred]` for mordredcommunity, `[pyg]` for graph tensors,
`[fcd]` for ChemNet embeddings, `[selfies]` for SELFIES conversion, `[cache]` for
HDF5/Parquet, `[viz]` for visualization, and `[cloud]` for S3/GCS stores. DGL and
Graphormer extras no longer exist. Pretrained inference may download substantial
weights; check model licensing, disk space, and device requirements first.

## Workflow

1. Preserve source record IDs, labels, original structures, and a declared policy for
   salts, stereochemistry, tautomers, charge, and duplicate compounds. Standardization
   changes chemical identity; apply the same policy to training and prediction.
2. Start with an explicit ECFP baseline. A calculator processes one molecule;
   `MoleculeTransformer` batches it. `datamol.Mol` is RDKit's molecule type.
3. Record rejected positions and align every associated array. Inspect descriptor
   NaN/Inf separately: successful parsing does not guarantee finite features.
4. Fit any feature selection, imputation, scaling, and model inside the training fold.
   Prefer scaffold/group or temporal splits appropriate to the scientific question;
   random splits can leak close analogues or repeated measurements.
5. Save the featurizer state, ordered feature names, package versions, molecular
   preprocessing policy, and input IDs. Revalidate old state after migrating to 1.x.

### Fingerprint baseline and invalid records

```python
import numpy as np
from molfeat.calc import FPCalculator
from molfeat.trans import MoleculeTransformer

smiles = ["CCO", "invalid", "CC(=O)O", "c1ccccc1"]
record_ids = np.array(["ethanol", "rejected", "acetate", "benzene"])
y = np.array([0.1, 9.9, 0.2, 0.3])  # toy labels only
calc = FPCalculator("ecfp", radius=2, fpSize=2048, includeChirality=True)
transformer = MoleculeTransformer(calc, n_jobs=1, dtype=np.float32)
X, valid_ids = transformer(smiles, ignore_errors=True)
assert X.shape == (3, 2048)
X_ids, y_valid = record_ids[valid_ids], y[valid_ids]
assert valid_ids == [0, 2, 3]
assert np.isfinite(X).all()
```

`ignore_errors` belongs on the call, not the constructor. With `True`, `__call__`
returns filtered features and original input positions; with `False`, it raises on
failed molecules. `transform(..., ignore_errors=True)` preserves positions using
`None` for failures. Never filter each feature block independently and then concatenate.

ECFP radius is a bond radius: `radius=2` means ECFP4; radius 3 means ECFP6. In 1.0.0
`FPCalculator("ecfp")` defaults to radius 2 and 2048 bits. `FPVecTransformer` has a
*different* default length of 2000, so specify `length=2048` when using it.

### Configuration round trip

```python
transformer.to_state_yaml_file("featurizer.yml")
loaded = MoleculeTransformer.from_state_yaml_file("featurizer.yml")
np.testing.assert_array_equal(loaded(["CCO"]), transformer(["CCO"]))
```

Load only trusted configuration/artifacts. State can identify Python classes and
custom serialized callables; YAML/JSON does not make arbitrary third-party state safe.
State saves configuration, not assay labels, preprocessing decisions, or a trained QSAR model.

### Pretrained embeddings

Illustrative; imports and signatures were checked, but no model weights were downloaded:

```python
from molfeat.trans.pretrained import PretrainedHFTransformer

embedder = PretrainedHFTransformer(
    kind="ChemBERTa-77M-MLM", pooling="mean", concat_layers=-1,
    device="cpu", max_length=128, preload=False,
)
# First inference downloads/loads the model.
# embeddings = embedder(["CCO", "c1ccccc1"])
```

`PretrainedMolTransformer` is a base class, not a model-name factory. Use the concrete
adapter. Embedding width depends on checkpoint, pooling, and selected layers; do not
assume 768. Inspect token lengths: truncation at `max_length` can discard chemical
information. Keep the model revision, tokenizer, notation, pooling, and maximum
length with every saved embedding cache.

## Select and discover representations

| Need | Starting point | Check |
| --- | --- | --- |
| Fingerprint baseline | `FPCalculator("ecfp", radius=2, fpSize=2048)` | Chirality, bit collisions, fixed parameters |
| Structural keys | `FPCalculator("maccs")` | 167 entries, including unused bit zero |
| Named descriptors | `RDKitDescriptors2D()` | Columns depend on RDKit; inspect nonfinite values |
| Pharmacophore pairs | `CATS()` | Distance bins determine width; 2D default is 189 |
| 3D shape | `USRDescriptors()` / `USRDescriptors("USRCAT")` | Conformer needed; 12 / 60 entries |
| Pretrained language model | `PretrainedHFTransformer(...)` | Weights, license, tokenization, pooling |

See [available featurizers](references/available_featurizers.md) for valid names and
optional backends, [API contracts](references/api_reference.md) for batch/store
semantics, [worked examples](references/examples.md) for preprocessing, concatenation,
3D and similarity, and [model selection](references/choosing_a_featurizer.md) for
leakage-aware QSAR and bounded-memory screening.

For disco

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

