---
id: sciref-pptx-posters-source-ledger
name: "Scientific Ref: Source ledger"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pptx-posters): Source ledger"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pptx posters source ledger"
  - "source ledger"
keywords:
  - "pptx"
  - "posters"
  - "source"
  - "ledger"
  - "specialized"
  - "scientific"
  - "reference"
---

# Source ledger

Latest API/workflow review: **2026-10-01**. Original research cutoff:
**2026-07-24**. Recheck live organizer, printer, package, and application guidance
before production use.

This ledger records the upstream basis for skill behavior. It is not a poster's
scientific bibliography.

Method: current official documentation, python-pptx tagged source, and official
PyPI release metadata were compared with all bundled scripts. The current exact
pins passed 52 local tests on Python 3.13.3, including UTC conversion, core metadata
limits, contain placement, deterministic generation, and path checks. Microsoft
PowerPoint, screen-reader, PDF export, and printer behavior remain manual checks.
The historical IEEE DSC example is explicitly bounded below; it was not
independently refreshed. These documentation checks are not authenticated service
tests: the shipped tools make no API calls.

## Microsoft PowerPoint

### Poster-specific product guidance

- [Microsoft Create poster templates for PowerPoint](https://create.microsoft.com/en-us/templates/posters)
  (official Microsoft Create, now redirected to PowerPoint templates; checked 2026-10-01).
  - Describes editable PowerPoint poster/flyer templates and saving, printing, or
    sending the result as PDF.

Skill impact: confirms PowerPoint as a supported poster authoring format, but does
not establish research-poster dimensions or printer requirements. This strict
generator does not ingest downloaded templates or use the page's AI design features.

### Slide dimensions and scaling

- [Change the size of your PowerPoint slides](https://support.microsoft.com/en-us/office/change-the-size-of-your-powerpoint-slides-040a811c-be43-40b9-8d04-0de5ed79987e)
  (Microsoft Support; checked 2026-10-01; no publication date exposed).
  - Custom width/height each range from 1 to 56 inches.
  - Units can be inches, centimeters, or pixels; PowerPoint converts them.
  - All slides in a presentation have the same size.
  - Maximize can cause content not to fit; Ensure Fit can make content smaller.

Skill impact: enforce 1–56 inches, one slide, exact aspect ratio, explicit physical
scale, and no reuse/resizing of existing content.

### Export

- [Export a presentation](https://support.microsoft.com/en-us/powerpoint/export-a-presentation)
  (Microsoft Support; checked 2026-10-01).
  - Standard is the option for publishing online and printing; Minimum size
    prioritizes a smaller file.

- [Create accessible PDFs](https://support.microsoft.com/en-us/accessibility/office-accessibility/create-accessible-pdfs)
  (Microsoft Support; checked 2026-10-01).
  - On macOS, the electronic-distribution/accessibility route sends the document to
    Microsoft's online conversion service; quality settings do not imply local-only
    processing. Object hyperlinks are preserved only by that documented route.

Skill impact: provide a manual export plan with separate canvas and final-artboard
PDF point dimensions, and require independent page-size/print checks. Scaled canvas
output needs confirmed printer scaling or a checked full-size derivative. The
scripts do not export PDF, invoke Office, or contact the conversion service.

### Accessibility

- [Make your PowerPoint presentations accessible to people with disabilities](https://support.microsoft.com/en-us/office/make-your-powerpoint-presentations-accessible-to-people-with-disabilities-6f7772b2-2f33-4bd2-8ca7-dae3b2b3ef25)
  (Microsoft Support; checked 2026-10-01).
  - Use Accessibility Checker and Reading Order pane.
  - Add alt text to visuals.
  - Do not use color alone.
  - Use sufficient text/background contrast.
  - Use meaningful hyperlink text.
  - Test with a screen reader.
  - Recommends 18 pt or larger for ordinary slides.

- [Rules for the Accessibility Checker](https://support.microsoft.com/en-us/accessibility/office-accessibility/rules-for-the-accessibility-checker)
  (Microsoft Support).
  - Includes missing alt text and logical reading order checks.

- [PowerPoint PDF Accessibility](https://learn.microsoft.com/en-us/office/pdf/powerpoint/powerpointpdfaccessibility)
  (Microsoft Learn; checked 2026-10-01).
  - Documents tagged-PDF behavior and applicable PowerPoint versions/channels.

Skill impact: automate only structural checks; require final Accessibility Checker,
reading-order, screen-reader, and exported-PDF review. The 18 pt recommendation is
identified as slide-specific, not a universal poster minimum.

### Fonts, pictures, and media

- [Benefits of embedding custom fonts](https://support.microsoft.com/en-us/office/benefits-of-embedding-custom-fonts-cb3982aa-ea76-4323-b008-86670f222dbc)
  (Microsoft Support; checked 2026-10-01).
  - Embedding can preserve layout, styling, and characters when a recipient lacks a
    font, but not all fonts permit embedding.
  - Embedding only used characters limits later editing; embedding all characters is
    the PowerPoint option intended for editing by others.

- [Change the default resolution for inserting pictures in Office](https://support.microsoft.com/en-us/office/change-the-default-resolution-for-inserting-pictures-in-office-f4aca5b4-6332-48c6-9488-bf5e0094a7d2)
  and [Turn off picture compression](https://support.microsoft.com/en-us/office/turn-off-picture-compression-81a6b603-0266-4451-b08e-fc1bf58da658)
  (Microsoft Support; checked 2026-10-01).
  - Microsoft documents High fidelity/minimal compression and a per-document option
    not to compress images.

- [Video and audio file formats supported in PowerPoint](https://support.microsoft.com/en-us/office/video-and-audio-file-formats-supported-in-powerpoint-d8b12450-26db-4c7b-a5c1-593d3418fb59)
  (Microsoft Support; checked 2026-10-01).
  - PowerPoint supports several audio/video formats and notes deprecations beginning
    in version 2505 for older formats.

Skill impact: the generator records font names but does not install or embed fonts;
availability, embedding rights, substitution, and the exported PDF are checked
manually. It accepts only fully decoded local PNG/JPEG still images, reports effective
DPI, and excludes every audio/video or linked-media feature from its package profile.

### Color API

- [PowerPoint ColorFormat.RGB property](https://learn.microsoft.com/en-us/office/vba/api/powerpoint.colorformat.rgb)
  (Microsoft Learn).

Skill impact: author opaque sRGB colors, label PowerPoint as an RGB workflow, and
block claims of CMYK readiness until printer-approved conversion/proof.

### 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

