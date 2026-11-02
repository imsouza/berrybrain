---
id: sciref-geomaster-machine-learning
name: "Scientific Ref: Machine Learning for Geospatial Data"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (geomaster): Machine Learning for Geospatial Data"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "geomaster machine learning"
  - "machine learning for geospatial data"
keywords:
  - "geomaster"
  - "machine"
  - "learning"
  - "specialized"
  - "scientific"
  - "reference"
---

# Machine Learning for Geospatial Data

Machine learning for remote sensing and spatial analysis, reviewed 2026-10-01.
RF arithmetic/masking is tested with synthetic rasters. Neural network, PyG and SHAP
examples are illustrative, source-reviewed templates; no training run or accuracy
claim is made. Install their packages separately. Record feature units, masks, band
order, normalization, labels and spatial/temporal split definitions.

## Traditional Machine Learning

### Random Forest for land cover

Use the bundled `classify_imagery` helper (see the main skill) for a small masked
raster fit/predict exercise. Rasterize labels in the raster CRS using its actual
transform. Exclude nodata from both fitting and prediction, reserve an output nodata
code and verify integer class range before casting.

For assessment, split at independent spatial/temporal units **before** fitting:

```python
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import numpy as np

# X, y and spatial_block_id have aligned rows, one row per valid labelled sample.
train, validation = next(GroupShuffleSplit(n_splits=1, test_size=0.2,
    random_state=42).split(X, y, groups=spatial_block_id))
if set(np.unique(y[validation])) - set(np.unique(y[train])):
    raise ValueError('Holdout contains classes absent from training')
model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=1)
model.fit(X[train], y[train])
print(classification_report(y[validation], model.predict(X[validation]), zero_division=0))
```

Random pixels from the same labelled polygon in both partitions leak spatial
information. Block size and buffer separation depend on autocorrelation and the
intended transfer region; grouping alone does not prove independence. Also report
held-out sample/area support, imbalance and uncertainty. Feature importance is model
association, not causal evidence.

### Support Vector Machine

```python
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler

def svm_classifier(X_train, y_train):
    """SVM classifier for remote sensing."""

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    # Train SVM
    svm = SVC(
        kernel='rbf',
        C=100,
        gamma='scale',
        class_weight='balanced',
        probability=True
    )
    svm.fit(X_train_scaled, y_train)

    return svm, scaler

# Multi-class classification
def multiclass_svm(X_train, y_train):
    from sklearn.multiclass import OneVsRestClassifier

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    svm_ovr = OneVsRestClassifier(
        SVC(kernel='rbf', C=10, probability=True),
        n_jobs=-1
    )
    svm_ovr.fit(X_train_scaled, y_train)

    return svm_ovr, scaler
```

## Deep Learning

### CNN tensor example (PyTorch)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader

# Define CNN
class LandCoverCNN(nn.Module):
    def __init__(self, in_channels=12, num_classes=10):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels, 64, 3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(128, 256, 3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(256, 128, 2, stride=2),
            nn.BatchNorm2d(128),
            nn.ReLU(),

            nn.ConvTranspose2d(128, 64, 2, stride=2),
            nn.BatchNorm2d(64),
            nn.ReLU(),

            nn.ConvTranspose2d(64, num_classes, 2, stride=2),
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x

# Training
def train_model(train_loader, val_loader, num_epochs=50):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = LandCoverCNN().to(device)

    criterion = nn.CrossEntropyLoss(ignore_index=-1)  # explicit nodata label
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(num_epochs):
        model.train()
        train_loss = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item()

        print(f'Epoch {epoch+1}/{num_epochs}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}')

    return model
```

### U-Net for Semantic Segmentation

Inputs are `(N,C,H,W)` float tensors; labels are `(N,H,W)` integer class IDs.
This architecture requires H/W divisible by 16; pad/crop with a recorded policy.
The simpler CNN above requires divisibility by 8. Neither model is pretrained.

```python
class UNet(nn.Module):
    def __init__(self, in_channels=4, num_classes=5):
        super().__init__()

        # Encoder
        self.enc1 = self.conv_block(in_channels, 64)
        self.enc2 = self.conv_block(64, 128)
        self.enc3 = self.conv_block(128, 256)
        self.enc4 = self.conv_block(256, 512)

        # Bottleneck
        self.bottleneck = self.conv_block(512, 1024)

        # Decoder
        self.up1 = nn.ConvTranspose2d(1024, 512, 2, stride=2)
        self.dec1 = self.conv_block(1024, 512)

        self.up2 = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.dec2 = self.conv_block(512, 256)

        self.up3 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.dec3 = self.conv_block(256, 128)

        self.up4 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        self.dec4 = self.conv_block(128, 64)

        # Final layer
        self.final = nn.Conv2d(64, num_classes, 1)

    def conv_block(self, in_ch, out_

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

