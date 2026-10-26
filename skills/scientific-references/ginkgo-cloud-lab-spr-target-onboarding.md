---
id: sciref-ginkgo-cloud-lab-spr-target-onboarding
name: "Scientific Ref: SPR Target Onboarding"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (ginkgo-cloud-lab): SPR Target Onboarding"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "ginkgo cloud lab spr target onboarding"
  - "spr target onboarding"
keywords:
  - "ginkgo"
  - "cloud"
  - "lab"
  - "spr"
  - "target"
  - "onboarding"
  - "specialized"
  - "scientific"
  - "reference"
---

# SPR Target Onboarding

**URL:** https://cloud.ginkgo.bio/protocols/spr-target-onboarding
**Service terms:** https://cloud.ginkgo.bio/terms/spr-target-onboarding
**Reviewed:** 2026-09-30; prices and turnaround below are catalog estimates.
**Status:** Beta
**Price:** $1,399/target
**Turnaround:** up to 4 weeks

> **Launch offer:** Terms restrict the credit to successful qualification and the first binding run against the same target lot; it expires 12 months after qualification. Confirm availability and the accepted order's terms.

## Overview

Qualifies a target on the Cloud Lab SPR (surface plasmon resonance) catalog for kinetic profiling against your binder candidates. Ginkgo procures the target and reference binder, selects capture chemistry, validates immobilization and surface activity on the Nicoya Alto, scouts regeneration conditions, and releases a qualified method to the catalog. Once onboarded, the target can be used in downstream kinetics/binding assay runs.

Onboarding does not screen the customer's binder library. Confirm the target's live
qualification status and availability of the separate binding service; a queued or
in-progress target is not qualified. The current launch scope uses commercial
target/reference-binder standards and starts downstream screening with minibinders.

## Input

(Use the provided `.xlsx` template; list each target on its own row for multi-target orders.)

- Target catalog number (vendor + SKU)
- Reference binder catalog number (vendor + SKU)
- Target metadata (MW, oligomeric state, sensitivities)
- Buffer preferences, if any
- Usable capture handle or amine-coupling requirement; reference-binder affinity if known
- Use approved vendors/SKUs or request vendor qualification; customer-supplied target/binder material is outside the launch scope

## Output

- Validated capture method and surface conditions
- Recommended assay parameters for downstream kinetics runs
- Qualification report with pass/fail call and remediation if needed

## Automated Workflow

### Phase 1 - Intake & Procurement

1. Catalog number intake (Nebula Core)
2. Vendor procurement (Nebula Core)

### Phase 2 - Surface Setup & Validation

1. Capture chemistry selection (project scientist)
2. Test immobilization (Nicoya Alto)
3. Surface activity check (Nicoya Alto)
4. Regeneration scouting (Nicoya Alto)

### Phase 3 - Qualification & Release

1. Qualification record (LIMS)
2. Release to catalog (project scientist)

## Ordering

- **Number of Targets:** configurable ($1,399/target)
- **File Upload:** `.xlsx` only (use the provided template)
- **Additional Details:** free-text field for special requirements

## Use Cases

- Preparing a target for SPR kinetic profiling of binder candidates
- Establishing capture/regeneration conditions before binding campaigns
- Onboarding a target ahead of antibody/minibinder affinity screening

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

