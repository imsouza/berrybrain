---
id: sciref-scikit-bio-api-reference
name: "Scientific Ref: scikit-bio API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scikit-bio): scikit-bio API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scikit bio api reference"
  - "scikit-bio api reference"
keywords:
  - "scikit"
  - "bio"
  - "api"
  - "reference"
  - "specialized"
  - "scientific"
---

# scikit-bio API Reference

Targets scikit-bio 0.7.4, reviewed 2026-10-01. Filename/undefined-input examples are templates; tiny native regression tests exercise the corrected API and numerical contracts. [Review evidence and limits](review.md).

## Table of Contents
1. [Sequence Classes](#sequence-classes)
2. [Alignment Methods](#alignment-methods)
3. [Phylogenetic Trees](#phylogenetic-trees)
4. [Diversity Metrics](#diversity-metrics)
5. [Ordination](#ordination)
6. [Statistical Tests](#statistical-tests)
7. [Distance Matrices](#distance-matrices)
8. [File I/O](#file-io)
9. [Troubleshooting](#troubleshooting)

## Sequence Classes

### DNA, RNA, and Protein Classes

```python
from skbio import DNA, RNA, Protein, Sequence

# Creating sequences
dna = DNA('ATCGATCGA', metadata={'id': 'seq1', 'description': 'Example'})
rna = RNA('AUCGAUCG')
protein = Protein('ACDEFGHIKLMNPQRSTVWY')

# Sequence operations
dna_rc = dna.reverse_complement()  # Reverse complement
rna = dna.transcribe()  # DNA -> RNA
protein = rna.translate()  # RNA -> Protein

# Using genetic code tables
protein = rna.translate(genetic_code=11)  # Bacterial code
```

### Sequence Searching and Pattern Matching

```python
# Find motifs using regex
dna = DNA('ATGCGATCGATGCATCG')
motif_locs = dna.find_with_regex('(ATG.{3})')  # capture groups yield slices

# Find all positions
import re
for match in re.finditer('ATG', str(dna)):
    print(f"ATG found at position {match.start()}")

# k-mer counting using the public API
kmers = dna.kmer_frequencies(k=3)
```

### Handling Sequence Metadata

```python
# Sequence-level metadata
dna = DNA('ATCG', metadata={'id': 'seq1', 'source': 'E. coli'})
print(dna.metadata['id'])

# Positional metadata (per-base quality scores from FASTQ)
from skbio import DNA
seqs = DNA.read('reads.fastq', format='fastq', phred_offset=33)
quality_scores = seqs.positional_metadata['quality']

# Interval metadata (features/annotations)
dna.interval_metadata.add([(0, 4)], metadata={'type': 'gene', 'name': 'geneA'})
```

### Distance Calculations

```python
from skbio import DNA

seq1 = DNA('ATCGATCG')
seq2 = DNA('ATCG--CG')

# Hamming distance (default)
dist = seq1.distance(seq2)

# Custom distance function
from skbio.sequence.distance import kmer_distance
from functools import partial
dist = seq1.distance(seq2, metric=partial(kmer_distance, k=3))
```

## Alignment Methods

### Pairwise Alignment

scikit-bio 0.7.0 introduced `pair_align`, a single fast engine for global, local, and semi-global alignment. The convenience wrappers `pair_align_nucl` and `pair_align_prot` ship with BLASTN/BLASTP-like scoring. The old SSW wrapper (`local_pairwise_align_ssw`, `StripedSmithWaterman`) was removed, and the pure-Python `global_pairwise_align`/`local_pairwise_align_*` functions are deprecated.

```python
from skbio import DNA, Protein
from skbio.alignment import pair_align_nucl, pair_align_prot, pair_align, align_score

# Nucleotide alignment with BLASTN-like defaults
seq1 = DNA('ATCGATCGATCG')
seq2 = DNA('ATCGGGGATCG')
aln = pair_align_nucl(seq1, seq2)

# Inspect the result (PairAlignResult: score + paths [+ matrices])
print(f"Score: {aln.score}")
path = aln.paths[0]                       # PairAlignPath; repr shows the CIGAR
aligned_seqs = path.to_aligned((seq1, seq2))   # list of gapped strings

# Global alignment with custom affine scoring via pair_align
aln = pair_align(
    seq1, seq2,
    mode='global',
    free_ends=False,        # default True would be semi-global/overlap
    sub_score=(2, -3),      # (match, mismatch)
    gap_cost=(5, 2),        # (open, extend) -> affine; a single number -> linear
)

# Use a named substitution matrix instead of match/mismatch scores
aln = pair_align(seq1, seq2, mode='global', sub_score='NUC.4.4', gap_cost=3)

# Protein alignment with BLASTP-like defaults (BLOSUM62)
protein_query = Protein('ACDEFGHIKLMNPQRSTVWY')
protein_target = Protein('ACDEFMNPQRSTVWY')
aln = pair_align_prot(protein_query, protein_target)

# Re-score an existing alignment with the same parameters
score = align_score((aln.paths[0], (protein_query, protein_target)),
                    sub_score='BLOSUM62', gap_cost=(11, 1))

# PairAlignResult also unpacks as a tuple
score, (path,), _ = pair_align_nucl(seq1, seq2)
```

### Multiple Sequence Alignment

```python
from skbio.alignment import TabularMSA, pair_align_nucl
from skbio import DNA

# Read MSA from file
msa = TabularMSA.read('alignment.fasta', constructor=DNA)

# Build a TabularMSA from a pairwise alignment path + original sequences
score, (path,), _ = pair_align_nucl(DNA('ATCGATCG'), DNA('ATCGGGGATCG'))
msa = TabularMSA.from_path_seqs(path, (DNA('ATCGATCG'), DNA('ATCGGGGATCG')))

# Create MSA manually
seqs = [
    DNA('ATCG--'),
    DNA('ATGG--'),
    DNA('ATCGAT')
]
msa = TabularMSA(seqs)

# MSA operations
consensus = msa.consensus()
# consensus() is the majority consensus; ties follow alphabet order

# Calculate conservation
conservation = msa.conservation()

# Access sequences
first_seq = msa[0]
column = msa[:, 2]  # Third column

# Filter gaps
keep = msa.gap_frequencies(axis='sequence', relative=True) <= 0.5
degapped_msa = msa.iloc[:, keep]

# Entropy in bits; this example treats gaps as a fifth symbol
from scipy.stats import entropy
position_entropies = [entropy(list(col.frequencies().values()), base=2)
                      for col in msa.iter_positions()]
```

### CIGAR Strings and Alignment Paths

```python
from skbio.alignment import PairAlignPath, AlignPath, pair_align_nucl
from skbio import DNA

# Parse a CIGAR string into a pairwise alignment path
path = PairAlignPath.from_cigar('10M2I5M3D10M')
print(repr(path))   # <PairAlignPath, ..., CIGAR: '10M2I5M3D10M'>

# A path produced by pair_align already carries its CIGAR
aln = pair_align_nucl(DNA('ATCGATCG'), DNA('ATCGGGGATCG'))
cigar_string = aln.paths[0].to_cigar()

# AlignPath generalizes to >2 sequences (e.g., from aligned strings)
path3 = AlignPath.from_aligned(['CGTCGTGC', 'CA--GT-C', 'CGTCGT-T'])

# Parse CIGAR output from external tools such as parasail
# path = PairAlignPath.from_cigar(res.cigar.decode)
```

## Phylogenetic Trees

### Tree Construction

```python
from skbio import TreeNode, DistanceMatrix
from skbio.tree import nj, upgma

# Distance matrix
dm = DistanceMatrix([[0, 5, 9, 9],
                     [5, 0, 10, 10],
                     [9, 10, 0, 8],
                     [9, 10, 8, 0]],
                    ids=['A', 'B', 'C', 'D'])

# Neighbor joining
nj_tree = nj(dm)

# UP

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

