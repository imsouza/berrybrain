---
id: sciref-shap-troubleshooting
name: "Scientific Ref: SHAP Troubleshooting"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (shap): SHAP Troubleshooting"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "shap troubleshooting"
keywords:
  - "shap"
  - "troubleshooting"
  - "specialized"
  - "scientific"
  - "reference"
---

# SHAP Troubleshooting

Diagnose SHAP problems from environment and semantics outward. Do not start by disabling checks or changing tolerances.

## Minimal Diagnostic Packet

Run without printing environment variables:

```python
import importlib.metadata
import platform
from pathlib import Path

import numpy as np
import shap

print("Python:", platform.python_version())
print("SHAP:", shap.__version__)
print("NumPy:", np.__version__)
print("SHAP import path:", Path(shap.__file__).resolve())

for package in [
    "pandas",
    "scikit-learn",
    "xgboost",
    "lightgbm",
    "catboost",
    "tensorflow",
    "keras",
    "torch",
]:
    try:
        print(f"{package}:", importlib.metadata.version(package))
    except importlib.metadata.PackageNotFoundError:
        pass
```

For an explanation:

```python
print("values:", np.shape(explanation.values))
print("base_values:", np.shape(explanation.base_values))
print("data:", np.shape(explanation.data))
print("feature_names:", explanation.feature_names)
print("output_names:", explanation.output_names)
print("model input:", X_eval.shape)
```

Do not include sensitive row values in a public bug report.

## Installation and Import Problems

SHAP 0.52.0 requires Python 3.12+ and NumPy 2+.

```bash
uv run python --version
uv pip show shap
uv pip tree
```

If Python 3.11 is required, pin SHAP 0.51.0. For Python 3.9/3.10, 0.49.1 is the final compatible line; upgrading Python is preferable.

### Wrong module imported

Never name a local script or directory:

- `shap.py`;
- `numpy.py`;
- `pandas.py`;
- `xgboost.py`;
- `lightgbm.py`;
- `joblib.py`;
- `sklearn.py`.

Local files can shadow installed packages. Verify:

```python
from pathlib import Path
import shap

print(Path(shap.__file__).resolve())
```

The path should point into the intended environment's installed package, not the project working directory.

After renaming a shadowing module, remove only its corresponding local `__pycache__` entries and restart Python.

## Shape Problems

### Old list logic fails

Since 0.45, one-input multi-output explainers return an array with outputs last:

```python
class_exp = explanation[..., class_index]
```

Do not use:

```python
class_exp = explanation[class_index]  # selects a sample
```

### Plot expects 2-D values

Select an output:

```python
print(explanation.values.shape)
single_output = explanation[..., output_index]
assert single_output.values.ndim == 2
shap.plots.beeswarm(single_output)
```

### Waterfall expects one row

```python
single_output = explanation[..., output_index]
shap.plots.waterfall(single_output[row_index])
```

### Feature count mismatch

Check:

```python
assert explanation.values.shape[1] == X_eval.shape[1]
assert len(explanation.feature_names) == X_eval.shape[1]
```

Likely causes:

- preprocessing was applied to only one of background/evaluation data;
- columns are reordered;
- one-hot categories differ;
- the model receives a NumPy array while names came from a different DataFrame;
- an identifier/target column was accidentally included.

## Additivity Failures

An additivity failure means the selected SHAP values do not reconstruct the selected output within expected tolerance.

### Diagnostic order

1. Confirm rows and order match.
2. Confirm transformed columns, order, dtype, missingness, and sparse/dense form match model fitting.
3. Confirm model artifact and explainer refer to the same fitted model.
4. Confirm output index and units.
5. Recompute on one row.
6. Use an explicit, representative background.
7. Upgrade/downgrade only after checking model-library compatibility notes.
8. Test a minimal model/dataset reproducer.

Explicit check for one tabular output:

```python
values = np.asarray(explanation.values)
base = np.asarray(explanation.base_values)
reconstructed = base + values.sum(axis=1)

error = reconstructed - expected_output
print("max abs error:", np.max(np.abs(error)))
print("mean abs error:", np.mean(np.abs(error)))
```

### Common output mismatch

For an XGBoost classifier, default TreeExplainer output may be a raw margin:

```python
raw_margin = model.predict(dmatrix, output_margin=True)
```

Comparing raw-margin SHAP reconstruction to `predict_proba` will fail conceptually even if both implementations are correct.

For probability explanations, configure:

```python
explainer = shap.TreeExplainer(
    model,
    data=background,
    feature_perturbation="interventional",
    model_output="probability",
)
```

### Do not immediately disable checks

`check_additivity=False` is appropriate only after:

- identifying a documented numerical or model-library limitation;
- quantifying the discrepancy;
- confirming it is acceptable for the use case;
- recording the decision.

It is not a fix for huge, non-finite, or wrong-unit values.

### Finite values and label-dependent loss

Require finite predictions, base values, contributions, and tolerances before trusting a reconstruction. NaN/Infinity cannot be repaired by larger tolerances. A tree-loss explanation may have callable `base_values`; evaluate `loss_explainer.expected_value(label)` for each row's encoded label before addition. Then check the exact model-specific loss, not just whether the call completed. See [workflows.md](workflows.md) for the explicit callable fallback and 0.52.0 sklearn loss limitations.

### Background size appears ineffective

Inspect `len(explainer.data)` or `len(explainer.masker.data)`. A bare 250-row frame can be internally sampled to 100 rows. Retain a selected sample with `shap.maskers.Independent(background, max_samples=len(background))`; changing the cap can change the baseline as well as runtime.

## Tree Model Problems

### Categorical splits

Support differs across XGBoost, LightGBM, CatBoost, and scikit-learn categorical configurations. SHAP 0.49 added categorical-split support in the C++ library, and 0.52 tightened unsupported categorical handling in GPU/sklearn paths.

XGBoost 3.4.1 defaults `enable_categorical=True`. SHAP 0.52.0 rejects that flag in the interventional path even on an all-numeric fixture. For a new numeric-only model, construct it with `enable_categorical=False` and validate predictions/explanations. For actual categorical models, retain the schema and use a supported path-dependent/raw or model-agnostic workflow; changing the flag or arbitrary integer coding is not a general fix. Tiny 3.4.1 numeric fixtures passed raw, probability, log-loss, `predict_proba`, multiclass, and interaction chec

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

