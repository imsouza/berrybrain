---
id: sciref-pysam-cram-and-performance
name: "Scientific Ref: CRAM, Remote I/O, Threads, and Performance"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pysam): CRAM, Remote I/O, Threads, and Performance"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pysam cram performance"
  - "cram, remote i/o, threads, and performance"
keywords:
  - "pysam"
  - "cram"
  - "performance"
  - "specialized"
  - "scientific"
  - "reference"
  - "remote"
---

# CRAM, Remote I/O, Threads, and Performance

This reference targets pysam 0.24.1, which embeds HTSlib/samtools/bcftools
1.24.

## Pysam 0.24 CRAM Changes

Pysam 0.24 is the first pysam release to wrap HTSlib 1.22 or later. Two
inherited operational changes matter:

1. New CRAM output defaults to CRAM **3.1**, not 3.0.
2. HTSlib no longer contacts the EBI CRAM reference server by default.

For compatibility with a consumer that cannot read CRAM 3.1:

```python
with pysam.AlignmentFile(
    "output.cram",
    "wc",
    header=header,
    reference_filename="reference.fa",
    format_options=["version=3.0"],
) as output:
    ...
```

In pysam 0.24, `format_options` accepts a list of Python `str` values as
documented.

## Why the Reference Matters

CRAM commonly stores differences from a reference rather than complete read
sequences. A matching reference can therefore be required to decode or encode
records.

Reference identity is represented by `M5` MD5 values and often `UR` fields in
`@SQ` header lines. Contig names alone are not sufficient.

Treat the reference as part of the data provenance:

- preserve the exact FASTA used to create the CRAM
- preserve its `.fai`
- record assembly/version and checksum
- back up reference cache content when it is the only decoding source
- verify contig lengths and M5 tags

Some CRAM files embed all or part of their reference, but do not assume that
every CRAM is self-contained.

## Deterministic Local CRAM Access

Prefer an explicit local FASTA:

```python
import pysam

pysam.faidx("reference.fa")

with pysam.AlignmentFile(
    "sample.cram",
    "rc",
    reference_filename="reference.fa",
    require_index=True,
    threads=4,
) as cram:
    for read in cram.fetch("chr1", 1_000, 2_000):
        ...
```

Use the same reference when writing:

```python
with pysam.AlignmentFile("input.bam", "rb") as source, pysam.AlignmentFile(
    "output.cram",
    "wc",
    template=source,
    reference_filename="reference.fa",
    threads=4,
) as destination:
    for read in source.fetch(until_eof=True):
        destination.write(read)
```

Then create a CRAI and read the output back with the same FASTA.

## `REF_PATH` and `REF_CACHE`

Use these HTSlib environment variables only when reference-by-MD5 lookup is
intentional:

- `REF_PATH`: colon-separated local paths and optionally URLs used to find a
  sequence by its M5 checksum
- `REF_CACHE`: location where retrieved references are cached

A local cache layout commonly uses:

```text
/reference-cache/%2s/%2s/%s
```

Do not add a remote endpoint merely to make an error disappear. Network
reference lookup changes reproducibility, privacy, availability, and cache
behavior. Pysam 0.24 intentionally inherits HTSlib's removal of implicit EBI
fetching.

When remote lookup is required:

- configure a controlled institutional proxy/cache where possible
- place a local cache before remote sources
- ensure downloads are checksum-validated
- document network and retention behavior
- avoid credentials in URLs and logs

An explicit `reference_filename=` is usually clearer for a single known
assembly.

## Convert BAM to CRAM with Wrapped Samtools

For bulk conversion:

```python
import pysam.samtools

pysam.samtools.view(
    "-@",
    "4",
    "-C",
    "-T",
    "reference.fa",
    "-o",
    "output.cram",
    "input.bam",
    catch_stdout=False,
)
pysam.samtools.index(
    "-@",
    "4",
    "output.cram",
    catch_stdout=False,
)
```

Using `-o` plus `catch_stdout=False` avoids capturing binary CRAM output in
Python memory.

Validate:

```python
pysam.samtools.quickcheck("-v", "output.cram")

with pysam.AlignmentFile(
    "output.cram",
    "rc",
    reference_filename="reference.fa",
) as cram:
    first = next(cram.fetch(until_eof=True), None)
```

`quickcheck` is structural, not a full decode or biological validation.
Compare record counts and selected records to the source.

## CRAM Failure Diagnosis

When CRAM open/fetch fails, check in this order:

1. Confirm the FASTA assembly and contig names.
2. Confirm `.fai` exists and lengths match the alignment header.
3. Inspect `@SQ` `M5` and `UR` fields.
4. Pass `reference_filename=` explicitly.
5. Confirm CRAI matches the current CRAM.
6. Try a sequential read to separate index from reference problems.
7. Capture HTSlib/samtools error messages.

Do not disable validation or substitute a similarly named assembly.

## Remote HTSlib I/O

Depending on how the wheel/build was configured, HTSlib can read HTTP(S) and
other plugin-backed URLs. Random access also needs a reachable index and range
request support.

The following URLs are illustrative placeholders, not a deployed endpoint.
Remote access was checked against upstream contracts, not a production service.

```python
with pysam.AlignmentFile(
    "https://example.org/data/sample.bam",
    "rb",
    index_filename="https://example.org/data/sample.bam.bai",
) as bam:
    for read in bam.fetch("chr1", 1_000, 2_000):
        ...
```

Remote support is build- and protocol-dependent. Before large analysis:

- issue one small known region query
- verify the exact index URL
- check content versioning/immutability
- confirm retries, timeout behavior, and credentials outside logs
- estimate request count from the access pattern

Many tiny random queries can be slower and more expensive than downloading or
staging a file once. Never put bearer tokens or secrets directly in committed
URLs.

## Threads

`threads=` on `AlignmentFile` and `VariantFile` controls HTSlib
compression/decompression threads:

```python
with pysam.AlignmentFile("sample.bam", "rb", threads=4) as bam:
    ...
```

In 0.24.1, `TabixFile` accepts `threads=` but its open path resets it to 1;
do not assume threaded tabix decoding. Linux 0.24.1 wheels load networking
libraries dynamically and restore Debian/Ubuntu S3 support; a wheel install
alone does not prove those runtime libraries/credentials are present.

It does **not** parallelize Python filtering, pileup interpretation, or
statistical analysis. More threads can increase memory and I/O contention, and
returns diminish when storage or network is the bottleneck.

`threads > 1` cannot be combined with `ignore_truncation=True`.

## Python Thread Safety

Pysam releases the GIL for many I/O-intensive operations, but not every code
path has been comprehensively validated for thread safety.

Avoid sharing one active file handle across threads. Prefer:

- one independently opened handle per worker, or
- indep

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

