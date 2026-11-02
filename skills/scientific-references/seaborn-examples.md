---
id: sciref-seaborn-examples
name: "Scientific Ref: Seaborn Common Use Cases and Examples"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (seaborn): Seaborn Common Use Cases and Examples"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "seaborn examples"
  - "seaborn common use cases and examples"
keywords:
  - "seaborn"
  - "examples"
  - "specialized"
  - "scientific"
  - "reference"
  - "common"
---

# Seaborn Common Use Cases and Examples

Seaborn 0.13.2 recipes reviewed 2026-10-01. These are illustrative templates: supply the named DataFrames and adapt the sampling design before using the statistics. Corrected contracts were exercised with tiny synthetic fixtures; notebook widget display and arbitrary scientific datasets were not validated. Import NumPy, pandas, Matplotlib, and Seaborn as below before using later snippets.

## Exploratory Data Analysis

### Quick Dataset Overview

```python
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# Load data
df = pd.read_csv('data.csv')

# Pairwise relationships for all numeric variables
sns.pairplot(df, hue='target_variable', corner=True, diag_kind='kde')
plt.suptitle('Dataset Overview', y=1.01)
plt.savefig('overview.png', dpi=300, bbox_inches='tight')
```

### Distribution Exploration

```python
# Multiple distributions across categories
g = sns.displot(
    data=df,
    x='measurement',
    hue='condition',
    col='timepoint',
    kind='kde',
    fill=True,
    height=3,
    aspect=1.5,
    col_wrap=3,
    common_norm=False
)
g.set_axis_labels('Measurement Value', 'Density')
g.set_titles('{col_name}')
```

### Correlation Analysis

```python
# Compute correlation matrix
corr = df.select_dtypes(include='number').corr()

# Create mask for upper triangle
mask = np.triu(np.ones_like(corr, dtype=bool))

# Plot heatmap
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(
    corr,
    mask=mask,
    annot=True,
    fmt='.2f',
    cmap='coolwarm',
    center=0,
    square=True,
    linewidths=1,
    cbar_kws={'shrink': 0.8}
)
plt.title('Correlation Matrix')
plt.tight_layout()
```

## Scientific Publications

### Multi-Panel Figure with Different Plot Types

```python
# Set publication style
sns.set_theme(style='ticks', context='paper', font_scale=1.1)
sns.set_palette('colorblind')

# Create figure with custom layout
fig = plt.figure(figsize=(12, 8))
gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)

# Panel A: Time series
ax1 = fig.add_subplot(gs[0, :2])
sns.lineplot(
    data=timeseries_df,
    x='time',
    y='expression',
    hue='gene',
    style='treatment',
    markers=True,
    dashes=False,
    ax=ax1
)
ax1.set_title('A. Gene Expression Over Time', loc='left', fontweight='bold')
ax1.set_xlabel('Time (hours)')
ax1.set_ylabel('Expression Level (AU)')

# Panel B: Distribution comparison
ax2 = fig.add_subplot(gs[0, 2])
sns.violinplot(
    data=expression_df,
    x='treatment',
    y='expression',
    inner='box',
    ax=ax2
)
ax2.set_title('B. Expression Distribution', loc='left', fontweight='bold')
ax2.set_xlabel('Treatment')
ax2.set_ylabel('')

# Panel C: Correlation
ax3 = fig.add_subplot(gs[1, 0])
sns.scatterplot(
    data=correlation_df,
    x='gene1',
    y='gene2',
    hue='cell_type',
    alpha=0.6,
    ax=ax3
)
sns.regplot(
    data=correlation_df,
    x='gene1',
    y='gene2',
    scatter=False,
    color='black',
    ax=ax3
)
ax3.set_title('C. Gene Correlation', loc='left', fontweight='bold')
ax3.set_xlabel('Gene 1 Expression')
ax3.set_ylabel('Gene 2 Expression')

# Panel D: Heatmap
ax4 = fig.add_subplot(gs[1, 1:])
sns.heatmap(
    sample_matrix,
    cmap='RdBu_r',
    center=0,
    annot=True,
    fmt='.1f',
    cbar_kws={'label': 'Log2 Fold Change'},
    ax=ax4
)
ax4.set_title('D. Treatment Effects', loc='left', fontweight='bold')
ax4.set_xlabel('Sample')
ax4.set_ylabel('Gene')

# Clean up
sns.despine()
plt.savefig('figure.pdf', dpi=300, bbox_inches='tight')
plt.savefig('figure.png', dpi=300, bbox_inches='tight')
```

### Box Plot with Significance Annotations

```python
import numpy as np
from scipy import stats
from statsmodels.stats.multitest import multipletests

# Assumes independent experimental units and two prespecified contrasts.
# Paired or clustered designs need a corresponding analysis.
comparisons = [('Control', 'High'), ('Control', 'Low')]
raw_p = []
for left, right in comparisons:
    a = df.loc[df['treatment'].eq(left), 'response'].dropna()
    b = df.loc[df['treatment'].eq(right), 'response'].dropna()
    if min(len(a), len(b)) < 2 or not np.isfinite(np.r_[a, b]).all():
        raise ValueError('Need at least two finite independent measurements per group')
    raw_p.append(stats.ttest_ind(a, b, equal_var=False).pvalue)
if not np.isfinite(raw_p).all():
    raise ValueError('A contrast was undefined; do not label it nonsignificant')
adjusted_p = multipletests(raw_p, method='holm')[1]

# Create plot
fig, ax = plt.subplots(figsize=(8, 6))
sns.boxplot(
    data=df,
    x='treatment',
    y='response',
    hue='treatment',
    order=['Control', 'Low', 'Medium', 'High'],
    palette='Set2',
    legend=False,
    ax=ax
)

# Add individual points
sns.stripplot(
    data=df,
    x='treatment',
    y='response',
    order=['Control', 'Low', 'Medium', 'High'],
    color='black',
    alpha=0.3,
    size=3,
    ax=ax
)

# Add significance bars
def add_significance_bar(ax, x1, x2, y, h, text):
    ax.plot([x1, x1, x2, x2], [y, y+h, y+h, y], 'k-', lw=1.5)
    ax.text((x1+x2)/2, y+h, text, ha='center', va='bottom')

y_max = df['response'].max()
add_significance_bar(ax, 0, 3, y_max + 1, 0.5, f'Holm p={adjusted_p[0]:.3g}')
add_significance_bar(ax, 0, 1, y_max + 3, 0.5, f'Holm p={adjusted_p[1]:.3g}')

ax.set_ylabel('Response (μM)')
ax.set_xlabel('Treatment Condition')
ax.set_title('Treatment Response Analysis')
sns.despine()
```

## Time Series Analysis

These aggregate examples assume independent replicates at each timestamp. Inspect missingness and replicate counts before plotting. `lineplot` bridges missing rows; use the explicit segment recipe in [patterns_and_troubleshooting.md](patterns_and_troubleshooting.md) for gaps. Autocorrelated samples are not independent replicates.

### Multiple Time Series with Confidence Bands

```python
# Plot with automatic aggregation
fig, ax = plt.subplots(figsize=(10, 6))
sns.lineplot(
    data=timeseries_df,
    x='timestamp',
    y='value',
    hue='sensor',
    style='location',
    markers=True,
    dashes=False,
    errorbar=('ci', 95),
    ax=ax
)

# Customize
ax.set_xlabel('Date')
ax.set_ylabel('Measurement (units)')
ax.set_title('Sensor Measurements Over Time')
ax.legend(title='Sensor & Location', bbox_to_anchor=(1.05, 1), loc='upper left')

# Format x-axis for dates
import matplotlib.dates as mdates
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
plt.xtic

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

