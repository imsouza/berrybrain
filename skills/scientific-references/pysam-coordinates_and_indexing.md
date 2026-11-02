---
id: sciref-pysam-coordinates-and-indexing
name: "Scientific Ref: Coordinates and Indexing"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pysam): Coordinates and Indexing"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pysam coordinates indexing"
  - "coordinates and indexing"
keywords:
  - "pysam"
  - "coordinates"
  - "indexing"
  - "specialized"
  - "scientific"
  - "reference"
---

# Coordinates and Indexing

Coordinate mistakes and stale indexes are the most common causes of plausible
but wrong genomic results. This reference targets pysam 0.24.1.

## The Pysam Rule

For region API numeric arguments and span properties such as `reference_start`
and `VariantRecord.start/stop`, pysam uses **0-based, half-open** intervals:

```text
[start, stop)
```

The first base is `0`; `start` is included and `stop` is excluded. Interval
length is `stop - start`.

`VariantRecord.pos` preserves the VCF 1-based POS field. A textual
samtools-style region string is also
**1-based, inclusive**:

```text
chr1:100-199
```

These refer to the same 100 bases:

```python
file.fetch("chr1", 99, 199)
file.fetch(region="chr1:100-199")
```

This rule applies to:

- `AlignmentFile.fetch()`, `count()`, `count_coverage()`, and `pileup()`
- `VariantFile.fetch()`
- `FastaFile.fetch()`
- `TabixFile.fetch()`

Do not treat numeric `VariantFile.fetch()` arguments as VCF text coordinates.

## Format Conversion Table

| Source representation | Source convention | Convert to pysam numeric |
|---|---|---|
| BED `chromStart`, `chromEnd` | 0-based, half-open | use unchanged |
| VCF `POS` and REF | 1-based position | `start = POS - 1`; `stop = start + len(REF)` unless record semantics provide another end |
| `VariantRecord.start`, `.stop` | 0-based, half-open | use unchanged |
| GFF/GTF start/end columns | 1-based, inclusive | `start = start_text - 1`; `stop = end_text` |
| SAM `POS` | 1-based leftmost base | use `AlignedSegment.reference_start` |
| samtools region string | 1-based, inclusive | pass as `region=...`, or convert both endpoints |

For VCF structural variants, symbolic alleles, breakends, and records with
`INFO/END`, use `VariantRecord.start` and `VariantRecord.stop` rather than
reconstructing the interval from `len(REF)`. This is the indexed local record
span, not a complete biological event: BND mate loci, confidence intervals,
per-allele SVLEN, and sample-specific lengths require their own interpretation.
VCF 4.5 deprecates INFO/END in favor of computed end semantics.

SAM text POS and CRAM absolute alignment starts are 1-based; BAM/BCF binary
positions are 0-based. Pysam translates the stored encodings; never apply a
second conversion to its numeric span properties.

## Single Positions

A 1-based position `p` becomes the one-base Python interval:

```python
start = p - 1
stop = p
```

For a VCF record:

```python
assert record.start == record.pos - 1
base = fasta.fetch(record.contig, record.start, record.start + 1)
```

## Overlap Versus Containment

Region fetches are overlap queries. An alignment or variant can begin before
the requested interval and still overlap it.

To require complete containment:

```python
def fully_contained(read, start: int, stop: int) -> bool:
    return (
        read.reference_start is not None
        and read.reference_end is not None
        and read.reference_start >= start
        and read.reference_end <= stop
    )
```

For point-based logic, define exactly what "overlap" means for deletions,
reference skips, symbolic alleles, and breakends.

`pileup()` has an additional trap: without `truncate=True`, it can emit columns
outside the requested interval because reads overlap the interval.

## Parser Coordinates

Pysam parser objects normalize coordinates:

- `asBed().start` / `.end`: 0-based, half-open
- `asGTF().start` / `.end`: exposed in Python coordinate convention
- `asVCF().pos`: **0-based**, unlike 1-based `VariantRecord.pos`; use
  `VariantFile` for full VCF record semantics
- `asGFF3().start` / `.end`: 0-based, half-open

When creating a custom tabix index:

- `seq_col`, `start_col`, and `end_col` are 0-based **column indices**
- file coordinates default to 1-based unless `zerobased=True`
- later `TabixFile.fetch()` numeric query coordinates are still 0-based

These are three distinct concepts: Python column index, coordinate encoding in
the stored table, and coordinate encoding in the query.

## Contig Identity

Coordinate conversion does not solve contig mismatches. Check:

- `chr1` versus `1`
- mitochondrial names (`chrM`, `MT`, `M`)
- alternate loci and decoys
- assembly version (for example GRCh37 versus GRCh38)
- contig order and lengths

```python
alignment_contigs = dict(zip(bam.references, bam.lengths))
fasta_contigs = dict(zip(fasta.references, fasta.lengths))

shared = alignment_contigs.keys() & fasta_contigs.keys()
length_mismatches = {
    name: (alignment_contigs[name], fasta_contigs[name])
    for name in shared
    if alignment_contigs[name] != fasta_contigs[name]
}
```

Do not silently strip or add `chr` across arbitrary assemblies. Use an explicit
reviewed mapping.

## Index Matrix

| Data | Random-access index | Sort requirement |
|---|---|---|
| BAM | `.bai` or `.csi` | coordinate order |
| CRAM | `.crai` | coordinate order |
| BGZF VCF | `.tbi` or `.csi` | contig/position order |
| BCF | `.csi` | contig/position order |
| FASTA | `.fai`; BGZF FASTA also `.gzi` | FASTA layout, not coordinate sort |
| BED/GFF/GTF/custom BGZF table | `.tbi` or `.csi` | contig/start order |
| SAM / ordinary VCF / FASTQ | no random-access index through these APIs | sequential only |

An index is a view of a specific file. If the data file changes, rebuild the
index. A stale index may fail loudly or return wrong/incomplete regions.

## BAI/TBI Versus CSI

Legacy BAI and standard TBI indexes have a maximum coordinate near `2^29`
(512 Mi bases). This is insufficient for some plant, animal, and synthetic
references. CSI is parameterized and supports larger coordinates.

Create a BAM CSI:

```python
import pysam

pysam.index("-c", "large-reference.bam", catch_stdout=False)
```

Create a tabix CSI:

```python
pysam.tabix_index(
    "large-reference.bed.gz",
    preset="bed",
    csi=True,
    min_shift=14,
)
```

Create a VCF/BCF CSI:

```python
import pysam.bcftools

pysam.bcftools.index(
    "--csi",
    "variants.vcf.gz",
    catch_stdout=False,
)
```

Prefer CSI when reference sizes are unknown or potentially large. Confirm
downstream tools support it.

## Sort Before Indexing

Indexing does not sort records.

BAM:

```python
import pysam.samtools

pysam.samtools.sort(
    "-@", "4",
    "-o", "sorted.bam",
    "input.bam",
    catch_stdout=False,
)
pysam.samtools.index(
    "-@", "4",
    "sorted.bam",
    catch_stdout=False,
)
```

VCF:

```python
import pysam.bcftools

pysam.bcftools.sort(
    "-Oz",
    "-o", "sorted.vcf.gz",
    "input.

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

