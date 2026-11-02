---
id: sciref-statsmodels-discrete-choice
name: "Scientific Ref: Discrete Choice Models Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (statsmodels): Discrete Choice Models Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "statsmodels discrete choice"
  - "discrete choice models reference"
keywords:
  - "statsmodels"
  - "discrete"
  - "choice"
  - "specialized"
  - "scientific"
  - "reference"
---

# Discrete Choice Models Reference

This document provides comprehensive guidance on discrete choice models in statsmodels, including binary, multinomial, count, and ordinal models.

## Overview

Discrete choice models handle outcomes that are:
- **Binary**: 0/1, success/failure
- **Multinomial**: Multiple unordered categories
- **Ordinal**: Ordered categories
- **Count**: Non-negative integers

These models use likelihood-based estimation. Independence and sampling assumptions are model-specific: conditional models condition out group intercepts, while clustered sampling needs an appropriate covariance/design. Check finite estimates, design rank, convergence and separation; convergence alone does not establish identifiability.

## Binary Models

### Logit (Logistic Regression)

Uses logistic distribution for binary outcomes.

**When to use:**
- Binary classification (yes/no, success/failure)
- Probability estimation for binary outcomes
- Interpretable odds ratios

**Model**: P(Y=1|X) = 1 / (1 + exp(-Xβ))

```python
import statsmodels.api as sm
from statsmodels.discrete.discrete_model import Logit

# Prepare data
X = sm.add_constant(X_data)

# Fit model
model = Logit(y, X)
results = model.fit()

print(results.summary())
```

**Interpretation:**
```python
import numpy as np

# Odds ratios
odds_ratios = np.exp(results.params)
print("Odds ratios:", odds_ratios)

# For 1-unit increase in X, odds multiply by exp(β)
# OR > 1: increases odds of success
# OR < 1: decreases odds of success
# OR = 1: no effect

# Confidence intervals for odds ratios
odds_ci = np.exp(results.conf_int())
print("Odds ratio 95% CI:")
print(odds_ci)
```

**Marginal effects:**
```python
# Average marginal effects (AME)
marginal_effects = results.get_margeff(at='overall')
print(marginal_effects.summary())

# Marginal effects at means (MEM)
marginal_effects_mem = results.get_margeff(at='mean', method='dydx')

# Marginal effects at representative values
marginal_effects_custom = results.get_margeff(at='mean',
                                              atexog={1: 1, 2: 5})  # Zero-based design-column indices
```

**Predictions:**
```python
# Predicted probabilities
probs = results.predict(X)

# Binary predictions (0.5 threshold)
predictions = (probs > 0.5).astype(int)

# Custom threshold
threshold = 0.3
predictions_custom = (probs > threshold).astype(int)

# For new data
X_new = sm.add_constant(X_new_data, has_constant="add")
new_probs = results.predict(X_new)
```

**Model evaluation:**
```python
from sklearn.metrics import (classification_report, confusion_matrix,
                             roc_auc_score, roc_curve)

# Classification report
print(classification_report(y, predictions))

# Confusion matrix
print(confusion_matrix(y, predictions))

# AUC-ROC
auc = roc_auc_score(y, probs)
print(f"AUC: {auc:.4f}")

# Pseudo R-squared
print(f"McFadden's Pseudo R²: {results.prsquared:.4f}")
```

### Probit

Uses normal distribution for binary outcomes.

**When to use:**
- Binary outcomes
- Prefer normal distribution assumption
- Field convention (econometrics often uses probit)

**Model**: P(Y=1|X) = Φ(Xβ), where Φ is standard normal CDF

```python
from statsmodels.discrete.discrete_model import Probit

model = Probit(y, X)
results = model.fit()

print(results.summary())
```

**Comparison with Logit:**
- Probit and Logit usually give similar results
- Probit: symmetric, based on normal distribution
- Logit: slightly heavier tails, easier interpretation (odds ratios)
- Coefficients not directly comparable (scale difference)

```python
# Marginal effects are comparable
logit_me = logit_results.get_margeff().margeff
probit_me = probit_results.get_margeff().margeff

print("Logit marginal effects:", logit_me)
print("Probit marginal effects:", probit_me)
```

## Multinomial Models

### MNLogit (Multinomial Logit)

For unordered categorical outcomes with 3+ categories.

**When to use:**
- Multiple unordered categories (e.g., transportation mode, brand choice)
- No natural ordering among categories
- Need probabilities for each category

**Model**: P(Y=j|X) = exp(Xβⱼ) / Σₖ exp(Xβₖ)

```python
from statsmodels.discrete.discrete_model import MNLogit

# y should be integers 0, 1, 2, ... for categories
model = MNLogit(y, X)
results = model.fit()

print(results.summary())
```

**Interpretation:**
```python
# One category is reference (usually category 0)
# Coefficients represent log-odds relative to reference

# For category j vs reference:
# exp(β_j) = odds ratio of category j vs reference

# Predicted probabilities for each category
probs = results.predict(X)  # Shape: (n_samples, n_categories)

# Most likely category
predicted_categories = np.asarray(probs).argmax(axis=1)
```

**Relative risk ratios:**
```python
# Exponentiate coefficients for relative risk ratios
import numpy as np
import pandas as pd

# Get parameter names and values
params_df = pd.concat({
    'coef': pd.DataFrame(results.params),
    'RRR': pd.DataFrame(np.exp(results.params))
}, axis=1)
print(params_df)
```

### Conditional Logit

For choice models where alternatives have characteristics.

**When to use:**
- Alternative-specific regressors (vary across choices)
- Panel data with choices
- Discrete choice experiments

```python
from statsmodels.discrete.conditional_models import ConditionalLogit

# Long format, binary choice indicator, no constant in X_alternatives.
# One group per choice occasion (not one person across multiple occasions).
model = ConditionalLogit(y_choice, X_alternatives, groups=choice_set_id)
results = model.fit()
```

## Count Models

### Poisson

Standard model for count data.

**When to use:**
- Count outcomes (events, occurrences)
- Rare events
- Mean ≈ variance

**Model**: P(Y=k|X) = exp(-λ) λᵏ / k!, where log(λ) = Xβ

```python
from statsmodels.discrete.discrete_model import Poisson

model = Poisson(y_counts, X)
results = model.fit()

print(results.summary())
```

**Interpretation:**
```python
# Rate ratios (incident rate ratios)
rate_ratios = np.exp(results.params)
print("Rate ratios:", rate_ratios)

# For 1-unit increase in X, expected count multiplies by exp(β)
```

**Check overdispersion:**
```python
# Dispersion concerns the conditional variance, not raw variance/mean.
mu = results.predict(X)
pearson_dispersion = np.sum((y_counts - mu)**2 / mu) / results.df_resid
print(f"Pearson dispersion: {pearson_dispersion:.2f}")
# A screening statistic: inspect mean misspecification, exposure and dependence.
```

**With offset (for rate

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

