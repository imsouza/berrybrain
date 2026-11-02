---
id: sciref-scvelo-velocity-models
name: "Scientific Ref: Velocity models and interpretation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scvelo): Velocity models and interpretation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scvelo velocity models"
  - "velocity models and interpretation"
keywords:
  - "scvelo"
  - "velocity"
  - "models"
  - "specialized"
  - "scientific"
  - "reference"
---

# Velocity models and interpretation

Reviewed 2026-10-01 for scVelo 0.3.4. API examples below assume the
preprocessed `adata` from the main workflow, including `Ms`, `Mu`, a neighbors
graph and, for dynamical operations, fitted dynamics. The core runtime stack
and its stochastic/pandas limitations are specified in `SKILL.md`.

## Kinetic framework

For unspliced abundance `u` and spliced abundance `s`:

```text
du/dt = alpha(t) - beta*u
ds/dt = beta*u - gamma*s
velocity = ds/dt
```

A positive velocity means increasing spliced abundance **under the fitted
model**, not guaranteed induction of an entire cell program. Rates, relative
scaling of the two modalities and inferred time can trade off. Snapshot data
alone do not identify an absolute biological clock.

| Model | Assumption and appropriate diagnostic |
| --- | --- |
| `deterministic` (`steady_state` alias) | Fits a steady-state spliced/unspliced relationship from expression extremes; requires informative steady-state coverage |
| `stochastic` | Adds second-order moments to the steady-state treatment; depends on neighborhood estimates and the same biological assumptions |
| `dynamical` | Fits induction/repression kinetics and cell-specific times, relaxing observed steady-state requirements but retaining the specified kinetic model |

The dynamical model usually costs more. None of these names guarantees accuracy
or publication readiness. Incomplete cycles, changing rates across branches,
transcriptional bursts, mature populations without true transitions and
measurement biases can make seemingly coherent estimates wrong.

```python
# Tested on the current core stack:
scv.tl.velocity(adata, mode='deterministic')

# Dynamical fitting must precede dynamical velocity:
scv.tl.recover_dynamics(adata, var_names='all', n_jobs=1, show_progress_bar=False)
scv.tl.velocity(adata, mode='dynamical')
```

These are alternative analyses on separately prepared objects. Default
`recover_dynamics(var_names='velocity_genes')` can select genes using an initial
steady-state estimate; explicit `var_names='all'` fits all genes in the already
filtered analysis object. It does not restore excluded genes.

The default stochastic GLS path is **not supported by the tested NumPy 2 stack**.
Do not enable offsets or substitute another estimator solely to bypass an API
failure: those choices change model assumptions. A legacy NumPy<2 environment
also needs an older compatible Scanpy/SciPy/Python combination, which was not
executed in this review.

## Graphs and projections

```python
scv.tl.velocity_graph(adata, n_jobs=1, show_progress_bar=False)
T = scv.utils.get_transition_matrix(adata)
```

`uns['velocity_graph']` stores positive cosine correlations between expression
changes and velocity; `velocity_graph_neg` stores the negative part. They are
not normalized probabilities. The transition utility applies a kernel and
normalization; check finite/nonnegative entries, each row sum, isolated cells,
and self-transition choices before using `T` for a Markov calculation. Changing
the kernel, connectivity blend or terminal states changes inferred fates.

For `velocity_graph`, `approx=True` performs cosine calculations in a reduced
PCA representation (first 30 PCs); it does **not** select an approximate nearest
neighbor backend. `sqrt_transform=None` is model-dependent in the released
implementation. Set it explicitly only with a scientific reason.

UMAP streams are interpolated projections of high-dimensional estimates, with
additional grid smoothing. Arrows can bridge populations that are not real
transitions. Check gene-space phase portraits and sensitivity to embedding,
neighbors and selected genes before interpreting projected topology.

## Relative time and fit diagnostics

`layers['fit_t']` contains gene-specific fitted coordinates; it does not impose
universal landmarks such as peak induction at 0.5. `tl.latent_time` filters genes
by likelihood, aligns/root-adjusts gene times, builds a shared time and smooths
it using neighborhood information. It can incorporate velocity-pseudotime
information. It is not simply a likelihood-weighted mean.

```python
scv.tl.latent_time(adata)  # requires fitted dynamics and a velocity graph
scv.pl.scatter(adata, color='latent_time', basis='umap', show=False)
```

The default output is scaled to 0–1. `t_max` rescales that ordering; supplying a
number does not measure hours. `root_key` and `end_key` encode root/end priors;
record external evidence for those priors and assess direction sensitivity.
There is no `t_max_rank` argument in the current latent-time API.

- `fit_likelihood` is a fit score, not causal evidence or a calibrated probability
  that a gene is biologically correct. Threshold 0.1 is an implementation default
  in some downstream methods, not a universal scientific cutoff.
- `fit_r2` reflects the steady-state regression used during fitting/selection;
  it is not a complete validation of the nonlinear kinetic model.
- `velocity_length` is processed-space vector magnitude, dependent on feature
  scaling and gene selection. It is not comparable physical cell speed.
- scVelo 0.3.4 clips negative neighbor correlations to zero for
  `velocity_confidence`; ordinary finite scores lie around 0–1. Zero-vector
  degeneracy can produce NaNs. Report nonfinite cells, rather than describing
  a coherence cutoff as a probability of correctness.
- `rank_velocity_genes` compares group-associated velocities. It does not show
  perturbational causality or replace biological-replicate-aware condition DE.

Diagnostic plotting uses existing functions:

```python
scv.pl.proportions(adata, groupby='clusters', show=False)
scv.tl.velocity_confidence(adata)
scv.pl.scatter(adata, color='velocity_confidence', show=False)
```

There is no `scv.pl.velocity_confidence` function in 0.3.4. Use pandas
`DataFrame` for the structured gene-ranking table, not removed
`scv.DataFrame` aliases.

## Preprocessing with Scanpy

In 0.3.4, `filter_and_normalize` filters genes and normalizes per cell; its stale
docstring still mentions log transformation. It no longer performs logging/HVG
selection. Apply `sc.pp.log1p` to X and `sc.pp.highly_variable_genes` explicitly.
Spliced/unspliced layers remain linear. A preprocessed Scanpy X is not evidence
that those layers have been normalized correctly.

Rebuild PCA and neighbors after selecting the velocity feature set. Reusing
an integration-derived graph is a separate analysis choice: batch correction
changes

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

