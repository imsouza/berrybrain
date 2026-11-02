---
id: sciref-genomic-coordinates-transcript-coordinates
name: "Scientific Ref: Transcript, CDS, and protein coordinates"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (genomic-coordinates): Transcript, CDS, and protein coordinates"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "genomic coordinates transcript coordinates"
  - "transcript, cds, and protein coordinates"
keywords:
  - "genomic"
  - "coordinates"
  - "transcript"
  - "specialized"
  - "scientific"
  - "reference"
---

# Transcript, CDS, and protein coordinates

Four coordinate spaces describe the same locus, and a position number is
meaningless without saying which one it is in.

| Space | Prefix | Origin | Counts |
| --- | --- | --- | --- |
| Genomic | `g.` | contig base 1 | every base, introns included |
| Transcript | `n.` | transcript base 1 | spliced bases, UTRs included |
| Coding | `c.` | the `A` of the initiator `ATG` | spliced coding bases |
| Protein | `p.` | initiator methionine | residues |

"Position 250" in a paper, a spreadsheet column, or a variant list is ambiguous
between all four, and the four differ by hundreds of bases.

## Genomic to transcript

The transcript is the concatenation of its exons in **transcription order**.
Introns are not numbered. On the minus strand, transcription order is decreasing
genomic coordinate, and the transcript sequence is the reverse complement.

Synthetic worked example of a two-exon minus-strand transcript (not a real
GRCh38 annotation):

```
exon 2:  chr1:1,000-1,099   (100 bp)   transcribed second
exon 1:  chr1:2,000-2,199   (200 bp)   transcribed first
```

Transcript position 1 is genomic 2,199 — the *highest* coordinate. Positions
1–200 walk down exon 1 to genomic 2,000; position 201 jumps to genomic 1,099;
positions 201–300 walk down exon 2 to genomic 1,000.

Converting a genomic position to a transcript position:

1. Confirm the position falls inside an exon. If it does not, it is intronic and
   has no plain transcript coordinate — see the intronic notation below.
2. Sum the lengths of all exons before it in transcription order.
3. Add its offset within its own exon, counted in transcription order:
   `pos - exon_start + 1` on the plus strand, `exon_end - pos + 1` on the minus.

Getting step 3's strand handling wrong is the single most common error here, and
it fails silently: the number produced is a valid transcript coordinate, just the
wrong one, mirrored within the exon.

## Transcript to coding

`c.1` is the first base of the initiator codon, not the first base of the
transcript. If the 5' UTR is 150 bases long, transcript position 151 is `c.1`.

HGVS coding numbering has no zero and uses four distinct forms:

| Region | Notation | Example |
| --- | --- | --- |
| 5' UTR | negative, counting back from `c.1` | `c.-15` |
| CDS | positive | `c.742` |
| 3' UTR | `*`, counting from the base after the stop codon | `c.*23` |
| Intron | nearest exonic base, then offset | `c.742+3`, `c.743-12` |

Intronic offsets are relative to the nearest exon boundary: `+` counts forward
from the last base of the preceding exon, `-` counts back from the first base of
the following exon. Bases in the 5' half of an intron take the `+` form, those in
the 3' half take the `-` form. `c.742+1` and `c.742+2` are the donor
dinucleotide; `c.743-2` and `c.743-1` are the acceptor positions. For an odd-length intron,
the midpoint uses the upstream `+` form. An intronic HGVS description needs a
genomic reference with the versioned transcript model; a spliced transcript
accession alone does not contain those intronic bases.

There is no `c.0`. A tool that emits one has an off-by-one at the UTR boundary.

## Coding to protein

```
codon      = (c_pos - 1) // 3 + 1
in_codon   = (c_pos - 1) %  3 + 1     # 1, 2 or 3
```

`p.1` is the initiator methionine. `c.1`, `c.2` and `c.3` all map to `p.1`, so
protein coordinates lose information — three different nucleotide variants share
one protein position, and two of them may be synonymous.

This formula maps a positive coding-base position to a codon index. Predicting
a protein change additionally needs alleles, transcript sequence, phase, splice
effects and the genetic code; it is not an arithmetic conversion of a variant. A protein
position corresponds to three nucleotide positions, and a protein *change*
usually corresponds to several possible nucleotide changes. Back-translating a
`p.` description into a genomic coordinate requires the transcript sequence and
still may be ambiguous. Never do it arithmetically.

## Phase, and why it is not frame

GFF3 column 8 (`phase`, called `frame` in GTF) locates the next complete codon
from the transcriptional start of this CDS segment. Do not remove phase bases
from each exon before concatenation: they can complete the preceding codon.
It takes the values 0, 1, and 2.

It is not `start % 3`, and it is not a property of the genomic position. It is
determined by how many coding bases precede this feature in the transcript:

```
phase = (3 - (coding_bases_before_this_CDS % 3)) % 3
```

A complete CDS beginning at its initiation codon starts at phase 0. Partial
CDSs can start with nonzero phase; special translation annotations can break
the simple cumulative-length rule. On the minus strand, "start of
the feature" means the end with the **higher** genomic coordinate, because that is
where translation reaches first.

Concatenating CDS features in genomic order and translating produces protein for
plus-strand genes and nonsense for minus-strand genes. On the minus strand, either reverse-complement the concatenated genomic-order
segments once, or reverse-complement each segment and join in transcription
order. Doing both reversals of segment order gives the wrong sequence.

Check whether the annotation includes the stop codon in CDS rows. GENCODE GTF
uses separate stop_codon features; blindly treating the CDS end as the end of
the HGVS coding reference can move the c.* boundary by three bases.

## Which transcript

A gene has many transcripts and the same variant gets a different `c.` and `p.`
in each. A `c.` description without a versioned transcript accession is not
actionable.

| Source | Default choice |
| --- | --- |
| MANE Select | one transcript per protein-coding gene, identical in RefSeq and Ensembl |
| Ensembl canonical | MANE Select where one exists, otherwise Ensembl's own rule |
| RefSeq Select | one per gene, not always the same as Ensembl canonical |
| UCSC canonical | track-dependent; inspect the actual selection and release |
| VEP output | transcript consequences depend on options and format; VCF CSQ can contain several in one row |

MANE Select provides a matched RefSeq/Ensembl transcript pair for supported
human genes. It is a useful reporting baseline, not proof that other isoforms
are irrelevant; MANE Plus Clinical adds transcripts needed for some clinically
relevant variants. Preserve the transcript used by the original evidence.

The version suffix matters. `ENST00

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

