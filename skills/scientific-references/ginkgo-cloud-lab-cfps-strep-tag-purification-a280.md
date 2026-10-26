---
id: sciref-ginkgo-cloud-lab-cfps-strep-tag-purification-a280
name: "Scientific Ref: Cell Free Protein Expression with Strep-tag Purification and Yield via A280"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (ginkgo-cloud-lab): Cell Free Protein Expression with Strep-tag Purification and Yield via A280"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "ginkgo cloud lab cfps strep tag purification a280"
  - "cell free protein expression with strep-tag purification and yield via a280"
keywords:
  - "ginkgo"
  - "cloud"
  - "lab"
  - "cfps"
  - "strep"
  - "tag"
  - "purification"
  - "a280"
  - "specialized"
  - "scientific"
  - "reference"
  - "cell"
---

# Cell Free Protein Expression with Strep-tag Purification and Yield via A280

**URL:** https://cloud.ginkgo.bio/protocols/cfps-strep-tag-purification-a280
**Service terms:** https://cloud.ginkgo.bio/terms/cfps-strep-tag-a280
**Reviewed:** 2026-09-30; prices and turnaround below are catalog estimates.
**Status:** Ginkgo Certified
**Price:** $149/sample
**Turnaround:** up to 11 days
**Throughput:** Up to 88 constructs per run (1 column reserved for controls), 96-well format

## Overview

End-to-end automated expression and purification of StrepII-tagged proteins in 100 uL CFPS reactions, followed by StreptactinXT magnetic bead purification and A280 quantification. The catalog mentions 20-hour expression and LabChip, but the service terms describe typical 4-16-hour reactions and promise A280 yield/reporting without a LabChip deliverable. Confirm incubation and readout scope in the order; choose the [A280 + LabChip tier](cfps-expression-purification-quantification.md) when purity/size data are required.

## Input

- **DNA Input:** Linear DNA sequence
- **Tag Orientation:** N-terminal or C-terminal Strep-II tag fusion (validated with C-terminal tags; success is protein-dependent)
- **Format:** Up to 88 constructs per run, 1 column of wells for controls

## Output

- **Yield Quantification:** A280 per well, converted to protein concentration (mg/mL) via the protein's molar extinction coefficient
- **Expression Confirmation:** Fluorescence signal relative to controls
- **Assay Quality Metrics:** Per-run quality summary with plate-level controls

## Automated Workflow

### Phase 1 - CFPS Reaction Setup

1. Stamp DNA into CFPS mix (Agilent Bravo 96)
2. Incubate (Cytomat / Inheco)

### Phase 2 - Mag Bead Purification

1. Dispense reagents and load samples (Biotek / Agilent)
2. Bind sample to beads (Bravo Shaker)
3. Wash beads (Agilent Bravo 96)
4. Elute purified protein (Agilent Bravo 96)

### Phase 3 - Detection & Quantification

1. Transfer eluate to read plate (Agilent Bravo 96)
2. Read A280 & fluorescence (BMG PHERAstar)

## Ordering

- **Number of Proteins:** configurable
- **Number of Replicates:** configurable
- **File Upload:** CSV, Excel, FASTA, TXT, PDF, ZIP
- **Additional Details:** free-text field for special requirements

## Use Cases

- Purified-protein yield quantification from cell-free expression
- Screening Strep-tagged constructs before scale-up
- Comparing purified concentration across sequence variants

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

