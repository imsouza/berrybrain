---
id: sciref-gtars-cli
name: "Scientific Ref: Command-line interface (`gtars-cli==0.10.0`)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (gtars): Command-line interface (`gtars-cli==0.10.0`)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "gtars cli"
  - "command-line interface (`gtars-cli==0.10.0`)"
keywords:
  - "gtars"
  - "cli"
  - "specialized"
  - "scientific"
  - "reference"
  - "command"
  - "line"
---

# Command-line interface (`gtars-cli==0.10.0`)

Source-reviewed from the published 0.10.0 crate (commit `90141b6`) on **2026-10-01**.
Commands below are illustrative templates; this audit did not compile the CLI.
The package is `gtars-cli`; the installed binary is `gtars`.

## Trust, installation, and features

Cargo installation compiles native code and may run transitive build scripts.
Review the official crate/source, lock resolution, license, and build environment
before:

```bash
cargo install gtars-cli --version 0.10.0 --locked
gtars --version
gtars --help
```

If using a precompiled binary, verify that its version and checksum match the
reviewed release before extraction or execution. The bundled `artifact_inspector.py` hashes/classifies an
artifact without extracting or executing it.

Default CLI features are:

```text
scoring uniwig bbcache igd fragsplit overlaprs genomicdist refget
```

To build a reduced binary:

```bash
cargo install gtars-cli --version 0.10.0 --locked \
  --no-default-features --features "overlaprs,genomicdist"
```

Feature availability controls subcommand availability. There is no 0.10.0 CLI
`tokenizers` feature/subcommand. Do not copy an old `--all-features` binary's
command assumptions into a reduced binary.

## Global behavior

```bash
gtars --help
gtars --version
gtars <command> --help
```

Tagged source defines no global `--threads`, `--memory-limit`, `--buffer-size`,
`--verbose`, `--quiet`, `--strict`, `--continue-on-error`, or `--log-file`
options. Concurrency is command-specific.

Before every real command, run the exact installed `--help`. This reference is
pinned to 0.10.0; unversioned web documentation can drift.

## `overlaprs`

```bash
gtars overlaprs \
  --query query.bed \
  --universe universe.bed \
  --backend bits
```

Options:

- `-q/--query PATH` (required);
- `-u/--universe PATH` (required);
- `-e/--backend bits|ailist` (handler default: `bits`);
- `--streaming` is parsed but ignored by the v0.10.0 handler.

Output is BED3 universe-hit coordinates to stdout, one row per overlap. It is not
a count table and does not retain query IDs. See `overlap.md`.

## `igd`

Create from a **folder** of BED files:

```bash
gtars igd create \
  --filelist approved-bed-directory \
  --output index-directory \
  --dbname reference_index
```

Search with a BED/BED.GZ query:

```bash
gtars igd search \
  --database index-directory/reference_index.igd \
  --query query.bed
```

Current subcommands are `create` and `search`, not `build`, `query`, or `count`.
The handler accepts a directory, a `.txt` file of paths, or `-`/`stdin`.
Directory discovery includes every `.bed` or `.gz` file, so use a reviewed list
when that would include unrelated gzip files. Create the output directory first.
`search --database` needs the `.igd` **file**, not its parent directory. Output
is per-database-file overlap counts plus a total, not row-aligned query matches.

## `uniwig`

Batch BigWig:

```bash
gtars uniwig \
  --file sorted.bed.gz \
  --filetype bed \
  --chromref assembly.chrom.sizes \
  --smoothsize 5 \
  --stepsize 1 \
  --fileheader output/sample_ \
  --outputtype bw \
  --counttype core \
  --threads 4
```

BAM QC:

```bash
gtars uniwig bamqc \
  --input aligned.bam \
  --output bamqc.tsv \
  --threads 1
```

BED streaming adds `--streaming` and supports only WIG/bedGraph output. Read
`coverage.md` for all flags, sorting/bounds, BAM behavior, and resource limits.

## `consensus`

```bash
gtars consensus \
  --beds a.bed b.bed c.bed \
  --min-count 2 \
  --output consensus.bed
```

- `--beds` requires at least two paths;
- `--min-count` defaults to 1;
- output defaults to stdout and is BED4 (`chr start end count`).

Consensus counts input sets overlapping a reduced union component; it is not
per-base support segmentation. See `overlap.md`.

## `ranges`

`ranges` exposes interval algebra:

```text
gtars ranges reduce      --input BED [--output OUT]
gtars ranges trim        --input BED --chrom-sizes SIZES [--output OUT]
gtars ranges promoters   --input BED [--upstream 2000] [--downstream 200] [--output OUT]
gtars ranges setdiff     -a BED_A -b BED_B [--output OUT]
gtars ranges pintersect  -a BED_A -b BED_B [--output OUT]
gtars ranges concat      -a BED_A -b BED_B [--output OUT]
gtars ranges union       -a BED_A -b BED_B [--output OUT]
gtars ranges jaccard     -a BED_A -b BED_B
gtars ranges shift       --input BED --offset N [--output OUT]
gtars ranges flank       --input BED --width N [--start|--both] [--output OUT]
gtars ranges resize      --input BED --width N [--fix start|end|center] [--output OUT]
gtars ranges narrow      --input BED [--start N] [--end N] [--width N] [--output OUT]
gtars ranges disjoin     --input BED [--output OUT]
gtars ranges gaps        --input BED --chrom-sizes SIZES [--output OUT]
gtars ranges intersect   -a BED_A -b BED_B [--output OUT]
```

Operations without `--output` write to stdout. `promoters` is anchored on region
starts in core behavior; do not assume strand-aware TSS handling.

## `fscoring` fragment counts

File-by-peak matrix:

```bash
gtars fscoring "fragments/sample01.fragments.tsv.gz" consensus.bed \
  --mode chip \
  --output counts.csv.gz
```

Arguments are positional:

```text
gtars fscoring <fragments> <consensus> [--mode atac|chip] [--output PATH]
```

- `fragments` is interpreted by `FragmentFileGlob`; a single explicit local file
  is safest. Shell globs can expose unintended files, while quoted globs are
  expanded by the library.
- default mode is `atac`;
- default output is `fscoring.csv.gz`;
- the shown `chip` mode uses fragment-body overlap semantics, one increment per
  row/peak overlap; it ignores the fifth fragment-support count;
- **do not use the default `atac` mode for scientific results in this pin.**
  The CLI's locked `gtars-scoring 0.5.2` constructs its right-cut query as
  `[fragment.end - 5, fragment.end - 6)`, an invalid reversed interval; small
  coordinates can also underflow unsigned arithmetic. This is a source-confirmed
  correctness issue, not a validated ATAC count implementation. The planner
  refuses to approve this mode. Use a separately validated cut-site workflow if
  ATAC insertion counts are required; selecting `chip` changes the measurement.

Sparse barcode mode:

```bash
gtars fscoring sample.fragments.tsv.gz consensus.bed \
  --barcode \
  --output output/sample01
```

This writes:

```text
output/sample01_matrix.mtx.gz
output/sample01_barcodes.tsv.gz
output/sample01_features

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

