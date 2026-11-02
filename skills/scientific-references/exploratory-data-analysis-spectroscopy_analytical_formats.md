---
id: sciref-exploratory-data-analysis-spectroscopy-analytical-formats
name: "Scientific Ref: Spectroscopy and Analytical Chemistry Formats"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (exploratory-data-analysis): Spectroscopy and Analytical Chemistry Formats"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "exploratory analysis spectroscopy analytical formats"
  - "exploratory analise spectroscopy analytical formats"
  - "spectroscopy and analytical chemistry formats"
keywords:
  - "exploratory"
  - "analysis"
  - "spectroscopy"
  - "analytical"
  - "formats"
  - "analise"
  - "specialized"
  - "scientific"
  - "reference"
---

# Spectroscopy and Analytical Chemistry Formats

**Reviewed:** 2026-09-30
**Executable scope:** No spectroscopy-native parser is bundled. General
CSV/TSV/JSON/NumPy/HDF5 inspectors apply only when a file is truly one of those
registered formats and do not add spectroscopy semantics.

## Capability boundary

| Format | Bundled native inspection | Status |
|---|---|---|
| mzML/mzXML, MGF | No | Reference-only MS tooling |
| JCAMP-DX (`.jdx`, `.dx`) | No | Reference-only technique/version-aware parser |
| SPC and vendor spectroscopy binaries | No | Reference-only producer-specific parser |
| Vendor `.raw`, `.d`, `.fid`, `.dat`, `.out` | No | Ambiguous suffix/path; producer and format must be confirmed |
| CSV/TSV exports | General tabular scripts | Bounded aggregates only after delimiter, units, axes, and missing codes are confirmed |
| NPY/NPZ/HDF5 exports | General container scripts | Structural/bounded numeric inspection only; no instrument semantics |

Unknown formats fail closed. Directory-based acquisitions are rejected by the
regular-file CLIs. No archive or compressed stream is unpacked.

## mzML and related mass-spectrometry formats

HUPO-PSI identifies mzML 1.1.0 as the long-term stable format; its index schema
and controlled vocabulary continue to receive compatible updates. mzML is XML
with encoded binary arrays and controlled-vocabulary metadata. The current
official links use main schema 1.1.1 and optional indexed wrapper 1.1.3; distinguish
the stable specification from schema revision numbers. The IM-MS/DIA proposal
updated August 2026 has not yet entered the PSI Document Process. A generic XML
parser is not sufficient. Use a local validator: PSI reports the former online
validators no longer function.

Use pinned pymzML, Pyteomics, OpenMS, or ProteoWizard tooling and inspect:

- schema/version, controlled-vocabulary terms, source files, checksums, and
  conversion software;
- run/instrument configuration, polarity, scan modes, MS levels, isolation,
  activation, and data processing;
- spectrum/chromatogram counts, retention/mobility time, m/z and intensity
  array lengths, precision, compression, and units;
- profile versus centroid data, TIC/BPC, calibration, lock mass, blanks, pooled
  QC, standards, carryover, drift, and batch order; and
- truncated scans, empty arrays, non-finite values, and metadata consistency.

Do not describe mzXML, mzData, mzMLb, or vendor RAW as equivalent to mzML.
Conversion can alter metadata, precision, centroiding, and compression; record
the converter/version/options and retain the original.

## JCAMP-DX

IUPAC describes JCAMP-DX as a family of standards for spectral data exchange.
It has technique- and version-specific specifications (IR, NMR, MS, IMS, and
others). Choose the applicable published recommendation instead of assuming
all JCAMP files share one interchangeable schema.

Before parsing, identify the technique and specification/version. Validate:

- label/value records and required metadata;
- X/Y units, first/last X, point count, spacing, factors, and encoded numeric
  representation;
- NTUPLES versus simpler XY forms;
- page/block boundaries and compound/instrument identifiers; and
- whether data are absorbance, transmittance, counts, complex NMR, peaks, or
  continuous spectra.

Metadata and comments are untrusted and should not be copied into a report.
The generic tabular scanner is not a JCAMP parser.

## NMR data

`.fid`, Bruker directory layouts, Varian/Agilent layouts, processed spectra,
and NMR exchange files require producer-aware tooling such as nmrglue. Record:

- vendor/software/version and complete acquisition directory;
- nucleus, field strength, spectral width, dwell time, point count, quadrature,
  digital filter, scans, temperature, pulse sequence, and reference;
- raw FID versus processed spectrum, apodization, zero filling, Fourier
  transform, phase, baseline, referencing, and solvent suppression;
- dimensional axes/units and whether data are real, imaginary, magnitude, or
  complex; and
- sample preparation, concentration, pH, replicates, and batch/order.

Peak picking, integration, baseline correction, phase correction, alignment,
binning, and normalization are transformations. Preserve raw data and report
parameter sensitivity; do not apply them automatically.

## Optical, vibrational, and diffraction spectra

SPC, OPUS, WDF, SPE, instrument `.raw`, `.dat`, and text exports are
producer/variant dependent. Confirm:

- physical X axis (wavelength, wavenumber, energy, angle, time) and units;
- Y quantity (counts, intensity, absorbance, transmittance, reflectance) and
  calibration;
- point order/spacing, detector/channel, exposure/accumulations, resolution,
  slit/grating/laser/source, and polarization;
- background/reference/dark correction and all processing already applied; and
- maps, time series, replicate spectra, and spatial coordinates.

For XRD, crystallographic CIF/MTZ/HKL are also reference-only and need
crystallography-aware validation. A `.cif` suffix is ambiguous between
small-molecule CIF and PDBx/mmCIF.

## Chromatography and thermal/electrochemical exports

Generic CSV/TSV can contain retention time, temperature, potential, wavelength,
or another independent axis. The general scripts can profile the table only
after the data dictionary confirms:

- axis and signal columns, units, ordering, spacing, and replicate layout;
- blanks, calibration standards, internal standards, dilution factors,
  injection order, batch, and sample identifiers;
- LOD/LOQ, saturation, censoring qualifiers, and negative/zero handling; and
- whether peaks/integrals are raw, manually edited, or software-derived.

Do not infer an axis from monotonic values or a column name. Do not
automatically smooth, baseline-correct, align, integrate, normalize, subtract
blanks, or delete peaks.

## Safe bounded tabular workflow

For an approved values-only export:

```bash
python scripts/tabular_profile.py spectrum.csv \
  --root /approved/project \
  --max-rows 100000

python scripts/missingness_leakage_audit.py spectrum.csv \
  --root /approved/project \
  --group-column sample_group \
  --entity-column sample_id \
  --split-column split \
  --time-column acquisition_time

python scripts/distribution_sensitivity.py spectrum.csv \
  --root /approved/project \
  --column intensity
```

Use only pseudonymous column roles in shared commands/logs. The outputs contain
aggregates and tokens, not spectra or identifiers.

## Analytic

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

