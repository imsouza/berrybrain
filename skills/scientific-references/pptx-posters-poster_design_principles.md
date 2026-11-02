---
id: sciref-pptx-posters-poster-design-principles
name: "Scientific Ref: Poster design and accessibility principles"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pptx-posters): Poster design and accessibility principles"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pptx posters poster design principles"
  - "poster design and accessibility principles"
keywords:
  - "pptx"
  - "posters"
  - "poster"
  - "design"
  - "principles"
  - "specialized"
  - "scientific"
  - "reference"
---

# Poster design and accessibility principles

## Requirements outrank conventions

There is no universal poster size, orientation, grid, body font, margin, image DPI,
word count, or number of columns. Confirm the current organizer and printer rules,
record exact source IDs, and design against those constraints.

Use generic advice only as a labeled project heuristic. Do not transform a heuristic
into a conference or accessibility requirement.

## Visual hierarchy

Make the research question, key result, and interpretation easy to locate without
forcing every poster into one visual style.

- Use a small, consistent set of text roles.
- Prefer left-aligned body text for left-to-right languages unless language or design
  requirements indicate otherwise.
- Keep related evidence, caption, and interpretation spatially grouped.
- Use spacing, alignment, size, and weight before adding decorative effects.
- Avoid unexplained icons, dense backgrounds, and text over uncontrolled imagery.
- Do not rely on a predicted "eye pattern"; confirm the actual reading order.

The generated PPTX uses fixed font sizes and disables text auto-shrink. A visual check
is still required because the XML package does not reveal font substitution or
rendered overflow.

## Font size means final-output size

PowerPoint stores point sizes on the PPTX canvas. When the printer scales the canvas,
the physical text scales too:

`final point size = design point size × physical artboard width / canvas width`

Use the same ratio on height; unequal ratios are prohibited.

Microsoft's PowerPoint accessibility guidance recommends 18 pt or larger for ordinary
slides. That is a [Microsoft slide recommendation](https://support.microsoft.com/en-us/office/make-your-powerpoint-presentations-accessible-to-people-with-disabilities-6f7772b2-2f33-4bd2-8ca7-dae3b2b3ef25),
not a universal poster minimum. Poster viewing distance, typeface, substrate, lighting,
audience, and organizer rules can require larger text.

The manifest therefore requires:

- a final-output minimum;
- a basis labeled `heuristic`, `source_specific`,
  `conference_requirement`, or `printer_requirement`;
- an exact source ID for every non-heuristic basis.

Test a reduced-scale print and the full-size proof under expected viewing conditions.

## Font availability and substitution

A typeface name in PresentationML is a request, not proof that the font is installed,
licensed for embedding, or rendered identically by another workstation. Microsoft's
[font-embedding guidance](https://support.microsoft.com/en-us/office/benefits-of-embedding-custom-fonts-cb3982aa-ea76-4323-b008-86670f222dbc)
notes that embedding can preserve layout but that not every font permits it and that
embedding only used characters limits editing.

The generator does not install or embed fonts. Before release:

- use fonts licensed for the intended authoring, sharing, embedding, and print use;
- confirm every declared face is installed on the review/export workstation;
- inspect substitutions, missing glyphs, equations, and line wrapping in PowerPoint;
- decide with the printer whether embedding is appropriate and permitted;
- inspect the actual exported PDF's font records and rendered glyphs.

## Text contrast

[WCAG 2.2 SC 1.4.3](https://www.w3.org/TR/WCAG22/#contrast-minimum) specifies:

- 4.5:1 for normal text;
- 3:1 for large text, defined as at least 18 pt, or at least 14 pt and bold.

WCAG is written for web content. This skill uses its sRGB contrast mathematics and
thresholds as an explicit design target for poster/PPTX color pairs; a passing ratio
does not by itself establish that a physical poster or exported PDF conforms to WCAG.
Print conversion, transparency, gradients, images behind text, paper, glare, and
lighting require manual review and proofing.

The manifest declares each foreground/background pair and its usage. Text elements
must reference a declared pair. The validator rejects a pair below its declared
threshold.

## Non-text contrast and color redundancy

[WCAG 2.2 SC 1.4.11](https://www.w3.org/TR/WCAG22/#non-text-contrast) uses 3:1
against adjacent colors for graphical parts required to understand content.
[SC 1.4.1](https://www.w3.org/TR/WCAG22/#use-of-color) says color must not be
the only visual means of conveying information.

For plots and diagrams:

- directly label important series and regions when practical;
- combine color with shape, marker, pattern, line style, position, or text;
- retain meaningful distinctions in grayscale;
- avoid assigning semantic meaning to a hue without another cue;
- check the rendered figure, not just the palette's color list.

The palette checker reports exact pair ratios and heuristic grayscale L* separation.
It explicitly does not certify color-vision accessibility.

## Choosing palettes

[ColorBrewer](https://colorbrewer2.org/) separates qualitative, sequential, and
diverging schemes and provides filters for colorblind-safe, print-friendly, and
photocopy-safe options. Its palettes were designed for maps; use the data-type logic,
then test the actual poster figure and background.

[Paul Tol's colour-scheme technical note](https://sronpersonalpages.nl/~pault/data/colourschemes.pdf)
provides schemes intended to remain clear for color-blind readers. Choose a scheme
for its documented purpose and supported category count. Do not assume every color
in a named scheme has sufficient text or line contrast against white.

Palette provenance does not replace contrast checks, redundant encodings, color-vision
simulation, or print proofing.

## Alt text and native text

Microsoft says visuals need concise alternative text describing their purpose and
important content. See
[Make PowerPoint presentations accessible](https://support.microsoft.com/en-us/office/make-your-powerpoint-presentations-accessible-to-people-with-disabilities-6f7772b2-2f33-4bd2-8ca7-dae3b2b3ef25).

This generator requires approved alt text for every local picture and writes it to
the standard PresentationML nonvisual drawing description. The technical inspector
checks that the description exists. It also supports a source-bound native text
element as a long description for a complex figure.

Alt text still needs human review:

- describe the purpose and essential conclusion, not every pixel;
- avoid repeating adjacent text verbatim;
- do not begin with redundant phrases such as "image of";
- include essential values and relationships when they are not available in nearby
 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

