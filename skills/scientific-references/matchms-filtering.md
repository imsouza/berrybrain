---
id: sciref-matchms-filtering
name: "Scientific Ref: Filtering and Spectrum Processing (matchms 0.33.1)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matchms): Filtering and Spectrum Processing (matchms 0.33.1)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matchms filtering"
  - "filtering and spectrum processing (matchms 0.33.1)"
keywords:
  - "matchms"
  - "filtering"
  - "specialized"
  - "scientific"
  - "reference"
  - "spectrum"
---

# Filtering and Spectrum Processing (matchms 0.33.1)

Use this reference when building or debugging metadata-cleaning, peak-processing,
or quality-control pipelines. The authoritative API is the matchms
[`filtering` package](https://matchms.readthedocs.io/en/latest/api/matchms.filtering.html).

## Filter Contract

Most matchms filters:

- accept one `Spectrum` as the first argument;
- return a `Spectrum` or `None`;
- default to `clone=True`, so direct calls usually return a modified copy;
- use `None` to indicate that a `require_*` condition failed; and
- should be assigned back when called directly.

```python
spectrum = normalize_intensities(spectrum)
spectrum = require_minimum_number_of_peaks(spectrum, n_required=5)
if spectrum is None:
    # The spectrum failed a quality requirement.
    ...
```

Do not continue passing `None` through ordinary filters. `SpectrumProcessor`
stops the chain and discards rejected spectra for you.

## Prefer `SpectrumProcessor`

`SpectrumProcessor` accepts:

- a built-in filter name such as `"normalize_intensities"`;
- a callable such as `normalize_intensities`; or
- `(filter, parameter_dict)`, where `filter` can be a name or callable.

Built-in filters are automatically sorted into matchms's required filter order.
Custom filters are appended unless an explicit position is supplied with
`parse_and_add_filter()`.

```python
from matchms import SpectrumProcessor
from matchms.filtering import (
    default_filters,
    normalize_intensities,
    remove_peaks_relative_to_precursor_mz,
    require_minimum_number_of_peaks,
    require_precursor_mz,
    select_by_mz,
    select_by_relative_intensity,
)

# Run the aggregate metadata harmonizer before SpectrumProcessor. If included as
# one callable inside the processor, it is treated as custom and placed last.
spectra = [default_filters(spectrum) for spectrum in spectra]

processor = SpectrumProcessor(
    [
        (require_precursor_mz, {"minimum_accepted_mz": 50.0, "maximum_mz": 1500.0}),
        normalize_intensities,
        (remove_peaks_relative_to_precursor_mz, {"offset_to_precursor": -1.6}),
        (select_by_mz, {"mz_from": 20.0, "mz_to": 1500.0}),
        (select_by_relative_intensity, {"intensity_from": 0.01}),
        (require_minimum_number_of_peaks, {"n_required": 5}),
    ]
)

cleaned, report = processor.process_spectra(
    spectra,
    progress_bar=False,
    create_report=False,
)
print(processor.processing_steps)
```

Important current behavior:

- `SpectrumProcessor` is **not callable**.
- Use `processor.process_spectrum(spectrum.clone())` to preserve one input.
  Without a processing report, `process_spectrum` passes `clone=False` to
  filters and can mutate its argument; it does not clone on entry.
- Use `processor.process_spectra(spectra)` for a list.
- `process_spectra()` returns `(processed_spectra, processing_report)`.
- With `create_report=False`, the processor clones each input once and disables
  per-filter cloning where supported.
- With `create_report=True`, filters are cloned step by step to measure changes.
  The aggregate `default_filters` function is not in the processor's built-in
  order registry and does not expose a `clone` parameter. If passed directly,
  it is placed after registered filters and detailed reporting logs a warning.
  Run it before the processor or expand it into the nine filters below.
- `process_spectrums()` is a deprecated spelling.

## What `default_filters()` Does

In 0.33.1, `default_filters()` applies exactly:

1. `make_charge_int`
2. `add_compound_name`
3. `derive_adduct_from_name`
4. `derive_formula_from_name`
5. `clean_compound_name`
6. `interpret_pepmass`
7. `add_precursor_mz`
8. `derive_ionmode`
9. `correct_charge`

It does **not** normalize peaks, add retention fields, harmonize structural
identifiers, require precursor metadata, or enforce peak-count quality. Add
those steps explicitly.

## Peak Processing

### Normalize and select peaks

- `normalize_intensities(spectrum_in, clone=True, scaling=None)` — normalize to
  maximum intensity 1 by default; pass `scaling=(low, high)` for min-max scaling.
- `select_by_intensity(spectrum_in, intensity_from=10.0, intensity_to=200.0,
  clone=True)` — keep an absolute intensity interval.
- `select_by_relative_intensity(spectrum_in, intensity_from=0.0,
  intensity_to=1.0, clone=True)` — keep a fraction-of-maximum interval.
- `select_by_mz(spectrum_in, mz_from=0.0, mz_to=1000.0, clone=True)` — crop the
  fragment m/z interval.

`select_by_relative_intensity` divides by the current maximum internally; prior
normalization is optional, and retained intensities keep their original scale.
Cropping away a base peak before this filter can change the retained peaks.

### Reduce and clean peaks

- `reduce_to_number_of_peaks(spectrum_in, n_required=0, n_max=inf,
  ratio_desired=None, clone=True)` — keep the most intense peaks within count
  constraints.
- `remove_noise_below_frequent_intensities(spectrum_in,
  min_count_of_frequent_intensities=5, noise_level_multiplier=2.0, clone=True)`
  — estimate and remove repeated low-intensity noise.
- `remove_peaks_around_precursor_mz(spectrum_in, mz_tolerance=17, clone=True)`
  — remove peaks within a precursor-centered exclusion window.
- `remove_peaks_relative_to_precursor_mz(spectrum_in,
  offset_to_precursor=-1.6, clone=True)` — remove peaks above a cutoff relative
  to precursor m/z.
- `remove_peaks_outside_top_k(spectrum_in, k=6, mz_window=50, clone=True)` —
  retain peaks within `mz_window` Da of one of the globally `k` most intense
  peaks; this is not a per-window top-k filter.
- `remove_profiled_spectra(spectrum_in, mz_window=0.5, clone=True)` — reject
  spectra likely to contain profile-mode rather than centroided data.

These defaults are starting points, not instrument-independent truth. Record
chosen windows and thresholds.

### Peak quality requirements

- `require_minimum_number_of_peaks(spectrum_in, n_required=10,
  ratio_required=None, clone=True)`
- `require_maximum_number_of_peaks(spectrum_in,
  maximum_number_of_fragments=1000, clone=True)`
- `require_minimum_number_of_high_peaks(spectrum_in, no_peaks=5,
  intensity_percent=2.0, clone=True)`

Older examples commonly use invalid
`require_minimum_number_of_high_peaks(n_required=..., intensity_threshold=...)`
arguments. In 0.33.1 the names are `no_peaks` and `intensity_percent`, where the
latter is a percentage rather than a 0-1 fraction.

## Precursor, Adduct, Charge, and Ion Mode

- `interpret_pe

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

