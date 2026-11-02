---
id: sciref-openpiv-advanced-algorithms
name: "Scientific Ref: Advanced OpenPIV Algorithms and Settings"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (openpiv): Advanced OpenPIV Algorithms and Settings"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "openpiv advanced algorithms"
  - "advanced openpiv algorithms and settings"
keywords:
  - "openpiv"
  - "advanced"
  - "algorithms"
  - "specialized"
  - "scientific"
  - "reference"
---

# Advanced OpenPIV Algorithms and Settings

Reviewed against the released **openpiv 0.26.1** source and SciPy runtime on 2026-10-01.
Hosted documentation can lag the wheel; for example its API listing omits the new `backend` argument.

## Correlation methods

`pyprocess.extended_search_area_piv(..., correlation_method=...)`:

| Value | Behaviour |
|-------|-----------|
| `"circular"` (default) | FFT correlation with no zero-padding. Fastest and lowest memory. Wrap-around means a displacement past half the window aliases back as a small one in the opposite direction. |
| `"linear"` | FFT padded to a power of two covering the full correlation, then cropped back to search-window size. Reduces wrap-around; displacement range is still limited by that crop and particle overlap. |

Use these two names. `"direct"` appears in some legacy docstrings but is not implemented by the
SciPy `extended_search_area_piv` correlation path. Do not offer it as an option.

Both methods support extended search; larger extreme velocities alone do not establish aliasing.
The bundled CLI chooses `"linear"` with `normalized_correlation=True` for extended windows,
following the API's normalization requirement. Validate either choice using known displacements.

`normalized_correlation=True` normalizes intensities per window before correlating, making peak
heights comparable across windows of differing brightness — useful under uneven illumination. It also
shifts the `s2n` scale, so re-tune the threshold after switching it on.

`use_vectorized=True` batches peak extraction and signal-to-noise calculations. Both paths already
hold the correlation stack; edge/degenerate peak behavior can differ. It remains False in
`extended_search_area_piv`, but `PIVSettings.use_vectorized` defaults to True since 0.25.5.

`backend="scipy"` selects the tested reference path. `"auto"` can use installed Rust components;
in 0.26.1 the FFT dispatcher still selects SciPy unless `"rust"` is explicit. `"rust"` requires
`openpiv_rust` and raises ImportError when absent. Record backend and package versions; do not
assume every wheel contains the extension or infer speed/numerical parity from release notes.

## Subpixel peak fitting

`subpixel_method` selects how the integer correlation peak is refined:

| Value | Notes |
|-------|-------|
| `"gaussian"` (default) | Three-point Gaussian fit per axis. Standard choice; biased toward integer values ("peak locking") when particle images are under 2 px. |
| `"parabolic"` | Three-point parabolic fit. Cheaper, slightly less accurate for Gaussian particle images. |
| `"centroid"` | Intensity-weighted centroid. More robust for wide or saturated peaks. |

Peak locking is a particle-imaging problem, not a fitting problem: aim for 2–3 px particle image
diameter rather than switching estimators.

## Signal-to-noise measures

`pyprocess.sig2noise_ratio(correlation, sig2noise_method="peak2peak", width=2)`:

- `"peak2mean"` — first peak divided by the mean of the correlation map. This is the default of both
  `extended_search_area_piv` and `PIVSettings`. Values run higher and depend on map size.
- `"peak2peak"` — first peak divided by the second-highest peak, excluding a `width`-pixel
  neighbourhood around the first. The classic PIV detectability ratio; usable thresholds are
  ~1.05–1.3.

The two scales are not interchangeable. A threshold copied from one to the other silently rejects
everything or nothing.

## Multi-pass window deformation (`openpiv.windef`)

`windef.simple_multipass(frame_a, frame_b, settings)` runs the full loop:

1. `windef.first_pass` — coarse correlation on `windowsizes[0]`.
2. `validation.typical_validation` — applies every enabled check in `settings` at once.
3. `filters.replace_outliers` — fills flagged vectors.
4. `windef.multipass_img_deform` for iterations `1 .. num_iterations-1` — deforms the interrogation
   windows using the previous pass as a predictor, then re-correlates on the next smaller window.
5. Remaining NaNs filled with zeros; `transform_coordinates` applied.

It returns `(x, y, u, v, flags)` with coordinates in pixels and velocities in **pixels per frame**.
`simple_multipass` (and alias `multigrid_windef`) ignore `settings.dt` and
`settings.scaling_factor`; convert afterwards:

```python
x, y, u, v = scaling.uniform(x, y, u, v, scaling_factor=96.52)
u, v = u / dt, v / dt      # scaling.uniform does not divide by dt
```

Batch `windef.piv(settings)` does apply both before saving. The array convenience wrapper always
validates/replaces the first pass, does not perform the batch image preprocessing or between-pass
smoothing, and discards the final masked-array mask when returning `.data`. For masks, full switch
control, and preserved quality information use the batch pipeline or manage lower-level passes.
Always supply settings: the no-settings wrapper resets window lists to two entries but leaves
`num_iterations=3`. Construction checks list lengths and overlap; changing attributes bypasses those
checks, and the number of iterations must still match the requested passes.

The upside of working in px/frame is that the validation defaults (`min_max_u_disp=(-30, 30)`,
`median_threshold=3`) are stated in px/frame and therefore mean what the PIV literature says they
mean. The same numbers applied to `extended_search_area_piv` output, which *has* been divided by
`dt`, would reject the whole field.

`deformation_method="symmetric"` (the default) deforms both frames toward the midpoint, which halves
the interpolation bias of deforming only the second frame. `interpolation_order` (default 3) is the
spline order used for that deformation.

Window deformation is what makes multi-pass worth the cost: it handles velocity gradients within a
window, which a fixed-window single pass cannot.

## `PIVSettings` reference

`windef.PIVSettings()` is a dataclass. Prefer constructor keywords so its consistency checks run.
This table describes batch settings; do not assume the simple array wrapper uses every field.

**Input and region**

| Field | Default | Meaning |
|-------|---------|---------|
| `filepath_images`, `save_path`, `frame_pattern_a`, `frame_pattern_b` | OpenPIV's bundled `data/test1` | Batch-mode paths; irrelevant when calling `simple_multipass` with arrays |
| `roi` | `"full"` | `"full"` or `(y1, y2, x1, x2)` crop |
| `invert` | `False` | Invert intensities, for dark particles on a bright background |

**Masking**

| Field | Default | Meaning |
|-------|---------|-------

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

