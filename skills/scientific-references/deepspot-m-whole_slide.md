---
id: sciref-deepspot-m-whole-slide
name: "Scientific Ref: Whole-slide and cohort runs"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (deepspot-m): Whole-slide and cohort runs"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "deepspot whole slide"
  - "whole-slide and cohort runs"
keywords:
  - "deepspot"
  - "whole"
  - "slide"
  - "specialized"
  - "scientific"
  - "reference"
---

# Whole-slide and cohort runs

This recipe separates optional **histolab 0.7.0 tiling** (Python 3.10/3.11 and
OpenSlide) from **DeepSpot-M inference** (tested API stack on Python 3.12).
Exchange tiles plus manifests between environments. Install AnnData, NumPy, pandas
and Pillow in the inference environment for export; matplotlib is only needed to plot.
Full WSI extraction and gated inference are illustrative, not an executed clinical
or biological validation. Local synthetic checks cover the boundary logic and export.

## 1. Verify physical resolution

A 224x224 tile at 0.5 microns/pixel spans about 112x112 microns. Do not assume
level 0 is 20x or level 1 is half its resolution: pyramid factors vary by scanner.
Check both axes and reject missing/invalid metadata. This native-level example uses
an explicit 10% engineering tolerance; choose and validate that tolerance for the
study, rather than interpreting it as an established model accuracy guarantee.

```python
import math
import openslide

def select_native_level(properties, downsamples, target=0.5, tolerance=0.10):
    mpp = [float(properties.get(f"openslide.mpp-{axis}", "nan")) for axis in ("x", "y")]
    if not all(math.isfinite(v) and v > 0 for v in mpp):
        raise ValueError("Need verified positive MPP for both slide axes")
    factors = [float(v) for v in downsamples]
    if not factors or not all(math.isfinite(v) and v > 0 for v in factors):
        raise ValueError("Invalid slide pyramid downsample factors")
    level = min(range(len(factors)), key=lambda i: max(
        abs(v * factors[i] / target - 1) for v in mpp
    ))
    actual = [v * factors[level] for v in mpp]
    if any(abs(v / target - 1) > tolerance for v in actual):
        raise ValueError("No matching native level; explicitly resample from finer pixels")
    return level, mpp, actual

with openslide.open_slide("slide.svs") as raw_slide:
    level, level0_mpp, actual_mpp = select_native_level(
        raw_slide.properties, raw_slide.level_downsamples
    )
    level0_dimensions = raw_slide.dimensions
```

If no native level qualifies, stop this recipe and use a separately verified resampling
workflow. Histolab exposes `mpp=...` but that path has additional backend requirements;
it is not exercised here. Record the original metadata, source level, resampling
method and effective MPP. Upsampling coarse pixels cannot recover missing detail.

## 2. Tile and create a coordinate manifest

Use a **new, empty directory per slide/run**; stale PNGs would corrupt assembly.
The tissue mask and 80% tissue threshold are analysis choices: inspect a thumbnail
with tile outlines, especially for small fragments, sparse tissues and artifacts.
The default `BiggestTissueBoxMask` can exclude separate tissue fragments; this
example explicitly requests `TissueMask`.

```python
from pathlib import Path
from histolab.slide import Slide
from histolab.tiler import GridTiler
from histolab.masks import TissueMask

tile_dir = Path("tiles")
tile_dir.mkdir(exist_ok=False)
slide = Slide("slide.svs", processed_path=str(tile_dir))
tiler = GridTiler(
    tile_size=(224, 224), level=level, check_tissue=True,
    tissue_percent=80.0, pixel_overlap=0,
)
tiler.extract(slide, extraction_mask=TissueMask())
```

Released GridTiler 0.7.0 returns `None` and writes coordinate-bearing filenames;
it does not provide a `report_path` argument. Build this explicit manifest from
that documented naming contract. The bounds are in **level-0 pixels**.

```python
import csv
import json
import re

pattern = re.compile(r"tile_\d+_level(\d+)_(\d+)-(\d+)-(\d+)-(\d+)\.png")
rows = []
for path in sorted(tile_dir.glob("*.png")):
    match = pattern.fullmatch(path.name)
    if not match:
        raise ValueError(f"Unexpected GridTiler filename: {path.name}")
    tile_level, x0, y0, x1, y1 = map(int, match.groups())
    if tile_level != level or not (0 <= x0 < x1 <= level0_dimensions[0]
                                   and 0 <= y0 < y1 <= level0_dimensions[1]):
        raise ValueError(f"Invalid level or bounds: {path.name}")
    rows.append([path.name, x0, y0, x1, y1, tile_level])
if not rows:
    raise ValueError("No tissue tiles survived extraction")
with open("tiles_report.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["tile_name", "x0", "y0", "x1", "y1", "level"])
    writer.writerows(rows)
Path("tiling.json").write_text(json.dumps({
    "slide_id": "slide", "level": level, "level0_mpp": level0_mpp,
    "actual_mpp": actual_mpp, "coordinate_units": "level0_pixels",
    "bounds_origin": "upper_left", "tile_px": 224,
    "tissue_mask": "TissueMask", "tissue_percent": 80.0,
}), encoding="utf-8")
```

## 3. Predict in the inference environment

Use the same gene order throughout. Start with a small batch; scale only after
measuring memory for the actual gene count. This in-memory example suits marker
panels/modest slides. A full-transcriptome WSI may require chunked persistence;
`torch.cat` temporarily duplicates stored expression chunks.

```python
from pathlib import Path
import json
import torch
from PIL import Image
from deepspotm import DeepSpotM

metadata = json.loads(Path("tiling.json").read_text(encoding="utf-8"))
tile_paths = sorted(Path("tiles").glob("*.png"))
if not tile_paths:
    raise ValueError("No input tiles")
genes = ["EPCAM", "CD3D", "PTPRC", "MKI67"]
source = "scgpt"
revision = "48be27af436a50e5c74175680ac2b7b2596a506b"
device = "cuda" if torch.cuda.is_available() else "cpu"
model, image_processor = DeepSpotM.from_pretrained(
    "ratschlab/DeepSpotM", source=source, device=device, revision=revision
)
if not genes or len(genes) != len(set(genes)) or not set(genes) <= set(model.gene_names):
    raise ValueError("Use unique genes from the loaded panel")

chunks = []
batch_size = 4
for start in range(0, len(tile_paths), batch_size):
    paths = tile_paths[start:start + batch_size]
    tensors = []
    for path in paths:
        with Image.open(path) as tile:
            if tile.size != (224, 224):
                raise ValueError(f"Wrong tile dimensions: {path.name}")
            tensors.append(image_processor(tile.convert("RGB")))
    batch = torch.stack(tensors).to(device)
    values = model.predict_genes(batch, genes).cpu()
    if values.shape != (len(paths), len(genes)) or not torch.isfinite(values).all():
        raise ValueError("Unexpected prediction shape or nonfinite values")
    chunks.append(values)
expression = torch.cat(chun

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

