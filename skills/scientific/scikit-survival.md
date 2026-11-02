---
id: sci-scikit-survival
name: "Scientific: scikit-survival"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Builds, evaluates, and audits right-censored or competing-risk survival workflows with scikit-survival, including leakage-safe preprocessing, model selection, probability prediction, and censoring-aware metrics."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "scikit survival"
  - "scikit-survival"
keywords:
  - "scikit"
  - "survival"
  - "builds"
  - "evaluates"
  - "audits"
  - "right"
  - "censored"
  - "competing"
---

# scikit-survival

## Scope

Use this skill for scikit-survival 0.28.0 workflows involving:

- right-censored structured outcomes;
- Cox PH, Coxnet, IPC ridge, survival trees, forests, boosting, and SVMs;
- discrimination, prediction error, calibration-oriented checks, and time-dependent prediction;
- nonparametric cumulative incidence with competing risks;
- scikit-learn pipelines, nested model selection, and reproducible reports.

scikit-survival primarily models right-censored outcomes. Its built-in competing-risk
support is nonparametric cumulative incidence; it does not provide Fine-Gray regression.
Do not present model output as clinical advice, causal evidence, or proof of clinical
utility.

Python snippets using study-defined variables such as `X_train`, `y_train`,
`frame`, or `times` are illustrative integration templates. The native regression
tests and local CLI smoke runs use small synthetic fixtures; they do not validate
an unprovided study, clinical dataset, or every optional dataframe backend.

## Current release and installation

Verified 2026-10-01:

- Latest stable: **scikit-survival 0.28.0**, released 2026-07-05.
- Python: **3.11 or later**; PyPI wheels cover CPython 3.11-3.14 on Linux
  x86-64, macOS x86-64/ARM64, and Windows x86-64.
- Runtime bounds: NumPy >=2.0.0, pandas >=2.2.0, SciPy >=1.13.0,
  scikit-learn >=1.9.0,<1.10, OSQP >=1.0.2, narwhals >=2.0.1.
- 0.28 adds pandas/Polars estimator support through narwhals and removes
  `criterion` from `GradientBoostingSurvivalAnalysis`.

The native refresh tests used Python 3.13 and the following snapshot (NumPy 2.5.1
was cached; this is a tested snapshot, not a claim that every pin is newest).
Create an isolated environment:

```bash
uv venv .venv-survival --python 3.13
source .venv-survival/bin/activate
uv pip install \
  "scikit-survival==0.28.0" \
  "scikit-learn==1.9.1" \
  "numpy==2.5.1" \
  "pandas==3.0.6" \
  "scipy==1.18.1" \
  "ecos==2.0.14" \
  "osqp==1.1.3" \
  "joblib==1.6.0" \
  "numexpr==2.14.2" \
  "narwhals==2.26.0"
```

Binary wheels are preferred. A source build requires a C/C++ compiler; OSQP may
also require CMake. This skill is MIT-licensed; the upstream scikit-survival package
is GPL-3.0-or-later, so review upstream licensing before redistribution.

## Non-negotiable workflow

1. **Define the estimand and event coding.** Decide whether the target is
   all-event survival, cause-specific hazard, or cause-specific cumulative incidence.
2. **Validate outcomes.** Standard estimators need a two-field structured array:
   boolean event first, observed time second. Competing-risk CIF instead needs a
   separate integer event vector: 0=censored, 1..K=causes.
3. **Split before learned preprocessing.** Never fit imputers, encoders, scalers,
   feature selectors, or alpha choices on all rows before splitting.
4. **Fit preprocessing inside a pipeline.** Unknown categories and missingness must
   be handled using training-fold state only.
5. **Tune without reusing evaluation data.** Use nested CV when reporting
   cross-validated tuned performance, or reserve a truly untouched final holdout.
6. **Fit censoring distributions on training data.** IPCW concordance, dynamic AUC,
   and Brier metrics receive `survival_train`, never a pooled train+test outcome.
7. **Restrict evaluation times.** Use a strictly increasing grid inside test
   follow-up and below the end of training support where the estimated censoring
   survival remains positive.
8. **Match predictions to metrics.** Concordance/dynamic AUC consume higher-is-riskier
   scores. Brier metrics consume survival probabilities with shape
   `(n_test, n_times)`, not risk scores or unevaluated step functions.
9. **Handle competing causes explicitly.** Standard survival probabilities and CIFs
   answer different questions. Never estimate event-specific probability with
   `1 - Kaplan-Meier` while censoring competing events.
10. **Report limits.** Separate discrimination, calibration, prediction error,
    and cumulative incidence. None alone establishes decision or clinical utility.

## Outcome construction

```python
from sksurv.util import Surv

y = Surv.from_arrays(event=event_bool, time=observed_time)
# Equivalent for pandas or Polars:
y = Surv.from_dataframe("event", "time", frame)
```

The first field is boolean (`True`=event, `False`=right-censored); the second is
floating-point time. Field names may vary, but field order and meaning may not.
Use `references/data-handling.md` before loading custom or competing-risk data.

## Leakage-safe pipeline

```python
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sksurv.linear_model import CoxPHSurvivalAnalysis

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y["event"], random_state=20260723
)

preprocess = ColumnTransformer(
    [
        ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric),
        (
            "cat",
            make_pipeline(
                SimpleImputer(strategy="most_frequent"),
                OneHotEncoder(handle_unknown="ignore", drop="first", sparse_output=False),
            ),
            categorical,
        ),
    ],
    sparse_threshold=0.0,
)
model = make_pipeline(preprocess, CoxPHSurvivalAnalysis(alpha=0.1, ties="efron"))
model.fit(X_train, y_train)
risk = model.predict(X_test)
```

The split precedes every learned transformation. For repeated or grouped records,
use a group-aware split; for temporal deployment, use a time-respecting split.

## Model choice

- `CoxPHSurvivalAnalysis`: interpretable log-hazard coefficients under proportional
  hazards; `alpha` is ridge shrinkage and `ties` is `"breslow"` or `"efron"`.
- `CoxnetSurvivalAnalysis`: LASSO/elastic-net path for high-dimensional data.
  `l1_ratio` is in `(0, 1]`; use `fit_baseline_model=True` before requesting
  survival or cumulative-hazard functions.
- `IPCRidge`: IPC-weighted ridge AFT model; `predict()` returns original-time values (the fitted objective uses log time),
  not a Cox risk score.
- `RandomSurvivalForest` / `ExtraSurvivalTrees`: nonlinear survival and cumulative
  hazard predictions; use permutation importance, not impurity importance.
- `GradientBoostingSurvivalAnalysis`: tree boosting with `"coxph"`, `"squared"`,
  or `"i

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

