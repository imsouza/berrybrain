---
id: sciref-pathml-multiparametric
name: "Scientific Ref: Multiparametric imaging, spatial data, and Mesmer integration"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pathml): Multiparametric imaging, spatial data, and Mesmer integration"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pathml multiparametric"
  - "multiparametric imaging, spatial data, and mesmer integration"
keywords:
  - "pathml"
  - "multiparametric"
  - "specialized"
  - "scientific"
  - "reference"
  - "imaging"
---

# Multiparametric imaging, spatial data, and Mesmer integration

This reference targets **PathML 3.0.8 stable**. It distinguishes generic loading
support from a dedicated analysis implementation and corrects older examples that
invented MERFISH decoders, spectral unmixing options, named-channel arguments, or
a DeepCell cloud prediction endpoint.

## Stable slide types and array order

```python
from pathml.core import CODEXSlide, MultiparametricSlide, VectraSlide

codex = CODEXSlide(
    "data/codex_region.tif",
    name="slide-001",
    backend="bioformats",
)
vectra = VectraSlide(
    "data/vectra_component_data.tif",
    name="slide-002",
)
generic = MultiparametricSlide(
    "data/multiplex.ome.tiff",
    name="slide-003",
)
```

Bio-Formats returns PathML arrays as:

```text
(i, j, z, c, t) = (row, column, z-plane, channel, time/cycle)
```

Generic Bio-Formats support means a format may be readable. It does not mean
PathML implements registration, decoding, spectral unmixing, compensation,
autofluorescence correction, cell phenotyping, or platform-specific QC for that
format.

Stable PathML has convenience classes for CODEX and Vectra. It can load examples
of MERFISH/Visium-like image data through generic backends, but it has no
`MERFISHSlide`, `DecodeMERFISH`, or `AssignTranscripts` stable API.

## Channel manifest

Create a local, versioned channel manifest before processing:

```text
channel_index,channel_name,marker,cycle,z_plane,role,exposure,batch
0,DAPI,DAPI,0,2,nuclear,100,run-01
1,CD45,CD45,0,2,membrane,150,run-01
2,CD3,CD3,1,2,measurement,200,run-01
```

Validate:

- channel index is zero-based, unique, and matches array order;
- DAPI/nuclear and membrane/cytoplasm choices are biologically and technically
  appropriate;
- cycle and Z-plane mappings are documented;
- blank, autofluorescence, isotype, and positive controls are identified;
- saturation, clipping, hot pixels, bleed-through, exposure, registration, and
  missing channels are assessed;
- marker names are not inferred from position alone.

Do not include patient names, accession numbers, or other direct identifiers.

## CODEX collapse

Stable signature:

```python
from pathml.preprocessing import CollapseRunsCODEX, Pipeline

pipeline = Pipeline([CollapseRunsCODEX(z=2)])
```

`CollapseRunsCODEX(z)` expects `(i, j, z, c, t)`, combines `c` and `t` into one
channel axis, selects the zero-based Z-plane, and produces `(i, j, c*t)`.

It does **not**:

- register cycles;
- choose a focal plane automatically;
- subtract background;
- reorder markers from a manifest;
- aggregate with max/mean/median; or
- correct illumination or bleed-through.

Perform and validate those operations upstream with a protocol appropriate to the
acquisition system. Record the exact flattened `(cycle, channel) → output index`
mapping.

The actual C-order reshape maps `(channel, cycle)` to
`output_index = channel * n_cycles + cycle` (cycle varies fastest). Verify it
with a channel-coded synthetic array; do not assume cycle-major order. The
released Z-index assertion checks the flattened channel axis by mistake, so
validate `0 <= z < image.shape[2]` yourself before calling it.

## Vectra collapse

Stable signature:

```python
from pathml.preprocessing import CollapseRunsVectra

collapse = CollapseRunsVectra()
```

It applies `numpy.squeeze` to coerce the image toward `(i, j, c)`. It does not
accept wavelengths and does not perform spectral unmixing or autofluorescence
correction. Supply already unmixed component data or perform those steps with
validated upstream software. Verify that squeezing singleton axes did not remove
an axis whose semantics must be retained.

## Segmentation choices

### Preferred no-network posture

For sensitive images, use an institution-approved local segmenter with a
reviewed, checksummed local model and network disabled. PathML's generic local
ONNX `Inference` can run compatible models, but Mesmer-specific pre/postprocessing
must match the model card exactly.

PathML 3.0.8 has no fully offline, nondeprecated Mesmer convenience class that
accepts a pre-provisioned model without trying a network download. Plan this
constraint before choosing PathML's Mesmer wrapper.

### `SegmentMIFRemote`: local inference after a model download

Stable signature:

```text
SegmentMIFRemote(
    model_path="temp.onnx",
    nuclear_channel=<integer index>,
    cytoplasm_channel=<integer index>,
    image_resolution=0.5,
    preprocess_kwargs=None,
    postprocess_kwargs_nuclear=None,
    postprocess_kwargs_whole_cell=None,
)
```

Despite the name, v3.0.8 does not send images to a DeepCell prediction service.
At construction it performs an HTTP GET from:

```text
https://huggingface.co/pathml/test/resolve/main/mesmer.onnx
```

It writes the response to `temp.onnx`, loads that ONNX model, and runs pixels
locally with ONNX Runtime. The outbound request discloses ordinary connection
metadata (for example IP address and request headers) to Hugging Face; image
pixels, channel data, and PathML metadata are not uploaded by this stable source.

Security and reproducibility limitations:

- construction has a network side effect;
- there is no built-in checksum, signature, offline flag, timeout, or size cap;
- inherited `local=False` forces `temp.onnx`, even if `SegmentMIFRemote` receives
  a different `model_path`; a supplied destination does not prevent overwriting
  that working-directory file;
- the model supports 256×256 input and 0.5 µm/pixel in stable code;
- `nuclear_channel` and `cytoplasm_channel` are integer indices, not names.

Validate HWC input (despite a contradictory channel-first wrapper docstring),
both spatial dimensions equal to 256, distinct valid channel indices, and
0.5 µm/pixel before constructing/running the wrapper. The source only prints for
other resolutions and its shape check uses `and`, so one incorrect spatial axis
can escape that check; it does not resample to the model resolution for you.

Do not instantiate it until the user explicitly consents to that endpoint and
download. Do not use it in a network-disabled workflow.

On 2026-10-01 the public Hugging Face model metadata listed both artifacts and
HEAD requests followed download redirects successfully (Mesmer 104,218,552 bytes;
HoVer-Net test model 151,068,601 bytes). These were unauthenticated metadata/HEAD
probes only, not weight downloads, checksum verification, or inference tests.

### Deprecated `SegmentMIF`

`SegmentMIF` imports `deepcell.applicat

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

