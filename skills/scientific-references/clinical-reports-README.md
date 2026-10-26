---
id: sciref-clinical-reports-readme
name: "Scientific Ref: Clinical Reports References"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (clinical-reports): Clinical Reports References"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "clinical reports readme"
  - "clinico reports readme"
  - "clinical reports references"
keywords:
  - "clinical"
  - "reports"
  - "readme"
  - "clinico"
  - "specialized"
  - "scientific"
  - "reference"
---

# Clinical Reports References

These references support local, deterministic drafting and review. They are not clinical, legal, regulatory, privacy, publication, or accreditation advice and do not establish compliance.

## Safety boundary

- Use only synthetic, de-identified, or aggregate data.
- Populate drafts only from verified authorized source facts.
- Do not diagnose, treat, dose, triage, interpret raw observations, fabricate results, sign, file, or submit.
- Keep data processing local; do not send inputs to external models, APIs, image tools, or other skills. Public guidance can be reviewed separately without patient or unpublished study details.
- Keep every output marked as a draft requiring qualified review.

## File map

| File | Use |
|---|---|
| `report_type_routing.md` | Select the artifact and exact source family before drafting |
| `case_report_guidelines.md` | CARE case-report structure, consent, and publication safeguards |
| `diagnostic_reports_standards.md` | Radiology, pathology, and laboratory field boundaries |
| `clinical_trial_reporting.md` | CONSORT 2025, SPIRIT 2025, ICH E3, and ICH E6(R3) |
| `safety_reporting.md` | ICH E2 and FDA safety-reporting distinctions |
| `privacy_and_deidentification.md` | HHS de-identification methods and process limits |
| `medical_terminology.md` | Versioned terminology and syntax-versus-semantics limits |
| `data_presentation.md` | Aggregate tables, denominators, units, dates, and missingness |
| `professional_review.md` | Ethics, accountability, review, and sign-off |
| `sources.md` | Dated official-source ledger |

## Source handling

`sources.md` records primary or official sources checked on 2026-09-30. Requirements, regional adoption, controlled terminologies, and professional standards can change. Before real-world use, a qualified reviewer must verify the current official source, applicable jurisdiction, institution, sponsor procedure, protocol, statistical analysis plan, and target-journal instructions.

## Terminology

“Required” in these references means required by the cited source within its stated scope, not universally required. “Complete” means structurally present in a manifest, not clinically correct. Script results never authorize use, release, signature, filing, or submission.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

