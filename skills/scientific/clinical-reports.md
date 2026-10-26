---
id: sci-clinical-reports
name: "Scientific: clinical-reports"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Creates safety-bounded draft structures and runs local deterministic checks for clinical case, diagnostic, trial, safety, and aggregate research reports. Use only with synthetic, de-identified, or aggregate inputs and verified source-fact manifests; every output requires qualifie"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "clinical reports"
  - "clinico reports"
  - "clinical-reports"
keywords:
  - "clinical"
  - "reports"
  - "clinico"
  - "creates"
  - "safety"
  - "bounded"
  - "draft"
  - "structures"
  - "runs"
---

# Clinical Reports

## Purpose

Prepare **draft reporting structures**, aggregate tables, and review manifests from verified authorized facts. Route each artifact to the correct reporting guidance, preserve provenance, and stop when source support or qualified review is missing.

This skill does not establish legal, regulatory, ethical, journal, accreditation, or institutional compliance. Its scripts check structure and internal consistency only.

## Non-Negotiable Boundary

Never:

- diagnose, recommend treatment, choose or change dosing, triage, or provide return precautions;
- interpret images, specimens, raw laboratory results, symptoms, or other clinical observations;
- invent, infer, normalize, “complete,” or silently reconcile observations, results, dates, units, denominators, causality, expectedness, seriousness, outcomes, or conclusions;
- create an individual case safety report from patient-level narrative or decide reportability;
- sign, attest, approve, file, transmit, submit, amend a source record, or act as a licensed clinician, pathologist, radiologist, laboratorian, safety physician, statistician, privacy officer, attorney, or regulatory professional;
- use real PHI in examples, assets, tests, prompts, logs, or external services;
- send report inputs, manifests, source locators, or clinical content to an external model, image service, API, or another skill.

Public official guidance may be retrieved separately using only public URLs or generic topic queries; include no patient or unpublished study details.

All generated artifacts must remain visibly marked:

> DRAFT — NOT FOR CLINICAL USE, SIGNATURE, FILING, OR SUBMISSION. Populate only from verified authorized source records. Qualified review and sign-off are required.

If the request crosses a boundary, stop the unsafe portion. Offer a blank structured template, a source-fact manifest, or a deterministic structural check. Direct clinical or regulatory decisions to the responsible qualified professional.

## Input Gate

Proceed only when all conditions are true:

1. **Purpose is explicit**: publication draft, diagnostic-report scaffold, trial-results manuscript, protocol reporting review, CSR draft, aggregate safety table, or aggregate research summary.
2. **Data class is allowed**: `synthetic`, `deidentified`, or `aggregate`.
3. **Authority is documented**: the requester is authorized to use the records for the stated purpose.
4. **Local-only handling is feasible**: no upload, remote API, telemetry, or credential is needed.
5. **Minimum necessary is defined**: exclude fields not needed for the artifact.
6. **Provenance exists**: every populated field or claim maps to one or more verified source-fact IDs.
7. **Review owner is identified**: qualified clinical, statistical, safety, privacy, legal, journal, and/or regulatory review as applicable.

These gates depend on documented human assessments. Scripts inspect declarations; they do not independently establish authorization, de-identification, reviewer qualifications, or jurisdictional applicability.

Do not accept raw free-text patient records when a structured source-fact manifest can be supplied. Do not copy direct identifiers into this skill’s templates or scripts.

## Route Before Drafting

| Artifact | Primary route | Important boundary |
|---|---|---|
| Case report for publication | CARE 2013 checklist and 2017 explanation | Publication consent, privacy, journal policy, and clinical accuracy require human verification |
| Radiology draft scaffold | ACR 2025 communication practice parameter plus modality-specific ACR material | A qualified radiologist authors findings/impression and handles nonroutine communication |
| Pathology draft scaffold | Current specimen-specific CAP Cancer Protocol, if applicable | A qualified pathologist selects the protocol/version and authors diagnosis |
| Laboratory draft scaffold | 42 CFR 493.1291 and laboratory policy | The performing laboratory controls results, reference intervals, corrections, and release |
| Randomized-trial results report | CONSORT 2025 plus every applicable current extension | CONSORT is reporting guidance, not a conduct or submission standard |
| Randomized-trial protocol report | SPIRIT 2025 plus applicable extensions | SPIRIT is for protocols, not results or CSRs |
| Clinical Study Report | ICH E3 plus E3 Q&A; consider ICH E6(R3) and regional requirements | E3 is adaptable guidance, not a rigid universal template |
| Pre-approval safety report | ICH E2A; E2B(R3) for electronic ICSR data; applicable regional law/guidance | Qualified sponsor/investigator safety assessment controls reportability and timing |
| Post-approval individual safety report | ICH E2D(R1), E2B(R3), and regional requirements | Do not automate case assessment, coding, or submission |
| Aggregate safety presentation | Protocol/SAP, ICH E3, CONSORT Harms, and applicable FDA/ICH guidance | Aggregate tables never determine individual-case reportability |
| Aggregate research summary | Study-design-specific reporting guideline and source protocol/SAP | State population, estimand, denominator, missingness, and limitations exactly as verified |

Read `references/report_type_routing.md` before choosing a route. Use the dated primary-source ledger in `references/sources.md`; check the live official source when requirements could have changed.

## Safe Drafting Workflow

### 1. Create a source-fact manifest

Use `assets/provenance_manifest_template.json`. Record only local record locators, field paths, verification state, verifier role, verification date, and a SHA-256 value hash. Do not duplicate source content or direct identifiers. Hashes are integrity metadata, not de-identification; do not hash an identifier as a substitute for removing it.

Every draft claim or populated field must cite one or more fact IDs. Unsupported content remains `null` or `missing`; never replace it with plausible text.

### 2. Generate the correct template

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/generate_report_template.py --list
PYTHONDONTWRITEBYTECODE=1 python3 scripts/generate_report_template.py \
  --type case-report \
  --output ./case-report-draft.json
```

The generator copies a fail-closed JSON template. It does not populate clinical content, create directories, overwrite files by default, or certify readiness.

### 3. Populate verified fields only

- Keep `draft_status` unchanged.
- Replace `null` only when a verified fact ID supports the

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

