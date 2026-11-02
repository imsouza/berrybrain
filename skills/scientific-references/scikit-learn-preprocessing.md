---
id: sciref-scikit-learn-preprocessing
name: "Scientific Ref: Data Preprocessing and Feature Engineering Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scikit-learn): Data Preprocessing and Feature Engineering Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scikit learn preprocessing"
  - "data preprocessing and feature engineering reference"
keywords:
  - "scikit"
  - "learn"
  - "preprocessing"
  - "specialized"
  - "scientific"
  - "reference"
---

# Data Preprocessing and Feature Engineering Reference

Targets scikit-learn 1.9.1. Snippets with caller-supplied data/columns are illustrative; fit all learned preprocessing inside the training folds when estimating predictive performance.

## Overview

Data preprocessing transforms raw data into a format suitable for machine learning models. This includes scaling, encoding, handling missing values, and feature engineering.

## Feature Scaling and Normalization

### StandardScaler

**StandardScaler (`sklearn.preprocessing.StandardScaler`)**
- Standardizes features to zero mean and unit variance
- Formula: z = (x - mean) / std
- Use when: Different feature scales distort a distance, kernel, or regularization penalty; standardization does not make data Gaussian
- Often useful for SVM, KNN, neural networks, PCA, and regularized linear models; choose scales using scientific units and noise. For sparse data use `with_mean=False`
- Example:
```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)  # Use same parameters as training

# Access learned parameters
print(f"Mean: {scaler.mean_}")
print(f"Std: {scaler.scale_}")
```

### MinMaxScaler

**MinMaxScaler (`sklearn.preprocessing.MinMaxScaler`)**
- Scales features to a given range (default [0, 1])
- Formula: X_scaled = (X - X.min) / (X.max - X.min)
- Training values map to the requested range; unseen values can exceed it unless `clip=True`. Clipping can hide distribution shift
- Sensitive to outliers
- Example:
```python
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler(feature_range=(0, 1))
X_scaled = scaler.fit_transform(X_train)

# Custom range
scaler = MinMaxScaler(feature_range=(-1, 1))
X_scaled = scaler.fit_transform(X_train)
```

### RobustScaler

**RobustScaler (`sklearn.preprocessing.RobustScaler`)**
- Scales using median and interquartile range (IQR)
- Formula: X_scaled = (X - median) / IQR
- Use when: Data contains outliers
- Robust to outliers
- Example:
```python
from sklearn.preprocessing import RobustScaler

scaler = RobustScaler()
X_scaled = scaler.fit_transform(X_train)
```

### Normalizer

**Normalizer (`sklearn.preprocessing.Normalizer`)**
- Normalizes samples individually to unit norm
- Common norms: 'l1', 'l2', 'max'
- Use when: Need to normalize each sample independently (e.g., text features)
- Example:
```python
from sklearn.preprocessing import Normalizer

normalizer = Normalizer(norm='l2')  # Euclidean norm
X_normalized = normalizer.fit_transform(X)
```

### MaxAbsScaler

**MaxAbsScaler (`sklearn.preprocessing.MaxAbsScaler`)**
- Scales by maximum absolute value
- Training range lies within [-1, 1]; new extrema can exceed it
- Doesn't shift/center data (preserves sparsity)
- Use when: Data is already centered or sparse
- Example:
```python
from sklearn.preprocessing import MaxAbsScaler

scaler = MaxAbsScaler()
X_scaled = scaler.fit_transform(X_sparse)
```

## Encoding Categorical Variables

### OneHotEncoder

**OneHotEncoder (`sklearn.preprocessing.OneHotEncoder`)**
- Creates binary columns for each category
- Use when: Nominal categories (no order), tree-based models or linear models
- Example:
```python
from sklearn.preprocessing import OneHotEncoder

encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
X_encoded = encoder.fit_transform(X_categorical)

# Get feature names
feature_names = encoder.get_feature_names_out(['color', 'size'])

# Handle unknown categories during transform
X_test_encoded = encoder.transform(X_test_categorical)
```

### OrdinalEncoder

**OrdinalEncoder (`sklearn.preprocessing.OrdinalEncoder`)**
- Encodes categories as integers
- Use when: Ordinal categories (ordered), or tree-based models
- Example:
```python
from sklearn.preprocessing import OrdinalEncoder

# Default sorted category order is not necessarily a scientific ordering
encoder = OrdinalEncoder()
X_encoded = encoder.fit_transform(X_categorical)

# Custom ordering
encoder = OrdinalEncoder(categories=[['small', 'medium', 'large']])
X_encoded = encoder.fit_transform(X_categorical)
```

### LabelEncoder

**LabelEncoder (`sklearn.preprocessing.LabelEncoder`)**
- Encodes target labels (y) as integers
- Use for: Target variable encoding
- Example:
```python
from sklearn.preprocessing import LabelEncoder

le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Decode back
y_decoded = le.inverse_transform(y_encoded)
print(f"Classes: {le.classes_}")
```

### Target Encoding (with internal cross-fitting)

```python
from sklearn.preprocessing import TargetEncoder
from sklearn.model_selection import StratifiedKFold

encoder = TargetEncoder(cv=StratifiedKFold(5, shuffle=True, random_state=42))
X_train_encoded = encoder.fit_transform(X_train_categorical, y_train)
X_test_encoded = encoder.transform(X_test_categorical)
```

`fit_transform` uses out-of-fold encodings for training rows, while `fit(...).transform(...)` does not; they intentionally differ. Put the encoder inside the model pipeline for outer CV. In 1.9, custom internal splitters are supported if every row occurs in exactly one validation fold; use metadata routing for groups. Ordinary `TimeSeriesSplit` does not satisfy that partition requirement. Use a study-specific causal encoding design for forecasting. Plain shuffled folds assume independent rows. The old encoder `shuffle` and `random_state` parameters are deprecated; configure the splitter instead. Numeric integer regression targets may be inferred as multiclass, so set `target_type='continuous'` when appropriate.

## Non-linear Transformations

### Power Transforms

**PowerTransformer**
- Makes data more Gaussian-like
- Methods: 'yeo-johnson' (works with negative values), 'box-cox' (positive only)
- Use when: Data is skewed, algorithm assumes normality
- Example:
```python
from sklearn.preprocessing import PowerTransformer

# Yeo-Johnson (handles negative values)
pt = PowerTransformer(method='yeo-johnson', standardize=True)
X_transformed = pt.fit_transform(X)

# Box-Cox (positive values only)
pt = PowerTransformer(method='box-cox', standardize=True)
X_transformed = pt.fit_transform(X)
```

### Quantile Transformation

**QuantileTransformer**
- Transforms features to follow uniform or normal distribution
- Robust to outliers
- Use when: Want to reduce outlier impact
- Example:
```python
from sklearn.preprocessing import QuantileTransformer

# Transform to uniform distribut

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

