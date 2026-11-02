---
id: sciref-shap-migration
name: "Scientific Ref: SHAP Migration and Compatibility"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (shap): SHAP Migration and Compatibility"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "shap migration"
  - "shap migration and compatibility"
keywords:
  - "shap"
  - "migration"
  - "specialized"
  - "scientific"
  - "reference"
---

# SHAP Migration and Compatibility

This guide covers migration to SHAP 0.52.0 and the modern `shap.Explanation` API.

## Version Baseline

| SHAP release | Python requirement | Important compatibility note |
|---|---|---|
| 0.52.0 | `>=3.12` | Current release; NumPy `>=2`; native bindings moved to nanobind/scikit-build-core |
| 0.51.0 | `>=3.11` | Latest release suitable for Python 3.11 |
| 0.50.0 | `>=3.11` | First release after Python 3.9/3.10 support ended |
| 0.49.1 | `>=3.9` | Last release line supporting Python 3.9 and 3.10; fixes the broken 0.49.0 publication |

For a new environment:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install "shap[plots]==0.52.0"
```

For a project that cannot move off Python 3.11:

```bash
uv pip install "shap[plots]==0.51.0"
```

For Python 3.9 or 3.10, upgrade Python if possible. If temporarily constrained:

```bash
uv pip install "shap[plots]==0.49.1"
```

Do not claim 0.49.1 behavior is identical to 0.52. Read the release notes and test model-library compatibility.

## Major Changes Affecting Existing Code

### 0.45.0

- Python 3.8 support ended.
- Multi-output SHAP values changed from a list to a NumPy array with the output dimension last.
- Deprecated `feature_dependence` parameters were removed from `TreeExplainer` and `LinearExplainer`.
- Python 3.12 support was added.

### 0.46.0

- NumPy 2, Keras 3, and TensorFlow 2.16 support was added.
- The deprecated `auto_size_plot` argument to `summary_plot` was removed.

### 0.47.0

- `TreeExplainer(feature_perturbation="auto")` became the default behavior: interventional when background data are supplied, tree-path-dependent otherwise.
- Passing `approximate` to the `TreeExplainer` constructor was deprecated; pass it when calling the explainer.
- Plotting APIs continued moving toward `Explanation` inputs and returned axes.
- Legacy bar plotting gained deprecation guidance.

### 0.49.x

- 0.49.1 repaired the 0.49.0 release publication.
- 0.49.x was the final line supporting Python 3.9 and 3.10.
- C++ categorical-split support expanded.

### 0.50.0–0.51.0

- Python 3.11 became the minimum.
- Type coverage and tree/path-dependent behavior continued to improve.

### 0.52.0

- Python 3.12 became the minimum.
- NumPy 2 became a core minimum requirement.
- Native bindings moved from legacy extension/setup.py machinery to nanobind with scikit-build-core and CMake.
- Tree/GPU fixes improved missing-value routing, vector-valued XGBoost base scores, and multiclass additivity.
- `TreeExplainer` gained a pandas nullable-dtype fix.
- Plot and documentation examples continued moving to the modern API.

### Verified 0.52.0 traps

- Tabular backgrounds are capped at 100 by default; set the masker's `max_samples` explicitly for larger experiments.
- `Explainer(algorithm="deep")` fails through unsupported dispatch keywords; use `DeepExplainer` directly.
- Kernel SHAP defaults to `l1_reg="num_features(10)"`; declare regularization and sampling budgets.
- Tree interactions require the raw, tree-path-dependent path; do not reuse a probability/interventional explainer.
- Loss baselines may be callable and label-dependent, and classifier loss transforms require model-specific verification.
- A one-output deep array can retain a final singleton output axis; `ranked_outputs` belongs on `.shap_values`, not the constructor.

## Explanation API Migration

### Compute explanations

Legacy:

```python
values = explainer.shap_values(X)
```

Modern:

```python
explanation = explainer(X)
values = explanation.values
base_values = explanation.base_values
```

Keep the `Explanation` object instead of immediately extracting `.values`; plots and slicing use its metadata.

### Base values

Legacy:

```python
base_value = explainer.expected_value
```

Modern:

```python
base_values = explanation.base_values
```

`base_values` can be scalar, per-row, per-output, or per-row/per-output. Inspect shape.

### Multi-output values

Pre-0.45 code often assumed a list:

```python
positive_values = values[1]
```

Modern tabular code uses the final output axis:

```python
positive_exp = explanation[..., 1]
positive_values = explanation.values[..., 1]
```

`explanation[1]` selects the second sample, not the second class.

For scikit-learn `RandomForestClassifier`, a typical shape is:

```text
(samples, features, classes)
```

For XGBoost binary classification with default raw output, a typical shape is:

```text
(samples, features)
```

Do not hard-code a binary shape across model families.

## Plot Migration

### Summary plot to beeswarm

Legacy:

```python
shap.summary_plot(values, X)
```

Modern:

```python
shap.plots.beeswarm(explanation)
```

### Summary bar to bar

Legacy:

```python
shap.summary_plot(values, X, plot_type="bar")
```

Modern:

```python
shap.plots.bar(explanation)
```

### Dependence plot to scatter

Legacy:

```python
shap.dependence_plot("age", values, X, interaction_index="bmi")
```

Modern:

```python
shap.plots.scatter(
    explanation[:, "age"],
    color=explanation[:, "bmi"],
)
```

### Force plot

Legacy:

```python
shap.force_plot(
    explainer.expected_value,
    values[row_index],
    X.iloc[row_index],
)
```

Modern:

```python
shap.plots.force(explanation[row_index])
```

### Local waterfall

Legacy code often manually built an `Explanation` from arrays. Modern:

```python
shap.plots.waterfall(explanation[row_index])
```

### Image plot

Legacy:

```python
shap.image_plot(values, images)
```

Modern:

```python
shap.plots.image(explanation)
```

### Decision plot

`shap.plots.decision` remains largely array-oriented:

```python
shap.plots.decision(
    base_value,
    values,
    features=X_display,
    feature_names=feature_names,
)
```

Select one output and compatible base value before calling it.

## TreeExplainer Migration

### `feature_dependence`

Removed:

```python
shap.TreeExplainer(model, feature_dependence="independent")
```

Current:

```python
shap.TreeExplainer(
    model,
    data=background,
    feature_perturbation="interventional",
)
```

Or:

```python
shap.TreeExplainer(
    model,
    feature_perturbation="tree_path_dependent",
)
```

These are not mechanical synonyms for every old setting. Reconfirm the intended game and baseline.

### Default feature perturbation

Old code could rely on an interventional default. Current `"auto"` behavior depends on whether data are passed.

Make reproducibility explicit:

```python
explainer = shap.TreeExplainer(
    model,
    d

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

