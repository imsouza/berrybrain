---
id: sciref-venue-templates-posters-guidelines
name: "Scientific Ref: Research Poster Guidelines"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (venue-templates): Research Poster Guidelines"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "venue templates posters guidelines"
  - "research poster guidelines"
keywords:
  - "venue"
  - "templates"
  - "posters"
  - "guidelines"
  - "specialized"
  - "scientific"
  - "reference"
  - "research"
---

# Research Poster Guidelines

Comprehensive guidelines for creating effective academic research posters including sizing, layout, typography, and design best practices.

**Reviewed**: 2026-10-01

Poster dimensions and upload rules are event-specific. Confirm the current presenter instructions before choosing a size, orientation, or file format. Numerical layout, typography, and content proportions below are adjustable design heuristics, not venue mandates or accessibility certification. Check readability at the actual printed size.

Primary package sources: https://ctan.org/pkg/beamerposter , https://ctan.org/pkg/tikzposter , https://ctan.org/pkg/qrcode . The beamerposter custom width/height options use centimetres. The beamerposter and tikzposter preambles below were compiled in the review environment; no tikzposter template is bundled. The baposter preamble received a bounded compatibility check with an archival 2011 class supplied separately in the test workspace; current upstream availability was not verified. No baposter class is bundled.

---

## Standard Poster Sizes

### International Sizes (ISO 216)

| Size | Dimensions (mm) | Dimensions (inches) | Common Use |
|------|----------------|---------------------|------------|
| **A0** | 841 × 1189 | 33.1 × 46.8 | ISO paper size; event may specify another |
| **A1** | 594 × 841 | 23.4 × 33.1 | Smaller conferences, travel-friendly |
| **A2** | 420 × 594 | 16.5 × 23.4 | Mini posters, small venues |

### US Sizes

| Size | Dimensions (inches) | Dimensions (mm) | Common Use |
|------|-------------------|-----------------|------------|
| **36" × 48"** | 36 × 48 | 914 × 1219 | Common US conference size (portrait) |
| **42" × 56"** | 42 × 56 | 1067 × 1422 | Large format US posters |
| **48" × 36"** | 48 × 36 | 1219 × 914 | Landscape orientation |
| **48" × 96"** | 48 × 96 | 1219 × 2438 | Extra-wide format |

### Other Common Sizes

| Size | Dimensions | Notes |
|------|-----------|-------|
| **90 cm × 120 cm** | 900 × 1200 mm / 35.4 × 47.2 in | Common in Europe |
| **40" × 30"** | 1016 × 762 mm | Landscape format |
| **3 ft × 4 ft** | 914 × 1219 mm / 36 × 48 in | Same as 36×48 |

### Orientation

- **Portrait**: height > width
  - Better for long visual flows (top to bottom)
  - Examples: A0, 36"×48"
- **Landscape**: width > height
  - Better for wide content, timelines
  - Examples: 48"×36", 40"×30"

**Always verify**: Check conference specifications before designing!

---

## Typography and Font Sizes

### Recommended Font Sizes by Distance

Posters are viewed from 3-6 feet (1-2 meters) away:

| Element | Size Range | Recommended |
|---------|-----------|-------------|
| **Title** | 60-85 pt | 72-85 pt |
| **Author Names** | 48-60 pt | 54 pt |
| **Affiliations** | 32-40 pt | 36 pt |
| **Section Headers** | 36-48 pt | 42 pt |
| **Body Text** | 24-32 pt | 28 pt |
| **Figure Captions** | 20-24 pt | 22 pt |
| **References** | 18-22 pt | 20 pt |

### Font Families

**Sans-Serif (Recommended for Posters)**:
- Arial
- Helvetica
- Calibri
- Futura
- Gill Sans
- **Why**: Clean, readable at distance

**Serif (Use Sparingly)**:
- Times New Roman
- Georgia
- Palatino
- **When**: Body text if preferred, but sans-serif better for headers

**Monospace**:
- Courier New
- Consolas
- **When**: Code snippets only

### Typography Best Practices

1. **Limit fonts**: Use 1-2 font families maximum
2. **Hierarchy**: Establish clear size hierarchy
3. **Weight**: Use bold for emphasis, not italics
4. **Alignment**: Left-align body text, center title
5. **Spacing**: Generous line spacing (1.2-1.5)
6. **Consistency**: Same fonts for similar elements

---

## Layout and Design Principles

### Grid-Based Layouts

**Column Structures**:

| Layout | Columns | Best For |
|--------|---------|----------|
| **Single Column** | 1 | Simple, linear flow; timeline posters |
| **Two Column** | 2 | Most common; balanced layout |
| **Three Column** | 3 | Dense content; multi-part studies |
| **Four Column** | 4 | Very dense; avoid if possible |

**Recommended**: **2 or 3 columns** for most research posters

### Visual Flow

**Reading Order** (Western conventions):
1. Top to bottom
2. Left to right
3. Z-pattern or F-pattern

**Section Ordering** (typical):
```
+----------------------------------+
|            TITLE                 |
|     Authors, Affiliations        |
+----------------------------------+
| Introduction | Results           |
|              |                   |
| Methods      | Discussion        |
|              |                   |
| [Optional]   | Conclusions       |
+----------------------------------+
|         References / QR Code     |
+----------------------------------+
```

### Spacing and Margins

- **Outer margins**: 1-2 inches (2.5-5 cm) all sides
- **Column spacing**: 0.5-1 inch (1.3-2.5 cm)
- **Inter-section spacing**: 0.5-1 inch
- **White space**: 30-40% of poster should be white space

**Avoid**: Dense, text-heavy layouts with minimal white space

---

## Color Schemes

### Colorblind-Safe Palettes

Use colorblind-friendly color combinations:

**Okabe-Ito Palette** (Recommended):
- Orange: `#E69F00`
- Sky Blue: `#56B4E9`
- Bluish Green: `#009E73`
- Yellow: `#F0E442`
- Blue: `#0072B2`
- Vermillion: `#D55E00`
- Reddish Purple: `#CC79A7`
- Black: `#000000`
- Gray: `#999999`

**Viridis Palette** (sequential):
- Good for heatmaps and gradients
- Colorblind-safe and perceptually uniform

### Color Usage Guidelines

**Background**:
- **White or light gray**: Most common, professional
- **Light colored**: Pale blue, beige (use cautiously)
- **Avoid dark backgrounds**: Harder to read, expensive to print

**Text**:
- **Dark on light**: Black or dark gray text on white/light backgrounds
- **Contrast ratio**: Use the WCAG text-contrast criterion as a design aid: 4.5:1 for ordinary text, 3:1 for large text; it is a web-content criterion, not proof of printed-poster accessibility

**Accent Colors**:
- Use 2-3 accent colors maximum
- Section headers, key findings
- Consistent throughout poster

**Figures**:
- Colorblind-safe palettes
- Sufficient contrast
- Test in grayscale

### Color Contrast Tools
- WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- Coblis (Color Blindness Simulator): https://www.color-blindness.com/coblis-color-blindness-simulator/

---

## Content Structure

### Essential Sections

#### 1. Title Section
- **Title**: Clear, specific, engaging
- **Authors**: Names (underline presenting author)
- **Affiliations**:

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

