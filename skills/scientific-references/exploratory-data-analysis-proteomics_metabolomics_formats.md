---
id: sciref-exploratory-data-analysis-proteomics-metabolomics-formats
name: "Scientific Ref: Proteomics and Metabolomics Formats"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (exploratory-data-analysis): Proteomics and Metabolomics Formats"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "exploratory analysis proteomics metabolomics formats"
  - "exploratory analise proteomics metabolomics formats"
  - "proteomics and metabolomics formats"
keywords:
  - "exploratory"
  - "analysis"
  - "proteomics"
  - "metabolomics"
  - "formats"
  - "analise"
  - "specialized"
  - "scientific"
  - "reference"
---

# Proteomics and Metabolomics Formats

**Reviewed:** 2026-09-30
**Executable scope:** No omics-native standard is parsed by bundled scripts.
Rectangular CSV/TSV result exports can use the general tabular CLIs after the
schema, units, and missing/censoring codes are confirmed.

## Exact capability boundary

| Format | Bundled native inspection | Status |
|---|---|---|
| mzML/mzXML, vendor RAW | No | Reference-only MS tooling; see `spectroscopy_analytical_formats.md` |
| mzIdentML (`.mzid`, `.mzIdentML`) | No | Reference-only PSI schema/CV-aware tooling |
| mzTab 1.0 / mzTab-M 2.0 | No | Reference-only version-aware validator; generic TSV parsing is insufficient |
| pepXML/protXML | No | Reference-only search/inference-aware parser |
| featureXML/consensusXML/idXML | No | Reference-only OpenMS tooling |
| Rectangular `.csv`/`.tsv` feature or abundance table | General scripts | Bounded aggregate tabular EDA, no omics semantics |
| `.h5`/`.hdf5` | Generic metadata only | No payload values or convention validation |
| `.h5ad`, `.loom` | No semantic support | See bioinformatics reference |
| Pickled models/results | **Never** | Request non-executable export |

Unknown formats fail closed. No format is identified from free-text metadata or
content guessing.

## mzML and raw spectra

mzML is a HUPO-PSI standard for spectra/chromatograms; use PSI-aware tooling.
Vendor RAW extensions are ambiguous and often require vendor libraries or
conversion. Preserve originals and record converter, version, options, and
checksums.

For spectral EDA, inventory:

- acquisition method, instrument, polarity, MS levels, scan modes, precursor
  isolation/activation, resolution, and centroid/profile status;
- run order, batches, blanks, pooled QC, standards, carryover, drift, and
  calibration;
- spectrum/chromatogram counts, retention/mobility ranges, m/z coverage, TIC/
  BPC, peak counts, and missing/corrupt scans; and
- processing history, controlled-vocabulary terms, source files, and units.

Do not automatically centroid, denoise, recalibrate, align, peak-pick, or
discard spectra.

## Identification formats

### mzIdentML

mzIdentML represents peptide/protein identification results, scores, search
parameters, databases, modifications, and links to spectra using controlled
vocabularies. Validate the schema and CV mapping with PSI-aware tooling.

Check:

- search engine/version, sequence database/version, decoy strategy, enzyme,
  tolerances, fixed/variable modifications, and spectrum references;
- score direction/meaning, rank, charge, mass error, peptide-spectrum matches,
  peptides, proteins, and protein groups;
- target/decoy and FDR method at each reported level; and
- ambiguity from shared peptides, indistinguishable proteins, and inference.

A score threshold is not automatically a validated FDR threshold. Do not
recompute or reinterpret confidence without the method and decoy design.

### pepXML/protXML

These formats are Trans-Proteomic Pipeline conventions. Use Pyteomics or TPP
tools with the generating software/version known. Preserve search-engine,
PeptideProphet/ProteinProphet, modification, decoy, and inference context.

## mzTab and mzTab-M

HUPO-PSI lists:

- mzTab 1.0.0 as the final proteomics release (accepted June 2014); and
- mzTab-M 2.0.0 as the final metabolomics/small-molecule release (accepted
  March 2019).

mzTab-M 2.1.0 is listed as draft, not a final standard. Do not silently treat
it as 2.0. The draft has moved to the separate
[HUPO-PSI/mzTab-M repository](https://github.com/HUPO-PSI/mzTab-M); the released
2.0 materials remain in HUPO-PSI/mzTab.

Although mzTab is tab-delimited, it has section-specific row types, metadata,
controlled vocabulary, optional columns, and null conventions. The generic
rectangular TSV scanner is not a validator and will reject legitimate
non-rectangular section structure. Use the PSI specification/reference
validator, then export a controlled rectangular analysis table if needed.

## Rectangular quantitative tables

Common outputs contain features/peptides/proteins/metabolites in rows and
samples in columns, or long-form measurements. Before using general CLIs,
create a data dictionary that records:

- row entity and identifier namespace/version;
- sample/subject/specimen, condition, batch, injection order, and QC role;
- abundance scale (raw intensity, area, count, ratio, normalized/logged);
- zero, missing, censored, filtered, not-identified, and not-quantified codes;
- normalization, transformation, imputation, roll-up, and batch correction
  already applied;
- internal standards, dilution, LOD/LOQ, blank subtraction, and detection
  frequency; and
- peptide-to-protein or feature-to-metabolite ambiguity.

Do not assume zeros are measured zeros. Missingness is often abundance-,
feature-, batch-, or identification-dependent and may be non-random.

### Safe commands

```bash
python scripts/tabular_profile.py abundance.csv \
  --root /approved/project \
  --missing-token NA \
  --max-rows 100000

python scripts/missingness_leakage_audit.py abundance.csv \
  --root /approved/project \
  --group-column condition \
  --entity-column subject_id \
  --split-column split \
  --time-column acquisition_time

python scripts/distribution_sensitivity.py abundance.csv \
  --root /approved/project \
  --column intensity
```

The column arguments are exact local identifiers; output tokenizes them unless
`--reveal-identifiers` is explicit. Values and subject/sample identifiers are
not emitted.

## Missingness, censoring, and limits

Separate at least:

- structurally absent/not applicable;
- not detected;
- detected below quantitation;
- failed identification or confidence filter;
- failed extraction/integration;
- filtered during preprocessing;
- saturated/above range; and
- genuinely missing metadata.

Preserve flags and limits in separate columns. Do not automatically replace
non-detects with zero, half-minimum, LOD/2, or a random draw. Report missing/
censored fractions by feature, sample, condition, batch, and run order, and
compare conclusions across scientifically justified handling strategies.

## Distribution and outlier sensitivity

For abundance tables:

- inspect sample totals/detection rates and feature detection frequency;
- compare raw-scale and scientifically justified log/variance-stabilizing
  diagnostics without overwriting raw data;
- compare mean/SD with median/IQR/MAD and leave-one-sample/batch sensitivity;
- investigate outliers against bla

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

