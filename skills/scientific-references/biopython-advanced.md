---
id: sciref-biopython-advanced
name: "Scientific Ref: Advanced Biopython Features"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (biopython): Advanced Biopython Features"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "biopython advanced"
  - "advanced biopython features"
keywords:
  - "biopython"
  - "advanced"
  - "specialized"
  - "scientific"
  - "reference"
---

# Advanced Biopython Features

## Sequence Motifs with Bio.motifs

### Creating Motifs

```python
from Bio import motifs
from Bio.Seq import Seq

# Create motif from instances
instances = [
    Seq("TACAA"),
    Seq("TACGC"),
    Seq("TACAC"),
    Seq("TACCC"),
    Seq("AACCC"),
    Seq("AATGC"),
    Seq("AATGC"),
]

motif = motifs.create(instances)
```

### Motif Consensus and Degenerate Sequences

```python
# Get consensus sequence
print(motif.counts.consensus)

# Get degenerate consensus (IUPAC ambiguity codes)
print(motif.counts.degenerate_consensus)

# Access counts matrix
print(motif.counts)
```

### Position Weight Matrix (PWM)

```python
# Create position weight matrix
motif.pseudocounts = 0.5
pwm = motif.pwm  # Keep the PWM and relative_entropy on the same pseudocount model
print(pwm)

# Calculate information content
ic = sum(motif.relative_entropy)
print(f"Information content: {ic:.2f} bits")
```

### Searching for Motifs

```python
from Bio.Seq import Seq

# Search sequence for motif
test_seq = Seq("ATACAGGACAGACATACGCATACAACATTACAC")

# Get Position Specific Scoring Matrix (PSSM)
pssm = pwm.log_odds()

# Search sequence
for position, score in pssm.search(test_seq, threshold=5.0):
    print(f"Position {position}: score = {score:.2f}")
```

### Reading Motifs from Files

```python
# Read motif from JASPAR format
with open("motif.jaspar") as handle:
    motif = motifs.read(handle, "jaspar")

# Read multiple motifs
with open("motifs.jaspar") as handle:
    for m in motifs.parse(handle, "jaspar"):
        print(m.name)

# Supported formats: jaspar, meme, transfac, pfm
```

### Writing Motifs

```python
# Write motif in JASPAR format
with open("output.jaspar", "w") as handle:
    handle.write(motif.format("jaspar"))
```

## Population Genetics with Bio.PopGen

### Working with GenePop Files

```python
from Bio.PopGen import GenePop

# Read GenePop file
with open("data.gen") as handle:
    record = GenePop.read(handle)

# Access populations
print(f"Number of populations: {len(record.populations)}")
print(f"Loci: {record.loci_list}")

# Iterate through populations
for pop_idx, pop in enumerate(record.populations):
    print(f"\nPopulation {pop_idx + 1}:")
    for individual in pop:
        print(f"  {individual[0]}: {individual[1]}")
```

### Population Statistics Require Separate Software

Biopython 1.88 retains GenePop file parsers, but does not ship
`Bio.PopGen.GenePop.Controller` or `GenePopController`. Do not call the former
`calc_fst_all`/`test_hw_pop` wrappers. Export validated GenePop data and run the
chosen population-statistics software separately; its estimates and test settings
need independent validation. No external GenePop executable was tested here.

## Sequence Utilities with Bio.SeqUtils

### GC Content

```python
from Bio.SeqUtils import gc_fraction
from Bio.Seq import Seq

seq = Seq("ATCGATCGATCG")
gc = gc_fraction(seq)
print(f"GC content: {gc:.2%}")
```

### Molecular Weight

```python
from Bio.SeqUtils import molecular_weight

# DNA molecular weight
dna_seq = Seq("ATCG")
mw = molecular_weight(dna_seq, seq_type="DNA")
print(f"DNA MW: {mw:.2f} g/mol")

# Protein molecular weight
protein_seq = Seq("ACDEFGHIKLMNPQRSTVWY")
mw = molecular_weight(protein_seq, seq_type="protein")
print(f"Protein MW: {mw:.2f} Da")
```

### Melting Temperature

```python
from Bio.SeqUtils import MeltingTemp as mt

# Calculate Tm using nearest-neighbor method
seq = Seq("ATCGATCGATCG")
tm = mt.Tm_NN(seq)
print(f"Tm: {tm:.1f}°C")

# Use different salt concentration
tm = mt.Tm_NN(seq, Na=50, Mg=1.5)  # 50 mM Na+, 1.5 mM Mg2+

# Wallace rule (for primers)
tm_wallace = mt.Tm_Wallace(seq)
```

### GC Skew

```python
from Bio.SeqUtils import GC_skew

# Calculate GC skew
seq = Seq("ATCGATCGGGCCCAAATTT")
skew = GC_skew(seq, window=100)
print(f"GC skew: {skew}")
```

### ProtParam - Protein Analysis

```python
from Bio.SeqUtils.ProtParam import ProteinAnalysis

protein_seq = "ACDEFGHIKLMNPQRSTVWY"
analyzed_seq = ProteinAnalysis(protein_seq)

# Molecular weight
print(f"MW: {analyzed_seq.molecular_weight():.2f} Da")

# Isoelectric point
print(f"pI: {analyzed_seq.isoelectric_point():.2f}")

# Amino acid composition in percent (0-100), not fractions
print(f"Composition: {analyzed_seq.amino_acids_percent}")

# Instability index
print(f"Instability: {analyzed_seq.instability_index():.2f}")

# Aromaticity
print(f"Aromaticity: {analyzed_seq.aromaticity():.2f}")

# Secondary structure fraction
ss = analyzed_seq.secondary_structure_fraction()
print(f"Helix: {ss[0]:.2%}, Turn: {ss[1]:.2%}, Sheet: {ss[2]:.2%}")

# Extinction coefficients: tuple for reduced cysteines and cystines, respectively
print(f"Extinction coefficient: {analyzed_seq.molar_extinction_coefficient()}")

# Gravy (grand average of hydropathy)
print(f"GRAVY: {analyzed_seq.gravy():.3f}")
```

## Restriction Analysis with Bio.Restriction

```python
from Bio import Restriction
from Bio.Seq import Seq

# Analyze sequence for restriction sites
seq = Seq("GAATTCATCGATCGATGAATTC")

# Use specific enzyme
ecori = Restriction.EcoRI
sites = ecori.search(seq)
print(f"EcoRI sites at: {sites}")

# Use multiple enzymes
rb = Restriction.RestrictionBatch(["EcoRI", "BamHI", "PstI"])
results = rb.search(seq)
for enzyme, sites in results.items():
    if sites:
        print(f"{enzyme}: {sites}")

# Get all enzymes that cut sequence
all_enzymes = Restriction.Analysis(rb, seq)
print(f"Cutting enzymes: {all_enzymes.with_sites()}")
```

## Sequence Translation Tables

```python
from Bio.Data import CodonTable

# Standard genetic code
standard_table = CodonTable.unambiguous_dna_by_id[1]
print(standard_table)

# Mitochondrial code
mito_table = CodonTable.unambiguous_dna_by_id[2]

# Get specific codon
print(f"ATG codes for: {standard_table.forward_table['ATG']}")

# Get stop codons
print(f"Stop codons: {standard_table.stop_codons}")

# Get start codons
print(f"Start codons: {standard_table.start_codons}")
```

## Cluster Analysis with Bio.Cluster

```python
from Bio.Cluster import kcluster
import numpy as np

# Sample data matrix (genes x conditions)
data = np.array([
    [1.2, 0.8, 0.5, 1.5],
    [0.9, 1.1, 0.7, 1.3],
    [0.2, 0.3, 2.1, 2.5],
    [0.1, 0.4, 2.3, 2.2],
])

# Perform k-means clustering
clusterid, error, nfound = kcluster(data, nclusters=2)
print(f"Cluster assignments: {clusterid}")
print(f"Error: {error}")
```

## Genome Diagrams with GenomeDiagram

```python
from Bio.Graphics import GenomeDiagram
from Bio.SeqFeature import SeqFeature, FeatureLo

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

