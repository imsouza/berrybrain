---
id: sciref-pathml-data-management
name: "Scientific Ref: Data management, h5path, manifests, datasets, and provenance"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pathml): Data management, h5path, manifests, datasets, and provenance"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pathml management"
  - "data management, h5path, manifests, datasets, and provenance"
keywords:
  - "pathml"
  - "management"
  - "specialized"
  - "scientific"
  - "reference"
  - "path"
---

# Data management, h5path, manifests, datasets, and provenance

This reference targets **PathML 3.0.8 stable** and a local, de-identified research
workflow.

## Data boundaries

Separate four classes of data:

1. **Source slides** — immutable, access-controlled originals.
2. **Linkage data** — direct identifiers and the pseudonym mapping, held outside
   the analysis workspace by an authorized custodian.
3. **Analysis data** — pseudonymous manifests, tiles, masks, counts, graphs, and
   features.
4. **Reports/models** — potentially identifying derived artifacts that still
   require governance.

Do not assume derived images or embeddings are anonymous. Rare morphology,
scanner metadata, dates, or cohort combinations can re-identify a participant.
Apply the minimum-necessary principle and institutional retention policy.

## Manifest first

Use one row per slide. Recommended columns:

```text
slide_id,patient_id,specimen_id,path,split,stain,backend,site,scanner
```

Rules:

- IDs are pseudonyms, not MRNs, accessions, initials, dates, or names.
- `slide_id` is unique.
- one `patient_id` maps to exactly one split;
- one slide path maps to one slide ID;
- paths are local, relative to a declared root where possible;
- URLs and symlinks are rejected;
- split values are a fixed allowlist such as `train`, `validation`, `test`;
- serial sections, rescans, and multiple blocks from one patient remain together.

Validate before PathML:

```bash
python scripts/slide_manifest.py validate \
  --manifest metadata/manifest.csv \
  --root .
```

The validator checks strict CSV structure, duplicate IDs/paths, missing local
files, unsafe paths, supported suffixes, and patient/slide leakage. It does not
upload data or inspect arbitrary clinical fields.
If the `split` column is present, every row must supply it. Without that column,
the report explicitly leaves patient split isolation unchecked.

## h5path format

PathML processes slides into an HDF5-based `.h5path` file. Stable documentation
describes:

```text
root/
├── fields/
│   ├── labels/          # slide-level attributes
│   └── slide_type/      # stain/platform flags
├── masks/               # slide-level masks
├── counts/              # AnnData-like counts storage
└── tiles/
    ├── attributes       # tile_shape, tile_stride
    └── "(i, j)"/
        ├── array
        ├── masks/
        ├── labels/
        └── attributes   # coords, name
```

Write and reopen through public APIs:

```python
from pathml.core import SlideData

slide.write("derived/slide-001.h5path")
reopened = SlideData("derived/slide-001.h5path")
```

There is no stable `to_hdf5()`, `from_hdf5()`, or
`load_tiles_from_hdf5()` API. `SlideDataset.write(directory, filenames=None)`
calls each slide's `write()`.

Released `h5pathManager.add_tile()` explicitly casts both tile images and tile
masks to `float16`. Integers through 2048 are exact, but 2049 rounds to 2048 and
large values can overflow beyond 65504. Thus distinct instance IDs can merge;
intensity values can also lose precision. This is a storage limitation, even
when Bio-Formats read with `normalize=False`.

Preserve authoritative quantitative images and integer instance maps in a
separate lossless, typed format. Check actual label identity and dtype after a
small h5path round trip before downstream counting. Binary masks are not subject
to the same instance-ID loss. Record tolerances for float measurements, but
require exact equality for categorical labels.

## h5path trust boundary

Treat `.h5path` as a structured binary input, not harmless data:

- HDF5 parsers have a large attack surface; open third-party files in isolation.
- PathML 3.0.8 `TileDataset` and core h5path/tile code dynamically interpret the
  stored `tile_shape` attribute as a Python expression. Never open an untrusted
  `.h5path`, including through `SlideData`.
- Labels can contain sensitive values. Do not copy direct identifiers into HDF5.
- A malformed file can request large allocations. Check file size and schema
  before loading.
- Do not edit HDF5 concurrently from multiple processes unless the access pattern
  is explicitly designed and tested.

Use a sidecar JSON manifest for provenance rather than relying on arbitrary HDF5
labels. Keep the JSON strict, bounded, pseudonymous, and versioned.

## PyTorch tile dataset

The canonical stable import is:

```python
from pathml.datasets import TileDataset
from torch.utils.data import DataLoader

tiles = TileDataset("derived/slide-001.h5path")
loader = DataLoader(
    tiles,
    batch_size=8,
    shuffle=False,
    num_workers=0,
)
```

Each item is:

```text
(tile_image, tile_masks, tile_labels, slide_labels)
```

Shapes:

- RGB/multichannel 3-D input becomes `(C, H, W)`.
- 5-D PathML input `(i, j, z, c, t)` becomes `(T, C, Z, W, H)` in stable
  source; verify axis semantics before use.
- masks are stacked as `(n_masks, tile_height, tile_width)` when present.
- values returned by the dataset are NumPy arrays; the PyTorch loader collates
  them to tensors. Missing masks are `None`, which default collation cannot
  handle; use a custom `collate_fn` for missing masks or nonstandard labels.

`TileDataset` does not return coordinates explicitly. Keep a parallel mapping
from sample index to its stored tile key/coords (HDF5 iteration is not a numeric
row/column sort), or include validated coordinate metadata in a custom dataset.

Do not assume mask dictionary order carries semantics. Persist ordered mask names
in a separate schema and assert them when loading.

`pathml.ml.TileDataset` is also exported in 3.0.8, but
`pathml.datasets.TileDataset` is the documented dataset API.

## SlideDataset

`SlideDataset(slides)` accepts a list of already constructed `SlideData` objects:

```python
from pathml.core import HESlide, SlideDataset

slides = [
    HESlide("data/slide-001.svs", backend="openslide"),
    HESlide("data/slide-002.svs", backend="openslide"),
]
cohort = SlideDataset(slides)
cohort.run(pipeline, distributed=False, tile_size=512, level=0)
cohort.write("derived")
```

It does not accept a glob/path list plus tiling arguments as a constructor.
Preserve a deterministic manifest order and map output filenames explicitly.

## Public data modules

Stable `pathml.datasets` exports:

```python
from pathml.datasets import DeepFocusDataModule, PanNukeDataModule
```

### PanNuke

```python
pannuke = PanNukeDataModule(
    data_dir="approved_data/pannuke",
    download=False,
    shuffle=True,
    nucleus_type_label

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

