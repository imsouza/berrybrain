---
id: sciref-vaex-machine-learning
name: "Scientific Ref: Machine learning and state transfer"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (vaex): Machine learning and state transfer"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "vaex machine learning"
  - "machine learning and state transfer"
keywords:
  - "vaex"
  - "machine"
  - "learning"
  - "specialized"
  - "scientific"
  - "reference"
---

# Machine learning and state transfer

Targets vaex-ml 0.19.0, core 4.19.0. See [official tutorial](https://vaex.io/docs/tutorial_ml.html)
and [released ML source](https://github.com/vaexio/vaex/tree/v4.19.0/packages/vaex-ml/vaex/ml).
Current package wheels are the runtime authority when the website or repository differs.

## Fit only on training observations

Split by the scientific sampling unit (participant, batch, site, or time) before any
imputation, scaling, feature selection, encoder fitting or resampling. Vaex's
`df.ml.train_test_split` slices an already shuffled frame; it does not guarantee a
random, stratified, grouped or temporal split. Model selection needs validation data
separate from the final test set. Target encoding on the same rows used to estimate
target means leaks labels; use out-of-fold training encodings and training-only
mappings for held-out rows. No Vaex target encoder here automatically cross-fits.

The following is a deterministic mechanics example, not an accuracy benchmark:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
import vaex
import vaex.ml
from vaex.ml.sklearn import Predictor, IncrementalPredictor
from sklearn.linear_model import LinearRegression, SGDRegressor

x = np.linspace(-1, 1, 60)
df = vaex.from_arrays(x=x, x2=x**2, target=3*x-2,
                      category=np.array(['A', 'B', 'C'] * 20),
                      binary=(x > 0).astype(int))
train, test = df[:40], df[40:]  # illustrative chronological split
scaler = vaex.ml.StandardScaler(features=['x'], prefix='scaled_')
train_scaled = scaler.fit_transform(train)
test_scaled = scaler.transform(test)
assert np.isclose(train_scaled.scaled_x.mean(), 0, atol=1e-12)
assert np.isclose(scaler.mean_[0], train.x.mean())
assert not np.isclose(test_scaled.scaled_x.mean(), 0)
model = Predictor(model=LinearRegression(), features=['scaled_x'], target='target',
                  prediction_name='prediction')
model.fit(train_scaled)
scored = model.transform(test_scaled)
assert np.allclose(scored.prediction.to_numpy(), test.target.to_numpy())
```

`Predictor.fit()` materializes the full feature matrix and target; wrapping sklearn
in Vaex does not make its fit out of core. `transform()` attaches a lazy prediction
expression; evaluating all predictions still allocates their full result. For
incremental training, choose an estimator whose `partial_fit` genuinely supports the
problem and configure batches/epochs explicitly:

```python
incremental = IncrementalPredictor(
    model=SGDRegressor(random_state=7, learning_rate='constant', eta0=0.01),
    features=['scaled_x'], target='target', batch_size=8, num_epochs=2,
    prediction_name='online_prediction', shuffle=False,
)
incremental.fit(train_scaled)
assert np.isfinite(incremental.transform(test_scaled).online_prediction.to_numpy()).all()
```

A classifier usually needs `partial_fit_kwargs={'classes': ...}` with the fixed
class set. Vaex's `shuffle=True` shuffles within a batch, not necessarily across the
whole dataset. Batch training can differ from a single full fit; assess convergence,
ordering effects and held-out calibration rather than merely checking finite predictions.

## Transformers: current classes and behavior

Transformations generally return a shallow copy with virtual output columns. Fitting
still computes statistics/mappings, and these may allocate substantial state. Explicit
prefixes make feature references unambiguous; inspect actual output names.

```python
for transformer in [
    vaex.ml.MinMaxScaler(features=['x'], feature_range=(-1, 1)),
    vaex.ml.MaxAbsScaler(features=['x']),
    vaex.ml.RobustScaler(features=['x']),
    vaex.ml.LabelEncoder(features=['category']),
    vaex.ml.OneHotEncoder(features=['category']),
    vaex.ml.FrequencyEncoder(features=['category'], unseen='nan'),
    vaex.ml.KBinsDiscretizer(features=['x'], n_bins=3, strategy='uniform'),
]:
    transformed_train = transformer.fit_transform(train)
    transformed_test = transformer.transform(test)
    assert len(transformed_train) == len(train)
    assert len(transformed_test) == len(test)
    assert len(transformed_test.get_column_names()) > len(test.get_column_names())
# One scalar period per transformer, not a list of periods.
cycle = vaex.ml.CycleTransformer(features=['x'], n=24)
cyclic = cycle.fit_transform(train)
assert np.allclose(cyclic.x_x.to_numpy()**2 + cyclic.x_y.to_numpy()**2, 1)
pca = vaex.ml.PCA(features=['x', 'x2'], n_components=2)
pca.fit(train)
projected = pca.transform(test)
assert projected[['PCA_0', 'PCA_1']].values.shape == (20, 2)
assert np.isclose(sum(pca.explained_variance_ratio_), 1)
random_projection = vaex.ml.RandomProjections(features=['x', 'x2'], n_components=2)
assert len(random_projection.fit_transform(train)) == len(train)
```

- `RandomProjections` is plural; `KBinsDiscretizer` replaces the nonexistent `Discretizer` example.
- `MaxAbsScaler` uses the default `absmax_scaled_` prefix. One-hot outputs depend on
  fitted category values; do not infer a fixed naming/schema contract from a toy example.
- Labels encode categories as integers without establishing a scientific order.
  One-hot state can be very large for high cardinality; define unseen/missing policy.
- `BayesianTargetEncoder(features=[...], target=..., weight=..., unseen='nan')`
  is the current class. Unseen choices are `'nan'` or `'zero'`, not automatically
  the global mean. `WeightOfEvidenceEncoder` requires a meaningful binary target
  and training-only estimates. Neither repairs label leakage.
- Standard scaling divides by standard deviation, not variance. Check zero/near-zero
  dispersion, missingness and nonfinite results before model fitting.
- RobustScaler and quantile discretization use approximate percentile machinery;
  their boundaries need independent scientific checks. PCA covariance state is
  quadratic in feature count; scale comparable quantities when appropriate and
  retain loadings/explained variance. Component signs may flip without changing the subspace.

## K-means

```python
from vaex.ml.cluster import KMeans
clusterer = KMeans(features=['x', 'x2'], n_clusters=2, max_iter=10,
                   random_state=7, prediction_label='cluster')
clusterer.fit(train)
clusters = clusterer.transform(test)
assert len(clusterer.cluster_centers) == 2
assert set(clusters.cluster.tolist()) <= {0, 1}
```

The class lives in `vaex.ml.cluster`; fitted centers are `cluster_centers`, without
an underscore. Default 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

