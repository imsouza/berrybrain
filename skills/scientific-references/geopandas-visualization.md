---
id: sciref-geopandas-visualization
name: "Scientific Ref: Static and interactive visualization"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (geopandas): Static and interactive visualization"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "geopandas visualization"
  - "static and interactive visualization"
keywords:
  - "geopandas"
  - "visualization"
  - "specialized"
  - "scientific"
  - "reference"
  - "static"
  - "interactive"
---

# Static and interactive visualization

A map is a derived analytical artifact. It can misstate units, hide missing
data, expose exact locations, or contact third-party services even when the
underlying geometry operations are correct.

## Privacy gate

Before plotting:

1. classify coordinates, addresses, trajectories, parcels, facilities, and
   small-area attributes for sensitivity;
2. decide whether the audience needs exact geometry;
3. aggregate, suppress small groups, jitter only with a defensible privacy
   model, or generalize at an appropriate scale;
4. remove direct identifiers and sensitive tooltip/popup fields;
5. inspect the output itself—HTML, SVG, PDF, and GeoJSON can preserve exact
   coordinates or attributes even when the image looks coarse.

The bundled `scripts/sensitive_coordinates_checklist.py` provides a conservative
release gate. It does not claim legal or privacy compliance.

## Static plotting

GeoPandas `.plot()` uses Matplotlib:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 6))
gdf.plot(
    ax=ax,
    column="rate",
    cmap="viridis",
    legend=True,
    missing_kwds={
        "color": "lightgrey",
        "edgecolor": "black",
        "hatch": "///",
        "label": "Missing",
    },
)
ax.set_title("Synthetic rate by region")
ax.set_axis_off()
fig.savefig("derived/map.png", dpi=300, bbox_inches="tight")
```

Pin Matplotlib and optional mapping dependencies in the project lock. The
GeoPandas 1.2 tagged source requires Matplotlib >=3.9 for plotting and
mapclassify >=2.7 for classifications. Static examples were exercised with
Matplotlib 3.11.2; the optional classification, interactive, and tile examples
are illustrative unless those dependencies are installed and tested.

GeoPandas 1.2 rewrote static plotting: categorical palettes/styles accept
dictionaries, legends reflect geometry types, and layered maps can use
`ax.legend()`. CRS-based axis labels are enabled by default (`add_labels=False`
disables them). `scheme=` supports `vmin`/`vmax` and can use
`legend_kwds={"colorbar": True}` for a classified colorbar. Inspect existing
figures after migration; Matplotlib collection layout is not a stable contract.

### Choropleth correctness

State in the title/caption or metadata:

- variable definition, units, date, and source;
- whether values are counts, rates, densities, or percentages;
- normalization denominator and treatment of zero/missing denominators;
- classification method, number of bins, and explicit boundaries;
- color-map direction and meaning;
- missing/suppressed/out-of-scope styling;
- CRS/projection and any geographic generalization.

Raw counts over unequal polygon areas often communicate population size rather
than rate. Compute an appropriate rate/density first and retain numerator and
denominator.

`scheme=` delegates classification to mapclassify:

```python
ax = gdf.plot(
    column="rate",
    scheme="quantiles",
    k=5,
    cmap="viridis",
    legend=True,
)
```

Quantiles balance feature counts but can place almost equal values in different
bins. Equal intervals can leave sparse bins; natural breaks are data-dependent
and make cross-map comparisons difficult. For comparisons, reuse explicit
boundaries and a common normalization.

### Missing data

GeoPandas ignores missing values by default. That can make missing areas look
like background or water. Always count missing values and use `missing_kwds`
when they are meaningful. Distinguish:

- missing attribute;
- missing geometry;
- empty geometry;
- suppressed value;
- zero;
- outside the study area.

Do not coerce missing values to zero for visual convenience.

### Categorical maps

Use `categorical=True` for categories and a qualitative palette. Verify category
order and legend labels; do not imply magnitude with a sequential palette.
For example, the following explicit palette is supported in 1.2:

```python
ax = gdf.plot(
    column="category", categorical=True,
    cmap={"A": "#4477AA", "B": "#EE6677"},
    legend=True, tiles=False,
)
```

Keep the palette complete for the data's categories. The earlier 1.1.4 fix for
custom categorical/boolean `explore()` legend labels is included.

### Layering

```python
fig, ax = plt.subplots(figsize=(8, 6))
areas.plot(ax=ax, facecolor="none", edgecolor="0.4", zorder=1)
generalized_points.plot(ax=ax, color="black", markersize=8, zorder=2)
```

- Reproject every layer to a common CRS.
- Use `facecolor="none"` for transparent polygon faces; Python `None` means
  something different.
- Choose `zorder`, alpha, and line width deliberately.
- Confirm no layer is hidden by a filled polygon.
- Keep a stable visual scale when comparing panels.

## Projection and extent

Choose a map projection for the communication goal:

- equal-area for area comparisons;
- local conformal for local shape/angles;
- Web Mercator only when required by a web tile system;
- a suitable global projection for world views.

GeoPandas may set a latitude-dependent aspect for geographic plots, but that is
not a replacement for a chosen projection. Exact metric scale bars require a
projected CRS with known linear units and limited distortion.

Antimeridian-crossing geometries must be split/wrapped before plotting; changing
axis limits does not repair a line drawn across the map.

## Basemaps are network and licensing dependencies

GeoPandas 1.2 static `plot(tiles=...)`, contextily, and `explore(tiles=...)` can send viewport,
zoom, IP, and timing information to a provider and can disclose the study area.
They also introduce attribution, terms-of-use, caching, availability, and
reproducibility requirements.

Static plots default to `tiles=False`; interactive drafts use `tiles=None`.
Do not fetch tiles automatically. If a user explicitly approves a provider:

- verify its official URL, license, attribution, and usage limits;
- generalize sensitive overlays before the request;
- record provider, style, retrieval date, zoom, and tile hashes/cache;
- do not put credentials in source or generated HTML;
- use a vetted cache for reproducible/offline output where permitted.

## Interactive `explore`

`GeoDataFrame.explore()` returns a `folium.Map`. Background tiles require CRS
metadata and normally cause network requests. Start with a no-tile,
no-attribute local draft:

```python
interactive = generalized_gdf.explore(
    tiles=None,
    tooltip=False,
    popup=False,
    style_kwds={"fillOpacity": 0.5, "weight": 1},
)
interactive.save("derived/lo

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

