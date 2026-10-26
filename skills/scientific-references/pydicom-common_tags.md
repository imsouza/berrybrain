---
id: sciref-pydicom-common-tags
name: "Scientific Ref: DICOM data elements, tags, and privacy review"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pydicom): DICOM data elements, tags, and privacy review"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pydicom common tags"
  - "dicom data elements, tags, and privacy review"
keywords:
  - "pydicom"
  - "common"
  - "tags"
  - "specialized"
  - "scientific"
  - "reference"
  - "dicom"
  - "elements"
---

# DICOM data elements, tags, and privacy review

This is a working guide, not a complete DICOM dictionary or an attribute
confidentiality profile. pydicom 3.0.2 bundles the 2024c public dictionary; use
the live DICOM PS3.3/PS3.6 and the selected IOD when correctness depends on a
newer edition.

## Privacy boundary

DICOM metadata and pixels may contain PHI. Do not print a complete `Dataset`,
serialize the full dataset to JSON, or copy arbitrary values into logs. Tag
names that appear technical can still identify a person through site-specific
values, free text, private data, UIDs, dates, devices, or linkage with external
records.

DICOM PS3.15 Annex E says that applying attribute actions does not guarantee
that the Information Object is de-identified. A valid workflow must select a
profile/options for its context and include expert verification and
re-identification risk review.

## pydicom access model

```python
from pydicom import dcmread
from pydicom.tag import Tag

ds = dcmread(
    "authorized/input.dcm",
    stop_before_pixels=True,
    specific_tags=["SOPClassUID", "Modality", "Rows", "Columns"],
)

modality = ds.get("Modality", "UNSPECIFIED")
element = ds.get_item(Tag(0x0008, 0x0016))
```

- Keyword access (`ds.Modality`) returns the value and raises `AttributeError`
  when absent.
- `ds.get("Modality", default)` is safer for optional elements.
- Tag indexing (`ds[0x0008, 0x0016]`) returns a `DataElement`; read `.value`
  only when authorized.
- A tag consists of a 16-bit group and 16-bit element.
- Standard public tags generally use even groups. Private data uses odd groups
  and private creator blocks.
- `Dataset` contains `DataElement` objects. A value with VR `SQ` is a
  `Sequence` of nested `Dataset` items.

## Narrow technical allowlist

The following values are commonly useful for bounded technical inventory.
They do not make an entire record safe to disclose.

| Tag | Keyword | VR | Technical use |
|---|---|---|---|
| (0008,0016) | SOPClassUID | UI | Identifies the standardized SOP Class |
| (0008,0060) | Modality | CS | Modality code |
| (0002,0010) | TransferSyntaxUID | UI | File encoding/compression |
| (0028,0002) | SamplesPerPixel | US | Samples per pixel |
| (0028,0004) | PhotometricInterpretation | CS | Pixel color/monochrome interpretation |
| (0028,0006) | PlanarConfiguration | US | Color sample layout |
| (0028,0008) | NumberOfFrames | IS | Declared frames |
| (0028,0010) | Rows | US | Rows per frame |
| (0028,0011) | Columns | US | Columns per frame |
| (0028,0100) | BitsAllocated | US | Storage bits per sample |
| (0028,0101) | BitsStored | US | Meaningful bits per sample |
| (0028,0102) | HighBit | US | Highest stored bit |
| (0028,0103) | PixelRepresentation | US | Unsigned (0) or signed (1) |
| (0028,0301) | BurnedInAnnotation | CS | Declared burned-in annotation status |
| (0028,0302) | RecognizableVisualFeatures | CS | Declared recognizable-feature status |
| (0028,2110) | LossyImageCompression | CS | Whether lossy compression occurred |

`BurnedInAnnotation=NO` is a declaration, not proof that pixels are clean.
Absence, `YES`, or another value requires review. Even `NO` does not address
recognizable facial/anatomic features or matching against source images.

## Instance, relationship, and spatial elements

These values are technically important but can enable linkage or reveal
individual context. Do not emit them in default reports.

| Tag | Keyword | Privacy/semantic concern |
|---|---|---|
| (0008,0018) | SOPInstanceUID | Instance identifier; may support linkage |
| (0020,000D) | StudyInstanceUID | Study-level linkage |
| (0020,000E) | SeriesInstanceUID | Series-level linkage |
| (0020,0052) | FrameOfReferenceUID | Spatial/reference linkage |
| (0008,1155) | ReferencedSOPInstanceUID | Cross-instance relationship |
| (0020,0032) | ImagePositionPatient | Patient-coordinate position |
| (0020,0037) | ImageOrientationPatient | Patient-coordinate orientation |
| (0028,0030) | PixelSpacing | Physical sample spacing |
| (0018,0050) | SliceThickness | Nominal reconstructed thickness |
| (0018,0088) | SpacingBetweenSlices | Center-to-center spacing when defined |

Do not sort a series only by `SliceLocation` or assume `SliceThickness` equals
inter-slice spacing. Reconstruct geometry from the applicable IOD, orientation,
position, frame functional groups, and validated series membership.

For the Image Plane Module with BIPED or absent Anatomical Orientation Type,
patient coordinates increase left, posterior, and toward the head (LPS).
`PixelSpacing = [row_spacing, column_spacing]` in mm. For zero-based NumPy
indices `[row, column]`, the pixel center is:

```text
ImagePositionPatient
  + column * PixelSpacing[1] * ImageOrientationPatient[:3]
  + row    * PixelSpacing[0] * ImageOrientationPatient[3:]
```

For a consistent parallel stack, sort positions projected onto the cross product
of the two orientation vectors, then check duplicates, spacing, orientation,
Frame of Reference, and acquisition dimensions. Series membership alone does
not separate time points/echoes/diffusion directions. Enhanced multi-frame
ordering uses Dimension Index Values and frame functional groups. A PNG does
not retain patient geometry; resampling/rotation requires corresponding affine
updates and interpolation appropriate to the data. QUADRUPED conventions differ.

## Direct and quasi-identifiers

The following examples are not exhaustive. PS3.15 Table E.1-1 and the chosen
options control action selection, including nested occurrences.

| Tag | Keyword | Typical risk |
|---|---|---|
| (0010,0010) | PatientName | Direct identifier |
| (0010,0020) | PatientID | Direct/local identifier |
| (0010,0021) | IssuerOfPatientID | Identifier namespace |
| (0010,0030) | PatientBirthDate | Date/quasi-identifier |
| (0010,0032) | PatientBirthTime | Time/quasi-identifier |
| (0010,0040) | PatientSex | Patient characteristic |
| (0010,1010) | PatientAge | Patient characteristic |
| (0010,1020) | PatientSize | Patient characteristic |
| (0010,1030) | PatientWeight | Patient characteristic |
| (0010,1040) | PatientAddress | Direct identifier |
| (0010,2154) | PatientTelephoneNumbers | Direct identifier |
| (0010,4000) | PatientComments | Free text |
| (0008,0050) | AccessionNumber | Order/study linkage |
| (0020,0010) | StudyID | Local study identifier |
| (0040,1001) | RequestedProcedureID | Order linkage |
| (0040,0009) | ScheduledProcedureStepID | Workflow linkage |
| (0008,0090) | Referr

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

