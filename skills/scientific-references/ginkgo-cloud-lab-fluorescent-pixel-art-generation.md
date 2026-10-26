---
id: sciref-ginkgo-cloud-lab-fluorescent-pixel-art-generation
name: "Scientific Ref: Fluorescent Pixel Art Generation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (ginkgo-cloud-lab): Fluorescent Pixel Art Generation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "ginkgo cloud lab fluorescent pixel art generation"
  - "fluorescent pixel art generation"
keywords:
  - "ginkgo"
  - "cloud"
  - "lab"
  - "fluorescent"
  - "pixel"
  - "art"
  - "generation"
  - "specialized"
  - "scientific"
  - "reference"
---

# Fluorescent Pixel Art Generation

**URL:** https://cloud.ginkgo.bio/protocols/fluorescent-pixel-art-generation
**Service terms:** https://cloud.ginkgo.bio/terms/pixel-art
**Reviewed:** 2026-09-30; prices and turnaround below are catalog estimates.
**Status:** Beta
**Price:** $25/plate (Echo 1536 format)
**Turnaround:** up to 7 days

## Overview

Transforms a digital image into a living, fluorescent bacterial artwork printed on an agar omni-tray. Designs are created with the on-platform **Design Tool** (upload an image or paint freehand); the tool maps the artwork onto a curated palette of 7 fluorescent E. coli strains. Overnight cultures are prepared from frozen glycerol stocks, diluted, and dispensed onto selective LB-chloramphenicol agar plates via Echo acoustic liquid handling at 50 nL per spot. Plates are incubated at 30 deg C for 16 hours, then 4 deg C for 12 hours to stabilize colony morphology and fluorescence. High-resolution photographs are captured under UV illumination and delivered digitally via your Cloud Lab account.

## Input

- **Design:** Created in the Design Tool (upload an image or paint from scratch); the tool maps the artwork to the 7-color palette automatically
- Service terms specify PNG or SVG design files and plate orientation; the result is a digital photograph, not a promise to ship a living plate
- **Plate format:** Echo 1536 (32x48 wells, 1,536 dots). The catalog still labels Echo 6144 (64x96) as coming soon, although the Design Tool displays that format; confirm orderability and price before selecting it.
- **Mapping controls:** Adjust brightness, contrast, and saturation, or use the Enhance slider to optimize color mapping in one step

## Available Fluorescent E. coli Strains (7-color palette)

| Strain/Protein | Color |
|---|---|
| sfGFP | Green |
| mRFP1 | Red |
| mKO2 | Orange |
| Venus | Yellow-green |
| mTurquoise2 | Cyan |
| Electra2 | Blue |
| mScarlet-I | Scarlet |

## Output

- **Digital delivery:** High-resolution UV photographs (TIFF/JPEG) of the printed plate, delivered via your Cloud Lab account

## Automated Workflow

### Phase 1 - Source Plate Preparation

1. Shake source plate (Bioshake)
2. Centrifuge source plate (BioNex HiG)
3. Peel source plate (Azenta XPeel)

### Phase 2 - Acoustic Dispensing (per destination plate)

1. Peel destination seal (Azenta XPeel)
2. Echo hit-pick dispensing at 50 nL per spot (Beckman Echo 525)
3. Seal destination plate (Agilent PlateLoc)
4. Shake destination plate (Bioshake)
5. Centrifuge destination (BioNex HiG)
6. Store destination at 30 deg C (Thermo CytoMat, 16 hr incubation)

### Phase 3 - Source Storage

1. Seal source plate (Agilent PlateLoc)
2. Store source plate (Thermo CytoMat)

### Post-Processing

1. Transfer to 4 deg C for 12 hours (fluorescence stabilization)
2. UV illumination photography
3. Image processing and delivery

## Ordering

- Create or import your design in the [Design Tool](https://cloud.ginkgo.bio/art), then order directly from it ($25/plate, Echo 1536)
- Or start from a community design in the **Gallery** (https://cloud.ginkgo.bio/gallery)

## Use Cases

- Educational outreach and demonstrations
- Unique scientific art and gifts
- Conference displays and promotional materials
- Lab team celebrations
- Visualizing biological art concepts

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

