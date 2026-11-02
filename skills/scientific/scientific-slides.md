---
id: sci-scientific-slides
name: "Scientific: scientific-slides"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Builds slide decks and presentations for research talks. Used for making PowerPoint slides, conference presentations, seminar talks, research presentations, thesis defense slides, or any scientific talk. Provides slide structure, design templates, timing guidance, and visual vali"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "scientific slides"
  - "cientifico slides"
  - "scientific-slides"
keywords:
  - "scientific"
  - "slides"
  - "cientifico"
  - "builds"
  - "slide"
  - "decks"
  - "presentations"
  - "research"
  - "talks"
---

# Scientific Slides

## Overview

Scientific presentations are a critical medium for communicating research, sharing findings, and engaging with academic and professional audiences. This skill provides comprehensive guidance for creating effective scientific presentations, from structure and content development to visual design and delivery preparation.

**Key Focus**: Oral presentations for conferences, seminars, defenses, and professional talks.

**CRITICAL DESIGN PHILOSOPHY**: Scientific presentations should be VISUALLY ENGAGING and RESEARCH-BACKED. Avoid dry, text-heavy slides at all costs. Great scientific presentations combine:
- **Compelling visuals**: High-quality figures, images, diagrams (not just bullet points)
- **Research context**: Proper citations from research-lookup establishing credibility
- **Minimal text**: Bullet points as prompts, YOU provide the explanation verbally
- **Professional design**: Modern color schemes, strong visual hierarchy, generous white space
- **Story-driven**: Clear narrative arc, not just data dumps

**Remember**: Boring presentations = forgotten science. Make your slides visually memorable while maintaining scientific rigor through proper citations.

## When to Use This Skill

This skill should be used when:
- Preparing conference presentations (5-20 minutes)
- Developing academic seminars (45-60 minutes)
- Creating thesis or dissertation defense presentations
- Designing grant pitch presentations
- Preparing journal club presentations
- Giving research talks at institutions or companies
- Teaching or tutorial presentations on scientific topics

## Slide Generation with Nano Banana 2

The bundled image helper uses `google/gemini-3.1-flash-image` (Nano Banana 2),
with `google/gemini-3.7-flash` for visual review. API contracts, setup, and limitations
are in [references/script_reference.md](references/script_reference.md). Generated
images are drafts: verify every claim, label, citation, and scientific relationship.

There are two workflows depending on output format:

### Image Workflow: PDF Slides

Generate conceptual or overview slides as complete images, then combine them into a PDF. Use editable PowerPoint or Beamer for quantitative results, exact equations, accessible text, or a user-supplied template.

**How it works:**
1. **Plan the deck**: Create a detailed plan for each slide (title, key points, visual elements)
2. **Generate slides**: Call Nano Banana 2 for each slide to create complete slide images
3. **Combine to PDF**: Assemble slide images into a single PDF presentation

**Step 1: Plan Each Slide**

Before generating, create a detailed plan for your presentation:

```markdown
# Presentation Plan: Introduction to Machine Learning

## Slide 1: Title Slide
- Title: "Machine Learning: From Theory to Practice"
- Subtitle: "AI Conference 2025"
- Speaker: Dr. Jane Smith, University of XYZ
- Visual: Modern abstract neural network background

## Slide 2: Introduction
- Title: "Why Machine Learning Matters"
- Key points: Industry adoption, breakthrough applications, future potential
- Visual: Icons showing different ML applications (healthcare, finance, robotics)

## Slide 3: Core Concepts
- Title: "The Three Types of Learning"
- Content: Supervised, Unsupervised, Reinforcement
- Visual: Three-part diagram showing each type with examples

... (continue for all slides)
```

**Step 2: Generate Each Slide**

Use the `generate_slide_image.py` script to create each slide.

**CRITICAL: Formatting Consistency Protocol**

To ensure unified formatting across all slides in a presentation:

1. **Define a Formatting Goal** at the start of your presentation and include it in EVERY prompt:
   - Color scheme (e.g., "dark blue background, white text, gold accents")
   - Typography style (e.g., "bold sans-serif titles, clean body text")
   - Visual style (e.g., "minimal, professional, corporate aesthetic")
   - Layout approach (e.g., "generous white space, left-aligned content")

2. **Always attach the previous slide** when generating subsequent slides using `--attach`:
   - This allows Nano Banana 2 to see and match the existing style
   - Creates visual continuity throughout the deck
   - Ensures consistent colors, fonts, and design language

3. **Use the supplied presenter name and affiliation**; omit them if unknown.

4. **Include citations directly in the prompt** for slides that reference research:
   - Add citations in the prompt text so they appear on the generated slide
   - Use format: "Include citation: (Author et al., Year)" or "Show reference: Author et al., Year"
   - For multiple citations, list them all in the prompt
   - Citations should appear in small text at the bottom of the slide or near relevant content

5. **Preserve scientific figures as original assets**:
   - Locate the user's figures and underlying data before composing results slides.
   - Embed the original chart unchanged in PowerPoint/Beamer, or regenerate it deterministically from the source data.
   - `--attach` guides the image model; it can redraw points, axes, labels, and logos. It does not paste the original pixels or guarantee quantitative fidelity.
   - Use attachments for style or conceptual layout drafts. For final results, add the original figure and verified text with a deterministic layout tool.

**Example with formatting consistency, citations, and figure attachments:**

```bash
# Title slide (first slide - establishes the style)
python scripts/generate_slide_image.py "Title slide for presentation: 'Machine Learning: From Theory to Practice'. Subtitle: '[Conference name and date]'. Speaker: '[Supplied presenter name]'. FORMATTING GOAL: Dark blue background (#1a237e), white text, gold accents (#ffc107), minimal design, sans-serif fonts, generous margins, no decorative elements." -o slides/01_title.png

# Content slide with citations (attach previous slide for consistency)
python scripts/generate_slide_image.py "Presentation slide titled 'Why Machine Learning Matters'. Three key points with simple icons: 1) Industry adoption, 2) Breakthrough applications, 3) Future potential. CITATIONS: Include at bottom in small text: (LeCun et al., 2015; Goodfellow et al., 2016). FORMATTING GOAL: Match attached slide style - dark blue background, white text, gold accents, minimal professional design, no visual clutter." -o slides/02_intro.png --attach slides/01_title.png

# Background slide with multiple citations
python scripts/generate_slide_image.py "Presentation slid

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

