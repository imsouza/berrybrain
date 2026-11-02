---
id: sci-pathml
name: "Scientific: pathml"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Supports local computational pathology research with PathML: slide loading and tiling, preprocessing and QC, h5path storage, multiplex quantification, spatial graphs, and bounded model inference. Use for whole-slide H&E, CODEX, Vectra, Mesmer, HoVer-Net, and HACTNet workflows."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "pathml"
keywords:
  - "pathml"
  - "supports"
  - "local"
  - "computational"
  - "pathology"
  - "research"
---

# PathML

## Scope and safety boundary

Use PathML for **local computational pathology research**. It is beta research
software, not a validated medical device, diagnostic system, clinical decision
support tool, or substitute for a pathologist. Do not use outputs to diagnose,
grade, stage, or treat a patient.

Pathology files may contain faces, labels, accession numbers, patient identifiers,
DICOM tags, filenames, or linked clinical data. Before processing:

1. Confirm authorization, consent/waiver, data-use terms, and institutional policy.
2. De-identify pixels and metadata; keep the re-identification key outside the
   analysis workspace.
3. Use pseudonymous `patient_id`, `slide_id`, and `specimen_id` values. Do not put
   direct identifiers in filenames, logs, `.h5path` labels, model cards, or reports.
4. Keep inputs, intermediates, and outputs on approved local encrypted storage.
5. Split by patient (then slide) before tiling or fitting any preprocessing step.

## Version baseline, reviewed 2026-10-01

- **Published stable release:** PyPI `pathml==3.0.8`, published 2026-08-14,
  source tag `v3.0.8` (`fa49ffb66757ed8a8265756c92b6290834eddecb`).
- The v3.0.5 release notes state Python **3.10-3.12** and sunset 3.9.
  PyPI does not declare `Requires-Python` and still has a stale 3.8 classifier, so
  use the release statement and test the exact environment.
- The current wheel incorporates the Torch/PyG dependency updates and explicit
  legacy ONNX export (`dynamo=False`). ReadTheDocs pages/search caches can show
  different versions; the 3.0.8 wheel and tagged source determine these APIs.
- Bundled CLIs are tested with synthetic data. PathML examples and installation
  commands are **illustrative, source-checked**, not a full native-stack or
  pathology-model execution claim. No slides, model weights, or datasets were
  downloaded for this review.
- This skill is MIT-licensed. PathML itself is GPL-2.0 with upstream commercial
  licensing options; review upstream terms before redistribution.

## Reproducible installation

Use Python 3.11 unless the project has tested another supported interpreter:

```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip install "pathml==3.0.8"
python -c "import importlib.metadata as m; print(m.version('pathml'))"
```

PathML 3.0.8 declares no package extras: do **not** use `pathml[all]`. Its base
distribution pins a large scientific/ML stack, including Torch 2.12.0, ONNX 1.22.0,
ONNX Runtime 1.17.x, OpenSlide Python 1.3.1, python-bioformats 4.1.0, and
python-javabridge 4.0.4, torch-geometric 2.8.0, and onnxscript 0.7.1. It also pins
NumPy below 2 and several older binary packages; do not upgrade them independently.

Install native prerequisites before the uv command:

```bash
# Debian/Ubuntu
sudo apt-get install openslide-tools gcc g++ libblas-dev liblapack-dev openjdk-17-jdk

# macOS
brew install openslide openjdk@17

# Windows OpenSlide option documented upstream
vcpkg install openslide
```

`python-javabridge==4.0.4` is source-only on PyPI and needs a **JDK** (including
`javac`/JNI headers), not just a JRE. Set `JAVA_HOME` to that JDK before building.
PathML imports the Java bridge/Bio-Formats in its shared backend module even when
the requested reader is OpenSlide; selecting OpenSlide does not avoid those
installation dependencies. Old import-error advice mentioning Java 8 and
`javabridge==1.0.19` does not match the released wheel requirements.

Java/Bio-Formats provides the broad multidimensional format backend.
OpenSlide handles common brightfield WSI formats more efficiently. CUDA is
optional and must match the pinned PyTorch build; follow PyTorch's platform
selector rather than guessing a CUDA wheel. See `references/image_loading.md`.

## Stable minimal workflow

PathML 3.0.8 uses slide convenience classes and `SlideData.run()`. It does not
provide `SlideData.from_slide()`, and `Pipeline` does not have `run()`:

```python
from pathml.core import HESlide
from pathml.preprocessing import BoxBlur, Pipeline, TissueDetectionHE

slide = HESlide("data/pseudonymous_slide.svs", backend="openslide")
pipeline = Pipeline(
    [
        BoxBlur(kernel_size=5),
        TissueDetectionHE(mask_name="tissue", min_region_size=5000),
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
slide.write("derived/pseudonymous_slide.h5path")
```

Start with a bounded manual sample before a full run:

```python
from itertools import islice

for tile in islice(slide.generate_tiles(shape=512, stride=512, level=0), 8):
    pipeline.apply(tile)
    assert tile.masks["tissue"].shape[:2] == tile.image.shape[:2]
```

Tiles use `(i, j)` = `(row, column)` coordinates at the selected pyramid level.
PathML 3.0.8 truncates OpenSlide's downsample to an integer when locating a region.
Use level 0 or an exactly integral downsample; a fractional downsample can shift
the sampled region. Record level, actual dimensions and MPP before converting to
`(x, y)` or micrometres. See `references/image_loading.md`.

Before comparing tile features, cell distances, or areas across scanners, validate
level-0 MPP separately for X and Y. Equal pixel tile sizes need not cover equal
physical areas, and OpenSlide MPP may be absent or inaccurate. Keep results in
pixel units when calibration is unknown, or document a validated calibration;
do not infer it from objective magnification alone. See [OpenSlide properties](https://openslide.org/docs/properties/).

## Research workflow

1. **Inventory locally.** Validate the manifest, reject URLs/symlinks, inspect only
   allowlisted technical metadata, and remove identifiers.
2. **Freeze splits.** Assign every patient and all their slides to one split before
   generating overlapping tiles, graphs, normalization references, or features.
3. **Plan bounds.** Estimate tile count, RAM, output size, and pipeline stages.
4. **Pilot preprocessing.** Inspect tissue masks, whitespace/artifact labels,
   stain behavior, edge padding, and empty-mask cases on representative training
   slides. Do not tune from test slides.
5. **Run and preserve coordinates.** Keep tile level, `(i, j)`, downsample, MPP,
   mask names, QC decisions, and failed/skipped tiles.
6. **Build spatial data deliberately.** Validate channel order, physical units,
   instance labels, node-feature alignment, graph edges, and cell-to-tissue
   assignments.
7. **Infer in bounded batches.** Verify model provenance and 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

