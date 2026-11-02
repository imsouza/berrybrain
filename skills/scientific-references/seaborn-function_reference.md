---
id: sciref-seaborn-function-reference
name: "Scientific Ref: Seaborn Function Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (seaborn): Seaborn Function Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "seaborn function reference"
keywords:
  - "seaborn"
  - "function"
  - "reference"
  - "specialized"
  - "scientific"
---

# Seaborn Function Reference

This document provides a selected reference for major seaborn functions, organized by category. Reviewed against the [0.13.2 API](https://seaborn.pydata.org/api.html) and released signatures on 2026-10-01. Parameter lists below are selected, not complete signatures. Figure-level wrappers accept only parameters supported by their selected `kind`; they do not accept `ax`. Examples use illustrative input DataFrames.

## Relational Plots

### scatterplot()

**Purpose:** Create a scatter plot with points representing individual observations.

**Key Parameters:**
- `data` - DataFrame, array, or dict of arrays
- `x, y` - Variables for x and y axes
- `hue` - Grouping variable for color encoding
- `size` - Grouping variable for size encoding
- `style` - Grouping variable for marker style
- `palette` - Color palette name or list
- `hue_order` - Order for categorical hue levels
- `hue_norm` - Normalization for numeric hue (tuple or Normalize object)
- `sizes` - Size range for size encoding (tuple or dict)
- `size_order` - Order for categorical size levels
- `size_norm` - Normalization for numeric size
- `markers` - Marker style(s) (string, list, or dict)
- `style_order` - Order for categorical style levels
- `legend` - How to draw legend: "auto", "brief", "full", or False
- `ax` - Matplotlib axes to plot on

**Example:**
```python
sns.scatterplot(data=df, x='height', y='weight',
                hue='gender', size='age', style='smoker',
                palette='Set2', sizes=(20, 200))
```

### lineplot()

**Purpose:** Draw a line plot with aggregation and confidence intervals across observations at each x; repeated measures need an explicit sampling-unit strategy.

**Key Parameters:**
- `data` - DataFrame, array, or dict of arrays
- `x, y` - Variables for x and y axes
- `hue` - Grouping variable for color encoding
- `size` - Grouping variable for line width
- `style` - Grouping variable for line style (dashes)
- `units` - Separate trajectory for each sampling unit; also set `estimator=None` (no aggregation)
- `weights` - Observation weights; only mean estimation with CI or no error bars
- `estimator` - Function for aggregating across observations (default: mean)
- `errorbar` - Method for error bars: "sd", "se", "pi", ("ci", level), ("pi", level), or None
- `n_boot` - Number of bootstrap iterations for CI computation
- `seed` - Random seed for reproducible bootstrapping
- `sort` - Sort data before plotting
- `err_style` - "band" or "bars" for error representation
- `err_kws` - Additional parameters for error representation
- `markers` - Marker style(s) for emphasizing data points
- `dashes` - Dash style(s) for lines
- `legend` - How to draw legend
- `ax` - Matplotlib axes to plot on

**Example:**
```python
sns.lineplot(data=timeseries, x='time', y='signal',
             hue='condition', units='subject',
             estimator=None, errorbar=None, marker='o')
```

### relplot()

**Purpose:** Figure-level interface for drawing relational plots (scatter or line) onto a FacetGrid.

**Key Parameters:**
Parameters for the selected `kind` (`scatterplot` or `lineplot`), except `ax`, plus:
- `kind` - "scatter" or "line"
- `col` - Categorical variable for column facets
- `row` - Categorical variable for row facets
- `col_wrap` - Wrap columns after this many columns
- `col_order` - Order for column facet levels
- `row_order` - Order for row facet levels
- `height` - Height of each facet in inches
- `aspect` - Aspect ratio (width = height * aspect)
- `facet_kws` - Additional parameters for FacetGrid

**Example:**
```python
sns.relplot(data=df, x='time', y='measurement',
            hue='treatment', style='batch',
            col='cell_line', row='timepoint',
            kind='line', height=3, aspect=1.5)
```

## Distribution Plots

### histplot()

**Purpose:** Plot univariate or bivariate histograms with flexible binning.

**Key Parameters:**
- `data` - DataFrame, array, or dict
- `x, y` - Variables (y optional for bivariate)
- `hue` - Grouping variable
- `weights` - Variable for weighting observations
- `stat` - Aggregate statistic: "count", "frequency", "probability", "percent", "density"
- `bins` - Number of bins, bin edges, or method ("auto", "fd", "doane", "scott", "stone", "rice", "sturges", "sqrt")
- `binwidth` - Width of bins (overrides bins)
- `binrange` - Range for binning (tuple)
- `discrete` - Treat x as discrete (centers bars on values)
- `cumulative` - Compute cumulative distribution
- `common_bins` - Use same bins for all hue levels
- `common_norm` - Normalize across hue levels
- `multiple` - How to handle hue: "layer", "dodge", "stack", "fill"
- `element` - Visual element: "bars", "step", "poly"
- `fill` - Fill bars/elements
- `shrink` - Scale bar width (for multiple="dodge")
- `kde` - Overlay KDE estimate
- `kde_kws` - Parameters for KDE
- `line_kws` - Parameters for the KDE line when `kde=True`
- `thresh` - Minimum count threshold for bins
- `pthresh` - Minimum probability threshold
- `pmax` - Maximum probability for color scaling
- `log_scale` - Log scale for axis (bool or base)
- `legend` - Whether to show legend
- `ax` - Matplotlib axes

**Example:**
```python
sns.histplot(data=df, x='measurement', hue='condition',
             stat='density', bins=30, kde=True,
             multiple='layer', alpha=0.5)
```

### kdeplot()

**Purpose:** Plot univariate or bivariate kernel density estimates.

**Key Parameters:**
- `data` - DataFrame, array, or dict
- `x, y` - Variables (y optional for bivariate)
- `hue` - Grouping variable
- `weights` - Variable for weighting observations
- `palette` - Color palette
- `hue_order` - Order for hue levels
- `hue_norm` - Normalization for numeric hue
- `multiple` - How to handle hue: "layer", "stack", "fill"
- `common_norm` - Normalize across hue levels
- `common_grid` - Use same grid for all hue levels
- `cumulative` - Compute cumulative distribution
- `bw_method` - Method for bandwidth: "scott", "silverman", or scalar
- `bw_adjust` - Bandwidth multiplier (higher = smoother)
- `log_scale` - Log scale for axis
- `levels` - Number or increasing iso-proportion levels in [0, 1] (bivariate)
- `thresh` - Lowest iso-proportion contour level, not a raw density or p-value
- `gridsize` - Grid resolution
- `cut` - Extension beyond data extremes (in bandwidth units)
- `clip` - Data range for curve (tuple)
- `fill` - Fill area under curve/contours
- `legend` - Whether to show legend
- `ax` - Matplotlib axes

**Example:**
```python
# Uni

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

