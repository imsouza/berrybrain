---
id: sciref-pydicom-transfer-syntaxes
name: "Scientific Ref: Transfer syntaxes, pixel plugins, and encapsulation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pydicom): Transfer syntaxes, pixel plugins, and encapsulation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pydicom transfer syntaxes"
  - "transfer syntaxes, pixel plugins, and encapsulation"
keywords:
  - "pydicom"
  - "transfer"
  - "syntaxes"
  - "specialized"
  - "scientific"
  - "reference"
---

# Transfer syntaxes, pixel plugins, and encapsulation

Transfer Syntax UID `(0002,0010)` identifies the encoding rules for the
dataset, including VR encoding, byte order, and pixel compression. This guide
targets stable pydicom 3.0.2. Always use the applicable DICOM PS3.5/PS3.6 and
the deployment's conformance statements for interoperability decisions. Snippets
with file paths, `encoded_frames`, or callback placeholders are illustrative;
repository tests exercise these APIs with small synthetic data.

## Inspect before decoding

```python
from pydicom import dcmread

ds = dcmread(
    "authorized/image.dcm",
    stop_before_pixels=True,
    specific_tags=[
        "Rows",
        "Columns",
        "NumberOfFrames",
        "SamplesPerPixel",
        "BitsAllocated",
        "BitsStored",
        "PhotometricInterpretation",
    ],
)
ts = ds.file_meta.TransferSyntaxUID
technical = {
    "uid": str(ts),
    "name": ts.name,
    "compressed": ts.is_compressed,
    "implicit_vr": ts.is_implicit_VR,
    "little_endian": ts.is_little_endian,
}
```

Do not infer decoder support from the UID name. Run:

```bash
python scripts/transfer_syntax_inspector.py --input authorized/image.dcm
python scripts/pixel_frame_planner.py authorized/image.dcm --frames 0
```

Plugin availability is not proof that a particular codestream, bit depth,
color representation, or platform is handled correctly.

## Native and dataset-compressed transfer syntaxes

| Name | UID | Encoding | pydicom constant |
|---|---|---|---|
| Implicit VR Little Endian | 1.2.840.10008.1.2 | implicit VR, little endian | `ImplicitVRLittleEndian` |
| Explicit VR Little Endian | 1.2.840.10008.1.2.1 | explicit VR, little endian | `ExplicitVRLittleEndian` |
| Deflated Explicit VR Little Endian | 1.2.840.10008.1.2.1.99 | deflated dataset | `DeflatedExplicitVRLittleEndian` |
| Explicit VR Big Endian | 1.2.840.10008.1.2.2 | explicit VR, big endian; retired | `ExplicitVRBigEndian` |

Explicit VR Big Endian was retired in 2006 and should not be selected for new
objects. pydicom can read it, but endianness conversion when writing is not an
automatic `Dataset.save_as()` operation.

The default DICOM network Transfer Syntax is Implicit VR Little Endian. This is
not a recommendation to omit File Meta Information from files.

## Encapsulated image transfer syntaxes

| Family | Name | UID | Loss |
|---|---|---|---|
| JPEG | JPEG Baseline 8-bit | 1.2.840.10008.1.2.4.50 | lossy |
| JPEG | JPEG Extended 12-bit | 1.2.840.10008.1.2.4.51 | lossy |
| JPEG | JPEG Lossless Process 14 | 1.2.840.10008.1.2.4.57 | lossless |
| JPEG | JPEG Lossless Process 14 SV1 | 1.2.840.10008.1.2.4.70 | lossless |
| JPEG-LS | JPEG-LS Lossless | 1.2.840.10008.1.2.4.80 | lossless |
| JPEG-LS | JPEG-LS Near-Lossless | 1.2.840.10008.1.2.4.81 | near-lossless |
| JPEG 2000 | JPEG 2000 Lossless Only | 1.2.840.10008.1.2.4.90 | lossless |
| JPEG 2000 | JPEG 2000 | 1.2.840.10008.1.2.4.91 | lossless or lossy in DICOM; pydicom encoding treats it as lossy |
| HTJ2K | HTJ2K Lossless | 1.2.840.10008.1.2.4.201 | lossless |
| HTJ2K | HTJ2K RPCL Lossless | 1.2.840.10008.1.2.4.202 | lossless |
| HTJ2K | HTJ2K | 1.2.840.10008.1.2.4.203 | lossy/lossless by syntax rules |
| RLE | RLE Lossless | 1.2.840.10008.1.2.5 | lossless |

In pydicom 3.0, `JPEGLossless` is `.57`; use `JPEGLosslessSV1` for `.70`.

Video, JPIP-referenced, encapsulated uncompressed, JPEG XL, and other current
DICOM transfer syntaxes exist but are not all decoded by pydicom's pixel API.
Consult PS3.6 and the installed `get_decoder()` result instead of assuming that
all registered UIDs are supported.

## Stable 3.0.2 decompression plugins

The pydicom 3.0.2 `pixels` backend and plugin source expose these main choices
(the older general handler guide includes legacy backend entries):

| Transfer-syntax family | Typical pydicom plugin dependencies |
|---|---|
| Native/deflated | pydicom + NumPy |
| RLE Lossless | built-in pydicom; `pylibjpeg-rle` |
| JPEG Baseline/Extended | `pylibjpeg-libjpeg`; GDCM; Pillow with JPEG support |
| JPEG Lossless | `pylibjpeg-libjpeg`; GDCM |
| JPEG-LS | `pyjpegls`; `pylibjpeg-libjpeg`; GDCM |
| JPEG 2000 | `pylibjpeg-openjpeg`; GDCM; Pillow with OpenJPEG |
| HTJ2K | `pylibjpeg-openjpeg` |

Pinned reviewed installations (Python 3.12+ for NumPy 2.5.3):

```bash
uv pip install "pydicom==3.0.2" "numpy==2.5.3"

uv pip install "pylibjpeg==2.1.0" \
  "pylibjpeg-libjpeg==2.4.0" \
  "pylibjpeg-openjpeg==2.6.0" \
  "pylibjpeg-rle==2.2.0"

uv pip install "pyjpegls==1.5.1"
uv pip install "Pillow==12.3.0"
uv pip install "python-gdcm==3.2.6"
```

Install only what is required. Review transitive/package licensing:
`pylibjpeg-libjpeg` has different licensing from MIT pydicom.

Important stable documentation limitations include:

- Pillow performs transformations that pydicom describes as not always
  reversible and is not the preferred general decoder.
- Pillow JPEG Extended support requires 8 Bits Allocated.
- Pillow JPEG 2000 multi-sample support is constrained by bit depth.
- GDCM has syntax/bit-depth limits; pydicom rejects known incorrect JPEG-LS
  combinations for older GDCM releases.
- `pylibjpeg-openjpeg` and other plugins have their own maximum bit depths.
- pydicom's built-in RLE implementation is slower than compiled alternatives.

Runtime check on macOS arm64, Python 3.13, pydicom 3.0.2 and GDCM 3.2.6:
`pixel_array(..., decoding_plugin="gdcm")` correctly decoded the synthetic
signed 12-bit JPEG-LS fixture, but `Dataset.decompress(decoding_plugin="gdcm")`
failed with a read-only-array error during sign correction. Use the tested
`decoding_plugin="pyjpegls"` for that decompression case. This is a scoped
runtime finding, not a claim that every GDCM JPEG-LS image fails. RLE encoding
also exposes a GDCM plugin in this release; new-backend RLE decoding does not.

Never silently fall back in a validated workflow. Pin a plugin explicitly with
`decoding_plugin=...`, record versions, and compare results against independent
test vectors.

## Frame-specific decoding

Stable pydicom 3.0 adds path-based APIs that can reduce memory use:

```python
from pydicom.pixels import iter_pixels, pixel_array

first = pixel_array("authorized/multiframe.dcm", index=0)

for frame in iter_pixels(
    "authorized/multiframe.dcm",
    indices=[0, 2, 4],
):
    process_bounded_frame(frame)
```

Always calculate limits from:

- Rows and Columns
- Samples per Pixel
- Bits Allocated and decoded NumPy item size
- Number of Frames
- expec

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

