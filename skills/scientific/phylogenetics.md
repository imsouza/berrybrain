---
id: sci-phylogenetics
name: "Scientific: phylogenetics"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Builds and analyzes phylogenetic trees using MAFFT multiple sequence alignment, IQ-TREE maximum likelihood with ModelFinder and branch support, and FastTree approximate inference. Uses ETE3 for tree summaries and visualization. Applies to homologous nucleotide or protein sequence"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "phylogenetics"
keywords:
  - "phylogenetics"
  - "builds"
  - "analyzes"
  - "phylogenetic"
  - "trees"
  - "mafft"
  - "multiple"
---

# Phylogenetics

## When to use

Use this workflow for an alignment of homologous loci or proteins, a gene tree,
branch support, and an interpretable tree figure. Multi-locus partitioning,
concordance factors, ancestral states and dating are covered in
[IQ-TREE reference](references/iqtree_inference.md).

A gene tree does not establish a species tree, transmission direction, or horizontal
transfer by itself. Sampling dates alone do not justify a molecular clock.

## Versions and installation

Reviewed against current official documentation on 2026-10-01. The executed
smoke workflow used MAFFT **7.526**, IQ-TREE **3.1.4**, FastTree **2.2.0** and
ETE3 **3.1.3** on Python 3.12. ETE3 remains deliberate for this helper; ETE4 is a
separate API and is not a drop-in replacement. ETE3 imports `cgi`, removed in
Python 3.13. The native executables are not Python packages.

Illustrative installation commands; verify executable versions after installation:

```bash
conda create -n phylo -c conda-forge -c bioconda mafft iqtree fasttree trimal
conda activate phylo
uv venv --python 3.12 .venv-phylo
uv pip install --python .venv-phylo/bin/python ete3==3.1.3 numpy six
# Optional rendering backend; it can require a working Qt platform plugin.
uv pip install --python .venv-phylo/bin/python PyQt5
```

The helper defaults to `iqtree3` and `FastTree`; use `--iqtree-bin iqtree2` for an
existing IQ-TREE 2 installation, or `--fasttree-bin fasttree` if that is the
installed name. Version 2 compatibility is source-checked, not runtime-tested
in this refresh. All analyses are local; this skill invokes no HTTP API or remote
inference endpoint.

## Workflow

### 1. Establish the biological input

- Select homologs with appropriate taxon coverage; investigate paralogs,
  contamination and recombination before assuming one history describes all sites.
- Use unique, whitespace-free FASTA IDs and keep a separate sample metadata table.
  The helper rejects empty/all-missing records and Newick punctuation in IDs.
- Specify `--type nt` or `--type aa`. The helper sends `-st DNA` or `-st AA` to
  IQ-TREE and selects nucleotide/protein FastTree flags explicitly.
- Coding DNA needs codon-aware alignment if using a codon model. Ordinary MAFFT
  nucleotide alignment does not preserve reading frames automatically.
- Keep the original sequences, accession versions, filters, alignment and exact
  commands. Inspect alignment lengths, gaps, composition and taxon identities.

### 2. Align and inspect

These MAFFT commands were exercised on small synthetic FASTA data:

```bash
mafft --auto --thread 1 --inputorder sequences.fasta > aligned.fasta
# L-INS-i: locally alignable homologs, typically small datasets.
mafft --localpair --maxiterate 1000 --thread 1 --inputorder sequences.fasta > linsi.fasta
# E-INS-i: homologs with large internal gaps.
mafft --genafpair --maxiterate 1000 --thread 1 --inputorder sequences.fasta > einsi.fasta
# FFT-NS-i (two refinement cycles), then FFT-NS-2 (progressive).
mafft --retree 2 --maxiterate 2 --thread 1 --inputorder sequences.fasta > fftnsi.fasta
mafft --retree 2 --maxiterate 0 --thread 1 --inputorder sequences.fasta > fftns.fasta
```

`auto` delegates the choice to MAFFT. Sequence count alone is not an accuracy
criterion. Single-thread runs simplify reproducibility; MAFFT iterative refinement
with multiple threads can produce different results between runs.

Trimming is optional and must be justified by alignment quality, not assumed to
improve every tree. The following trimAl command is documentation-checked and
illustrative; trimAl was not installed for this review:

```bash
trimal -in aligned.fasta -out trimmed.fasta -automated1 -fasta
```

Record retained columns/taxa and compare sensitivity to trimming. A failed trim
must stop the trimming step; do not silently copy the untrimmed input under a
“trimmed” filename. The bundled helper does not trim automatically.

### 3. Infer a tree

Use the maintained helper instead of recreating subprocess wrappers. From the
skill directory, with the executable names on `PATH`:

```bash
python scripts/phylogenetic_analysis.py sequences.fasta --type nt --threads 1 \
  --bootstrap 1000 --seed 42 --output-dir results --no-visualization
# Use a reviewed alignment (including any explicit trimming) without realigning.
python scripts/phylogenetic_analysis.py aligned.fasta --aligned --type nt \
  --threads 1 --output-dir reviewed --no-visualization
# Protein FastTree alternative; --threads applies to MAFFT/IQ-TREE, not FastTree.
python scripts/phylogenetic_analysis.py proteins.fasta --type aa --fasttree \
  --threads 1 --output-dir fast_protein --no-visualization
```

The standard IQ-TREE command uses `-m MFP` (ModelFinder including FreeRate
models), `-B 1000` (UFBoot) and `--alrt 1000`. `-m TEST` remains supported but
searches a narrower model set. Use `--model` for a scientifically justified fixed
model. IQ-TREE checkpoints are preserved; `--redo` explicitly restarts and
replaces results. Use a new output prefix when data or model assumptions change.

FastTree uses `-nt -gtr -gamma` for DNA and `-lg -gamma` for proteins. Its search
uses the CAT approximation before Gamma20 rescaling; it is not a full Gamma-model
ML search. JTT is FastTree's protein default (no `-jtt` flag); nucleotide JC is
selected by `-nt` without `-gtr`. FastTree defaults to **SH-like local support**
in the **0–1** range, not UFBoot percentages. Use workload-based benchmarking,
not a universal taxon threshold, to decide between inference tools.

### 4. Interpret support, rooting and outputs

Read `.iqtree` and `.log`, not only the image. In the default combined test,
IQ-TREE writes slash-delimited SH-aLRT/UFBoot labels; verify their order in the
report. UFBoot >=95 and SH-aLRT >=80 are common screening thresholds, not proof
of correctness or posterior probabilities. Do not apply a standard-bootstrap
70% rule to UFBoot. Model misspecification, alignment error and sampling can
produce strongly supported wrong branches; consider `-bnni` when assessing
model violations and UFBoot overestimation.

Reversible substitution models do not infer the evolutionary root. The helper
preserves the supplied tree orientation unless an explicit `--outgroup` or
`--midpoint` display choice is made. Select outgroups biologically; midpoint
rooting assumes sufficiently clock-like path lengths and is only a heuristic.
`--outgroup` passes one taxon to IQ-TREE and verifies that it exists. Display
rerooting preserves s

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

