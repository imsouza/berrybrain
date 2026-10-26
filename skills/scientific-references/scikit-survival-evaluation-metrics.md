---
id: sciref-scikit-survival-evaluation-metrics
name: "Scientific Ref: Censoring-aware evaluation, calibration, and model selection"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scikit-survival): Censoring-aware evaluation, calibration, and model selection"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scikit survival evaluation metrics"
  - "censoring-aware evaluation, calibration, and model selection"
keywords:
  - "scikit"
  - "survival"
  - "evaluation"
  - "metrics"
  - "specialized"
  - "scientific"
  - "reference"
  - "censoring"
---

# Censoring-aware evaluation, calibration, and model selection

Verified for scikit-survival 0.28.0 on 2026-10-01. API statements below use
official scikit-survival documentation; interpretation is anchored to the cited
primary methodological literature.

## Keep the targets distinct

- **Discrimination:** can the score order subjects by event risk?
  Harrell C, Uno C, and cumulative/dynamic AUC.
- **Probability prediction error:** how close are predicted survival probabilities
  to observed event-free status after censoring adjustment? Brier score and IBS.
- **Calibration:** do predicted probabilities agree with observed probabilities at
  a specified horizon and population? Requires horizon-specific assessment; Brier
  score is not a pure calibration measure.
- **Cause-specific cumulative incidence:** what is the absolute probability of a
  particular competing cause by time \(t\)? Standard survival metrics are not
  automatically cause-specific CIF metrics.
- **Clinical/decision utility:** do decisions based on predictions improve outcomes
  under defined consequences? None of the metrics above establishes this.

Do not label one aggregate number "model accuracy" without its estimand, horizon,
censoring estimator, and input type.

## Prediction contracts

### Higher-is-riskier scalar

Shape `(n_test,)`. Used by:

- `concordance_index_censored`
- `concordance_index_ipcw`
- `cumulative_dynamic_auc` (same score at each requested time)

Typical source:

```python
risk = estimator.predict(X_test)
```

Confirm direction. Cox and ranking-only SVM predictions are higher-is-riskier.
Predicted survival/log-time outputs are the opposite direction and must not be
silently treated as risk.

### Time-dependent risk

Shape `(n_test, n_times)`. Accepted by `cumulative_dynamic_auc`, where column
`j` is risk at `times[j]`. For a random survival forest:

```python
functions = estimator.predict_cumulative_hazard_function(X_test)
risk_by_time = np.vstack([fn(times) for fn in functions])
```

Cumulative hazard is risk-oriented. Untransformed survival probabilities have the opposite direction and are not valid risk inputs to `cumulative_dynamic_auc`. Numeric shape validation does not detect that semantic error; check output direction explicitly before using a transformed probability or hazard score.

### Survival probability

Shape `(n_test, n_times)`, values in `[0, 1]`, non-increasing across columns.
Used by:

- `brier_score`
- `integrated_brier_score`

```python
functions = estimator.predict_survival_function(X_test)
survival_probability = np.vstack([fn(times) for fn in functions])
```

Metric functions expect the numeric matrix, not a list of unevaluated
`StepFunction` objects and not a 1D risk score.

## Harrell concordance

```python
from sksurv.metrics import concordance_index_censored

harrell_c = concordance_index_censored(
    y_test["event"],
    y_test["time"],
    risk,
)[0]
```

Harrell C is the fraction of comparable pairs whose risk ordering is concordant,
with handling for tied risk and event times. It measures rank discrimination over
the observed follow-up mix.

Important limitations:

- It does not assess probability calibration.
- It does not focus on a prespecified horizon.
- The set of comparable pairs changes under censoring.
- Uno et al. showed the conventional estimator's limiting value can depend on the
  censoring distribution.

There is no universal censoring-percentage cutoff at which Harrell C suddenly
becomes invalid. Report censoring, compare sensitivity to IPCW concordance, and
justify the estimand.

## Uno IPCW concordance

```python
from sksurv.metrics import concordance_index_ipcw

uno_c = concordance_index_ipcw(
    y_train,
    y_test,
    risk,
    tau=tau,
)[0]
```

`survival_train` estimates the censoring distribution. Never pass pooled
train+test outcomes or `y_test` as the training distribution.

`tau` truncates the concordance target. Choose it before seeing model performance
and where the estimated training censoring survival is positive. In 0.28.0 only test event times strictly below `tau` enter its censoring-weight
lookup; later records remain potential comparison partners with zero event weight.
A valid `tau` can therefore avoid a late-event support error for Uno C. This does
not make the same test outcomes valid for AUC or Brier APIs.

The implementation uses Kaplan-Meier censoring weights and assumes censoring is
random/independent of features. If censoring depends on covariates, this marginal
weight model may be inadequate. IPCW is not a generic correction for informative
censoring.

## Cumulative/dynamic AUC

```python
from sksurv.metrics import cumulative_dynamic_auc

auc, mean_auc = cumulative_dynamic_auc(
    y_train,
    y_test,
    risk,   # (n_test,) or (n_test, n_times)
    times,
)
```

At each \(t\), cumulative cases have an observed event by \(t\), while dynamic
controls remain event-free after \(t\). IPCW handles right censoring.

Requirements:

- `times` is one-dimensional, unique, and strictly increasing;
- every value lies within test follow-up;
- training follow-up supports test outcomes and the grid;
- the training censoring survival is positive over the grid and at every test
  event time used by the implementation (AUC weights all test events before
  applying horizons);
- each horizon has at least one observed case and a later control;
- risk has shape `(n_test,)` or `(n_test, n_times)`;
- higher values mean higher event risk.

The returned `mean_auc` is not the arithmetic mean. It integrates
\(\widehat{AUC}(t)\) over the time range, weighted by the estimated survival
function.

The cumulative/dynamic definition is one time-dependent ROC estimand. State it;
other incident/dynamic or competing-risk definitions answer different questions.

## Brier score

```python
from sksurv.metrics import brier_score, integrated_brier_score

returned_times, brier = brier_score(
    y_train,
    y_test,
    survival_probability,
    times,
)
ibs = integrated_brier_score(
    y_train,
    y_test,
    survival_probability,
    times,
)
```

The time-dependent Brier score is an IPC-weighted squared error between predicted
survival probability and event-free status at \(t\). Lower is better.

Requirements:

- predictions are survival probabilities, not risk scores;
- prediction shape is `(n_test, n_times)`;
- time and training-support rules match the IPCW setting;
- the marginal Kaplan-Meier censoring estimator's independence assumption is
  plaus

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

