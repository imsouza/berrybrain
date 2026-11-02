---
id: sciref-neuropixels-analysis-analysis
name: "Scientific Ref: Post-Processing & Analysis Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (neuropixels-analysis): Post-Processing & Analysis Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "neuropixels analysis analysis"
  - "neuropixels analise analise"
  - "post-processing & analysis reference"
keywords:
  - "neuropixels"
  - "analysis"
  - "analise"
  - "specialized"
  - "scientific"
  - "reference"
  - "post"
---

# Post-Processing & Analysis Reference

Targets SI 0.105.0 (reviewed 2026-10-01). Recording-dependent examples are illustrative.
Use [QUALITY_METRICS.md](QUALITY_METRICS.md) for metric dependencies and caveats;
result columns below are not necessarily computation names.

## Sorting Analyzer

The `SortingAnalyzer` is the central object for post-processing.

### Create Analyzer
```python
import spikeinterface.full as si

# Create analyzer
analyzer = si.create_sorting_analyzer(
    sorting,
    recording,
    sparse=True,                    # Use sparse representation
    format='binary_folder',         # Storage format
    folder='analyzer_output'        # Save location
)
```

### Compute Extensions
```python
# Compute all standard extensions
analyzer.compute('random_spikes')       # Random spike selection
analyzer.compute('waveforms')           # Extract waveforms
analyzer.compute('templates')           # Compute templates
analyzer.compute('noise_levels')        # Noise estimation
analyzer.compute('principal_components')  # PCA
analyzer.compute('spike_amplitudes')
analyzer.compute('amplitude_scalings')    # Amplitude per spike
analyzer.compute('correlograms')        # Auto/cross correlograms
analyzer.compute('unit_locations')      # Unit locations
analyzer.compute('spike_locations')     # Per-spike locations
analyzer.compute('template_similarity') # Template similarity matrix
analyzer.compute('quality_metrics', metric_names=['snr', 'isi_violation', 'presence_ratio', 'amplitude_cutoff', 'firing_rate'])     # Quality metrics

# Or compute multiple at once
analyzer.compute([
    'random_spikes', 'waveforms', 'templates', 'noise_levels',
    'principal_components', 'spike_amplitudes', 'amplitude_scalings', 'correlograms',
    'unit_locations', 'quality_metrics'
])
```

### Save and Load
```python
# Save
analyzer.save_as(folder='analyzer_saved', format='binary_folder')

# Load
analyzer = si.load_sorting_analyzer('analyzer_saved')
```

## Quality Metrics

### Compute Metrics
```python
analyzer.compute('quality_metrics', metric_names=['snr', 'isi_violation', 'presence_ratio', 'amplitude_cutoff', 'firing_rate'])
qm = analyzer.get_extension('quality_metrics').get_data()
print(qm)
```

### Available Metrics

| Metric | Description | Good Values |
|--------|-------------|-------------|
| `snr` | Signal-to-noise ratio | > 5 |
| `isi_violations_ratio` | Rate-normalized ISI ratio | < 0.01 (not 1%) |
| `isi_violations_count` | ISI violation count | Low |
| `presence_ratio` | Fraction of recording with spikes | > 0.9 |
| `firing_rate` | Spikes per second | 0.1-50 Hz |
| `amplitude_cutoff` | Estimated missed spikes | < 0.1 |
| `amplitude_median` | Median spike amplitude | - |
| `amplitude_cv` | Coefficient of variation | < 0.5 |
| `drift_ptp` | Peak-to-peak drift (um) | < 40 |
| `drift_std` | Standard deviation of drift | < 10 |
| `drift_mad` | Median absolute deviation | < 10 |
| `sliding_rp_violation` | Sliding refractory period | < 0.05 |
| `sync_spike_2` | Synchrony with other units | < 0.5 |
| `isolation_distance` | Mahalanobis distance | > 20 |
| `l_ratio` | L-ratio (isolation) | < 0.1 |
| `d_prime` | Discriminability | > 5 |
| `nn_hit_rate` | Nearest neighbor hit rate | > 0.9 |
| `nn_miss_rate` | Nearest neighbor miss rate | < 0.1 |
| `silhouette_score` | Cluster silhouette | > 0.5 |

### Compute Specific Metrics
```python
analyzer.compute(
    'quality_metrics',
    metric_names=['snr', 'isi_violation', 'presence_ratio', 'firing_rate']
)
```

### Custom Quality Thresholds
```python
qm = analyzer.get_extension('quality_metrics').get_data()

# Define quality criteria
quality_criteria = {
    'snr': ('>', 5),
    'isi_violations_ratio': ('<', 0.01),
    'presence_ratio': ('>', 0.9),
    'firing_rate': ('>', 0.1),
    'amplitude_cutoff': ('<', 0.1),
}

# Filter good units
good_units = qm.query(
    "(snr > 5) & (isi_violations_ratio < 0.01) & (presence_ratio > 0.9)"
).index.tolist()

print(f"Good units: {len(good_units)}/{len(qm)}")
```

## Waveforms & Templates

### Extract Waveforms
```python
analyzer.compute('random_spikes', max_spikes_per_unit=500, seed=42)
analyzer.compute('waveforms', ms_before=1.5, ms_after=2.5)

# Get waveforms for a unit
waveforms = analyzer.get_extension('waveforms').get_waveforms_one_unit(unit_id=0)
print(f"Shape: {waveforms.shape}")  # (n_spikes, n_samples, n_channels)
```

### Compute Templates
```python
analyzer.compute('templates', operators=['average', 'std', 'median'])

# Get template
templates_ext = analyzer.get_extension('templates')
template = templates_ext.get_unit_template(unit_id=0, operator='average')
```

### Template Similarity
```python
analyzer.compute('template_similarity')
sim = analyzer.get_extension('template_similarity').get_data()
# Matrix of cosine similarities between templates
```

## Unit Locations

### Compute Locations
```python
analyzer.compute('unit_locations', method='monopolar_triangulation')
locations = analyzer.get_extension('unit_locations').get_data()
print(locations)  # x, y coordinates per unit
```

### Spike Locations
```python
analyzer.compute('spike_locations', method='center_of_mass')
spike_locs = analyzer.get_extension('spike_locations').get_data()
```

### Location Methods
- `'center_of_mass'` - Fast, less accurate
- `'monopolar_triangulation'` - More accurate, slower
- `'grid_convolution'` - Good balance

## Correlograms

### Auto-correlograms
```python
analyzer.compute('correlograms', window_ms=50, bin_ms=1)
correlograms, bins = analyzer.get_extension('correlograms').get_data()

# correlograms shape: (n_units, n_units, n_bins)
# Auto-correlogram for unit i: correlograms[i, i, :]
# Cross-correlogram units i,j: correlograms[i, j, :]
```

## Visualization

### Probe Map
```python
si.plot_probe_map(recording, with_channel_ids=True)
```

### Unit Templates
```python
# All units
si.plot_unit_templates(analyzer)

# Specific units
si.plot_unit_templates(analyzer, unit_ids=[0, 1, 2])
```

### Waveforms
```python
# Plot waveforms with template
si.plot_unit_waveforms(analyzer, unit_ids=[0])

# Waveform density
si.plot_unit_waveforms_density_map(analyzer, unit_ids=[0])
```

### Raster Plot
```python
si.plot_rasters(sorting, time_range=(0, 10))  # First 10 seconds
```

### Amplitudes
```python
analyzer.compute('spike_amplitudes')
analyzer.compute('amplitude_scalings')
si.plot_amplitudes(analyzer)

# Distribution
si.plot_all_amplitudes_distributions(analyzer)
```

### Correlograms
```python
# Auto-correlograms
si.plot_autocorrelogr

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

