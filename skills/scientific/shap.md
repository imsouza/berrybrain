---
id: sci-shap
name: "Scientific: shap"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Explain and audit machine-learning predictions with SHAP. Use for selecting SHAP explainers and maskers, computing and validating feature attributions, handling multi-output explanations, and producing local or global SHAP visualizations."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "shap"
keywords:
  - "shap"
  - "explain"
  - "audit"
  - "machine"
  - "learning"
  - "predictions"
---

# SHAP

Use SHAP to describe how a fitted predictive model maps inputs to outputs. Work from the modern `shap.Explanation` API, make the explained output and background distribution explicit, and validate every explanation before interpreting it.

This skill is aligned with **SHAP 0.52.0** (released 2026-05-28). That release requires Python 3.12 or newer.

The maintained examples were checked on Python 3.12.10 with SHAP 0.52.0, NumPy 2.5.3, pandas 3.0.6, scikit-learn 1.9.1, and matplotlib 3.11.2. Native tests cover small tree, exact, permutation, partition, linear, additive, kernel, text, and constant-image games; additional numeric XGBoost 3.4.1 smoke checks cover raw, probability, loss, and interaction outputs. Reference snippets that require a project model, framework, or data are adaptation templates; optional pretrained/deep, GPU, and distributed integrations remain illustrative and require their own runtime validation.

## Operating Rules

1. Explain a fixed, evaluated model; do not use SHAP as a substitute for predictive validation.
2. Use held-out or clearly labeled analysis rows for explanations. Choose background rows only from an appropriate training or reference population.
3. State the explained output: regression value, raw margin, probability, log loss, logit, or another model method.
4. Prefer `shap.Explanation` objects and `explainer(X)`. Some specialized options still require `.shap_values(X)`, including deep ranked outputs, gradient sampling budgets, and Kernel SHAP `nsamples`. Preserve their output indexes and baselines explicitly.
5. For multi-output models, select one output before using tabular plots: `explanation[..., output_index]`.
6. Check `base_values + values.sum(...)` against the exact model output being explained.
7. Treat SHAP as a description of model behavior under a masking/background choice. It does not establish causality, fairness, recourse, or scientific mechanism.
8. Never silence an additivity failure until input shape, preprocessing, model version, output space, and row ordering have been checked.
9. Do not load untrusted pickle, joblib, model, or explainer artifacts; those formats can execute code during deserialization.

## Install

Create an isolated environment and pin the documented release:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install "shap[plots]==0.52.0"
```

`shap[plots]` installs the plotting dependencies. Add the fitted model's package at a version compatible with the project. For older Python compatibility, read [references/migration.md](references/migration.md) instead of silently installing a different SHAP release.

Confirm the environment before debugging an API mismatch:

```python
import platform
import shap

print("Python:", platform.python_version())
print("SHAP:", shap.__version__)
```

## Standard Workflow

### 1. Define the explanation target

Record:

- model and preprocessing version;
- exact callable or model method being explained;
- output name/index and units;
- evaluation rows;
- background/reference population;
- masker and explainer algorithm;
- SHAP and model-library versions.

For classifiers, decide whether the task needs raw margins or probabilities. Defaults differ by model family; never infer units from the plot color or sign.

### 2. Select an explainer and masker

Start with `shap.Explainer(model, masker)` when automatic dispatch is sufficient. Instantiate a specialized explainer when its assumptions or output controls matter.

| Situation | Preferred choice | Important constraint |
|---|---|---|
| Supported tree ensemble | `TreeExplainer` | `model_output="probability"` and `"log_loss"` require interventional masking and background data |
| Linear model | `LinearExplainer` | The masker determines interventional versus correlation-aware behavior |
| Small feature space | `ExactExplainer` | Cost grows quickly with unconstrained feature count |
| General tabular callable | `PermutationExplainer` | Budget at least one full forward/reverse permutation |
| Hierarchical feature groups, text, or image | `PartitionExplainer` | The partition tree changes the cooperative game |
| Differentiable neural network | `DeepExplainer` or `GradientExplainer` | Framework support, output shape, and background choice require testing |
| Legacy Kernel SHAP workflow | `KernelExplainer` | Usually much slower than model-specific methods |

Use the detailed decision guide in [references/explainers.md](references/explainers.md). Use [references/data-maskers.md](references/data-maskers.md) when features are correlated, structured, sparse, or semantically grouped.

### 3. Compute a modern `Explanation`

This complete binary-classification example uses an explicit background and selects output index 1. In the breast-cancer dataset, class 1 means **benign**, so positive SHAP values below increase predicted benign probability, not cancer risk. For another dataset, resolve the requested label through `model.classes_` and record its meaning before selecting an output index; column 1 is not universally the clinically positive event.

```python
import numpy as np
import shap
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

X, y = load_breast_cancer(as_frame=True, return_X_y=True)
X = X.astype(np.float32)  # Match sklearn forest prediction inputs.
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y,
    random_state=7,
)

model = RandomForestClassifier(
    n_estimators=200,
    min_samples_leaf=3,
    random_state=7,
    n_jobs=-1,
).fit(X_train, y_train)

X_test = X_test.iloc[:100]  # Predeclared held-out explanation subset.
background = shap.sample(X_train, 100, random_state=7)
explainer = shap.Explainer(model, background, algorithm="tree")
all_outputs = explainer(X_test)

# sklearn tree classifiers expose one output per class.
positive = all_outputs[..., 1]
assert positive.values.shape == X_test.shape

reconstructed = np.asarray(positive.base_values) + positive.values.sum(axis=1)
expected = model.predict_proba(X_test)[:, 1]
np.testing.assert_allclose(reconstructed, expected, rtol=1e-5, atol=1e-6)

shap.plots.beeswarm(positive, max_display=15)
shap.plots.waterfall(positive[0], max_display=15)
```

Output shape is model-dependent:

- one tabular output: `(samples, features)`;
- multiple tabular outputs: `(samples, features, outputs)`;
- multiple model inp

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

