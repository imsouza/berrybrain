---
id: sciref-pysam-common-workflows
name: "Scientific Ref: Correct Pysam Workflow Patterns"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pysam): Correct Pysam Workflow Patterns"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pysam common workflows"
  - "correct pysam workflow patterns"
keywords:
  - "pysam"
  - "common"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
  - "correct"
---

# Correct Pysam Workflow Patterns

These patterns target pysam 0.24.1 and make filtering and coordinate semantics
explicit. Adapt thresholds to the assay rather than treating them as universal
defaults.

## Preflight an Analysis

Before combining files, verify:

1. Reference assembly and contig naming agree (`chr1` versus `1`).
2. Numeric coordinates use 0-based, half-open intervals.
3. Alignment and variant inputs are sorted as expected.
4. Random-access inputs have valid indexes.
5. CRAM has the exact reference FASTA available.
6. Read-group/sample metadata identifies the intended samples.
7. Duplicate, secondary, supplementary, QC-fail, and quality policies are
   stated.

Use the bundled inspectors:

```bash
python scripts/inspect_hts.py sample.bam
python scripts/inspect_hts.py cohort.vcf.gz
python scripts/inspect_hts.py reference.fa
```

## Streaming Alignment QC

The bundled script scans in file order and does not require an index:

```bash
python scripts/alignment_qc.py sample.bam --output sample.qc.json
python scripts/alignment_qc.py sample.cram \
  --reference reference.fa \
  --max-records 100000
```

The report counts alignment records, not unique templates or fragments.
Secondary and supplementary records are reported separately. Use
`--max-records` for a sampling pass; omit it for a complete scan.

For index-level counts without reading every record:

```python
import pysam

with pysam.AlignmentFile("sample.bam", "rb", require_index=True) as bam:
    for stats in bam.get_index_statistics():
        print(stats.contig, stats.mapped, stats.unmapped, stats.total)
```

Index statistics are fast but cannot replace custom record-level QC. CRAI has
no record counts: the CRAM index-statistic zeros are unavailable data.
The QC script counts mapped non-soft-clipped query bases, including insertions,
only when CIGAR and SEQ exist. Missing SEQ does not contribute to mean length.

## Zero-Aware Coverage

`pileup()` omits positions with no columns. Use `count_coverage()` when zeros
must be represented:

```python
import pysam


def base_depth(
    bam: pysam.AlignmentFile,
    contig: str,
    start: int,
    stop: int,
    *,
    min_base_quality: int = 20,
) -> list[int]:
    if not 0 <= start < stop <= bam.get_reference_length(contig):
        raise ValueError("coverage interval must be nonempty and within the contig")
    a, c, g, t = bam.count_coverage(
        contig,
        start,
        stop,
        quality_threshold=min_base_quality,
        read_callback="all",
    )
    return [sum(counts) for counts in zip(a, c, g, t)]


with pysam.AlignmentFile("sample.bam", "rb") as bam:
    depth = base_depth(bam, "chr1", 1_000, 2_000)
```

`read_callback="all"` excludes unmapped, secondary, QC-fail, and duplicate
records, but not supplementary records. Use a custom callback when
supplementary or low-MAPQ reads must also be excluded:

```python
def usable_read(read: pysam.AlignedSegment) -> bool:
    return (
        not read.is_unmapped
        and not read.is_secondary
        and not read.is_supplementary
        and not read.is_qcfail
        and not read.is_duplicate
        and read.mapping_quality >= 20
    )


a, c, g, t = bam.count_coverage(
    "chr1",
    1_000,
    2_000,
    quality_threshold=20,
    read_callback=usable_read,
)
```

Only A/C/G/T query bases contribute. Overlapping mates count separately.
`count_coverage` does not use pileup BAQ/overlap correction; pass numeric span
arguments because 0.24.1 does not size arrays from `region=`/`end=` aliases.

### Convert low-depth bases into intervals

```python
def below_threshold_intervals(
    depths: list[int],
    start: int,
    threshold: int,
):
    interval_start = None

    for offset, value in enumerate(depths):
        position = start + offset
        if value < threshold and interval_start is None:
            interval_start = position
        elif value >= threshold and interval_start is not None:
            yield interval_start, position
            interval_start = None

    if interval_start is not None:
        yield interval_start, start + len(depths)
```

The yielded intervals remain 0-based, half-open and correctly include regions
with no aligned columns.

## Exact Pileup at a Position

Use explicit pileup options and retain the iterator:

```python
def aligned_depth_at(
    bam: pysam.AlignmentFile,
    fasta: pysam.FastaFile,
    contig: str,
    position: int,
) -> int:
    iterator = bam.pileup(
        contig,
        position,
        position + 1,
        truncate=True,
        stepper="samtools",
        fastafile=fasta,
        min_mapping_quality=20,
        min_base_quality=20,
        max_depth=100_000,
        ignore_overlaps=True,
        ignore_orphans=True,
    )
    for column in iterator:
        if column.reference_pos == position:
            return sum(
                not item.is_del and not item.is_refskip
                and item.query_position is not None
                for item in column.pileups
            )
    return 0
```

`get_num_aligned()` includes D/N entries in 0.24.1, so this helper deliberately
counts observed bases. BAQ is enabled when the reference is supplied. MAPQ255
is retained by the numeric threshold; apply an explicit unavailable-MAPQ
policy if required. This definition is not identical to VCF `INFO/DP` from a caller. Name custom
annotations so their provenance and filters remain clear.

## SNP Base Support

This helper is deliberately limited to single-nucleotide REF/ALT alleles:

```python
from collections import Counter


def snp_base_counts(
    bam: pysam.AlignmentFile,
    fasta: pysam.FastaFile,
    record: pysam.VariantRecord,
) -> Counter[str]:
    if (
        record.ref.upper() not in {"A", "C", "G", "T"}
        or not record.alts
        or any(alt.upper() not in {"A", "C", "G", "T"} for alt in record.alts)
        or any(alt.upper() == record.ref.upper() for alt in record.alts)
    ):
        raise ValueError("snp_base_counts only supports simple SNP records")

    # Validate REF without inferring a variant from a mismatched assembly.
    observed_ref = fasta.fetch(record.contig, record.start, record.start + 1)
    if observed_ref.upper() != record.ref.upper():
        raise ValueError("VCF REF does not match the selected FASTA")
    counts: Counter[str] = Counter()
    iterator = bam.pileup(
        record.contig,
        record.start,
        record.start + 1,
        truncate=True,
        stepper="samtools",
        fastafile=fas

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

