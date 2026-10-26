---
id: sciref-biopython-alignment
name: "Scientific Ref: Sequence Alignments with Bio.Align and Bio.AlignIO"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (biopython): Sequence Alignments with Bio.Align and Bio.AlignIO"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "biopython alignment"
  - "sequence alignments with bio.align and bio.alignio"
keywords:
  - "biopython"
  - "alignment"
  - "specialized"
  - "scientific"
  - "reference"
  - "sequence"
  - "alignments"
---

# Sequence Alignments with Bio.Align and Bio.AlignIO

## Overview

Bio.Align provides tools for pairwise sequence alignment using various algorithms, while Bio.AlignIO handles reading and writing multiple sequence alignment files in various formats.

## Pairwise Alignment with Bio.Align

### The PairwiseAligner Class

The `PairwiseAligner` class performs pairwise sequence alignments using Needleman-Wunsch (global), Smith-Waterman (local), Gotoh (three-state), and Waterman-Smith-Beyer algorithms. The appropriate algorithm is automatically selected based on gap score parameters.

### Creating an Aligner

```python
from Bio import Align

# Create aligner with default parameters
aligner = Align.PairwiseAligner()

# Default scores (as of Biopython 1.86+):
# - Match score: +1.0
# - Mismatch score: 0.0
# - All gap scores: -1.0  (changed from 0 in 1.86 to avoid trivial tie alignments)
```

**Note (1.86+):** The default gap score changed from 0 to -1. Previously, mismatches and gap combinations could score 0, producing many logically equivalent alignments. To restore pre-1.86 behavior:

```python
aligner.gap_score = 0
```

### Customizing Alignment Parameters

```python
# Set scoring parameters
aligner.match_score = 2.0
aligner.mismatch_score = -1.0
aligner.gap_score = -0.5

# Or use separate gap opening/extension penalties
aligner.open_gap_score = -2.0
aligner.extend_gap_score = -0.5

# Set internal gap scores separately
aligner.open_internal_gap_score = -2.0
aligner.extend_internal_gap_score = -0.5

# Set end gap scores (for semi-global alignment)
aligner.open_left_gap_score = 0.0
aligner.extend_left_gap_score = 0.0
aligner.open_right_gap_score = 0.0
aligner.extend_right_gap_score = 0.0
```

### Alignment Modes

```python
# Global alignment (default)
aligner.mode = 'global'

# Local alignment
aligner.mode = 'local'
```

### Performing Alignments

```python
from Bio.Seq import Seq

seq1 = Seq("ACCGGT")
seq2 = Seq("ACGGT")

# Get all optimal alignments
alignments = aligner.align(seq1, seq2)

# Iterate through alignments
for alignment in alignments:
    print(alignment)
    print(f"Score: {alignment.score}")

# Get just the score
score = aligner.score(seq1, seq2)
```

### Using Substitution Matrices

```python
from Bio.Align import substitution_matrices

# Load a substitution matrix
matrix = substitution_matrices.load("BLOSUM62")
aligner.substitution_matrix = matrix

# Align protein sequences
protein1 = Seq("KEVLA")
protein2 = Seq("KSVLA")
alignments = aligner.align(protein1, protein2)
```

### Available Substitution Matrices

Common matrices include:
- **BLOSUM** series (BLOSUM45, BLOSUM50, BLOSUM62, BLOSUM80, BLOSUM90)
- **PAM** series (PAM30, PAM70, PAM250)
- **MATCH** - Simple match/mismatch matrix

```python
# List available matrices
available = substitution_matrices.load()
print(available)
```

## Multiple Sequence Alignments with Bio.AlignIO

### Reading Alignments

Bio.AlignIO provides similar API to Bio.SeqIO but for alignment files:

```python
from Bio import AlignIO

# Read a single alignment
alignment = AlignIO.read("alignment.aln", "clustal")

# Parse multiple alignments from a file
for alignment in AlignIO.parse("alignments.aln", "clustal"):
    print(f"Alignment with {len(alignment)} sequences")
    print(f"Alignment length: {alignment.get_alignment_length()}")
```

### Supported Alignment Formats

Common formats include:
- **clustal** - Clustal format
- **phylip** - PHYLIP format
- **phylip-relaxed** - Relaxed PHYLIP (longer names)
- **stockholm** - Stockholm format
- **fasta** - FASTA format (aligned)
- **nexus** - NEXUS format
- **emboss** - EMBOSS alignment format
- **msf** - MSF format
- **maf** - Multiple Alignment Format

### Writing Alignments

```python
# Write alignment to file
AlignIO.write(alignment, "output.aln", "clustal")

# Convert between formats
count = AlignIO.convert("input.aln", "clustal", "output.phy", "phylip")
```

### Working with Alignment Objects

```python
from Bio import AlignIO

alignment = AlignIO.read("alignment.aln", "clustal")

# Get alignment properties
print(f"Number of sequences: {len(alignment)}")
print(f"Alignment length: {alignment.get_alignment_length()}")

# Access individual sequences
for record in alignment:
    print(f"{record.id}: {record.seq}")

# Get alignment column
column = alignment[:, 0]  # First column

# Get alignment slice
sub_alignment = alignment[:, 10:20]  # Positions 10-20

# Get specific sequence
seq_record = alignment[0]  # First sequence
```

### Alignment Analysis

```python
# Calculate alignment statistics with current Biopython APIs.
# Avoid Bio.AlignInfo.SummaryInfo: it is deprecated in 1.86 and several
# methods were removed in 1.85/1.86.
from Bio import AlignIO
from Bio.motifs import Motif

msa = AlignIO.read("alignment.aln", "clustal")
alignment = msa.alignment  # New-style Bio.Align.Alignment

# Build a motif from a DNA alignment to inspect per-column counts
motif = Motif("ACGT", alignment)
counts = motif.counts
consensus = counts.consensus

# Information content replacement for deprecated SummaryInfo methods
information_content = sum(motif.relative_entropy)

# Replacement dictionary from the new-style Alignment object
substitutions = alignment.substitutions
```

## Creating Alignments Programmatically

### From SeqRecord Objects

```python
from Bio.Align import MultipleSeqAlignment
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq

# Create records
records = [
    SeqRecord(Seq("ACTGCTAGCTAG"), id="seq1"),
    SeqRecord(Seq("ACT-CTAGCTAG"), id="seq2"),
    SeqRecord(Seq("ACTGCTA-CTAG"), id="seq3"),
]

# Create alignment
alignment = MultipleSeqAlignment(records)
```

### Adding Sequences to Alignments

```python
# Start with empty alignment
alignment = MultipleSeqAlignment([])

# Add sequences (must have same length)
alignment.append(SeqRecord(Seq("ACTG"), id="seq1"))
alignment.append(SeqRecord(Seq("ACTG"), id="seq2"))

# Extend with another alignment
alignment.extend(other_alignment)
```

## Advanced Alignment Operations

### Removing Gaps

```python
# Remove all gap-only columns
no_gaps = []
for i in range(alignment.get_alignment_length()):
    column = alignment[:, i]
    if set(column) != {'-'}:  # Not all gaps
        no_gaps.append(column)
```

### Alignment Sorting

```python
# Sort by sequence ID
sorted_alignment = sorted(alignment, key=lambda x: x.id)
alignment = MultipleSeqAlignment(sorted_alignment)
```

### Computing Pairwise Identities

```python
def pairwise_identity(seq1, seq2):


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

