---
id: sciref-biopython-sequence-io
name: "Scientific Ref: Sequence Handling with Bio.Seq and Bio.SeqIO"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (biopython): Sequence Handling with Bio.Seq and Bio.SeqIO"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "biopython sequence"
  - "sequence handling with bio.seq and bio.seqio"
keywords:
  - "biopython"
  - "sequence"
  - "specialized"
  - "scientific"
  - "reference"
  - "handling"
---

# Sequence Handling with Bio.Seq and Bio.SeqIO

## Overview

Bio.Seq provides the `Seq` object for biological sequences with specialized methods, while Bio.SeqIO offers a unified interface for reading, writing, and converting sequence files across multiple formats.

## The Seq Object

### Creating Sequences

```python
from Bio.Seq import Seq

# Create a basic sequence
my_seq = Seq("AGTACACTGGT")

# Sequences support string-like operations
print(len(my_seq))  # Length
print(my_seq[0:5])  # Slicing
```

### Core Sequence Operations

```python
# Complement and reverse complement
complement = my_seq.complement()
rev_comp = my_seq.reverse_complement()

# Transcription (DNA to RNA)
rna = my_seq.transcribe()

# Translation (to protein)
protein = my_seq.translate()

# Back-transcription (RNA to DNA)
dna = rna.back_transcribe()
```

### Sequence Methods

- `complement()` - Returns complementary strand
- `reverse_complement()` - Returns reverse complement
- `transcribe()` - DNA to RNA transcription
- `back_transcribe()` - RNA to DNA conversion
- `translate()` - Translate to protein sequence
- `translate(table=N)` - Use specific genetic code table
- `translate(to_stop=True)` - Stop at first stop codon

## Bio.SeqIO: Sequence File I/O

### Core Functions

**Bio.SeqIO.parse()**: The primary workhorse for reading sequence files as an iterator of `SeqRecord` objects.

```python
from Bio import SeqIO

# Parse a FASTA file
for record in SeqIO.parse("sequences.fasta", "fasta"):
    print(record.id)
    print(record.seq)
    print(len(record))
```

**Bio.SeqIO.read()**: For single-record files (validates exactly one record exists).

```python
record = SeqIO.read("single.fasta", "fasta")
```

**Bio.SeqIO.write()**: Output SeqRecord objects to files.

```python
# Write records to file
count = SeqIO.write(seq_records, "output.fasta", "fasta")
print(f"Wrote {count} records")
```

**Bio.SeqIO.convert()**: Streamlined format conversion.

```python
# Convert between formats
count = SeqIO.convert("input.gbk", "genbank", "output.fasta", "fasta")
```

### Supported File Formats

Common formats include:
- **fasta** - FASTA format
- **fastq** - FASTQ format (with quality scores)
- **genbank** or **gb** - GenBank format
- **embl** - EMBL format
- **swiss** - SwissProt format
- **fasta-2line** - FASTA with sequence on one line
- **fasta-pearson** - Pearson FASTA with comment lines before the first record
- **fasta-blast** - BLAST-style FASTA where `#`, `;`, or `!` comment lines are ignored
- **tab** - Simple tab-separated format

**Biopython 1.87 note:** `format="fasta"` no longer accepts comment lines before the first `>` record. If you need to parse FASTA files with leading comments, use `format="fasta-pearson"` or `format="fasta-blast"` depending on the source convention.

### The SeqRecord Object

`SeqRecord` objects combine sequence data with annotations:

```python
record.id          # Primary identifier
record.name        # Short name
record.description # Description line
record.seq         # The actual sequence (Seq object)
record.annotations # Dictionary of additional info
record.features    # List of SeqFeature objects
record.letter_annotations  # Per-letter annotations (e.g., quality scores)
```

### Modifying Records

```python
# Modify record attributes
record.id = "new_id"
record.description = "New description"

# Extract subsequences
sub_record = record[10:30]  # Keeps per-letter data and fully contained features
# Most record.annotations and dbxrefs are deliberately omitted; review before copying.

# Reverse sequence AND transform its features/quality scores
record = record.reverse_complement(id=True, name=True, description=True)
```

## Working with Large Files

### Memory-Efficient Parsing

Use iterators to avoid loading entire files into memory:

```python
# Good for large files
for record in SeqIO.parse("large_file.fasta", "fasta"):
    if len(record.seq) > 1000:
        print(record.id)
```

### Dictionary-Based Access

Three approaches for random access:

**1. Bio.SeqIO.to_dict()** - Loads all records into memory:

```python
seq_dict = SeqIO.to_dict(SeqIO.parse("sequences.fasta", "fasta"))
record = seq_dict["sequence_id"]
```

**2. Bio.SeqIO.index()** - Lazy-loaded dictionary (memory efficient):

```python
seq_index = SeqIO.index("sequences.fasta", "fasta")
record = seq_index["sequence_id"]
seq_index.close()
```

**3. Bio.SeqIO.index_db()** - SQLite-based index for very large files:

```python
seq_index = SeqIO.index_db("index.idx", "sequences.fasta", "fasta")
record = seq_index["sequence_id"]
seq_index.close()
```

### Low-Level Parsers for High Performance

For high-throughput sequencing data, use low-level parsers that return tuples instead of objects:

```python
from Bio.SeqIO.FastaIO import SimpleFastaParser

with open("sequences.fasta") as handle:
    for title, sequence in SimpleFastaParser(handle):
        print(title, len(sequence))

from Bio.SeqIO.QualityIO import FastqGeneralIterator

with open("reads.fastq") as handle:
    for title, sequence, quality in FastqGeneralIterator(handle):
        print(title)
```

## Compressed Files

Open ordinary gzip files explicitly in text mode. BGZF supports indexed random access;
ordinary gzip does not. Consume lazy parsers before closing their handle.

```python
import gzip
from Bio import SeqIO

with gzip.open("sequences.fasta.gz", "rt") as handle:
    for record in SeqIO.parse(handle, "fasta"):
        print(record.id)

# A BGZF file can be indexed directly; close the index after use.
seq_index = SeqIO.index("sequences.fasta.bgz", "fasta")
try:
    print(list(seq_index))
finally:
    seq_index.close()
```

## Data Extraction Patterns

### Extract Specific Information

```python
# Get all IDs
ids = [record.id for record in SeqIO.parse("file.fasta", "fasta")]

# Get sequences above length threshold
long_seqs = [record for record in SeqIO.parse("file.fasta", "fasta")
             if len(record.seq) > 500]

# Extract organism from GenBank
for record in SeqIO.parse("file.gbk", "genbank"):
    organism = record.annotations.get("organism", "Unknown")
    print(f"{record.id}: {organism}")
```

### Filter and Write

```python
# Filter sequences by criteria
long_sequences = (record for record in SeqIO.parse("input.fasta", "fasta")
                  if len(record) > 500)
SeqIO.write(long_sequences, "filtered.fasta", "fasta")
```

## Best Practices

1. **Use iterators** for large files rather than loading everything into memory
2. **Prefer index()** 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

