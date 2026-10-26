---
id: sciref-pysam-api-reference
name: "Scientific Ref: Pysam 0.24 API Quick Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pysam): Pysam 0.24 API Quick Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pysam api reference"
  - "pysam 0.24 api quick reference"
keywords:
  - "pysam"
  - "api"
  - "reference"
  - "specialized"
  - "scientific"
  - "quick"
---

# Pysam 0.24 API Quick Reference

This is a compact navigation aid, not a replacement for the official API
documentation. Signatures and defaults below are for pysam 0.24.1.

## Alignment Files

### Constructor

```python
pysam.AlignmentFile(
    filepath_or_object,
    mode=None,  # pass the remaining options by keyword
    template=None,
    reference_names=None,
    reference_lengths=None,
    text=None,
    header=None,
    add_sq_text=True,
    add_sam_header=True,
    check_header=True,
    check_sq=True,
    reference_filename=None,
    index_filename=None,
    filepath_index=None,
    require_index=False,
    duplicate_filehandle=True,
    ignore_truncation=False,
    format_options=None,
    threads=1,
)
```

Core methods:

```python
AlignmentFile.fetch(
    contig=None,
    start=None,
    stop=None,
    region=None,
    tid=None,
    until_eof=False,
    multiple_iterators=False,
    reference=None,  # compatibility alias
    end=None,        # compatibility alias
)

AlignmentFile.count(
    contig=None,
    start=None,
    stop=None,
    region=None,
    until_eof=False,
    read_callback="nofilter",
    reference=None,
    end=None,
)

AlignmentFile.count_coverage(
    contig,
    start=None,
    stop=None,
    region=None,
    quality_threshold=15,
    read_callback="all",
    reference=None,
    end=None,
)

AlignmentFile.pileup(
    contig=None,
    start=None,
    stop=None,
    region=None,
    reference=None,
    end=None,
    **kwargs,
)
```

Important pileup kwargs/defaults:

| Option | Default | Meaning |
|---|---:|---|
| `truncate` | `False` | limit columns to exact query interval |
| `max_depth` | `8000` | maximum depth |
| `stepper` | `"samtools"` in current implementation/docs context | read filtering/processing mode |
| `fastafile` | `None` | reference for BAQ/samtools behavior |
| `ignore_overlaps` | `True` | adjust qualities of overlapping paired bases |
| `ignore_orphans` | `True` | exclude improper paired orphans |
| `flag_filter` | unmapped, secondary, QC-fail, duplicate | excluded flags |
| `flag_require` | `0` | required flags |
| `min_base_quality` | `13` | base-quality threshold |
| `min_mapping_quality` | `0` | mapping-quality threshold |
| `compute_baq` | `True` | compute BAQ when reference is available |
| `redo_baq` | `False` | recompute existing BAQ |

For `count_coverage`, pass numeric `contig`, `start`, `stop` within contig
bounds; the accepted `region`/`end` aliases do not size its arrays correctly
in 0.24.1.

Always pass important pileup semantics explicitly rather than depending on
defaults. `get_num_aligned()` is a quality-filtered pileup-entry count in
0.24.1 and can include D/N entries. Count non-deletion/non-refskip entries
explicitly for observed base depth.

Other useful methods/properties:

- `write(read)`
- `has_index()` / `check_index()`
- `get_index_statistics()`
- `get_reference_name(tid)` / `get_tid(name)`
- `get_reference_length(name)`
- `find_introns(read_iterator)`
- `head(n, multiple_iterators=True)`
- `references`, `lengths`, `nreferences`
- `mapped`, `unmapped`, `nocoordinate` when index statistics support them;
  CRAI returns zeros because it stores no such counts

## `AlignedSegment`

Construction:

```python
read = pysam.AlignedSegment(header=None)
```

Prefer passing the destination `AlignmentHeader`.

Frequently used attributes:

- identity: `query_name`, `query_sequence`, `query_qualities`
- query spans: `query_length`, `query_alignment_start`,
  `query_alignment_end`, `query_alignment_length`
- reference: `reference_id`, `reference_name`, `reference_start`,
  `reference_end`, `reference_length`
- mapping: `mapping_quality`, `cigarstring`, `cigartuples`
- mate: `next_reference_id`, `next_reference_name`,
  `next_reference_start`, `template_length`
- flags: `flag` and `is_*` boolean properties

Methods:

- `get_tag(tag, with_value_type=False)`
- `set_tag(tag, value, value_type=None, replace=True)`
- `has_tag(tag)`
- `get_tags(with_value_type=False)`
- `set_tags(tags)`
- `get_aligned_pairs(matches_only=False, with_seq=False, with_cigar=False)`
- `get_blocks()`
- `get_reference_positions(full_length=False)`
- `get_reference_sequence()` (requires MD)
- `get_forward_sequence()` / `get_forward_qualities()`
- `infer_query_length()` / `infer_read_length()`

Modified-base properties:

- `modified_bases`
- `modified_bases_forward`

They return mappings from `(canonical_base, strand, modification)` to
`(query_position, quality)` calls.

## Pileup Objects

`PileupColumn`:

- `reference_id`, `reference_name`, `reference_pos`
- `nsegments`
- `pileups`
- `get_num_aligned()`
- `get_query_sequences(...)`
- `get_query_qualities()`
- `get_mapping_qualities()`

`PileupRead`:

- `alignment`
- `query_position`
- `query_position_or_next`
- `is_del`
- `is_refskip`
- `indel`
- `level`

Read column values before the iterator advances; the buffer is reused.
`PileupRead.level` is exposed but is not currently computed.

## Variant Files

### Constructor

```python
pysam.VariantFile(
    filename,
    mode=None,
    index_filename=None,
    header=None,
    drop_samples=False,
    duplicate_filehandle=True,
    ignore_truncation=False,
    threads=1,
)
```

Core methods:

```python
VariantFile.fetch(
    contig=None,
    start=None,
    stop=None,
    region=None,
    reopen=False,
    end=None,
    reference=None,
)

VariantFile.subset_samples(include_samples)
VariantFile.new_record(*args, **kwargs)
VariantFile.write(record)
```

Numeric fetch coordinates are 0-based, half-open. `reopen=True` supports
multiple simultaneous iterators. Use `contig`, not the legacy `reference`
alias: without `contig` or `region`, 0.24.1 selects the sequential-rewind path
before interpreting that alias.

`VariantHeader`:

```python
header.copy()
header.add_meta(key, value=None, items=None)
header.add_line(line)
header.add_sample(sample)
header.new_record(
    contig=None,
    start=0,
    stop=0,
    alleles=None,
    id=None,
    qual=None,
    filter=None,
    info=None,
    samples=None,
    **kwargs,
)
```

Metadata collections:

- `contigs`
- `samples`
- `filters`
- `info`
- `formats`
- `records`

`VariantRecord`:

- location: `contig`, `chrom`, `pos`, `start`, `stop`, `rlen`
- alleles: `ref`, `alts`, `alleles`, `alleles_variant_types`
- metadata: `id`, `qual`, `filter`, `info`
- samples: `samples`
- methods: `copy()`, `translate(destination_header)`

## FASTA and FASTX

```python
pysam.FastaFile(
    filename,
    filepath_index=None,
    filepath_inde

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

