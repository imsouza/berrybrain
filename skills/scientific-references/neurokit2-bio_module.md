---
id: sciref-neurokit2-bio-module
name: "Scientific Ref: Multimodal processing with `bio_process`"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (neurokit2): Multimodal processing with `bio_process`"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "neurokit2 bio module"
  - "multimodal processing with `bio_process`"
keywords:
  - "neurokit2"
  - "bio"
  - "module"
  - "specialized"
  - "scientific"
  - "reference"
  - "neurokit"
  - "multimodal"
  - "processing"
---

# Multimodal processing with `bio_process`

Checked **2026-10-01** against NeuroKit2 0.2.13 stable source/runtime
and the official Bio API/examples.

## What `bio_process()` does—and does not do

Stable signature:

```text
bio_process(
  ecg=None, rsp=None, eda=None, emg=None,
  ppg=None, eog=None, keep=None, sampling_rate=1000
)
```

It dispatches each non-`None` vector to the modality's `*_process()` function,
concatenates outputs by pandas index, adds `keep`, and computes continuous RSA when ECG
and RSP are both present.

It does **not**:

- infer or accept one native sampling rate per modality;
- synchronize clocks, estimate lag/drift, or align timestamps;
- automatically resample streams to `sampling_rate`;
- reject unequal lengths before concatenation;
- standardize units; or
- return a nested modality-info structure.

Passing ECG at 1000 Hz and EDA at 100 Hz with `sampling_rate=1000` falsely tells the
EDA processor that its samples are 1000 Hz. Unequal lengths are outer-concatenated by
index and can introduce NaN. Align first.

## Flat output schema

```python
bio_signals, bio_info = nk.bio_process(
    ecg=ecg_aligned,
    rsp=rsp_aligned,
    eda=eda_aligned,
    sampling_rate=100,
)
```

`bio_signals` is one wide DataFrame. With pinned synthetic ECG+RSP+EDA, it contained
43 columns:

- 19 ECG raw/clean/rate/quality/peaks/delineation/phase columns;
- 11 RSP raw/clean/amplitude/rate/RVT/phase/symmetry/extrema columns;
- 11 EDA raw/clean/tonic/phasic/SCR columns; and
- `RSA_P2T`, `RSA_Gates`.

`bio_info` is one flat dict built with repeated `dict.update()`. The pinned run
contained prefixed ECG/RSP/SCR keys, method metadata, and one `sampling_rate`; it did
not support:

```python
bio_info["ECG"]["ECG_R_Peaks"]  # wrong for stable 0.2.13
```

Use:

```python
rpeaks = bio_info["ECG_R_Peaks"]
rsp_troughs = bio_info["RSP_Troughs"]
```

Output columns depend on provided modalities, methods, optional dependencies, and
release. Save `list(bio_signals.columns)` and `sorted(bio_info)`.

## Alignment workflow

### 1. Preserve native clocks

For each stream record:

- timestamp origin/time zone or monotonic device time;
- native rate and observed timestamp intervals;
- dropped/duplicate/backward samples;
- clock reset, drift, and synchronization events;
- sensor latency and acquisition filters; and
- unit, polarity, and artifact mask.

Do not align only by truncating arrays to equal length.

### 2. Establish synchronization evidence

Prefer:

1. one acquisition system/shared clock;
2. common hardware trigger captured on each device;
3. validated timestamps with drift correction; or
4. a documented manual alignment with uncertainty.

Cross-correlation can support QC when signals share physiology, but a correlation peak
can be ambiguous and physiologically lagged. It is not a replacement for a clock.

### 3. Process at native rates

Apply modality-specific cleaning, peak detection, decomposition, and quality at the
correct native rate. Preserve native event/peak timestamps.

### 4. Build a common grid

Choose the target rate from the fastest retained continuous feature and analysis—not
convenience. Anti-alias downsampling; report interpolation/filter method and edge
validity. Map discrete peaks/triggers by time, using an explicit rounding/tolerance
policy; never spline binary markers.

### 5. Validate before `bio_process()`

The bundled validator accepts a strict JSON manifest:

```json
{
  "schema_version": "1.0",
  "streams": [
    {
      "name": "ECG",
      "path": "ecg.csv",
      "value_column": "ECG",
      "time_column": "time_s",
      "sampling_rate_hz": 250,
      "unit": "mV"
    },
    {
      "name": "RSP",
      "path": "rsp.csv",
      "value_column": "RSP",
      "time_column": "time_s",
      "sampling_rate_hz": 50,
      "unit": "a.u."
    }
  ],
  "alignment": {
    "reference_stream": "ECG",
    "synchronization": "shared_clock",
    "max_start_offset_ms": 2,
    "minimum_overlap_s": 60
  }
}
```

```bash
python skills/neurokit2/scripts/validate_multimodal.py \
  --manifest streams.json --root . --deidentified
```

The validator reports units, rates, timestamp order/jitter, missingness, starts, common
overlap, and whether streams meet its numerical requirements for `bio_process()`.
It checks all observed timestamps against each stream's declared regular grid and
against corresponding reference-stream timestamps, allowing at most half a sample.
Equal starts/rates/counts can conceal accumulating drift or interior timing jumps.
Without a time column, the assumed uniform grid is marked as declared, not observed.
`valid` describes the manifest checks; direct compatibility is a separate field.
Neither field validates synchronization hardware, sensor latency, or physiology. It
does not resample or modify data.

## `keep`

`keep` must be a pandas Series or DataFrame and is concatenated after processed
modalities. It is useful for a pre-aligned trigger or covariate:

```python
bio_signals, bio_info = nk.bio_process(
    ecg=ecg,
    rsp=rsp,
    keep=aligned[["Trigger"]],
    sampling_rate=100,
)
```

Verify equal index/length first. Do not use `keep` for participant identifiers or PHI.

## EOG and optional dependencies

The high-level Bio wrapper calls `eog_process()` without exposing an EOG method.
Stable EOG peak detection defaults to MNE, which is optional. A core-only environment
can therefore fail when `eog` is supplied. Process EOG explicitly with a chosen method
and merge after alignment, or add MNE at a reviewed exact version to the project lock.

## RSA

When both ECG and RSP are present, stable `bio_process()` adds continuous:

```text
RSA_P2T, RSA_Gates
```

This assumes the arrays already represent synchronized samples at the supplied rate.
It does not check respiration polarity, sensor lag, clock drift, or R-peak validity.
For summary RSA:

```python
rsa = nk.hrv_rsa(
    bio_signals,
    bio_signals,
    rpeaks=bio_info,
    sampling_rate=100,
    continuous=False,
)
```

Report the RSA method/output family, respiration behavior, usable cycles/windows, and
alignment uncertainty. See `hrv.md`.

## `bio_analyze()`

```text
bio_analyze(
  data, sampling_rate=1000, method="auto",
  window_lengths="constant"
)
```

It detects available column prefixes and joins modality-specific analysis. With
interval-related data it can add summary RSA. `method="auto"` uses event-related mode
when mean duration is under 10 seconds; use explicit `event-related` or
`interval-re

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

