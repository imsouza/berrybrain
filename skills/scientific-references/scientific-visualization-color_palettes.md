---
id: sciref-scientific-visualization-color-palettes
name: "Scientific Ref: Color, Contrast, and Palette Selection"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-visualization): Color, Contrast, and Palette Selection"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific visualization color palettes"
  - "cientifico visualization color palettes"
  - "color, contrast, and palette selection"
keywords:
  - "scientific"
  - "visualization"
  - "color"
  - "palettes"
  - "cientifico"
  - "specialized"
  - "reference"
---

# Color, Contrast, and Palette Selection

Reviewed 2026-10-01. Source IDs resolve in `sources.md`. A named “colorblind-safe” palette is not a guarantee that a rendered figure is accessible: background, line thickness, adjacency, text, category count, display/print conversion, and redundant encoding all matter.

## Start with data semantics

- **Qualitative:** unordered categories. Hue can separate groups; lightness should not imply an unintended ranking.
- **Sequential:** ordered low-to-high values. Use monotonic perceived lightness.
- **Diverging:** departure around a meaningful center. Use a neutral midpoint and document the normalization.
- **Cyclic:** periodic values where endpoints meet.

Do not use a diverging map merely because values contain positive and negative numbers; the center must have scientific meaning. Do not use a rainbow map as a generic ordered scale. Paul Tol documents false visual transitions, lack of inherent magnitude ordering, and color-vision problems in ordinary rainbow schemes [TOL].

With Matplotlib, colormap and normalization are separate:

```python
import matplotlib as mpl

norm = mpl.colors.TwoSlopeNorm(vmin=-2, vcenter=0, vmax=5)
image = ax.imshow(values, cmap="RdBu_r", norm=norm)
fig.colorbar(image, ax=ax, label="Change (unit)")
```

Use `LogNorm` for strictly positive orders of magnitude, `SymLogNorm` for signed data with a disclosed linear zone, `BoundaryNorm` for meaningful classes, and `TwoSlopeNorm` for unequal ranges around a center [MPL-NORM].

## Okabe-Ito / Wong colors

The eight colors commonly reproduced from Wong’s Nature Methods article are [WONG]:

```python
OKABE_ITO = [
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#F0E442",  # yellow
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
    "#000000",  # black
]
```

Several light colors do not reach 3:1 against white. For thin lines or required graphical objects on white, start with the bundled five-color subset:

```python
OKABE_ITO_ON_WHITE = [
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#000000",
]
```

This subset is derived by WCAG sRGB contrast calculation; it is not a published palette or a compliance certification. Use marker/line-style redundancy and audit the actual rendering.

## Paul Tol qualitative schemes

Paul Tol’s canonical site moved to `sronpersonalpages.nl` in July 2026. The current technical note remains SRON/EPS/TN/09-002, issue 3.2, dated 2021-08-18 [TOL] [TOL-HOME].

The note states that the bright, high-contrast, vibrant, muted, and medium-contrast qualitative schemes are color-blind safe under its design/testing assumptions. It also states:

- high-contrast is the strongest choice for grayscale/monochrome separation;
- medium-contrast provides three pairs but weaker grayscale separation;
- light is reasonably distinct and intended mainly for labeled cell fills;
- pale/dark are not sufficiently distinct for multi-series lines or maps and are meant for text backgrounds/foregrounds;
- most multi-color qualitative schemes do not remain fully separable in grayscale.

Bundled fixed-order values:

```python
TOL_BRIGHT = [
    "#4477AA", "#EE6677", "#228833", "#CCBB44",
    "#66CCEE", "#AA3377", "#BBBBBB",
]

TOL_HIGH_CONTRAST = ["#004488", "#DDAA33", "#BB5566"]

TOL_VIBRANT = [
    "#EE7733", "#0077BB", "#33BBEE", "#EE3377",
    "#CC3311", "#009988", "#BBBBBB",
]

TOL_MUTED = [
    "#CC6677", "#332288", "#DDCC77", "#117733", "#88CCEE",
    "#882255", "#44AA99", "#999933", "#AA4499",
]

TOL_MEDIUM_CONTRAST = [
    "#6699CC", "#004488", "#EECC66",
    "#994455", "#997700", "#EE99AA",
]
```

The maximum intended series counts are 7, 3, 7, 9, and 6 respectively. Do not interpolate qualitative palettes.

## ColorBrewer

ColorBrewer 2.0 is an authoritative interactive resource for sequential, diverging, and qualitative cartographic schemes. It allows filtering by “colorblind safe,” “print friendly,” and “photocopy safe,” and exposes the supported number of data classes [COLORBREWER].

Use the exact class count shown by ColorBrewer. A scheme marked safe at one class count may not be marked safe at another. ColorBrewer’s flags are design guidance for its intended mapping context, not a WCAG conformance result for arbitrary line widths, backgrounds, or text.

Matplotlib exposes many ColorBrewer-derived maps. Verify the exact map direction and class count rather than relying on its name.

## Perceptually uniform continuous maps

Matplotlib recommends selecting maps based on data semantics and discusses lightness behavior in its colormap guide [MPL-CMAP]. Common continuous candidates:

- `viridis`, `plasma`, `inferno`, `magma`: perceptually uniform sequential families;
- `cividis`: designed with color-vision deficiencies in mind;
- `RdBu_r`, `PuOr`, `BrBG`: possible diverging candidates after checking the center, direction, contrast, and grayscale behavior.

No list is universally safe. A map can be perceptually uniform yet still fail to distinguish a narrow feature at the chosen size, or lose detail during RGB-to-CMYK conversion.

## WCAG contrast: what to test

WCAG 2.2 is normative for web content [WCAG22]:

- normal text: 4.5:1 against its background (SC 1.4.3 AA);
- large text: 3:1 (SC 1.4.3 AA);
- graphical objects required to understand content: 3:1 against adjacent colors (SC 1.4.11 AA);
- color must not be the only visual means of conveying information (SC 1.4.1 A).

W3C’s understanding document uses line and pie charts as examples and explains that required graphical objects are tested against adjacent colors; all data-series colors do not automatically need 3:1 against each other when they do not overlap [WCAG-NONTEXT].

Run:

```bash
uv run --isolated --no-project --python 3.13 \
  python scripts/palette_audit.py \
  --palette okabe_ito_on_white \
  --background FFFFFF \
  --role graphical
```

The CLI reports:

- exact WCAG sRGB contrast against the chosen background;
- pairwise contrast;
- pairwise CIE L* separation after removing hue.

Its default grayscale threshold (ΔL* 10) is a heuristic. It is not a WCAG threshold and does not simulate every color-vision deficiency, printer, profile, or viewing condition.

## Redundant encoding

Use at least one non-color cue:

```python
colors = ["#0072B2", "#D55E00", "#009E73"]
linestyles = ["-", "--", "-."]
markers = ["o", "s", "^"]

for index, series in enumerate(series_list):
    ax.plot(
        x,
        series,
  

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

