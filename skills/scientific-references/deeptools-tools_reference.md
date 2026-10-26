---
id: sciref-deeptools-tools-reference
name: "Scientific Ref: deepTools Complete Tool Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (deeptools): deepTools Complete Tool Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "deeptools tools reference"
  - "deeptools complete tool reference"
keywords:
  - "deeptools"
  - "tools"
  - "reference"
  - "specialized"
  - "scientific"
  - "complete"
---

# deepTools Complete Tool Reference

Targets the released deepTools 4.0.0 commands. This is a reference for the main CLI tools; run each command/subcommand with `--help` for its complete parser. Examples are templates. See `review.md` for executed tests and limits.

## BAM and bigWig File Processing Tools

### multiBamSummary

Computes read coverages for genomic regions across multiple BAM files, outputting compressed numpy arrays for downstream correlation and PCA analysis.

**Modes:**
- **bins**: Genome-wide analysis using consecutive equal-sized windows (default 10kb)
- **BED-file**: Restricts analysis to user-specified genomic regions

**Key Parameters:**
- `--bamfiles, -b`: Indexed BAM files (space-separated, required)
- `--outFileName, -o`: Output coverage matrix file (required)
- `--BED`: Region specification file (BED-file mode only)
- `--binSize`: Window size in bases (default: 10,000)
- `--labels`: Custom sample identifiers
- `--minMappingQuality`: Quality threshold for read inclusion
- `--numberOfProcessors, -p`: Parallel processing cores
- `--extendReads`: Fragment size extension
- `--samFlagExclude 1024`: Exclude already-marked duplicate alignments (0x400)
- `--outRawCounts`: Export tab-delimited file with coordinate columns and per-sample counts

**Output:** Compressed numpy array (.npz) for plotCorrelation and plotPCA

**Common Usage:**
```bash
# Genome-wide comparison
multiBamSummary bins --bamfiles sample1.bam sample2.bam -o results.npz

# Peak region comparison
multiBamSummary BED-file --BED peaks.bed --bamfiles sample1.bam sample2.bam -o results.npz
```

---

### multiBigwigSummary

Similar to multiBamSummary but operates on bigWig files instead of BAM files. Used for comparing coverage tracks across samples.

**Modes:**
- **bins**: Genome-wide analysis
- **BED-file**: Region-specific analysis

**Key Parameters:** `--bwfiles, -b` for bigWigs; `--BED` for BED-file mode; `--binSize`, `--outRawCounts`, labels and processors. BAM read/flag/extension options do not apply

---

### bamCoverage

Converts BAM alignment files into normalized coverage tracks in bigWig or bedGraph formats. Calculates coverage as number of reads per bin.

**Key Parameters:**
- `--bam, -b`: Input BAM file (required)
- `--outFileName, -o`: Output filename (required)
- `--outFileFormat, -of`: Output type (bigwig or bedgraph)
- `--normalizeUsing`: Normalization method
  - **RPKM**: Reads Per Kilobase per Million mapped reads
  - **CPM**: Counts Per Million mapped reads
  - **BPM**: Numerically CPM in the released Rust implementation (despite different rolling-doc formula)
  - **RPGC**: Reads per genomic content (requires --effectiveGenomeSize)
  - **None**: No normalization (default)
- `--effectiveGenomeSize`: Mappable genome size (required for RPGC)
- `--binSize`: Resolution in base pairs (default: 50)
- `--extendReads, -e`: Extend reads to fragment length (recommended for ChIP-seq, NOT for RNA-seq)
- `--centerReads`: Center reads at fragment length for sharper signals
- `--samFlagExclude 1024`: Exclude already-marked duplicates; no coordinate deduplication
- `--minMappingQuality`: Filter reads below quality threshold
- `--minFragmentLength / --maxFragmentLength`: Fragment length filtering
- `--smoothLength`: Window averaging for noise reduction
- `--MNase`: Analyze MNase-seq data for nucleosome positioning
- `--Offset`: Position-specific offsets (useful for RiboSeq, GROseq)
- `--filterRNAstrand`: Separate forward/reverse strand reads
- `--ignoreForNormalization`: Exclude chromosomes from normalization (e.g., sex chromosomes)
- `--numberOfProcessors, -p`: Parallel processing

**Important Notes:**
- For RNA-seq: Do NOT use --extendReads (would extend over splice junctions)
- `--filterRNAstrand` assumes common dUTP/NSR/NNSR reverse-stranded libraries; verify library orientation before interpreting forward/reverse tracks
- For ChIP-seq: Use --extendReads with smaller bin sizes
- Never apply --samFlagExclude 1024 after GC bias correction

**Common Usage:**
```bash
# Basic coverage with RPKM normalization
bamCoverage --bam input.bam --outFileName coverage.bw --normalizeUsing RPKM

# ChIP-seq with extension
bamCoverage --bam chip.bam --outFileName chip_coverage.bw \
    --binSize 10 --extendReads 200 --samFlagExclude 1024

# Strand-specific RNA-seq
bamCoverage --bam rnaseq.bam --outFileName forward.bw \
    --filterRNAstrand forward
```

---

### bamCompare

Compares two BAM files by generating bigWig or bedGraph files, normalizing for sequencing depth differences. Processes genome in equal-sized bins and performs per-bin calculations.

**Comparison Methods:**
- **log2** (default): Log2 ratio of samples
- **ratio**: Direct ratio calculation
- **subtract**: Difference between files
- **add/mean/first/second**: Advertised by the parser but fell through to log2 in 4.0.0; use bamCoverage plus bigwigCompare for these operations
- **reciprocal_ratio**: Released Rust behavior reverses the documented magnitude; do not rely on this option for signed fold changes

**Scaling/normalization:**
- `--scaleFactorsMethod readCount` (default) or `None`; SES is removed in 4.0.0.
- For `--normalizeUsing RPKM`, `CPM`, or `BPM`, set `--scaleFactorsMethod None`.
- The released Rust command accepts RPGC with --effectiveGenomeSize; tiny-fixture ratio scaling passed, contradicting the rolling docs note that it exits.
- Separate bamCoverage tracks followed by bigwigCompare make RPGC normalization easier to inspect. Rust operations round output to two decimals; unequal pseudocounts also affect subtract.

**Key Parameters:**
- `--bamfile1, -b1`: First BAM file (required)
- `--bamfile2, -b2`: Second BAM file (required)
- `--outFileName, -o`: Output filename (required)
- `--outFileFormat`: bigwig or bedgraph
- `--operation`: Comparison method (see above)
- `--scaleFactorsMethod`: readCount or None (separate from --normalizeUsing)
- `--binSize`: Bin width for output (default: 50bp)
- `--pseudocount`: Avoid division by zero (default: 1)
- `--extendReads`: Extend reads to fragment length
- `--samFlagExclude 1024`: Exclude already-marked duplicate alignments
- `--minMappingQuality`: Quality threshold
- `--numberOfProcessors, -p`: Parallelization

**Common Usage:**
```bash
# Log2 ratio of treatment vs control
bamCompare -b1 treatment.bam -b2 control.bam -o log2ratio.bw

# Subtract control from treatment
bamCompare -b1 treatment.bam -b2 control.bam -o difference.bw \
    --operation subtract --scaleFactorsMethod readCount
```

---



*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

