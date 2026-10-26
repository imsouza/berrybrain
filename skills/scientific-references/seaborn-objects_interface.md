---
id: sciref-seaborn-objects-interface
name: "Scientific Ref: Seaborn Objects Interface"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (seaborn): Seaborn Objects Interface"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "seaborn objects interface"
keywords:
  - "seaborn"
  - "objects"
  - "interface"
  - "specialized"
  - "scientific"
  - "reference"
---

# Seaborn Objects Interface

Reviewed against Seaborn 0.13.2's [objects API](https://seaborn.pydata.org/api.html)
and released source on 2026-10-01. Upstream still calls this interface experimental
and incomplete. Use it when composing layers helps; use the function interface for
plot types it does not implement, such as bivariate KDE.

## Build, retain, and render a specification

`Plot` methods return a new specification. Assign the result or chain methods;
calling `p.add(...)` without retaining the return value does not update `p`.
Mappings belong in `Plot`/`add`; constant visual properties belong in the mark.
`so.Dot(alpha=.4)` sets opacity directly; `add(so.Dot(), alpha=.4)` creates a
constant *data mapping* whose default scale need not render opacity .4.

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import seaborn.objects as so

# Small offline fixture; repeated measurements are independent here by design.
df = pd.DataFrame({
    'category': np.repeat(['A', 'B'], 8),
    'group': ['control', 'control', 'treated', 'treated'] * 4,
    'value': [1, 2, 3, 5, 2, 3, 4, 6, 3, 5, 6, 8, 4, 6, 7, 9],
    'x': np.tile(np.arange(8), 2),
})
p = so.Plot(df, x='x', y='value', color='category').add(so.Dot(alpha=.4))
p = p.add(so.Line(), so.PolyFit(order=1))  # Default PolyFit order is 2
p.save('objects-scatter.png', dpi=150, bbox_inches='tight')
```

In notebooks the last expression can display automatically. In scripts use
`.show()`, `.save()`, or `.plot()`. Include `bbox_inches='tight'` on exports when an external legend would otherwise be clipped. To customize an existing Matplotlib axes,
`.on(ax)` needs a subsequent compilation call:

```python
fig, ax = plt.subplots(figsize=(5, 3))
p.on(ax).plot()
ax.set_ylabel('Response (units)')
fig.savefig('objects-on-axes.pdf', bbox_inches='tight')
```

## Layers and estimation

`Plot.add(mark, *transforms, orient=None, legend=True, label=None, data=None,
**variables)` supports at most one Stat, placed first, followed by Moves.
`orient='x'` means grouping along x and estimation along y (`'v'` is a synonym);
`'y'`/`'h'` reverses this. A layer can override data and mapped variables.

An estimator computes interval columns but does **not** make every mark draw them.
`Line` and `Bar` use the point estimate; add `Band` or `Range` for uncertainty.
Use the same estimator, seed, grouping, and dodge on both layers.

```python
est = so.Est(func='mean', errorbar=('ci', 95), n_boot=1000, seed=7)
bars = (
    so.Plot(df, x='category', y='value', color='group')
    .add(so.Bar(), est, so.Dodge())
    .add(so.Range(), est, so.Dodge())
    .label(y='Mean response', color='Group')
)
bars.save('objects-intervals.png', dpi=150, bbox_inches='tight')
```

For a line plus interval use `.add(so.Line(), est).add(so.Band(), est)`.
`Est(errorbar='sd')` depicts spread, not a confidence interval. `Est` has no
`units=` constructor parameter for multilevel bootstrap; compute design-aware
intervals outside Seaborn when rows are dependent, then map `ymin`/`ymax`.
Weights passed as a layer variable are supported for a mean with bootstrap CI or
no error bars, not arbitrary estimators or complex sampling designs.

## Choose marks by their actual geometry

| Mark | Behavior and useful constant properties |
| --- | --- |
| `Dot` | Individual points: `color`, `alpha`, `marker`, `pointsize`, `stroke`, `fill`, `edgecolor`, `edgewidth`. No `fillcolor` or `fillalpha` constructor arguments. |
| `Line`, `Path` | `Line` sorts on the orientation axis; `Path` follows row order. `linewidth`, `linestyle`, marker/pointsize, `fillcolor`, `edgecolor`. Neither aggregates by itself. |
| `Bar`, `Bars` | Baseline to value; `Bar` is flexible, `Bars` batches artists with histogram-friendly defaults. Neither adds error bars. `width` is relative to the spacing on the orientation axis, not a universal physical data-unit width. |
| `Area`, `Band` | Filled baseline-to-value area versus interval between bounds. `Area` has `baseline`; `Band` has no baseline. Map `ymin`/`ymax` (or horizontal bounds) for a band. |
| `Range` | Segment between minimum and maximum values/bounds. `color`, `alpha`, `linewidth`, `linestyle`; no endpoint `marker`, `pointsize`, or `edgewidth` properties. |
| `Dash` | Short segment per observation; `width` controls relative length, with line properties. |
| `Text` | `text`, `color`, `fontsize`, `halign`, `valign`; `offset` is a scalar in points, not an `(x, y)` tuple. |

Marks accept `artist_kws={...}` for underlying Matplotlib customization; they do
not accept arbitrary unknown keyword properties. Faster plural `Dots`, `Lines`,
and `Paths` also exist; consult their own properties rather than assuming all
singular-mark options apply.

```python
labels = df.groupby('category', as_index=False).agg(x=('x', 'mean'), value=('value', 'mean'))
text_plot = (
    so.Plot(labels, x='x', y='value', text='category')
    .add(so.Dot())
    .add(so.Text(offset=6, valign='bottom'))
)
text_plot.save('objects-labels.png', dpi=150, bbox_inches='tight')
```

## Statistical transforms

| Stat | Parameters and interpretation |
| --- | --- |
| `Agg(func='mean')` | Aggregate along the value axis; string or callable, without intervals. |
| `Est(func='mean', errorbar=('ci',95), n_boot=1000, seed=None)` | Estimate plus bounds; seed controls bootstrap repeatability. Use a range/band layer to show bounds. |
| `Hist(stat='count', bins='auto', binwidth=None, binrange=None, common_norm=True, common_bins=True, cumulative=False, discrete=False)` | Counts or normalized bins; `binwidth` overrides `bins`. |
| `KDE(bw_adjust=1, bw_method='scott', common_norm=True, common_grid=True, gridsize=200, cut=3, cumulative=False)` | Univariate density. `common_norm=False` normalizes each group separately; use comparable grids/bandwidths and inspect support. |
| `Count()` | Count observations in groups. |
| `PolyFit(order=2, gridsize=100)` | Polynomial prediction curve; no confidence interval or causal inference. Set `order=1` for linear regression. |
| `Perc(k=5, method='linear')` | Compute k equally spaced percentiles including 0 and 100; `k=[25,75]` selects the IQR. It returns values, not `ymin`/`ymax` bounds. |

`Band` can span the values returned by `Perc([25,75])`; with the default `Perc(5)`
it spans the full min/max range, not the IQR. A `Range` can display the same bounds
at discrete x positions. Use NumPy-compatible percentile methods

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

