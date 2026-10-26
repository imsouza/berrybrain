---
id: sciref-neurokit2-eeg
name: "Scientific Ref: EEG and microstates"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (neurokit2): EEG and microstates"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "neurokit2 eeg"
  - "eeg and microstates"
keywords:
  - "neurokit2"
  - "eeg"
  - "specialized"
  - "scientific"
  - "reference"
  - "neurokit"
  - "microstates"
---

# EEG and microstates

Checked **2026-10-01** against NeuroKit2 0.2.13 stable source/runtime,
the official EEG/microstate APIs, and SPR EEG/MEG guidance.

## Scope

NeuroKit2 does not expose an `eeg_process()` equivalent to its ECG/EDA pipelines.
It provides selected feature, QC, re-reference, MNE, source, and microstate helpers.
Use MNE or another validated EEG framework for the full acquisition/preprocessing
workflow, while recording every transform and bad-segment decision.

For NumPy input, NeuroKit2 EEG functions expect shape:

```text
(channels, time_samples)
```

Do not pass `(time, channels)` silently. Preserve channel names/order, montage,
reference, sensor locations, units (typically volts in MNE), sampling rate, and bad
channel/segment annotations.

## Current stable helpers

### Power

```python
power = nk.eeg_power(
    eeg_channels_by_time,
    sampling_rate=250,
    frequency_band=["Gamma", "Beta", "Alpha", "Theta", "Delta"],
)
```

The argument is singular `frequency_band`, not `frequency_bands`. The pinned default
array probe returned one row per channel with:

```text
Channel, Gamma, Beta, Alpha, Theta, Delta
```

Standard named bands in the docs include Delta 1–4, Theta 4–8, Alpha 8–13, Beta
13–30, and Gamma 30–80 Hz, with additional sub-bands. Band definitions are conventions,
not universal physiology. Report exact boundaries, PSD parameters, reference, artifact
handling, absolute/relative normalization, and usable duration.

### Bad channels

```python
bads, channel_info = nk.eeg_badchannels(
    eeg_channels_by_time,
    bad_threshold=0.5,
    distance_threshold=0.99,
    show=False,
)
```

Return order is a list plus a DataFrame. The pinned info schema contained `SD`, `Mean`,
`MAD`, `Median`, `Skewness`, `Kurtosis`, `Amplitude`, interval bounds,
`n_ZeroCrossings`, and `Bad`.

This statistical screen is not a universal rejection rule. Review raw data, montage,
bridging, line noise, drift, channel location, task, and condition. Fit thresholds
without leaking group/condition outcomes.

### Re-reference, GFP, and dissimilarity

```python
rereferenced = nk.eeg_rereference(eeg_channels_by_time, reference="average")
gfp = nk.eeg_gfp(rereferenced, method="l1")
diss = nk.eeg_diss(rereferenced, gfp=gfp)
```

For array input `eeg_rereference()` returns an array. For MNE input it returns an MNE
object. Average reference requires adequate channel coverage and bad-channel handling;
it is not automatically appropriate for sparse montages.

`eeg_gfp()` defaults to L1 in NeuroKit2, while publications may use other definitions.
Report method, standardization, normalization, smoothing, and reference.

## Optional MNE requirements

Core NeuroKit2 does not install MNE. Stable functions that require it include:

- `eeg_simulate()` (confirmed by pinned runtime);
- `mne_data()` and MNE object helpers;
- `eeg_source()` / `eeg_source_extract()`; and
- `mne_templateMRI()`.

Add only the optional package(s) required for the analysis at reviewed exact versions,
commit/review the resulting `uv.lock`, and install with `uv sync --locked`. Do not
install the upstream floating `full` extra in an automated workflow without such a
lock.

Some MNE helpers download datasets/templates. Treat network access, cache paths,
licenses, versions, and checksums as study dependencies; do not use them in a
restricted/offline workflow without prior provisioning.

## Source reconstruction

Stable signature:

```text
eeg_source(raw, src, bem, method="sLORETA", show=False, ...)
```

It requires an MNE Raw object, source space, BEM/head model, montage/electrode
locations, and appropriate co-registration. `eeg_source_extract(stc, src, ...)` returns
region time series from a segmentation.

A template MRI does not validate localization for an individual or population.
Report coordinate frames, digitization, head/conductivity model, inverse method,
regularization, noise covariance, depth/orientation choices, atlas, and uncertainty.
Do not use NeuroKit2 source estimates for diagnosis, surgical planning, or clinical
localization.

## Microstates

### Segmentation

```python
out = nk.microstates_segment(
    eeg_channels_by_time,
    n_microstates=4,
    train="gfp",
    method="kmod",
    sampling_rate=250,
    n_runs=50,
    random_state=42,
)
```

Stable methods include `kmod`, `kmeans`, `kmedoids`, `pca`, `ica`, and `aahc`.
The pinned 0.2.13 output dict included:

```text
Microstates, Sequence, GEV, GEV_per_microstate, GFP,
Polarity, Info, Info_algorithm
```

It did **not** use lowercase `maps`, `labels`, `gfp`, or `gev`. `Microstates` contains
maps, and `Sequence` is the sample-wise class assignment.

### Preparation and summaries

```python
clean, train_indices, gfp, input_info = nk.microstates_clean(
    eeg_channels_by_time,
    sampling_rate=250,
    train="gfp",
)

static = nk.microstates_static(out["Sequence"], sampling_rate=250)
dynamic = nk.microstates_dynamic(out["Sequence"])
```

`microstates_clean()` is a utility for array normalization/standardization and training
sample selection; it does not implement a full EEG artifact pipeline.

`microstates_classify()` is experimental and requires two arguments:

```python
sequence, maps = nk.microstates_classify(
    out["Sequence"],
    out["Microstates"],
)
```

Its classification depends on channel ordering, so it is not a reliable substitute for
template matching with a defined montage.

`microstates_findnumber()` returns `(optimal_number, scores_dataframe)`. Choosing a
state count from the same dataset and then testing selected-state effects can inflate
research flexibility. Prespecify or cross-validate clustering choices and assess
initialization stability.

## Preprocessing/reporting

At minimum report:

- hardware, montage/locations/reference/ground, unit, sample rate, online filters;
- resampling, offline filters/notches, edge handling, and line frequency;
- bad channels/segments and interpolation;
- ocular/muscle/cardiac correction and ICA details;
- epoch/baseline definitions and retained trials;
- PSD/time-frequency estimator and normalization;
- microstate input band/reference, GFP definition, training points, algorithm,
  state count, runs/seed, polarity, smoothing, and fit/stability; and
- exact NeuroKit2/MNE versions and observed schemas.

Avoid frequency-band mental-state labels such as “beta = anxiety” or
“theta/beta = ADHD.” EEG features are not diagnosis, consciousness monitoring,
anesthesia control, seizure detection, or neurofeedback va

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

