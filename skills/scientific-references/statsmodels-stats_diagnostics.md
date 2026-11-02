---
id: sciref-statsmodels-stats-diagnostics
name: "Scientific Ref: Statistical Tests and Diagnostics Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (statsmodels): Statistical Tests and Diagnostics Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "statsmodels stats diagnostics"
  - "statistical tests and diagnostics reference"
keywords:
  - "statsmodels"
  - "stats"
  - "diagnostics"
  - "specialized"
  - "scientific"
  - "reference"
  - "statistical"
  - "tests"
---

# Statistical Tests and Diagnostics Reference

This document provides comprehensive guidance on statistical tests, diagnostics, and tools available in statsmodels.

## Overview

Statsmodels provides extensive statistical testing capabilities:
- Residual diagnostics and specification tests
- Hypothesis testing (parametric and non-parametric)
- Goodness-of-fit tests
- Multiple comparisons and post-hoc tests
- Power and sample size calculations
- Robust covariance matrices
- Influence and outlier detection

Fragments require the appropriate result type and aligned inputs; OLS diagnostics do not apply automatically to GLMs or dependent observations. A non-significant assumption test does not validate its null. Prespecify the inferential target and covariance from the study design, rather than selecting inference after a sequence of pretests. VIF/influence cutoffs are screening heuristics, and condition numbers depend on units.

## Residual Diagnostics

### Autocorrelation Tests

**Ljung-Box Test**: Tests for autocorrelation in residuals

```python
from statsmodels.stats.diagnostic import acorr_ljungbox

# Test residuals for autocorrelation
lb_test = acorr_ljungbox(residuals, lags=10, return_df=True)
print(lb_test)

# H0: No autocorrelation up to lag k
# If p-value < 0.05, reject H0 (autocorrelation present)
```

**Durbin-Watson Test**: Tests for first-order autocorrelation

```python
from statsmodels.stats.stattools import durbin_watson

dw_stat = durbin_watson(residuals)
print(f"Durbin-Watson: {dw_stat:.4f}")

# DW ≈ 2: no autocorrelation
# DW < 2: positive autocorrelation
# DW > 2: negative autocorrelation
# Exact critical values depend on n and k
```

**Breusch-Godfrey Test**: More general test for autocorrelation

```python
from statsmodels.stats.diagnostic import acorr_breusch_godfrey

bg_test = acorr_breusch_godfrey(results, nlags=5, result_object=True)
lm_stat, lm_pval = bg_test.lm, bg_test.lmpval

print(f"LM statistic: {lm_stat:.4f}, p-value: {lm_pval:.4f}")
# H0: No autocorrelation up to lag k
```

### Heteroskedasticity Tests

**Breusch-Pagan Test**: Tests for heteroskedasticity

```python
from statsmodels.stats.diagnostic import het_breuschpagan

bp_test = het_breuschpagan(residuals, exog)
lm_stat, lm_pval, f_stat, f_pval = bp_test

print(f"Breusch-Pagan test p-value: {lm_pval:.4f}")
# H0: Homoskedasticity (constant variance)
# If p-value < 0.05, reject H0 (heteroskedasticity present)
```

**White Test**: More general test for heteroskedasticity

```python
from statsmodels.stats.diagnostic import het_white

white_test = het_white(residuals, exog)
lm_stat, lm_pval, f_stat, f_pval = white_test

print(f"White test p-value: {lm_pval:.4f}")
# H0: Homoskedasticity
```

**ARCH Test**: Tests for autoregressive conditional heteroskedasticity

```python
from statsmodels.stats.diagnostic import het_arch

arch_test = het_arch(residuals, nlags=5, result_object=True)
lm_stat, lm_pval = arch_test.lm, arch_test.lmpval

print(f"ARCH test p-value: {lm_pval:.4f}")
# H0: No ARCH effects
# If significant, consider GARCH model
```

### Normality Tests

**Jarque-Bera Test**: Tests for normality using skewness and kurtosis

```python
from statsmodels.stats.stattools import jarque_bera

jb_stat, jb_pval, skew, kurtosis = jarque_bera(residuals)

print(f"Jarque-Bera statistic: {jb_stat:.4f}")
print(f"p-value: {jb_pval:.4f}")
print(f"Skewness: {skew:.4f}")
print(f"Kurtosis: {kurtosis:.4f}")

# H0: Residuals are normally distributed
# Normal: skewness ≈ 0, kurtosis ≈ 3
```

**Omnibus Test**: Another normality test (also based on skewness/kurtosis)

```python
from statsmodels.stats.stattools import omni_normtest

omni_stat, omni_pval = omni_normtest(residuals)
print(f"Omnibus test p-value: {omni_pval:.4f}")
# H0: Normality
```

**Anderson-Darling Test**: Distribution fit test

```python
from statsmodels.stats.diagnostic import normal_ad

ad_stat, ad_pval = normal_ad(residuals)
print(f"Anderson-Darling test p-value: {ad_pval:.4f}")
```

**Lilliefors Test**: Modified Kolmogorov-Smirnov test

```python
from statsmodels.stats.diagnostic import lilliefors

lf_stat, lf_pval = lilliefors(residuals, dist='norm')
print(f"Lilliefors test p-value: {lf_pval:.4f}")
```

### Linearity and Specification Tests

**Ramsey RESET Test**: Tests for functional form misspecification

```python
from statsmodels.stats.diagnostic import linear_reset

reset_test = linear_reset(results, power=2, use_f=True)
f_stat, f_pval = reset_test.fvalue, reset_test.pvalue

print(f"RESET test p-value: {f_pval:.4f}")
# H0: the added nonlinear terms have zero coefficients; not a general validity test
# If rejected, may need polynomial terms or transformations
```

**Harvey-Collier Test**: Tests for linearity

```python
from statsmodels.stats.diagnostic import linear_harvey_collier

hc_stat, hc_pval = linear_harvey_collier(results)
print(f"Harvey-Collier test p-value: {hc_pval:.4f}")
# H0: Linear specification is correct
```

## Multicollinearity Detection

**Variance Inflation Factor (VIF)**:

```python
from statsmodels.stats.outliers_influence import variance_inflation_factor
import pandas as pd

# Calculate VIF for each variable
vif_data = pd.DataFrame()
vif_data["Variable"] = X.columns
vif_data["VIF"] = [variance_inflation_factor(X.values, i)
                   for i in range(X.shape[1])]

print(vif_data.sort_values('VIF', ascending=False))

# Interpretation:
# VIF = 1: No correlation with other predictors
# VIF > 5: Moderate multicollinearity
# VIF > 10: Serious multicollinearity problem
# VIF > 20: Severe multicollinearity (consider removing variable)
```

**Condition Number**: From regression results

```python
print(f"Condition number: {results.condition_number:.2f}")

# Interpretation:
# < 10: No multicollinearity concern
# 10-30: Moderate multicollinearity
# > 30: Strong multicollinearity
# > 100: Severe multicollinearity
```

## Influence and Outlier Detection

### Leverage

High leverage points have extreme predictor values.

```python
from statsmodels.stats.outliers_influence import OLSInfluence

influence = results.get_influence()

# Hat values (leverage)
leverage = influence.hat_matrix_diag

# Rule of thumb: leverage > 2*p/n or 3*p/n is high
# p = number of parameters, n = sample size
threshold = 2 * len(results.params) / len(y)
high_leverage = np.where(leverage > threshold)[0]

print(f"High leverage observations: {high_leverage}")
```

### Cook's Distance

Measures overall influence of each observation.

```python
# Cook's dist

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

