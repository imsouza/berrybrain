---
id: sciref-shap-workflows
name: "Scientific Ref: SHAP Workflows"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (shap): SHAP Workflows"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "shap workflows"
keywords:
  - "shap"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
---

# SHAP Workflows

These workflows target SHAP 0.52.0 and the `shap.Explanation` API. Adapt model-specific code, but preserve the decisions about output, background, masking, validation, and reporting.

## Workflow 1: Reproducible Tabular Audit

### 1. Freeze the predictive context

Record:

- dataset and split identifiers;
- model and preprocessing artifact versions;
- package versions;
- feature schema and order;
- output method/index/name/units;
- background population and sampling rule;
- explainer/masker configuration;
- evaluation row selection.

Do not begin interpretation until predictive performance is acceptable for the intended population.

### 2. Build the background from training/reference data

```python
rng_seed = 7
background = shap.sample(X_train, 100, random_state=rng_seed)
```

Use a shared background for results intended for direct comparison.

### 3. Explain held-out rows

```python
explainer = shap.Explainer(
    model,
    background,
    algorithm="tree",
    seed=rng_seed,
)
all_outputs = explainer(X_test)
```

### 4. Select and validate the output

```python
if all_outputs.values.ndim == 3:
    explanation = all_outputs[..., class_index]
    expected = model.predict_proba(X_test)[:, class_index]
else:
    explanation = all_outputs
    expected = model.predict(X_test)

reconstructed = (
    np.asarray(explanation.base_values)
    + np.asarray(explanation.values).sum(axis=1)
)
max_abs_error = float(np.max(np.abs(reconstructed - expected)))
np.testing.assert_allclose(reconstructed, expected, rtol=1e-5, atol=1e-6)
```

This example is appropriate only when the explainer's selected output matches `predict` or `predict_proba`. For raw-margin models, compute the corresponding margin instead.

### 5. Move from global to local

```python
shap.plots.bar(explanation, max_display=20)
shap.plots.beeswarm(explanation, max_display=20)

global_importance = explanation.abs.mean(0)
top_index = int(np.argmax(global_importance.values))
top_feature = global_importance.feature_names[top_index]
shap.plots.scatter(explanation[:, top_feature], color=explanation)

shap.plots.waterfall(explanation[selected_row])
```

Select local rows using a documented criterion: high error, threshold proximity, representative quantile, or predeclared case.

### 6. Publish an audit record

Include:

- model metric table;
- global attribution distribution;
- selected feature relationships;
- local explanations with selection rules;
- background and masking sensitivity;
- additivity error;
- non-causal and non-fairness caveats.

## Workflow 2: Regression

```python
explainer = shap.Explainer(regressor, background)
explanation = explainer(X_test)

prediction = regressor.predict(X_test)
reconstructed = explanation.base_values + explanation.values.sum(axis=1)
np.testing.assert_allclose(reconstructed, prediction, rtol=1e-5, atol=1e-6)
```

State whether the target was transformed. If the model predicts log target values, SHAP values are in log-target units unless the explained callable reverses the transform.

For transformed targets, choose one:

- explain the model's native output and label units accurately;
- wrap the inverse-transformed prediction in a model-agnostic callable and explain that output;
- provide both and explain why additive decompositions differ.

## Workflow 3: Binary Classification

Binary model outputs vary:

- scikit-learn tree classifiers commonly return one output per class;
- XGBoost/LightGBM raw tree outputs commonly return one margin;
- a model-agnostic `predict_proba` callable returns two columns.

### Explicit probability-space tree explanation

```python
explainer = shap.TreeExplainer(
    model,
    data=background,
    feature_perturbation="interventional",
    model_output="probability",
)
all_outputs = explainer(X_test)

if all_outputs.values.ndim == 3:
    positive = all_outputs[..., positive_class_index]
else:
    positive = all_outputs

expected = model.predict_proba(X_test)[:, positive_class_index]
reconstructed = positive.base_values + positive.values.sum(axis=1)
np.testing.assert_allclose(reconstructed, expected, rtol=1e-5, atol=1e-6)
```

If the model family exposes only one positive-class probability output, do not attempt a second class slice.

### Threshold-focused analysis

```python
probability = model.predict_proba(X_test)[:, positive_class_index]
distance = np.abs(probability - decision_threshold)
near_threshold = np.argsort(distance)[:25]

shap.plots.heatmap(positive[near_threshold])
```

Threshold proximity is a legitimate predeclared selection rule. It does not make SHAP a recourse method.

## Workflow 4: Multiclass or Multi-Output Models

```python
all_outputs = explainer(X_test)
print(all_outputs.values.shape)
print(all_outputs.output_names)

per_output = {
    str(name): all_outputs[..., index]
    for index, name in enumerate(all_outputs.output_names)
}
```

For each output:

1. validate against the corresponding model output;
2. generate its own global summary;
3. keep axis units and scales explicit;
4. report class prevalence and performance.

Do not:

- use `all_outputs[class_index]` to select an output;
- assume old list-of-arrays behavior;
- average signed attributions across classes;
- compare classes after using different backgrounds.

For many outputs, explain only predeclared or top-ranked outputs:

```python
selected = explainer(
    X_subset,
    outputs=shap.Explanation.argsort.flip[:5],
)
```

The `outputs` option is explainer-dependent. Verify selected indexes/names, especially when top outputs can vary by row.

## Workflow 5: Pipelines and Feature Names

Choose whether to explain raw or transformed features.

### Transformed-space, model-specific explanation

```python
X_train_t = preprocessor.transform(X_train)
X_test_t = preprocessor.transform(X_test)
feature_names = preprocessor.get_feature_names_out()

explainer = shap.Explainer(
    model,
    X_train_t[:100],
    feature_names=feature_names.tolist(),
)
explanation = explainer(X_test_t)
```

Benefits: speed and specialized explainer support.

Costs: one source feature may expand into many encoded columns. Aggregate one-hot levels only after preserving signed local contributions and documenting the aggregation:

```python
source_group_value = explanation.values[:, source_column_indices].sum(axis=1)
```

Sum signed values for a local additive group. For global importance, decide whether the quantity is:

- mean absolute value of the summed group; or
- sum of each encoded column

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

