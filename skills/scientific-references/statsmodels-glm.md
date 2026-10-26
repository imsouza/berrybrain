---
id: sciref-statsmodels-glm
name: "Scientific Ref: Generalized Linear Models (GLM) Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (statsmodels): Generalized Linear Models (GLM) Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "statsmodels glm"
  - "generalized linear models (glm) reference"
keywords:
  - "statsmodels"
  - "glm"
  - "specialized"
  - "scientific"
  - "reference"
  - "generalized"
  - "linear"
---

# Generalized Linear Models (GLM) Reference

This document provides comprehensive guidance on generalized linear models in statsmodels, including families, link functions, and applications.

## Overview

GLMs extend linear regression to non-normal response distributions through:
1. **Distribution family**: Specifies the conditional distribution of the response
2. **Link function**: Maps the conditional mean to the linear predictor; the inverse link maps back
3. **Variance function**: Relates variance to the mean

**General form**: g(μ) = Xβ, where g is the link function and μ = E(Y|X)

## When to Use GLM

- **Binary outcomes**: Logistic regression (Binomial family with logit link)
- **Count data**: Poisson or Negative Binomial regression
- **Positive continuous data**: Gamma or Inverse Gaussian
- **Conditional mean/variance structure**: Choose family from the response mechanism, not a normality test on the marginal response
- **Link functions**: Need non-linear relationship between predictors and response scale

Formula predictions take raw named columns; array predictions take the exact training design. Do not reuse a result from a different family in a later fragment. Use positive finite exposure, pass `exposure=e` or `offset=np.log(e)` (not both), and supply new exposure/offset when predicting new rows. Binomial proportions need trial counts (`var_weights=n`) or a two-column `[successes, failures]` response; arbitrary proportions are not Bernoulli observations.

## Distribution Families

### Binomial Family

For binary outcomes (0/1) or proportions (k/n).

**When to use:**
- Binary classification
- Success/failure outcomes
- Proportions or rates

**Common links:**
- Logit (default): log(μ/(1-μ))
- Probit: Φ⁻¹(μ)
- Log: log(μ)

```python
import statsmodels.api as sm
import statsmodels.formula.api as smf

# Binary logistic regression
model = sm.GLM(y, X, family=sm.families.Binomial())
results = model.fit()

# Formula API
results = smf.glm('success ~ x1 + x2', data=df,
                  family=sm.families.Binomial()).fit()

# Access predictions (probabilities)
probs = results.predict(new_df)  # Raw named predictors after a formula fit

# Classification (0.5 threshold)
predictions = (probs > 0.5).astype(int)
```

**Interpretation:**
```python
import numpy as np

# Odds ratios (for logit link)
odds_ratios = np.exp(results.params)
print("Odds ratios:", odds_ratios)

# For 1-unit increase in x, odds multiply by exp(beta)
```

### Poisson Family

For count data (non-negative integers).

**When to use:**
- Count outcomes (number of events)
- Rare events
- Rate modeling (with offset)

**Common links:**
- Log (default): log(μ)
- Identity: μ
- Sqrt: √μ

```python
# Poisson regression
model = sm.GLM(y, X, family=sm.families.Poisson())
results = model.fit()

# With exposure/offset for rates
# If modeling rate = counts/exposure
model = sm.GLM(y, X, family=sm.families.Poisson(),
               offset=np.log(exposure))
results = model.fit()

# Interpretation: exp(beta) = multiplicative effect on expected count
import numpy as np
rate_ratios = np.exp(results.params)
print("Rate ratios:", rate_ratios)
```

**Overdispersion check:**
```python
# Pearson dispersion is a screening statistic, not a calibrated universal test
overdispersion = results.pearson_chi2 / results.df_resid
print(f"Overdispersion: {overdispersion}")

# If >> 1, consider Negative Binomial
if overdispersion > 1.5:
    print("Consider Negative Binomial model for overdispersion")
```

### Negative Binomial Family

For overdispersed count data.

**When to use:**
- Count data with variance > mean
- Excess zeros or large variance
- Poisson model shows overdispersion

```python
# Negative Binomial GLM with fixed alpha
model = sm.GLM(y, X, family=sm.families.NegativeBinomial(alpha=1.0))
results = model.fit()

# Use the discrete count model when alpha should be estimated
from statsmodels.discrete.discrete_model import NegativeBinomial
nb_model = NegativeBinomial(y, X)
nb_results = nb_model.fit()

print(f"Dispersion parameter alpha: {np.asarray(nb_results.params)[-1]}")
```

### Gaussian Family

Equivalent to OLS but fit via IRLS (Iteratively Reweighted Least Squares).

**When to use:**
- Want GLM framework for consistency
- Need robust standard errors
- Comparing with other GLMs

**Common links:**
- Identity (default): μ
- Log: log(μ)
- Inverse: 1/μ

```python
# Gaussian GLM (equivalent to OLS)
model = sm.GLM(y, X, family=sm.families.Gaussian())
results = model.fit()

# Verify equivalence with OLS
ols_results = sm.OLS(y, X).fit()
print("Parameters close:", np.allclose(results.params, ols_results.params))
```

### Gamma Family

For positive continuous data, often right-skewed.

**When to use:**
- Positive outcomes (insurance claims, survival times)
- Right-skewed distributions
- Variance proportional to mean²

**Common links:**
- Inverse (default): 1/μ
- Log: log(μ)
- Identity: μ

```python
# Gamma regression (common for cost data)
model = sm.GLM(y, X, family=sm.families.Gamma())
results = model.fit()

# Log link often preferred for interpretation
model = sm.GLM(y, X, family=sm.families.Gamma(link=sm.families.links.Log()))
results = model.fit()

# With log link, exp(beta) = multiplicative effect
import numpy as np
effects = np.exp(results.params)
```

### Inverse Gaussian Family

For positive continuous data with specific variance structure.

**When to use:**
- Positive skewed outcomes
- Variance proportional to mean³
- Alternative to Gamma

**Common links:**
- Inverse squared (default): 1/μ²
- Log: log(μ)

```python
model = sm.GLM(y, X, family=sm.families.InverseGaussian())
results = model.fit()
```

### Tweedie Family

Flexible family covering multiple distributions.

**When to use:**
- Insurance claims (mixture of zeros and continuous)
- Semi-continuous data
- Need flexible variance function

**Special cases (power parameter p):**
- p=0: Normal
- p=1: Poisson
- p=2: Gamma
- p=3: Inverse Gaussian
- 1<p<2: Compound Poisson-Gamma (common for insurance)

```python
# Tweedie with power=1.5
model = sm.GLM(y, X, family=sm.families.Tweedie(link=sm.families.links.Log(),
                                                 var_power=1.5))
results = model.fit()
```

## Link Functions

Link functions connect the linear predictor to the mean of the response.

### Available Links

```python
from statsmodels.genmod import families

# Identity: g(μ) = μ
link = families.links.Identity()

# Log: g(μ) = log(μ)
link = families.links.Log()

# Logit: g(μ) = l

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

