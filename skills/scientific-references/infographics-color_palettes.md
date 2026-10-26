---
id: sciref-infographics-color-palettes
name: "Scientific Ref: Infographic Color Palettes Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (infographics): Infographic Color Palettes Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "infographics color palettes"
  - "infographic color palettes reference"
keywords:
  - "infographics"
  - "color"
  - "palettes"
  - "specialized"
  - "scientific"
  - "reference"
  - "infographic"
---

# Infographic Color Palettes Reference

This reference provides comprehensive color palette options for creating accessible, professional infographics.

---

## Colorblind-Safe Palettes

These palettes are designed to be distinguishable by people with various forms of color vision deficiency.

### Okabe-Ito / Wong Palette (7 Chromatic Colors Plus Black)

The [Okabe-Ito palette](https://jfly.uni-koeln.de/color/), popularized by [Bang Wong](https://doi.org/10.1038/nmeth.1618), provides seven chromatic colors and black. It does not guarantee contrast between every pair.

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Black | `#000000` | 0, 0, 0 | Text, outlines |
| Orange | `#E69F00` | 230, 159, 0 | Primary accent |
| Sky Blue | `#56B4E9` | 86, 180, 233 | Primary data |
| Bluish Green | `#009E73` | 0, 158, 115 | Secondary data |
| Yellow | `#F0E442` | 240, 228, 66 | Highlight |
| Blue | `#0072B2` | 0, 114, 178 | Primary category |
| Vermillion | `#D55E00` | 213, 94, 0 | Alert, emphasis |
| Reddish Purple | `#CC79A7` | 204, 121, 167 | Tertiary data |

**Prompt usage:**
```
"Use Wong's colorblind-safe palette: orange (#E69F00), sky blue (#56B4E9), 
bluish green (#009E73), and blue (#0072B2) for data categories"
```

---

### Legacy IBM Preset (5 Data Colors Plus Optional Neutrals)

The `ibm` CLI preset retains the five historical data colors below. Black, white, and gray are supporting neutrals, not additional categorical colors. Treat this as a legacy preset rather than a current IBM design-system specification.

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Ultramarine | `#648FFF` | 100, 143, 255 | Primary blue |
| Indigo | `#785EF0` | 120, 94, 240 | Secondary |
| Magenta | `#DC267F` | 220, 38, 127 | Accent/Alert |
| Orange | `#FE6100` | 254, 97, 0 | Warning/Highlight |
| Gold | `#FFB000` | 255, 176, 0 | Positive/Success |
| Black | `#000000` | 0, 0, 0 | Text |
| White | `#FFFFFF` | 255, 255, 255 | Background |
| Gray | `#808080` | 128, 128, 128 | Neutral |

**Prompt usage:**
```
"Use IBM colorblind-safe colors: ultramarine (#648FFF), indigo (#785EF0),
magenta (#DC267F), and gold (#FFB000) for visual elements"
```

---

### Okabe-Ito Palette (8 Colors)

Developed by Masataka Okabe and Kei Ito, widely used in scientific publications.

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Black | `#000000` | 0, 0, 0 | Text, primary |
| Orange | `#E69F00` | 230, 159, 0 | Category 1 |
| Sky Blue | `#56B4E9` | 86, 180, 233 | Category 2 |
| Bluish Green | `#009E73` | 0, 158, 115 | Category 3 |
| Yellow | `#F0E442` | 240, 228, 66 | Category 4 |
| Blue | `#0072B2` | 0, 114, 178 | Category 5 |
| Vermillion | `#D55E00` | 213, 94, 0 | Category 6 |
| Reddish Purple | `#CC79A7` | 204, 121, 167 | Category 7 |

**Note:** Identical to Wong's palette - both are industry standards.

---

### Tol's Muted Qualitative Palette (9 Colors)

[Paul Tol's muted scheme](https://sronpersonalpages.nl/~pault/#fig:scheme_muted) contains nine categorical colors; pale gray is reserved for missing data. Gray and black are not extra categories in this scheme.

| Name | Hex | RGB |
|------|-----|-----|
| Indigo | `#332288` | 51, 34, 136 |
| Cyan | `#88CCEE` | 136, 204, 238 |
| Teal | `#44AA99` | 68, 170, 153 |
| Green | `#117733` | 17, 119, 51 |
| Olive | `#999933` | 153, 153, 51 |
| Sand | `#DDCC77` | 221, 204, 119 |
| Rose | `#CC6677` | 204, 102, 119 |
| Wine | `#882255` | 136, 34, 85 |
| Purple | `#AA4499` | 170, 68, 153 |
| Pale Gray (missing data only) | `#DDDDDD` | 221, 221, 221 |

---

## Industry-Specific Palettes

### Corporate/Business

Classic, professional appearance suitable for business reports and presentations.

| Role | Name | Hex | RGB |
|------|------|-----|-----|
| Primary | Navy | `#1E3A5F` | 30, 58, 95 |
| Secondary | Steel Blue | `#4A90A4` | 74, 144, 164 |
| Tertiary | Light Blue | `#A8D5E2` | 168, 213, 226 |
| Accent | Gold | `#F5A623` | 245, 166, 35 |
| Background | Light Gray | `#F5F5F5` | 245, 245, 245 |
| Text | Charcoal | `#333333` | 51, 51, 51 |

**Prompt usage:**
```
"Corporate business color scheme: navy blue (#1E3A5F) primary, 
steel blue (#4A90A4) secondary, gold (#F5A623) accent, 
light gray background, professional clean design"
```

---

### Healthcare/Medical

Trust-inducing, clinical colors appropriate for health-related content.

| Role | Name | Hex | RGB |
|------|------|-----|-----|
| Primary | Medical Blue | `#0077B6` | 0, 119, 182 |
| Secondary | Cyan | `#00B4D8` | 0, 180, 216 |
| Tertiary | Light Cyan | `#90E0EF` | 144, 224, 239 |
| Accent | Coral | `#FF6B6B` | 255, 107, 107 |
| Background | White | `#FFFFFF` | 255, 255, 255 |
| Text | Dark Blue | `#023E8A` | 2, 62, 138 |

**Prompt usage:**
```
"Healthcare medical color scheme: medical blue (#0077B6), 
cyan (#00B4D8) accents, coral (#FF6B6B) for emphasis, 
clean clinical white background, professional medical design"
```

---

### Technology/Data

Modern, tech-forward appearance, works well with dark mode.

| Role | Name | Hex | RGB |
|------|------|-----|-----|
| Primary Dark | Deep Navy | `#1A1A2E` | 26, 26, 46 |
| Secondary | Navy | `#16213E` | 22, 33, 62 |
| Tertiary | Blue | `#0F3460` | 15, 52, 96 |
| Accent | Electric Blue | `#00D9FF` | 0, 217, 255 |
| Accent 2 | Neon Purple | `#7B2CBF` | 123, 44, 191 |
| Text | White | `#FFFFFF` | 255, 255, 255 |

**Light Mode Alternative:**

| Role | Name | Hex | RGB |
|------|------|-----|-----|
| Primary | Tech Blue | `#2563EB` | 37, 99, 235 |
| Secondary | Slate | `#475569` | 71, 85, 105 |
| Accent | Violet | `#7C3AED` | 124, 58, 237 |
| Background | Light Gray | `#F8FAFC` | 248, 250, 252 |

**Prompt usage:**
```
"Technology data visualization colors: deep navy (#1A1A2E) background,
electric blue (#00D9FF) and neon purple (#7B2CBF) accents,
modern tech aesthetic, futuristic design"
```

---

### Nature/Environmental

Earth tones and greens for sustainability and environmental topics.

| Role | Name | Hex | RGB |
|------|------|-----|-----|
| Primary | Forest | `#2D6A4F` | 45, 106, 79 |
| Secondary | Green | `#40916C` | 64, 145, 108 |
| Tertiary | Mint | `#95D5B2` | 149, 213, 178 |
| Accent | Earth Brown | `#8B4513` | 139, 69, 19 |
| Background | Cream | `#FAF3E0` | 250, 243, 224 |
| Text | Dark Green | `#1B4332` | 27, 67, 50 |

**Prompt usage:**
```
"Environmental nature color scheme: forest green (#2D6A4F),
mint (#95D5B2), earth brown (#8B4513) accents,
cream background, organic natural design feel"
```

---

### Education/Academic

Friendly yet

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

