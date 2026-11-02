---
id: sciref-matlab-graphics-visualization
name: "Scientific Ref: Graphics and Export"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matlab): Graphics and Export"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matlab graphics visualization"
  - "graphics and export"
keywords:
  - "matlab"
  - "graphics"
  - "visualization"
  - "specialized"
  - "scientific"
  - "reference"
  - "export"
---

# Graphics and Export

This reference targets MATLAB R2026a. Rendering and property support differ in
GNU Octave and across MATLAB releases/platforms.

## Build figures with explicit ownership

Use handles instead of relying on `gcf`/`gca` in reusable code:

```matlab
fig = figure(Color="white");
layout = tiledlayout(fig, 2, 1, ...
    TileSpacing="compact", ...
    Padding="compact");

ax1 = nexttile(layout);
plot(ax1, time, signal, LineWidth=1.5);
xlabel(ax1, "Time (s)");
ylabel(ax1, "Amplitude (V)");
title(ax1, "Measured signal");
grid(ax1, "on");

ax2 = nexttile(layout);
histogram(ax2, residual, Normalization="pdf");
xlabel(ax2, "Residual (V)");
ylabel(ax2, "Density");
```

Explicit handles make tests, nested layouts, apps, and exports predictable.
Set limits, aspect ratio, color limits, and view deliberately when comparison
across figures matters.

## Scientific communication checklist

- Include quantities and units in labels.
- State transformations, normalization, aggregation, and uncertainty.
- Use colorblind-aware, perceptually ordered palettes; do not use color alone
  for categories.
- Keep data and annotations distinguishable in grayscale when required.
- Match marker/line width, font size, and panel size to final publication size.
- Avoid misleading axis truncation or 3-D effects.
- Set deterministic sorting/group order before plotting categorical data.
- Add alternative text/caption information in the surrounding document.
- Inspect embedded raster content even when the container format is vector.

Graphics functions can belong to separate products. For example, basic
`plot`, `scatter`, `histogram`, `imagesc`, `surf`, and `tiledlayout` are base
MATLAB, while domain-specific statistical, mapping, image, signal, or medical
visualizations can require named toolboxes.

## Export with `exportgraphics`

Prefer `exportgraphics` for current workflows:

```matlab
exportgraphics(fig, "overview.pdf", ContentType="vector");
exportgraphics(ax1, "signal.png", Resolution=300);
```

R2026a-supported output includes:

- raster: PNG, JPEG, TIFF, GIF;
- vector-capable: PDF, SVG, EPS, and Windows-only EMF;
- interactive HTML web canvas (new in R2026a).

SVG support was added in R2025a. `Append=true` is supported for PDF and GIF,
not every format. `ContentType` selects vector/image content for PDF, EPS,
and EMF; choose SVG by its extension without relying on this option.
Inspect export artifacts and any embedded images. `Resolution` has no effect
on vector output or HTML. R2025a
added dimensions/padding controls; verify exact option and unit support in the
target release.

Interactive HTML is active web content, not a static image. Review its
embedded assets and distribution context; do not open an untrusted exported
HTML file automatically.

### Which export API?

| API | Prefer for | Notes |
|---|---|---|
| `exportgraphics` | axes, layouts, figures, publication files | current default; crop/padding, vector/raster, multipage PDF |
| `copygraphics` | clipboard | interactive transfer; not reproducible file output |
| `exportapp` | app/UI capture | UI-focused behavior |
| `print` | legacy/device-specific workflows | behavior and UI support differ |
| `savefig` | editable MATLAB figure | MATLAB object artifact, not archival interchange |
| `saveas` | simple legacy save | less control than `exportgraphics` |
| `imwrite` | image arrays/animated GIF construction | not a general figure renderer |

Never treat `.fig` as passive. It stores MATLAB graphics objects and should be
handled as an untrusted MATLAB object artifact unless its provenance is known.

## Headless and batch behavior

`matlab -batch` starts without the desktop but can still display figure windows
unless `-noFigureWindows` or `-nodisplay` is added. Rendering may depend on
graphics hardware, fonts, installed system support, and platform. A planner
should distinguish:

- **compute-only**: no figures;
- **off-screen export**: figures created but not shown;
- **interactive graphics**: requires a display and user;
- **web-canvas export**: generates active HTML.

The bundled command planner only returns argv and never starts MATLAB.
Review trusted code, fonts, output paths, overwrite policy, and license before
an approved run.

For deterministic export:

1. create a new explicit figure;
2. set size/units, axes limits, color limits, and fonts;
3. avoid dependence on desktop defaults and current objects;
4. set RNG before randomized jitter/layout;
5. export to a new local path and refuse unintended overwrite;
6. inventory output dimensions, file type, fonts, and embedded raster content;
7. compare images with an appropriate visual tolerance, not byte equality.

## Color and layout

```matlab
colororder(ax1, orderedColors);
colormap(ax2, "parula");
clim(ax2, [lowerLimit upperLimit]);
axis(ax2, "tight");
```

Use a sequential map for ordered magnitude, a diverging map around a meaningful
center, and distinct categorical colors for unordered groups. Avoid `jet` for
quantitative interpretation. Keep a shared color scale when panels are meant
to be compared.

Use `tiledlayout`/`nexttile` rather than new `subplot` code. Legends and
colorbars can belong to an axes or layout; make ownership explicit.

## Time, table, and categorical plots

Many plotting functions accept tables directly. This preserves variable-name
selection but does not remove the need to validate types and missing data.

```matlab
plot(T, "Time", ["Observed" "Predicted"]);
legend(["Observed" "Predicted"], Location="best");
```

Sort time values and define duplicate/missing handling before plotting.
Categorical order controls axis/group order. Avoid silently dropping missing
values without reporting the count.

## 3-D, transparency, and large data

3-D surfaces, transparency, lighting, and very dense primitives can force
rasterization or produce platform-specific output. For large data:

- decimate only with a documented visual/statistical rule;
- preserve extremes and events;
- distinguish display reduction from analysis data;
- record the displayed sample count and aggregation;
- test export memory and file size.

## Review checklist

- [ ] Every object has an explicit parent handle.
- [ ] Data transformations and missing-value counts are documented.
- [ ] Axes, units, limits, and color scale are intentional.
- [ ] Product/toolbox requirements are declared.
- [ ] Output path is local, new, and reviewed.
- [ ] Vector versus raster intent is explicit.
- [ ] HTML and `.fig`

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

