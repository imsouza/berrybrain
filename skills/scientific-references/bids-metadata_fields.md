---
id: sciref-bids-metadata-fields
name: "Scientific Ref: BIDS Metadata Fields Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (bids): BIDS Metadata Fields Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "bids metadata fields"
  - "bids metadata fields reference"
keywords:
  - "bids"
  - "metadata"
  - "fields"
  - "specialized"
  - "scientific"
  - "reference"
---

# BIDS Metadata Fields Reference

Reviewed against [BIDS 1.11.2](https://bids-specification.readthedocs.io/en/stable/)
on 2026-09-30. This is a practical selection, not a complete validator. The bundled
`bids_schema.json` contains field definitions under `objects.metadata`, conditional
requirements under `rules.sidecars`, and cross-file checks under `rules.checks`.
A field can be required only for a particular suffix, acquisition, or dataset context.
Read selectors before interpreting a rule; do not merge every modality's requirements.
Required metadata may be inherited from matching higher-level sidecars.

## MRI: units, timing and orientation

Use seconds for MRI timing fields, degrees for `FlipAngle`, and tesla for
`MagneticFieldStrength`. Convert DICOM millisecond values; do not copy units blindly.
`Manufacturer`, `ManufacturersModelName`, scanner/software identifiers and institution
fields are generally recommended. Check `rules.sidecars.mri` for exceptions, including
ASL and concurrent PET requirements.

- Anatomical MRI: `EchoTime` and `FlipAngle` are generally recommended;
  `RepetitionTimeExcitation` and `RepetitionTimePreparation` are available where applicable.
  Do not present one mandatory qMRI field set for all anatomical suffixes.
- BOLD: `TaskName` is required. It need not equal or be derived from the `task-` label.
  Specify **either** `RepetitionTime` **or** `VolumeTiming`, never both.
  With `VolumeTiming`, provide `SliceTiming` or `FrameAcquisitionDuration`;
  `DelayTime` is not used with `VolumeTiming`. Sparse sequences need the additional
  timing information described in the [MRI timing table](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/magnetic-resonance-imaging-data.html#timing-parameters).
- `EchoTime` is required for multi-echo data, ASL, or where the stated fieldmap
  conditions apply. With an `echo-` entity, record that echo's actual time, not its index.
- `PhaseEncodingDirection` uses NIfTI voxel axes `i`, `j`, `k` with optional `-`.
  Anatomical AP/PA/LR labels do not determine the axis or sign without the affine and
  converter orientation. Verify scanner metadata and image orientation together.
- `PhaseEncodingDirection` and `TotalReadoutTime` are recommended for DWI/BOLD and
  become required under specified fieldmap/opposing-encoding conditions. For pepolar
  `_epi` images, readout timing must be supplied or calculable through supported metadata.
  `EffectiveEchoSpacing` alone is not numerically interchangeable with total readout time.
- `SliceTiming` contains acquisition offsets in seconds, indexed by slice (reversed
  relative to slice index when `SliceEncodingDirection` is negative). It is not a list
  of slice indices. The list length must match the slice dimension. Never infer offsets
  from TR and slice order without accounting for multiband acquisition and dead time.

Illustrative odd-first order 1,3,5,2,4,6 with TR=2 s, equal spacing, no dead time and
positive slice encoding direction:

```json
{"SliceTiming": [0.0, 1.0, 0.333, 1.333, 0.667, 1.667]}
```

qMRI requirements are suffix-specific (`rules.sidecars.qmri`): VFA requires
`FlipAngle`, `PulseSequenceType`, and `RepetitionTimeExcitation`; MP2RAGE additionally
requires `InversionTime`, `RepetitionTimePreparation`, `NumberShots`, and field strength.
`MTState` is required for MT collections, not universally for every quantitative map.
The spelling is **`RepetitionTimePreparation`**.

## Diffusion gradients

Store `.bvec` as 3 rows × N columns and `.bval` as 1 row × N columns, with N equal to
stored image volumes. Use space-separated numbers. b=0 volumes have zero vectors;
diffusion-weighted vectors should be unit length. Preserve dcm2niix's FSL/BIDS image
coordinate convention and verify gradients after any image reorientation (including
the x-component handedness convention); scanner anatomical directions are insufficient.
See the [DWI specification](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/magnetic-resonance-imaging-data.html#diffusion-imaging-data).

## Fieldmaps and association

| Acquisition | Required core fields | Additional checks |
|---|---|---|
| `_phasediff` | `EchoTime1`, `EchoTime2` | Shorter echo first; matching magnitude image |
| `_phase1` / `_phase2` | `EchoTime` per image | Verify echo pairs and magnitude association |
| `_fieldmap` | `Units` | `Hz`, `rad/s`, or `T`; retain actual physical units |
| `_epi` pepolar | `PhaseEncodingDirection` | Readout time or supported inputs to calculate it; complementary encoding scans |

`IntendedFor` is optional for fieldmaps, not universally required. Use meaningful
associations for processing: `B0FieldIdentifier` defines a field estimate and
`B0FieldSource` on a target selects it; `IntendedFor` remains supported. Check the
pipeline's support before choosing the association method.

Fieldmap JSON example for a target in the same raw dataset:

```json
{
  "B0FieldIdentifier": "pepolar_fmap0",
  "IntendedFor": ["bids::sub-01/func/sub-01_task-rest_bold.nii.gz"]
}
```

Target BOLD JSON addition:

```json
{"B0FieldSource": "pepolar_fmap0"}
```

`bids::` is relative to the nearest dataset root, including a derivative's own root.
For cross-dataset sources, use a named BIDS URI and `DatasetLinks`. Legacy subject-relative
`IntendedFor` paths are deprecated. See [BIDS URI resolution](https://bids-specification.readthedocs.io/en/stable/common-principles.html#resolution-of-bids-uris).

## ASL

For `_asl`, core requirements include `ArterialSpinLabelingType` (`CASL`, `PCASL`,
`PASL`), `PostLabelingDelay`, `BackgroundSuppression`, `M0Type`,
`RepetitionTimePreparation`, `TotalAcquiredPairs`, `MagneticFieldStrength`,
`MRAcquisitionType`, and `EchoTime`. Also provide `_aslcontext.tsv` with one volume
label per stored volume, and verify the M0 acquisition/estimate relation.

- CASL/PCASL requires `LabelingDuration`; it is not a universal PASL field.
- PASL requires `BolusCutOffFlag`; when true, also supply `BolusCutOffDelayTime`
  and **`BolusCutOffTechnique`**.
- `M0Type: "Estimate"` requires `M0Estimate`; a separate `_m0scan` has an `IntendedFor` requirement.
- 2D ASL requires `SliceTiming`. Suppression pulse count/times are recommended when
  background suppression is true.

Use the full [ASL specification](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/magnetic-resonance-imaging-data.html#arterial-spin-labeling-perfusion-data)
for acquisition-speci

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

