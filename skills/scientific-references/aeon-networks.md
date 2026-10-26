---
id: sciref-aeon-networks
name: "Scientific Ref: Deep Learning Networks"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (aeon): Deep Learning Networks"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "aeon networks"
  - "deep learning networks"
keywords:
  - "aeon"
  - "networks"
  - "specialized"
  - "scientific"
  - "reference"
  - "deep"
  - "learning"
---

# Deep Learning Networks

Aeon 1.6 provides TensorFlow/Keras network building blocks. This reference was checked against release source; all deep-training snippets are illustrative and were not executed during this review. Install the estimator's TensorFlow dependency separately rather than downloading all optional stacks. Estimator inputs use `(cases, channels, timepoints)` and wrappers transpose internally to Keras layouts.

## Core Network Architectures

### Convolutional Networks

**FCNNetwork** - Fully Convolutional Network
- Three convolutional blocks with batch normalization
- Global average pooling for dimensionality reduction
- **Use when**: Need simple yet effective CNN baseline

**ResNetNetwork** - Residual Network
- Residual blocks with skip connections
- Prevents vanishing gradients in deep networks
- **Use when**: Deep networks needed, training stability important

**InceptionNetwork** - Inception Modules
- Multi-scale feature extraction with parallel convolutions
- Different kernel sizes capture patterns at various scales
- **Use when**: Patterns exist at multiple temporal scales

**TimeCNNNetwork** - Standard CNN
- Basic convolutional architecture
- **Use when**: Simple CNN sufficient, interpretability valued

**DisjointCNNNetwork** - Separate Pathways
- Disjoint convolutional pathways
- **Use when**: Different feature extraction strategies needed

**DCNNNetwork** - Dilated CNN
- Dilated convolutions for large receptive fields
- **Use when**: Long-range dependencies without many layers

### Recurrent Networks

**RecurrentNetwork** - RNN/LSTM/GRU
- `rnn_type` supports `"simple"`, `"lstm"`, and `"gru"`
- Sequential modeling of temporal dependencies
- **Use when**: Sequential dependencies are important

### Temporal Convolutional Network

**TCNNetwork** - Temporal Convolutional Network
- Dilated causal convolutions
- Large receptive field without recurrence
- **Use when**: Long sequences, need parallelizable architecture

### Multi-Layer Perceptron

**MLPNetwork** - Basic Feedforward
- Simple fully-connected layers
- Flattens time series before processing
- **Use when**: Baseline needed, computational limits, or simple patterns

## Encoder-Based Architectures

Networks designed for representation learning and clustering.

### Autoencoder Variants

**EncoderNetwork** - Convolutional Encoder
- Convolutional layers and attention-based encoding
- **Use when**: Custom encoding needed

**AEFCNNetwork** - FCN-based Autoencoder
- Fully convolutional encoder-decoder
- **Use when**: Need convolutional representation learning

**AEResNetNetwork** - ResNet Autoencoder
- Residual blocks in encoder-decoder
- **Use when**: Deep autoencoding with skip connections

**AEDCNNNetwork** - Dilated CNN Autoencoder
- Dilated convolutions for compression
- **Use when**: Need large receptive field in autoencoder

**AEDRNNNetwork** - Dilated RNN Autoencoder
- Dilated recurrent connections
- **Use when**: Sequential patterns with long-range dependencies

**AEBiGRUNetwork** - Bidirectional GRU
- Bidirectional recurrent encoding
- **Use when**: Context from both directions helpful

**AEAttentionBiGRUNetwork** - Attention + BiGRU
- Attention mechanism on BiGRU outputs
- **Use when**: Need to focus on important time steps

## Specialized Architectures

**LITENetwork** - Lightweight Inception Time Ensemble
- Efficient inception-based architecture
- LITEMV variant for multivariate series
- **Use when**: Need efficiency with strong performance

**DeepARForecaster** - Probabilistic forecasting (use via `aeon.forecasting.deep_learning`)
- Autoregressive RNN for forecasting
- Point output by default; `use_probabilistic=True` requests mean/scale output. Validate loss and calibration for uncertainty use
- **Use when**: Need forecast uncertainty quantification

## Usage with Estimators

Networks are typically used within estimators, not directly:

```python
from aeon.classification.deep_learning import FCNClassifier
from aeon.regression.deep_learning import ResNetRegressor
from aeon.clustering.deep_learning import AEFCNClusterer

# Classification with FCN
clf = FCNClassifier(n_epochs=100, batch_size=16)
clf.fit(X_train, y_train)

# Regression with ResNet
reg = ResNetRegressor(n_epochs=100)
reg.fit(X_train, y_train)

# Clustering with autoencoder
from sklearn.cluster import KMeans
clusterer = AEFCNClusterer(
    estimator=KMeans(n_clusters=3, random_state=42), n_epochs=100
)
labels = clusterer.fit_predict(X_train)
```

## Custom Network Configuration

Many networks accept configuration parameters:

```python
# Configure FCN layers and the optimizer (no learning_rate constructor field)
from tensorflow.keras.optimizers import Adam
clf = FCNClassifier(
    n_epochs=200,
    batch_size=32,
    kernel_size=[7, 5, 3],  # Kernel sizes for each layer
    n_filters=[128, 256, 128],  # Filters per layer
    optimizer=Adam(learning_rate=0.001)
)
```

## Base Classes

- `BaseDeepLearningNetwork` - Abstract base for all networks
- `BaseDeepRegressor` - Base for deep regression
- `BaseDeepClassifier` - Base for deep classification
- `BaseDeepForecaster` - Base for deep forecasting

Extend these to implement custom architectures.

## Training Considerations

### Hyperparameters

Key hyperparameters to tune:

- `n_epochs` - Training iterations (50-200 typical)
- `batch_size` - Samples per batch (16-64 typical)
- Learning rate belongs to the Keras `optimizer`; it is not an FCNClassifier parameter
- Network-specific: layers, filters, kernel sizes

### Callbacks

Many estimators support callbacks. FCNClassifier.fit does not pass a validation set to Keras; use training `loss` for these callbacks, and evaluate generalization on independent validation data:

```python
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

clf = FCNClassifier(
    n_epochs=200,
    callbacks=[
        EarlyStopping(monitor="loss", patience=20, restore_best_weights=True),
        ReduceLROnPlateau(monitor="loss", patience=10, factor=0.5)
    ]
)
```

### GPU Acceleration

Deep learning networks benefit from GPU:

```python
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # Set before importing TensorFlow
from aeon.classification.deep_learning import InceptionTimeClassifier

# TensorFlow uses a supported GPU when its platform backend is configured
clf = InceptionTimeClassifier(n_epochs=100)
clf.fit(X_train, y_train)
```

## Architecture Selection

### By Task:

**Classification**: InceptionNetwork, ResNetNetwork, FCNNetwork
**

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

