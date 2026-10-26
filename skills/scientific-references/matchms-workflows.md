---
id: sciref-matchms-workflows
name: "Scientific Ref: Practical Workflows (matchms 0.33.1)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matchms): Practical Workflows (matchms 0.33.1)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matchms workflows"
  - "practical workflows (matchms 0.33.1)"
keywords:
  - "matchms"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
  - "practical"
---

# Practical Workflows (matchms 0.33.1)

These patterns use the current 0.33.1 API. Adapt tolerances and quality filters
to the instrument, acquisition method, and scientific question.

## 1. Standard Query/Reference Preprocessing

Apply the same peak processing to both collections. Metadata enrichment can
differ when a reference library contains known structures and queries do not.

```python
from matchms import SpectrumProcessor
from matchms.filtering import (
    default_filters,
    normalize_intensities,
    require_minimum_number_of_peaks,
    require_precursor_mz,
    select_by_mz,
    select_by_relative_intensity,
)
from matchms.importing import load_spectra


def preprocess(path):
    raw = [default_filters(spectrum) for spectrum in load_spectra(path)]
    processor = SpectrumProcessor(
        [
            (require_precursor_mz, {"minimum_accepted_mz": 50.0}),
            normalize_intensities,
            (select_by_mz, {"mz_from": 20.0, "mz_to": 1500.0}),
            (select_by_relative_intensity, {"intensity_from": 0.01}),
            (require_minimum_number_of_peaks, {"n_required": 5}),
        ]
    )
    cleaned, _ = processor.process_spectra(
        raw,
        progress_bar=False,
        create_report=False,
    )
    return cleaned, ["default_filters", *processor.processing_steps]


queries, query_steps = preprocess("queries.mgf")
references, reference_steps = preprocess("library.msp")
assert query_steps == reference_steps
```

`SpectrumProcessor` may reorder built-in filters. Persist the final
`processing_steps`, not only the requested list. Run the aggregate
`default_filters` before the processor; if passed as one callable, it is treated
as a custom filter and placed after registered filters.

## 2. Run the Bundled Library Search

The bundled CLI is the fastest route to a reproducible CSV:

```bash
uv run python scripts/library_search.py \
  queries.mgf library.msp hits.csv \
  --metric modified \
  --tolerance 0.02 \
  --top-k 10 \
  --min-score 0.6 \
  --min-matches 5
```

The script:

- applies the same configurable peak filters to both inputs;
- supports cosine, exact/greedy modified cosine, neutral-loss, BLINK, and Flash
  modes;
- handles both scalar and structured matchms score records;
- rejects non-finite numeric settings and invalid/nonpositive precursors when
  the selected operation needs them;
- applies the requested relative-intensity cutoff inside Flash as well;
- records identifiers, precursor m/z, rank, score, and matched peaks;
- refuses pickle inputs;
- refuses to overwrite output unless `--force`; and
- stops before an unexpectedly large pairwise matrix unless `--max-pairs` is
  explicitly raised.

Use `--help` before batch use.

## 3. Programmatic Spectral-Library Search

```python
from matchms import calculate_scores
from matchms.similarity import ModifiedCosineGreedy

metric = ModifiedCosineGreedy(tolerance=0.02)
scores = calculate_scores(
    references=references,
    queries=queries,
    similarity_function=metric,
)

score_name = "ModifiedCosineGreedy_score"
matches_name = "ModifiedCosineGreedy_matches"
rows = []

for query_index, query in enumerate(queries):
    ranked = scores.scores_by_query(query, name=score_name, sort=True)
    for rank, (reference, value) in enumerate(ranked[:10], start=1):
        rows.append(
            {
                "query_index": query_index,
                "query_id": query.get("spectrum_id", query.get("id")),
                "reference_id": reference.get(
                    "spectrum_id",
                    reference.get("compound_name"),
                ),
                "rank": rank,
                "score": float(value[score_name]),
                "matches": int(value[matches_name]),
            }
        )
```

Filter on both score and matched peaks only after examining their distributions.
Do not label arbitrary cutoffs as universal high/medium/low confidence.

## 4. Efficient Precursor-Gated Search

For identity-oriented search, a precursor gate can reduce expensive spectral
calculations:

```python
from matchms import calculate_scores
from matchms.similarity import ModifiedCosineGreedy, PrecursorMzMatch

scores = calculate_scores(
    references,
    queries,
    PrecursorMzMatch(tolerance=10, tolerance_type="ppm"),
    array_type="sparse",
)
scores.filter_by_range(
    name="PrecursorMzMatch",
    low=0.5,
    above_operator=">=",
)
if len(scores.scores.row) == 0:
    raise ValueError("No candidates passed the precursor gate")
scores.calculate(
    ModifiedCosineGreedy(tolerance=0.02),
    array_type="sparse",
    join_type="left",
)
```

This restricts computation to retained coordinates only when fewer than half
of all pairs remain and the join is left/inner. Otherwise matchms 0.33.1
computes the full matrix before joining; a 1-by-1 input always uses `pair()`.
Stop when no candidates remain. This gate is inappropriate for broad analog
discovery across precursor shifts or adducts.

## 5. Reproducible `Pipeline` Workflow

`Pipeline` combines import, ordered filtering, sparse score gating, and score
calculation. A workflow can also be written to YAML.

```python
from matchms import Pipeline
from matchms.Pipeline import create_workflow

common_filters = [
    "make_charge_int",
    "add_compound_name",
    "derive_adduct_from_name",
    "derive_formula_from_name",
    "clean_compound_name",
    "interpret_pepmass",
    "add_precursor_mz",
    "derive_ionmode",
    "correct_charge",
    ["require_precursor_mz", {"minimum_accepted_mz": 50.0}],
    "normalize_intensities",
    ["select_by_relative_intensity", {"intensity_from": 0.01}],
    ["require_minimum_number_of_peaks", {"n_required": 5}],
]

workflow = create_workflow(
    yaml_file_name=None,
    query_filters=common_filters,
    reference_filters=common_filters,
    score_computations=[
        ["precursormzmatch", {"tolerance": 10, "tolerance_type": "ppm"}],
        ["filter_by_range", {"name": "PrecursorMzMatch", "low": 0.5}],
        ["modifiedcosinegreedy", {"tolerance": 0.02}],
        [
            "filter_by_range",
            {"name": "ModifiedCosineGreedy_score", "low": 0.6},
        ],
    ],
)

pipeline = Pipeline(
    workflow,
    progress_bar=False,
    logging_level="WARNING",
    logging_file="matchms-pipeline.log",
)
pipeline.run(
    query_files="queries.mgf",
    reference_files="library.msp",
    cleaned_query_file="queries-cleaned.mgf",
    cleaned_reference_file="library-cleaned.msp",
    create_report=Fals

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

