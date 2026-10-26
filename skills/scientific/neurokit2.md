---
id: sci-neurokit2
name: "Scientific: neurokit2"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Builds and audits reproducible NeuroKit2 research workflows for physiological time-series preprocessing, event/interval analysis, multimodal alignment, variability, and complexity. Use when code imports neurokit2 or needs its current APIs, schemas, and method-aware validation—not"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "neurokit2"
keywords:
  - "neurokit2"
  - "builds"
  - "audits"
  - "reproducible"
  - "neurokit"
  - "research"
  - "workflows"
---

# NeuroKit2

## Scope and evidence cutoff

Use this skill for method-aware, reproducible biosignal research with NeuroKit2. The
snapshot was checked on **2026-10-01** against:

- stable PyPI **0.2.13**, released 2026-03-02;
- Python metadata (`>=3.10`; classifiers 3.10–3.14) and wheel dependencies;
- GitHub release notes/tags, `NEWS.rst`, source at tag `v0.2.13`;
- official API pages/examples (the live site identified itself as
  `0.2.13.dev214`); and
- pinned 0.2.13 runtime signatures and synthetic output schemas.

The current wheel requires `pandas<3.0.0`. The refreshed core checks use Python 3.13,
NumPy 2.5.3, and pandas 2.3.3; forcing pandas 3 conflicts with upstream metadata.
API fragments below assume caller-provided arrays and imports. Optional MNE source
reconstruction, cvxEDA, EMD, and pyRQA paths are source-reviewed, not runtime-validated
by this refresh. Synthetic checks establish software behavior, not empirical validity.

The live documentation can be ahead of the stable wheel. Prefer the pinned runtime
for reproducible work and name both versions if consulting development docs.

## Boundary

NeuroKit2 is a research and educational toolbox. Do **not** present its output as:

- a diagnosis, treatment recommendation, patient-monitoring decision, or alarm;
- validation, certification, or regulatory evidence for a medical device; or
- proof that a physiological construct is measured validly in a new sensor,
  protocol, environment, population, or disease group.

Validate acquisition hardware, electrode/optode placement, units, sampling and clock
accuracy, preprocessing, detector/decomposition method, population, task, and
outcomes for the intended study. Preserve raw data and an auditable exclusion log.
Use deidentified local files only; do not place PHI in prompts, logs, examples, or
bundled fixtures.

## Reproducible installation

```bash
uv pip install "neurokit2==0.2.13"
```

For optional features, create a uv project, add only the packages actually required at
reviewed exact versions, and commit/review the resulting `uv.lock` before
`uv sync --locked`. NeuroKit2 exposes an upstream `full` extra, but this skill
intentionally does not install that floating transitive set in an automated workflow.
Optional capabilities can require MNE, cvxopt, Plotly, PyEMD, pyRQA, Pillow, OpenCV,
or file readers. Record the resolved environment with the analysis. Provision any MNE
data/template download as an explicit, checksummed study input. Do not install a moving
development branch for a reproducible study.

## Required data contract

Before processing, record:

1. signal identity and sensor/channel configuration;
2. native sampling rate in Hz and physical unit (or explicitly `arbitrary_unit`);
3. clock, timestamp origin, drift correction, and synchronization evidence;
4. polarity/orientation and acquisition-side filters/gain;
5. missing samples, discontinuities, saturation, flatlines, motion, and annotations;
6. whether event onsets are zero-based sample indices or seconds;
7. planned preprocessing order, methods, parameters, exclusions, and outputs; and
8. participant-level grouping needed to prevent leakage in later statistics.

Never infer units from a column name. Do not silently treat samples as milliseconds,
volts, microsiemens, or arbitrary units.

## Core workflow

### 1. Inspect before transforming

```bash
python skills/neurokit2/scripts/inspect_signal.py \
  --input recording.csv --root . --deidentified \
  --columns ECG,RSP,EDA --time-column time_s \
  --units ECG=mV,RSP=a.u.,EDA=uS
```

The inspector is bounded and emits no row values or paths. Resolve non-monotonic time,
duplicate samples, gaps, non-finite values, flat runs, and sampling-rate disagreement
before filtering.

### 2. Preserve preprocessing order

Use this default reasoning order, adapting it to the acquisition and cited method:

1. preserve immutable raw signal and annotations;
2. verify time base, units, polarity, clipping, gaps, and artifacts;
3. segment at long gaps; only interpolate short gaps under a declared policy;
4. apply modality-specific cleaning at the native sampling rate;
5. detect peaks/onsets or decompose components;
6. inspect quality outputs and raw overlays;
7. correct peaks only with logged categories and sensitivity checks;
8. derive rates/features;
9. align continuous modalities on a declared common time grid; and
10. map event indices to that grid, epoch, baseline, and analyze.

Do not resample binary markers or peak-index arrays as ordinary continuous signals.
Map their timestamps to the target grid. Filtering and interpolation can create edge
artifacts and false precision; retain masks for padded, missing, and rejected regions.

### 3. Treat schemas as runtime observations

Return columns depend on NeuroKit2 version, function, method, signal availability, and
analysis mode. Never claim that one column list is universal.

```python
signals, info = nk.ecg_process(ecg, sampling_rate=250)
observed_schema = {
    "columns": list(signals.columns),
    "info_keys": sorted(info),
}
```

Persist the observed schema with package version, method parameters, sampling rate, and
quality/exclusion summary. Reference files list verified default schemas for 0.2.13,
not guarantees for every method.

## Current patterns

### ECG, corrected peaks, and duration-aware HRV

In stable 0.2.13, `ecg_process()` performs cleaning, R-peak detection with
`correct_artifacts=True`, rate, default `averageQRS` quality, DWT delineation, and phase.

```python
signals, info = nk.ecg_process(ecg, sampling_rate=250, method="neurokit")
time_hrv = nk.hrv_time(info, sampling_rate=250)
```

Inspect `ECG_R_Peaks_Uncorrected` and `ECG_fixpeaks_*`; a corrected series is not
automatically a valid NN series. For frequency/nonlinear HRV, enforce metric-specific
duration and beat-count requirements. Five minutes is the conventional short-term
reference; ULF is a long-recording measure, and VLF interpretation from short records
is unsafe. Do not interpret LF/HF as a direct sympathovagal balance. PPG pulse-rate
variability is not interchangeable with ECG HRV.

Use the bounded pipeline:

```bash
python skills/neurokit2/scripts/ecg_hrv_pipeline.py \
  --synthetic --sampling-rate 250 --duration 300 \
  --domains time,frequency,nonlinear
```

The helper gates frequency analysis using the first-to-last corrected-peak span,
separately from recording duration. It uses Welch, 4 Hz interval interpolation, and
`normalize=False`; absolut

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

