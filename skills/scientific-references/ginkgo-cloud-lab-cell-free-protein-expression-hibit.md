---
id: sciref-ginkgo-cloud-lab-cell-free-protein-expression-hibit
name: "Scientific Ref: Cell Free Protein Expression with HiBiT Quantification"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (ginkgo-cloud-lab): Cell Free Protein Expression with HiBiT Quantification"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "ginkgo cloud lab cell free protein expression hibit"
  - "cell free protein expression with hibit quantification"
keywords:
  - "ginkgo"
  - "cloud"
  - "lab"
  - "cell"
  - "free"
  - "protein"
  - "expression"
  - "hibit"
  - "specialized"
  - "scientific"
  - "reference"
---

# Cell Free Protein Expression with HiBiT Quantification

**URL:** https://cloud.ginkgo.bio/protocols/cell-free-protein-expression-hibit
**Service terms:** https://cloud.ginkgo.bio/terms/cfps-hibit
**Reviewed:** 2026-09-30; prices and turnaround below are catalog estimates.
**Status:** Ginkgo Certified
**Price:** $39/sample
**Turnaround:** up to 11 days
**Throughput:** 384-well format

## Overview

Fastest path from a sequence to a protein yield metric. Uses a proprietary reconstituted E. coli transcription-translation (CFPS) system; reactions complete in 4-16 hours and can yield up to 3 mg/mL of target protein. Expressed proteins are quantified directly from the crude reaction mixture (no purification) using the Promega Nano-Glo HiBiT Lytic Detection System. Designed for early-stage screening, novel construct evaluation, and rapid, data-driven triage before committing to optimization or purification.

## Input

- **Sequence input:** The protocol page links a CFPS `.xlsx` template for linear DNA; service terms describe protein or DNA in CSV. Confirm the downloaded schema and synthesis format (linear DNA or clonal plasmid).
- **HiBiT Tag Orientation:** N-terminal or C-terminal fusion
- **Linker Sequence:** If unspecified, Ginkgo uses a standard GGGS linker

## Output

- **Expression Detection:** Confirmation of target protein expression via background-subtracted luminescence (bcRLU) relative to controls
- **Relative Yield Quantification:** Target protein concentration (reported in nM), interpolated from a standard curve
- **Assay Quality Metrics:** Z-prime scores, replicate CV%, and matrix-effect controls

## Automated Workflow

### Phase 1 - CFPS Reaction Setup & Incubation

1. Stamp DNA templates into CFPS reaction mix
2. Seal and incubate (4-16 h)

### Phase 2 - Detection Prep

1. Spin down plates
2. Transfer samples and standards (Echo)
3. Dispense PBS/buffer and prepare the HiBiT assay plate (MultiFlo / Bravo 384)

### Phase 3 - Detection & Quantification

1. Incubate (ambistore)
2. Luminescence read (BMG PHERAstar)
3. Seal & store (Agilent PlateLoc)

## Ordering

- **Number of Proteins:** configurable
- **Number of Replicates:** configurable
- **File Upload:** CSV, Excel, FASTA, TXT, PDF, ZIP
- **Additional Details:** free-text field for special requirements

## Use Cases

- High-throughput expressibility screening without purification
- Rapid relative-yield comparison across construct variants
- Early triage before A280/LabChip purification tiers

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

