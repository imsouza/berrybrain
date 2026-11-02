---
id: sciref-scikit-survival-ensemble-models
name: "Scientific Ref: Survival trees, forests, and boosting"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scikit-survival): Survival trees, forests, and boosting"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scikit survival ensemble models"
  - "survival trees, forests, and boosting"
keywords:
  - "scikit"
  - "survival"
  - "ensemble"
  - "models"
  - "specialized"
  - "scientific"
  - "reference"
---

# Survival trees, forests, and boosting

Verified for scikit-survival 0.28.0 on 2026-10-01.

## Model families

- `SurvivalTree`: one log-rank survival tree.
- `RandomSurvivalForest`: bootstrap-aggregated survival trees with random feature
  subsets.
- `ExtraSurvivalTrees`: additional randomization of candidate split thresholds.
- `GradientBoostingSurvivalAnalysis`: regression-tree gradient boosting.
- `ComponentwiseGradientBoostingSurvivalAnalysis`: linear componentwise base
  learners and implicit sparse selection.

Model family does not determine quality in advance. Compare prespecified candidates
with identical outer resamples, censoring assumptions, time grids, and preprocessing.

## Random survival forest

```python
from sksurv.ensemble import RandomSurvivalForest

model = RandomSurvivalForest(
    n_estimators=500,
    min_samples_split=10,
    min_samples_leaf=8,
    max_features="sqrt",
    n_jobs=1,
    random_state=20260723,
)
model.fit(X_train, y_train)
```

Current defaults include `n_estimators=100`, `min_samples_split=6`,
`min_samples_leaf=3`, `max_features="sqrt"`, `bootstrap=True`, and
`low_memory=False`.

Each terminal node estimates:

- a survival function using Kaplan-Meier;
- a cumulative hazard function using Nelson-Aalen;
- a risk score summing the estimated cumulative hazard over the training event
  times; its magnitude is neither a probability nor an expected count at a named horizon.

Forest predictions average tree predictions:

```python
risk = model.predict(X_test)  # (n_test,), higher is riskier
survival = model.predict_survival_function(X_test, return_array=True)
cumulative_hazard = model.predict_cumulative_hazard_function(
    X_test, return_array=True
)
times = model.unique_times_
```

Array predictions use the model's `unique_times_`. For an evaluation grid, returned
step functions are often more convenient:

```python
import numpy as np

functions = model.predict_survival_function(X_test, return_array=False)
survival_on_grid = np.vstack([fn(evaluation_times) for fn in functions])
```

Do not treat the numeric magnitude of `predict()` as an event probability.

### Missing values and memory

Current survival trees and forest split logic supports missing values, with fixes
aligned to scikit-learn 1.8 in scikit-survival 0.27. This does not remove the need
to:

- verify which columns and missingness patterns are supported;
- encode categorical columns consistently;
- keep all learned preprocessing within training folds;
- assess whether missingness itself changes across deployment settings.

`low_memory=True` reduces stored prediction state but disables survival-function
and cumulative-hazard prediction. It is incompatible with Brier-score workflows
that require survival probabilities.

### OOB estimates

With `oob_score=True` and bootstrap sampling, `oob_score_` provides an internal
out-of-bag concordance estimate. It is not a substitute for:

- nested tuning when parameters were selected using OOB results;
- an independent test set;
- censoring-aware probability metrics;
- external validation.

## Extra survival trees

```python
from sksurv.ensemble import ExtraSurvivalTrees

model = ExtraSurvivalTrees(
    n_estimators=500,
    min_samples_leaf=8,
    max_features="sqrt",
    n_jobs=1,
    random_state=20260723,
)
model.fit(X_train, y_train)
```

Extra trees randomize split thresholds in addition to feature selection. They are
not guaranteed to be faster, better regularized, or better calibrated for a given
dataset. Tune and evaluate them as a distinct candidate under the same protocol.

## Permutation importance

Survival forest impurity importance is not implemented as a valid
`feature_importances_` measure. Use held-out permutation importance with an
explicit score:

```python
from sklearn.inspection import permutation_importance

result = permutation_importance(
    fitted_pipeline,
    X_test,
    y_test,
    scoring=None,  # estimator.score: Harrell concordance
    n_repeats=20,
    random_state=20260723,
    n_jobs=1,
)
```

If Harrell C is not the target, wrap the estimator with the appropriate
scikit-survival scorer class before permutation or write a scorer that fits no
state on the test set. Importance depends on:

- the metric and horizon;
- correlated features;
- the held-out population;
- preprocessing and random seed.

It is predictive sensitivity, not causal importance.

## Tree gradient boosting

```python
from sksurv.ensemble import GradientBoostingSurvivalAnalysis

model = GradientBoostingSurvivalAnalysis(
    loss="coxph",
    learning_rate=0.05,
    n_estimators=300,
    max_depth=2,
    subsample=0.8,
    random_state=20260723,
)
model.fit(X_train, y_train)
```

Current losses:

- `"coxph"`: Cox partial-likelihood objective; `predict()` is a higher-is-riskier
  score, and baseline-based survival/cumulative-hazard methods are available.
- `"ipcwls"`: intended IPC-weighted least-squares AFT objective; see the release
  defects below before relying on it.
- `"squared"`: squared-error time-oriented objective.

Time-oriented losses do not make `predict()` a Cox risk score and do not provide
the same baseline survival-function interface. Both non-Cox losses return exponentiated predictions on the original-time scale.
Confirm prediction direction before
using concordance or dynamic AUC; negate a predicted-time output only when that
conversion is explicitly intended and reported.

Released 0.28.0 `ipcwls` has two native/source-confirmed limitations in both
boosting classes: positive times below 1 become negative after the internal log
transform and the censoring-weight estimator rejects them; and the gradient
omits IPC weights even though the reported loss uses them. With fixed iterations,
full subsampling, and default sample weights, changing event/censor labels while
keeping observed times fixed produced identical predictions on the synthetic
fixture. Do not treat a successful `ipcwls` fit as validated IPC-weighted training
or change time units merely to hide the error. Prefer a verified alternative such
as `IPCRidge` when an IPC-weighted AFT fit is required.

Current regularization controls:

- `learning_rate`
- `n_estimators`
- `subsample`
- `dropout_rate`
- tree depth/leaf controls
- `ccp_alpha`
- `validation_fraction`, `n_iter_no_change`, and `tol`
- a custom `monitor` passed to `fit()` for controlled early stopping

The old `criterion` parameter was removed in 0.28. Do not copy it from older
examples.

Use only training dat

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

