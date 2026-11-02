---
id: sciref-neuropixels-analysis-plotting-guide
name: "Scientific Ref: Plotting Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (neuropixels-analysis): Plotting Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "neuropixels analysis plotting guide"
  - "neuropixels analise plotting guide"
  - "plotting guide"
keywords:
  - "neuropixels"
  - "analysis"
  - "plotting"
  - "guide"
  - "analise"
  - "specialized"
  - "scientific"
  - "reference"
---

# Plotting Guide

Targets SI 0.105.0 (reviewed 2026-10-01). Examples assume one continuous segment,
calibrated amplitudes and computed extensions. Real-data figures are illustrative.

## Setup

```python
import matplotlib.pyplot as plt
import numpy as np
import spikeinterface.full as si
import spikeinterface.widgets as sw

# High-quality settings
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'sans-serif'
```

## Drift and Motion Plots

### Basic Drift Map

```python
from spikeinterface.sortingcomponents.peak_detection import detect_peaks
from spikeinterface.sortingcomponents.peak_localization import localize_peaks

noise_levels = si.get_noise_levels(recording, return_in_uV=False)
peaks = detect_peaks(recording, method='locally_exclusive', method_kwargs={'noise_levels': noise_levels, 'detect_threshold': 5, 'radius_um': 50.0})
peak_locations = localize_peaks(recording, peaks, method='center_of_mass')

si.plot_drift_raster_map(
    peaks=peaks,
    peak_locations=peak_locations,
    recording=recording,
    clim=(-50, 50),
)
plt.savefig('drift_raster.png', bbox_inches='tight')
```

### Motion Estimate Visualization

`correct_motion(..., output_motion_info=True)` returns `(recording, motion_info)`. The
`motion_info` dict can be plotted directly with the built-in widget:

```python
rec_corrected, motion_info = si.correct_motion(
    recording, preset='nonrigid_fast_and_accurate', output_motion_info=True, folder='motion/'
)

# Built-in motion visualization (drift raster + motion field)
sw.plot_motion_info(motion_info, recording=recording)
plt.savefig('motion_analysis.png', dpi=300, bbox_inches='tight')

# Or inspect the Motion object directly
motion = motion_info['motion']
displacement = motion.displacement[0]          # (n_temporal_bins, n_spatial_bins)
temporal_bins = motion.temporal_bins_s[0]
plt.figure(figsize=(10, 4))
plt.plot(temporal_bins, displacement, alpha=0.5)
plt.xlabel('Time (s)'); plt.ylabel('Displacement (um)'); plt.title('Estimated Motion')
plt.savefig('motion_traces.png', dpi=300, bbox_inches='tight')
```

## Waveform Plots

### Single Unit Waveforms

```python
unit_id = 0

# Basic waveforms
sw.plot_unit_waveforms(analyzer, unit_ids=[unit_id])
plt.savefig(f'unit_{unit_id}_waveforms.png')

# With density map
sw.plot_unit_waveforms_density_map(analyzer, unit_ids=[unit_id])
plt.savefig(f'unit_{unit_id}_density.png')
```

### Template Comparison

```python
# Compare multiple units
unit_ids = [0, 1, 2, 3]
sw.plot_unit_templates(analyzer, unit_ids=unit_ids)
plt.savefig('template_comparison.png')
```

### Waveforms on Probe

```python
# Show waveforms spatially on probe
sw.plot_unit_waveforms(
    analyzer,
    unit_ids=[unit_id],
    plot_channels=True,
)
plt.savefig(f'unit_{unit_id}_probe.png')
```

## Quality Metrics Visualization

### Metrics Overview

```python
# Built-in quality-metrics widget (scatter matrix of all computed metrics)
sw.plot_quality_metrics(analyzer)
plt.savefig('quality_overview.png', dpi=300, bbox_inches='tight')
```

### Metrics Distribution

```python
fig, axes = plt.subplots(2, 3, figsize=(12, 8))

metric_names = ['snr', 'isi_violations_ratio', 'presence_ratio',
                'amplitude_cutoff', 'firing_rate', 'amplitude_cv_median']

for ax, metric in zip(axes.flat, metric_names):
    if metric in metrics.columns:
        values = metrics[metric].dropna()
        ax.hist(values, bins=30, edgecolor='black', alpha=0.7)
        ax.axvline(values.median(), color='red', linestyle='--', label='median')
        ax.set_xlabel(metric)
        ax.set_ylabel('Count')
        ax.legend()

plt.tight_layout()
plt.savefig('metrics_distribution.png', dpi=300)
```

### Metrics Scatter Matrix

```python
import pandas as pd

key_metrics = ['snr', 'isi_violations_ratio', 'presence_ratio', 'firing_rate']
pd.plotting.scatter_matrix(
    metrics[key_metrics],
    figsize=(10, 10),
    alpha=0.5,
    diagonal='hist',
)
plt.savefig('metrics_scatter.png', dpi=300)
```

### Metrics vs Labels

```python
labels_series = pd.Series(labels)

fig, axes = plt.subplots(1, 3, figsize=(12, 4))

for ax, metric in zip(axes, ['snr', 'isi_violations_ratio', 'presence_ratio']):
    for label in ['good', 'mua', 'noise']:
        mask = labels_series == label
        if mask.any():
            ax.hist(metrics.loc[mask.index[mask], metric],
                   alpha=0.5, label=label, bins=20)
    ax.set_xlabel(metric)
    ax.legend()

plt.tight_layout()
plt.savefig('metrics_by_label.png', dpi=300)
```

## Correlogram Plots

### Autocorrelogram

```python
sw.plot_autocorrelograms(
    analyzer,
    unit_ids=[unit_id],
    window_ms=50,
    bin_ms=1,
)
plt.savefig(f'unit_{unit_id}_acg.png')
```

### Cross-correlograms

```python
analyzer.compute("template_similarity")
unit_pairs = [(0, 1), (0, 2), (1, 2)]
sw.plot_crosscorrelograms(
    analyzer,
    unit_ids=sorted(set(uid for pair in unit_pairs for uid in pair)),
    window_ms=50,
    bin_ms=1,
)
plt.savefig('crosscorrelograms.png')
```

### Correlogram Matrix

```python
sw.plot_autocorrelograms(
    analyzer,
    unit_ids=analyzer.sorting.unit_ids[:10],  # First 10 units
)
plt.savefig('acg_matrix.png')
```

## Spike Train Plots

### Raster Plot

```python
sw.plot_rasters(
    sorting,
    time_range=(0, 30),  # First 30 seconds
    unit_ids=unit_ids[:5],
)
plt.savefig('raster.png')
```

### Firing Rate Over Time

```python
unit_id = 0
spike_train = sorting.get_unit_spike_train(unit_id)
fs = recording.get_sampling_frequency()
times = spike_train / fs

# Compute firing rate histogram
bin_width = 1.0  # seconds
duration = recording.get_total_duration()
bins = np.append(np.arange(0, duration, bin_width), duration)
hist, _ = np.histogram(times, bins=bins)
firing_rate = hist / np.diff(bins)

plt.figure(figsize=(12, 3))
plt.bar(bins[:-1], firing_rate, width=np.diff(bins), align="edge", edgecolor='none')
plt.xlabel('Time (s)')
plt.ylabel('Firing rate (Hz)')
plt.title(f'Unit {unit_id} firing rate')
plt.savefig(f'unit_{unit_id}_firing_rate.png', dpi=300)
```

## Probe and Location Plots

### Probe Layout

```python
sw.plot_probe_map(recording, with_channel_ids=True)
plt.savefig('probe_layout.png')
```

### Unit Locations on Probe

```python
sw.plot_unit_locations(analyzer, with_channel_ids=True)
plt.savefig('unit_locations.png')
```

### Spike Locations

```python
sw.plot_spike_locations(analyzer, unit_ids=[unit_id])
plt.savefig(f'unit_{unit_id}_spike_locations.png')
`

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

