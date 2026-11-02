---
id: sciref-pathml-preprocessing
name: "Scientific Ref: Preprocessing pipelines, masks, stain handling, and QC"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pathml): Preprocessing pipelines, masks, stain handling, and QC"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pathml preprocessing"
  - "preprocessing pipelines, masks, stain handling, and qc"
keywords:
  - "pathml"
  - "preprocessing"
  - "specialized"
  - "scientific"
  - "reference"
  - "pipelines"
---

# Preprocessing pipelines, masks, stain handling, and QC

This reference describes **PathML 3.0.8 stable**. It corrects older examples that
called nonexistent `Pipeline.run()`, omitted required mask/label names, or passed
unsupported transform arguments.

## Pipeline execution model

A `Pipeline` is an ordered list of `Transform` objects. `Pipeline.apply(tile)`
modifies one `Tile` in place and returns it. A slide or dataset owns execution:

```python
from pathml.core import HESlide
from pathml.preprocessing import BoxBlur, Pipeline, TissueDetectionHE

slide = HESlide("data/slide-001.svs", backend="openslide")
pipeline = Pipeline(
    [
        BoxBlur(kernel_size=5),
        TissueDetectionHE(mask_name="tissue"),
    ]
)

slide.run(
    pipeline,
    distributed=False,
    tile_size=512,
    tile_stride=512,
    level=0,
    tile_pad=False,
)
```

Stable facts:

- `Pipeline(transform_sequence=None)` and `Pipeline.apply(tile)` are public.
- `Pipeline` has no `run()` method.
- `SlideData.run()` and `SlideDataset.run()` apply pipelines.
- `distributed=True` is the default and may create a local Dask cluster using
  available cores. Start with `distributed=False`.
- Existing tiles are protected unless `overwrite_existing_tiles=True`.
- `write_dir` causes a `<slide.name>.h5path` write after processing.
- `Pipeline.save()` writes a pickle. A pickle is executable on load; never use a
  pipeline file from an untrusted source.

## Stable transform imports

```python
from pathml.preprocessing import (
    AdaptiveHistogramEqualization,
    BinaryThreshold,
    BoxBlur,
    CollapseRunsCODEX,
    CollapseRunsVectra,
    ForegroundDetection,
    GaussianBlur,
    HistogramEqualization,
    LabelArtifactTileHE,
    LabelWhiteSpaceHE,
    MedianBlur,
    MorphClose,
    MorphOpen,
    NucleusDetectionHE,
    Pipeline,
    QuantifyMIF,
    RescaleIntensity,
    SegmentMIF,
    SegmentMIFRemote,
    StainNormalizationHE,
    SuperpixelInterpolation,
    TissueDetectionHE,
)
```

There is no stable `transform='...'` registry and no safe reason to construct
transforms from arbitrary Python expressions. Parse a strict allowlisted config,
then instantiate known classes explicitly.

## Tissue detection

```python
from pathml.preprocessing import TissueDetectionHE

tissue = TissueDetectionHE(
    mask_name="tissue",
    use_saturation=True,
    blur_ksize=17,
    threshold=None,          # Otsu when None
    morph_n_iter=3,
    morph_k_size=7,
    min_region_size=5000,
    max_hole_size=1500,
    outer_contours_only=False,
)
```

The transform expects an H&E `uint8` tile. It:

1. uses HSV saturation or greyscale;
2. median-blurs;
3. applies Otsu or the explicit threshold;
4. performs morphological opening and closing;
5. keeps foreground regions under the configured area/hole policy; and
6. writes `tile.masks["tissue"]`.

`mask_name` is required in practice; `None` fails when `apply()` runs.
`min_region_size`, `max_hole_size`, and morphology kernels are measured in pixels
at the processing level. Re-tune if level or MPP changes.

Tissue detection is tile-local. It can disagree at tile edges, and PathML does not
automatically remove background tiles from the pipeline. Compute and record tissue
coverage after the mask exists:

```python
coverage = float((tile.masks["tissue"] > 0).mean())
keep = coverage >= 0.50
```

Choose the coverage rule on training data and preserve rejected-tile counts.

## Whitespace and artifact QC

These transforms write **tile labels**, not pixel masks:

```python
from pathml.preprocessing import LabelArtifactTileHE, LabelWhiteSpaceHE

whitespace = LabelWhiteSpaceHE(
    label_name="mostly_white",
    greyscale_threshold=230,
    proportion_threshold=0.5,
)
artifact = LabelArtifactTileHE(label_name="artifact")
```

- `LabelWhiteSpaceHE` labels a tile when the proportion of greyscale pixels above
  the threshold exceeds `proportion_threshold`.
- `LabelArtifactTileHE` is a fixed rule-based HSI heuristic for whitespace,
  dark regions, and pen-like colors. It exposes only `label_name`; older examples
  with `pen_threshold` or `bubble_threshold` are invalid.

Neither is a complete slide-quality system. Review representative overlays and
track blur, folds, bubbles, pen, tissue coverage, clipping, color drift, missing
channels, and focus separately. Do not convert a heuristic QC flag into a clinical
quality judgment.

The dependency-free helper provides a deliberately simple synthetic/local check,
not a replacement for PathML:

```bash
python scripts/image_qc.py synthetic --width 256 --height 256
python scripts/image_qc.py inspect --image tests/fixtures/synthetic.ppm --root .
```

It reports brightness/saturation and a coarse tissue-like mask using bounded
pixels. PNG/JPEG/TIFF input needs Pillow, imported only after argument validation.

## H&E stain normalization and separation

```python
from pathml.preprocessing import StainNormalizationHE

normalizer = StainNormalizationHE(
    target="normalize",             # normalize | hematoxylin | eosin
    stain_estimation_method="macenko",  # macenko | vahadane
    optical_density_threshold=0.15,
    regularizer=0.1,
    angular_percentile=0.01,
    background_intensity=245,
)
```

Stable `StainNormalizationHE` does **not** accept `tissue_mask_name`,
`target_od`, or `target_concentrations`. It accepts `stain_matrix_target_od` and
`max_c_target`, and supplies fixed defaults.

To fit a reference:

```python
normalizer.fit_to_reference(training_reference_rgb)
normalized_rgb = normalizer.F(source_rgb)
```

Leakage controls:

- Select the reference and tune OD parameters using training slides only.
- Freeze the fitted stain matrix and target concentration before validation/test.
- Do not choose a reference because test performance looks better.
- Record source slide pseudonym, region coordinates, level, MPP, method, and all
  fitted arrays without direct identifiers.
- Fit on tissue-rich, artifact-free RGB regions. Stable API does not consume a
  tissue mask directly, so crop/filter the reference beforehand.

Macenko and Vahadane are model-based color standardization methods, not guarantees
that biological staining becomes comparable. Preserve raw inputs and assess
whether normalization removes task-relevant signal or amplifies artifacts.

## Simple H&E nucleus mask

```python
from pathml.preprocessing import NucleusDetectionHE

nuclei = NucleusDetectionHE(
    mask_name="nuclei",
    stain_estimation_method="vahadane",
    superpixel_regio

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

