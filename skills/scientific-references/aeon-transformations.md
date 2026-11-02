---
id: sciref-aeon-transformations
name: "Scientific Ref: Transformations"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (aeon): Transformations"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "aeon transformations"
  - "transformations"
keywords:
  - "aeon"
  - "transformations"
  - "specialized"
  - "scientific"
  - "reference"
---

# Transformations

Aeon provides extensive transformation capabilities for preprocessing, feature extraction, and representation learning from time series data.

## Transformation Types

Aeon distinguishes between:
- **CollectionTransformers**: Transform multiple time series (collections)
- **SeriesTransformers**: Transform individual time series

## Collection Transformers

### Convolution-Based Feature Extraction

Fast, scalable feature generation using random kernels:

- `Rocket` - Random convolutional kernels
- `MiniRocket` - Simplified ROCKET for speed
- `MultiRocket` - Enhanced ROCKET variant
- `HydraTransformer` - Multi-resolution dilated convolutions
- `ROCKETGPU` - GPU-accelerated variant

**Use when**: Need fast, scalable features for any ML algorithm, strong baseline performance.

### Statistical Feature Extraction

Domain-agnostic features based on time series characteristics:

- `Catch22` - 22 canonical time-series characteristics
- `TSFresh` - Comprehensive automated feature extraction (100+ features)
- `TSFreshRelevant` - Feature extraction with relevance filtering
- `SevenNumberSummary` - Descriptive statistics (mean, std, quantiles)

**Use when**: Need interpretable features, domain-agnostic approach, or feeding traditional ML.

### Dictionary-Based Representations

Symbolic approximations for discrete representations:

- `SAX` - Symbolic Aggregate approXimation
- `PAA` - Piecewise Aggregate Approximation
- `SFA` - Symbolic Fourier Approximation
- `SFAFast` - Optimized SFA
- `SFAWhole` - SFA on entire series (no windowing)
- `BORF` - Bag-of-Receptive-Fields

**Use when**: Need discrete/symbolic representation, dimensionality reduction, interpretability.

### Shapelet-Based Features

Discriminative subsequence extraction:

- `RandomShapeletTransform` - Random discriminative shapelets
- `RandomDilatedShapeletTransform` - Dilated shapelets for multi-scale
- `SAST` - Scalable And Accurate Subsequence Transform
- `RSAST` - Randomized SAST

**Use when**: Need interpretable discriminative patterns, phase-invariant features.

### Interval-Based Features

Statistical summaries from time intervals:

- `RandomIntervals` - Features from random intervals
- `SupervisedIntervals` - Supervised interval selection
- `QUANTTransformer` - Quantile-based interval features

**Use when**: Predictive patterns localized to specific windows.

### Preprocessing Transformations

Data preparation and normalization:

- `MinMaxScaler` - Scale to [0, 1] range
- `Normalizer` - Z-normalization (zero mean, unit variance)
- `Centerer` - Center to zero mean
- `SimpleImputer` - Fill missing values
- `DownsampleTransformer` - Reduce temporal resolution
- `Tabularizer` - Convert time series to tabular format

**Use when**: Need standardization, missing value handling, format conversion.

### Specialized Transformations

Advanced analysis methods:

- `MatrixProfileTransformer` (series module) - Nearest-neighbor distance per subsequence; requires stumpy
- `DWTTransformer` - Discrete Wavelet Transform
- `AutocorrelationFunctionTransformer` - ACF computation
- `Dobin` (series module) - Distance-based Outlier BasIs using Neighbors
- `SignatureTransformer` - Path signature methods; aeon 1.6 uses RoughPy instead of esig
- `PLASeriesTransformer` (series module) - Piecewise Linear Approximation

`Normalizer` and `MinMaxScaler` scale each case/channel along time; they do not learn population-wide feature statistics. `Catch22` uses native features by default; `use_pycatch22` is deprecated in 1.6.

### Class Imbalance Handling

- `ADASYN` - Adaptive Synthetic Sampling
- `SMOTE` - Synthetic Minority Over-sampling
- `OHIT` - Over-sampling with Highly Imbalanced Time series

**Use when**: Classification with imbalanced classes. Apply samplers only inside training folds; sampler `fit_transform(X, y)` returns resampled `(X, y)`, so do not treat it as a feature-only transformer.

### Pipeline Composition

- `CollectionTransformerPipeline` - Chain multiple transformers

## Series Transformers

Transform individual time series (e.g., for preprocessing in forecasting).

### Statistical Analysis

- `AutoCorrelationSeriesTransformer` - Autocorrelation
- `StatsModelsACF` / `StatsModelsPACF` are deprecated in 1.6; prefer `AutoCorrelationSeriesTransformer` for ACF and a supported statsmodels PACF workflow when needed

### Smoothing and Filtering

Import smoothing classes from `aeon.transformations.series.smoothing`; `BKFilter` remains in `aeon.transformations.series`.

- `ExponentialSmoothing` - Exponentially weighted moving average
- `MovingAverage` - Simple sliding-window average
- `SavitzkyGolayFilter` - Polynomial smoothing
- `GaussianFilter` - Gaussian kernel smoothing
- `BKFilter` - Baxter-King bandpass filter
- `DiscreteFourierApproximation` - Fourier-based filtering

**Use when**: Need noise reduction, trend extraction, or frequency filtering.

### Dimensionality Reduction

- `PCASeriesTransformer` - Principal component analysis
- `PLASeriesTransformer` - Piecewise Linear Approximation

### Transformations

- `BoxCoxTransformer` - Variance stabilization
- `LogTransformer` - Logarithmic scaling
- `ClaSPTransformer` - Classification Score Profile

### Pipeline Composition

- `SeriesTransformerPipeline` (from `aeon.transformations.series.compose`) - Chain series transformers

## Quick Start: Feature Extraction

```python
from aeon.transformations.collection.convolution_based import Rocket
from aeon.classification.sklearn import RotationForestClassifier
from aeon.datasets import load_classification

# Load data
X_train, y_train = load_classification("GunPoint", split="train")
X_test, y_test = load_classification("GunPoint", split="test")

# Extract ROCKET features
rocket = Rocket()
X_train_features = rocket.fit_transform(X_train)
X_test_features = rocket.transform(X_test)

# Use with any sklearn classifier
clf = RotationForestClassifier()
clf.fit(X_train_features, y_train)
accuracy = clf.score(X_test_features, y_test)
```

## Quick Start: Preprocessing Pipeline

```python
from aeon.transformations.collection import (
    MinMaxScaler,
    SimpleImputer
)
from aeon.transformations.collection.compose import CollectionTransformerPipeline

# Build preprocessing pipeline
pipeline = CollectionTransformerPipeline([
    ('imputer', SimpleImputer(strategy='mean')),
    ('scaler', MinMaxScaler())
])

X_transformed = pipeline.fit_transform(X_train)
```

## Quick Start: Series Smoothing

```python
from aeon.transformations.series.smo

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

