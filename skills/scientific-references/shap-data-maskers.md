---
id: sciref-shap-data-maskers
name: "Scientific Ref: Background Data and Maskers"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (shap): Background Data and Maskers"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "shap maskers"
  - "background data and maskers"
keywords:
  - "shap"
  - "maskers"
  - "specialized"
  - "scientific"
  - "reference"
  - "background"
---

# Background Data and Maskers

SHAP values are defined relative to a cooperative game. The background data and masker define what hidden features mean and therefore help define the question being answered. They are not merely performance parameters.

## Start With the Estimand

For a row `x`, an explanation decomposes a model output relative to a baseline:

```text
explained output = base value + sum(feature attributions)
```

The baseline and attributions depend on the reference distribution used when features are hidden.

Examples of distinct questions:

- **Population-relative:** Why is this prediction different from the training population?
- **Current-production-relative:** Why is it different from recent production traffic?
- **Control-relative:** Why is it different from a clinically meaningful reference cohort?
- **Case-relative:** Why do two otherwise comparable cases receive different scores?

These questions can produce different baselines, signs, magnitudes, and rankings. State the intended question before sampling background rows.

## Background Selection

Use background data that:

- comes from the population relevant to the explanation question;
- passed the same preprocessing and schema validation as explained rows;
- excludes targets, post-outcome information, identifiers, and leakage fields;
- includes valid values and missingness patterns;
- is independent of the specific examples selected for storytelling;
- is versioned or reproducibly sampled.

Do not use:

- the explained row itself as the only background unless a pairwise contrast is explicitly intended;
- the test target to choose "representative" rows;
- the full dataset automatically;
- synthetic mean rows that violate categorical, compositional, or physiological constraints;
- production rows collected after an outcome if that changes the interpretation.

## Size and Convergence

Larger backgrounds increase cost for interventional tree, deep, kernel, and permutation methods. `Independent` and `Partition` default to at most 100 tabular background rows, including when `TreeExplainer` wraps a bare frame. Increasing `shap.sample(..., 250)` alone therefore does not run a 250-row background experiment. Use `shap.maskers.Independent(background, max_samples=len(background))`, pass that to the explainer, and inspect its effective background before reporting convergence.

Treat size as an empirical convergence choice:

1. Choose a reproducible candidate pool.
2. Compare baselines and top attribution summaries at increasing sizes, such as 25, 50, 100, and 250.
3. Repeat with multiple seeds when random sampling is used.
4. Stop when conclusions are stable enough for the use case.
5. Record the selected rows or a deterministic selection rule.

`shap.sample` samples without replacement:

```python
background = shap.sample(X_train, 100, random_state=7)
```

For heterogeneous populations, stratified sampling may be more appropriate:

```python
background = (
    training_frame.groupby("site", group_keys=False)
    .sample(n=20, random_state=7)
    .drop(columns="site")
)
```

Only stratify on information legitimately available at the prediction time and relevant to the reference population.

## Tabular Maskers

### `Independent`

```python
masker = shap.maskers.Independent(background, max_samples=100)
```

Hidden features are replaced by values from background rows and integrated over that marginal reference distribution.

Use when:

- interventional/marginal semantics match the question;
- the model accepts independently combined columns;
- a general callable needs a standard tabular masker.

Risk: combining observed and background columns can create off-manifold or impossible rows when features are dependent.

### `Partition`

```python
masker = shap.maskers.Partition(
    background,
    max_samples=100,
    clustering="correlation",
)
```

`Partition` constrains coalitions using a hierarchical feature tree. With `PartitionExplainer`, this produces Owen values for the constrained game.

Use when:

- feature groups should enter together;
- a hierarchy is scientifically meaningful;
- correlated or redundant features need grouped interpretation;
- text tokens or image regions have structure.

`clustering` can be:

- a SciPy pairwise-distance metric string; SHAP recommends `"correlation"` for common tabular use;
- a precomputed linkage matrix encoding a domain-defined hierarchy.

Correlation clustering is descriptive, not causal. Review the tree rather than assuming automatically derived groups are scientifically valid.

### `Impute`

```python
masker = shap.maskers.Impute(background, method="linear")
```

`Impute` estimates hidden features conditional on observed features. It is commonly paired with `LinearExplainer` for correlation-aware allocations.

Conditional games can give attribution to a feature the model does not directly use because that feature carries information about a used feature. Do not interpret such an attribution as a model coefficient or intervention effect.

### `Fixed` and composite maskers

- `Fixed`: leaves an input unchanged; useful for fixed labels or auxiliary arguments.
- `Composite`: joins maskers for multiple model inputs only when their row counts, call signatures, and clustering are compatible; this is not a universal multimodal adapter.
- `FixedComposite`: returns both masked and original inputs.
- `OutputComposite`: combines masking with a model output used by an explanation algorithm.

Use these only after verifying the model's full call signature with a one-row test.

## Domain Maskers

### Text

```python
masker = shap.maskers.Text(tokenizer)
```

Text masking respects tokenizer boundaries and can create a token hierarchy for `PartitionExplainer`. The mask token, collapse behavior, and tokenizer special tokens affect the explanation.

### Image

```python
masker = shap.maskers.Image("inpaint_telea", image_shape)
```

Supported masking approaches include blurring, inpainting, and constant values. Each asks a different counterfactual question. Inpainting may create plausible local texture but does not guarantee an in-distribution image.

See [modalities.md](modalities.md) for full workflows.

## Correlated and Redundant Features

There is no universally correct single-feature allocation when inputs share information.

### Marginal/interventional allocation

An independent masker asks how model output changes while integrating hidden features over a marginal reference. It can expos

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

