---
id: sciref-seaborn-palettes-and-theming
name: "Scientific Ref: Color Palettes, Theming, and Aesthetics"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (seaborn): Color Palettes, Theming, and Aesthetics"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "seaborn palettes theming"
  - "color palettes, theming, and aesthetics"
keywords:
  - "seaborn"
  - "palettes"
  - "theming"
  - "specialized"
  - "scientific"
  - "reference"
  - "color"
---

# Color Palettes, Theming, and Aesthetics

Qualitative, sequential, and diverging palettes, colorblind-safe choices, and theme,
context, and style control.

## Color Palettes

Seaborn provides carefully designed color palettes for different data types:

### Qualitative Palettes (Categorical Data)

Distinguish categories through hue variation:
- `"deep"` - Default, vivid colors
- `"muted"` - Softer, less saturated
- `"pastel"` - Light, desaturated
- `"bright"` - Highly saturated
- `"dark"` - Dark values
- `"colorblind"` - Designed to improve distinction for common color vision deficiencies; also use shapes, line styles, or direct labels

```python
sns.set_palette("colorblind")
sns.color_palette("Set2")
```

### Sequential Palettes (Ordered Data)

Show progression from low to high values:
- `"rocket"`, `"mako"` - Wide luminance range (good for heatmaps)
- `"flare"`, `"crest"` - Restricted luminance (good for points/lines)
- `"viridis"`, `"magma"`, `"plasma"` - Matplotlib perceptually uniform

```python
sns.heatmap(data, cmap='rocket')
sns.kdeplot(data=df, x='x', y='y', cmap='mako', fill=True)
```

### Diverging Palettes (Centered Data)

Emphasize deviations from a midpoint:
- `"vlag"` - Blue to red
- `"icefire"` - Blue to orange
- `"coolwarm"` - Cool to warm
- `"Spectral"` - Rainbow diverging

```python
sns.heatmap(correlation_matrix, cmap='vlag', center=0)
```

### Custom Palettes

```python
# Create custom palette
custom = sns.color_palette("husl", 8)

# Light to dark gradient
palette = sns.light_palette("seagreen", as_cmap=True)

# Diverging palette from hues
palette = sns.diverging_palette(250, 10, as_cmap=True)
```

## Theming and Aesthetics

### Set Theme

`set_theme()` controls overall appearance:

```python
# Set complete theme
sns.set_theme(style='whitegrid', palette='pastel', font='sans-serif')

# Reset to defaults
sns.set_theme()
```

### Styles

Control background and grid appearance:
- `"darkgrid"` - Gray background with white grid (default)
- `"whitegrid"` - White background with gray grid
- `"dark"` - Gray background, no grid
- `"white"` - White background, no grid
- `"ticks"` - White background with axis ticks

```python
sns.set_style("whitegrid")

# Remove spines
sns.despine(left=False, bottom=False, offset=10, trim=True)

# Temporary style
with sns.axes_style("white"):
    sns.scatterplot(data=df, x='x', y='y')
```

### Contexts

Scale elements for different use cases:
- `"paper"` - Smallest
- `"notebook"` - Default context, slightly larger
- `"talk"` - Presentation slides
- `"poster"` - Large format

```python
sns.set_context("talk", font_scale=1.2)

# Temporary context
with sns.plotting_context("poster"):
    sns.barplot(data=df, x='category', y='value')
```

Reviewed against [the palette tutorial](https://seaborn.pydata.org/tutorial/color_palettes.html) and [plotting_context](https://seaborn.pydata.org/generated/seaborn.plotting_context.html), 2026-10-01. A palette name alone does not establish accessibility for a finished figure.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

