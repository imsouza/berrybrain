---
id: sciref-molfeat-api-reference
name: "Scientific Ref: Molfeat 1.0 API contracts"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (molfeat): Molfeat 1.0 API contracts"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "molfeat api reference"
  - "molfeat 1.0 api contracts"
keywords:
  - "molfeat"
  - "api"
  - "reference"
  - "specialized"
  - "scientific"
  - "contracts"
---

# Molfeat 1.0 API contracts

Checked against [tagged source](https://github.com/datamol-io/molfeat/tree/1.0.0/molfeat)
on 2026-10-01. Core examples are exercised in the repository's Molfeat tests;
pretrained and optional backend examples are illustrative unless stated otherwise.

## Calculators

`SerializableCalculator` is the extension base. Implement `__call__`, and provide
`__len__` and `columns` when fixed-width output is available. State methods include
`to_state_dict`, `to_state_json`, `to_state_yaml`, and matching `from_state_*` methods.
A calculator acts on one SMILES/RDKit molecule, not a batch.

`FPCalculator(method, length=None, counting=False, **method_params)` accepts only
parameters valid for that fingerprint. Query `available_fingerprints()` and
`default_parameters(method)`. Unknown method parameters are logged and ignored,
so validate the resulting `calc.params` and `len(calc)` instead of assuming an
unrecognized keyword changed the representation. `fpSize` is appropriate for ECFP;
Avalon uses `nBits`, MAP4 uses `dimensions`, and `length` is a common size override.

```python
from molfeat.calc import FPCalculator
calc = FPCalculator("ecfp", radius=2, fpSize=2048, includeChirality=True)
assert calc.params["radius"] == 2
assert calc("CCO").shape == (2048,)
rdkit_fp = calc("CCO", raw=True)  # RDKit bit vector for Tanimoto
```

Use `ecfp-count`/`counting=True` for supported count variants. Counts are folded and
can collide; they are not uniquely identified substructure counts. Not every method
has a count variant.

`get_calculator(name, **params)` recognizes fingerprint names plus `desc2D`, `desc3D`,
`mordred`, `cats`, `cats2D`, `cats3D`, `pharm2D`, `pharm3D`, `usr`, `usrcat`,
`electroshape`, and scaffold-key aliases. See the catalog for concrete classes.

## Batch transformers and dtype

`MoleculeTransformer(featurizer, n_jobs=1, verbose=False, dtype=None,
parallel_kwargs=None, **params)` accepts a calculator/callable or factory name.

| Method | Contract |
| --- | --- |
| `transform(mols, ignore_errors=False)` | Computes rows; raises on failed rows by default; `True` retains failed positions as `None` |
| `__call__(mols, enforce_dtype=True, ignore_errors=False)` | Normal output, or `(filtered_features, original_positions)` when ignoring errors |
| `fit(X, y=None)` | Learns columns without NaN on training inputs; can change output width |
| `preprocess(inputs, labels=None)` | Returns prepared inputs/labels; it is **not invoked automatically** by transform |
| `columns`, `len(transformer)` | Names/width after any fitted column selection |
| `to_state_yaml_file`, `to_state_json_file` | Saves the configuration; corresponding `from_state_*_file` loads it |

Set `dtype=np.float32` explicitly for consistent arrays. The default is `None`, not
float32. Without dtype conversion the output may be a list, including for valid inputs. A single SMILES passed to a transformer still produces a batch with one row;
use `FPCalculator` or select row zero for a one-dimensional vector. For tensor output,
`dtype=torch.float32` is supported by `__call__` with dtype enforcement.

Keep `fit` inside cross-validation: global fitting can use validation-set missingness
to choose columns. NaNs in later validation inputs and infinities still require an
explicit descriptor policy; `ignore_errors=True` is not a complete finite-value check.

## Concatenation

`FeatConcat` takes `FPVecTransformer` instances or names that it turns into those
transformers. It does not take raw calculators and should not be wrapped in
`MoleculeTransformer`.

```python
import numpy as np
from molfeat.trans import FeatConcat
from molfeat.trans.fp import FPVecTransformer

combined = FeatConcat([
    FPVecTransformer("maccs"),
    FPVecTransformer("ecfp:4", length=2048),
], dtype=np.float32)
X = combined(["CCO", "CC"], enforce_dtype=True)
assert X.shape == (2, 2215)
assert combined.length == 2215
assert len(combined) == 2  # number of component transformers
```

The colon suffix belongs to `FPVecTransformer`: `ecfp:4` is diameter 4/radius 2,
while `morgan:2` denotes radius 2. `FPCalculator("ecfp:4")` is not valid. Explicitly
set lengths; `FPVecTransformer` defaults to 2000.

In 1.0.0 `FeatConcat.__call__(ignore_errors=True)` filters each component before
concatenation. If different components fail on different rows, rows may be mismatched
or array sizes may differ. Validate common inputs first and use strict calls, or
combine position-preserving outputs using an explicit shared valid-row intersection.

## Pretrained adapters

Use `PretrainedHFTransformer(kind=..., pooling="mean", concat_layers=-1,
max_length=128, device="cpu", preload=False)` for supported Hugging Face model-store
entries. `kind` is an exact store name; arbitrary Hub IDs are not automatically store
entries. Advanced custom model/tokenizer loading uses `HFModel.from_pretrained`
from `molfeat.trans.pretrained.hf_transformers`.

`PretrainedMolTransformer` is an extension base. Maintained concrete classes also
include `FCDTransformer`, `CheMeleonTransformer`, and `MolJEPATransformer`. The latter
requires the upstream noncommercial license acknowledgement and remote-code trust;
do not enable those switches automatically. Review the upstream integration and a
pinned model revision for an intended application. No weights were downloaded in
this skill's verification.

## Model store

```python
from molfeat.store import ModelStore
store = ModelStore()  # lazy: no discovery request yet
matches = store.search(name="ChemBERTa-77M-MLM")  # exact equality
if matches:
    card = matches[0]
    print(card.name, card.group, card.license)
    print(card.usage())  # string, not an executing loader

# Substring matching must be explicit:
chemberta = [c for c in store.available_models if "chemberta" in c.name.lower()]
```

`ModelInfo` exposes name, group, type, inputs, representation, description, authors,
tags, version, require_3D, license, and license_url. It has no `load()` method.
`store.load(model_name, load_fn=None, ...)` downloads and returns `(artifact, card)`;
its default loader is `joblib.load`. In 1.0.0, loading a metadata-only local card
without `model.save` fails during checksum calculation; instantiate handcrafted
calculators directly. Use the concrete adapter for inference, and load only trusted
serialized artifacts.

The default public root is `https://fs.molfeat.datamol.io/artifacts/`. Discovery
recursively finds `metadata.json` via fsspec; this is a file store

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

