---
id: sciref-polars-bio-configuration
name: "Scientific Ref: Configuration and metadata (0.36.0)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (polars-bio): Configuration and metadata (0.36.0)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "polars bio configuration"
  - "configuration and metadata (0.36.0)"
keywords:
  - "polars"
  - "bio"
  - "configuration"
  - "specialized"
  - "scientific"
  - "reference"
  - "metadata"
---

# Configuration and metadata (0.36.0)

The [release context implementation](https://github.com/biodatageeks/polars-bio/blob/0.36.0/polars_bio/context.py)
is the authority for defaults; some function docstrings incorrectly call
coordinate checking strict by default.

| Option | Actual default | Effect |
|---|---|---|
| `datafusion.execution.target_partitions` | `"1"` | DataFusion execution partition target |
| `datafusion.bio.coordinate_system_zero_based` | `"false"` | Readers default to 1-based closed output |
| `datafusion.bio.coordinate_system_check` | `"false"` | Missing metadata warns and falls back to session convention |
| `bio.interval_join_algorithm` | `"coitrees"` | Default interval join backend |

```python
import polars_bio as pb

pb.set_option("datafusion.bio.coordinate_system_zero_based", True)
pb.set_option("datafusion.bio.coordinate_system_check", True)
pb.set_option("datafusion.execution.target_partitions", 4)
assert pb.get_option("datafusion.execution.target_partitions") == "4"
```

`set_option` accepts boolean/numeric values and converts them to backend strings;
`get_option` returns a string (or None). Options affect a shared process context:
set them deliberately before constructing scans/registered tables, record them,
and restore previous values when a reusable workflow finishes. Four partitions
is an example, not a performance recommendation for every dataset. Each
partition and object-store fetch can increase memory consumption.

## Metadata versus coordinate conversion

I/O functions that expose `use_zero_based` convert their output coordinates and
set metadata. Explicit reader arguments override the global default. Native
BED is 0-based half-open; VCF/GFF/GTF and SAM text are 1-based. BAM's internal
stored position is 0-based. Read all files into one chosen convention.

```python
import polars as pl
import polars_bio as pb

closed = pl.DataFrame({"chrom": ["chr1"], "start": [1], "end": [10]})
closed.config_meta.set(coordinate_system_zero_based=False)
half_open = closed.with_columns((pl.col("start") - 1).alias("start"))
half_open.config_meta.set(coordinate_system_zero_based=True)
assert half_open.select("start", "end").row(0) == (0, 10)
```

`config_meta.set()` labels the existing values, never shifts them. Subtracting
one from an unsigned zero risks underflow: validate the source convention before
conversion, and use signed arithmetic when deriving lengths/differences.
Changing a global option does not convert or relabel existing frames.

Two-input interval operations reject disagreeing coordinate metadata. Strict
checking rejects absent metadata; lenient checking may hide an accidental
coordinate mismatch. Strict checking still does not validate genome assembly,
strand meaning, reference contig lengths or every biological interval rule.

## Inspect and retain metadata

```python
# Template: df is a frame returned by a genomic reader.
metadata = pb.get_metadata(df)
pb.print_metadata_summary(df)
pb.print_metadata_json(df)
assert metadata["coordinate_system_zero_based"] is True
```

`pb.set_source_metadata(df, format="bed", path="regions.bed")` records provenance;
it is not a coordinate converter or a substitute for explicit coordinate
metadata. Readers also retain headers needed for writing VCF/BAM/CRAM. Confirm
metadata after select/rename/concat, SQL, conversion to pandas, or saving and
reloading an intermediate format. Do not assume arbitrary SQL expressions or
Parquet round trips preserve this Python metadata.

## Streaming and logging

`scan_*` builds lazy readers, and supported sources deliver batches from
DataFusion to Polars. `lf.collect(engine="streaming")` selects Polars' streaming
engine for the plan but still returns a materialized DataFrame. Joins may build
an in-memory index; sorting, merge/cluster and dense pileup can need substantial
working memory. Use sinks when output size itself is large. Indexes and reader
pushdown support vary by format; do not equate lazy input with indexed access.

Call `pb.set_loglevel("info")` immediately after import if needed. Accepted levels
are `debug`, `info`, `warn` and `warning`. The upstream logging implementation
restricts later verbosity changes; start a new Python process if changing the
level does not take effect. For ordinary analysis leave logging at its default.
See [official auxiliary API](https://biodatageeks.org/polars-bio/api/auxiliary/).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

