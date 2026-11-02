---
id: sciref-deeptools-workflows
name: "Scientific Ref: deepTools Common Workflows"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (deeptools): deepTools Common Workflows"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "deeptools workflows"
  - "deeptools common workflows"
keywords:
  - "deeptools"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
  - "common"
---

# deepTools Common Workflows

These deepTools 4.0.0 commands are templates. The four generated workflows and selected numeric contracts were exercised on tiny synthetic inputs; arbitrary data/plot variants remain illustrative. GC correction is illustrative and requires a matching 2bit genome. Inputs must be coordinate-sorted/indexed and duplicate-marked before `--samFlagExclude 1024`. The 200 bp extension is an example, not a measured fragment length. TSS requires strand-aware BED6/GTF; use matching assemblies and an effective genome size derived for the actual reference.

## ChIP-seq Quality Control Workflow

Complete quality control assessment for ChIP-seq experiments.

### Step 1: Initial Correlation Assessment

Compare replicates and samples to verify experimental quality:

```bash
# Generate coverage matrix across genome
multiBamSummary bins \
    --bamfiles Input1.bam Input2.bam ChIP1.bam ChIP2.bam \
    --labels Input_rep1 Input_rep2 ChIP_rep1 ChIP_rep2 \
    -o readCounts.npz \
    --numberOfProcessors 8

# Create correlation heatmap
plotCorrelation \
    -in readCounts.npz \
    --corMethod pearson \
    --whatToPlot heatmap \
    --plotFile correlation_heatmap.png \
    --plotNumbers

# Generate PCA plot
plotPCA \
    -in readCounts.npz \
    -o PCA_plot.png \
    -T "PCA of ChIP-seq samples"
```

**Expected Results:**
- Replicates should cluster together
- Input samples should be distinct from ChIP samples

---

### Step 2: Coverage and Depth Assessment

```bash
# Check sequencing depth and coverage
plotCoverage \
    --bamfiles Input1.bam ChIP1.bam ChIP2.bam \
    --labels Input ChIP_rep1 ChIP_rep2 \
    --plotFile coverage.png \
    --samFlagExclude 1024 \
    --numberOfProcessors 8
```

**Interpretation:** Assess whether sequencing depth is adequate for downstream analysis.

---

### Step 3: Fragment Size Validation (Paired-end)

```bash
# Verify expected fragment sizes
bamPEFragmentSize \
    --bamfiles Input1.bam ChIP1.bam ChIP2.bam \
    --histogram fragmentSizes.png \
    --plotTitle "Fragment Size Distribution"
```

**Expected Results:** Fragment sizes should match library preparation protocols (typically 200-600bp for ChIP-seq).

---

### Step 4: GC Bias Detection and Correction

```bash
# Compute GC bias
computeGCBias \
    --bamfile ChIP1.bam \
    --effectiveGenomeSize 2913022398 \
    --genome genome.2bit \
    --fragmentLength 200 \
    --biasPlot GCbias.png \
    --GCbiasFrequenciesFile freq.txt

# If bias detected, correct it
correctGCBias \
    --bamfile ChIP1.bam \
    --effectiveGenomeSize 2913022398 \
    --genome genome.2bit \
    --GCbiasFrequenciesFile freq.txt \
    --correctedFile ChIP1_GCcorrected.bam
```

**Note:** Only correct if significant bias is observed. Do NOT use `--samFlagExclude 1024` with GC-corrected files.

---

### Step 5: ChIP Signal Strength Assessment

```bash
# Evaluate ChIP enrichment quality
plotFingerprint \
    --bamfiles Input1.bam ChIP1.bam ChIP2.bam \
    --labels Input ChIP_rep1 ChIP_rep2 \
    --plotFile fingerprint.png \
    --extendReads 200 \
    --samFlagExclude 1024 \
    --numberOfProcessors 8 \
    --outQualityMetrics fingerprint_metrics.txt
```

**Interpretation:**
- Strong ChIP: Steep rise in cumulative curve
- Weak enrichment: Curve close to diagonal (input-like)

---

## ChIP-seq Analysis Workflow

Complete workflow from BAM files to publication-quality visualizations.

### Step 1: Generate Normalized Coverage Tracks

```bash
# Input control
bamCoverage \
    --bam Input.bam \
    --outFileName Input_coverage.bw \
    --normalizeUsing RPGC \
    --effectiveGenomeSize 2913022398 \
    --binSize 10 \
    --extendReads 200 \
    --samFlagExclude 1024 \
    --numberOfProcessors 8

# ChIP sample
bamCoverage \
    --bam ChIP.bam \
    --outFileName ChIP_coverage.bw \
    --normalizeUsing RPGC \
    --effectiveGenomeSize 2913022398 \
    --binSize 10 \
    --extendReads 200 \
    --samFlagExclude 1024 \
    --numberOfProcessors 8
```

---

### Step 2: Create Log2 Ratio Track

```bash
# Compare ChIP to Input
bamCompare \
    --bamfile1 ChIP.bam \
    --bamfile2 Input.bam \
    --outFileName ChIP_vs_Input_log2ratio.bw \
    --operation log2 \
    --scaleFactorsMethod readCount \
    --binSize 10 \
    --extendReads 200 \
    --samFlagExclude 1024 \
    --numberOfProcessors 8
```

**Result:** Log2 ratio track showing enrichment (positive values) and depletion (negative values).

---

### Step 3: Compute Matrix Around TSS

```bash
# Prepare data for heatmap/profile around transcription start sites
computeMatrix reference-point \
    --referencePoint TSS \
    --scoreFileName ChIP_coverage.bw \
    --regionsFileName genes.bed \
    --beforeRegionStartLength 3000 \
    --afterRegionStartLength 3000 \
    --binSize 10 \
    --sortRegions descend \
    --sortUsing mean \
    --outFileName matrix_TSS.gz \
    --outFileNameMatrix matrix_TSS.tab \
    --numberOfProcessors 8
```

---

### Step 4: Generate Heatmap

```bash
# Create heatmap around TSS
plotHeatmap \
    --matrixFile matrix_TSS.gz \
    --outFileName heatmap_TSS.png \
    --colorMap YlOrRd \
    --whatToShow 'plot, heatmap and colorbar' \
    --yAxisLabel "Genes" \
    --xAxisLabel "Distance from TSS (bp)" \
    --refPointLabel "TSS" \
    --heatmapHeight 15 \
    --kmeans 3
```

---

### Step 5: Generate Profile Plot

```bash
# Create meta-profile around TSS
plotProfile \
    --matrixFile matrix_TSS.gz \
    --outFileName profile_TSS.png \
    --plotType lines \
    --perGroup \
    --colors blue \
    --plotTitle "ChIP-seq signal around TSS" \
    --yAxisLabel "Average signal" \
    --refPointLabel "TSS"
```

---

### Step 6: Enrichment at Peaks

```bash
# Calculate enrichment in peak regions
plotEnrichment \
    --bamfiles Input.bam ChIP.bam \
    --BED peaks.bed \
    --labels Input ChIP \
    --plotFile enrichment.png \
    --outRawCounts enrichment_counts.tab \
    --extendReads 200 \
    --samFlagExclude 1024
```

---

## RNA-seq Coverage Workflow

Generate strand-specific coverage tracks for RNA-seq data.

### Forward Strand

```bash
bamCoverage \
    --bam rnaseq.bam \
    --outFileName forward_coverage.bw \
    --filterRNAstrand forward \
    --normalizeUsing CPM \
    --binSize 1 \
    --numberOfProcessors 8
```

### Reverse Strand

```bash
bamCoverage \
    --bam rnaseq.bam \
    --outFileName reverse_coverage.bw \
    --filterRNAstrand reverse \
    --normalizeUsing CPM \
    --binSize 1 \
    --numberOfProcessors 8
```

**Important:** Do NOT use

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

