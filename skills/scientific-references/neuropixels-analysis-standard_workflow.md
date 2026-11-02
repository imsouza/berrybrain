---
id: sciref-neuropixels-analysis-standard-workflow
name: "Scientific Ref: Standard Neuropixels Analysis Workflow"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (neuropixels-analysis): Standard Neuropixels Analysis Workflow"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "neuropixels analysis standard workflow"
  - "neuropixels analise standard workflow"
  - "standard neuropixels analysis workflow"
keywords:
  - "neuropixels"
  - "analysis"
  - "standard"
  - "workflow"
  - "analise"
  - "specialized"
  - "scientific"
  - "reference"
---

# Standard Neuropixels Analysis Workflow

Complete step-by-step guide for analyzing Neuropixels recordings from raw data to curated
units, using SpikeInterface 0.105.0 (reviewed 2026-10-01). Real-data/sorter/model
examples are illustrative; validate acquisition calibration, probe mapping and
segment time origins before running them.

## Overview

```
Raw Recording → Preprocessing → Motion Correction → Spike Sorting →
Postprocessing → Quality Metrics → Curation → Export
```

```python
import spikeinterface.full as si
import spikeinterface.curation as sc

si.set_global_job_kwargs(n_jobs=-1, chunk_duration="1s", progress_bar=True)
```

## 1. Data Loading

### Supported formats

```python
# Inspect streams first
stream_names, stream_ids = si.get_neo_streams("spikeglx", "/path/to/run_g0/")

# SpikeGLX (most common)
recording = si.read_spikeglx("/path/to/run_g0/", stream_name="imec0.ap")

# Open Ephys
recording = si.read_openephys("/path/to/experiment/")

# NWB
recording = si.read_nwb("/path/to/file.nwb")
```

### Verify recording properties

```python
print(f"Channels: {recording.get_num_channels()}")
print(f"Duration: {recording.get_total_duration():.1f}s")
print(f"Sampling rate: {recording.get_sampling_frequency()}Hz")
print(f"Probe: {recording.get_probe()}")
locations = recording.get_channel_locations()
```

## 2. Preprocessing

### Filter/reference chain (single shank; not full IBL destriping)

```python
rec = si.highpass_filter(recording, freq_min=400.0)
bad_channel_ids, channel_labels = si.detect_bad_channels(rec)
rec = rec.remove_channels(bad_channel_ids)
rec = si.phase_shift(rec)                                   # Requires inter_sample_shift metadata
rec = si.common_reference(rec, operator="median", reference="global")
```

A bandpass alternative (some labs prefer an explicit passband):

```python
rec = si.bandpass_filter(recording, freq_min=300.0, freq_max=6000.0)
rec = si.phase_shift(rec)
bad_channel_ids, _ = si.detect_bad_channels(rec)
rec = rec.remove_channels(bad_channel_ids)
rec = si.common_reference(rec, operator="median", reference="global")
```

### Spatial destriping (strong artifacts)

```python
rec = si.highpass_filter(recording, freq_min=400.0)
rec = si.phase_shift(rec)
rec = si.highpass_spatial_filter(rec)                       # destriping
rec = si.common_reference(rec, operator="median", reference="global")
```

### Save preprocessed data

```python
rec = rec.save(folder="preprocessed/", format="binary")
```

## 3. Motion/Drift Correction

### Check whether correction is needed

```python
from spikeinterface.sortingcomponents.peak_detection import detect_peaks
from spikeinterface.sortingcomponents.peak_localization import localize_peaks

noise_levels = si.get_noise_levels(rec, return_in_uV=False)
peaks = detect_peaks(rec, method='locally_exclusive', method_kwargs={'noise_levels': noise_levels, 'detect_threshold': 5, 'radius_um': 50.0})
peak_locations = localize_peaks(rec, peaks, method="center_of_mass")

si.plot_drift_raster_map(peaks=peaks, peak_locations=peak_locations, recording=rec, clim=(-50, 50))
```

### Apply correction

```python
# One-call correction with a preset
rec_corrected = si.correct_motion(rec, preset="nonrigid_fast_and_accurate", folder="motion/")
```

See [MOTION_CORRECTION.md](MOTION_CORRECTION.md) for the full estimate/interpolate pipeline
and DREDge usage.

## 4. Spike Sorting

### Recommended: Kilosort4

```python
sorting = si.run_sorter("kilosort4", rec_corrected, folder="sorting_KS4/", do_correction=False, verbose=True)

# With custom parameters
sorting = si.run_sorter(
    "kilosort4", rec_corrected, folder="sorting_KS4/",
    do_correction=False,  # Input is already motion-corrected.
    Th_universal=9,      # detection threshold
    Th_learned=8,
    batch_size=60000,
)
```

### Alternative sorters

```python
sorting = si.run_sorter("spykingcircus2", rec_corrected, folder="sc2/", apply_motion_correction=False)   # CPU
sorting = si.run_sorter("tridesclous2", rec_corrected, folder="tdc2/")    # CPU
sorting = si.run_sorter("mountainsort5", rec_corrected, folder="ms5/")    # CPU
```

### Compare multiple sorters

```python
sortings = {
    "kilosort4": si.run_sorter("kilosort4", rec_corrected, folder="ks4/", do_correction=False),
    "spykingcircus2": si.run_sorter("spykingcircus2", rec_corrected, folder="sc2/", apply_motion_correction=False),
}

comparison = si.compare_multiple_sorters(list(sortings.values()),
                                         name_list=list(sortings.keys()))
agreement = comparison.get_agreement_sorting(minimum_agreement_count=2)
```

## 5. Postprocessing

### Create analyzer and compute extensions

```python
analyzer = si.create_sorting_analyzer(sorting, rec_corrected, sparse=True,
                                      format="binary_folder", folder="analyzer/")

analyzer.compute("random_spikes", method="uniform", max_spikes_per_unit=500)
analyzer.compute("waveforms", ms_before=1.0, ms_after=2.0)
analyzer.compute("templates", operators=["average", "std"])
analyzer.compute("noise_levels")
analyzer.compute("spike_amplitudes")
analyzer.compute("amplitude_scalings")
analyzer.compute("correlograms", window_ms=50.0, bin_ms=1.0)
analyzer.compute("unit_locations", method="monopolar_triangulation")
analyzer.compute("template_similarity")
```

## 6. Quality Metrics

```python
metric_names = ["snr", "isi_violation", "presence_ratio", "amplitude_cutoff",
                "firing_rate", "amplitude_cv", "sliding_rp_violation"]
analyzer.compute("quality_metrics", metric_names=metric_names)
metrics = analyzer.get_extension("quality_metrics").get_data()
print(metrics.head())
```

### Key metrics

| Metric (column) | Good value | Description |
|-----------------|------------|-------------|
| `snr` | > 5 | Signal-to-noise ratio |
| `isi_violations_ratio` | < 0.5 (strict: < 0.01) | Refractory period violations |
| `presence_ratio` | > 0.9 | Fraction of recording with spikes |
| `amplitude_cutoff` | < 0.1 | Estimated missed spikes |
| `firing_rate` | > 0.1 Hz | Average firing rate |

## 7. Curation

### Threshold-based

```python
query = "(amplitude_cutoff < 0.1) & (isi_violations_ratio < 0.5) & (presence_ratio > 0.9)"
good_unit_ids = metrics.query(query).index.values
```

For local `allen` / legacy `ibl` / `strict` screening presets (not IBL standards) in one call, use `scripts/compute_metrics.py`.

### Model-based (UnitRefine)

First inspect [model compatibility and required features](AUTOMATED_CURATION.md).
The public models a

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

