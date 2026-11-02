---
id: sciref-matplotlib-api-reference
name: "Scientific Ref: Matplotlib API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matplotlib): Matplotlib API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matplotlib api reference"
keywords:
  - "matplotlib"
  - "api"
  - "reference"
  - "specialized"
  - "scientific"
---

# Matplotlib API Reference

Targets Matplotlib 3.11.2. Examples are fragments requiring imports and correctly shaped named data. See the [official API](https://matplotlib.org/stable/api/index.html) and [3.11 changes](https://matplotlib.org/stable/api/prev_api_changes/api_changes_3.11.0.html).

## Core Classes

### Figure

The top-level container for all plot elements.

**Creation:**
```python
fig = plt.figure(figsize=(10, 6), dpi=100, facecolor='white')
fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(10, 6))
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
```

**Key Methods:**
- `fig.add_subplot(nrows, ncols, index)` - Add a subplot
- `fig.add_axes([left, bottom, width, height])` - Add axes at specific position
- `fig.savefig(filename, dpi=300, bbox_inches='tight')` - Save figure
- `fig.tight_layout()` - Adjust spacing to prevent overlaps
- `fig.suptitle(title)` - Set figure title
- `fig.legend()` - Create figure-level legend
- `fig.colorbar(mappable, ax=ax)` - Add colorbar to figure
- `plt.close(fig)` - Close figure to free memory

**Key Attributes:**
- `fig.axes` - List of all axes in the figure
- `fig.dpi` - Resolution in dots per inch
- `fig.get_size_inches()` - Figure dimensions in inches (width, height); use `fig.set_size_inches(width, height)` to change them

### Axes

The actual plotting area where data is visualized.

**Creation:**
```python
fig, ax = plt.subplots()  # Single axes
ax = fig.add_subplot(111)  # Alternative method
```

**Plotting Methods:**

**Line plots:**
- `ax.plot(x, y, **kwargs)` - Line plot
- `ax.step(x, y, where='pre'/'mid'/'post')` - Step plot
- `ax.errorbar(x, y, yerr=yerr, xerr=xerr)` - Nonnegative error sizes: scalar, `(N,)`, or `(2, N)` for lower/upper sizes

**Scatter plots:**
- `ax.scatter(x, y, s=size, c=color, marker='o', alpha=0.5)` - Scatter plot

**Bar charts:**
- `ax.bar(x, height, width=0.8, align='center')` - Vertical bar chart
- `ax.barh(y, width)` - Horizontal bar chart

**Statistical plots:**
- `ax.hist(data, bins=10, density=False)` - Histogram
- `ax.boxplot(data, tick_labels=None, orientation='vertical')` - Box plot
- `ax.violinplot(data)` - Violin plot

**2D plots:**
- `ax.imshow(array, cmap='viridis', aspect='auto')` - Display image/matrix
- `ax.contour(X, Y, Z, levels=10)` - Contour lines
- `ax.contourf(X, Y, Z, levels=10)` - Filled contours
- `ax.pcolormesh(X, Y, Z)` - Pseudocolor plot

**Filling:**
- `ax.fill_between(x, y1, y2, alpha=0.3)` - Fill between curves
- `ax.fill_betweenx(y, x1, x2)` - Fill between vertical curves

**Text and annotations:**
- `ax.text(x, y, text, fontsize=12)` - Add text
- `ax.annotate(text, xy=(x, y), xytext=(x2, y2), arrowprops={})` - Annotate with arrow

**Customization Methods:**

**Labels and titles:**
- `ax.set_xlabel(label, fontsize=12)` - Set x-axis label
- `ax.set_ylabel(label, fontsize=12)` - Set y-axis label
- `ax.set_title(title, fontsize=14)` - Set axes title

**Limits and scales:**
- `ax.set_xlim(left, right)` - Set x-axis limits
- `ax.set_ylim(bottom, top)` - Set y-axis limits
- `ax.set_xscale('linear'/'log'/'symlog')` - Set x-axis scale
- `ax.set_yscale('linear'/'log'/'symlog')` - Set y-axis scale

**Ticks:**
- `ax.set_xticks(positions)` - Set x-tick positions
- `ax.set_xticks(positions, labels)` - Set x-tick positions and labels together
- `ax.tick_params(axis='both', labelsize=10)` - Customize tick appearance

**Grid and spines:**
- `ax.grid(True, alpha=0.3, linestyle='--')` - Add grid
- `ax.spines['top'].set_visible(False)` - Hide top spine
- `ax.spines['right'].set_visible(False)` - Hide right spine

**Legend:**
- `ax.legend(loc='best', fontsize=10, frameon=True)` - Add legend
- `ax.legend(handles, labels)` - Custom legend

**Aspect and layout:**
- `ax.set_aspect('equal'/'auto'/ratio)` - Set aspect ratio
- `ax.invert_xaxis()` - Invert x-axis
- `ax.invert_yaxis()` - Invert y-axis

### pyplot Module

High-level interface for quick plotting.

**Figure creation:**
- `plt.figure()` - Create new figure
- `plt.subplots()` - Create figure and axes
- `plt.subplot()` - Add subplot to current figure

**Plotting (uses current axes):**
- `plt.plot()` - Line plot
- `plt.scatter()` - Scatter plot
- `plt.bar()` - Bar chart
- `plt.hist()` - Histogram
- Many plotting methods have pyplot wrappers; Axes setters are not all exposed with the same name (for example, `plt.xlabel` wraps `ax.set_xlabel`).

**Display and save:**
- `plt.show()` - Display figure
- `plt.savefig()` - Save figure
- `plt.close()` - Close figure

**Style:**
- `plt.style.use(style_name)` - Apply style sheet
- `plt.style.available` - List available styles

**State management:**
- `plt.gca()` - Get current axes
- `plt.gcf()` - Get current figure
- `plt.sca(ax)` - Set current axes
- `plt.clf()` - Clear current figure
- `plt.cla()` - Clear current axes

## Line and Marker Styles

### Line Styles
- `'-'` or `'solid'` - Solid line
- `'--'` or `'dashed'` - Dashed line
- `'-.'` or `'dashdot'` - Dash-dot line
- `':'` or `'dotted'` - Dotted line
- `''` or `' '` or `'None'` - No line

### Marker Styles
- `'.'` - Point marker
- `'o'` - Circle marker
- `'v'`, `'^'`, `'<'`, `'>'` - Triangle markers
- `'s'` - Square marker
- `'p'` - Pentagon marker
- `'*'` - Star marker
- `'h'`, `'H'` - Hexagon markers
- `'+'` - Plus marker
- `'x'` - X marker
- `'D'`, `'d'` - Diamond markers

### Color Specifications

**Single character shortcuts:**
- `'b'` - Blue
- `'g'` - Green
- `'r'` - Red
- `'c'` - Cyan
- `'m'` - Magenta
- `'y'` - Yellow
- `'k'` - Black
- `'w'` - White

**Named colors:**
- `'steelblue'`, `'coral'`, `'teal'`, etc.
- See full list: https://matplotlib.org/stable/gallery/color/named_colors.html

**Other formats:**
- Hex: `'#FF5733'`
- RGB tuple: `(0.1, 0.2, 0.3)`
- RGBA tuple: `(0.1, 0.2, 0.3, 0.5)`

## Common Parameters

### Plot Function Parameters

```python
ax.plot(x, y,
    color='blue',           # Line color
    linewidth=2,            # Line width
    linestyle='--',         # Line style
    marker='o',             # Marker style
    markersize=8,           # Marker size
    markerfacecolor='red',  # Marker fill color
    markeredgecolor='black',# Marker edge color
    markeredgewidth=1,      # Marker edge width
    alpha=0.7,              # Transparency (0-1)
    label='data',           # Legend label
    zorder=2,               # Drawing order
    rasterized=True         # Rasterize for smaller file size
)
```

### Scatter Function Parameters

```python
ax.scatter(x, y,
    s=50,                   # Marker area in points squared
 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

