---
id: sciref-biopython-blast
name: "Scientific Ref: BLAST Operations with Bio.Blast"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (biopython): BLAST Operations with Bio.Blast"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "biopython blast"
  - "blast operations with bio.blast"
keywords:
  - "biopython"
  - "blast"
  - "specialized"
  - "scientific"
  - "reference"
  - "operations"
---

# BLAST Operations with Bio.Blast

## Overview

Bio.Blast provides tools for running BLAST searches (both locally and via NCBI web services) and parsing BLAST results in various formats. The module handles the complexity of submitting queries and parsing outputs.

## Running BLAST via NCBI Web Services

### Bio.Blast.NCBIWWW

The `qblast()` function submits to `https://blast.ncbi.nlm.nih.gov/Blast.cgi`
(`CMD=Put` then `CMD=Get` with the returned RID). The current URL API documents
`XML2_S` for one XML document; `XML2` can return a ZIP archive. The legacy
`NCBIWWW` API returns a text handle and `NCBIXML` supports XML1/XML2; keep that
object model separate from the newer binary-handle `Bio.Blast.qblast`/`Blast.read`.

Set `NCBIWWW.email` and `NCBIWWW.tool` before submission. Entrez settings and its
3/10 requests-per-second limits do not apply to BLAST: leave at least 10 seconds
between contacts and 60 seconds between polls of one RID. Coordinate across
workers; use local BLAST for volume. `qblast` polls internally without a hard
completion deadline. These remote examples were checked against docs/source and
mocked transport, not submitted to the public search queue.

```python
from Bio.Blast import NCBIWWW
NCBIWWW.email = "your.email@example.com"
NCBIWWW.tool = "your_tool_name"
```

Submit a single query:

```python
from Bio.Blast import NCBIWWW
from Bio import SeqIO

# Read sequence from file
record = SeqIO.read("sequence.fasta", "fasta")

# Run BLAST search
result_handle = NCBIWWW.qblast(
    program="blastn",           # BLAST program
    database="nt",              # Database to search
    sequence=str(record.seq),   # Query sequence
    format_type="XML2_S"        # Single XML document, not a ZIP archive
)

# Save results
with open("blast_results.xml", "w") as out_file:
    out_file.write(result_handle.read())
result_handle.close()
```

### BLAST Programs Available

- **blastn** - Nucleotide vs nucleotide
- **blastp** - Protein vs protein
- **blastx** - Translated nucleotide vs protein
- **tblastn** - Protein vs translated nucleotide
- **tblastx** - Translated nucleotide vs translated nucleotide

### Common Databases

**Nucleotide databases:**
- `nt` - NCBI nucleotide collection; the service can substitute `core_nt`
- `core_nt` - Core nucleotide database; record the actual database in results
- `refseq_rna` - RefSeq RNA sequences

**Protein databases:**
- `nr` - NCBI nonredundant protein collection (not every possible protein)
- `refseq_protein` - RefSeq protein sequences
- `pdb` - Protein Data Bank sequences
- `swissprot` - Curated UniProtKB/Swiss-Prot

### Advanced qblast Parameters

```python
result_handle = NCBIWWW.qblast(
    program="blastn",
    database="nt",
    sequence=str(record.seq),
    expect=0.001,              # E-value threshold
    hitlist_size=50,           # Number of hits to return
    word_size=11,              # Word size for initial match
    gapcosts="5 2",            # Gap costs (open extend)
    format_type="XML2_S"       # Single XML document
)
```

### Using Sequence Files or IDs

```python
# Use FASTA format string
with open("sequence.fasta") as handle:
    fasta_string = handle.read()
result_handle = NCBIWWW.qblast("blastn", "nt", fasta_string, format_type="XML2_S")

# Use GenBank ID
result_handle = NCBIWWW.qblast("blastn", "nt", "EU490707", format_type="XML2_S")

# Prefer accession.version identifiers over historical GI numbers.
```

## Parsing BLAST Results

### Bio.Blast.NCBIXML

NCBIXML provides parsers for BLAST XML output (the recommended format):

```python
from Bio.Blast import NCBIXML

# Parse single BLAST result
with open("blast_results.xml") as result_handle:
    blast_record = NCBIXML.read(result_handle)
```

### Accessing BLAST Record Data

```python
# Query information
print(f"Query: {blast_record.query}")
print(f"Query length: {blast_record.query_length}")
print(f"Database: {blast_record.database}")
print(f"Number of sequences in database: {blast_record.database_sequences}")

# Iterate through alignments (hits)
for alignment in blast_record.alignments:
    print(f"\nHit: {alignment.title}")
    print(f"Length: {alignment.length}")
    print(f"Accession: {alignment.accession}")

    # Each alignment can have multiple HSPs (high-scoring pairs)
    for hsp in alignment.hsps:
        print(f"  E-value: {hsp.expect}")
        print(f"  Score: {hsp.score}")
        print(f"  Bits: {hsp.bits}")
        print(f"  Identities: {hsp.identities}/{hsp.align_length}")
        print(f"  Gaps: {hsp.gaps}")
        print(f"  Query: {hsp.query}")
        print(f"  Match: {hsp.match}")
        print(f"  Subject: {hsp.sbjct}")
```

### Filtering Results

```python
# Only show hits with E-value < 0.001
E_VALUE_THRESH = 0.001

for alignment in blast_record.alignments:
    for hsp in alignment.hsps:
        if hsp.expect < E_VALUE_THRESH:
            print(f"Hit: {alignment.title}")
            print(f"E-value: {hsp.expect}")
            print(f"Identities: {hsp.identities}/{hsp.align_length}")
            print()
```

### Multiple BLAST Results

For files containing multiple BLAST results (e.g., from batch searches):

```python
from Bio.Blast import NCBIXML

with open("batch_blast_results.xml") as result_handle:
    blast_records = NCBIXML.parse(result_handle)

    for blast_record in blast_records:
        print(f"\nQuery: {blast_record.query}")
        print(f"Hits: {len(blast_record.alignments)}")

        if blast_record.alignments:
            # Get best hit
            best_alignment = blast_record.alignments[0]
            best_hsp = best_alignment.hsps[0]
            print(f"Best hit: {best_alignment.title}")
            print(f"E-value: {best_hsp.expect}")
```

## Running Local BLAST

### Prerequisites

Local BLAST requires:
1. BLAST+ command-line tools installed
2. BLAST databases downloaded locally

### Running BLAST+ via subprocess

Biopython 1.86 removed `Bio.Application` and the BLAST command-line wrappers in `Bio.Blast.Applications`. Use the standard library `subprocess` module with explicit argument lists. Keep command names and flags fixed, validate file paths before running, and do not interpolate unsanitized user input into shell commands.

```python
import subprocess
from Bio.Blast import NCBIXML

cmd = [
    "blastn",
    "-query", "input.fasta",
    "-db", "local_database",
    "-evalue", "0.001",
    "-outfmt", "5",  # XML format for NCBIXML
    "-out", "results.xml",
]
subprocess.run(cmd, check=True)

# Parse results
with open

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

