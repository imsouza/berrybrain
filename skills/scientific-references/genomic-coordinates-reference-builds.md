---
id: sciref-genomic-coordinates-reference-builds
name: "Scientific Ref: Reference builds, contig naming, and liftover"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (genomic-coordinates): Reference builds, contig naming, and liftover"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "genomic coordinates reference builds"
  - "reference builds, contig naming, and liftover"
keywords:
  - "genomic"
  - "coordinates"
  - "reference"
  - "builds"
  - "specialized"
  - "scientific"
---

# Reference builds, contig naming, and liftover

A coordinate is meaningless without the assembly it was measured against. Two
files can share contig names, share a coordinate range, join cleanly, and refer
to different parts of the genome.

All lengths below were read from the UCSC `bigZips` `chrom.sizes` for each
assembly; all 24 nuclear lengths in the bundled tables were rechecked against
those downloads on 2026-10-01. GRCh37 mitochondrial context is documented by UCSC. `scripts/check_contigs.py` carries the same table and
matches files against it.

## Discriminating lengths

| Contig | GRCh37 / hg19 | GRCh38 / hg38 | T2T-CHM13v2.0 / hs1 |
| --- | --- | --- | --- |
| chr1 | 249,250,621 | 248,956,422 | 248,387,328 |
| chr2 | 243,199,373 | 242,193,529 | 242,696,752 |
| chrX | 155,270,560 | 156,040,895 | 154,259,566 |
| chrY | 59,373,566 | 57,227,415 | 62,460,029 |
| chrM / MT | 16,571 *(hg19)* / 16,569 *(GRCh37)* | 16,569 | 16,569 |

```bash
python3 check_contigs.py --identify unknown.fa.fai
```

## GRCh37 is not hg19

They are the same assembly for every primary chromosome except the
mitochondrion. UCSC's hg19 kept the older `NC_001807` sequence at **16,571 bp**;
GRCh37 adopted the revised Cambridge Reference Sequence (rCRS, `NC_012920`) at
**16,569 bp**. GRCh38 also uses rCRS, so chrM length distinguishes hg19 from
everything else but does not distinguish GRCh37 from GRCh38.

Consequences:

- Mitochondrial coordinates and alleles cannot be compared by renaming alone;
  some positions agree while others shift or refer to different bases.
- Use reference-aware sequence mapping and allele checks, or re-call from reads,
  before comparing mtDNA calls. Re-calling is not the only possible conversion.

The two also differ in naming and in alternate-haplotype handling:

| | GRCh37 (Ensembl/NCBI) | hg19 (UCSC) |
| --- | --- | --- |
| Autosomes | `1`, `2`, … | `chr1`, `chr2`, … |
| Mitochondrion | `MT` (16,569) | `chrM` (16,571) |
| Alt haplotypes | `GL000250.1`-style | 9 `chr6_cox_hap2`-style contigs |
| Unplaced | `GL000191.1`-style | `chrUn_gl000191` |

### The b37 family

`b37` (Broad) is GRCh37 with plain naming and rCRS `MT`. `hs37d5` (1000 Genomes
phase 2) is b37 plus a decoy contig (`hs37d5`) and the EBV genome. Shared primary
sequences can use an audited name map without liftover. Whole files are not
equivalent: decoy/EBV records have no counterpart in a smaller reference, and
reads may map elsewhere or remain unmapped when decoys are removed.

## GRCh38 and its ALT contigs

The base UCSC `hg38.chrom.sizes` download checked in this review has 455
sequences: 25 primary/mitochondrial, **261 `_alt`**, 42 `_random`, and 127 `chrUn_`.
These counts describe that download, not every GRCh38 patch or analysis set. The ALT contigs are alternate representations of
regions that are genuinely polymorphic — mostly MHC, and the HLA haplotypes.

ALT sequence can affect multi-mapping, MAPQ and downstream coverage. The
outcome depends on the aligner and its ALT handling; equal alignments do not
universally receive MAPQ 0. Use the reference bundle and ALT-aware alignment
procedure documented for the chosen pipeline. A no-ALT set is a distinct
analysis choice, not a universal default.

Some analysis sets mask duplicated regions such as chrY PARs. Contig lengths
cannot reveal masking or same-length substitutions. Record the exact FASTA
checksum and sequence dictionary, not just a build label.

Patch releases (`GRCh38.p13`, `p14`) add `_fix` and new `_alt` contigs but never
move a coordinate on a primary chromosome. Shared unchanged sequences keep their coordinates; patch-contig availability differs.

## T2T-CHM13

CHM13v2.0/hs1 is a different assembly, not a GRCh38 patch. Many coordinates
shift and newly resolved sequence may lack a GRCh38 counterpart. The v2.0
bundle includes chromosome Y from HG002, not the CHM13 cell line. Choose
annotations explicitly released for the target assembly and treat unresolved
or multi-mapped liftover regions as such.

## Contig naming

Four naming schemes are in circulation for the same chromosome:

```
chr1            UCSC
1               Ensembl, NCBI, GATK b37
NC_000001.11    RefSeq accession (GRCh38); NC_000001.10 is GRCh37
CM000663.2      GenBank accession (GRCh38); CM000663.1 is GRCh37
```

Note that the accession's version suffix, not the base accession, carries the
build. `NC_000001.10` and `NC_000001.11` differ only in the last character and
are different assemblies.

When sequences are proven identical, renaming is the fix; `bcftools annotate --rename-chrs`, `samtools reheader`,
and a two-column mapping file all do it. Two rules:

- Rename the **smaller, cheaper** file, and rename it to match the reference —
  never rename the reference.
- `chrM` ↔ `MT` is safe only after confirming the mitochondrial sequences match.
  GRCh37/GRCh38 commonly use rCRS, while hg19 uses a different chrM. This says
  nothing about nuclear compatibility between GRCh37 and GRCh38.

An ordinary text join across naming schemes may not error. It returns the rows that happen to
match — often zero, sometimes a misleading subset when one file is partly
renamed. `check_contigs.py` reports style and exact-name conflicts, but alias folding
is diagnostic only. The normalizer requires exact FASTA names and does not
silently map `chrM` to `MT` or a case variant.

## Liftover

`liftOver` (UCSC, with a `.chain` file) and `CrossMap` (which also handles BAM,
VCF, and BigWig) are the working tools. Both depend on a specific source-to-target chain and supported format semantics:

- **Coordinates can vanish.** A region deleted from the newer assembly has no
  target. liftOver writes these to its unmapped file, which is easy to ignore and
  should be counted every time.
- **Mappings can be one-to-many.** A region duplicated in the target maps to
  several places; taking the first is a silent choice.
- **Strand can flip.** Inverted segments between builds mean a plus-strand
  feature lifts to the minus strand. Interval files carry this fine; anything
  where sequence orientation matters (primer sites, guide RNAs, motif hits) does
  not.
- **Interval endpoints can lift independently.** A long feature can lift to a
  different length, or split.
- **Variants need more than coordinates.** After lifting a VCF, `REF` may no
  longer match the new reference, and if the segment inverted, `REF` and `ALT`
  need reverse-complementing. CrossMap has VCF-specific handling and rejected-record output; inspect bo

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

