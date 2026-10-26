---
id: sciref-scikit-learn-pipelines-and-composition
name: "Scientific Ref: Pipelines and Composite Estimators Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scikit-learn): Pipelines and Composite Estimators Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scikit learn pipelines composition"
  - "pipelines and composite estimators reference"
keywords:
  - "scikit"
  - "learn"
  - "pipelines"
  - "composition"
  - "specialized"
  - "scientific"
  - "reference"
---

# Pipelines and Composite Estimators Reference

Targets scikit-learn 1.9.1. Snippets with caller-supplied data/columns are illustrative; fit all learned preprocessing inside the training folds when estimating predictive performance.

## Overview

Pipelines chain multiple processing steps into a single estimator, preventing data leakage and simplifying code. They enable reproducible workflows and seamless integration with cross-validation and hyperparameter tuning.

## Pipeline Basics

### Creating a Pipeline

**Pipeline (`sklearn.pipeline.Pipeline`)**
- Chains transformers with a final estimator
- All intermediate steps must implement `fit` and `transform` (`fit_transform` is optional)
- Final step can be any estimator (transformer, classifier, regressor, clusterer)
- Example:
```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('pca', PCA(n_components=10)),
    ('classifier', LogisticRegression())
])

# Fit the entire pipeline
pipeline.fit(X_train, y_train)

# Predict using the pipeline
y_pred = pipeline.predict(X_test)
y_proba = pipeline.predict_proba(X_test)
```

### Using make_pipeline

**make_pipeline**
- Convenient constructor that auto-generates step names
- Example:
```python
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

pipeline = make_pipeline(
    StandardScaler(),
    PCA(n_components=10),
    SVC(kernel='rbf')
)

pipeline.fit(X_train, y_train)
```

## Accessing Pipeline Components

### Accessing Steps

```python
# By index
scaler = pipeline.steps[0][1]

# By name
scaler = pipeline.named_steps['scaler']
pca = pipeline.named_steps['pca']

# Using indexing syntax
scaler = pipeline['scaler']
pca = pipeline['pca']

# Get all step names
print(pipeline.named_steps.keys())
```

### Setting Parameters

```python
# Set parameters using double underscore notation
pipeline.set_params(
    pca__n_components=15,
    classifier__C=0.1
)

# Or during creation
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('pca', PCA(n_components=10)),
    ('classifier', LogisticRegression(C=1.0))
])
```

### Accessing Attributes

```python
# Access fitted attributes
pca_components = pipeline.named_steps['pca'].components_
explained_variance = pipeline.named_steps['pca'].explained_variance_ratio_

# Access intermediate transformations
X_scaled = pipeline.named_steps['scaler'].transform(X_test)
X_pca = pipeline.named_steps['pca'].transform(X_scaled)
```

## Hyperparameter Tuning with Pipelines

### Grid Search with Pipeline

```python
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', SVC())
])

param_grid = {
    'classifier__C': [0.1, 1, 10, 100],
    'classifier__gamma': ['scale', 'auto', 0.001, 0.01],
    'classifier__kernel': ['rbf', 'linear']
}

grid_search = GridSearchCV(pipeline, param_grid, cv=5, n_jobs=-1)
grid_search.fit(X_train, y_train)

print(f"Best parameters: {grid_search.best_params_}")
print(f"Best score: {grid_search.best_score_:.3f}")
```

### Tuning Multiple Pipeline Steps

```python
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('pca', PCA()),
    ('classifier', SVC())
])
# Every PCA candidate must fit within min(n_training_fold, n_features).
param_grid = {
    # PCA parameters
    'pca__n_components': [5, 10, 20, 50],

    # Classifier parameters
    'classifier__C': [0.1, 1, 10],
    'classifier__kernel': ['rbf', 'linear']
}

grid_search = GridSearchCV(pipeline, param_grid, cv=5)
grid_search.fit(X_train, y_train)
```

## ColumnTransformer

### Basic Usage

**ColumnTransformer (`sklearn.compose.ColumnTransformer`)**
- Apply different preprocessing to different columns
- Prevents preprocessing leakage only when placed inside the estimator passed to cross-validation
- Example:
```python
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

# Define column groups
numeric_features = ['age', 'income', 'hours_per_week']
categorical_features = ['gender', 'occupation', 'native_country']

# Create preprocessor
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ],
    remainder='passthrough'  # Keep other columns unchanged
)

X_transformed = preprocessor.fit_transform(X)
```

### With Pipeline Steps

```python
from sklearn.pipeline import Pipeline

numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ]
)

# Full pipeline with model
full_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', LogisticRegression())
])

full_pipeline.fit(X_train, y_train)
```

### Using make_column_transformer

```python
from sklearn.compose import make_column_transformer

preprocessor = make_column_transformer(
    (StandardScaler(), numeric_features),
    (OneHotEncoder(handle_unknown='ignore'), categorical_features),
    remainder='passthrough'
)
```

### Column Selection

```python
# By column names (if X is DataFrame)
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), ['age', 'income']),
    ('cat', OneHotEncoder(), ['gender', 'occupation'])
])

# By column indices
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), [0, 1, 2]),
    ('cat', OneHotEncoder(), [3, 4])
])

# By boolean mask
numeric_mask = [True, True, True, False, False]
categorical_mask = [False, False, False, True, True]

preprocessor = ColumnTransformer([
    ('num', StandardScaler(), numeric_mask),
    ('cat', OneHotEncoder(), categorical_mask)
])

# By callable
def is_numeric(X):
    return X.select_dtypes(include=['number']).columns.tolist()

preprocessor = C

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

