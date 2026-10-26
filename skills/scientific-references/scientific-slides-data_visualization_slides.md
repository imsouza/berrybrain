---
id: sciref-scientific-slides-data-visualization-slides
name: "Scientific Ref: Data Visualization for Slides"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-slides): Data Visualization for Slides"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific slides visualization slides"
  - "cientifico slides visualization slides"
  - "data visualization for slides"
keywords:
  - "scientific"
  - "slides"
  - "visualization"
  - "cientifico"
  - "specialized"
  - "reference"
---

# Data Visualization for Slides

## Overview

Effective data visualization in presentations differs fundamentally from journal figures. While publications prioritize comprehensive detail, presentation slides must emphasize clarity, impact, and immediate comprehension. This guide covers adapting figures for slides, choosing appropriate chart types, and avoiding common visualization mistakes.

## Key Principles for Presentation Figures

### 1. Simplify, Don't Replicate

**The Core Difference**:
- **Journal figures**: Dense, detailed, for careful study
- **Presentation figures**: Clear, simplified, for quick understanding

**Simplification Strategies**:

**Remove Non-Essential Elements**:
- ❌ Minor gridlines
- ❌ Detailed legends (label directly instead)
- ❌ Multiple panels (split into separate slides)
- ❌ Secondary axes (rarely work in presentations)
- ❌ Dense tick marks and minor labels

**Focus on Key Message**:
- Focus the view on the current comparison while retaining controls and results that could change its interpretation
- Disclose selection criteria when subsetting data
- Highlight the specific comparison you're discussing
- Keep essential uncertainty, sample sizes, and limitations visible

**Example Transformation**:
```
Journal Figure:
- 6 panels (A-F)
- 4 experimental conditions per panel
- 50+ data points visible
- Complex statistical annotations
- Small font labels

Presentation Version:
- 3 separate slides (1-2 panels each)
- Focus on key comparison per slide
- Large, clear data representation
- One statistical result highlighted
- Large, readable labels
```

### 2. Emphasize Visual Hierarchy

**Guide Attention**:
- Make key result visually dominant
- De-emphasize background or comparison data
- Use size, color, and position strategically

**Techniques**:

**Color Emphasis**:
```
Main Result: Bold, saturated color (e.g., blue)
Comparison: Muted gray or desaturated color
Background: Very light gray or white
```

**Size Emphasis**:
```
Key line/bar: Thicker (3-4pt)
Reference lines: Thinner (1-2pt)
Grid lines: Very thin (0.5pt) or remove
```

**Annotation**:
```
Add text callouts: "34% increase" with arrow
Add shapes: Circle key region
Add color highlights: Background shading for important area
```

### 3. Maximize Readability

**Font Sizes for Presentations**:
- **Axis labels**: 18-24pt minimum
- **Tick labels**: 16-20pt minimum
- **Title**: 24-32pt
- **Legend**: 16-20pt (or label directly on plot)
- **Annotations**: 18-24pt

**The Distance Test**:
- If your figure isn't readable at 2-3 feet from your laptop screen, it won't work in a presentation
- Test by stepping back from screen
- Better to split into multiple simpler figures

**Line and Marker Sizes**:
- **Lines**: 2-4pt thickness (thicker than journal figures)
- **Markers**: 8-12pt size
- **Error bars**: 1.5-2pt thickness
- **Bars**: Adequate width with clear spacing

### 4. Use Progressive Disclosure

**Build Complex Figures Incrementally**:

Instead of showing complete figure at once:
1. **Baseline**: Show axes and basic setup
2. **Data Group 1**: Add first dataset
3. **Data Group 2**: Add comparison dataset
4. **Highlight**: Emphasize key difference
5. **Interpretation**: Add annotation with finding

**Benefits**:
- Controls audience attention
- Prevents information overload
- Guides interpretation
- Emphasizes narrative structure

**Implementation**:
- PowerPoint: Use animation to reveal layers
- Beamer: Use `\pause` or overlays
- Static: Create sequence of slides building the figure

## Chart Types and When to Use Them

### Bar Charts

**Best For**:
- Comparing discrete categories
- Showing counts or frequencies
- Highlighting differences between groups

**Presentation Optimization**:
```
✅ DO:
- Large, clear bars with adequate spacing
- Horizontal bars for long category names
- Direct labeling on bars (not legend)
- Order by value (highest to lowest) unless natural order exists
- Start y-axis at zero for accurate visual comparison

❌ DON'T:
- Too many categories (max 8-10)
- 3D bars (distorts perception)
- Multiple grouped comparisons (split to separate slides)
- Decorative patterns or gradients
```

**Example Enhancement**:
```
Before: 12 categories, small fonts, legend
After: Top 6 categories only, large fonts, direct labels, key bar highlighted
```

### Line Graphs

**Best For**:
- Trends over time
- Continuous data relationships
- Comparing trajectories

**Presentation Optimization**:
```
✅ DO:
- Thick lines (2-4pt)
- Distinct colors AND line styles (solid, dashed, dotted)
- Direct line labeling (at end of lines, not legend)
- Highlight key line with color/thickness
- Minimal gridlines or none
- Clear markers at data points

❌ DON'T:
- More than 4-5 lines per plot
- Similar colors (ensure high contrast)
- Small markers or thin lines
- Cluttered with excess gridlines
```

**Time Series Tips**:
- Mark key events or interventions with vertical lines
- Annotate important time points
- Use shaded regions for different phases

### Scatter Plots

**Best For**:
- Relationships between two variables
- Correlations
- Distributions
- Outliers

**Presentation Optimization**:
```
✅ DO:
- Large, distinct markers (8-12pt)
- Color code groups clearly
- Show trendline if discussing correlation
- Annotate key points (outliers, examples)
- Report R² or p-value directly on plot

❌ DON'T:
- Overplot (too many overlapping points)
- Small markers
- Multiple marker types that look similar
- Missing scale information
```

**Overplotting Solutions**:
- Transparency (alpha) for overlapping points
- Hexbin or density plots for very large datasets
- Random jitter for discrete data
- Marginal distributions on axes

### Box Plots / Violin Plots

**Best For**:
- Distribution comparisons
- Showing variability and outliers
- Multiple group comparisons

**Presentation Optimization**:
```
✅ DO:
- Large, clear boxes
- Color code groups
- Add individual data points if n is small (< 30)
- Annotate median or mean values
- Explain components (quartiles, whiskers) first time shown

❌ DON'T:
- Assume audience knows box plot conventions
- Use without brief explanation
- Too many groups (max 6-8)
- Omit axis labels and units
```

**First Use**:
If your audience may be unfamiliar, briefly explain: "Box shows middle 50% of data, line is median, whiskers follow the plotted convention (commonly the most extreme values within 1.5 IQR; outliers are separate)"

### Heatmaps

**Best For**:
- Matrix data
- Gene expression or correlation patterns
- Large d

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

