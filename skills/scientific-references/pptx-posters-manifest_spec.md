---
id: sciref-pptx-posters-manifest-spec
name: "Scientific Ref: Poster manifest 2.0"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pptx-posters): Poster manifest 2.0"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pptx posters manifest spec"
  - "poster manifest 2.0"
keywords:
  - "pptx"
  - "posters"
  - "manifest"
  - "spec"
  - "specialized"
  - "scientific"
  - "reference"
  - "poster"
---

# Poster manifest 2.0

## Purpose

The manifest is the only content input to the generator. It binds:

- approved text and images;
- exact source IDs;
- local asset hashes and licenses;
- PowerPoint canvas and physical output geometry;
- conference and printer rules;
- accessibility/quality thresholds and their basis;
- reading order;
- author approval to a canonical content hash.

Unknown keys, duplicate JSON keys, non-finite numbers, remote asset paths, path escape,
unapproved fields, unresolved sources, unused records, and common placeholders are
rejected.

## Template

`assets/poster_manifest_template.json` is intentionally invalid. It contains
replacement tokens, false confirmations, and draft approval so it cannot produce a
poster accidentally.

Copy it into a project directory, then replace every field with reviewed values.
Asset paths are relative to that manifest's directory.

## Top-level object

Manifest version 2.0 requires exactly these keys:

- `schema_version`
- `document`
- `canvas`
- `physical_output`
- `requirements`
- `quality`
- `palette`
- `sources`
- `assets`
- `elements`
- `approval`

The validator rejects extensions to the schema rather than silently ignoring them.

## `document`

- `id`: stable identifier beginning with a letter.
- `title`: exact approved title, at most 255 characters.
- `subject`: exact approved description for core document metadata, at most 255 characters.
- `language`: BCP 47-style language tag.
- `authors`: exact ordered author names; joined by `; ` they must fit the 255-character
  core-property limit. No author is silently dropped or shortened.
- `source_ids`: exact records supporting title, subject, language, and author metadata.

Exactly one text element with role `title` must match `document.title` verbatim.
It must have `reading_order: 1`; generation uses it as the native PowerPoint slide
title placeholder rather than as an undifferentiated text box.

## `canvas`

- `width_in`, `height_in`: PowerPoint slide dimensions, each 1–56 inches.
- `background_color`: opaque six-digit sRGB hex.

These are design dimensions, not automatically the physical trim size.

## `physical_output`

- `trim_width_in`, `trim_height_in`: finished physical dimensions.
- `bleed_in`: physical bleed on each edge.
- `safe_margin_in`: inset inside the trim edge for non-bleed content.
- `orientation`: `portrait`, `landscape`, or `square`, matching trim dimensions.

The physical artboard is trim plus twice the bleed. It must share the canvas aspect
ratio.

## `requirements`

### `conference`

The organizer record must be confirmed and provide:

- exact `source_id`;
- maximum width and height;
- orientation (`portrait`, `landscape`, `square`, or `either`);
- required delivery format (`PDF`, `PPTX`, `PDF_AND_PPTX`, or `OTHER`);
- notes copied or summarized from the verified rule.

The physical trim dimensions must fit.
The referenced source record must have kind `conference_rule`.

### `printer`

The printer record must be confirmed and provide:

- exact `source_id`;
- trim width/height, bleed, and safe margin matching `physical_output`;
- accepted color mode (`RGB`, `CMYK`, or `PRINTER_MANAGED`);
- whether uniform scaling is allowed;
- notes describing the confirmed workflow.

If scaling is forbidden, canvas and physical artboard must be 1:1. A CMYK requirement
does not prevent creation of an editable RGB PPTX, but the export plan blocks a claim
of print readiness pending printer-approved conversion/proof.
The referenced source record must have kind `printer_rule`.

## `quality`

- `minimum_font_pt_final`
- `font_guidance_basis`
- `font_guidance_source_id`
- `minimum_raster_dpi_final`
- `raster_dpi_basis`
- `raster_dpi_source_id`

Basis values are:

- `heuristic`
- `source_specific`
- `conference_requirement`
- `printer_requirement`

A heuristic must have a null source ID. Every other basis requires an exact source
ID. Values apply at final physical output, after uniform scaling.

## `palette`

`colors` maps stable IDs to opaque `#RRGGBB` sRGB values.

Each `contrast_pairs` record contains:

- `id`
- `foreground_color_id`
- `background_color_id`
- `usage`: `normal_text`, `large_text`, or `non_text`

The validator applies 4.5:1 to normal text and 3:1 to large text/non-text. A text
element using `large_text` must be at least 18 pt final, or at least 14 pt final and
bold.

`data_series_redundant_encoding` must be true. This is an author confirmation that
color is supplemented by labels, shapes, markers, patterns, or line styles. It is not
an automated certification.

## `sources`

Each source has:

- `id`
- `kind`
- `citation`
- `locator`
- `author_verified: true`

Kinds include author content, publication, dataset, asset license, conference rule,
printer rule, institutional rule, and other.

Every source must be used, and every referenced ID must exist. The scripts do not
resolve URLs, DOIs, or local records.

## `assets`

The array may be empty: figures, logos, and QR codes are optional. Only local
PNG/JPEG assets are accepted when an asset is present. Each record has:

- `id`
- manifest-relative `path`
- `role`: `figure`, `logo`, or `qr_code`
- lowercase SHA-256
- exact `source_id`
- `license`: exact license or permission statement
- `provenance`: exact author-verified origin or generation record
- concise `alt_text`
- `author_approved: true`
- `qr_target`

`qr_target` is null except for QR assets, where it is an exact `https://` URL. Files
are bounded, final symlinks are rejected, paths cannot escape the manifest directory,
and hashes must match.

All asset records must be placed in the poster.
Use one asset record for repeated placement of the same file; duplicate asset paths
are rejected.

The image inventory rejects EXIF, XMP, comments, and embedded text/application
metadata to avoid publishing hidden or location-identifying information. Flatten and
strip such metadata in an author-reviewed offline workflow, then hash and approve the
resulting pixels as a new asset. ICC profiles and basic technical image fields are
reported but not silently removed.

## `elements`

Elements are listed in ascending, contiguous `reading_order` from 1. The list order is
not silently changed.

Every element has:

- `id`, `type`, and `reading_order`
- design coordinates `x_in`, `y_in`, `width_in`, `height_in`
- one or more exact `source_ids`
- `author_approved: true`
- `allow_in_bleed`

All boxes must stay on the canvas. Non-bleed elements must remain inside the physical
safe

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

