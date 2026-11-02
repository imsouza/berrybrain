---
id: sciref-ginkgo-cloud-lab-cfps-expression-purification-quantification
name: "Scientific Ref: Cell Free Protein Expression, Purification, and Quantification"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (ginkgo-cloud-lab): Cell Free Protein Expression, Purification, and Quantification"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "ginkgo cloud lab cfps expression purification quantification"
  - "cell free protein expression, purification, and quantification"
keywords:
  - "ginkgo"
  - "cloud"
  - "lab"
  - "cfps"
  - "expression"
  - "purification"
  - "quantification"
  - "specialized"
  - "scientific"
  - "reference"
  - "cell"
---

# Cell Free Protein Expression, Purification, and Quantification

**URL:** https://cloud.ginkgo.bio/protocols/cfps-expression-purification-quantification
**Service terms:** https://cloud.ginkgo.bio/terms/cfps-expression-purification
**Reviewed:** 2026-09-30; prices and turnaround below are catalog estimates.
**Status:** Ginkgo Certified
**Price:** $159/sample
**Turnaround:** up to 12 days
**Throughput:** Up to 88 constructs per run (1 column reserved for controls), 96-well format

## Overview

End-to-end automated cell-free expression, Strep-tag purification, and quantification of StrepII-tagged proteins, combining A280 yield with LabChip purity/size assessment. CFPS products are purified with magnetic beads on the Agilent Bravo, quantified by A280 on the BMG PHERAstar, then characterized on the Revvity LabChip. The catalog describes an 8-hour expression step while terms describe reactions typically completed within 20 hours; confirm the run-specific incubation rather than treating either as fixed.

## Input

- **DNA Input:** Linear DNA sequence (`.xlsx` template)
- **Tag Orientation:** N-terminal or C-terminal fusion (validated with C-terminal tags; success is protein-dependent)
- **Format:** Up to 88 constructs per run, 1 column of wells for controls

## Output

- **Expression Confirmation:** Verification of the target protein at the expected molecular weight
- **Baseline Titer:** Initial quantitative yield measurement (mg/L)
- **Initial Purity:** Percentage of target protein vs. impurities, delivered with virtual gel images
- **Purified concentration:** A280 eluate concentration in mg/mL with annotated CE-SDS data, QC report, and raw CSV files; do not conflate eluate concentration with reaction titer.

## Automated Workflow

### Phase 1 - CFPS Reaction Setup & Incubation

1. Retrieve plates from storage (HRB TundraStore)
2. Stamp DNA templates into CFPS reaction mix (Agilent Bravo 96)
3. Seal plate (Agilent PlateLoc)
4. Incubate shaking at 29-30 deg C (Thermo Cytomat)

### Phase 2 - Mag Bead Purification & Quantification

1. Dispense reagents and load samples (Biotek / Agilent)
2. Bind sample to beads (Bravo Shaker)
3. Wash beads (Agilent Bravo 96)
4. Elute purified protein (Agilent Bravo 96)
5. Transfer eluate to read plate (Agilent Bravo 96)
6. Read A280 & fluorescence (BMG PHERAstar)

### Phase 3 - LabChip Purity and Size Assessment

1. LabChip assessment (Revvity LabChip)
2. Seal plate (Agilent PlateLoc)
3. Store at 4 deg C (HRB TundraStore)

## Ordering

- **Number of Proteins:** configurable
- **Number of Replicates:** configurable
- **File Upload:** CSV, Excel, FASTA, TXT, PDF, ZIP
- **Additional Details:** free-text field for special requirements

## Use Cases

- Purified yield plus purity/size profiling in one cell-free run
- Characterizing constructs before scale-up production
- Comparing titer and purity across sequence variants

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

