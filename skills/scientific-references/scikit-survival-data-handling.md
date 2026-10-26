---
id: sciref-scikit-survival-data-handling
name: "Scientific Ref: Data handling and leakage-safe preprocessing"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scikit-survival): Data handling and leakage-safe preprocessing"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scikit survival handling"
  - "data handling and leakage-safe preprocessing"
keywords:
  - "scikit"
  - "survival"
  - "handling"
  - "specialized"
  - "scientific"
  - "reference"
---

# Data handling and leakage-safe preprocessing

Verified for scikit-survival 0.28.0 on 2026-10-01.

## Standard right-censored outcome

scikit-survival estimators expect a one-dimensional NumPy structured array with
exactly two fields:

1. a boolean event indicator (`True`=event observed, `False`=right-censored);
2. a floating-point observed time (event or censoring time).

Field names are configurable, but field order and meaning are fixed.

```python
from sksurv.util import Surv

y = Surv.from_arrays(
    event=[True, False, True],
    time=[2.5, 4.0, 7.25],
    name_event="event",
    name_time="time",
)
assert y.dtype.names == ("event", "time")
```

`Surv.from_arrays()` accepts boolean or strict 0/1 event values.
`Surv.from_dataframe(event, time, data)` accepts pandas and, in 0.28, Polars
DataFrames:

```python
y = Surv.from_dataframe("event", "time", frame)
```

Do not use `astype(bool)` on unvalidated strings: `"False"` is a non-empty string
and therefore converts to `True`. Validate accepted values explicitly.

## Competing-risk outcome is different

`Surv` is not the input contract for nonparametric competing-risk cumulative
incidence. Use two arrays:

```python
# 0 = right-censored; 1..K = mutually exclusive causes
event_code = frame["status"].to_numpy(dtype=int)
observed_time = frame["time"].to_numpy(dtype=float)
```

Validate integer cause codes before the integer cast: `.to_numpy(dtype=int)` can
silently truncate fractional labels. Positive cause codes must be understood before modeling. Do not collapse them to
boolean until the estimand explicitly requires all-cause event status or a
cause-specific hazard outcome. See `competing-risks.md`.

## Minimum validation

Before splitting:

- event and time lengths match feature rows;
- standard event values are boolean/0/1;
- competing-risk codes are non-negative integers and 0 means censoring;
- time is numeric, finite, and strictly positive;
- outcomes are not included among predictors;
- feature names are unique and schema roles are explicit;
- repeated entities, temporal ordering, or sites are identified for the split;
- every planned training/CV fold contains events and enough comparable pairs;
  event-stratified CV in the bundled trainer also requires censored rows;
- missingness is described, but imputation is not yet fitted.

The bundled validator checks outcome coding, positive finite times, feature exclusion,
and the local CSV schema. Group independence, fold support, temporal ordering and
missingness interpretation require the study-specific review above. Strictly positive
times are a helper policy; some native nonparametric APIs permit zero.

Validate bounded local CSV input:

```bash
python skills/scikit-survival/scripts/validate_survival_csv.py \
  --input data.csv \
  --event-column event \
  --time-column time \
  --feature-columns x1,x2,group \
  --structured-output outcome.npy
```

The `.npy` file contains a non-object structured array and can be loaded with
`numpy.load(path, allow_pickle=False)`.

## Split before learned preprocessing

This order is mandatory:

1. validate types and outcome coding;
2. split rows;
3. fit imputation, encoding, scaling, and feature selection on training rows;
4. transform validation/test rows with training-fitted state;
5. fit the survival estimator;
6. evaluate once on the held-out rows.

Computing medians, category levels, scaling moments, univariate scores, or
regularization paths on all rows leaks validation/test information.

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.25,
    stratify=y["event"],
    random_state=20260723,
)
```

Event stratification does not guarantee balanced follow-up times. Inspect each
split. Use group-aware splitting for repeated entities and time-respecting
splitting for future-deployment questions. A random split is not automatically
appropriate.

## Explicit heterogeneous pipeline

Use scikit-learn's `ColumnTransformer` when numeric and categorical columns need
different imputers or when unseen categories must be handled explicitly.

```python
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sksurv.linear_model import CoxPHSurvivalAnalysis

numeric_pipe = make_pipeline(
    SimpleImputer(strategy="median"),
    StandardScaler(),
)
categorical_pipe = make_pipeline(
    SimpleImputer(strategy="most_frequent"),
    OneHotEncoder(
        handle_unknown="ignore",
        drop="first",
        sparse_output=False,
    ),
)
preprocess = ColumnTransformer(
    [
        ("numeric", numeric_pipe, numeric_columns),
        ("categorical", categorical_pipe, categorical_columns),
    ],
    sparse_threshold=0.0,
)
pipeline = make_pipeline(
    preprocess,
    CoxPHSurvivalAnalysis(alpha=0.1, ties="efron"),
)
pipeline.fit(X_train, y_train)
```

Keep the estimator in the same pipeline used by cross-validation so each fold
fits its own preprocessing state.

### scikit-survival encoder

`sksurv.preprocessing.OneHotEncoder(allow_drop=True)`:

- treats pandas `category`/`object` and Polars categorical/enum/string columns as
  categorical;
- leaves non-categorical column order in place;
- drops one category per categorical feature;
- returns the same DataFrame library as its input;
- requires `fit` and `transform` to use the same DataFrame library;
- supports `get_feature_names_out()` and pipeline use.

It is convenient for already clean DataFrames:

```python
from sklearn.pipeline import make_pipeline
from sksurv.preprocessing import OneHotEncoder

pipeline = make_pipeline(
    OneHotEncoder(),
    CoxPHSurvivalAnalysis(alpha=0.1),
)
pipeline.fit(X_train, y_train)
```

For custom files, an explicit `ColumnTransformer` usually makes missing-value,
unknown-category, and scaling behavior easier to audit.

`encode_categorical()` is a one-shot transformation, not a fitted train/test
transformer. Do not call it separately on all data or independently on train and
test when category sets can differ.

## Scaling and missing values

- Scale Coxnet, survival SVM, IPC ridge, and other coefficient/penalty models.
- Tree ensembles generally do not require scaling.
- Impute inside the pipeline unless the selected estimator explicitly supports the
  observed missing-value pattern.
- SurvivalTree, RandomSurvivalForest, and Ext

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

