---
id: sciref-pysam-variant-files
name: "Scientific Ref: Variant Files: VCF and BCF"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pysam): Variant Files: VCF and BCF"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pysam variant files"
  - "variant files: vcf and bcf"
keywords:
  - "pysam"
  - "variant"
  - "files"
  - "specialized"
  - "scientific"
  - "reference"
---

# Variant Files: VCF and BCF

This reference targets pysam 0.24.1. Numeric pysam coordinates are 0-based,
half-open even though VCF text uses a 1-based `POS`.

## Open and Iterate

`VariantFile` auto-detects VCF, BGZF-compressed VCF, and BCF input:

```python
import pysam

with pysam.VariantFile("cohort.vcf.gz", threads=4) as variants:
    for record in variants:
        print(record.contig, record.pos, record.ref, record.alts)
```

Common modes:

- `r`: VCF input
- `rb`: BCF input; input auto-detection usually makes an explicit mode
  unnecessary
- `w`: VCF output; a `.vcf.gz` suffix selects BGZF-compressed VCF
- `wb`: compressed BCF output
- `wz`: explicitly BGZF-compressed VCF output
- `wb0`: BCF in BGZF blocks with compression level zero

The advertised `wbu` mode is rejected as conflicting format specifiers in
0.24.1; use `wb0`. Do not mistake level-zero BGZF for a raw unframed BCF stream.

Writing requires a `VariantHeader`.

Useful constructor options:

- `index_filename=` for a nonstandard or remote index
- `drop_samples=True` to skip sample data
- `threads=` for compression/decompression
- `ignore_truncation=True` for missing BGZF EOF markers; not compatible with
  `threads > 1`

## Coordinates and Region Queries

```python
with pysam.VariantFile("cohort.vcf.gz") as variants:
    # Numeric coordinates: [999_999, 2_000_000)
    numeric = variants.fetch("chr1", 999_999, 2_000_000)

    # Region string: 1-based inclusive
    text = variants.fetch(region="chr1:1000000-2000000")
```

`VariantFile.fetch()` explicitly defines numeric `start`/`stop` as 0-based,
half-open. Region strings follow samtools notation.

For each `VariantRecord`:

- `contig` / `chrom`: contig name
- `pos`: 1-based VCF position
- `start`: 0-based inclusive position
- `stop`: 0-based exclusive record end
- `rlen`: reference span

Do not subtract one from a numeric `start` passed to `fetch()`. Use
`record.start` when integrating with BAM, BED, or FASTA APIs.

Random access requires:

- BGZF VCF: `.tbi` or `.csi`
- BCF: `.csi`

An unindexed VCF.gz or BCF can still be read sequentially with normal
iteration. In 0.24.1, `fetch()` with no contig/region rewinds to the start of
records and returns a sequential iterator without requiring an index. Normal
`for record in variants` iteration starts at the current position. This differs
from the broad index-driven wording in the upstream fetch docstring; verified
against tagged source and native VCF/BCF tests.

Use the canonical `contig=` keyword. In 0.24.1, supplying only the legacy
`reference=` alias takes the no-contig sequential branch and ignores the
intended region bounds.

For simultaneous iterators, `VariantFile.fetch()` uses `reopen=True`:

```python
first = variants.fetch("chr1", reopen=True)
second = variants.fetch("chr2", reopen=True)
```

## Header Model

```python
with pysam.VariantFile("cohort.vcf.gz") as variants:
    header = variants.header
    print(list(header.samples))

    for name, contig in header.contigs.items():
        print(name, contig.length)

    for name, field in header.info.items():
        print(name, field.number, field.type, field.description)
```

Important collections:

- `header.contigs`
- `header.samples`
- `header.filters`
- `header.info`
- `header.formats`
- `header.records`

INFO and FORMAT values can only be interpreted safely when their definitions
exist in the header. Do not infer missing Number/Type metadata.

## Record Fields

```python
for record in variants:
    alleles = record.alleles       # (REF, ALT1, ALT2, ...)
    alt_alleles = record.alts      # tuple or None
    identifier = record.id         # string or None
    quality = record.qual          # float or None
    filters = tuple(record.filter.keys())
```

`record.alleles_variant_types` classifies alleles with values such as `REF`,
`SNP`, `MNP`, `INDEL`, `BND`, `OVERLAP`, and `OTHER`.

Handle non-simple alleles:

- multiallelic records can have several ALT alleles
- symbolic alleles include `<DEL>`, `<DUP>`, `<INS>`, and others
- paired breakends use bracket notation; single breakends use `A.` or `.A`
- spanning deletion uses `*`
- gVCF records often use `<NON_REF>` or `<*>`

Do not apply single-nucleotide logic to every record.

## INFO Fields

```python
for record in variants:
    depth = record.info.get("DP")
    frequencies = record.info.get("AF")
    if frequencies is not None:
        for allele_index, frequency in enumerate(frequencies, start=1):
            alt = record.alleles[allele_index]
            print(alt, frequency)
```

Number semantics matter:

- `1`: one value
- `A`: one value per ALT allele
- `R`: one value per REF+ALT allele
- `G`: one value per genotype
- `.`: variable number

For FORMAT fields, 0.24.1 also supports `P` (ploidy), local-allele `LA`, `LR`,
`LG`, and modification `M` cardinalities. Preserve the source VCF version and
required companion fields such as `LAA`; these are not interchangeable with
ordinary `A`/`R`/`G`. Consult VCF 4.5 and test the actual caller's schema.

Flag fields are represented as booleans. Missing values may be `None`, a tuple
containing `None`, or absent from the mapping depending on the field.

## FILTER Semantics

```python
filters = tuple(record.filter.keys())

if "PASS" in filters:
    status = "pass"
elif not filters:
    status = "unfiltered"  # VCF '.'
else:
    status = "failed"
```

`PASS`, an empty filter set (`.`), and a failed filter are distinct states. Do
not treat `.` as equivalent to `PASS` without an explicit policy.

## Sample and Genotype Data

```python
for sample_name, call in record.samples.items():
    genotype = call.get("GT")
    depth = call.get("DP")
    genotype_quality = call.get("GQ")
    phased = call.phased
    allele_strings = call.alleles
```

Genotype allele integers index `record.alleles`:

- `0`: REF
- `1`: first ALT
- `2`: second ALT
- `None`: missing allele

Do not assume diploidy:

```python
def called_alleles(genotype):
    if genotype is None:
        return ()
    return tuple(allele for allele in genotype if allele is not None)


called = called_alleles(record.samples["sample_A"].get("GT"))
alternate_count = sum(allele > 0 for allele in called)
```

`call.phased` records separator semantics but the Python GT remains a tuple.

## Efficient Sample Subsetting

Call `subset_samples()` before retrieving any record:

```python
samples = ["sample_A", "sample_B"]

with pysam.VariantFile("cohort.bcf") as source:
    source.subset_samples(samples)
    output_header = so

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

