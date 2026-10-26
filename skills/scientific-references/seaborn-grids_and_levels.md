---
id: sciref-seaborn-grids-and-levels
name: "Scientific Ref: Multi-Plot Grids, Figure-Level vs Axes-Level"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (seaborn): Multi-Plot Grids, Figure-Level vs Axes-Level"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "seaborn grids levels"
  - "multi-plot grids, figure-level vs axes-level"
keywords:
  - "seaborn"
  - "grids"
  - "levels"
  - "specialized"
  - "scientific"
  - "reference"
  - "multi"
  - "plot"
---

# Multi-Plot Grids, Figure-Level vs Axes-Level

`FacetGrid`, `PairGrid`, and `JointGrid`, and how figure-level and axes-level functions
differ in what they return and how they are composed with Matplotlib.

## Multi-Plot Grids

Seaborn provides grid objects for creating complex multi-panel figures:

### FacetGrid

Create subplots based on categorical variables. Most useful when called through figure-level functions (`relplot`, `displot`, `catplot`), but can be used directly for custom plots.

```python
g = sns.FacetGrid(df, col='time', row='sex', hue='smoker')
g.map_dataframe(sns.scatterplot, x='total_bill', y='tip')
g.add_legend()
```

### PairGrid

Show pairwise relationships between all variables in a dataset.

```python
g = sns.PairGrid(df, hue='species')
g.map_upper(sns.scatterplot)
g.map_lower(sns.kdeplot)
g.map_diag(sns.histplot)
g.add_legend()
```

### JointGrid

Combine bivariate plot with marginal distributions.

```python
g = sns.JointGrid(data=df, x='total_bill', y='tip')
g.plot_joint(sns.scatterplot)
g.plot_marginals(sns.histplot)
```

## Figure-Level vs Axes-Level Functions

Understanding this distinction is crucial for effective seaborn usage:

### Axes-Level Functions
- Plot to a single matplotlib `Axes` object
- Integrate easily into complex matplotlib figures
- Accept `ax=` parameter for precise placement
- Return `Axes` object
- Examples: `scatterplot`, `histplot`, `boxplot`, `regplot`, `heatmap`

**When to use:**
- Building custom multi-plot layouts
- Combining different plot types
- Need matplotlib-level control
- Integrating with existing matplotlib code

```python
fig, axes = plt.subplots(2, 2, figsize=(10, 10))
sns.scatterplot(data=df, x='x', y='y', ax=axes[0, 0])
sns.histplot(data=df, x='x', ax=axes[0, 1])
sns.boxplot(data=df, x='cat', y='y', ax=axes[1, 0])
sns.kdeplot(data=df, x='x', y='y', ax=axes[1, 1])
```

### Figure-Level Functions
- Manage entire figure including all subplots
- `relplot`, `displot`, `catplot`, and `lmplot` facet via `col`/`row`; `jointplot`/`pairplot` use their own grid layouts
- Return `FacetGrid`, `JointGrid`, or `PairGrid` objects
- Use `height` and usually `aspect` for sizing; `jointplot` has square figure height and no `aspect`
- Cannot be placed in existing figure
- Examples: `relplot`, `displot`, `catplot`, `lmplot`, `jointplot`, `pairplot`

**When to use:**
- Faceted visualizations (small multiples)
- Quick exploratory analysis
- Consistent multi-panel layouts
- Don't need to combine with other plot types

```python
# Automatic faceting
sns.relplot(data=df, x='x', y='y', col='category', row='group',
            hue='type', height=3, aspect=1.2)
```

For direct grids, set a shared `hue_order` and palette mapping when subsets could omit levels. Prefer `map_dataframe` for Seaborn keyword-oriented functions. See [FacetGrid](https://seaborn.pydata.org/generated/seaborn.FacetGrid.html) and [function overview](https://seaborn.pydata.org/tutorial/function_overview.html) (reviewed 2026-10-01).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

