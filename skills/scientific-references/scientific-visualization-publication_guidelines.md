---
id: sciref-scientific-visualization-publication-guidelines
name: "Scientific Ref: Publication Figure Principles"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-visualization): Publication Figure Principles"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific visualization publication guidelines"
  - "cientifico visualization publication guidelines"
  - "publication figure principles"
keywords:
  - "scientific"
  - "visualization"
  - "publication"
  - "guidelines"
  - "cientifico"
  - "specialized"
  - "reference"
---

# Publication Figure Principles

Reviewed 2026-10-01. These are general scientific-communication principles, not publisher requirements. Date-sensitive rules belong in `journal_requirements.md`. Source IDs resolve in `sources.md`.

## Preserve evidence before styling

Keep three layers separate:

1. **Raw/source data**: immutable originals, acquisition metadata, exclusions, and missing-value codes.
2. **Transformation record**: executable code or a machine-readable log of filtering, normalization, aggregation, statistical estimation, image processing, and random seeds.
3. **Presentation output**: the figure and an export manifest recording dimensions, format, package versions, and source references.

Do not overwrite raw images or tabular data. Keep native-resolution images. Upsampling changes pixel count, not information; PLOS, Science, Nature, Cell Press, Elsevier, and IEEE explicitly warn against treating it as improved quality [PLOS-FIG] [SCIENCE-REVISED] [NATURE-FINAL] [CELL-FIG] [ELSEVIER-SIZE] [IEEE-SIZE].

For experimental/observational images:

- Apply necessary brightness, contrast, and color adjustments consistently to the whole image unless a disclosed scientific method requires otherwise.
- Never selectively erase, obscure, clone, or enhance features.
- Preserve background and nonspecific signal.
- Mark and explain splices, omitted lanes, composites, or stitched fields.
- Retain originals and the exact processing steps. Some publishers request originals during review or production [CELL-FIG] [PLOS-FIG].

The bundled exporter can write a provenance manifest, but it cannot confirm that supplied provenance is complete.

## Avoid visual deception

### Baselines and context

- **Bars and filled areas encode length/area from a baseline**: normally show the zero baseline. If a nonzero reference is scientifically meaningful, make that reference explicit and avoid implying absolute magnitude.
- **Points and lines encode position**: a nonzero axis limit can be valid, but show enough context, disclose breaks, and avoid choosing limits solely to magnify a small effect.
- Use common limits for panels intended for direct comparison. If limits differ, make the difference unmistakable.
- Do not extend axes far beyond observed data merely to suppress visible variation; Science explicitly advises that scales not extend beyond plotted data [SCIENCE-INITIAL].

### Uncertainty and raw observations

- Do not add error bars mechanically. Show uncertainty when an estimate is displayed, and show spread when the distribution is the question.
- Name the interval precisely: SD, SE, percentile interval, parametric CI, bootstrap CI, posterior interval, or another definition.
- State sample size, unit of replication, estimator, interval level, and dependence/repeated-measure handling.
- Use deterministic seeds for bootstrap displays. Seaborn 0.13.2 supports `errorbar="sd"`, `"se"`, `"pi"`, `"ci"`, tuples such as `("ci", 95)`, or a callable; bootstrap results vary unless `seed` is set [SEABORN-ERROR].
- Show raw observations when feasible. Do not jitter points so far that their category or value becomes ambiguous.
- Significance stars are not uncertainty. Add them only for a reported analysis, identify the test and multiplicity handling, and provide exact values where practical.

### Missing, excluded, and censored data

- Keep missing values distinct from zero, below-detection-limit values, and excluded observations.
- Do not silently connect across missing time points. Use a gap, explicit interpolation style, or a model curve whose status is stated.
- Give missing values a dedicated legend entry or neutral `bad` colormap color.
- Record exclusions and their rationale outside the plotting code as well as in the caption/methods.

### Area, volume, and 3D encodings

- Prefer position on a common scale.
- If area represents magnitude, scale **area**, not radius. If volume represents magnitude, scale volume, not diameter.
- Avoid perspective 3D bars, pies, and surfaces for simple comparisons; occlusion and perspective distort values.
- If a true 3D scientific structure is necessary, add orthogonal views, scale/orientation cues, and accessible alternatives.

### Logarithms and other transforms

- Label the transformed scale and base. Say whether values, axes, or model outputs were transformed.
- A logarithmic axis requires a declared policy for zero and negative values; never silently discard them.
- Interpret equal distances as ratios, not additive differences.
- For signed data around zero, consider `SymLogNorm`/a symmetric log axis with a disclosed linear region; for unequal ranges around a meaningful center, consider `TwoSlopeNorm` [MPL-NORM].
- Power-law or arbitrary transforms need strong justification and conspicuous disclosure. Matplotlib itself notes that viewers are less familiar with power normalization [MPL-NORM].

### Binning, smoothing, and aggregation

- Record bin edges, inclusion convention, bandwidth/window, smoothing method, and whether choices were made before seeing the result.
- Show sensitivity to reasonable bin or bandwidth choices when conclusions depend on them.
- Do not use interpolation or smoothing to imply observations between measured points.
- Preserve and, where practical, expose underlying observations.

### Normalization and color limits

- State the formula and reference: per-capita, percent of baseline, z-score axis, library-size factor, min-max range, or other transformation.
- Fit normalization parameters on the appropriate data partition; avoid information leakage.
- Use the same normalization and color limits across directly compared panels unless the difference is explicit.
- A diverging map needs a scientifically meaningful center. `Normalize`, `LogNorm`, `CenteredNorm`, `SymLogNorm`, `TwoSlopeNorm`, and `BoundaryNorm` encode different assumptions [MPL-NORM].
- Always label colorbars with units and transformed scale.

### Dual axes

Prefer aligned panels or normalized/common-unit displays. Dual y-axes can make unrelated series appear correlated because each range can be tuned independently. If unavoidable:

- justify the shared x-domain and distinct units;
- label each axis and series directly;
- avoid matching colors as the only association cue;
- choose limits independently of the desired visual relationship;
- provide the underlying data.

### Image contrast and channels

- Inspect histograms and clipped-pixel counts before and after adjustment.
- Apply c

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

