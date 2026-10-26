---
id: sciref-pysam-alignment-files
name: "Scientific Ref: Alignment Files: SAM, BAM, and CRAM"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pysam): Alignment Files: SAM, BAM, and CRAM"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pysam alignment files"
  - "alignment files: sam, bam, and cram"
keywords:
  - "pysam"
  - "alignment"
  - "files"
  - "specialized"
  - "scientific"
  - "reference"
---

# Alignment Files: SAM, BAM, and CRAM

This reference targets pysam 0.24.1. All numeric coordinates shown here are
0-based, half-open.

## Open Modes and Handles

| Format | Read | Write |
|---|---:|---:|
| SAM text | `r` | `w` |
| BAM | `rb` | `wb` |
| CRAM | `rc` | `wc` |

```python
import pysam

with pysam.AlignmentFile("input.bam", "rb", threads=4) as alignments:
    print(alignments.references)
```

For CRAM, supply the exact reference where possible:

```python
with pysam.AlignmentFile(
    "input.cram",
    "rc",
    reference_filename="GRCh38.fa",
    threads=4,
) as alignments:
    ...
```

`AlignmentFile` can use a path or a real file object that exposes `fileno()`.
In-memory objects such as `io.BytesIO` are not supported by HTSlib. Use `"-"`
for stdin/stdout. When an existing file object is accepted,
`duplicate_filehandle=True` (the default) prevents pysam from closing the
caller's descriptor.

Useful constructor options:

- `index_filename=`: nonstandard, remote, or separately named index
- `require_index=True`: fail early if random access is required
- `reference_filename=`: CRAM reference FASTA
- `threads=`: compression/decompression threads
- `format_options=["key=value"]`: HTSlib format options
- `ignore_truncation=True`: downgrade a missing BGZF EOF marker to a warning;
  do not combine with `threads > 1`

## Headers and Index State

`AlignmentFile.header` is an `AlignmentHeader`, not a plain dictionary.

```python
with pysam.AlignmentFile("input.bam", "rb") as bam:
    header_dict = bam.header.to_dict()
    header_text = str(bam.header)
    contigs = dict(zip(bam.references, bam.lengths))
    has_index = bam.has_index()
```

Use `check_index()` when a missing index should be an error. It raises for SAM,
closed files, or unusable indexes. `get_index_statistics()` exposes per-contig
mapped/unmapped counts recorded in an available index; these are index
statistics, not a fresh scan of every record. CRAI does not store these counts:
CRAM `mapped`, `unmapped`, `nocoordinate`, and index-statistic values return zero
and must not be interpreted as an empty CRAM. Use a sequential scan for counts.

## Iteration Choices

### Indexed region query

```python
with pysam.AlignmentFile("input.bam", "rb") as bam:
    for read in bam.fetch("chr1", 1_000, 2_000):
        ...
```

- Requires BAI/CSI for BAM or CRAI for CRAM.
- Returns reads overlapping the interval, including reads that start before it
  or end after it.
- Records are returned in coordinate/index order.
- BAM/CRAM `fetch()` with no region requires an index and visits placed records
  by reference. Placed unmapped records can appear in both this and region
  queries; test `read.is_unmapped`. Unplaced reads need sequential scanning.
- SAM `fetch()` without a region is sequential; SAM region access is unsupported
  by `AlignmentFile` even though standalone samtools can index BGZF SAM.

### Sequential scan

```python
with pysam.AlignmentFile("input.bam", "rb") as bam:
    for read in bam.fetch(until_eof=True):
        ...
```

- Does not require an index.
- Starts at the current file position.
- Preserves file order.
- Includes unplaced unmapped records.

`fetch("*")` requests only unplaced unmapped records at the end of a
coordinate-sorted alignment file.

### Multiple active iterators

`multiple_iterators` belongs to `fetch()`, not the `AlignmentFile`
constructor:

```python
with pysam.AlignmentFile("input.bam", "rb") as bam:
    chr1_reads = bam.fetch("chr1", multiple_iterators=True)
    chr2_reads = bam.fetch("chr2", multiple_iterators=True)
```

Each such iterator reopens the file and has overhead. Prefer one ordered pass
when possible.

## `AlignedSegment` Essentials

### Identity and sequence

- `query_name`
- `query_sequence`
- `query_qualities`: numeric Phred scores, or `None`
- `query_length`
- `query_alignment_sequence`: query bases participating in the alignment
- `query_alignment_qualities`
- `get_forward_sequence()` / `get_forward_qualities()`: original sequencer
  orientation of the retained sequence (hard-clipped bases cannot be recovered)

Assigning `query_sequence` invalidates `query_qualities`. Save and reassign
qualities after changing sequence.

### Reference placement

- `reference_name`
- `reference_id`
- `reference_start`: 0-based inclusive
- `reference_end`: 0-based exclusive; derived from CIGAR
- `mapping_quality`
- `next_reference_name`, `next_reference_start`
- `template_length`

Many placement-derived properties are `None` or sentinel values for unmapped
or CIGAR-less records. Check `is_unmapped` before using them.

### Flags

Common boolean properties:

- pairing: `is_paired`, `is_proper_pair`, `is_read1`, `is_read2`
- orientation: `is_reverse`, `mate_is_reverse`
- mapping: `is_unmapped`, `mate_is_unmapped`
- status: `is_secondary`, `is_supplementary`, `is_qcfail`, `is_duplicate`

For a typical primary mapped-read filter:

```python
def keep_primary(read: pysam.AlignedSegment) -> bool:
    return (
        not read.is_unmapped
        and not read.is_secondary
        and not read.is_supplementary
        and not read.is_qcfail
        and not read.is_duplicate
        and read.mapping_quality >= 20
    )
```

State whether supplementary alignments and duplicates are intentionally
excluded; there is no universal filter for every analysis. MAPQ 255 denotes
unavailable quality, and the numeric threshold above keeps it. Exclude it
explicitly when the assay requires measured MAPQ. Proper-pair flags describe
the aligner's criteria, not independent proof of a valid biological fragment.

## CIGAR Operations and Alignment Geometry

`cigartuples` stores `(operation, length)`, the reverse of textual SAM CIGAR
notation.

| Enum | Code | SAM op | Consumes query | Consumes reference |
|---|---:|---:|---:|---:|
| `CIGAR_OPS.CMATCH` | 0 | `M` | yes | yes |
| `CIGAR_OPS.CINS` | 1 | `I` | yes | no |
| `CIGAR_OPS.CDEL` | 2 | `D` | no | yes |
| `CIGAR_OPS.CREF_SKIP` | 3 | `N` | no | yes |
| `CIGAR_OPS.CSOFT_CLIP` | 4 | `S` | yes | no |
| `CIGAR_OPS.CHARD_CLIP` | 5 | `H` | no | no |
| `CIGAR_OPS.CPAD` | 6 | `P` | no | no |
| `CIGAR_OPS.CEQUAL` | 7 | `=` | yes | yes |
| `CIGAR_OPS.CDIFF` | 8 | `X` | yes | yes |
| `CIGAR_OPS.CBACK` | 9 | `B` | legacy | legacy |

Prefer enum members in new code. Top-level aliases such as `pysam.CMATCH`
remain in 0.24 for compatibility but are expected to be removed in a future
release.

Useful geometry methods:

```python
blocks = read.get_blocks()  # M/=/X blocks; D/N gaps, I

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

