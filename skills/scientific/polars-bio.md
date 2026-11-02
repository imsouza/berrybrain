---
id: sci-polars-bio
name: "Scientific: polars-bio"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Performs genomic interval overlap, nearest, merge, coverage, complement and subtraction on Polars DataFrames, and reads or writes BED, VCF, BCF, BAM, CRAM, GFF, GTF, FASTA and FASTQ data. Use for coordinate-aware genomic joins, read-depth analysis, lazy bioinformatics I/O, SQL qu"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "polars bio"
  - "polars-bio"
keywords:
  - "polars"
  - "bio"
  - "performs"
  - "genomic"
  - "interval"
  - "overlap"
  - "nearest"
  - "merge"
---

# polars-bio

Use this skill for genomic interval arithmetic and bioinformatics file I/O through
Polars and DataFusion. It targets **polars-bio 0.36.0**, tested with **Polars 1.44.2**
on Python 3.13. The upstream package requires Polars >=1.37.1, PyArrow >=23.0.1,<25,
DataFusion >=53,<54 and polars-config-meta >=0.3.2,<1. Keep this environment separate
from packages needing incompatible Arrow or DataFusion releases.

```bash
uv pip install "polars-bio==0.36.0" "polars==1.44.2"
# Optional pandas interoperability (requires pandas >=3):
uv pip install "polars-bio[pandas]==0.36.0" "polars==1.44.2"
```

Verify new releases against the [official release notes](https://github.com/biodatageeks/polars-bio/releases)
and [package requirements](https://pypi.org/project/polars-bio/0.36.0/).
The examples below with named files are **templates**: substitute actual files and
check their schemas. The synthetic interval example and small local format
round trips were executed during this review.

## Workflow

1. Record the assembly, contig naming, coordinate convention, strand policy and
   unit of analysis. Identical contig names do not prove identical assemblies.
2. Choose readers by format; BCF has its own reader. Inspect schemas and source
   metadata before selecting attributes or genotypes.
3. Normalize all inputs to one coordinate system and validate their bounds.
4. Choose pair output, hit counts, covered bases or read depth deliberately.
5. Filter and project lazily, then inspect a small result before scaling up.
6. Validate output counts and boundaries against a hand-computable fixture;
   preserve IDs, coordinate metadata and provenance when saving results.

## Coordinate contract

The default is **1-based closed**, including converted BED reads. Use
`use_zero_based=True` on genomic readers for **0-based half-open** output.
This argument converts positions; it is not only a metadata label. For example,
BED `[0,10)` becomes `[1,10]` by default and remains `[0,10)` with the override.
SAM text POS is 1-based, whereas BAM stores its alignment position internally
as 0-based. Both readers expose the requested output convention.

For manually constructed DataFrames, metadata labels existing numbers and
**does not convert them**. Converting closed `[s,e]` to half-open means `s-1,e`.
Set metadata only after conversion. Never convert twice.

```python
import polars as pl
import polars_bio as pb

pb.set_option("datafusion.bio.coordinate_system_zero_based", True)
pb.set_option("datafusion.bio.coordinate_system_check", True)

query = pl.DataFrame({
    "query_id": ["q1", "q2", "q3"],
    "chrom": ["chr1", "chr1", "chr2"],
    "start": [0, 10, 0], "end": [10, 20, 10],
})
target = pl.DataFrame({
    "chrom": ["chr1", "chr1"], "start": [5, 8], "end": [12, 15],
})
for frame in (query, target):
    frame.config_meta.set(coordinate_system_zero_based=True)

pairs = pb.overlap(query, target).collect()
counts = pb.count_overlaps(query, target).collect().sort("query_id")
covered = pb.coverage(query, target).collect().sort("query_id")
assert pairs.height == 4
assert counts["count"].to_list() == [2, 2, 0]
assert covered["coverage"].to_list() == [5, 5, 0]
```

Require non-null contigs, integer positions and valid positive-length intervals
(`0 <= start < end` in half-open form), within the chosen assembly. Do not silently
turn points/insertions into nonempty intervals: choose the biological convention.
Mismatched input metadata raises `CoordinateSystemMismatchError`; missing metadata
warns and uses the global setting by default, or raises `MissingCoordinateSystemError`
in strict mode. Inspect `pb.get_metadata(frame)` after transformations and SQL.
See [configuration](references/configuration.md).

## Choose the operation

| Question | Operation | Interpretation |
|---|---|---|
| Which interval pairs intersect? | `overlap(a, b)` | Inner pair join; a query can appear repeatedly |
| Which query rows have any hit? | `overlap(a, b, overlap_output="left", distinct_output=True)` | One hit per original query row; duplicate input rows retain identity |
| How many target intervals intersect each query? | `count_overlaps(a, b)` | Target-record count, including zero for no hit |
| How many query bases are covered? | `coverage(a, b)` | Length of the union of target intersections; not read depth |
| Which targets are closest? | `nearest(a, b, k=1)` | Up to k neighbors, with nullable target/distance for no candidate |
| Combine overlapping regions | `merge(a)` | Coordinates plus `n_intervals`; other annotations are not aggregated |
| Label overlapping groups | `cluster(a)` | Adds `cluster`, `cluster_start`, `cluster_end` |
| Find uncovered regions | `complement(a, view_df=genome)` | Gaps within explicit assembly bounds |
| Remove target-covered pieces | `subtract(a, b)` | Remaining coordinate fragments; source annotations are not retained |

Important 0.36.0 behavior:

- `on_cols` is exposed in several signatures but **not implemented**; non-None
  values raise `AssertionError`. For strand/sample-specific analysis, split both
  inputs by that key, run matching groups separately and restore the group key.
- `merge(..., min_dist=0)` and `cluster(..., min_dist=0)` keep bookended half-open
  intervals separate. `min_dist=1` joins bookends for integer coordinates. Test
  boundary fixtures when porting bioframe code; its threshold conventions differ.
- `nearest` supports `k`, `overlap=False` and `distance=False`. Distance zero can
  mean overlap **or adjacency**; it does not prove an intersecting base. Do not
  infer a unique biological annotation from an arbitrary equidistant candidate.
- Default COITrees overlap indexing casts coordinates to signed Int32; an Int64
  DataFrame does not remove the 2,147,483,647 bound. Validate maximum coordinates
  before execution, especially concatenated genomes or custom coordinate spaces.
- `complement` without a view uses an effectively unbounded contig extent. Always
  supply finite genome bounds and ensure their convention matches the intervals.

Functional interval calls return `pl.LazyFrame` by default; `.collect()` or
`output_type="polars.DataFrame"` gives an eager result. The `.pb` interval accessor
is on `LazyFrame`: `query.lazy().pb.overlap(target).collect()`. DataFrame `.pb`
provides write methods. See [interval operations](references/interval_operations.md).

## Read, query and write files

Use `scan_*` for lazy plans and `read_*` for eager reads. They do not guarantee
that every sta

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

