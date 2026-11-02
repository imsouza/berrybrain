---
id: sciref-matchms-similarity
name: "Scientific Ref: Similarity and Scores (matchms 0.33.1)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matchms): Similarity and Scores (matchms 0.33.1)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matchms similarity"
  - "similarity and scores (matchms 0.33.1)"
keywords:
  - "matchms"
  - "similarity"
  - "specialized"
  - "scientific"
  - "reference"
  - "scores"
---

# Similarity and Scores (matchms 0.33.1)

Use this reference to select a similarity class, interpret its output, extract
top hits, or scale a comparison. The authoritative API is
[`matchms.similarity`](https://matchms.readthedocs.io/en/latest/api/matchms.similarity.html).

## Core Calculation

```python
from matchms import calculate_scores
from matchms.similarity import CosineGreedy

metric = CosineGreedy(tolerance=0.02)
scores = calculate_scores(
    references=reference_spectra,
    queries=query_spectra,
    similarity_function=metric,
    array_type="numpy",
    is_symmetric=False,
)
```

Set `is_symmetric=True` only when references and queries are the same collection
in the same order and the metric is symmetric.

## Understand the Output Before Indexing

`Scores.scores` is a `sparsestack.StackedSparseArray`, not a plain two-dimensional
NumPy array. Its shape is `(n_references, n_queries, n_score_fields)`.

Cosine-family methods produce two fields:

```python
print(scores.score_names)
# ('CosineGreedy_score', 'CosineGreedy_matches')

similarities = scores.to_array("CosineGreedy_score")
matched_peaks = scores.to_array("CosineGreedy_matches")
```

Scalar methods such as `FlashSimilarity`, `PrecursorMzMatch`, and
`FingerprintSimilarity` produce one field named after the class.

### Top hits for one query

```python
score_name = "CosineGreedy_score"
matches_name = "CosineGreedy_matches"

ranked = scores.scores_by_query(query_spectrum, name=score_name, sort=True)
for reference, value in ranked[:10]:
    print(
        reference.get("spectrum_id"),
        float(value[score_name]),
        int(value[matches_name]),
    )
```

The first tuple item is the actual reference `Spectrum`, not an integer index.
The second item can be a structured NumPy record containing every score field.

### Iterate stored pairs

```python
for reference, query, values in scores:
    print(reference.get("id"), query.get("id"), values)
```

Iteration covers stored coordinates. After sparse filtering, that may be only a
subset of the Cartesian product.

## Peak-Based Cosine Methods

All cosine classes below use:

```text
tolerance=0.1, mz_power=0.0, intensity_power=1.0
```

unless noted otherwise. Tolerance is in daltons for these classes.

### `CosineGreedy`

Greedily assigns candidate peak pairs within tolerance.

Use for:

- routine spectral-library comparisons;
- a transparent baseline;
- moderate collections where exact assignment is not essential.

Output fields: `CosineGreedy_score`, `CosineGreedy_matches`.

### `CosineHungarian`

Uses optimal assignment rather than greedy assignment.

Use for:

- benchmarking peak-assignment effects;
- smaller datasets;
- cases where greedy ambiguity materially affects results.

It is computationally more expensive than `CosineGreedy`.

### `CosineLinear`

Added in 0.33.0. It first greedily merges nearby peaks using a `2 * tolerance`
separation criterion, then performs linear-time matching on the merged spectra.
The score and matched-peak count therefore need not equal `CosineGreedy` on the
original peaks, even with identical tolerance and intensity powers.

Use when:

- cosine is the intended metric;
- matrix size makes assignment cost important; and
- you have benchmarked agreement and runtime on representative spectra.

Output fields: `CosineLinear_score`, `CosineLinear_matches`.

## Modified Cosine

Modified cosine allows unshifted peak matches and matches shifted by the
difference in precursor m/z. Both spectra need valid `precursor_mz`.

### `ModifiedCosineGreedy`

```python
from matchms.similarity import ModifiedCosineGreedy

metric = ModifiedCosineGreedy(tolerance=0.02)
```

This is the current name for the implementation formerly called
`ModifiedCosine`. It uses greedy assignment.

### `ModifiedCosineHungarian`

```python
from matchms.similarity import ModifiedCosineHungarian

metric = ModifiedCosineHungarian(tolerance=0.02)
```

Use for exact modified-cosine assignment in benchmarks or method development.
It is slower than the greedy variant.

Do not infer that a shifted match proves a specific chemical transformation.
Inspect precursor delta, adduct/charge compatibility, shifted peaks, and
orthogonal annotations.

## Neutral-Loss Cosine

```python
from matchms.similarity import NeutralLossesCosine

metric = NeutralLossesCosine(
    tolerance=0.02,
    ignore_peaks_above_precursor=True,
)
```

`NeutralLossesCosine` computes losses from `precursor_mz - fragment_mz`.
Both spectra require precursor m/z. Do not call the removed `add_losses()`
filter; losses are computed on demand in current matchms.

Output fields: `NeutralLossesCosine_score`,
`NeutralLossesCosine_matches`.

## Fast Matrix-Oriented Methods

### `BlinkCosine`

BLINK-style approximate cosine:

```python
from matchms.similarity import BlinkCosine

metric = BlinkCosine(
    tolerance=0.01,
    bin_width=0.001,
    min_relative_intensity=0.01,
    top_k=None,
    batch_size=1024,
    sparse_score_min=0.0,
)
```

Important parameters include peak preprocessing, precursor cropping, batch
size, and sparse score minimum. By default `crop_above_precursor=True` crops
where a precursor is available; record precursor coverage or disable this
option when that extra step is inappropriate. Output contains a float32 score
and matched-peak count. Validate approximation behavior against `CosineGreedy` on a subset
before changing production workflows.

### `FlashSimilarity`

Fast matrix scoring based on the Flash Entropy approach:

```python
from matchms.similarity import FlashSimilarity

entropy = FlashSimilarity(
    score_type="spectral_entropy",
    matching_mode="fragment",
    tolerance=0.02,
)

fast_modified_cosine = FlashSimilarity(
    score_type="cosine",
    matching_mode="hybrid",
    tolerance=0.02,
)
```

Current choices and behavior:

- `score_type`: `spectral_entropy` or `cosine`
- `matching_mode`: `fragment`, `neutral_loss`, or `hybrid`
- `use_ppm=True` switches fragment tolerance to symmetric ppm; default is Da
- `remove_precursor=False`, `noise_cutoff=0.01`, `merge_within=0`, and
  `normalize_to_half=True` are defaults; entropy weighting is internal
- neutral-loss/hybrid matching and an identity precursor gate need valid
  precursor metadata
- `identity_precursor_tolerance` and `identity_use_ppm` control a separate
  precursor gate

`pair()` exists but emits a warning because it is not the optimized use. Call
`calculate_scores()` for multi-spectrum matrices. A 1-by-1 `Scores.calculate`
call 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

