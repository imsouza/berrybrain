---
id: sciref-pathml-image-loading
name: "Scientific Ref: Image loading, formats, levels, and coordinates"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pathml): Image loading, formats, levels, and coordinates"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pathml image loading"
  - "image loading, formats, levels, and coordinates"
keywords:
  - "pathml"
  - "image"
  - "loading"
  - "specialized"
  - "scientific"
  - "reference"
---

# Image loading, formats, levels, and coordinates

This reference targets the **PyPI-stable PathML 3.0.8 API**. All sources were
checked on 2026-10-01 against the v3.0.8 wheel/tag. PathML examples are
illustrative: native readers were not executed in this review.

## Start with a local, de-identified file

Never infer authorization from the fact that a file is readable. Whole-slide
images and DICOM objects can carry identifiers in pixels, labels, filenames, and
metadata. Keep the original on approved storage, use a pseudonymous working name,
and do not print arbitrary metadata. The bundled inspector emits only an
allowlist of technical fields:

```bash
python scripts/slide_manifest.py inspect \
  --slide data/pseudonymous_slide.svs \
  --root .
```

It rejects URLs and symlinks. PathML itself accepts paths more broadly, so validate
before constructing a slide object.

## Stable slide classes

```python
from pathml.core import (
    CODEXSlide,
    HESlide,
    IHCSlide,
    MultiparametricSlide,
    SlideData,
    SlideDataset,
    VectraSlide,
    types,
)
```

Convenience classes pass a stable `SlideType`:

- `HESlide(...)` → `types.HE`
- `IHCSlide(...)` → `types.IHC`
- `MultiparametricSlide(...)` → `types.IF`, Bio-Formats by default
- `VectraSlide(...)` → `types.Vectra`, Bio-Formats by default
- `CODEXSlide(...)` → `types.CODEX`, Bio-Formats by default

The generic constructor is:

```python
slide = SlideData(
    "data/pseudonymous_slide.svs",
    name="slide-001",
    backend="openslide",
    slide_type=types.HE,
)
```

`SlideData.from_slide()`, `read_region()`, `level_dimensions`, and
`level_downsamples` are not stable `SlideData` APIs. Use the constructor,
`extract_region()`, `shape`, and backend-specific objects where necessary.

For a local cohort, instantiate slides first:

```python
from pathlib import Path
from pathml.core import HESlide, SlideDataset

root = Path("data/slides")
paths = sorted(root.glob("*.svs"))
slides = [HESlide(path, backend="openslide", name=path.stem) for path in paths]
dataset = SlideDataset(slides)
```

Do not recursively accept arbitrary user-controlled paths. Validate a manifest,
freeze the patient split, and then build this list.

## Backends and file types

### OpenSlide

Use `backend="openslide"` for common brightfield pyramid formats. Stable PathML
lists:

`.svs`, `.tif`, `.tiff`, `.bif`, `.ndpi`, `.vms`, `.vmu`, `.scn`, `.mrxs`,
and `.svslide`.

The complete capability depends on the installed OpenSlide build and the vendor
subtype, not only the suffix. Some generic TIFFs are not valid WSIs, and some
files with a supported suffix use unsupported compression.

Native OpenSlide is required. Official PathML guidance uses
`openslide-tools` on Debian/Ubuntu, Homebrew `openslide` on macOS, and vcpkg or
official prebuilt binaries on Windows.

### Bio-Formats

Use `backend="bioformats"` for multidimensional microscopy, OME-TIFF, QPTIFF, and
formats OpenSlide cannot read. Bio-Formats supports a large catalogue (the
upstream examples describe 160+ formats), including `.ome.tif`, `.ome.tiff`,
`.qptiff`, `.czi`, `.vsi`, `.zvi`, and many laboratory formats.

This backend requires Java, `python-bioformats`, and `python-javabridge`. It
starts a JVM and stable source configures a large maximum heap, so isolate and
resource-limit untrusted images. Java has an approximately 2 GB array limit in
the backend. A listed extension is not proof that every variant loads.

Bio-Formats returns five-dimensional arrays in PathML order:

`(i, j, z, channel, time)` = `(row, column, z, c, t)`.

Even singleton `z` and `time` dimensions are retained until a transform such as
`CollapseRunsCODEX` or `CollapseRunsVectra` changes the layout.

`extract_region(..., normalize=True)` is the default. It divides by
`2**(8 * source_dtype.itemsize)`, multiplies by 256, then casts to `uint8`.
This loses high-bit-depth intensity precision and is not a valid generic
normalization for signed/floating-point acquisitions. For quantification use
`normalize=False` in `extract_region`, `generate_tiles`, or `SlideData.run`
(forwarded through `**kwargs`), and verify dtype/range with known pixels.
This preserves the read values in memory; h5path storage has a separate float16
conversion described in `data_management.md`.

### DICOM

Use `backend="dicom"` for `.dcm` or `.dicom`. Stable PathML treats DICOM frames as
tiles. DICOM metadata is especially likely to contain PHI; de-identify with an
approved DICOM process before PathML, preserve required UIDs consistently, and
never dump the full dataset to logs.

### h5path

`.h5` and `.h5path` inputs are inferred as PathML's processed HDF5 format:

```python
from pathml.core import SlideData

processed = SlideData("derived/slide-001.h5path")
```

There is no stable `from_hdf5()` constructor. See `data_management.md`.

## Backend inference versus explicit selection

If `backend=None`, PathML infers a backend from the suffix. Prefer an explicit
backend in reproducible work:

```python
from pathml.core import HESlide

slide = HESlide("data/slide-001.svs", backend="openslide")
```

Reasons to be explicit:

- `.tif` can mean a brightfield pyramid, OME-TIFF, or a plain raster.
- Bio-Formats is broader but slower and starts Java.
- Backend metadata and pyramid interpretation differ.
- A file renamed to a recognized suffix is not thereby valid.

## Shape, regions, and tile generation

`slide.shape` returns `(height, width)` for the backend's default level.

```python
height, width = slide.shape

region = slide.extract_region(
    location=(2_000, 3_000),  # (i, j) = (row, column)
    size=(512, 768),          # (height, width)
    level=1,
)

tiles = slide.generate_tiles(
    shape=(512, 512),
    stride=(256, 256),
    pad=False,
    level=1,
)
```

`generate_tiles()` is lazy. Do not materialize all tiles just to count them.
Use the bounded planner first:

```bash
python scripts/plan_pipeline.py \
  --width 100000 --height 80000 \
  --tile-size 512 --stride 256 \
  --level-downsample 4 \
  --level-width 25000 --level-height 20000
```

The level dimensions above are illustrative; supply values read from your file.

`SlideData.run()` uses different parameter names: `tile_size`, `tile_stride`,
`tile_pad`, and `level`.

## Coordinate convention

PathML's `Tile.coords` is the top-left `(i, j)`:

- `i`: row / vertical / image `y`
- `j`: column / horizontal / image `x`
- origin: top-left pixel `(0, 0)`
- units: pixels at the **selected pyramid level**

For OpenSl

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

