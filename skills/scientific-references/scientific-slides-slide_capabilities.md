---
id: sciref-scientific-slides-slide-capabilities
name: "Scientific Ref: Slide Capabilities"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-slides): Slide Capabilities"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific slides slide capabilities"
  - "cientifico slides slide capabilities"
  - "slide capabilities"
keywords:
  - "scientific"
  - "slides"
  - "slide"
  - "capabilities"
  - "cientifico"
  - "specialized"
  - "reference"
---

# Slide Capabilities

Presentation structure, design principles, data visualization for slides, talk-specific
guidance, implementation options, visual review and iteration, timing and pacing, and
validation and quality assurance.

## Core Capabilities

### 1. Presentation Structure and Organization

Build presentations with clear narrative flow and appropriate structure for different contexts. For detailed guidance, refer to `references/presentation_structure.md`.

**Universal Story Arc**:
1. **Hook**: Grab attention (30-60 seconds)
2. **Context**: Establish importance (5-10% of talk)
3. **Problem/Gap**: Identify what's unknown (5-10% of talk)
4. **Approach**: Explain your solution (15-25% of talk)
5. **Results**: Present key findings (40-50% of talk)
6. **Implications**: Discuss meaning (15-20% of talk)
7. **Closure**: Memorable conclusion (1-2 minutes)

**Talk-Specific Structures**:
- **Conference talks (15 min)**: Focused on 1-2 key findings, minimal methods
- **Academic seminars (45 min)**: Comprehensive coverage, detailed methods, multiple studies
- **Thesis defenses (60 min)**: Complete dissertation overview, all studies covered
- **Grant pitches (15 min)**: Emphasis on significance, feasibility, and impact
- **Journal clubs (30 min)**: Critical analysis of published work

### 2. Slide Design Principles

Create professional, readable, and accessible slides that enhance understanding. For complete design guidelines, refer to `references/slide_design_principles.md`.

**ANTI-PATTERN: Avoid Dry, Text-Heavy Presentations**

❌ **What Makes Presentations Dry and Forgettable:**
- Walls of text (more than 6 bullets per slide)
- Small fonts (<24pt body text)
- Black text on white background only (no visual interest)
- No images or graphics (bullet points only)
- Generic templates with no customization
- Dense, paragraph-like bullet points
- Missing research context (no citations)
- All slides look the same (repetitive)

✅ **What Makes Presentations Engaging and Memorable:**
- HIGH-QUALITY VISUALS dominate (figures, photos, diagrams, icons)
- Large, clear text as accent (not the main content)
- Modern, purposeful color schemes (not default themes)
- Generous white space (slides breathe)
- Research-backed context (proper citations from research-lookup)
- Variety in slide layouts (not all bullet lists)
- Story-driven flow with visual anchors
- Professional, polished appearance

**Core Design Principles**:

**Visual-First Approach** (CRITICAL):
- Start with visuals (figures, images, diagrams), add text as support
- Every slide should have STRONG visual element (figure, chart, photo, diagram)
- Text explains or complements visuals, not replaces them
- Think: "How can I show this, not just tell it?"
- Target: 60-70% visual content, 30-40% text

**Simplicity with Impact**:
- One main idea per slide
- MINIMAL text (3-4 bullets, 4-6 words each preferred)
- Generous white space (40-50% of slide)
- Clear visual focus
- Bold, confident design choices

**Typography for Engagement**:
- Sans-serif fonts (Arial, Calibri, Helvetica)
- LARGE fonts: 24-28pt for body text (not minimum 18pt)
- 36-44pt for slide titles (make bold)
- High contrast (minimum 4.5:1, prefer 7:1)
- Use size for hierarchy, not just weight

**Color for Impact**:
- MODERN color palettes (not default blue/gray)
- Consider your topic: biotech? vibrant colors. Physics? sleek darks. Health? warm tones.
- Limited palette (3-5 colors total)
- High contrast combinations
- Color-blind safe (avoid red-green combinations)
- Use color purposefully (not decoration)

**Layout for Visual Interest**:
- Vary layouts (not all bullet lists)
- Use two-column layouts (text + figure)
- Full-slide figures for key results
- Asymmetric compositions (more interesting than centered)
- Rule of thirds for focal points
- Consistent but not repetitive

### 3. Data Visualization for Slides

Adapt scientific figures for presentation context. For detailed guidance, refer to `references/data_visualization_slides.md`.

**Key Differences from Journal Figures**:
- Simplify, don't replicate
- Larger fonts (18-24pt minimum)
- Fewer panels (split across slides)
- Direct labeling (not legends)
- Emphasis through color and size
- Progressive disclosure for complex data

**Visualization Best Practices**:
- **Bar charts**: Comparing discrete categories
- **Line graphs**: Trends and trajectories
- **Scatter plots**: Relationships and correlations
- **Heatmaps**: Matrix data and patterns
- **Network diagrams**: Relationships and connections

**Common Mistakes to Avoid**:
- Tiny fonts (<18pt)
- Too many panels on one slide
- Complex legends
- Insufficient contrast
- Cluttered layouts

### 4. Talk-Specific Guidance

Different presentation contexts require different approaches. For comprehensive guidance on each type, refer to `references/talk_types_guide.md`.

**Conference Talks** (10-20 minutes):
- Structure: Brief intro → minimal methods → key results → quick conclusion
- Focus: 1-2 main findings only
- Style: Engaging, fast-paced, memorable
- Goal: Generate interest, network, get invited

**Academic Seminars** (45-60 minutes):
- Structure: Comprehensive coverage with detailed methods
- Focus: Multiple findings, depth of analysis
- Style: Scholarly, interactive, discussion-oriented
- Goal: Demonstrate expertise, get feedback, collaborate

**Thesis Defenses** (45-60 minutes):
- Structure: Complete dissertation overview, all studies
- Focus: Demonstrating mastery and independent thinking
- Style: Formal, comprehensive, prepared for interrogation
- Goal: Pass examination, defend research decisions

**Grant Pitches** (10-20 minutes):
- Structure: Problem → significance → approach → feasibility → impact
- Focus: Innovation, preliminary data, team qualifications
- Style: Persuasive, focused on outcomes and impact
- Goal: Secure funding, demonstrate viability

**Journal Clubs** (20-45 minutes):
- Structure: Context → methods → results → critical analysis
- Focus: Understanding and critiquing published work
- Style: Educational, critical, discussion-facilitating
- Goal: Learn, critique, discuss implications

### 5. Implementation Options

#### Nano Banana 2 PDF (Conceptual Drafts)

**Best for**: Conceptual or overview slides where editable or semantic text is not required

Generate conceptual slides as images when an image-only PDF meets the brief. Embed quantitative figures unchanged with PowerPoint/Beamer; reference-image generation can redraw them.

**Workflow**:
1. Plan each sl

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

