---
version: alpha
name: "Frequency-Based Extraction — BerryBrain Edition"
description: "Design tokens extracted from frequency analysis, adapted for BerryBrain brand identity (#CC4168 / #96B55C)."
colors:
  primary: "#CC4168"
  primary-hover: "#B33654"
  secondary: "#96B55C"
  secondary-hover: "#7FA04A"
  surface: "#FAF8F5"
  surface-elevated: "#FFFFFF"
  text: "#1D1B18"
  text-2: "#5C5C5C"
  text-3: "#6B655E"
  text-4: "#7A746B"
  text-5: "#CC4168"
  text-6: "#FFFFFF"
  local-accent: "#E8D5DA"
  local-accent-2: "#E8EDD8"
  border: "#E4E0D8"
  border-focus: "#CC4168"
  success: "#96B55C"
  error: "#CC4168"
typography:
  type-1:
    fontFamily: "Inter"
    fontSize: "16px"
    fontWeight: "400"
    lineHeight: "24px"
  type-2:
    fontFamily: "Inter"
    fontSize: "14px"
    fontWeight: "400"
    lineHeight: "20px"
  type-3:
    fontFamily: "Inter"
    fontSize: "14px"
    fontWeight: "600"
    lineHeight: "20px"
  type-4:
    fontFamily: "Geist Mono"
    fontSize: "11px"
    fontWeight: "400"
    lineHeight: "16.5px"
  type-5:
    fontFamily: "Inter"
    fontSize: "14px"
    fontWeight: "400"
    lineHeight: "22.75px"
rounded:
  radius-1: "8px"
  radius-2: "10px"
  radius-3: "6px"
  radius-4: "12px"
spacing:
  space-1: "16px"
  space-2: "20px"
  space-3: "12px"
  space-4: "8px"
  space-5: "4px"
  space-6: "24px"
  space-7: "40px"
  space-8: "6px"
  space-9: "112px"
  space-10: "10px"
---

## Overview

Design tokens extracted from frequency analysis, adapted for BerryBrain brand identity. The palette now centers on the logo's signature berry pink (#CC4168) and fresh green (#96B55C), with supporting neutrals drawn from the original warm grayscale to preserve the system's tactile, organic feel.

**Signature traits:**
- Berry-forward primary: warm, energetic pink-red anchors CTAs and brand moments.
- Fresh green secondary: signals growth, health, and positive states.
- Warm neutral surfaces: off-white and parchment tones keep the palette approachable.

## Colors

The palette uses 16 validated color tokens across 1 theme profile. Semantic roles are mapped to observed usage patterns so generation agents can choose accents without inventing new color meaning.

### Primary Brand
- **Primary** (#CC4168): BerryBrain logo pink. Role: primary action, brand emphasis, links, active states. {authored: rgb(204, 65, 104), space: rgb}
- **Primary-hover** (#B33654): Darkened 10% for hover/focus states. Role: interactive feedback. {authored: rgb(179, 54, 84), space: rgb}

### Secondary Brand
- **Secondary** (#96B55C): BerryBrain logo green. Role: success states, secondary actions, positive indicators, badges. {authored: rgb(150, 181, 92), space: rgb}
- **Secondary-hover** (#7FA04A): Darkened 10% for hover/focus states. Role: interactive feedback. {authored: rgb(127, 160, 74), space: rgb}

### Text Scale
- **Text** (#1D1B18): Near-black for maximum legibility. Role: primary text, headings, body. {authored: rgb(29, 27, 24), space: rgb}
- **Text-2** (#5C5C5C): Neutral gray for secondary text. Role: descriptions, captions, meta. {authored: rgb(92, 92, 92), space: rgb}
- **Text-3** (#6B655E): Warm gray for tertiary text. Role: placeholders, disabled labels, timestamps. {authored: rgb(107, 101, 94), space: rgb}
- **Text-4** (#7A746B): Muted warm gray for quaternary text. Role: footnotes, legal copy. {authored: rgb(122, 116, 107), space: rgb}
- **Text-5** (#CC4168): Brand pink for emphasized inline text, active nav items, prices. Role: accent text. {authored: rgb(204, 65, 104), space: rgb}
- **Text-6** (#FFFFFF): Pure white for text on dark or saturated backgrounds. Role: inverse text. {authored: rgb(255, 255, 255), space: rgb}

### Surface & Shadows
- **Surface** (#FAF8F5): Warm off-white base background. Role: page canvas, card backgrounds. {authored: rgb(250, 248, 245), space: rgb}
- **Surface-elevated** (#FFFFFF): Pure white for elevated layers (modals, dropdowns, cards). Role: popover, modal, sticky headers. {authored: rgb(255, 255, 255), space: rgb}

### Interactive & Borders
- **Local-accent** (#E8D5DA): Soft berry tint for subtle highlights, selected rows, tag backgrounds. Role: selection, highlight. {authored: rgb(232, 213, 218), space: rgb}
- **Local-accent-2** (#E8EDD8): Soft green tint for success highlights, tag backgrounds, progress fills. Role: positive highlight. {authored: rgb(232, 237, 216), space: rgb}
- **Border** (#E4E0D8): Neutral warm border for dividers, input outlines, card strokes. Role: structural border. {authored: rgb(228, 224, 216), space: rgb}
- **Border-focus** (#CC4168): Brand pink for focused input outlines, active tab indicators. Role: focus ring. {authored: rgb(204, 65, 104), space: rgb}

### Semantic
- **Success** (#96B55C): Green for confirmations, checkmarks, completion states. Role: positive feedback. {authored: rgb(150, 181, 92), space: rgb}
- **Error** (#CC4168): Pink for errors, warnings, destructive actions. Role: negative feedback. {authored: rgb(204, 65, 104), space: rgb}

## Typography

Typography uses Inter and Geist Mono across extracted hierarchy roles. Keep hierarchy mapped to these token rows before adding decorative type styles.

Mixes Inter and Geist Mono for visual contrast. Weight range spans regular, semi-bold. Sizes range from 11px to 16px.

### Type Scale Evidence
| Role | Font | Size | Weight | Line Height | Letter Spacing | Stack / Features | Notes |
|------|------|------|--------|-------------|----------------|------------------|-------|
| Frequency rank #1 | Inter | 16px | 400 | 24px | normal | Inter, Inter Fallback, ui-sans-serif, system-ui, sans-serif | Extracted token |
| Frequency rank #2 | Inter | 14px | 400 | 20px | normal | Inter, Inter Fallback, ui-sans-serif, system-ui, sans-serif | Extracted token |
| Frequency rank #3 | Inter | 14px | 600 | 20px | normal | Inter, Inter Fallback, ui-sans-serif, system-ui, sans-serif | Extracted token |
| Frequency rank #4 | Geist Mono | 11px | 400 | 16.5px | normal | Geist Mono, Geist Mono Fallback, ui-monospace, monospace | Extracted token |
| Frequency rank #5 | Inter | 14px | 400 | 22.75px | normal | Inter, Inter Fallback, ui-sans-serif, system-ui, sans-serif | Extracted token |

## Layout

Layout rhythm is inferred from spacing tokens and responsive breakpoint evidence.

### Spacing System
| Token | Value | Px | Notes |
|------|-------|----|-------|
| space-5 | 4px | 4 | Extracted spacing token |
| space-8 | 6px | 6 | Extracted spacing token |
| space-4 | 8px | 8 | Extracted spacing token |
| space-10 | 10px | 10 | Extracted spacing token |
| space-3 | 12px | 12 | Extracted spacing token |
| space-1 | 16px | 16 | Extracted spacing token |
| space-2 | 20px | 20 | Extracted spacing token |
| space-6 | 24px | 24 | Extracted spacing token |
| space-7 | 40px | 40 | Extracted spacing token |
| space-9 | 112px | 112 | Extracted spacing token |

## Elevation & Depth

Keep depth flat unless validated shadow or interaction evidence appears in the extraction payload. Do not invent shadows beyond this evidence boundary.

### Shadow Evidence
| Shadow Token | Layers | Details |
|--------------|--------|---------|
| n/a | 0 | No validated shadow payload |

### Interaction Signals
| Theme | Signal | Evidence |
|-------|--------|----------|
| Light | backdrop-filter | blur(8px) |
| Light | outline-color | #CC4168 at 50% opacity |
| Light | outline-width | 3px |
| Light | outline-offset | 0px |

## Shapes

Shape language maps directly to rounded tokens. Keep component corners consistent with the role mapping below before introducing bespoke geometry.

### Radius Roles
| Token | Value | Px | Role Mapping |
|------|-------|----|--------------|
| radius-3 | 6px | 6 | Subtle corner |
| radius-1 | 8px | 8 | Control corner |
| radius-2 | 10px | 10 | Control corner |
| radius-4 | 12px | 12 | Control corner |

### Geometry Evidence
| Radius Token | Shape | Units |
|--------------|-------|-------|
| radius-1 | 8px | px |
| radius-2 | 10px | px |
| radius-3 | 6px | px |
| radius-4 | 12px | px |

## Components

(none detected)

## Do's and Don'ts

Guardrails tie generation choices back to validated tokens, component patterns, and evidence-backed hierarchy.

| Do | Don't |
|----|---------|
| Do use **primary** (#CC4168) for the single most important action per screen | Don't use primary pink for large background fills — it overwhelms |
| Do use **secondary** (#96B55C) for success states and secondary CTAs | Don't mix both brand colors at equal weight in the same component |
| Do maintain consistent spacing using the base grid | Don't make unsupported claims about absent visual features |
| Do maintain WCAG AA contrast ratios (4.5:1 for normal text) | Don't mix rounded and sharp corners in the same view |
| Do verify evidence before writing new design-system guidance | Don't use #CC4168 on #E8D5DA without ensuring 4.5:1 contrast |
| Do use **surface** (#FAF8F5) as the default page background | Don't place #96B55C text on #E8EDD8 — contrast is too low |

## Responsive Evidence

### Breakpoints

No distinct responsive breakpoints were extracted.

## Agent Prompt Guide

### Example Component Prompts
- Create button component using validated primary (#CC4168) and secondary (#96B55C) color roles, with primary-hover (#B33654) and secondary-hover (#7FA04A) states.
- Create card component with mapped radius role, surface (#FAF8F5) or surface-elevated (#FFFFFF) background, and border (#E4E0D8) stroke.
- Create form input component using inferred typography hierarchy, border (#E4E0D8) default state, and border-focus (#CC4168) focused state.
- Create badge/tag component using local-accent (#E8D5DA) for brand tags and local-accent-2 (#E8EDD8) for success tags.

### Iteration Guide
1. Start with extracted palette and typography roles only.
2. Map spacing and radius directly from token tables before visual polish.
3. Apply component patterns one section at a time and compare against source intent.
4. Keep elevation claims tied to explicit evidence in output.
5. Iterate with smallest diffs and re-check section hierarchy after each change.
