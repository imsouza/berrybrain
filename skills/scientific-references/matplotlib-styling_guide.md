---
id: sciref-matplotlib-styling-guide
name: "Scientific Ref: Matplotlib Styling Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matplotlib): Matplotlib Styling Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matplotlib styling guide"
keywords:
  - "matplotlib"
  - "styling"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
---

# Matplotlib Styling Guide

Styling patterns for Matplotlib 3.11.2. Fragments assume NumPy/pyplot imports and named inputs. Style settings control presentation; verify scientific scales and uncertainty independently.

## Colormaps

### Colormap Categories

**1. Perceptually Uniform Sequential**
Best for ordered data that progresses from low to high values.
- `viridis` (default, colorblind-friendly)
- `plasma`
- `inferno`
- `magma`
- `cividis` (optimized for colorblind viewers)

**Usage:**
```python
im = ax.imshow(data, cmap='viridis')
scatter = ax.scatter(x, y, c=values, cmap='plasma')
```

**2. Sequential**
Traditional colormaps for ordered data.
- `Blues`, `Greens`, `Reds`, `Oranges`, `Purples`
- `YlOrBr`, `YlOrRd`, `OrRd`, `PuRd`
- `BuPu`, `GnBu`, `PuBu`, `YlGnBu`

**3. Diverging**
Best for data with a meaningful center point (e.g., zero, mean).
- `coolwarm` (blue to red)
- `RdBu` (red-blue)
- `RdYlBu` (red-yellow-blue)
- `RdYlGn` (red-yellow-green)
- `PiYG`, `PRGn`, `BrBG`, `PuOr`, `RdGy`

**Usage:**
```python
# Center colormap at zero
im = ax.imshow(data, cmap='coolwarm', vmin=-1, vmax=1)
```

**4. Qualitative**
Best for categorical/nominal data without inherent ordering.
- `tab10` (10 distinct colors)
- `tab20` (20 distinct colors)
- `Set1`, `Set2`, `Set3`
- `Pastel1`, `Pastel2`
- `Dark2`, `Accent`, `Paired`

**Usage:**
```python
import matplotlib as mpl

# tab10 has only 10 distinct colors; do not interpolate beyond its capacity.
if n_categories > 10:
    raise ValueError('Use another encoding or a larger distinguishable palette')
colors = mpl.colormaps['tab10'].colors[:n_categories]
for i, category in enumerate(categories):
    ax.plot(x, y[i], color=colors[i], label=category)
```

**5. Cyclic**
Best for cyclic data (e.g., phase, angle).
- `twilight`
- `twilight_shifted`
- `hsv` (not perceptually uniform; inspect lightness artifacts)

### Colormap Best Practices

1. **Avoid `jet` colormap** - Not perceptually uniform, misleading
2. **Use perceptually uniform colormaps** - `viridis`, `plasma`, `cividis`
3. **Consider colorblind users** - Use `viridis`, `cividis`, or test with colorblind simulators
4. **Match colormap to data type**:
   - Sequential: increasing/decreasing data
   - Diverging: data with meaningful center
   - Qualitative: categories
5. **Reverse colormaps** - Add `_r` suffix: `viridis_r`, `coolwarm_r`

### Shared Scales and Missing Values

Use one explicit norm for comparable panels, based on a justified common domain.
A diverging map alone does not center zero when limits are asymmetric.

```python
from matplotlib.colors import TwoSlopeNorm
import matplotlib as mpl

norm = TwoSlopeNorm(vmin=-2, vcenter=0, vmax=5)
cmap = mpl.colormaps['RdBu_r'].with_extremes(bad='lightgray')
fig, axes = plt.subplots(1, 2, layout='constrained')
for ax, values in zip(axes, [data1, data2]):
    im = ax.imshow(np.ma.masked_invalid(values), cmap=cmap, norm=norm,
                   interpolation='nearest')
fig.colorbar(im, ax=axes, label='Change (data units)', extend='both')
```

Document missing-value color, bounds, units, and out-of-range behavior. Norm
objects already carry limits; do not also pass `vmin`/`vmax`. `LogNorm` requires
positive data: count/mask zero and negative values explicitly, or use a justified
`SymLogNorm`. Prefer `with_extremes` over pending-deprecated mutating setters.

### Creating Custom Colormaps

```python
from matplotlib.colors import LinearSegmentedColormap
import matplotlib as mpl

# From color list
colors = ['blue', 'white', 'red']
n_bins = 100
cmap = LinearSegmentedColormap.from_list('custom', colors, N=n_bins)

# From RGB values
colors = [(0, 0, 1), (1, 1, 1), (1, 0, 0)]  # RGB tuples
cmap = LinearSegmentedColormap.from_list('custom', colors)

# Use the custom colormap
ax.imshow(data, cmap=cmap)

# Optionally register it by name for reuse
mpl.colormaps.register(cmap, name='custom')
```

### Discrete Colormaps

```python
import matplotlib.colors as mcolors
import matplotlib as mpl

# Create discrete colormap from continuous
cmap = mpl.colormaps['viridis']
bounds = np.linspace(0, 10, 11)
norm = mcolors.BoundaryNorm(bounds, cmap.N)
im = ax.imshow(data, cmap=cmap, norm=norm)
```

## Style Sheets

### Using Built-in Styles

```python
# List available styles
print(plt.style.available)

# Apply a style
plt.style.use('seaborn-v0_8-darkgrid')

# Apply multiple styles (later styles override earlier ones)
plt.style.use(['seaborn-v0_8-whitegrid', 'seaborn-v0_8-poster'])

# Temporarily use a style
with plt.style.context('ggplot'):
    fig, ax = plt.subplots()
    ax.plot(x, y)
```

### Popular Built-in Styles

- `default` - Matplotlib's default style
- `classic` - Classic matplotlib look (pre-2.0)
- `seaborn-v0_8-*` - Seaborn-inspired styles
  - `seaborn-v0_8-darkgrid`, `seaborn-v0_8-whitegrid`
  - `seaborn-v0_8-dark`, `seaborn-v0_8-white`
  - `seaborn-v0_8-ticks`, `seaborn-v0_8-poster`, `seaborn-v0_8-talk`
- `ggplot` - ggplot2-inspired style
- `bmh` - Bayesian Methods for Hackers style
- `fivethirtyeight` - FiveThirtyEight style
- `grayscale` - Grayscale style

### Creating Custom Style Sheets

Create a file named `custom_style.mplstyle`:

```
# custom_style.mplstyle

# Figure
figure.figsize: 10, 6
figure.dpi: 100
figure.facecolor: white

# Font
font.family: sans-serif
font.sans-serif: Arial, Helvetica, DejaVu Sans
font.size: 12

# Axes
axes.labelsize: 14
axes.titlesize: 16
axes.facecolor: white
axes.edgecolor: black
axes.linewidth: 1.5
axes.grid: True
axes.axisbelow: True

# Grid
grid.color: gray
grid.linestyle: --
grid.linewidth: 0.5
grid.alpha: 0.3

# Lines
lines.linewidth: 2
lines.markersize: 8

# Ticks
xtick.labelsize: 10
ytick.labelsize: 10
xtick.direction: in
ytick.direction: in
xtick.major.size: 6
ytick.major.size: 6
xtick.minor.size: 3
ytick.minor.size: 3

# Legend
legend.fontsize: 12
legend.frameon: True
legend.framealpha: 0.8
legend.fancybox: True

# Savefig
savefig.dpi: 300
savefig.bbox: tight
savefig.facecolor: white
```

Style files treat unquoted `#` as a comment: write `axes.facecolor: "#1e1e1e"`
for hex colors. Save as UTF-8. These files configure plotting, not scientific
validity; review font availability and final-size readability.

Load and use:
```python
plt.style.use('path/to/custom_style.mplstyle')
```

## rcParams Configuration

### Global Configuration

```python
import matplotlib.pyplot as plt

# Configure globally
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14

# Or upda

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

