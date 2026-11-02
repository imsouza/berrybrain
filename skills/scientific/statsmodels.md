---
id: sci-statsmodels
name: "Scientific: statsmodels"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Fits and diagnoses Python statistical models including OLS, GLM, discrete and mixed models, ARIMA and SARIMAX. Supports coefficient inference, marginal effects, model comparison and time series forecasting with explicit design and uncertainty checks. Used for econometrics and sta"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "statsmodels"
keywords:
  - "statsmodels"
  - "fits"
  - "diagnoses"
  - "python"
  - "statistical"
  - "models"
  - "including"
---

# Statsmodels: Statistical Modeling and Econometrics

## Overview

Statsmodels provides estimation, inference and diagnostics for regression, time series and econometric models. A successful fit establishes numerical execution; causal identification, calibrated uncertainty and model adequacy require a defensible study design and assumptions.

## Current Compatibility

Reviewed against statsmodels 0.15.0 (released August 27, 2026). Native checks used Python 3.13, NumPy 2.5.3, SciPy 1.18.1, pandas 3.0.6, matplotlib 3.11.2 and scikit-learn 1.9.1. Install in a dedicated environment:

```bash
uv pip install statsmodels==0.15.0 numpy==2.5.3 scipy==1.18.1 pandas==3.0.6 matplotlib==3.11.2 scikit-learn==1.9.1
```

Use `statsmodels.api` and `statsmodels.formula.api` for stable high-level imports, and direct module imports when examples require newer or specialized classes such as `HurdleCountModel`.

The [review and source ledger](references/review.md) records API coverage and verification limits. The quick start is executable; topic references are contextual fragments requiring the named data and a matching model result. In 0.15, use `result_object=True` and named fields for ADF/KPSS and other transitioning tests; prefer `rng=` where statsmodels formerly accepted `seed` or `random_state`.

## When to Use This Skill

This skill should be used when:
- Fitting regression models (OLS, WLS, GLS, quantile regression)
- Performing generalized linear modeling (logistic, Poisson, Gamma, etc.)
- Analyzing discrete outcomes (binary, multinomial, count, ordinal)
- Conducting time series analysis (ARIMA, SARIMAX, VAR, forecasting)
- Running statistical tests and diagnostics
- Testing model assumptions (heteroskedasticity, autocorrelation, normality)
- Detecting outliers and influential observations
- Comparing models (AIC/BIC, likelihood ratio tests)
- Estimating causal effects
- Producing publication-ready statistical tables and inference

## Quick Start, Capabilities, and Model Selection

- [references/quick_start_guide.md](references/quick_start_guide.md): minimal worked
  examples for OLS, logistic regression, ARIMA, and GLM, and how to read the summary.
- [references/modeling_capabilities.md](references/modeling_capabilities.md): linear
  models, GLMs, discrete choice, time series, and the statistical tests and diagnostics.
- [references/model_selection.md](references/model_selection.md): the R-style formula API
  and model comparison.
- Per-topic detail: [references/linear_models.md](references/linear_models.md),
  [references/glm.md](references/glm.md),
  [references/discrete_choice.md](references/discrete_choice.md),
  [references/time_series.md](references/time_series.md), and
  [references/stats_diagnostics.md](references/stats_diagnostics.md).

statsmodels supports inference and prediction, including forecasting. Match validation to the sampling design: grouped splits for repeated units, chronological splits for time series, and preprocessing learned on training data only.

## Best Practices

### Data Preparation

1. **Specify the intercept**: Array OLS/GLM/Logit need an explicit constant; formula models include one by default. OrderedModel and ConditionalLogit must not receive a constant.
2. **Check for missing values**: For array-based models, use `missing="raise"` during construction to catch unexpected NaNs; the default `missing="none"` does not check and can yield all-NaN estimates. If dropping rows is justified, record retained row IDs and compare models on the same observations. Fit any imputation on training data only.
3. **Scale if needed**: Can improve conditioning and convergence; record units and estimate scaling on training data
4. **Encode categoricals**: Use formula API or manual dummy coding

### Model Building

1. **Start simple**: Begin with basic model, add complexity as needed
2. **Check assumptions**: Test residuals, heteroskedasticity, autocorrelation
3. **Use appropriate model**: Match model to outcome type (binary→Logit, count→Poisson)
4. **Consider alternatives**: If assumptions violated, use robust methods or different model

### Inference

1. **Report effect sizes**: Not just p-values
2. **Use robust SEs**: When heteroskedasticity or clustering present
3. **Multiple comparisons**: Correct when testing many hypotheses
4. **Confidence intervals**: Always report alongside point estimates

### Model Evaluation

1. **Check residuals**: Plot residuals vs fitted, Q-Q plot
2. **Influence diagnostics**: Identify and investigate influential observations
3. **Out-of-sample validation**: Test on holdout set or cross-validate
4. **Compare models**: Use AIC/BIC only for comparable likelihoods on the same response and rows; regular nested-model LR tests need interior parameters and valid likelihood assumptions

### Reporting

1. **Comprehensive summary**: Use `.summary()` for detailed output
2. **Document decisions**: Note transformations, excluded observations
3. **Interpret carefully**: Account for link functions (e.g., exp(β) for log link)
4. **Visualize**: Plot predictions, confidence intervals, diagnostics

## Common Workflows

### Workflow 1: Linear Regression Analysis

1. Explore data (plots, descriptives)
2. Fit initial OLS model
3. Check residual diagnostics
4. Test for heteroskedasticity, autocorrelation
5. Check for multicollinearity (VIF)
6. Identify influential observations
7. Refit with robust SEs if needed
8. Interpret coefficients and inference
9. Validate on holdout or via CV

### Workflow 2: Binary Classification

1. Fit logistic regression (Logit)
2. Check for convergence issues
3. Interpret odds ratios
4. Calculate marginal effects
5. Evaluate classification performance (AUC, confusion matrix)
6. Check for influential observations
7. Compare with alternative models (Probit)
8. Validate predictions on test set

### Workflow 3: Count Data Analysis

1. Fit Poisson regression
2. Check for overdispersion
3. If overdispersed, fit Negative Binomial
4. Check for excess zeros (consider ZIP/ZINB)
5. Interpret rate ratios
6. Assess goodness of fit
7. Compare models via AIC
8. Validate predictions

### Workflow 4: Time Series Forecasting

1. Plot series, check for trend/seasonality
2. Test for stationarity (ADF, KPSS)
3. Choose deterministic terms and differencing using domain context, plots and tests; do not treat failure to reject a unit root as proof
4. Use ACF/PACF for candidate orders, then compare converged fits on training data
5. Fit ARIMA or SARIMAX
6. Check r

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

