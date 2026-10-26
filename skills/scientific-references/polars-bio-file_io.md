---
id: sciref-polars-bio-file-io
name: "Scientific Ref: File I/O (polars-bio 0.36.0)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (polars-bio): File I/O (polars-bio 0.36.0)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "polars bio file"
  - "file i/o (polars-bio 0.36.0)"
keywords:
  - "polars"
  - "bio"
  - "file"
  - "specialized"
  - "scientific"
  - "reference"
---

# File I/O (polars-bio 0.36.0)

Use the [reader API](https://biodatageeks.org/polars-bio/api/reading/),
[format guide](https://biodatageeks.org/polars-bio/features/reading/), and
[writer API](https://biodatageeks.org/polars-bio/api/writing/).
The examples with filenames are templates. Small synthetic local reads and
round trips were exercised on 0.36.0/Polars 1.44.2; inspect real input schemas.

## Select a format-specific entry point

| Format | Eager / lazy | SQL registration | Native output |
|---|---|---|---|
| BED | `read_bed` / `scan_bed` | `register_bed` | No BED writer |
| VCF text | `read_vcf` / `scan_vcf` | `register_vcf` | `write_vcf` / `sink_vcf` |
| BCF binary | `read_bcf` / `scan_bcf` | `register_bcf` | No BCF writer |
| VCF Zarr | `read_vcf_zarr` / `scan_vcf_zarr` | `register_vcf_zarr` | None |
| BAM | `read_bam` / `scan_bam` | `register_bam` | `write_bam` / `sink_bam` |
| SAM | `read_sam` / `scan_sam` | `register_sam` | `write_sam` / `sink_sam` |
| CRAM | `read_cram` / `scan_cram` | `register_cram` (reference caveat below) | `write_cram` / `sink_cram` |
| GFF / GTF | `read_gff` / `scan_gff`; `read_gtf` / `scan_gtf` | `register_gff` / `register_gtf` | None |
| FASTA / FASTQ | `read_fasta` / `scan_fasta`; `read_fastq` / `scan_fastq` | `register_fasta` / `register_fastq` | Corresponding `write_*` / `sink_*` |
| Hi-C pairs | `read_pairs` / `scan_pairs` | `register_pairs` | None |
| Tabular text | `read_table` / `scan_table` | Use `from_polars` | Use Polars |

0.36.0 also has BGEN/PGEN, BigWig/BigBed, Cooler, MSA and structure readers.
Consult their specific signatures and companion-file requirements when needed;
this reference's examples concern genomic intervals and the formats above.

## BED and custom tables

`read_bed`/`scan_bed` expose `chrom` (String), `start`/`end` (UInt32) and
`name` (String). BED3 yields a null name. Extra BED6/BED12 fields are discarded,
not auto-detected into extra columns. Do not lose strand or exon block structure
by assuming a BED12 input is twelve output columns.

```python
import polars as pl
import polars_bio as pb

# Preserve native half-open coordinates.
regions = pb.scan_bed("regions.bed", use_zero_based=True)

# Preserve BED6 annotations; generic table readers do not convert coordinates.
bed6 = pb.scan_table("regions.bed6", schema="bed6")
bed6.config_meta.set(coordinate_system_zero_based=True)

# Nonstandard, headerless TSV: explicit Polars schema.
custom = pl.scan_csv("regions.tsv", separator="\t", has_header=False,
                     schema={"chrom": pl.String, "start": pl.Int64,
                             "end": pl.Int64, "label": pl.String})
custom.config_meta.set(coordinate_system_zero_based=True)
```

Despite its `Dict` annotation, `read_table`/`scan_table` expect a named schema
such as `"bed3"`/`"bed6"`/`"bed12"`, not a dictionary of Python types. They wrap
Polars TSV scanning; pass Polars CSV options as appropriate. Handle `track`,
`browser` and comment lines explicitly and validate field counts. BED12 block
columns need parsing/explosion if analysis is at exon level, not outer span.

There is no `pb.write_bed`: select the intended ordered BED columns and use
Polars tab-separated output with no header after confirming 0-based coordinates.

## VCF, BCF and VCF Zarr

```python
variants = pb.scan_vcf("cohort.vcf.gz", use_zero_based=True,
                       info_fields=["AF"], format_fields=["GT", "DP"])
binary = pb.scan_bcf("cohort.bcf", use_zero_based=True,
                     info_fields=[], format_fields=["GT"])
local_zarr = pb.scan_vcf_zarr("cohort.vcz", use_zero_based=True,
                             info_fields=[], format_fields=[])
```

VCF and BCF entry points are distinct; passing `.bcf` to `read_vcf` is rejected.
Base VCF columns include `chrom`, `start`, `end`, `id`, `ref`, `alt`, `qual` and
`filter`. Executed VCF output had UInt32 bounds and Float64 `qual`. There is no
universal raw `info` string: `info_fields=None` expands header declarations;
`[]` excludes them. FORMAT behaves analogously. Inspect list versus scalar
fields from their VCF Number declarations before filtering.

Single-sample FORMAT appears at the top level, with collision handling such as
`fmt_DP` when INFO already owns `DP`. Multisample `genotypes` is a struct of
per-field lists; sample order is in `pb.get_metadata(df)["header"]["sample_names"]`.
`samples=[...]` is case sensitive and follows requested order; missing names
warn and are skipped. Validate the selected names/count instead of treating a
warning as proof that every requested sample was loaded.

BCF additionally supports `genotype_output="dosage"` with
`format_fields=["GT"]`: nullable Int8 ALT counts, biallelic only, missing/partial
calls null. It is not an imputed dosage-probability reader. This option is absent
from text VCF. VCF Zarr uses local directory paths and has its own
`genotype_encoding_raw` option; do not pass that option to VCF/BCF.

VCF interval span is a representation of the record, not a complete model of
structural-variant breakends or all allele effects. Confirm END, REF length,
symbolic alleles and multiallelic normalization against the biological question.
Variant-record counts are not allele counts or independent sample counts.

### VCF writes and fidelity

```python
# Retains per-record INFO/FORMAT key layout as well as source metadata.
lf = pb.scan_vcf("cohort.vcf", use_zero_based=True,
                  preserve_record_layout=True)
pb.sink_vcf(lf.filter(pl.col("qual") > 30), "filtered.vcf.bgz")
```

Keep `_vcf_info_keys`, `_vcf_format_keys` and their metadata to retain source
key layout. Numeric values can still be canonicalized, so this is not a byte
identity guarantee. Local input header text is preserved; remote headers are
rebuilt from typed metadata and can lose free-form provenance lines. Added
annotation fields require correct header declarations. A declared `INFO_<id>`
column can supply source INFO values when an annotation column shadows `<id>`.
Write a small file and re-read with a VCF parser before relying on a transformed
header/schema. BCF is input-only; `write_vcf` emits text even if given a misleading
extension, so use `.vcf`, `.vcf.gz` or `.vcf.bgz`.

## BAM, SAM and CRAM

Executed SAM/BAM schemas contain `name`, `chrom`, `start`, `end`, `flags`,
`cigar`, `mapping_quality`, `mate_chrom`, `mate_start`, `sequence`,
`quality_scores`, `template_length`. Bounds and flags are UInt32;
`template_length` is Int32. Unmapped positions can be nu

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

