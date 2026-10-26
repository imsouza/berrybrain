---
id: sciref-pysam-sequence-files
name: "Scientific Ref: FASTA, FASTQ, and Tabix-Indexed Files"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pysam): FASTA, FASTQ, and Tabix-Indexed Files"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pysam sequence files"
  - "fasta, fastq, and tabix-indexed files"
keywords:
  - "pysam"
  - "sequence"
  - "files"
  - "specialized"
  - "scientific"
  - "reference"
  - "fasta"
  - "fastq"
---

# FASTA, FASTQ, and Tabix-Indexed Files

This reference targets pysam 0.24.1.

## Indexed FASTA

`FastaFile` provides random access through a faidx index.

```python
import pysam

pysam.faidx("reference.fa")

with pysam.FastaFile("reference.fa") as fasta:
    print(fasta.references)
    print(fasta.lengths)
    print(fasta.get_reference_length("chr1"))
```

An uncompressed FASTA uses `<name>.fai`. With a default index path, `FastaFile`
can build a missing index on open. Pass an existing `filepath_index` to prevent
implicit index creation (as the bundled inspector does). A BGZF-compressed FASTA also needs a
`.gzi` compressed-offset index. Ordinary gzip is not suitable for indexed
random access.

The constructor can use nonstandard index paths:

```python
fasta = pysam.FastaFile(
    "reference.fa.gz",
    filepath_index="indexes/reference.fa.gz.fai",
    filepath_index_compressed="indexes/reference.fa.gz.gzi",
)
```

### Numeric and string coordinates

```python
with pysam.FastaFile("reference.fa") as fasta:
    # Numeric: 0-based, half-open
    sequence = fasta.fetch("chr1", 999, 1_099)

    # Region string: 1-based, inclusive
    same_sequence = fasta.fetch(region="chr1:1000-1099")
```

If start or end is omitted, pysam uses the sequence boundary. Negative or
inverted coordinates raise, but an end beyond the contig clips and a start
at/beyond the end returns an empty string in 0.24.1. Check
`0 <= start <= stop <= fasta.get_reference_length(contig)` when exact length
is required; absence of an exception is not a bounds check.

### Fetch variant context

```python
def variant_context(
    fasta: pysam.FastaFile,
    contig: str,
    pos_1based: int,
    ref: str,
    flank: int = 20,
) -> tuple[str, bool]:
    if pos_1based < 1 or flank < 0 or not ref:
        raise ValueError("positive POS, nonempty REF, and nonnegative flank required")
    start = pos_1based - 1
    if start + len(ref) > fasta.get_reference_length(contig):
        raise ValueError("REF extends beyond the contig")
    context_start = max(0, start - flank)
    context_stop = min(
        fasta.get_reference_length(contig),
        start + len(ref) + flank,
    )
    context = fasta.fetch(contig, context_start, context_stop)
    observed_ref = fasta.fetch(contig, start, start + len(ref))
    return context, observed_ref.upper() == ref.upper()
```

Validate the entire REF allele, not only its first base. A mismatch often
means the VCF and FASTA use different assemblies, contig aliases, or
normalization.

### Strand-aware extraction

Coordinates do not encode strand. Reverse-complement after fetching:

```python
sequence = fasta.fetch("chr1", start, stop)
if strand == "-":
    sequence = pysam.reverse_complement(sequence)
```

Confirm annotation coordinates before conversion: BED is normally 0-based
half-open; GFF/GTF text is normally 1-based inclusive.

## Sequential FASTA and FASTQ

`FastxFile` streams FASTA, FASTQ, or mixed FASTX records. It does not implement
random access.

```python
with pysam.FastxFile("reads.fastq.gz") as reads:
    for record in reads:
        print(record.name)
        print(record.sequence)
        print(record.comment)
        print(record.quality)
```

The current class is `FastxFile`; `FastqFile` is an old compatibility name.

### Record persistence

`persist=True` is the default and copies each record so it remains valid.
For high-throughput scans, `persist=False` avoids the copy:

```python
with pysam.FastxFile("reads.fastq.gz", persist=False) as reads:
    for record in reads:
        process(record.name, record.sequence)
        # Do not save `record` for use after the iterator advances.
```

With `persist=False`, records are read-only proxies and cease to be valid after
iteration advances. Copy needed strings or use the default when retaining
records.

### Quality scores

```python
with pysam.FastxFile("reads.fastq") as reads:
    for record in reads:
        if record.quality is None:  # FASTA record
            continue
        qualities = record.get_quality_array()
        mean_quality = (
            sum(qualities) / len(qualities) if qualities else None
        )
```

Pysam converts the FASTQ quality string to numeric Phred scores. Confirm the
source encoding for legacy FASTQ; modern data is normally Phred+33.

### Safe writing

`str(record)` preserves whether the record is FASTA or FASTQ and includes the
comment and quality line correctly:

```python
with pysam.FastxFile("reads.fastq.gz") as source, open(
    "filtered.fastq", "x", encoding="utf-8"
) as destination:
    for record in source:
        qualities = record.get_quality_array()
        if qualities and sum(qualities) / len(qualities) >= 20:
            destination.write(str(record) + "\n")
```

Use exclusive creation (`"x"`) when replacement was not requested. Manual
four-line FASTQ formatting can lose comments or create sequence/quality length
mismatches.

### Streaming statistics

```python
from __future__ import annotations


def fastx_stats(path: str) -> dict[str, float | int | None]:
    record_count = 0
    base_count = 0
    quality_sum = 0
    quality_count = 0

    with pysam.FastxFile(path, persist=False) as records:
        for record in records:
            record_count += 1
            base_count += len(record.sequence)
            if record.quality is not None:
                qualities = record.get_quality_array()
                quality_sum += sum(qualities)
                quality_count += len(qualities)

    return {
        "records": record_count,
        "bases": base_count,
        "mean_length": (
            base_count / record_count if record_count else None
        ),
        "mean_quality": (
            quality_sum / quality_count if quality_count else None
        ),
    }
```

This is a full scan but has constant memory.

## BGZF and Tabix

`TabixFile` provides random access to coordinate-sorted, BGZF-compressed
tabular files.

### Non-destructive compression and indexing

```python
import pysam

pysam.tabix_compress("regions.bed", "regions.bed.gz")
pysam.tabix_index("regions.bed.gz", preset="bed")
```

This leaves `regions.bed` intact. By contrast, calling `tabix_index()` directly
on an uncompressed file may automatically compress it and remove the original
unless `keep_original=True`.

Do not use `force=True` unless replacing existing compressed data or indexes is
explicitly intended.

### Input requirements

- Sort by contig and coordinate first. The wrapper does not sort or perfor

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

