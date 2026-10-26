---
id: sciref-shap-explainers
name: "Scientific Ref: SHAP Explainers"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (shap): SHAP Explainers"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "shap explainers"
keywords:
  - "shap"
  - "explainers"
  - "specialized"
  - "scientific"
  - "reference"
---

# SHAP Explainers

This reference targets SHAP 0.52.0. Prefer the callable interface (`explanation = explainer(X)`) so results retain values, baselines, data, feature names, and output names in a `shap.Explanation`.

## Selection Checklist

Before choosing an explainer, answer:

1. What exact callable or model output is being explained?
2. Is the model natively supported by a specialized explainer?
3. What does "missing" mean for each input feature?
4. Are features independent, correlated, grouped, sequential, or spatial?
5. How many model evaluations are affordable per row?
6. Is the output scalar or multi-output?
7. Is an exact result required under the chosen game, or is a sampled estimate acceptable?

## Recommended Decision Path

| Model/input | First choice | Alternative | Main risk |
|---|---|---|---|
| Supported tree ensemble | `TreeExplainer` | `GPUTreeExplainer` (experimental) | Output units and feature-dependence semantics |
| Linear model | `LinearExplainer` | `ExactExplainer` | Correlation assumptions |
| Small tabular feature set | `ExactExplainer` | `PermutationExplainer` | Exponential cost without a partition tree |
| General tabular callable | `PermutationExplainer` | `PartitionExplainer`, `KernelExplainer` | Evaluation cost and off-manifold masks |
| Hierarchically grouped inputs | `PartitionExplainer` | `PermutationExplainer` with `Partition` masker | Attributions are Owen values for the constrained game |
| Differentiable TensorFlow/PyTorch model | `DeepExplainer` or `GradientExplainer` | `PartitionExplainer` | Operator support, background, and output shape |
| Text or image callable | `PartitionExplainer` with domain masker | Framework-specific deep explainer | Masking semantics dominate interpretation |

## `shap.Explainer`

`shap.Explainer` combines a model, masker, link, and algorithm. With `algorithm="auto"`, it returns a compatible specialized subclass.

```python
explainer = shap.Explainer(
    model,
    masker=background,
    algorithm="auto",
    output_names=output_names,
    feature_names=feature_names,
    seed=7,
)
explanation = explainer(X_eval)
```

The 0.52.0 selector advertises `auto`, `permutation`, `partition`, `tree`, `linear`, `deep`, `exact`, and `additive`. However, its `algorithm="deep"` dispatch forwards unsupported keywords to `DeepExplainer` and raises `TypeError`; construct `shap.DeepExplainer(model, background)` directly. `auto` is not a general framework detector.

Use the auto-selector when:

- the model/masker pair is conventional;
- default output semantics are acceptable;
- no algorithm-specific parameter is needed.

Instantiate the specialized class when:

- tree `model_output` or `feature_perturbation` must be explicit;
- a particular approximation or evaluation budget is part of the analysis;
- a framework-specific deep model requires a precise input/layer form.

Passing a background matrix is shorthand for a standard tabular masker. Prefer an explicit masker when its semantics need to appear in an audit record.

## `TreeExplainer`

Common constructor arguments (the deprecated `approximate` parameter and unused link controls are intentionally omitted):

```python
shap.TreeExplainer(
    model,
    data=None,
    model_output="raw",
    feature_perturbation="auto",
    feature_names=None,
)
```

Supported families include XGBoost, LightGBM, CatBoost, PySpark trees, and most scikit-learn tree models. Support varies by model version and categorical configuration, so test a small batch after dependency changes.

### Feature perturbation

`feature_perturbation` defines how hidden features are integrated:

- `"interventional"` requires background data. Runtime scales approximately linearly with background size.
- `"tree_path_dependent"` uses training counts stored in tree leaves and does not require a separate background.
- `"auto"` uses interventional semantics when `data` is supplied and tree-path-dependent semantics otherwise. This has been the default since 0.47.

These options answer different questions and can allocate credit differently for dependent features. Neither turns an ordinary predictive model into a causal model.

### Output space

`model_output` can be:

- `"raw"`: model-specific raw tree output;
- `"probability"`: transformed probability output;
- `"log_loss"`: a model-specific loss transform; for supported binary margin models this is negative log likelihood, while squared-error objectives use squared loss;
- a supported model method name such as `"predict_proba"`.

`"probability"` and `"log_loss"` currently require `feature_perturbation="interventional"` and background data.

Raw output is model-dependent:

- regression commonly uses the predicted target value;
- XGBoost binary classification commonly uses a margin/log-odds value;
- scikit-learn tree classifiers commonly expose one probability output per class.

Always inspect shape and verify the additive reconstruction against the exact model output.

### Calling and validation

```python
explainer = shap.TreeExplainer(
    model,
    data=background,
    feature_perturbation="interventional",
    model_output="probability",
)
all_outputs = explainer(X_eval)
class_exp = all_outputs[..., class_index]

reconstructed = class_exp.base_values + class_exp.values.sum(axis=1)
expected = model.predict_proba(X_eval)[:, class_index]
np.testing.assert_allclose(reconstructed, expected, rtol=1e-5, atol=1e-6)
```

The built-in tree additivity check applies to raw output paths; explicitly validate probability and loss reconstructions. Loss baselines can be label-dependent callables: see the concrete loss workflow in [workflows.md](workflows.md). A bare DataFrame background is capped at 100 rows; retain a larger selected sample with `data=shap.maskers.Independent(background, max_samples=len(background))` and record the effective size.

### Approximate tree values

Do not pass `approximate` to the constructor. If the speed/quality trade-off is intentional:

```python
approx_exp = explainer(X_eval, approximate=True)
```

This uses a single-ordering approximation associated with Saabas values. It does not retain the consistency guarantee of Tree SHAP and can over-weight lower tree splits. Label the result as approximate.

### Interaction values

Use a separate **raw, tree-path-dependent** explainer for supported tree interactions:

```python
interaction_explainer = shap.TreeExplainer(
    model, feature_perturbation="tree_path_dependent", model_output="raw",
)
interaction =

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

