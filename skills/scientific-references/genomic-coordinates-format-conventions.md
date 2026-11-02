---
id: sciref-genomic-coordinates-format-conventions
name: "Scientific Ref: Coordinate conventions, format by format"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (genomic-coordinates): Coordinate conventions, format by format"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "genomic coordinates format conventions"
  - "coordinate conventions, format by format"
keywords:
  - "genomic"
  - "coordinates"
  - "format"
  - "conventions"
  - "specialized"
  - "scientific"
  - "reference"
  - "coordinate"
---

# Coordinate conventions, format by format

Two independent choices define a convention, and formats mix them freely:

- **Base**: is the first base of a contig called 0 or 1?
- **Closure**: is the end coordinate part of the interval (inclusive) or one past
  it (half-open)?

There is no correlation between a format's age, its authorship, or its purpose and
which pair it picked. UCSC alone ships both.

## The table

| Format | Convention | Length | Notes |
| --- | --- | --- | --- |
| BED (3/6/12) | 0-based half-open | `end - start` | `chromStart` may be 0 |
| bedGraph | 0-based half-open | `end - start` | despite sitting next to WIG |
| bigWig / bigBed | 0-based half-open | `end - start` | binary; matches BED |
| narrowPeak / broadPeak | 0-based half-open | `end - start` | BED6+4 and BED6+3 |
| WIG (fixedStep, variableStep) | 1-based inclusive | `end - start + 1` | the trap next to bedGraph |
| GFF3 | 1-based inclusive | `end - start + 1` | `start <= end` always |
| GTF / GFF2 | 1-based inclusive | `end - start + 1` | GENCODE, Ensembl |
| VCF text | 1-based POS | `len(REF)` for literal REF span | event span can differ; BCF binary POS is 0-based |
| SAM (text) | 1-based inclusive | from CIGAR | `POS` is the leftmost mapped base |
| BAM (binary) | 0-based | from CIGAR | encoded alignment start |
| CRAM | 1-based absolute alignment start | from alignment | AP can be delta encoded; do not treat it as BAM |
| genePred / refFlat | 0-based half-open | `end - start` | `exonEnds` are exclusive |
| PSL (BLAT) | 0-based half-open | `end - start` | see the minus-strand note below |
| Picard interval_list | 1-based inclusive | `end - start + 1` | GATK targets, bait sets |
| MAF — Mutation Annotation | 1-based inclusive | `End - Start + 1` | TCGA somatic calls |
| MAF — Multiple Alignment | 0-based half-open | `size` field | UCSC whole-genome alignments |
| samtools / tabix region string | 1-based inclusive | `end - start + 1` | `chr3:1000-2000` is 1001 bp |
| UCSC browser position box | 1-based inclusive | `end - start + 1` | 1-based UI over 0-based files |
| Ensembl REST region string | 1-based inclusive | `end - start + 1` | `chr:start..end:strand` |
| IGV locus box | 1-based inclusive | `end - start + 1` | matches the UCSC box |
| Bioconductor GRanges / IRanges | 1-based inclusive | `width()` | R ecosystem default |
| PyRanges / pybedtools | 0-based half-open | `End - Start` | Python ecosystem default |

`scripts/convert_coords.py --list` prints its supported convention names. It
converts explicit interval triples; its limited file readers are listed in
`../SKILL.md`. It is not a native parser for every format in this table.

## The conversions worth memorising

For ordinary nonempty spans, these two transformations cover the base/closure change:

```
1-based inclusive  ->  0-based half-open :  start - 1,  end
0-based half-open  ->  1-based inclusive :  start + 1,  end
```

For these nonempty spans on one reference, only the start changes. This rule
does not describe strand reversal, insertions, circular features, or liftover.

## Per-format detail

### BED

`chromStart` is 0-based, `chromEnd` is exclusive. The first base of a chromosome
is `0 1`. A single base at 1-based position 100 is `99 100`.

`chromStart == chromEnd` is a **legal zero-length feature** — an insertion point
between two bases, used by some variant tracks. Converting it requires feature
semantics. GFF3 represents an insertion after base N with start=end=N; the same
numbers can also denote a one-base feature. The generic converter reports
`unrepresentable` for inclusive targets instead of guessing the feature meaning.

BED12 block fields have exact rules that hand-written files routinely break:

- `blockStarts` are offsets **from `chromStart`**, not absolute coordinates.
- `blockStarts[0]` must be `0`.
- `chromStart + blockStarts[-1] + blockSizes[-1]` must equal `chromEnd`.
- `blockCount` must equal the length of both lists.

`thickStart`/`thickEnd` delimit the CDS and must lie within `chromStart`/`chromEnd`;
`thickStart == thickEnd` marks a non-coding transcript.

narrowPeak's tenth column, `peak`, is an offset **from `chromStart`**, or `-1` when
no summit was called. Adding it to `chromStart` gives the summit; treating it as an
absolute coordinate puts the summit on the wrong chromosome arm.

### GFF3 and GTF

Both are 1-based inclusive across nine tab-separated columns. `start <= end` is
required **regardless of strand** — a minus-strand exon is still written with the
smaller coordinate first, and orientation lives only in column 7. A GFF file with
`start > end` is corrupt, not reverse-stranded.

`start == 0` violates the format; inspect provenance before deciding that an
entire file needs a shift. GFF3 circular features may have end larger than the
landmark length to encode crossing its origin. The `##FASTA` directive terminates
feature rows and introduces an optional sequence section.

Column 8 is **phase** in GFF3 and **frame** in GTF, and they mean the same thing:
the bases to skip from the transcriptional start of this segment to find the
next complete codon. Retain those bases when concatenating CDS segments: they
complete the codon begun in the preceding exon. Values are `0`, `1`, `2`, or `.`. It is not the reading
frame of the feature's start position, and it is not `start % 3`. Every CDS
feature should declare it; a missing phase requires annotation-specific review.

Attribute syntax differs and parsers key on it:

```
GFF3   ID=exon1;Parent=transcript1;gene_name=TP53
GTF    gene_id "ENSG00000141510"; transcript_id "ENST00000269305";
```

A `.gtf` file containing GFF3 attributes may fail or lose attributes in readers
that choose a parser from the extension.

`exon_number` in GTF counts in **transcription order**, so on the minus strand
exon 1 has the largest genomic coordinate. Sorting exons by coordinate and
numbering them reproduces the right answer only on the plus strand.

### VCF

`POS` is 1-based and refers to the first base of `REF`. The interval a record
occupies is `POS` to `POS + len(REF) - 1`.

For a simple indel, the unchanged padding base normally precedes the event;
at the beginning of a contig, it follows it. Complex substitutions need not have
an unchanged padding base.

```
reference   ...  A  C  G  T  T  T  A  ...
positions        4  5  6  7  8  9 10

deletion of TT at 8-9    POS=7  REF=TTT   ALT=T
insertion of AA after 7  POS=7  REF=T     ALT=TAA
SNV at 7                POS=7  REF=T     AL

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

