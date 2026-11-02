---
id: sciref-scikit-learn-model-evaluation
name: "Scientific Ref: Model Selection and Evaluation Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scikit-learn): Model Selection and Evaluation Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scikit learn model evaluation"
  - "model selection and evaluation reference"
keywords:
  - "scikit"
  - "learn"
  - "model"
  - "evaluation"
  - "specialized"
  - "scientific"
  - "reference"
---

# Model Selection and Evaluation Reference

Targets scikit-learn 1.9.1. Snippets with caller-supplied data/columns are illustrative; fit all learned preprocessing inside the training folds when estimating predictive performance.

## Overview

Comprehensive guide for evaluating models, tuning hyperparameters, and selecting the best model using scikit-learn's model selection tools.

## Train-Test Split

### Basic Splitting

```python
from sklearn.model_selection import train_test_split

# Basic split (default 75/25)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

# With stratification (preserves class distribution)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)

# Three-way split (train/val/test)
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
```

Split by the independent unit: patients/specimens/sites and related molecules must not cross partitions. Future prediction requires temporal boundaries and available-at-prediction features. Integer index examples below assume NumPy arrays; use `.iloc[index]` for pandas. CV fold SD is descriptive, not a confidence interval, because folds overlap in training data.

## Cross-Validation

#Split by the independent unit: patients/specimens/sites and related molecules must not cross partitions. Future prediction requires temporal boundaries and available-at-prediction features. Integer index examples below assume NumPy arrays; use `.iloc[index]` for pandas. CV fold SD is descriptive, not a confidence interval, because folds overlap in training data.

## Cross-Validation Strategies

**KFold**
- Standard k-fold cross-validation
- Splits data into k consecutive folds
```python
from sklearn.model_selection import KFold

kf = KFold(n_splits=5, shuffle=True, random_state=42)
for train_idx, val_idx in kf.split(X):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
```

**StratifiedKFold**
- Preserves class distribution in each fold
- Use for imbalanced classification
```python
from sklearn.model_selection import StratifiedKFold

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for train_idx, val_idx in skf.split(X, y):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
```

**TimeSeriesSplit**
- For time series data
- Respects temporal order
```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, val_idx in tscv.split(X):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
```

**GroupKFold**
- Ensures samples from same group don't appear in both train and validation
- Use when samples are not independent
```python
from sklearn.model_selection import GroupKFold

gkf = GroupKFold(n_splits=5)
for train_idx, val_idx in gkf.split(X, y, groups=group_ids):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
```

**LeaveOneOut (LOO)**
- Each sample used as validation set once
- Use for very small datasets
- Computationally expensive
```python
from sklearn.model_selection import LeaveOneOut

loo = LeaveOneOut()
for train_idx, val_idx in loo.split(X):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
```

#Split by the independent unit: patients/specimens/sites and related molecules must not cross partitions. Future prediction requires temporal boundaries and available-at-prediction features. Integer index examples below assume NumPy arrays; use `.iloc[index]` for pandas. CV fold SD is descriptive, not a confidence interval, because folds overlap in training data.

## Cross-Validation Functions

**cross_val_score**
- Evaluate model using cross-validation
- Returns array of scores
```python
from sklearn.model_selection import cross_val_score
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100, random_state=42)
scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')

print(f"Scores: {scores}")
print(f"Mean: {scores.mean():.3f} (fold SD {scores.std():.3f})")
```

**cross_validate**
- More comprehensive than cross_val_score
- Can return multiple metrics and fit times
```python
from sklearn.model_selection import cross_validate

model = RandomForestClassifier(n_estimators=100, random_state=42)
cv_results = cross_validate(
    model, X, y, cv=5,
    scoring=['accuracy', 'precision_macro', 'recall_macro', 'f1_macro'],
    return_train_score=True,
    return_estimator=True  # Returns fitted estimators
)

print(f"Test accuracy: {cv_results['test_accuracy'].mean():.3f}")
print(f"Test precision: {cv_results['test_precision_macro'].mean():.3f}")
print(f"Fit time: {cv_results['fit_time'].mean():.3f}s")
```

**cross_val_predict**
- Get predictions for each sample when it was in validation set
- Useful for analyzing errors; requires each sample to appear in exactly one test fold. Pooled prediction metrics need not equal average fold scores
```python
from sklearn.model_selection import cross_val_predict

model = RandomForestClassifier(n_estimators=100, random_state=42)
y_pred = cross_val_predict(model, X, y, cv=5)

# Now can analyze predictions vs actual
from sklearn.metrics import confusion_matrix
cm = confusion_matrix(y, y_pred)
```

## Hyperparameter Tuning

### Grid Search

**GridSearchCV**
- Exhaustive search over parameter grid
- Tests all combinations
```python
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}

model = RandomForestClassifier(random_state=42)
grid_search = GridSearchCV(
    model, param_grid,
    cv=5,
    scoring='accuracy',
    n_jobs=-1,  # Use all CPU cores
    verbose=1
)

grid_search.fit(X_train, y_train)

print(f"Best parameters: {grid_search.best_params_}")
print(f"Best cross-validation score: {grid_search.best_score_:.3f}")
print(f"Test score: {grid_search.score(X_test, y_test):.3f}")

# Access best model
best_model = grid_search.best_estimator_

# View all results
import pandas as pd
results_df = pd.DataFrame(grid_search.cv_results_)
```

### Randomized Search

**Ran

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

