---
id: sci-scientific-visualization
name: "Scientific: scientific-visualization"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Creates and audits truthful, accessible, publication-ready scientific figures with Matplotlib, Seaborn, or Plotly. Use it for figure design, multi-panel layouts, uncertainty and missing-data displays, color/contrast review, image metadata validation, and journal export planning."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "scientific visualization"
  - "cientifico visualization"
  - "scientific-visualization"
keywords:
  - "scientific"
  - "visualization"
  - "cientifico"
  - "creates"
  - "audits"
  - "truthful"
  - "accessible"
  - "publication"
  - "ready"
---

# Scientific Visualization

Build figures that preserve scientific meaning before optimizing appearance. Separate universal principles from dated publisher rules, preserve raw data and transformations, use color redundantly, and inspect delivered files rather than trusting plotting defaults.

## Non-negotiable guardrails

- Never alter, hide, invent, or selectively enhance data to improve a figure.
- Preserve raw tables/images, exclusions, missing-value codes, analysis code, normalization, binning, image adjustments, and random seeds.
- Do not infer journal requirements. Identify the exact journal, article type, figure type, and submission phase; verify its live official guidance.
- Do not claim that a palette, DPI value, format, or automated report makes a figure accessible or journal-compliant.
- Do not silently connect missing observations, suppress inconvenient points, upsample images as if detail increased, or tune axes/dual axes to exaggerate a conclusion.
- Keep interactive and static outputs as distinct deliverables. Interactive hover is not a substitute for labels, alt text, keyboard access, an accessible data table, or a static fallback.

Read `references/publication_guidelines.md` for deceptive-encoding and integrity checks. Read `references/journal_requirements.md` only after the target and phase are known.

## Workflow

### 1. Define the evidence and destination

Record:

- audience and medium: manuscript, web, slide, poster, supplement;
- exact publisher/journal, article type, submission phase, and intended final width;
- variable semantics, units, sample/replicate structure, missing/censored values;
- estimator and uncertainty definition;
- transformations: filtering, aggregation, normalization, smoothing, bins, image processing;
- source-data paths/identifiers and output provenance.

If requirements are not known, create a provisional general figure and label all publisher choices as pending verification.

### 2. Choose an honest encoding

Prefer position on a common scale. Before coding, check:

- **Bars/areas:** normally include zero because length/area is measured from a baseline.
- **Points/lines:** nonzero limits can be valid; show context and disclose breaks.
- **Uncertainty:** name SD, SE, CI, percentile, posterior, or another interval; state `n` and the unit of replication.
- **Raw observations:** show them when feasible; do not let jitter obscure categories/values.
- **Missing data:** distinguish missing, zero, censored, and excluded; use gaps or explicit model/interpolation styling.
- **Area/volume:** scale area/volume, not radius/diameter; avoid decorative 3D.
- **Log axes:** label the base/transform and declare how zero/negative values are handled.
- **Binning/smoothing:** record edges, bandwidth/window, method, and sensitivity.
- **Normalization:** state formula/reference and keep limits consistent across compared panels.
- **Dual axes:** prefer aligned panels; if unavoidable, justify units and do not engineer apparent correlation.
- **Images:** preserve originals, disclose whole-image adjustments, show scale bars, and avoid clipped/erased background.

### 3. Design accessibility in, not after

- Use color plus marker, line style, hatching, direct label, or panel separation.
- Choose qualitative, sequential, diverging, or cyclic color according to data semantics.
- Audit foreground/background contrast at the rendered size.
- Make missing and out-of-range values explicit.
- Provide alt text, a longer description for complex figures, and underlying data for web delivery.
- Treat WCAG 2.2 as web guidance: 4.5:1 normal text, 3:1 large text, and 3:1 for graphical objects required for understanding; color cannot be the only cue. Applicability and exceptions matter.

See `references/color_palettes.md`. A grayscale screen is useful but is not a complete color-vision or accessibility test.

### 4. Implement with scoped styles

Run shell examples from this skill directory. For your own figure script, add `scripts/` and `assets/` to the import path (see the bootstrap in `references/matplotlib_examples.md`) and create the output directory. Use Matplotlib's object-oriented API and temporary style contexts:

```python
import matplotlib.pyplot as plt

from style_presets import style_context

with style_context("default", palette_name="okabe_ito_on_white"):
    fig, ax = plt.subplots(
        figsize=(89 / 25.4, 60 / 25.4),
        layout="constrained",
    )
    ax.plot(x, y, marker="o", label="Observed")
    ax.set(xlabel="Time (hours)", ylabel="Response (unit)")
    ax.legend()
```

`layout="constrained"` supports colorbars, nested GridSpec, subfigures, and `subplot_mosaic`. Do not call `tight_layout()` afterward; it disables constrained layout.

For exact physical dimensions, do not use `bbox_inches="tight"` unless the changed page size is intentional.

#### Color normalization

```python
import matplotlib as mpl

norm = mpl.colors.TwoSlopeNorm(vmin=-2, vcenter=0, vmax=5)
cmap = mpl.colormaps["RdBu_r"].with_extremes(bad="#777777")
image = ax.imshow(values, norm=norm, cmap=cmap, interpolation="nearest")
fig.colorbar(image, ax=ax, label="Change (unit)")
```

Use `LogNorm`, `CenteredNorm`, `SymLogNorm`, `BoundaryNorm`, or `TwoSlopeNorm` only when its mapping matches the scientific meaning.

#### Seaborn

Seaborn 0.13.2 uses the current `errorbar` API:

```python
sns.lineplot(
    data=frame,
    x="time",
    y="response",
    hue="treatment",
    style="treatment",
    markers=True,
    errorbar=("ci", 95),
    n_boot=5000,
    seed=20260723,
    ax=ax,
)
```

For repeated measurements, preserve the subject/sample identifier. To show individual trajectories, use Seaborn's `units` with `estimator=None`; this draws one line per sampling unit instead of an aggregate mean. For an aggregate uncertainty band, compute intervals using the actual independent sampling unit (for example, a subject-level bootstrap) and plot those intervals explicitly. A row-wise CI and a fixed random seed do not account for within-subject dependence. See the [relational tutorial](https://seaborn.pydata.org/tutorial/relational).

Seaborn drops missing rows before drawing lines, so it can bridge a missing observation. For visible gaps, use explicit NaNs/masks with Matplotlib or draw contiguous observed segments separately.

Axes-level functions fit custom Matplotlib layouts; figure-level functions create their own figures/facets. Do not customize Seaborn's internal artist lists as if they were

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

