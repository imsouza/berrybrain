---
id: sci-infographics
name: "Scientific: infographics"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Creates and reviews infographics with Nano Banana 2 via OpenRouter. Use for statistical summaries, timelines, comparisons, processes, and visual explanations with supplied data or optional Sonar research. Supports ten layouts, eight style presets, reference images, and accessible"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "infographics"
keywords:
  - "infographics"
  - "creates"
  - "reviews"
  - "nano"
  - "banana"
  - "openrouter"
---

# Infographics

## Overview

Infographics are visual representations of information, data, or knowledge designed to present complex content quickly and clearly. **This skill uses Nano Banana 2 AI for infographic generation with Gemini 3.7 Flash quality review and Perplexity Sonar for research.**

**How it works:**
- (Optional) **Research phase**: Gather candidate facts and source records using Perplexity Sonar Pro
- Describe your infographic in natural language
- Nano Banana 2 generates raster drafts from your content
- **Gemini 3.7 Flash reviews quality** against document-type thresholds
- **Smart iteration**: Regenerates when review requests improvements, within the iteration budget
- Inspect every final image at its intended display size and check claims against sources

**Quality Thresholds by Document Type:**
| Document Type | Threshold | Description |
|---------------|-----------|-------------|
| marketing | 8.5/10 | Marketing materials - must be compelling |
| report | 8.0/10 | Business reports - professional quality |
| presentation | 7.5/10 | Slides, talks - clear and engaging |
| social | 7.0/10 | Social media content |
| internal | 7.0/10 | Internal use |
| draft | 6.5/10 | Working drafts |
| default | 7.5/10 | General purpose |

**Simply describe what you want, and Nano Banana 2 creates it.**

## Quick Start

Install the only runtime dependency in your chosen Python environment (`python -m pip install requests`),
then set `OPENROUTER_API_KEY`. Examples below illustrate CLI usage; paid generation was not
executed during this review. Scripts accept PNG output paths only.

Generate a draft by describing it:

```bash
# Generate a list infographic (default threshold 7.5/10)
python skills/infographics/scripts/generate_infographic.py \
  "5 benefits of regular exercise" \
  -o figures/exercise_benefits.png --type list

# Generate for marketing (highest threshold: 8.5/10)
python skills/infographics/scripts/generate_infographic.py \
  "Product features comparison" \
  -o figures/product_comparison.png --type comparison --doc-type marketing

# Generate with corporate style
python skills/infographics/scripts/generate_infographic.py \
  "Company milestones 2010-2025" \
  -o figures/timeline.png --type timeline --style corporate

# Generate with colorblind-safe palette
python skills/infographics/scripts/generate_infographic.py \
  "Heart disease statistics worldwide" \
  -o figures/health_stats.png --type statistical --palette wong

# Generate WITH RESEARCH for accurate, up-to-date data
python skills/infographics/scripts/generate_infographic.py \
  "Global AI market size and growth projections" \
  -o figures/ai_market.png --type statistical --research
```

**What happens behind the scenes:**
1. **(Optional) Research**: Perplexity Sonar Pro gathers candidate facts with source annotations
2. **Generation 1**: Nano Banana 2 creates initial infographic following design best practices
3. **Review 1**: **Gemini 3.7 Flash** evaluates quality against document-type threshold
4. **Decision**: Stop when the scored review meets threshold and requests no further changes
5. **If improvements are requested**: Retain content and source context, refine the prompt, regenerate
6. **Repeat**: Until quality meets threshold or the iteration budget is reached; stop on API failure and keep the latest saved draft

**Smart Iteration Benefits:**
- ✅ Saves API calls if first generation is good enough
- ✅ Higher quality standards for marketing materials
- ✅ Faster turnaround for drafts/internal use
- ✅ Appropriate quality for each use case

**Output**: Versioned PNGs plus a review log with models, scores, `quality_met`, and `termination_reason`. A saved image (`success: true`) can still be unreviewed or below threshold. Human factual and visual checks remain required.

## When to Use This Skill

Use the **infographics** skill when:
- Presenting data or statistics in a visual format
- Creating timeline visualizations for project milestones or history
- Explaining processes, workflows, or step-by-step guides
- Comparing options, products, or concepts side-by-side
- Summarizing key points in an engaging visual format
- Creating geographic or map-based data visualizations
- Building hierarchical or organizational charts
- Designing social media content or marketing materials

**Use scientific-schematics instead for:**
- Technical flowcharts and circuit diagrams
- Biological pathways and molecular diagrams
- Neural network architecture diagrams
- CONSORT/PRISMA methodology diagrams

---

## Research Integration

### Automatic Data Gathering (`--research`)

When creating infographics that require accurate, up-to-date data, use the `--research` flag to gather candidate facts and statistics using **Perplexity Sonar Pro**. The script preserves source annotations; it does not independently verify claims or source relevance. For scientific or medical publication, verify primary sources before including the resulting numbers.

```bash
# Research and generate statistical infographic
python skills/infographics/scripts/generate_infographic.py \
  "Global renewable energy adoption rates by country" \
  -o figures/renewable_energy.png --type statistical --research

# Research for timeline infographic
python skills/infographics/scripts/generate_infographic.py \
  "History of artificial intelligence breakthroughs" \
  -o figures/ai_history.png --type timeline --research

# Research for comparison infographic
python skills/infographics/scripts/generate_infographic.py \
  "Electric vehicles vs hydrogen vehicles comparison" \
  -o figures/ev_hydrogen.png --type comparison --research
```

### What Research Provides

The research phase automatically:

1. **Gathers Key Facts**: 5-8 relevant facts and statistics about the topic
2. **Provides Context**: Background information for accurate representation
3. **Requests Data Points**: Numbers with units, populations, denominators, and dates
4. **Preserves Sources**: OpenRouter URL-citation annotations, plus optional provider citation fields
5. **Dates the Request**: Uses the current date while preserving historical event dates

### When to Use Research

**Enable research (`--research`) for:**
- Statistical infographics requiring accurate numbers
- Market data, industry statistics, or trends
- Scientific or medical information
- Current events or recent developments
- Any topic where accuracy is critical

**Skip research for:**
- Simple conceptual infographics
- Internal process documen

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

