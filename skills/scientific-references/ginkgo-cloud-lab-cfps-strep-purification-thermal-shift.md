---
id: sciref-ginkgo-cloud-lab-cfps-strep-purification-thermal-shift
name: "Scientific Ref: Protein Expression and Thermal Shift Assay"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (ginkgo-cloud-lab): Protein Expression and Thermal Shift Assay"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "ginkgo cloud lab cfps strep purification thermal shift"
  - "protein expression and thermal shift assay"
keywords:
  - "ginkgo"
  - "cloud"
  - "lab"
  - "cfps"
  - "strep"
  - "purification"
  - "thermal"
  - "shift"
  - "specialized"
  - "scientific"
  - "reference"
  - "protein"
---

# Protein Expression and Thermal Shift Assay

**URL:** https://cloud.ginkgo.bio/protocols/cfps-strep-purification-thermal-shift
**Service terms:** https://cloud.ginkgo.bio/terms/cfps-strep-purification-thermal-shift
**Reviewed:** 2026-09-30; prices and turnaround below are catalog estimates.
**Status:** Ginkgo Certified
**Price:** $159/sample
**Turnaround:** up to 12 days
**Throughput:** Up to 88 constructs per run (1 column reserved for controls)

## Overview

Combines cell-free protein expression, Strep-tag magnetic bead purification, and a Protein Thermal Shift Assay using SYPRO Orange into a single end-to-end workflow. Starting from a DNA template plate, the protocol expresses protein in a CFPS reaction, purifies the tagged product via Strep-Tactin magnetic beads, and characterizes thermal unfolding of the purified protein by extrinsic fluorimetry.

SYPRO Orange fluorescence tracks exposure of hydrophobic regions during a temperature ramp. The service reports **Tonset** and up to three apparent transitions (**TM1, TM2, TM3**) where callable. Compare variants under matched conditions and review thermograms and QC flags; multiple peaks alone do not establish which structural domains unfolded. This assay supports stability ranking, not binding-affinity measurement.

## Input

- **DNA Input:** Linear DNA sequence
- **Tag Orientation:** N-terminal or C-terminal fusion (validated with C-terminal tags; success is protein-dependent)
- **Format:** Up to 88 constructs per run, 1 column of wells for controls

## Output

- **Cell-Free Reaction:** 100 uL E. coli-based CFPS reaction per sample with process controls
- **Yield Quantification:** Absolute protein yield in eluate via A280, converted to mg/mL
- **Thermal Stability Measurement:** SYPRO Orange thermal shift in triplicate on purified eluate, reporting Tonset and up to three melting transitions (TM1, TM2, TM3) in deg C, where applicable
- **Reporting & Data:** PDF report with yield data, thermogram plots, called TM values, reaction condition metadata, and QC status

## Automated Workflow

### Phase 1 - CFPS Reaction Setup

1. Stamp DNA into CFPS mix (Agilent Bravo 96)
2. Incubate (Cytomat / Inheco)

### Phase 2 - Mag Bead Purification

1. Dispense reagents and load samples (Biotek / Agilent)
2. Bind sample to beads (Bravo Shaker)
3. Wash beads (Agilent Bravo 96)
4. Elute purified protein (Agilent Bravo 96)

### Phase 3 - Assay Plate Preparation

1. Transfer 1 uL SYPRO dye (Echo 525)
2. Stamp purified protein (Agilent Bravo 96)

### Phase 4 - Plate Sealing & Thermal Ramp

1. Seal plate (Agilent PlateLoc)
2. Execute melt-curve protocol (Bio-Rad CFX Opus thermal cycler)

## Ordering

- **Number of Proteins:** configurable
- **Number of Replicates:** configurable
- **File Upload:** CSV, Excel, FASTA, TXT, PDF, ZIP
- **Additional Details:** free-text field for special requirements

## Use Cases

- Ranking protein variants by thermal stability (Tm/Tonset) directly from DNA
- Developability screening and stability-liability flagging
- Comparing domain unfolding across candidate libraries

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

