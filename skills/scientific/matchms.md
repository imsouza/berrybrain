---
id: sci-matchms
name: "Scientific: matchms"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Processes, cleans, compares, and searches tandem mass spectra with matchms. Use for MS/MS file I/O, metadata harmonization, peak filtering, spectral similarity, library matching, score matrices, and molecular-similarity networks. Use pyopenms instead for LC-MS feature detection o"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "matchms"
keywords:
  - "matchms"
  - "processes"
  - "cleans"
  - "compares"
  - "searches"
  - "tandem"
  - "mass"
---

# Matchms

## Purpose and Scope

Matchms is a Python package for importing, cleaning, processing, and comparing
tandem mass spectra. This skill targets **matchms 0.33.1**, released 2026-06-08,
verified again on 2026-10-01. Older tutorials can use removed names; see the
migration reference.

Use matchms for:

- MS/MS library search and query-versus-reference scoring
- Metadata harmonization, adduct/precursor handling, and peak filtering
- Cosine, modified-cosine, neutral-loss, approximate, and entropy scoring
- Structured score matrices, top-hit extraction, and spectral networks
- MGF, MSP, mzML, mzXML, JSON, mzSpecLib, and metabolomics-USI workflows

Do not use matchms as a replacement for:

- LC-MS feature detection, chromatographic alignment, peptide identification, or
  protein quantification — use pyopenms
- Vendor raw-file conversion — convert to mzML/mzXML first
- A validated compound-identification protocol — similarity is evidence, not
  proof of identity

## Install the Verified Release

Create or activate an environment, then install the release used by this skill:

```bash
uv pip install "matchms==0.33.1"
```

Verify the runtime:

```bash
uv run python -c "import matchms; print(matchms.__version__)"
```

Matchms 0.33.1 supports Python 3.10-3.14 and installs RDKit as a regular
dependency. The old `matchms[chemistry]` extra is not part of the current
package metadata.

## Operating Workflow

1. **Inspect the inputs.** Record format, spectrum count, MS level, precursor
   coverage, ion mode, peak counts, and identifier fields.
2. **Load with metadata harmonization enabled** by default. Retain original
   files: disabling the flag in 0.33.1 still harmonizes metadata keys.
3. **Apply the same peak-processing steps** to query and reference spectra.
   Keep metadata enrichment separate when reference annotations are richer.
4. **Drop invalid spectra explicitly.** Many `require_*` filters return `None`.
5. **Choose the score from the scientific question**, not from convenience.
   Modified and neutral-loss scores require valid `precursor_mz`.
6. **Estimate `len(references) * len(queries)` before scoring.** A sparse result
   container does not automatically avoid computing every requested pair.
7. **Report score settings and evidence.** Include tolerance **and units**, preprocessing,
   score name, number of matched peaks when available, and candidate metadata.
   The cosine-family `tolerance` is an absolute m/z window in Da, not ppm;
   a precursor filter with `tolerance_type="ppm"` does not change fragment tolerance.
8. **Validate top hits visually and chemically.** Use mirror plots, precursor
   agreement, ion/adduct compatibility, and orthogonal evidence.

## Current API Guardrails

These points prevent the most common failures from pre-0.33 examples:

- Use `ModifiedCosineGreedy` or `ModifiedCosineHungarian`; `ModifiedCosine` was
  removed in 0.32.0.
- Do not call `add_losses()`. It was removed in 0.27.0; use
  `spectrum.losses`, `spectrum.compute_losses(...)`, or
  `NeutralLossesCosine` directly.
- `SpectrumProcessor` is not callable. Use `process_spectrum()` or
  `process_spectra()`. The single-spectrum call mutates by default; pass a clone
  when preserving the original.
- `process_spectra()` returns `(processed_spectra, processing_report)`.
- `Scores.scores` is a `StackedSparseArray`, often with separate structured
  fields such as `CosineGreedy_score` and `CosineGreedy_matches`.
- `scores_by_query()` returns `(reference_spectrum, score_record)` pairs, not
  reference indices.
- Prefer `spectra` in parameter names. The legacy spelling `spectrums` is
  deprecated.
- Never load pickle files from an untrusted source; unpickling can execute code.

See `references/migration.md` for a complete old-to-current mapping.

## Quick Start: Clean and Search a Library

```python
from math import isfinite

from matchms import SpectrumProcessor, calculate_scores
from matchms.filtering import (
    default_filters,
    normalize_intensities,
    require_minimum_number_of_peaks,
    require_precursor_mz,
    select_by_relative_intensity,
)
from matchms.importing import load_spectra
from matchms.similarity import ModifiedCosineGreedy


def load_and_process(path):
    spectra = [default_filters(spectrum) for spectrum in load_spectra(path)]
    processor = SpectrumProcessor(
        [
            (require_precursor_mz, {"minimum_accepted_mz": 10.0}),
            normalize_intensities,
            (select_by_relative_intensity, {"intensity_from": 0.01}),
            (require_minimum_number_of_peaks, {"n_required": 5}),
        ]
    )
    processed, _ = processor.process_spectra(
        spectra,
        progress_bar=False,
        create_report=False,
    )
    return [s for s in processed if isfinite(s.get("precursor_mz"))]


references = load_and_process("library.msp")
queries = load_and_process("queries.mgf")

metric = ModifiedCosineGreedy(tolerance=0.02)
scores = calculate_scores(
    references=references,
    queries=queries,
    similarity_function=metric,
)

score_name = "ModifiedCosineGreedy_score"
matches_name = "ModifiedCosineGreedy_matches"
for query in queries:
    ranked = scores.scores_by_query(query, name=score_name, sort=True)
    for reference, values in ranked[:5]:
        print(
            query.get("spectrum_id", query.get("id")),
            reference.get("compound_name", reference.get("spectrum_id")),
            float(values[score_name]),
            int(values[matches_name]),
        )
```

`SpectrumProcessor` automatically orders built-in filters according to matchms's
filter order. The aggregate `default_filters` callable is not in that registry,
so run it first as above or expand its nine component filters. Inspect
`processor.processing_steps` and preserve it with results.

## Pair Scoring

Similarity classes expose `pair()` for one reference/query pair. Cosine-family
results are structured NumPy scalars:

```python
from matchms.similarity import CosineGreedy

result = CosineGreedy(tolerance=0.02).pair(reference, query)
similarity = float(result["score"])
matched_peaks = int(result["matches"])
```

Use `calculate_scores()` for matrix-oriented methods such as
`FlashSimilarity` for larger comparisons; a 1-by-1 `calculate_scores()` call
still uses `pair()`. Flash also allocates a dense matrix internally even with
`array_type="sparse"`, so estimate memory before use.

## Choose a Similarity Method

- `CosineGreedy` — standard peak cosine with greedy peak assignm

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

