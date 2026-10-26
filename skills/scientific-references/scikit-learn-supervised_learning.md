---
id: sciref-scikit-learn-supervised-learning
name: "Scientific Ref: Supervised Learning Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scikit-learn): Supervised Learning Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scikit learn supervised learning"
  - "supervised learning reference"
keywords:
  - "scikit"
  - "learn"
  - "supervised"
  - "learning"
  - "specialized"
  - "scientific"
  - "reference"
---

# Supervised Learning Reference

Targets scikit-learn 1.9.1. Snippets with caller-supplied data/columns are illustrative; fit all learned preprocessing inside the training folds when estimating predictive performance.

## Overview

Supervised learning algorithms learn from labeled training data to make predictions on new data. Scikit-learn provides comprehensive implementations for both classification and regression tasks.

## Linear Models

### Regression

**Linear Regression (`sklearn.linear_model.LinearRegression`)**
- Ordinary least squares regression
- Ordinary least squares; choices include intercept, positivity constraints, and sparse-solver tolerance
- Use when: Linear relationships, interpretability matters
- Example:
```python
from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(X_train, y_train)
predictions = model.predict(X_test)
```

**Ridge Regression (`sklearn.linear_model.Ridge`)**
- L2 regularization to prevent overfitting
- Key parameter: `alpha` (regularization strength, default=1.0)
- Use when: Multicollinearity present, need regularization
- Example:
```python
from sklearn.linear_model import Ridge

model = Ridge(alpha=1.0)
model.fit(X_train, y_train)
```

**Lasso (`sklearn.linear_model.Lasso`)**
- L1 regularization with feature selection
- Key parameter: `alpha` (regularization strength)
- Use when: Want sparse models, feature selection
- Can reduce some coefficients to exactly zero
- Example:
```python
from sklearn.linear_model import Lasso

model = Lasso(alpha=0.1)
model.fit(X_train, y_train)
# Check which features were selected
print(f"Non-zero coefficients: {sum(model.coef_ != 0)}")
```

**ElasticNet (`sklearn.linear_model.ElasticNet`)**
- Combines L1 and L2 regularization
- Key parameters: `alpha`, `l1_ratio` (0=Ridge, 1=Lasso)
- Use when: Need both feature selection and regularization
- Example:
```python
from sklearn.linear_model import ElasticNet

model = ElasticNet(alpha=0.1, l1_ratio=0.5)
model.fit(X_train, y_train)
```

### Classification

**Logistic Regression (`sklearn.linear_model.LogisticRegression`)**
- Binary and multiclass classification
- Key parameters: `C` (inverse regularization), `l1_ratio` (0=L2, 1=L1, between for elastic net)
- Returns probability estimates
- Use when: Need probabilistic predictions, interpretability
- `penalty` is deprecated since 1.8; use `l1_ratio`. `lbfgs` supports only L2 (`l1_ratio=0`); use `saga` for elastic net. Use `C=np.inf` for no regularization
- Example:
```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(C=1.0, l1_ratio=0.0, max_iter=1000)
model.fit(X_train, y_train)
probas = model.predict_proba(X_test)
```

**Stochastic Gradient Descent (SGD)**
- `SGDClassifier`, `SGDRegressor`
- Efficient for large-scale learning
- Key parameters: `loss`, `penalty`, `alpha`, `learning_rate`
- Use when: Very large datasets (>10^4 samples)
- Example:
```python
from sklearn.linear_model import SGDClassifier

model = SGDClassifier(loss='log_loss', max_iter=1000, tol=1e-3)
model.fit(X_train, y_train)
```

## Support Vector Machines

**SVC (`sklearn.svm.SVC`)**
- Classification with kernel methods
- Key parameters: `C`, `kernel` ('linear', 'rbf', 'poly'), `gamma`
- Use when: Small to medium datasets, complex decision boundaries
- Note: Does not scale well to large datasets
- Example:
```python
from sklearn.svm import SVC

# Linear kernel for linearly separable data
model_linear = SVC(kernel='linear', C=1.0)

# RBF kernel for non-linear data
model_rbf = SVC(kernel='rbf', C=1.0, gamma='scale')
model_rbf.fit(X_train, y_train)
```

**SVR (`sklearn.svm.SVR`)**
- Regression with kernel methods
- Similar parameters to SVC
- Additional parameter: `epsilon` (tube width)
- Example:
```python
from sklearn.svm import SVR

model = SVR(kernel='rbf', C=1.0, epsilon=0.1)
model.fit(X_train, y_train)
```

## Decision Trees

**DecisionTreeClassifier / DecisionTreeRegressor**
- Non-parametric model learning decision rules
- Key parameters:
  - `max_depth`: Maximum tree depth (prevents overfitting)
  - `min_samples_split`: Minimum samples to split a node
  - `min_samples_leaf`: Minimum samples in leaf
  - `criterion`: 'gini', 'entropy' for classification; 'squared_error', 'absolute_error' for regression
- Use when: Need interpretable model, non-linear relationships, mixed feature types
- Prone to overfitting - use ensembles or pruning
- Example:
```python
from sklearn.tree import DecisionTreeClassifier

model = DecisionTreeClassifier(
    max_depth=5,
    min_samples_split=20,
    min_samples_leaf=10,
    criterion='gini'
)
model.fit(X_train, y_train)

# Visualize the tree
from sklearn.tree import plot_tree
plot_tree(model, feature_names=feature_names, class_names=class_names)
```

## Ensemble Methods

### Random Forests

**RandomForestClassifier / RandomForestRegressor**
- Ensemble of decision trees with bagging
- Key parameters:
  - `n_estimators`: Number of trees (default=100)
  - `max_depth`: Maximum tree depth
  - `max_features`: Features to consider for splits ('sqrt', 'log2', or int)
  - `min_samples_split`, `min_samples_leaf`: Control tree growth
- Use when: High accuracy needed, can afford computation
- Provides impurity importance, which favors high-cardinality features; use held-out permutation importance to assess predictive contribution, not causality
- Example:
```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    max_features='sqrt',
    n_jobs=-1  # Use all CPU cores
)
model.fit(X_train, y_train)

# Feature importance
importances = model.feature_importances_
```

### Gradient Boosting

**GradientBoostingClassifier / GradientBoostingRegressor**
- Sequential ensemble building trees on residuals
- Key parameters:
  - `n_estimators`: Number of boosting stages
  - `learning_rate`: Shrinks contribution of each tree
  - `max_depth`: Depth of individual trees (typically 3-5)
  - `subsample`: Fraction of samples for training each tree
- Use when: Need high accuracy, can afford training time
- Compare on a held-out design; no estimator is universally best
- Example:
```python
from sklearn.ensemble import GradientBoostingClassifier

model = GradientBoostingClassifier(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=3,
    subsample=0.8
)
model.fit(X_train, y_train)
```

**HistGradientBoostingClassifier / HistGradientBoostingRegressor**
- Faster gradient boosting with hist

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

