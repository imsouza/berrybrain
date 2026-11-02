---
id: sciref-statsmodels-linear-models
name: "Scientific Ref: Linear Regression Models Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (statsmodels): Linear Regression Models Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "statsmodels linear models"
  - "linear regression models reference"
keywords:
  - "statsmodels"
  - "linear"
  - "models"
  - "specialized"
  - "scientific"
  - "reference"
  - "regression"
---

# Linear Regression Models Reference

This document provides detailed guidance on linear regression models in statsmodels, including OLS, GLS, WLS, quantile regression, and specialized variants.

## Core Model Classes

### OLS (Ordinary Least Squares)

OLS estimates a linear conditional mean. Conventional covariance assumes homoscedastic, uncorrelated errors; normal errors support exact small-sample t/F inference. Robust covariance changes uncertainty, not an omitted-variable or endogeneity bias.

**When to use:**
- Standard regression analysis
- Errors are independent and have constant variance
- No autocorrelation or heteroscedasticity
- Most common starting point

**Basic usage:**
```python
import statsmodels.api as sm
import numpy as np

# Array interface: add a constant if an intercept is intended
X = sm.add_constant(X_data)  # Adds column of 1s for intercept

# Fit model
model = sm.OLS(y, X)
results = model.fit()

# View results
print(results.summary())
```

**Key results attributes:**
```python
results.params           # Coefficients
results.bse              # Standard errors
results.tvalues          # T-statistics
results.pvalues          # P-values
results.rsquared         # R-squared
results.rsquared_adj     # Adjusted R-squared
results.fittedvalues     # Fitted values (predictions on training data)
results.resid            # Residuals
results.conf_int()       # Confidence intervals for parameters
```

**Prediction with confidence/prediction intervals:**
```python
# For in-sample predictions
pred = results.get_prediction(X)
pred_summary = pred.summary_frame()
print(pred_summary)  # Contains mean, std, confidence intervals

# For out-of-sample predictions
X_new = sm.add_constant(X_new_data, has_constant="add")
pred_new = results.get_prediction(X_new)
pred_summary = pred_new.summary_frame()

# Access intervals
mean_ci_lower = pred_summary["mean_ci_lower"]
mean_ci_upper = pred_summary["mean_ci_upper"]
obs_ci_lower = pred_summary["obs_ci_lower"]  # Prediction intervals
obs_ci_upper = pred_summary["obs_ci_upper"]
```

**Formula API (R-style):**
```python
import statsmodels.formula.api as smf

# Automatic handling of categorical variables and interactions
formula = 'y ~ x1 + x2 + C(category) + x1:x2'
results = smf.ols(formula, data=df).fit()
```

### WLS (Weighted Least Squares)

Handles heteroscedastic errors (diagonal Σ) where variance differs across observations.

**When to use:**
- Known heteroscedasticity (non-constant error variance)
- Different observations have different reliability
- Weights are known or can be estimated

**Usage:**
```python
# If you know the weights (inverse variance)
weights = 1 / error_variance
model = sm.WLS(y, X, weights=weights)
results = model.fit()

# Common weight patterns:
# - 1/variance: when variance is known
# - n_i: sample size for grouped data
# - 1/x: when variance proportional to x
```

**Feasible WLS (estimating weights):**
```python
# Step 1: Fit OLS
ols_results = sm.OLS(y, X).fit()

# Step 2: Model squared residuals to estimate variance
abs_resid = np.abs(ols_results.resid)
variance_model = sm.OLS(np.log(np.maximum(abs_resid**2, np.finfo(float).tiny)), X).fit()

# Step 3: Use estimated variance as weights
weights = 1 / np.exp(variance_model.fittedvalues)
wls_results = sm.WLS(y, X, weights=weights).fit()
```

### GLS (Generalized Least Squares)

Handles arbitrary covariance structure (Σ). Superclass for other regression methods.

**When to use:**
- Known covariance structure
- Correlated errors
- More general than WLS

**Usage:**
```python
# Specify covariance structure
# Sigma should be (n x n) covariance matrix
model = sm.GLS(y, X, sigma=Sigma)
results = model.fit()
```

### GLSAR (GLS with Autoregressive Errors)

Feasible generalized least squares with AR(p) errors for time series data.

**When to use:**
- Time series regression with autocorrelated errors
- Need to account for serial correlation
- Violations of error independence

**Usage:**
```python
# AR(1) errors
model = sm.GLSAR(y, X, rho=1)  # rho=1 for AR(1), rho=2 for AR(2), etc.
results = model.iterative_fit(maxiter=20)  # Default maxiter=3 may be insufficient

print(results.summary())
print(f"Estimated rho: {results.model.rho}")
```

### RLS (Recursive Least Squares)

Expanding-window estimates of a fixed-coefficient regression, plus stability diagnostics; this is not a stochastic time-varying-coefficient model.

**When to use:**
- Assess coefficient stability as observations accumulate
- Inspect recursive residuals and CUSUM
- Refit with additional data; do not assume a streaming update interface

**Usage:**
```python
from statsmodels.regression.recursive_ls import RecursiveLS

model = RecursiveLS(y, X)
results = model.fit()

# Expanding-window filtered/smoothed coefficient estimates
params_over_time = results.recursive_coefficients.filtered
cusum = results.cusum  # CUSUM statistic for structural breaks
```

### Rolling Regressions

Compute estimates across moving windows for time-varying parameter detection.

**When to use:**
- Parameters vary over time
- Want to detect structural changes
- Time series with evolving relationships

**Usage:**
```python
from statsmodels.regression.rolling import RollingOLS, RollingWLS

# Rolling OLS with 60-period window
rolling_model = RollingOLS(y, X, window=60)
rolling_results = rolling_model.fit()

# Extract time-varying parameters
rolling_params = pd.DataFrame(rolling_results.params)  # Also handles NumPy inputs
rolling_rsquared = rolling_results.rsquared

# Plot parameter evolution
import matplotlib.pyplot as plt
rolling_params.plot()
plt.title('Time-Varying Coefficients')
plt.show()
```

### Quantile Regression

Analyzes conditional quantiles rather than conditional mean.

**When to use:**
- Interest in quantiles (median, 90th percentile, etc.)
- Robust to outliers (median regression)
- Distributional effects across quantiles
- Heterogeneous effects

**Usage:**
```python
from statsmodels.regression.quantile_regression import QuantReg

# Median regression (50th percentile)
model = QuantReg(y, X)
results_median = model.fit(q=0.5)

# Multiple quantiles
quantiles = [0.1, 0.25, 0.5, 0.75, 0.9]
results_dict = {}
for q in quantiles:
    results_dict[q] = model.fit(q=q)

# Plot quantile-varying effects
import matplotlib.pyplot as plt
coef_dict = {q: res.params for q, res in results_dict.items()}
coef_df = pd.DataFrame(coef_dict).T
coef_df.plot()
plt.xlabel('Quantile')
plt.ylabel('Coefficient')
plt.show()
```

## Mixed Effects Models



*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

