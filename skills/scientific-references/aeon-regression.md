---
id: sciref-aeon-regression
name: "Scientific Ref: Time Series Regression"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (aeon): Time Series Regression"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "aeon regression"
  - "time series regression"
keywords:
  - "aeon"
  - "regression"
  - "specialized"
  - "scientific"
  - "reference"
  - "time"
  - "series"
---

# Time Series Regression

Selected aeon 1.6 regressors predict one continuous target per series. This is distinct from forecasting future timepoints.

## Convolution-Based Regressors

Apply convolutional kernels for feature extraction:

- `HydraRegressor` - Multi-resolution dilated convolutions
- `RocketRegressor` - Random convolutional kernels
- `MiniRocketRegressor` - Simplified ROCKET for speed
- `MultiRocketRegressor` - Convolutional features from raw and differenced series with multiple pooling operators
- `MultiRocketHydraRegressor` - Merges ROCKET and Hydra approaches

**Use when**: Need fast regression with strong baseline performance.

## Deep Learning Regressors

Neural architectures for end-to-end temporal regression:

- `FCNRegressor` - Fully convolutional network
- `ResNetRegressor` - Residual blocks with skip connections
- `InceptionTimeRegressor` - Multi-scale inception modules
- `TimeCNNRegressor` - Standard CNN architecture
- `RecurrentRegressor` - RNN/LSTM/GRU variants
- `MLPRegressor` - Multi-layer perceptron
- `EncoderRegressor` - Convolutional encoder architecture
- `LITETimeRegressor` - Lightweight inception time ensemble
- `DisjointCNNRegressor` - Specialized CNN architecture

**Use when**: Large datasets, complex patterns, or need feature learning.

## Distance-Based Regressors

k-nearest neighbors with temporal distance metrics:

- `KNeighborsTimeSeriesRegressor` - k-NN with DTW, LCSS, ERP, or other distances

**Use when**: Small datasets, local similarity patterns, or interpretable predictions.

## Feature-Based Regressors

Extract statistical features before regression:

- `Catch22Regressor` - 22 canonical time-series characteristics
- `FreshPRINCERegressor` - TSFresh features followed by rotation forest
- `SummaryRegressor` - Summary statistics features
- `TSFreshRegressor` - Automated tsfresh feature extraction

**Use when**: Need interpretable features or domain-specific feature engineering.

## Hybrid Regressors

Combine multiple approaches:

- `RISTRegressor` - Randomized Interval-Shapelet Transformation

**Use when**: Benefit from combining interval and shapelet methods.

## Interval-Based Regressors

Extract features from time intervals:

- `CanonicalIntervalForestRegressor` - Random intervals with decision trees
- `DrCIFRegressor` - Diverse Representation CIF
- `TimeSeriesForestRegressor` - Random interval ensemble
- `RandomIntervalRegressor` - Simple interval-based approach
- `RandomIntervalSpectralEnsembleRegressor` - Spectral interval features
- `QUANTRegressor` - Quantile-based interval features

**Use when**: Predictive patterns occur in specific time windows.

## Shapelet-Based Regressors

Use discriminative subsequences for prediction:

- `RDSTRegressor` - Random Dilated Shapelet Transform

**Use when**: Need phase-invariant discriminative patterns.

## Composition Tools

Build custom regression pipelines:

- `RegressorPipeline` - Chain transformers with regressors
- `RegressorEnsemble` - Weighted ensemble with learnable weights
- `SklearnRegressorWrapper` - Adapt sklearn regressors for time series

## Utilities

- `DummyRegressor` - Baseline strategies (mean, median)
- `BaseRegressor` - Abstract base for custom regressors
- `BaseDeepRegressor` - Base for deep learning regressors

## Quick Start

```python
from aeon.regression.convolution_based import RocketRegressor
from aeon.datasets import load_regression

# Load data
X_train, y_train = load_regression("Covid3Month", split="train")
X_test, y_test = load_regression("Covid3Month", split="test")

# Train and predict
reg = RocketRegressor()
reg.fit(X_train, y_train)
predictions = reg.predict(X_test)
```

## Algorithm Selection

- **Speed priority**: MiniRocketRegressor
- **Accuracy priority**: InceptionTimeRegressor, MultiRocketHydraRegressor
- **Interpretability**: Catch22Regressor, SummaryRegressor
- **Small data**: KNeighborsTimeSeriesRegressor
- **Large data**: Deep learning regressors, ROCKET variants
- **Interval patterns**: DrCIFRegressor, CanonicalIntervalForestRegressor

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

