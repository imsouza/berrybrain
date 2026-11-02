---
id: sci-pyopenms
name: "Scientific: pyopenms"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Processes mass spectrometry data with pyOpenMS. Supports proteomics and metabolomics workflows—feature detection, peptide/protein identification, label-free quantification, adduct/accurate-mass annotation, and complex LC-MS/MS pipelines. Supports extensive file formats and algori"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "pyopenms"
keywords:
  - "pyopenms"
  - "processes"
  - "mass"
  - "spectrometry"
  - "supports"
  - "proteomics"
---

# PyOpenMS

## Overview

PyOpenMS provides Python bindings to the OpenMS library for computational mass
spectrometry, enabling analysis of proteomics and metabolomics data. Use it to
read/write MS file formats, process raw spectra, detect and quantify features,
identify peptides and proteins, and run end-to-end LC-MS/MS pipelines.

**This skill ships ready-to-run scripts in `scripts/`** covering the most common
high-level workflows. Prefer running a script over writing new code—each is a
parameterized CLI tool that handles loading, processing, and export. Drop into the
Python API (and the `references/`) only when no script fits.

## Installation

```bash
uv venv --python 3.13
uv pip install "pyopenms==3.6.0" pandas numpy matplotlib
```

Verify (note: `__version__` works, but the bundled binary prints a one-line
memory-status notice on import that is harmless):

```python
import pyopenms as ms
print(ms.__version__)  # 3.6.0
```

## Scripts (start here)

Run with `python scripts/<name>.py --help` for full options. Input formats differ by script; inspect its help. Commands below run from the skill
directory with the environment activated. Native regression tests use tiny synthetic
files; instrument-specific detection/search performance is not validated.

### Inspect & convert
| Script | What it does |
|--------|--------------|
| `inspect_ms_data.py` | Summarize any mzML/mzXML/featureXML/consensusXML/idXML (counts, RT/m/z ranges, TIC, metadata); optional per-spectrum CSV. |
| `convert_format.py` | Convert between mzML/mzXML/MGF with optional MS-level, RT, and intensity filtering. |
| `process_spectra.py` | Configurable signal-processing chain: smoothing (Gauss/SGolay), centroiding (PeakPickerHiRes), normalization, S/N and intensity thresholds. |

### Feature detection & quantification
| Script | What it does |
|--------|--------------|
| `detect_features_metabo.py` | Untargeted metabolomics feature finding: MassTraceDetection → ElutionPeakDetection → FeatureFindingMetabo. |
| `detect_features_centroided.py` | Peptide/centroided feature detection via FeatureFinderAlgorithmPicked. |
| `align_link_quantify.py` | Multi-sample pipeline: detect (or load) features → RT alignment → consensus linking → quant matrix CSV. |
| `consensus_to_matrix.py` | consensusXML → wide intensity matrix + metadata, with optional median/quantile normalization and long format. |

### Annotation
| Script | What it does |
|--------|--------------|
| `detect_adducts.py` | Group adducts/charge variants of the same neutral mass (MetaboliteFeatureDeconvolution). |
| `accurate_mass_search.py` | Annotate features against local formula/structure TSVs by accurate mass (AccurateMassSearchEngine → mzTab/CSV). |
| `export_gnps_sirius.py` | Export GNPS FBMN inputs (MGF + quant table) or a SIRIUS `.ms` file. |

### Identification
| Script | What it does |
|--------|--------------|
| `process_identifications.py` | Re-index against FASTA, estimate FDR/q-values, filter (FDR/length/best-per-spectrum), export idXML + CSV. |

### Chemistry
| Script | What it does |
|--------|--------------|
| `mass_calculator.py` | Monoisotopic/average mass, charged m/z, formula, and isotope pattern for peptides or empirical formulas. |
| `digest_protein.py` | In-silico protease digestion of FASTA/sequence → theoretical peptides with masses and m/z. |
| `theoretical_spectrum.py` | Generate annotated theoretical fragment spectra (b/y/a/c/x/z, losses) for a peptide. |

### Targeted & visualization
| Script | What it does |
|--------|--------------|
| `extract_chromatograms.py` | Build TIC/BPC and XIC traces for target m/z (CSV + optional plot). |
| `plot_ms_data.py` | Quick plots: single spectrum, TIC, 2D feature map, MS1 signal map. |

### Common script recipes

```bash
# Inspect a file
python scripts/inspect_ms_data.py sample.mzML --spectra-csv spectra.csv

# Untargeted metabolomics: features for one sample
python scripts/detect_features_metabo.py sample.mzML --out-csv features.csv

# Full multi-sample quantification study
python scripts/align_link_quantify.py s1.mzML s2.mzML s3.mzML --out-prefix study
python scripts/consensus_to_matrix.py study.consensusXML --out quant.csv --normalize median

# Peptide chemistry
python scripts/mass_calculator.py --peptide "PEPTIDEM(Oxidation)K" --charges 1 2 3 --isotopes 5
python scripts/digest_protein.py proteins.fasta --enzyme Trypsin --missed 2 --out peptides.csv

# Identification post-processing
python scripts/process_identifications.py search.idXML --fasta db.fasta --fdr 0.01 --out filtered.idXML --csv hits.csv
```

## Identification confidence

`--fdr` estimates top-hit PSM q-values from one comparable search run and rejects
missing labels, non-finite scores, mixed score types/directions, and absent target
or decoy top hits. It does not recalibrate existing q-values. Before using it, verify target/decoy annotations, score direction, and the search database used to generate the hits. The script applies `FalseDiscoveryRate` to peptide identifications; its threshold does not establish protein-level FDR. Report the tested unit (PSM, unique peptide, or protein), pooling/search settings, decoy strategy, and threshold explicitly. Protein inference and protein-level error control need their own validated workflow; do not label all inferred proteins “1% FDR” from the peptide-hit filter alone. See the [OpenMS FDR API](https://www.openms.org/documentation/html/classOpenMS_1_1FalseDiscoveryRate.html).

## Version 3.6.0 API and scientific checks

OpenMS 3.6.0 moved pyOpenMS to nanobind. The old documentation site's `latest`
page still identifies itself as 3.5.0dev; use installed `help()` and release source
when a signature disagrees. This skill's version 3.0 updates the binding calls and
changes the peptide detector option from `--mz-tol-ppm` to `--mz-tol-da`: its native
algorithm uses an absolute m/z tolerance, so conversion at an arbitrary m/z 400
was incorrect for the rest of the mass range.

- `MassTraceDetection.run(exp, 0)` returns traces; `ElutionPeakDetection.detectPeaks(traces)`
  returns split traces; `FeatureFindingMetabo.run(traces, features)` fills the map
  and returns a tuple. It no longer accepts a third chromatogram output list.
- `Param.keys()` returns strings. Use `PeptideIdentificationList` for mutable IDs;
  `IdXMLFile.load(path)` also supports returning `(proteins, peptides)` in 3.6.
- Feature tables use `rt`/`mz`; consensus tables use `get_intensity_df()` and
  `get_metadata_df()`. RT and chromat

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

