---
id: sciref-aeon-classification
name: "Scientific Ref: Time Series Classification"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (aeon): Time Series Classification"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "aeon classification"
  - "time series classification"
keywords:
  - "aeon"
  - "classification"
  - "specialized"
  - "scientific"
  - "reference"
  - "time"
  - "series"
---

# Time Series Classification

Selected aeon 1.6 classifiers with scikit-learn compatible APIs. Verify estimator capability tags before choosing multivariate, missing-value, or unequal-length data.

## Convolution-Based Classifiers

Apply random convolutional transformations for efficient feature extraction:

- `Arsenal` - Ensemble of ROCKET classifiers with varied kernels
- `HydraClassifier` - Multi-resolution convolution with dilation
- `RocketClassifier` - Random convolution kernels with ridge regression
- `MiniRocketClassifier` - Simplified ROCKET variant for speed
- `MultiRocketClassifier` - Convolutional features from raw and differenced series with multiple pooling operators

**Use when**: Need fast, scalable classification with strong performance across diverse datasets.

## Deep Learning Classifiers

Neural network architectures optimized for temporal sequences:

- `FCNClassifier` - Fully convolutional network
- `ResNetClassifier` - Residual networks with skip connections
- `InceptionTimeClassifier` - Multi-scale inception modules
- `TimeCNNClassifier` - Standard CNN for time series
- `MLPClassifier` - Multi-layer perceptron baseline
- `EncoderClassifier` - Convolutional encoder architecture
- `DisjointCNNClassifier` - Shapelet-focused architecture

**Use when**: Large datasets available, need end-to-end learning, or complex temporal patterns.

## Dictionary-Based Classifiers

Transform time series into symbolic representations:

- `BOSSEnsemble` - Bag-of-SFA-Symbols with ensemble voting
- `TemporalDictionaryEnsemble` - Ensemble of symbolic Fourier bag-of-words models
- `WEASEL` - Word ExtrAction for time SEries cLassification
- `MrSEQLClassifier` - Multiple symbolic sequence learning

**Use when**: Need interpretable models, sparse patterns, or symbolic reasoning.

## Distance-Based Classifiers

Leverage specialized time series distance metrics:

- `KNeighborsTimeSeriesClassifier` - k-NN with temporal distances (DTW, LCSS, ERP, etc.)
- `ElasticEnsemble` - Combines multiple elastic distance measures
- `ProximityForest` - Tree ensemble using distance-based splits

**Use when**: Small datasets, need similarity-based classification, or interpretable decisions.

## Feature-Based Classifiers

Extract statistical and signature features before classification:

- `Catch22Classifier` - 22 canonical time-series characteristics
- `TSFreshClassifier` - Automated feature extraction via tsfresh
- `SignatureClassifier` - Path signature transformations
- `SummaryClassifier` - Summary statistics extraction
- `FreshPRINCEClassifier` - TSFresh features followed by rotation forest

**Use when**: Need interpretable features, domain expertise available, or feature engineering approach.

## Interval-Based Classifiers

Extract features from random or supervised intervals:

- `CanonicalIntervalForestClassifier` - Random interval features with decision trees
- `DrCIFClassifier` - Diverse Representation CIF with catch22 features
- `TimeSeriesForestClassifier` - Random intervals with summary statistics
- `RandomIntervalClassifier` - Simple interval-based approach
- `RandomIntervalSpectralEnsembleClassifier` - Spectral features from intervals
- `SupervisedTimeSeriesForest` - Supervised interval selection

**Use when**: Discriminative patterns occur in specific time windows.

## Shapelet-Based Classifiers

Identify discriminative subsequences (shapelets):

- `ShapeletTransformClassifier` - Discovers and uses discriminative shapelets
- `SASTClassifier` - Scalable approximate shapelet transform
- `RDSTClassifier` - Random dilated shapelet transform

**Use when**: Need interpretable discriminative patterns or phase-invariant features.

## Hybrid Classifiers

Combine multiple classification paradigms:

- `HIVECOTEV1` - Hierarchical Vote Collective of Transformation-based Ensembles (version 1)
- `HIVECOTEV2` - Enhanced version with updated components

**Use when**: Maximum accuracy required, computational resources available.

## Early Classification

Make predictions before observing entire time series:

- `TEASER` - Two-tier Early and Accurate Series Classifier
- `ProbabilityThresholdEarlyClassifier` - Prediction when confidence exceeds threshold

**Use when**: Real-time decisions needed, or observations have cost.

## Ordinal Classification

Handle ordered class labels:

- `OrdinalTDE` - Temporal dictionary ensemble for ordinal outputs

**Use when**: Classes have natural ordering (e.g., severity levels).

## Composition Tools

Build custom pipelines and ensembles:

- `ClassifierPipeline` - Chain transformers with classifiers
- `ClassifierEnsemble` - Weighted combination of classifiers
- `SklearnClassifierWrapper` - Adapt sklearn classifiers for time series

`LearningShapeletClassifier` was removed in aeon 1.6 after deprecation in 1.5. Use the supported shapelet estimators above.

## Quick Start

```python
from aeon.classification.convolution_based import RocketClassifier
from aeon.datasets import load_classification

# Load data
X_train, y_train = load_classification("GunPoint", split="train")
X_test, y_test = load_classification("GunPoint", split="test")

# Train and predict
clf = RocketClassifier()
clf.fit(X_train, y_train)
accuracy = clf.score(X_test, y_test)
```

## Algorithm Selection

- **Speed priority**: MiniRocketClassifier, Arsenal
- **Accuracy priority**: HIVECOTEV2, InceptionTimeClassifier
- **Interpretability**: ShapeletTransformClassifier, Catch22Classifier
- **Small data**: KNeighborsTimeSeriesClassifier, Distance-based methods
- **Large data**: Deep learning classifiers, ROCKET variants

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

