---
id: sci-genomic-coordinates
name: "Scientific: genomic-coordinates"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Converts genomic intervals between coordinate conventions, normalises and compares variant representations, and detects assembly or contig-naming mismatches before they corrupt an analysis. Used whenever coordinates cross a format, tool, or assembly boundary - converting between "
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "genomic coordinates"
  - "genomic-coordinates"
keywords:
  - "genomic"
  - "coordinates"
  - "converts"
  - "intervals"
  - "between"
  - "coordinate"
  - "conventions"
---

# Genomic Coordinates

## When to use

Any time a coordinate crosses a boundary: between two file formats, between two
tools, between two assemblies, or between the genome and a transcript.

## The rule

**A coordinate is three facts, not one: the number, the convention it is written
in, and the assembly it was measured against.** Carry all three or the number is
not interpretable.

Coordinate errors are the quietest class of bug in genomics. An off-by-one BED
file parses, sorts, and intersects without complaint. A GRCh37 VCF joined against
a GRCh38 annotation returns rows. A right-shifted indel simply fails to match its
entry in ClinVar, and the result is a variant reported as novel. Nothing raises
an error; the answer is just wrong, and it is wrong in a direction that looks
plausible.

So: convert with the table, not from memory, and verify against the reference
whenever a reference is available.

## The two conversions

```
1-based inclusive  ->  0-based half-open :  start - 1,  end
0-based half-open  ->  1-based inclusive :  start + 1,  end
```

These formulas apply to nonempty spans on the same reference and strand. They do
not encode insertions, circular wraparound, liftover, or transcript mapping.

## Which format is which

| 0-based, half-open | 1-based, inclusive |
| --- | --- |
| BED, bedGraph, bigWig, narrowPeak | GFF3, GTF, VCF |
| BAM (binary POS), BCF (binary POS) | SAM text POS, CRAM absolute alignment start |
| PSL, genePred, refFlat | WIG, Picard interval_list |
| MAF (UCSC multiple alignment) | MAF (TCGA mutation annotation) |
| PyRanges, pybedtools | GRanges/IRanges, samtools & UCSC & Ensembl region strings |

Both "MAF" formats exist, they mean different things, and they disagree. UCSC
serves 0-based files through a 1-based browser box. `references/format-conventions.md`
has the full table with per-format detail.

```bash
cd skills/genomic-coordinates/scripts

python3 convert_coords.py --list                          # the table
python3 convert_coords.py --from bed --to gff chr1 999 1000
python3 convert_coords.py --from ucsc --to bed "chr7:5,530,601-5,530,625"
python3 convert_coords.py --from granges --to pyranges --input regions.tsv
```

```
contig  input                 output           length  status  detail
chr7    chr7:5530601-5530625  5530600-5530625  25      ok
```

Zero-length BED features (`chromStart == chromEnd`, a legal insertion point) are
reported as `unrepresentable` for an inclusive target because the converter lacks
feature semantics. GFF3 can encode insertion sites with equal endpoints and a
feature type; that is different from an ordinary single-base interval. Exit code
is 1 for invalid or unrepresentable output; valid zero-length half-open output
exits 0. Output is a diagnostic TSV/JSON table, not a rewritten GFF/VCF.

`--input` parses BED/bedGraph, GFF/GTF, literal-allele VCF REF spans, explicit
region strings, and three-column GRanges/PyRanges/Python TSVs. Other table rows
are conventions only: extract an interval with a native parser and pass a triple.
All bundled text readers expect uncompressed files.

## Variants are not intervals

For a simple VCF indel, `POS` normally identifies the unchanged padding base
before the event. At contig position 1 the padding can follow the event. Complex
substitutions need not have an unchanged anchor. And the same change can be written many ways:
`chr1:7:CAC:C`, `chr1:3:CAC:C` and `chr1:2:GCA:G` are one deletion. Joining,
deduplicating, or looking up variants before normalising loses real matches
silently, and it loses them preferentially in repeats, where indels concentrate.

Normalise — trim to parsimony, then left-align against the reference — before any
comparison:

```bash
python3 normalize_variant.py --fasta ref.fa chr1 7 CAC C
python3 normalize_variant.py --fasta ref.fa --split --input cohort.vcf
python3 normalize_variant.py --fasta ref.fa --compare chr1:7:CAC:C chr1:2:GCA:G
```

```
input         normalized    type      pos_shift  ref_check  changed
chr1:7:CAC:C  chr1:2:GCA:G  deletion  5          ok         yes
```

Literal alleles are checked against the FASTA using exact contig names. A
`MISMATCH` can indicate an assembly, sequence, strand, or coordinate error; stop
and investigate with `check_contigs.py` and sequence provenance. The helper
rejects unsplit ALT lists: use `--split` for independently normalized allele keys.
Its TSV discards genotypes and annotations; use `bcftools norm` for production
VCF rewriting. Symbolic/breakend/missing/spanning-deletion alleles are passed
through as `skipped`, without REF or structural validation.

The default left-shift window is 1,000 bp. If it prevents completion, the helper
returns `incomplete`, exits 1, and refuses an equivalence verdict. Increase
`--window` and rerun. Matching normalized keys tests individual literal alleles,
not haplotype equivalence across multiple records.

[HGVS applies the 3'-most rule](https://hgvs-nomenclature.org/stable/recommendations/general/)
to the reference sequence being described. For transcript `c.`/`n.` notation,
this means increasing genomic coordinates on a plus-strand gene and decreasing
coordinates on a minus-strand gene. The minus-strand direction can therefore
agree with VCF left-alignment; genomic `g.` notation shifts toward the contig
end. Details and exceptions: `references/variant-representation.md`.

## Check the assembly before trusting a join

```bash
python3 check_contigs.py --identify unknown.fa.fai
python3 check_contigs.py variants.vcf annotation.gtf --genome GRCh38.fa.fai
```

```
file          kind    contigs  naming        assembly  detail
ref.fa.fai    sizes   25       plain         GRCh37    24/24 primary chromosome lengths match;
                                                       chrM is 16569 bp, i.e. GRCh37/38 (rCRS MT)
```

The script reads `.fai`, `.chrom.sizes`, VCF headers, SAM headers, FASTA, BED,
and GTF/GFF, identifies the assembly from primary-chromosome lengths, and reports
detectable conflicts: naming mismatch, length
conflict, coordinates past a contig end, contigs present in one file only. Exit
code 1 on a detected conflict. `unknown`/`ambiguous` with exit 0 is not proof of
compatibility; lengths cannot detect same-length sequence changes or masking.
Reference contig supersets are expected. VCF header and record extents are both
checked when comparing; SV/gVCF spans require a native validator.

**GRCh37 and hg19 share primary nuclear coordinates, but differ in mitochondria

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

