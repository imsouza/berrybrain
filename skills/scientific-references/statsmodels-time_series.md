---
id: sciref-statsmodels-time-series
name: "Scientific Ref: Time Series Analysis Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (statsmodels): Time Series Analysis Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "statsmodels time series"
  - "time series analysis reference"
keywords:
  - "statsmodels"
  - "time"
  - "series"
  - "specialized"
  - "scientific"
  - "reference"
---

# Time Series Analysis Reference

This document provides comprehensive guidance on time series models in statsmodels, including ARIMA, state space models, VAR, exponential smoothing, and forecasting methods.

## Overview

Statsmodels offers extensive time series capabilities:
- **Univariate models**: AR, ARIMA, SARIMAX, Exponential Smoothing
- **Multivariate models**: VAR, VARMAX, Dynamic Factor Models
- **State space framework**: Custom models, Kalman filtering
- **Diagnostic tools**: ACF, PACF, stationarity tests, residual analysis
- **Forecasting**: Point forecasts and prediction intervals

Use a sorted, unique regular time grid with a recorded frequency; do not drop interior missing dates and silently compress time. State-space models can handle missing responses, but exogenous data must be finite/aligned, and ADF/KPSS reject missing values. For date-labeled forecasting, preserve the frequency and provide future exogenous rows in exact model-column order.

## Univariate Time Series Models

### AutoReg (AR Model)

Autoregressive model: current value depends on past values.

**When to use:**
- Univariate time series
- Past values predict future
- Stationary series

**Model**: yₜ = c + φ₁yₜ₋₁ + φ₂yₜ₋₂ + ... + φₚyₜ₋ₚ + εₜ

```python
from statsmodels.tsa.ar_model import AutoReg
import pandas as pd

# Fit AR(p) model
model = AutoReg(y, lags=5)  # AR(5)
results = model.fit()

print(results.summary())
```

**With exogenous regressors:**
```python
# AR with exogenous variables (ARX)
model = AutoReg(y, lags=5, exog=X_exog)
results = model.fit()
```

**Seasonal AR:**
```python
# Lags 1..12 plus seasonal dummies; use lags=[1, 12] for sparse seasonal lags
model = AutoReg(y, lags=12, seasonal=True, period=12)
results = model.fit()
```

### ARIMA (Autoregressive Integrated Moving Average)

Combines AR, differencing (I), and MA components.

**When to use:**
- Non-stationary time series (needs differencing)
- Past values and errors predict future
- Flexible model for many time series

**Model**: ARIMA(p,d,q)
- p: AR order (lags)
- d: differencing order (to achieve stationarity)
- q: MA order (lagged forecast errors)

```python
from statsmodels.tsa.arima.model import ARIMA

# Fit ARIMA(p,d,q)
model = ARIMA(y, order=(1, 1, 1))  # ARIMA(1,1,1)
results = model.fit()

print(results.summary())
```

**Choosing p, d, q:**

1. **Determine d (differencing order)**:
```python
from statsmodels.tsa.stattools import adfuller

# ADF test for stationarity
def check_stationarity(series):
    result = adfuller(series, result_object=True)
    print(f"ADF Statistic: {result.statistic:.4f}")
    print(f"p-value: {result.pvalue:.4f}")
    if result.pvalue <= 0.05:
        print("Reject unit-root null under the chosen deterministic specification")
        return True
    else:
        print("Do not reject unit root; this does not prove nonstationarity")
        return False

# Combine the test with trend/seasonal plots, sampling frequency and domain knowledge.
check_stationarity(y)
# Compare a prespecified candidate difference; do not repeatedly difference
# until a p-value crosses a threshold. ARIMA(y, order=(p,d,q)) uses original y.
y_diff = y.diff().dropna()
check_stationarity(y_diff)
```

2. **Determine p and q (ACF/PACF)**:
```python
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt

# After differencing to stationarity
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# ACF: helps determine q (MA order)
plot_acf(y_stationary, lags=40, ax=ax1)
ax1.set_title('Autocorrelation Function (ACF)')

# PACF: helps determine p (AR order)
plot_pacf(y_stationary, lags=40, ax=ax2)
ax2.set_title('Partial Autocorrelation Function (PACF)')

plt.tight_layout()
plt.show()

# Rules of thumb:
# - PACF cuts off at lag p → AR(p)
# - ACF cuts off at lag q → MA(q)
# - Both decay → ARMA(p,q)
```

3. **Model selection (AIC/BIC)**:
```python
# Grid search for best (p,q) given d
import numpy as np

best_aic = np.inf
best_order = None
best_result = None
candidates = []

for p in range(5):
    for q in range(5):
        try:
            model = ARIMA(y, order=(p, d, q))
            results = model.fit()
            converged = results.mle_retvals.get("converged", False)
            candidates.append({"order": (p, d, q), "converged": converged, "aic": results.aic})
            if converged and np.isfinite(results.aic) and results.aic < best_aic:
                best_aic = results.aic
                best_order = (p, d, q)
                best_result = results
        except (ValueError, np.linalg.LinAlgError) as exc:
            candidates.append({"order": (p, d, q), "error": str(exc)})

if best_order is None:
    raise RuntimeError("No converged finite-likelihood candidate; inspect failures")
results = best_result  # Keep the selected fit, not the last grid candidate
print(pd.DataFrame(candidates))
print(f"Best order: {best_order} with AIC: {best_aic:.2f}")
```

### SARIMAX (Seasonal ARIMA with Exogenous Variables)

Extends ARIMA with seasonality and exogenous regressors.

**When to use:**
- Seasonal patterns (monthly, quarterly data)
- External variables influence series
- Most flexible univariate model

**Model**: SARIMAX(p,d,q)(P,D,Q,s)
- (p,d,q): Non-seasonal ARIMA
- (P,D,Q,s): Seasonal ARIMA with period s

```python
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Seasonal ARIMA for monthly data (s=12)
model = SARIMAX(y,
                order=(1, 1, 1),           # (p,d,q)
                seasonal_order=(1, 1, 1, 12))  # (P,D,Q,s)
results = model.fit()

print(results.summary())
```

**With exogenous variables:**
```python
# SARIMAX with external predictors
model = SARIMAX(y,
                exog=X_exog,
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 12))
results = model.fit()
```

**Example: Monthly sales with trend and seasonality**
```python
# Typical for monthly data: (p,d,q)(P,D,Q,12)
# Start with (1,1,1)(1,1,1,12) or (0,1,1)(0,1,1,12)

model = SARIMAX(monthly_sales,
                order=(0, 1, 1),
                seasonal_order=(0, 1, 1, 12),
                enforce_stationarity=False,
                enforce_invertibility=False)
results = model.fit()
```

### Exponential Smoothing

Weighted averages of past observations with exponentially decreasing weights.

**When to use:**
- Simple, interpretable forecasts
- Trend and/or seasonality present
- No need for explicit model specification

**Types:**
- Simple Exponential Smoothing: no trend, no 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

