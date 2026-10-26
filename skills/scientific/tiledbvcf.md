---
id: sci-tiledbvcf
name: "Scientific: tiledbvcf"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Stores and retrieves genomic variant calls with TileDB-VCF. Use for indexed single-sample VCF/BCF ingestion, incremental cohorts, region and sample queries, streaming results, allele statistics, QC, and VCF/BCF export locally or through TileDB Cloud."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "tiledbvcf"
keywords:
  - "tiledbvcf"
  - "stores"
  - "retrieves"
  - "genomic"
  - "variant"
  - "calls"
  - "tiledb"
---

# TileDB-VCF

## When to use

Use for cohort variant storage, incremental sample ingestion, interval queries, and
exporting subsets for downstream genomics. TileDB-VCF stores records; it does not
perform joint variant calling, association testing, normalization, or population
structure adjustment. Dataset size alone does not determine whether cloud execution
is appropriate: benchmark the intended sample, region, and attribute workload.

This skill targets released **TileDB-VCF 0.40.3**. Native Python/CLI checks used two
synthetic single-sample VCFs on macOS ARM64. Cloud client **0.14.4** contracts were
checked against its released wheel and mocked dispatch; hosted queries and jobs
were not executed. See [installation and verification notes](references/verification.md).

## Install and verify the native stack

The `tiledbvcf` Python distribution is not published on PyPI at this review. The
official **`tiledb` Conda channel** supplies `tiledbvcf-py` 0.40.3 for macOS ARM64,
macOS x86-64, and Linux x86-64, with Python 3.9-3.12 builds. `tiledb` on PyPI is
TileDB-Py and does not install TileDB-VCF. Native Apple Silicon no longer requires
forcing `CONDA_SUBDIR=osx-64`.

For the tested macOS ARM64 environment, pins below avoid versioned-library import
failures in the otherwise successful current Conda solve:

```bash
conda create -n tiledb-vcf -c tiledb -c conda-forge \
  python=3.12 tiledbvcf-py=0.40.3 \
  azure-core-cpp=1.16.2 azure-storage-blobs-cpp=12.16.0 \
  azure-storage-files-datalake-cpp=12.14.0 capnproto=1.4.0 c-blosc2=2.23.1
conda activate tiledb-vcf
python -c 'import tiledbvcf; print(tiledbvcf.version)'
tiledbvcf version
```

The equivalent Micromamba solve/install was executed. These extra ABI pins are a
verified macOS ARM64 workaround, not a claim about all platforms. Preserve the
resolved environment for production. Other-platform installation and official
Docker images are alternatives documented upstream, not tested here.

## Prepare and create a cohort

1. Record reference assembly, contig naming/lengths, callers, normalization rules,
   sample identity, and file checksums. Do not mix assemblies or assume `1` and
   `chr1` are equivalent. Confirm compatible headers across inputs.
2. Each input must contain **one sample**, be coordinate sorted, and have an index.
   Use BGZF-compressed VCF or BCF with a matching `.csi`/`.tbi`. Inspect
   `bcftools query -l sample1.vcf.gz`; filenames are not sample identifiers.
3. Create the dataset explicitly, then ingest. Opening `mode="w"` alone does not
   create its schema. Materialize frequently read fields at creation time.
4. Validate a small known interval and a round-trip export before scaling.

For existing sorted plain-text VCFs (run once per input; output names must be new):

```bash
bcftools view -Oz -o sample1.vcf.gz sample1.vcf
bcftools index -c sample1.vcf.gz
bcftools view -Oz -o sample2.vcf.gz sample2.vcf
bcftools index -c sample2.vcf.gz
```

The following local examples were exercised with sample IDs `S1` and `S2`, contig
`chr1`, and coordinates 1-100; substitute the verified IDs and intervals in real data.

```python
import tiledbvcf

uri = "cohort"
config = {"sm.compute_concurrency_level": "2", "sm.io_concurrency_level": "2"}
with tiledbvcf.Dataset(uri, mode="w", tiledb_config=config) as ds:
    ds.create_dataset(extra_attrs=["fmt_GT", "fmt_DP"])
    ds.ingest_samples(
        ["sample1.vcf.gz"], threads=2, total_memory_budget_mb=512
    )

# Incremental ingestion uses the existing dataset; do not call create_dataset again.
with tiledbvcf.Dataset(uri, mode="w", tiledb_config=config) as ds:
    ds.ingest_samples(
        ["sample2.vcf.gz"], threads=2, total_memory_budget_mb=512
    )
```

The schema-v4 data array has `contig`, start-coordinate, and sample **dimensions**;
headers and optional statistics are separate arrays in the dataset group. Fields
not explicitly materialized remain in the INFO/FORMAT payloads. Query names such
as `pos_start` need not match raw storage column names.

Upstream supports parallel thread/process ingestion. Assign distinct sample work
and coordinate lifecycle/maintenance operations; do not blindly re-ingest samples.
`resume=True` supports interrupted ingestion, not arbitrary duplicate correction.

## Query completely and interpret coordinates correctly

| Surface | Coordinate convention |
| --- | --- |
| Python `regions=["chr1:10-14"]` | 1-based, closed interval |
| Returned `pos_start`, `pos_end` | 1-based, inclusive record endpoints |
| BED input and `query_bed_start`, `query_bed_end` | 0-based, half-open |
| `read_variant_stats()` / `read_allele_count()` column `pos` in 0.40.3 | **0-based**; add one before joining to VCF POS |

Queries return **overlapping records**, not just records starting inside the
interval. A deletion spanning positions 10-14 appears in `chr1:14-14`, with
`pos_start=10`. For BED `[13,14)`, the equivalent string is `chr1:14-14`.
The Python region parser requires explicit `contig:start-end`; bare `"chr1"`
is rejected in this release. Use a known contig length for a whole-contig query.

```python
cfg = tiledbvcf.ReadConfig(memory_budget_mb=128, tiledb_config=config)
attrs = ["sample_name", "contig", "pos_start", "pos_end", "alleles", "fmt_GT"]
with tiledbvcf.Dataset(uri, cfg=cfg) as ds:
    assert {"S1", "S2"}.issubset(ds.samples())
    assert set(attrs).issubset(ds.attributes())
    for batch in ds.read_iter(
        attrs=attrs, regions=["chr1:1-100"], samples=["S1", "S2"]
    ):
        print(batch)  # Replace with a bounded consumer or partitioned output.
```

- `read()` returns a pandas DataFrame; `read_arrow()` returns a PyArrow Table.
  Either can return only the first memory-limited batch. Continue with
  `continue_read()` / `continue_read_arrow()` until `read_completed()`, or use
  `read_iter()` for ordinary DataFrame queries. Avoid concatenating all batches
  when the result cannot fit in memory.
- `ReadConfig(memory_budget_mb=...)` controls reads; use
  `ingest_samples(total_memory_budget_mb=...)` for writes. A read budget is not
  a process RSS cap. `limit` truncates total output; it is not a pagination size.
- `sample_partition=(0, 2)` selects partition zero of two. Likewise,
  `region_partition=(index, number_of_partitions)` partitions query regions;
  these tuples are not coordinate bounds, tile extents, or sample capacities.
- **0.40.3 retains BED selection state** when a later call omits `bed_file`.
  Open a fresh `Dataset` for an independent quer

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

