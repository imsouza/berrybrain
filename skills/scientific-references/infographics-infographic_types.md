---
id: sciref-infographics-infographic-types
name: "Scientific Ref: Infographic Types Reference Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (infographics): Infographic Types Reference Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "infographics infographic types"
  - "infographic types reference guide"
keywords:
  - "infographics"
  - "infographic"
  - "types"
  - "specialized"
  - "scientific"
  - "reference"
---

# Infographic Types Reference Guide

This reference provides extended templates, examples, and prompt patterns for each infographic type.
All example commands are illustrative and were not sent to paid generation APIs during review.
Numerical samples are layout inputs, not verified current facts: replace them with sourced
values, units, denominators, geography, and dates before producing a factual infographic.
For exact plots or maps, render with plotting/GIS tools and use the result as reference.

---

## 1. Statistical/Data-Driven Infographics

### Purpose
Present quantitative data, statistics, survey results, and numerical comparisons in an engaging visual format.

### Visual Elements
- **Bar charts**: Horizontal or vertical for comparisons
- **Pie/donut charts**: For proportions and percentages
- **Line charts**: For trends over time
- **Large number callouts**: Highlight key statistics
- **Icons**: Represent categories visually
- **Progress bars**: Show percentages or completion

### Layout Patterns
- **Single-stat hero**: One large number with supporting context
- **Multi-stat grid**: 3-6 statistics in a grid layout
- **Chart-centric**: Large visualization with supporting text
- **Comparison bars**: Side-by-side bar comparisons

### Prompt Templates

**Single Statistic Hero:**
```
Statistical infographic featuring one key statistic about [TOPIC]:
Main stat: [LARGE NUMBER] [UNIT/CONTEXT]
Supporting context: [2-3 sentences explaining the significance]
Large bold number in center, supporting text below,
relevant icon or illustration, [COLOR] accent color,
clean minimal design, white background.
```

**Multi-Statistic Grid:**
```
Statistical infographic presenting [TOPIC] data:
Stat 1: [NUMBER] [LABEL] (icon: [ICON])
Stat 2: [NUMBER] [LABEL] (icon: [ICON])
Stat 3: [NUMBER] [LABEL] (icon: [ICON])
Stat 4: [NUMBER] [LABEL] (icon: [ICON])
2x2 grid layout, large bold numbers, small icons above each,
[COLOR SCHEME], modern clean typography, white background.
```

**Chart-Focused:**
```
Statistical infographic with [CHART TYPE] showing [TOPIC]:
Data points: [VALUE 1], [VALUE 2], [VALUE 3], [VALUE 4]
Labels: [LABEL 1], [LABEL 2], [LABEL 3], [LABEL 4]
Large [bar/pie/donut] chart as main element,
title at top, legend below chart, [COLOR SCHEME],
data labels on chart, clean professional design.
```

### Example Prompts

**Synthetic Clinic Operations (layout example):**
```bash
python skills/infographics/scripts/generate_infographic.py \
  "Illustrative clinic operations, synthetic data: 100 scheduled visits; \
   80 completed, 15 rescheduled, 5 canceled. Show counts and percentages, \
   label denominator 100 scheduled visits, label data synthetic, \
   blue and gray medical design, white background" \
  --output figures/clinic_operations.png --type statistical
```

**Business Metrics:**
```bash
python skills/infographics/scripts/generate_infographic.py \
  "Statistical infographic for Q4 business results: \
   Revenue: USD 2.4M (+15% YoY), Customers: 12,500 (+22%), \
   NPS Score: 78 (+8 points), Retention: 94%. \
   4-stat grid with upward arrow indicators for growth, \
   bar chart showing quarterly trend, \
   navy blue and gold corporate color scheme, \
   professional business design, white background" \
  --output figures/q4_metrics.png --type statistical
```

---

## 2. Timeline Infographics

### Purpose
Display events, milestones, or developments in chronological order.

### Visual Elements
- **Timeline axis**: Horizontal or vertical line
- **Date markers**: Years, months, or specific dates
- **Event nodes**: Circles, icons, or images at each point
- **Description boxes**: Brief text for each event
- **Connecting elements**: Lines, arrows, or paths

### Layout Patterns
- **Horizontal timeline**: Left-to-right progression
- **Vertical timeline**: Top-to-bottom progression
- **Winding/snake timeline**: S-curve for many events
- **Circular timeline**: For cyclical or repeating events

### Prompt Templates

**Horizontal Timeline:**
```
Horizontal timeline infographic showing [TOPIC] from [START YEAR] to [END YEAR]:
[YEAR 1]: [EVENT 1] - [brief description]
[YEAR 2]: [EVENT 2] - [brief description]
[YEAR 3]: [EVENT 3] - [brief description]
[YEAR 4]: [EVENT 4] - [brief description]
Left-to-right timeline with circular nodes for each event,
connecting line between nodes, icons above each node,
[COLOR] gradient from past to present, date labels below,
clean modern design, white background.
```

**Vertical Timeline:**
```
Vertical timeline infographic showing [TOPIC]:
Top (earliest): [YEAR] - [EVENT]
Middle events: [YEAR] - [EVENT], [YEAR] - [EVENT]
Bottom (latest): [YEAR] - [EVENT]
Top-to-bottom flow, alternating left-right event boxes,
central vertical line connecting all events,
circular nodes with dates, [COLOR SCHEME],
professional clean design, white background.
```

**Project Milestone Timeline:**
```
Project timeline infographic for [PROJECT NAME]:
Phase 1: [DATES] - [MILESTONE] (status: complete)
Phase 2: [DATES] - [MILESTONE] (status: in progress)
Phase 3: [DATES] - [MILESTONE] (status: upcoming)
Phase 4: [DATES] - [MILESTONE] (status: planned)
Gantt-style horizontal bars, color-coded by status,
green for complete, yellow for in progress, gray for upcoming,
project name header, clean professional design.
```

### Example Prompts

**Technology Evolution:**
```bash
python skills/infographics/scripts/generate_infographic.py \
  "Horizontal timeline infographic: Evolution of Mobile Phones \
   1983: First mobile phone (Motorola DynaTAC), \
   1992: First smartphone (IBM Simon), \
   2007: iPhone launches touchscreen era, \
   2010: First 4G networks, \
   2019: First 5G phones, \
   2023: Foldable phones mainstream. \
   Phone icons evolving at each node, gradient from gray (old) to blue (new), \
   connecting timeline arrow, year labels, clean tech design" \
  --output figures/mobile_evolution.png --type timeline
```

**Company History:**
```bash
python skills/infographics/scripts/generate_infographic.py \
  "Vertical timeline infographic: Our Company Journey \
   2010: Founded in garage with 2 employees, \
   2012: First major client signed, \
   2015: Reached 100 employees, \
   2018: IPO on NASDAQ, \
   2022: Expanded to 30 countries, \
   2025: 10,000 employees worldwide. \
   Milestone icons for each event, alternating left-right layout, \
   blue and gold corporate colors, growth trajectory feel, \
   professional business design" \
  --output figures/company_history.png --

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

