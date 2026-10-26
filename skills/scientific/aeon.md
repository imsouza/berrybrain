---
id: sci-aeon
name: "Scientific: aeon"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "This skill should be used for time series machine learning tasks including classification, regression, clustering, forecasting, anomaly detection, segmentation, and similarity search. Use when working with temporal data, sequential patterns, or time-indexed observations requiring"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "aeon"
keywords:
  - "aeon"
  - "should"
  - "used"
  - "time"
  - "series"
  - "machine"
  - "learning"
---

# Aeon Time Series Machine Learning

## Overview

Aeon is a scikit-learn compatible Python toolkit for time series machine learning ([aeon-toolkit.org](https://www.aeon-toolkit.org/)). It provides algorithms across classification, regression, clustering, forecasting, anomaly detection, segmentation, similarity search, distances, transformations, benchmarking, and visualization — with a consistent estimator API.

**Version note:** Reviewed against **aeon 1.6.0** (Python 3.13). Small synthetic checks cover classification, regression, clustering, forecasts, preprocessing, distances, search, segmentation, matrix profiles, metrics, and local dataset I/O. Remote archive and TensorFlow training snippets are illustrative; they were not executed during this review. Reference catalogs are selected methods, not exhaustive lists. See the [1.6 release notes](https://www.aeon-toolkit.org/en/stable/changelogs/v1.6.html).

## When to Use This Skill

Apply this skill when:
- Classifying or predicting from time series data
- Detecting anomalies or change points in temporal sequences
- Clustering similar time series patterns
- Forecasting future values
- Finding repeated patterns (motifs) or unusual subsequences (discords)
- Comparing time series with specialized distance metrics
- Extracting features from temporal data

## Installation

Requires **Python 3.11-3.14**. Pin the reviewed release for reproducibility:

```bash
uv pip install "aeon==1.6.0"
```

Install only the extras required by the chosen estimator. The broad optional set is available as:

```bash
uv pip install "aeon[all_extras]==1.6.0"
```

On zsh, quote the extras: `uv pip install "aeon[all_extras]==1.6.0"`.

For the matrix-profile examples: `uv pip install "aeon==1.6.0" stumpy`. Range precision/recall/F-score depend on `prts`, whose current NumPy<2 requirement conflicts with aeon 1.6; use the runnable AUC metrics or a separately validated environment. Deep learning estimators use TensorFlow. Inspect an estimator's `python_dependencies` tag before installing optional packages.

### Experimental modules

Upstream treats **forecasting**, **anomaly_detection**, **segmentation**, **similarity_search**, and **visualisation** as experimental — interfaces may change between minor releases. Prefer stable modules (classification, regression, clustering, distances, transformations) for production pipelines unless you need these tasks.

## Core Capabilities

### 1. Time Series Classification

Categorize time series into predefined classes. See `references/classification.md` for selected methods.

**Quick Start:**
```python
from aeon.classification.convolution_based import RocketClassifier
from aeon.datasets import load_classification

# Load data
X_train, y_train = load_classification("GunPoint", split="train")
X_test, y_test = load_classification("GunPoint", split="test")

# Train classifier
clf = RocketClassifier(n_kernels=10000)
clf.fit(X_train, y_train)
accuracy = clf.score(X_test, y_test)
```

**Algorithm Selection:**
- **Speed + Performance**: `MiniRocketClassifier`, `Arsenal`
- **Accuracy candidates to validate**: `HIVECOTEV2`, `InceptionTimeClassifier`
- **Interpretability**: `ShapeletTransformClassifier`, `Catch22Classifier`
- **Small Datasets**: `KNeighborsTimeSeriesClassifier` with DTW distance

### 2. Time Series Regression

Predict continuous values from time series. See `references/regression.md` for algorithms.

**Quick Start:**
```python
from aeon.regression.convolution_based import RocketRegressor
from aeon.datasets import load_regression

X_train, y_train = load_regression("Covid3Month", split="train")
X_test, y_test = load_regression("Covid3Month", split="test")

reg = RocketRegressor()
reg.fit(X_train, y_train)
predictions = reg.predict(X_test)
```

### 3. Time Series Clustering

Group similar time series without labels. See `references/clustering.md` for methods.

**Quick Start:**
```python
from aeon.clustering import TimeSeriesKMeans

clusterer = TimeSeriesKMeans(
    n_clusters=3,
    distance="dtw",
    averaging_method="ba"
)
labels = clusterer.fit_predict(X_train)
centers = clusterer.cluster_centers_
```

### 4. Forecasting

Predict future time series values (experimental module in aeon 1.x). See `references/forecasting.md` for forecasters.

**Quick Start:**
```python
import numpy as np
from aeon.forecasting import NaiveForecaster
from aeon.forecasting.stats import ARIMA

y_train = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])

# predict returns one value at the configured horizon, not a 5-value vector
naive = NaiveForecaster(strategy="drift", horizon=5)
naive.fit(y_train)
y_at_5 = naive.predict(y_train)  # 15.0

# ARIMA uses p/d/q (not order=); multi-step via iterative_forecast
arima = ARIMA(p=1, d=1, q=1)
y_pred = arima.iterative_forecast(y_train, prediction_horizon=5)  # fits once
```

### 5. Anomaly Detection

Identify unusual patterns or outliers. See `references/anomaly_detection.md` for detectors.

**Quick Start:**
```python
from aeon.anomaly_detection.series.distance_based import STOMP

detector = STOMP(window_size=50)
anomaly_scores = detector.fit_predict(y)

# Higher scores indicate anomalies
threshold = np.percentile(anomaly_scores, 95)
anomalies = anomaly_scores > threshold
```

### 6. Segmentation

Partition time series into regions with change points. See `references/segmentation.md`.

**Quick Start:**
```python
from aeon.segmentation import ClaSPSegmenter

segmenter = ClaSPSegmenter()
change_points = segmenter.fit_predict(y)
```

### 7. Similarity Search

Find similar patterns within or across time series. See `references/similarity_search.md`.

**Quick Start:**
```python
from aeon.similarity_search.subsequence import MASS

# X_train: (n_cases, n_channels, n_timepoints); query: (n_channels, 20)
searcher = MASS(length=20, normalize=True).fit(X_train)
query = X_train[0, :, :20]
indices, distances = searcher.predict(query, k=3, X_index=(0, 0))
# indices rows are (case_index, window_start); self-match is excluded
```

## Feature Extraction and Transformations

Transform time series for feature engineering. See `references/transformations.md`.

**ROCKET Features:**
```python
from aeon.transformations.collection.convolution_based import Rocket

rocket = Rocket()
X_features = rocket.fit_transform(X_train)

# Use features with any sklearn classifier
from sklearn.ensemble import RandomForestClassifier
clf = RandomForestClassifier()
clf.fit(X_features, y_train)
```

**Statistical Features:**
```

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

