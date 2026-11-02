---
id: sciref-matplotlib-common-issues
name: "Scientific Ref: Matplotlib Common Issues and Solutions"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matplotlib): Matplotlib Common Issues and Solutions"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matplotlib common issues"
  - "matplotlib common issues and solutions"
keywords:
  - "matplotlib"
  - "common"
  - "issues"
  - "specialized"
  - "scientific"
  - "reference"
---

# Matplotlib Common Issues and Solutions

Targets Matplotlib 3.11.2. Snippets illustrate individual fixes and assume imports, a figure, and suitable data unless shown. Apply alternatives separately; do not combine layout engines or run notebook magics as Python scripts.

## Display and Backend Issues

### Issue: Plots Not Showing

**Problem:** `plt.show()` doesn't display anything

**Solutions:**
```python
# 1. Check if backend is properly set (for interactive use)
import matplotlib
print(matplotlib.get_backend())

# 2. Select an installed GUI backend before importing pyplot
matplotlib.use('TkAgg')  # or 'QtAgg', 'MacOSX'; requires the corresponding GUI toolkit
import matplotlib.pyplot as plt

# 3. In Jupyter notebooks, use magic command
%matplotlib inline  # Static images
# or
%matplotlib widget  # Interactive plots

# 4. Ensure plt.show() is called
plt.plot([1, 2, 3])
plt.show()
```

### Issue: "RuntimeError: main thread is not in main loop"

**Problem:** Interactive mode issues with threading

**Solution:**
```python
# Switch to non-interactive backend
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# plt.ioff() alone does not make a GUI backend safe in a worker thread.
```

### Issue: Figures Not Updating Interactively

**Problem:** Changes not reflected in interactive windows

**Solution:**
```python
# Enable interactive mode
plt.ion()

# Draw after each change
plt.plot(x, y)
plt.draw()
plt.pause(0.001)  # Brief pause to update display
```

## Layout and Spacing Issues

### Issue: Overlapping Labels and Titles

**Problem:** Labels, titles, or tick labels overlap or get cut off

**Solutions:**
```python
# Solution 1: Constrained layout (RECOMMENDED)
fig, ax = plt.subplots(layout='constrained')

# Solution 2: Tight layout
fig, ax = plt.subplots()
plt.tight_layout()

# Solution 3: Adjust margins manually
plt.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.15)

# Solution 4: Crop the export (changes final dimensions; does not fix overlaps)
plt.savefig('figure.png', bbox_inches='tight')

# Solution 5: Rotate long tick labels
ax.set_xticks(positions, labels)
plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
```

### Issue: Colorbar Affects Subplot Size

**Problem:** Adding colorbar shrinks the plot

**Solution:**
```python
# Solution 1: Use constrained layout
fig, ax = plt.subplots(layout='constrained')
im = ax.imshow(data)
plt.colorbar(im, ax=ax)

# Solution 2: Manually specify colorbar dimensions
from mpl_toolkits.axes_grid1 import make_axes_locatable
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0.05)
plt.colorbar(im, cax=cax)

# Solution 3: For multiple subplots, share colorbar
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax in axes:
    im = ax.imshow(data)
fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.95)
```

### Issue: Subplots Too Close Together

**Problem:** Multiple subplots overlapping

**Solution:**
```python
# Solution 1: Use constrained_layout
fig, axes = plt.subplots(2, 2, layout='constrained')

# Solution 2: Adjust spacing with subplots_adjust
fig, axes = plt.subplots(2, 2)
plt.subplots_adjust(hspace=0.4, wspace=0.4)

# Solution 3: Specify spacing in tight_layout
plt.tight_layout(h_pad=2.0, w_pad=2.0)
```

## Memory and Performance Issues

### Issue: Memory Leak with Multiple Figures

**Problem:** Memory usage grows when creating many figures

**Solution:**
```python
# Close figures explicitly
fig, ax = plt.subplots()
ax.plot(x, y)
plt.savefig('plot.png')
plt.close(fig)  # or plt.close('all')

# Clear current figure without closing
plt.clf()

# Clear current axes
plt.cla()
```

### Issue: Large File Sizes

**Problem:** Saved figures are too large

**Solutions:**
```python
# Solution 1: Reduce DPI
plt.savefig('figure.png', dpi=150)  # Instead of 300

# Solution 2: Use rasterization for complex plots
ax.plot(x, y, rasterized=True)

# Solution 3: Use vector format for simple plots
plt.savefig('figure.pdf')  # or .svg

# Solution 4: Pass PNG compression options through Pillow
fig.savefig('figure.png', dpi=300, pil_kwargs={'optimize': True})
```

### Issue: Slow Plotting with Large Datasets

**Problem:** Plotting takes too long with many points

**Solutions:**
```python
# Solution 1: Downsample data
from scipy.signal import decimate
y_downsampled = decimate(y, 10)  # Anti-alias filtering, then decimation
ax.plot(x[::10], y_downsampled)  # Assumes evenly sampled x; inspect edge effects

# Solution 2: Use rasterization
ax.plot(x, y, rasterized=True)

# Solution 3: Simplify paths in display coordinates; check that peaks survive
with plt.rc_context({'path.simplify': True, 'path.simplify_threshold': 0.1}):
    fig, ax = plt.subplots()
    ax.plot(x, y)
    fig.savefig('simplified.png')

# Solution 4: For scatter plots, consider hexbin or 2d histogram
ax.hexbin(x, y, gridsize=50, cmap='viridis')
```

## Font and Text Issues

### Issue: Font Warnings

**Problem:** "findfont: Font family [...] not found"

**Solutions:**
```python
# Solution 1: Use available fonts
from matplotlib.font_manager import findfont, FontProperties
print(findfont(FontProperties(family=['sans-serif'])))

# Solution 2: Check Matplotlib's cache directory, then restart Python
import matplotlib
print(matplotlib.get_cachedir())

# Solution 3: Specify installed fallback fonts; missing-glyph warnings matter
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
```

### Issue: LaTeX Rendering Errors

**Problem:** Math text not rendering correctly

**Solutions:**
```python
# Solution 1: Use raw strings with r prefix
ax.set_xlabel(r'$\alpha$')  # Not '\alpha'

# Solution 2: Escape backslashes in regular strings
ax.set_xlabel('$\\alpha$')

# Solution 3: Disable LaTeX if not installed
plt.rcParams['text.usetex'] = False

# Solution 4: Use mathtext instead of full LaTeX
# Mathtext is always available, no LaTeX installation needed
ax.text(x, y, r'$\int_0^\infty e^{-x} dx$')
```

### Issue: Text Cut Off or Outside Figure

**Problem:** Labels or annotations appear outside figure bounds

**Solutions:**
```python
# Solution 1: Use bbox_inches='tight'
plt.savefig('figure.png', bbox_inches='tight')

# Solution 2: Adjust figure bounds
plt.subplots_adjust(left=0.15, right=0.85, top=0.85, bottom=0.15)

# Solution 3: Clip text to axes
ax.text(x, y, 'text', clip_on=True)

# Solution 4: Use constrained_layout
fig, ax = plt.subplots(layout='constrained')
```

## Color and Colormap Issues

### Issue: Colorbar Not Matching Plot

**Pro

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

