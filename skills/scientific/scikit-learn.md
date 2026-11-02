---
id: sci-scikit-learn
name: "Scientific: scikit-learn"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Supports machine learning in Python with scikit-learn. Applies when working with supervised learning (classification, regression), unsupervised learning (clustering, dimensionality reduction), model evaluation, hyperparameter tuning, preprocessing, or building ML pipelines. Provi"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "scikit learn"
  - "scikit-learn"
keywords:
  - "scikit"
  - "learn"
  - "supports"
  - "machine"
  - "learning"
  - "python"
---

# Scikit-learn

## Overview

This skill provides comprehensive guidance for machine learning tasks using scikit-learn, the industry-standard Python library for classical machine learning. Use this skill for classification, regression, clustering, dimensionality reduction, preprocessing, model evaluation, and building production-ready ML pipelines.

## Installation

Targets **scikit-learn 1.9.1**, verified with Python 3.13. The release requires Python 3.11+; use its published wheels for your interpreter/platform. See the [1.9 release notes](https://scikit-learn.org/stable/whats_new/v1.9.html). The bundled scripts and regression tests are executable examples. Reference snippets using caller-provided `X`, `y`, columns, or placeholders are illustrative adaptations, not complete standalone programs.

Install the PyPI package **`scikit-learn`** (not the deprecated `sklearn` package on PyPI). Import in code as `sklearn`.

```bash
# Install scikit-learn using uv
uv pip install "scikit-learn==1.9.1"

# Optional: plotting utilities and bundled script dependencies
uv pip install "scikit-learn[plots]==1.9.1" matplotlib pandas

# Commonly used with
uv pip install pandas numpy
```

Check your version:

```python
import sklearn
print(sklearn.__version__)
```

## When to Use This Skill

Use the scikit-learn skill when:

- Building classification or regression models
- Performing clustering or dimensionality reduction
- Preprocessing and transforming data for machine learning
- Evaluating model performance with cross-validation
- Tuning hyperparameters with grid or random search
- Creating ML pipelines for production workflows
- Comparing different algorithms for a task
- Working with both structured (tabular) and text data
- Need interpretable, classical machine learning approaches

## Quick Start

### Classification Example

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# Preprocess
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)

# Evaluate
y_pred = model.predict(X_test_scaled)
print(classification_report(y_test, y_pred))
```

### Complete Pipeline with Mixed Data

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import GradientBoostingClassifier

# Define feature types
numeric_features = ['age', 'income']
categorical_features = ['gender', 'occupation']

# Create preprocessing pipelines
numeric_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

categorical_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

# Combine transformers
preprocessor = ColumnTransformer([
    ('num', numeric_transformer, numeric_features),
    ('cat', categorical_transformer, categorical_features)
])

# Full pipeline
model = Pipeline([
    ('preprocessor', preprocessor),
    ('classifier', GradientBoostingClassifier(random_state=42))
])

# Fit and predict
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
```

## Core Capabilities

Five capability areas are documented in
[references/core_capabilities.md](references/core_capabilities.md), with per-topic detail
in [references/supervised_learning.md](references/supervised_learning.md),
[references/unsupervised_learning.md](references/unsupervised_learning.md),
[references/model_evaluation.md](references/model_evaluation.md),
[references/preprocessing.md](references/preprocessing.md), and
[references/pipelines_and_composition.md](references/pipelines_and_composition.md):

1. **Supervised learning** — classification and regression estimator families.
2. **Unsupervised learning** — clustering, decomposition, and manifold learning.
3. **Model evaluation and selection** — metrics, cross-validation, and hyperparameter search.
4. **Data preprocessing** — scaling, encoding, imputation, and feature selection.
5. **Pipelines and composition** — `Pipeline` and `ColumnTransformer`.

Always fit preprocessing inside a `Pipeline` so it is refit per cross-validation fold;
scaling or imputing before splitting leaks test information into training.

Two worked workflows are in
[references/common_workflows.md](references/common_workflows.md).

## Example Scripts

Run these commands from this skill directory; the clustering demo writes PNGs into the working directory. Its synthetic noise is seeded. The classification script assumes independent rows with enough observations per class for stratified CV; adapt both splits for grouped or temporal data.

### Classification Pipeline

Run a complete classification workflow with preprocessing, model comparison, hyperparameter tuning, and evaluation:

```bash
uv run --no-project --with scikit-learn==1.9.1 --with pandas --with matplotlib python scripts/classification_pipeline.py
```

This script demonstrates:
- Handling mixed data types (numeric and categorical)
- Model comparison using stratified cross-validation and balanced accuracy by default
- Hyperparameter tuning with GridSearchCV
- Comprehensive evaluation with multiple metrics
- Impurity feature importances, with their high-cardinality bias made explicit

### Clustering Analysis

Perform clustering analysis with algorithm comparison and visualization:

```bash
uv run --no-project --with scikit-learn==1.9.1 --with pandas --with matplotlib python scripts/clustering_analysis.py
```

This script demonstrates:
- Exploring candidate cluster counts (inertia/elbow and silhouette analysis)
- Comparing multiple clustering algorithms (K-Means, DBSCAN, Agglomerative, Gaussian Mixture)
- Reporting undefined metrics for degenerate clusterings and DBSCAN noise coverage
- Assessing internal geometry without treating it as proof of scientific clusters
- Visualizing results with PCA projection

## Reference Documentation

This skill includes comprehensive reference files for deep dives into specific topics:

### Quick 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

