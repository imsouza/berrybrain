---
id: sciref-matplotlib-plot-types
name: "Scientific Ref: Matplotlib Plot Types Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matplotlib): Matplotlib Plot Types Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matplotlib plot types"
  - "matplotlib plot types guide"
keywords:
  - "matplotlib"
  - "plot"
  - "types"
  - "specialized"
  - "scientific"
  - "reference"
---

# Matplotlib Plot Types Guide

Matplotlib 3.11.2 examples. Fragments assume `import numpy as np`, `import matplotlib.pyplot as plt`, an Axes, and named inputs of matching shape. The bundled template provides executable synthetic examples; these fragments illustrate API patterns rather than a complete analysis.

## 1. Line Plots

**Use cases:** Time series, continuous data, trends, function visualization

### Basic Line Plot
```python
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(x, y, linewidth=2, label='Data')
ax.set_xlabel('X axis')
ax.set_ylabel('Y axis')
ax.legend()
```

### Multiple Lines
```python
ax.plot(x, y1, label='Dataset 1', linewidth=2)
ax.plot(x, y2, label='Dataset 2', linewidth=2, linestyle='--')
ax.plot(x, y3, label='Dataset 3', linewidth=2, linestyle=':')
ax.legend()
```

### Line with Markers
```python
ax.plot(x, y, marker='o', markersize=8, linestyle='-',
        linewidth=2, markerfacecolor='red', markeredgecolor='black')
```

### Step Plot
```python
ax.step(x, y, where='mid', linewidth=2, label='Step function')
# where options: 'pre', 'post', 'mid'
```

### Error Bars

Calculate the uncertainty upstream. `yerr` is a nonnegative size (scalar, `(N,)`,
or `(2, N)` with lower then upper sizes), not interval endpoints. For intervals
`lower <= y <= upper`, use `np.vstack([y - lower, upper - y])`. State SD, SEM, or
CI level/method, sampling unit, and sample size in the caption.
```python
ax.errorbar(x, y, yerr=error, fmt='o-', linewidth=2,
            capsize=5, capthick=2, label='With uncertainty')
```

## 2. Scatter Plots

**Use cases:** Correlations, relationships between variables, clusters, outliers

### Basic Scatter
```python
ax.scatter(x, y, s=50, alpha=0.6)
```

### Sized and Colored Scatter

`s` is marker area in points squared; area encoding needs nonnegative values and
a size legend. Numeric `c` has one value per point. For one RGB color use
`color=(r, g, b)` to avoid ambiguity with three numeric observations.
```python
scatter = ax.scatter(x, y, s=sizes*100, c=colors,
                     cmap='viridis', alpha=0.6, edgecolors='black')
plt.colorbar(scatter, ax=ax, label='Color variable')
```

### Categorical Scatter
```python
for category in categories:
    mask = data['category'] == category
    ax.scatter(data[mask]['x'], data[mask]['y'],
               label=category, s=50, alpha=0.7)
ax.legend()
```

## 3. Bar Charts

**Use cases:** Categorical comparisons, discrete data, counts

### Vertical Bar Chart
```python
ax.bar(categories, values, color='steelblue',
       edgecolor='black', linewidth=1.5)
ax.set_ylabel('Values')
```

### Horizontal Bar Chart
```python
ax.barh(categories, values, color='coral',
        edgecolor='black', linewidth=1.5)
ax.set_xlabel('Values')
```

### Grouped Bar Chart
```python
x = np.arange(len(categories))
width = 0.35

ax.bar(x - width/2, values1, width, label='Group 1')
ax.bar(x + width/2, values2, width, label='Group 2')
ax.set_xticks(x, categories)
ax.legend()
```

### Stacked Bar Chart
```python
ax.bar(categories, values1, label='Part 1')
ax.bar(categories, values2, bottom=values1, label='Part 2')
ax.bar(categories, values3, bottom=values1+values2, label='Part 3')
ax.legend()
```

### Bar Chart with Error Bars
```python
ax.bar(categories, values, yerr=errors, capsize=5,
       color='steelblue', edgecolor='black')
```

### Bar Chart with Patterns
```python
bars1 = ax.bar(x - width/2, values1, width, label='Group 1',
               color='white', edgecolor='black', hatch='//')
bars2 = ax.bar(x + width/2, values2, width, label='Group 2',
               color='white', edgecolor='black', hatch='\\\\')
```

## 4. Histograms

**Use cases:** Distributions, frequency analysis

### Basic Histogram
```python
ax.hist(data, bins=30, edgecolor='black', alpha=0.7)
ax.set_xlabel('Value')
ax.set_ylabel('Frequency')
```

### Multiple Overlapping Histograms
```python
bins = np.histogram_bin_edges(np.concatenate([data1, data2]), bins=30)
ax.hist(data1, bins=bins, alpha=0.5, label='Dataset 1')
ax.hist(data2, bins=bins, alpha=0.5, label='Dataset 2')
ax.legend()
```

### Normalized Histogram (Density)

Density integrates to one (`sum(height * bin_width) == 1`); bar heights need not
sum to one. A normal-density overlay does not establish goodness of fit.
```python
ax.hist(data, bins=30, density=True, alpha=0.7,
        edgecolor='black', label='Empirical')

# Overlay theoretical distribution
from scipy.stats import norm
x = np.linspace(data.min(), data.max(), 100)
ax.plot(x, norm.pdf(x, data.mean(), data.std()),
        'r-', linewidth=2, label='Normal fit')
ax.legend()
```

### 2D Histogram (Hexbin)
```python
hexbin = ax.hexbin(x, y, gridsize=30, cmap='Blues')
plt.colorbar(hexbin, ax=ax, label='Counts')
```

### 2D Histogram (hist2d)
```python
h = ax.hist2d(x, y, bins=30, cmap='Blues')
plt.colorbar(h[3], ax=ax, label='Counts')
```

## 5. Box and Violin Plots

**Use cases:** Statistical distributions, outlier detection, comparing distributions

### Box Plot

Default whiskers reach the most extreme observation within 1.5 IQR of each
quartile; fliers are observations beyond them, not proven data errors.
```python
ax.boxplot([data1, data2, data3],
           tick_labels=['Group A', 'Group B', 'Group C'],
           showmeans=True, meanline=True)
ax.set_ylabel('Values')
```

### Horizontal Box Plot
```python
ax.boxplot([data1, data2, data3],
           orientation='horizontal',
           tick_labels=['Group A', 'Group B', 'Group C'])
ax.set_xlabel('Values')
```

### Violin Plot

Bandwidth controls apparent modes. Count valid samples per group explicitly;
3.11 ignores masked/nonfinite values. Do not silently compare groups after
different exclusion rates, and handle empty or singleton groups before plotting.
```python
parts = ax.violinplot([data1, data2, data3],
                      positions=[1, 2, 3],
                      showmeans=True, showmedians=True)
ax.set_xticks([1, 2, 3], ['Group A', 'Group B', 'Group C'])
```

## 6. Heatmaps

**Use cases:** Matrix data, correlations, intensity maps

### Basic Heatmap

Choose `origin`, `extent`, and aspect from array orientation and physical units.
Use equal aspect for equal physical x/y units; `aspect="auto"` is suitable for
abstract matrices. Comparable panels require the same norm, limits, and units.
```python
im = ax.imshow(matrix, cmap='viridis', aspect='auto', interpolation='nearest')
plt.colorbar(im, ax=ax, label='Values')
ax.set_xlabel('X')
ax.set_ylabel('Y')
```

### Heatmap with Annota

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

