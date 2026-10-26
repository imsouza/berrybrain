---
id: sciref-latex-posters-poster-design-principles
name: "Scientific Ref: Research Poster Design Principles"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (latex-posters): Research Poster Design Principles"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "latex posters poster design principles"
  - "research poster design principles"
keywords:
  - "latex"
  - "posters"
  - "poster"
  - "design"
  - "principles"
  - "specialized"
  - "scientific"
  - "reference"
  - "research"
---

# Research Poster Design Principles

Reviewed 2026-09-30. Design numbers are starting points, not measured guarantees.
Code fragments are illustrative; use the bundled tested templates as the executable
starting point. Replace example names, statistics, citations, URLs, and assets with
verified project content.

## Overview

Effective poster design balances visual appeal, readability, and scientific content. This guide covers typography, color theory, visual hierarchy, accessibility, and practical design starting points for research posters.

## Core Design Principles

### 1. Visual Hierarchy

Guide viewers through content in logical order using size, color, position, and contrast.

**Hierarchy Levels**:

1. **Primary (Title)**: Largest, most prominent
   - Size: 72-120pt
   - Position: Top center or top spanning
   - Weight: Bold
   - Purpose: Capture attention from 20+ feet

2. **Secondary (Section Headers)**: Organize content
   - Size: 48-72pt
   - Weight: Bold or semi-bold
   - Purpose: Section navigation, readable from 10 feet

3. **Tertiary (Body Text)**: Main content
   - Size: 24-36pt minimum
   - Weight: Regular
   - Purpose: Detailed information, readable from 4-6 feet

4. **Quaternary (Captions, References)**: Supporting info
   - Size: 18-24pt
   - Weight: Regular or light
   - Purpose: Context and attribution

**Implementation**:
```latex
% Illustrative Beamer font settings; sizes depend on class and poster scale.
\setbeamerfont{title}{size=\VeryHuge,series=\bfseries}
\setbeamerfont{block title}{size=\Huge,series=\bfseries}
\setbeamerfont{block body}{size=\LARGE}
\setbeamerfont{caption}{size=\large}
```

### 2. White Space (Negative Space)

Empty space is not wasted space—it enhances readability and guides attention.

**White Space Functions**:
- **Breathing room**: Prevents overwhelming viewers
- **Grouping**: Shows which elements belong together
- **Focus**: Draws attention to important elements
- **Flow**: Creates visual pathways through content

**Guidelines**:
- Keep a safe margin required by the printer, then choose padding for readability
- Consistent spacing between blocks (1-2cm)
- Space around figures equal to or greater than border width
- Group related items closely, separate unrelated items
- Don't fill every inch—aim for 40-60% text coverage

**LaTeX Implementation**:
```latex
% beamerposter spacing
\setbeamertemplate{block begin}{
  \vskip2ex  % Space before block
  ...
}

% tikzposter spacing
\documentclass[..., blockverticalspace=15mm, colspace=15mm]{tikzposter}

% Manual spacing
\vspace{2cm}  % Vertical space
\hspace{1cm}  % Horizontal space
```

### 3. Alignment and Grid Systems

Proper alignment creates professional, organized appearance.

**Alignment Types**:
- **Left-aligned text**: Most readable for body text (Western audiences)
- **Center-aligned**: Headers, titles, symmetric layouts
- **Right-aligned**: Rarely used, special cases only
- **Justified**: Avoid (creates uneven spacing)

**Grid Systems**:
- **2-column**: Simple, traditional, good for narrative flow
- **3-column**: Most common, balanced, versatile
- **4-column**: Complex, information-dense, requires careful design
- **Asymmetric**: Creative, modern, requires expertise

**Best Practices**:
- Align block edges to invisible grid lines
- Keep consistent column widths (unless intentionally asymmetric)
- Align similar elements (all figures, all text blocks)
- Use consistent margins throughout

### 4. Visual Flow and Reading Patterns

Design for natural eye movement and logical content progression.

**Common Reading Patterns**:

**Z-Pattern (Landscape posters)**:
```
Start → → → Top Right
  ↓
Middle Left → → Middle
  ↓
Bottom Left → → → End
```

**F-Pattern (Portrait posters)**:
```
Title → → → →
↓
Section 1 → →
↓
Section 2 → →
↓
Section 3 → →
↓
Conclusion → →
```

**Gutenberg Diagram**:
```
Primary Area     Strong Fallow
(top-left)       (top-right)
        ↓              ↓
Weak Fallow      Terminal Area
(bottom-left)    (bottom-right)
```

**Implementation Strategy**:
1. Place most important content in "hot zones" (top-left, center)
2. Create visual paths with arrows, lines, or color
3. Use numbering for sequential information (Methods steps)
4. Design left-to-right, top-to-bottom flow (Western audiences)
5. Position conclusions prominently (bottom-right is natural endpoint)

## Typography

### Font Selection

**Recommended Fonts**:

**Sans-Serif (Recommended for posters)**:
- **Helvetica**: Clean, professional, widely available
- **Arial**: Similar to Helvetica, universal compatibility
- **Calibri**: Modern, friendly, good readability
- **Open Sans**: Contemporary, excellent web and print
- **Roboto**: Modern, Google design, highly readable
- **Lato**: Warm, professional, works at all sizes

**Serif (Use sparingly)**:
- **Times New Roman**: Traditional, formal
- **Garamond**: Elegant, good for humanities
- **Georgia**: Designed for screens, readable

**Avoid**:
- ❌ Comic Sans (unprofessional)
- ❌ Decorative or script fonts (illegible from distance)
- ❌ Mixing more than 2-3 font families

**LaTeX Implementation**:
```latex
% Helvetica (sans-serif)
\usepackage{helvet}
\renewcommand{\familydefault}{\sfdefault}

% Avant Garde (not Arial)
\usepackage{avant}
\renewcommand{\familydefault}{\sfdefault}

% Modern fonts with fontspec (requires LuaLaTeX/XeLaTeX)
\usepackage{fontspec}
\setmainfont{Helvetica Neue}
\setsansfont{Open Sans}
```

### Font Sizing

**Absolute Minimum Sizes** (readable from 4-6 feet):
- Title: 72pt+ (85-120pt recommended)
- Section headers: 48-72pt
- Body text: 24-36pt (30pt+ recommended)
- Captions/small text: 18-24pt
- References: 16-20pt minimum

**Testing Readability**:
- Print at 25% scale
- Read from 2-3 feet distance
- If legible, full-scale poster will be readable from 8-12 feet

**Font commands are class-dependent.** `\Large`, `\Huge`, and related commands
change with the document class and poster scale; there is no universal point-size
conversion table. `\VeryHuge` is provided by beamerposter, not ordinary LaTeX.
For explicit control, use `\fontsize{30}{36}\selectfont` in the appropriate scope
and verify the rendered PDF at final size.

### Text Formatting Best Practices

**Use**:
- ✅ **Bold** for emphasis and headers
- ✅ Short paragraphs (3-5 lines maximum)
- ✅ Bullet points for lists
- ✅ Adequate line spacing (1.2-1.5)
- ✅ High contrast (dark text on light background)

**Avoid**:
- ❌ Italics from distance (hard to read)
- ❌ ALL CAPS FOR LONG TEXT (SLOW TO RE

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

