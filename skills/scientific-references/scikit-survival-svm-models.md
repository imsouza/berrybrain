---
id: sciref-scikit-survival-svm-models
name: "Scientific Ref: Survival support vector machines"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scikit-survival): Survival support vector machines"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scikit survival svm models"
  - "survival support vector machines"
keywords:
  - "scikit"
  - "survival"
  - "svm"
  - "models"
  - "specialized"
  - "scientific"
  - "reference"
---

# Survival support vector machines

Verified for scikit-survival 0.28.0 on 2026-10-01.

## What survival SVMs predict

Survival SVMs optimize ranking, regression, or a mixture. They generally return a
scalar score, not a baseline survival function or cumulative hazard function.
Therefore:

- use concordance or cumulative/dynamic AUC only after confirming score direction;
- do not pass SVM output to Brier metrics;
- do not convert a margin to event probability without a separately validated
  calibration model and protocol.

## Fast linear survival SVM

```python
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sksurv.svm import FastSurvivalSVM

model = make_pipeline(
    StandardScaler(),
    FastSurvivalSVM(
        alpha=1.0,
        rank_ratio=1.0,
        max_iter=1000,
        tol=1e-5,
        random_state=20260723,
    ),
)
model.fit(X_train, y_train)
risk = model.predict(X_test)
```

Current signature:

```text
FastSurvivalSVM(
    alpha=1, *,
    rank_ratio=1.0,
    fit_intercept=False,
    max_iter=20,
    verbose=False,
    tol=None,
    optimizer=None,
    random_state=None,
    timeit=False,
)
```

Key semantics:

- `rank_ratio=1.0`: ranking-only objective; higher predictions indicate shorter
  survival/higher event risk.
- `0 < rank_ratio < 1`: mixed ranking and regression.
- `rank_ratio=0.0`: regression-only objective.
- When `rank_ratio < 1`, `predict()` exponentiates the log-time predictor and returns
  original-time values: lower prediction means shorter survival. For a metric requiring
  higher event risk, use `-prediction` and document the conversion.
- `alpha` weights the data-fit/ranking objective relative to the penalty, so larger
  values mean less regularization; tune it within inner CV.

Do not use an arbitrary sign simply because a C-index improves. The sign follows
the model objective and target interpretation.

## Fast kernel survival SVM

```python
from sksurv.svm import FastKernelSurvivalSVM

model = FastKernelSurvivalSVM(
    alpha=1.0,
    rank_ratio=1.0,
    kernel="rbf",
    gamma=0.05,
    max_iter=100,
    tol=1e-5,
    random_state=20260723,
)
model.fit(X_train_scaled, y_train)
risk = model.predict(X_test_scaled)
```

Current signature:

```text
FastKernelSurvivalSVM(
    alpha=1, *,
    rank_ratio=1.0,
    fit_intercept=False,
    kernel="rbf",
    gamma=None,
    degree=3,
    coef0=1,
    kernel_params=None,
    max_iter=20,
    verbose=False,
    tol=None,
    optimizer=None,
    random_state=None,
    timeit=False,
)
```

Kernel choices follow scikit-learn pairwise-kernel behavior, including `"linear"`,
`"poly"`, `"rbf"`, `"sigmoid"`, callable kernels, and `"precomputed"` where
supported. Do not copy older examples that use `gamma="scale"` without checking
the current API; the current scikit-survival parameter default is `None`.

Kernel fitting and prediction depend on training rows and can require
quadratic-size kernel matrices. Enforce row/memory bounds before fitting.

## Hinge, Minlip, and naive formulations

Current additional estimators:

- `HingeLossSurvivalSVM(alpha=1.0, solver="ecos", kernel="linear", pairs="all", ...)`
- `MinlipSurvivalAnalysis(alpha=1.0, solver="ecos", kernel="linear",
  pairs="nearest", ...)`
- `NaiveSurvivalSVM(penalty="l2", loss="squared_hinge", dual=False,
  alpha=1.0, ...)`

Important current differences:

- `HingeLossSurvivalSVM` and `MinlipSurvivalAnalysis` do not have a
  `random_state` constructor parameter.
- Their convex optimization defaults to the ECOS solver.
- Pair construction and kernel matrices can become expensive.
- `NaiveSurvivalSVM` uses a linear-SVM-style formulation and is mainly useful for
  small comparisons; it is not the fast implementation.

Use the exact current signature rather than transferring parameters across SVM
classes.

## Scaling and explicit preprocessing

Scale continuous features and fit scaling only on training folds:

```python
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

preprocess = ColumnTransformer(
    [
        (
            "num",
            make_pipeline(SimpleImputer(strategy="median"), StandardScaler()),
            numeric_columns,
        ),
        (
            "cat",
            make_pipeline(
                SimpleImputer(strategy="most_frequent"),
                OneHotEncoder(
                    drop="first",
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
            categorical_columns,
        ),
    ],
    sparse_threshold=0.0,
)
model = make_pipeline(
    preprocess,
    FastSurvivalSVM(rank_ratio=1.0, random_state=20260723),
)
```

Do not call `StandardScaler.fit_transform(X)` before cross-validation. Keeping it
inside the pipeline makes every inner and outer fold independent.

## Kernel preprocessing

For `"precomputed"`, training input must be a square
`(n_train, n_train)` kernel matrix; test input must be
`(n_test, n_train)` with columns in the identical training order.

`sksurv.kernels.ClinicalKernelTransform` and `clinical_kernel()` support mixed
continuous, ordinal, and nominal DataFrame columns, including pandas/Polars in
0.28. They do not accept an ad hoc list of `(clinical, molecular)` tuples as a
special API. Fit the transform on a clearly typed training DataFrame or explicitly
precompute the kernel:

```python
from sksurv.kernels import ClinicalKernelTransform
from sksurv.svm import FastKernelSurvivalSVM

kernel = ClinicalKernelTransform()
kernel_train = kernel.fit_transform(X_train_typed)
kernel_test = kernel.transform(X_test_typed)

model = FastKernelSurvivalSVM(
    kernel="precomputed",
    rank_ratio=1.0,
    random_state=20260723,
)
model.fit(kernel_train, y_train)
risk = model.predict(kernel_test)
```

The one-shot `clinical_kernel(X_test, X_train)` infers numeric ranges from both
arguments, changing normalization with the test cohort. Prefer the fitted transform
above. The released one-shot Cython routine also allocates its range buffer by
row count while writing one value per numeric feature: avoid that routine when
numeric features outnumber rows (source finding; unsafe case not executed).
Put `ClinicalKernelTransform()` inside the pipeline for CV so its ranges
and reference rows are learned afresh in every fold. Out-of-training-range values
can produce 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

