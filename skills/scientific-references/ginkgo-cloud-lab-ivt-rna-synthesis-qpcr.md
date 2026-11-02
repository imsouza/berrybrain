---
id: sciref-ginkgo-cloud-lab-ivt-rna-synthesis-qpcr
name: "Scientific Ref: IVT mRNA/circRNA Synthesis, SPRI Purification & qPCR Quantification"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (ginkgo-cloud-lab): IVT mRNA/circRNA Synthesis, SPRI Purification & qPCR Quantification"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "ginkgo cloud lab ivt rna synthesis qpcr"
  - "ivt mrna/circrna synthesis, spri purification & qpcr quantification"
keywords:
  - "ginkgo"
  - "cloud"
  - "lab"
  - "ivt"
  - "rna"
  - "synthesis"
  - "qpcr"
  - "specialized"
  - "scientific"
  - "reference"
  - "mrna"
---

# IVT mRNA/circRNA Synthesis, SPRI Purification & qPCR Quantification

**URL:** https://cloud.ginkgo.bio/protocols/ivt-rna-synthesis-qpcr
**Service terms:** https://cloud.ginkgo.bio/terms/ivt-rna-synthesis-qpcr
**Reviewed:** 2026-09-30; prices and turnaround below are catalog estimates.
**Status:** Ginkgo Certified
**Price:** $99/sample
**Turnaround:** up to 12 business days (extended: up to 17 business days for longer or clonal DNA constructs)
**Throughput:** 384-well format throughout

## Overview

End-to-end automated RNA production and quantification pipeline ("data in / data out"). Submit DNA sequences via CSV; Ginkgo sources DNA synthesis from commercial providers (e.g., Twist), then runs PCR template prep, in vitro transcription (linear mRNA or circRNA), SPRI bead purification, and qPCR quantification.

**Note:** The circRNA pipeline is limited to Permuted Intron-Exon (PIE) with group I introns.
Other RNA classes such as guide RNA, siRNA, and tRNA are outside this service scope.

## Input

- **DNA Input:** Sequences submitted via the CSV template (select linear mRNA or circRNA mode)

## Output

- Purified RNA samples in 384-well format with qPCR quantification readout
- Spectrophotometric concentration and purity ratios (A260/A280, A260/A230) are available without a customer calibration standard
- RT-qPCR is relative by default; absolute **qPCR** quantification requires a customer-supplied standard with identity and concentration
- RNA integrity/fragmentation (including RIN-type assessment) is not measured

The turnaround clock begins at order acceptance after usable input is received;
commercial DNA synthesis lead time and shipping are excluded by the service terms.

## Automated Workflow

### Phase 1 - PCR Template Preparation

1. Transfer primers (Labcyte Echo)
2. Transfer templates (Labcyte Echo)
3. Stamp mastermix (Bravo 384)
4. PCR thermocycle (ATC384)

### Phase 2 - In Vitro Transcription

1. Stamp mastermix (Bravo 384)
2. IVT incubation (ATC384)
3. Stamp DNase mix (Bravo 384)
4. Circularization for circRNA (ATC384)

### Phase 3 - SPRI RNA Purification

1. Load decks with reagents (Bravo 384)
2. Magnetic bead purification (Bravo 384)
3. Unload decks (Bravo 384)

### Phase 4 - Quantify RNAs

1. Stamp RNAs (Bravo 384)
2. RNA yield / purity quantification (Lunatic)

### Phase 5 - Circularization Quantification

1. Echo qPCR setup (Labcyte Echo)
2. Stamp mastermix (Bravo 384)
3. Run RT-qPCR (CFX Opus)

## Ordering

- **Samples:** configurable
- **File Upload:** CSV, Excel, FASTA, TXT, PDF, ZIP (DNA sequences via CSV template)
- **Additional Details:** free-text field for special requirements

## Use Cases

- mRNA production for screening and assay development
- circRNA synthesis (PIE / group I intron designs)
- High-throughput RNA generation with purity/yield readouts

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

