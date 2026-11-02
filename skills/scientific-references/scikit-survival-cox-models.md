---
id: sciref-scikit-survival-cox-models
name: "Scientific Ref: Cox, Coxnet, and IPC ridge models"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scikit-survival): Cox, Coxnet, and IPC ridge models"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scikit survival cox models"
  - "cox, coxnet, and ipc ridge models"
keywords:
  - "scikit"
  - "survival"
  - "cox"
  - "models"
  - "specialized"
  - "scientific"
  - "reference"
  - "coxnet"
---

# Cox, Coxnet, and IPC ridge models

Verified for scikit-survival 0.28.0 on 2026-10-01.

## Cox proportional hazards model

For covariates \(x\),

\[
h(t \mid x) = h_0(t)\exp(x^\top\beta).
\]

`CoxPHSurvivalAnalysis` estimates coefficients by partial likelihood. The model
assumes covariate effects multiply the hazard by a time-constant factor. A fitted
coefficient is a log hazard ratio only under the model, coding, scale, and PH
assumptions.

```python
from sksurv.linear_model import CoxPHSurvivalAnalysis

model = CoxPHSurvivalAnalysis(
    alpha=0.1,
    ties="efron",
    n_iter=100,
    tol=1e-9,
)
model.fit(X_train, y_train)
risk = model.predict(X_test)
survival = model.predict_survival_function(X_test)
hazard = model.predict_cumulative_hazard_function(X_test)
```

Current key parameters:

- `alpha`: non-negative L2/ridge penalty. It may be a scalar or feature-specific
  vector where documented. `alpha=0` is unpenalized.
- `ties`: `"breslow"` (default) or `"efron"`.
- `n_iter`, `tol`, `verbose`: Newton-Raphson controls.

`predict()` returns the linear predictor \(x^\top\hat\beta\); higher means higher
event risk. Absolute survival probabilities come from the fitted baseline survival,
not from transforming a risk score by itself.

### Stability and interpretation

- Encode and scale inside a training-fitted pipeline.
- Use ridge shrinkage for unstable or correlated designs; a successful numerical
  fit does not establish inferential validity.
- Check coefficient sensitivity to coding, scaling, missingness, influential rows,
  and regularization.
- Exponentiating a coefficient gives a model-based hazard ratio for one unit of its
  encoded feature, holding other modeled features fixed.
- A hazard ratio is not a risk ratio, probability difference, causal effect, or
  clinical utility measure.

scikit-survival does not provide a complete PH-diagnostics workflow. Assess the PH
assumption using residual/graphical/domain methods appropriate to the study. If it
fails, consider time interactions, stratification in a method that supports it, a
time-varying model, an AFT model, or a flexible prediction model. Do not merely
switch models and retain Cox coefficient interpretation.

## Penalized Cox path with Coxnet

`CoxnetSurvivalAnalysis` implements a Cox elastic-net path:

\[
\text{penalty} =
\alpha\left(\rho\|\beta\|_1 + \frac{1-\rho}{2}\|\beta\|_2^2\right),
\]

where `l1_ratio` is \(\rho\).

```python
from sksurv.linear_model import CoxnetSurvivalAnalysis

model = CoxnetSurvivalAnalysis(
    n_alphas=100,
    alpha_min_ratio="auto",
    l1_ratio=0.9,
    fit_baseline_model=True,
)
model.fit(X_train_scaled, y_train)
```

Current details:

- `l1_ratio` must be in `(0, 1]`; `1.0` is LASSO and values below 1 mix L1/L2.
  Exact pure ridge is handled by `CoxPHSurvivalAnalysis(alpha=...)`, not by setting
  `l1_ratio=0`.
- `alphas=None` estimates a decreasing path; explicit `alphas` selects the path.
- `alpha_min_ratio` controls the smallest/largest path ratio. It is not the
  L1/L2 mixing parameter.
- `penalty_factor` can vary penalties by feature; zero leaves a feature unpenalized.
- `normalize=False` is current. Prefer an explicit `StandardScaler` pipeline so
  fold behavior and feature scaling are visible.
- `coef_` has shape `(n_features, n_alphas)`. There is no current `coef_path_`
  attribute.
- `predict(X, alpha=...)` uses the selected path point (or interpolation).
- `predict_survival_function()` and
  `predict_cumulative_hazard_function()` require
  `fit_baseline_model=True`. An explicit `alpha` for either probability method must
  match a fitted `alphas_` value; risk-score interpolation does not provide an
  interpolated baseline survival model.

### Leakage-safe alpha selection

Do not estimate the alpha path on all rows and then claim nested-CV performance.
For a final held-out evaluation:

1. split train/test;
2. define an alpha grid from subject-matter scale or from training data only;
3. fit scaler and Coxnet inside each inner fold;
4. tune alpha on inner validation folds;
5. evaluate the selected procedure in an outer fold or untouched test set.

```python
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

pipeline = make_pipeline(
    StandardScaler(),
    CoxnetSurvivalAnalysis(l1_ratio=0.9, fit_baseline_model=True),
)
search = GridSearchCV(
    pipeline,
    {
        "coxnetsurvivalanalysis__alphas": [
            [0.01],
            [0.05],
            [0.2],
        ]
    },
    cv=inner_splits,
    error_score="raise",
)
search.fit(X_outer_train, y_outer_train)
```

When using censoring-aware scorer wrappers, wrap the entire pipeline and prefix
the parameter again:

```python
from sksurv.metrics import as_concordance_index_ipcw_scorer

wrapped = as_concordance_index_ipcw_scorer(pipeline, tau=tau)
search = GridSearchCV(
    wrapped,
    {
        "estimator__coxnetsurvivalanalysis__alphas": [
            [0.01],
            [0.05],
            [0.2],
        ]
    },
    cv=inner_splits,
)
```

IPCRidge `.score()` handles its time direction, but metric scorer wrappers call raw
`.predict()` and do not automatically negate time-oriented predictions. Use an
explicit risk adapter if applying a discrimination wrapper to an AFT estimator.

The wrapper is the estimator passed to `GridSearchCV`; it is not a zero-argument
`scoring` callable. Its fit fold supplies the censoring distribution. Time support
still has to be valid in every score fold.

### Feature selection is uncertain

Non-zero coefficients at one alpha do not prove that a feature is biologically,
causally, or clinically important. Report:

- the exact preprocessing and penalty grid;
- nested-CV or holdout protocol;
- coefficient stability across resamples;
- correlated alternatives and selection frequency;
- the selected alpha and `l1_ratio`;
- calibration and discrimination on independent data.

## IPC ridge AFT model

`IPCRidge` is an inverse-probability-of-censoring weighted ridge regression model
for a log-time/AFT objective:

```python
from sksurv.linear_model import IPCRidge

model = IPCRidge(alpha=1.0)
model.fit(X_train_scaled, y_train)
predicted_time = model.predict(X_test_scaled)
```

The fitted linear predictor models log time, but `predict()` exponentiates it and
returns original-time values; do not exponentiate it again. This output is time-oriented: larger predicted values imply longer predicted
survival time, u

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

