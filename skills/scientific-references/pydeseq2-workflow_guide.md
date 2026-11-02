---
id: sciref-pydeseq2-workflow-guide
name: "Scientific Ref: Normalization, QC, and downstream use"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pydeseq2): Normalization, QC, and downstream use"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pydeseq2 workflow guide"
  - "normalization, qc, and downstream use"
keywords:
  - "pydeseq2"
  - "workflow"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
  - "pydeseq"
  - "normalization"
  - "downstream"
---

# Normalization, QC, and downstream use

## Importing counts from AnnData

`obs` indexes samples and `var` indexes genes. Establish which matrix contains
counts from preprocessing provenance: neither `.X`, `.raw.X`, nor a layer named
`counts` guarantees that values are unnormalized. PyDESeq2's `adata=` constructor
reads `.X`; it has no `layer=` argument. For a small dataset with a verified counts
layer, this conversion was tested with dense and CSR inputs:

```python
import numpy as np
import pandas as pd
from scipy import sparse

matrix = adata.layers['counts']  # verified count provenance, not inferred from name
# Dense storage is needed downstream; check the memory cost before materializing.
if sparse.issparse(matrix):
    matrix = matrix.toarray()
counts_df = pd.DataFrame(matrix, index=adata.obs_names, columns=adata.var_names)
metadata = adata.obs.copy()
assert counts_df.index.is_unique and counts_df.columns.is_unique
assert np.isfinite(counts_df.to_numpy()).all()
```

Resolve missing annotations across **all** design variables before fitting.
Explicitly log any sample exclusions, then perform gene filtering. Never infer
transposition from whether the number of genes exceeds the number of samples.

AnnData 0.13 exposes `layers[None]` as an alias for `.X`. Avoid loops assuming every
layer key is a string, and never delete the alias as a workaround. A fitted
PyDESeq2 0.5.4 object was successfully exported with
`dds.to_picklable_anndata().write_h5ad(...)` and reloaded under AnnData 0.13.4.

## Size factors and count normalization

For the ratio method, positive-in-every-sample genes define geometric reference
counts. PyDESeq2 computes each sample's factor as the exponential of its median
log count/reference ratio. `normed_counts = X / size_factors[:, None]`. This is
within-gene library/composition normalization; it is not cross-gene length correction.

Size factors need not cluster near one. Inspect library totals, composition,
replicate structure and external controls together; a wide factor range is a QC
lead, not an automatic failure. Broad unidirectional expression shifts can violate
the default reference assumption. Use prespecified invariant control genes only
when they have defensible experimental support.

```python
from pydeseq2.dds import DeseqDataSet

normalization_dds = DeseqDataSet(
    counts=counts_df, metadata=metadata, design='~condition',
    size_factors_fit_type='ratio', n_cpus=1,
)
normalization_dds.fit_size_factors()
sf = normalization_dds.obs['size_factors'].to_numpy()
assert np.isfinite(sf).all() and (sf > 0).all()
np.testing.assert_allclose(normalization_dds.layers['normed_counts'], counts_df.to_numpy() / sf[:, None])
```

Normalization options in 0.5.4:

- `ratio` is default. If every gene contains a zero, `DeseqDataSet` warns and
  switches to iterative estimation. The standalone `preprocessing.deseq2_norm`
  does **not** provide that fallback.
- `poscounts` uses positive entries, replacing zeros' log contribution with zero
  when calculating gene log means, then centers size factors to geometric mean one.
  The released implementation additionally selects genes with `logmeans > 0`:
  all-zero **and all-zero/one** genes are excluded. A binary-only native fixture
  produced missing factors. Check factors explicitly; do not treat this as a
  general per-cell single-cell DE method.
- `iterative` estimates factors with an intercept-only fit. In the released source,
  the `control_genes` mask is not passed into this branch, including automatic
  fallback. Do not claim control-only normalization if iteration was used.
- `control_genes` accepts valid AnnData gene indexers for ratio/poscounts. Ensure
  selected controls survived filtering and contain usable positive counts for
  every sample; checking only that names exist is insufficient.

Record the actual method and fallback warnings. Changing normalization to obtain
more significant genes is not a validation strategy.

## Dispersion and model diagnostics

For a negative-binomial count with mean `mu`, the dispersion convention is
`variance = mu + dispersion * mu**2`. PyDESeq2 estimates gene-wise dispersions,
fits a parametric trend or a mean trend, and obtains MAP dispersions. This is
dispersion shrinkage; it is separate from optional LFC shrinkage after testing.

The parametric trend can fail and fall back to a mean trend. This occurred in the
small Poisson-like regression fixture and is reported, not hidden. Tiny panels
provide little information for global dispersion estimation. Inspect nonfinite
estimates, convergence fields, the trend and mean/count distributions. A plausible
plot or convergence flag does not establish model adequacy or biological validity.

```python
import matplotlib.pyplot as plt

dds.plot_dispersions(save_path='dispersion_plot.png')
plt.close('all')
print(dds.var[['genewise_dispersions', 'dispersions', '_LFC_converged']].head())
print(dds.obs['size_factors'])
```

The model requires independent biological replication and residual degrees of
freedom. The library warns on rank deficiency; the bundled driver explicitly
stops. An interaction cannot recover information absent from a confounded design.

Cook replacement and Cook test filtering are different operations. Default
`min_replicates=7` governs eligible replacement; a three-versus-three experiment
may still have Cook-filtered results without replacement. Do not delete samples
because one gene has a large Cook distance. Inspect sample-wide QC and preserve the
reason for any scientifically justified exclusion.

## Missing tests, adjusted p-values, and plots

All-zero genes lack estimable coefficients/tests. Extreme Cook outliers can have
missing p-values; the original statistic may still be present. Independent
filtering uses normalized mean count to select a rejection threshold for the
specified `alpha`, leaving some adjusted p-values missing. It differs from the
manual prefilter and does not remove those genes' rows from the result table.

A p-value histogram need not be flat: true effects, discrete low-count tests,
filtering, model errors and sample structure all affect it. Uniform null behavior
is an idealization, not a required shape for a mixed real dataset. Compare with
QC and study design rather than using the histogram alone to certify the analysis.

For a volcano plot, omit missing y values and cap exact zero adjusted p-values
only in the plotting copy:

```python
plot_results = wald_results.copy()
plot_results['minus_

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

