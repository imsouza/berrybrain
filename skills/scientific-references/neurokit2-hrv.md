---
id: sciref-neurokit2-hrv
name: "Scientific Ref: Heart-rate variability and RSA"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (neurokit2): Heart-rate variability and RSA"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "neurokit2 hrv"
  - "heart-rate variability and rsa"
keywords:
  - "neurokit2"
  - "hrv"
  - "specialized"
  - "scientific"
  - "reference"
  - "neurokit"
  - "heart"
  - "rate"
---

# Heart-rate variability and RSA

Checked **2026-10-01** against NeuroKit2 0.2.13 stable runtime/source,
the official HRV API/tutorial, and HRV/RSA measurement guidance.

## Define the interval series

HRV analysis needs beat timing plus a defensible classification/correction policy.
Distinguish:

- **RR/RRI**: intervals between detected R peaks;
- **NN**: intervals between beats judged normal sinus beats; and
- **PP/PRV**: intervals between peripheral pulse peaks.

Do not relabel automatically corrected RR or PPG intervals as NN. Preserve raw waveform,
raw peaks, corrected peaks, excluded segments, correction categories, and interval units.

Accepted NeuroKit2 inputs include:

- a list/array of peak sample indices;
- marker/info objects from `ecg_peaks()`, `ppg_peaks()`, `ecg_process()`, or
  `bio_process()`; and
- a dict with `RRI` (milliseconds) and `RRI_Time` (seconds).

Always pass the sampling rate of the continuous signal in which peak indices were
defined.

## Current functions and schemas

```python
time = nk.hrv_time(peaks, sampling_rate=250)
frequency = nk.hrv_frequency(peaks, sampling_rate=250)
nonlinear = nk.hrv_nonlinear(peaks, sampling_rate=250)
all_domains = nk.hrv(peaks, sampling_rate=250)
```

All four return one-row DataFrames. `hrv()` concatenates the available domains and can
append RSA when its input contains processed respiration data. Columns vary with data
length, kwargs, available modalities, and release.

Pinned 0.2.13 observations:

- `hrv_time()` returned 25 columns, including `HRV_MeanNN`, `HRV_SDNN`,
  `HRV_RMSSD`, `HRV_SDSD`, `HRV_CVNN`, `HRV_CVSD`, robust interval summaries,
  `HRV_pNN50`, `HRV_pNN20`, `HRV_HTI`, and `HRV_TINN`. Long-segment indices
  (`SDANN*`, `SDNNI*`) can be NaN when duration is insufficient.
- `hrv_frequency()` returned exactly `HRV_ULF`, `HRV_VLF`, `HRV_LF`, `HRV_HF`,
  `HRV_VHF`, `HRV_TP`, `HRV_LFHF`, `HRV_LFn`, `HRV_HFn`, and `HRV_LnHF` in the
  default probe.
- `hrv_nonlinear()` returned Poincaré, asymmetry, fragmentation, DFA/MFDFA,
  entropy/fractal, Lempel–Ziv, and symbolic-dynamics columns. Stable 0.2.13 added
  default `HRV_Symbolic_EqualProb4_*` features.

Do not hard-code a “complete” HRV column list. Persist `list(result.columns)` and map
only prespecified outputs.

## Units and interval helpers

Time-domain metrics are milliseconds where applicable. For absolute band power in ms²,
use `hrv_frequency(..., normalize=False)`. The default `normalize=True` divides the
PSD by its maximum before band integration, so those powers must not be labeled ms².

```python
processed_rri, processed_time, interpolation_rate = nk.intervals_process(
    rri_ms,
    intervals_time=time_s,
    interpolate=True,
    interpolation_rate=4,
    detrend=None,
)
peaks = nk.intervals_to_peaks(rri_ms, sampling_rate=1000)
```

`intervals_process()` returns three objects: intervals in milliseconds, timestamps in
seconds, and interpolation rate. `intervals_to_peaks()` returns integer peak indices,
with a constructed first peak. Verify external-device interval definitions and dropped
beats before conversion.

## Recording duration

Duration requirements are metric-, population-, protocol-, and estimator-specific.
Use these conservative planning principles:

- Five minutes is the conventional standardized short-term HRV window.
- RMSSD can be computed on shorter windows, but ultra-short estimates require
  endpoint- and population-specific reliability/validity evidence.
- A spectral segment should contain enough cycles of the lowest frequency interpreted.
  Five minutes is a practical reference for conventional LF/HF short-term analysis.
- Do not interpret ULF from a short recording; it is conventionally associated with
  long, often 24-hour recordings.
- VLF physiological interpretation in short recordings is uncertain.
- Entropy, DFA, MFDFA, correlation dimension, and RQA need enough beats for stable
  estimation; defaults returning a number do not establish adequacy.

Do not compare metrics estimated from unequal durations without a validated strategy.
Report exact usable duration and beat count after exclusions, not nominal acquisition
duration.

## Ectopy and artifact policy

1. Inspect ECG/PPG quality and peak overlays.
2. Review the tachogram and interval histogram.
3. Identify non-sinus beats separately from detector errors when possible.
4. Report raw and corrected beat counts and percentage.
5. Limit interpolation/correction according to a prespecified exclusion rule.
6. Repeat key analyses under plausible correction choices.

`ecg_process()` requests artifact correction automatically in 0.2.13. If that is not
the planned policy, run `ecg_clean()` and `ecg_peaks()` explicitly.

Heavy correction can manufacture smooth HRV. A segment with excessive ectopy,
detachment, or motion may need exclusion rather than interpolation.

## Frequency domain

Stable signature:

```text
hrv_frequency(
  peaks, sampling_rate=1000,
  ulf=(0, 0.0033), vlf=(0.0033, 0.04),
  lf=(0.04, 0.15), hf=(0.15, 0.4), vhf=(0.4, 0.5),
  psd_method="welch", normalize=True, interpolation_rate=100, ...
)
```

Set `interpolation_rate=4` to approximate a common Kubios interpolation choice; set it
to `None` for already-interpolated intervals or Lomb–Scargle. Record detrending,
interpolation, PSD method, window/order, frequency bands, and normalization.

Stable `HRV_LFn` and `HRV_HFn` divide LF and HF by `HRV_TP`, which sums all five
requested bands (ULF, VLF, LF, HF, VHF). They are not the conventional LF/(LF+HF) and
HF/(LF+HF) definitions. Report the exact denominator rather than importing a textbook
interpretation from the column names. Zero/NaN band power does not prove absent
physiological modulation.

The bundled pipeline deliberately uses `normalize=False`, Welch, and 4 Hz
interpolation, records these choices, and gates frequency analysis on the span
between first and last corrected peaks. This span still does not certify that every
interval is usable: inspect exclusions, non-sinus beats, and correction burden.

Do **not** interpret `HRV_LFHF` as a direct “sympathovagal balance.” LF contains mixed
influences; HF depends on breathing frequency/depth and can miss respiratory variation
outside the default 0.15–0.4 Hz band.

## PPG-derived variability

PPG pulse timing includes pre-ejection and pulse-transit effects, and varies with site,
vascular state, posture, temperature, motion, contact pressure, and sensor design.
Label results PRV/PPG-derived HRV and validate against

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

