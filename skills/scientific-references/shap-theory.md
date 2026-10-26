---
id: sciref-shap-theory
name: "Scientific Ref: SHAP Theory and Interpretation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (shap): SHAP Theory and Interpretation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "shap theory"
  - "shap theory and interpretation"
keywords:
  - "shap"
  - "theory"
  - "specialized"
  - "scientific"
  - "reference"
---

# SHAP Theory and Interpretation

SHAP applies Shapley-style credit allocation to model explanations. The numerical result is defined by more than the fitted model: it also depends on the model output, background distribution, masking rule, and any coalition constraints.

## Additive Explanation

For one scalar model output and one row `x`, SHAP constructs an additive decomposition:

```text
f_explained(x) = base_value + sum_i phi_i(x)
```

- `f_explained` is the exact output selected for explanation.
- `base_value` is the expected output under the explainer's reference game.
- `phi_i` is the attribution assigned to feature `i`.

For modern tabular `shap.Explanation` objects:

```python
reconstructed = explanation.base_values + explanation.values.sum(axis=1)
```

The equation is meaningful only when the output units are known. A raw margin, probability, log loss, and logit are different quantities.

## Cooperative-Game Formulation

Let `F` be the set of features and `v(S)` the value assigned to coalition `S`. A Shapley value for feature `i` is:

```text
phi_i =
  sum over S subset of F \ {i}
  [ |S|! (|F|-|S|-1)! / |F|! ]
  * [v(S union {i}) - v(S)]
```

This averages the marginal contribution of `i` over all feature orderings.

In machine learning, defining `v(S)` is the hard part because a model normally requires all inputs. The masker and background distribution specify how hidden features are integrated or imputed.

## What the Axioms Mean

Classic Shapley values satisfy:

- **Efficiency:** all feature values sum to the coalition payoff difference.
- **Symmetry:** interchangeable players receive equal credit.
- **Dummy/null player:** a player with no marginal contribution receives zero.
- **Additivity:** values for combined games are sums of values for component games.

The SHAP paper describes related properties for additive feature-attribution methods:

- **Local accuracy:** the additive explanation reconstructs the selected output.
- **Missingness:** absent simplified inputs receive zero attribution under the formulation.
- **Consistency:** if a feature's marginal contribution increases for every coalition, its attribution does not decrease.

These are mathematical allocation properties. They do **not** mean:

- ethical or legal fairness;
- causal correctness;
- robustness to distribution shift;
- truthfulness of the fitted model;
- stability under a different background or masker.

Avoid calling SHAP values "fair" without specifying that the term refers only to a cooperative-game allocation axiom.

## The Value Function Is Part of the Result

Common tabular games include:

### Marginal/interventional game

Hidden features are sampled from a background distribution independently of the observed features.

Conceptually:

```text
v(S) = E_background[f(x_S, X_not_S)]
```

Advantages:

- clear reference population;
- preserves the dummy property with respect to direct model use;
- straightforward model-agnostic masking.

Limitations:

- can evaluate unrealistic combinations;
- can be sensitive to the selected background;
- "interventional" in the API name does not make the resulting predictive explanation a causal effect.

### Conditional game

Hidden features are drawn from a distribution conditional on observed features:

```text
v(S) = E[f(X) | X_S = x_S]
```

Advantages:

- can stay closer to the observed data manifold;
- incorporates statistical dependence.

Limitations:

- requires estimating conditional distributions;
- can assign credit to a feature the model does not directly use;
- dependence can be mistaken for causation;
- estimates can be unstable in sparse regions.

### Partitioned game

Only coalitions compatible with a hierarchy are considered. The resulting allocations are Owen values.

Advantages:

- respects semantic or statistical groups;
- makes structured high-dimensional problems more tractable;
- reduces arbitrary competition among related features.

Limitation: the hierarchy is an assumption and changes the game.

There is no universal answer to "the SHAP value" without specifying the game.

## Background and Baseline

The base value is the reference-game expectation, not automatically:

- the overall target mean;
- the model intercept;
- class prevalence;
- a neutral patient/customer;
- a decision threshold.

Different backgrounds can change:

- base values;
- signed local attributions;
- mean absolute global rankings;
- cohort comparisons.

Treat background sensitivity as a substantive analysis, not just a runtime check.

## Output Scale

SHAP values use the additive scale selected by the explainer.

Examples:

- regression prediction in target units;
- binary tree margin in log-odds;
- class probability;
- per-row log loss;
- transformed output under a link function.

A display transform such as `link="logit"` on a force plot changes labels, not the computed SHAP game. If probability-space additivity is required for supported trees, configure `TreeExplainer(model_output="probability", feature_perturbation="interventional", data=...)`.

Do not compare mean absolute SHAP magnitudes across models or outputs on different scales.

## Local and Global Quantities

Local attribution:

```text
phi_i(x)
```

Global mean absolute attribution:

```text
E_x[abs(phi_i(x))]
```

Mean absolute attribution:

- discards direction;
- depends on the evaluated sample distribution;
- is not normalized predictive performance;
- is not a causal effect size.

Mean signed attribution can cancel heterogeneous effects. Plot the distribution before summarizing.

## Exact and Approximate Algorithms

Unconstrained exact Shapley computation grows exponentially with feature count. SHAP uses model-specific algorithms or sampling:

- **Tree SHAP:** exploits tree structure and is exact for the selected tree game.
- **Linear SHAP:** closed-form or transformation-based allocation for supported linear games.
- **ExactExplainer:** optimized enumeration for small or hierarchically constrained inputs.
- **PermutationExplainer:** averages forward/reverse feature orderings.
- **KernelExplainer:** estimates values through a weighted linear regression over coalitions.
- **DeepExplainer:** combines DeepLIFT-style rules with multiple background samples.
- **GradientExplainer:** uses expected gradients.
- **PartitionExplainer:** exploits a coalition hierarchy.

"Exact" always means exact under a specified output, background, masker, and coalition game.

## Interaction Values

Tree SHAP can decom

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

