---
id: sciref-clinical-reports-professional-review
name: "Scientific Ref: Professional, Ethical, and Human Review"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (clinical-reports): Professional, Ethical, and Human Review"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "clinical reports professional review"
  - "clinico reports professional revisao"
  - "professional, ethical, and human review"
keywords:
  - "clinical"
  - "reports"
  - "professional"
  - "review"
  - "clinico"
  - "revisao"
  - "specialized"
  - "scientific"
  - "reference"
---

# Professional, Ethical, and Human Review

## Accountability

Automation may organize verified facts but cannot assume professional accountability. A named, qualified human must review each domain and take responsibility in the authorized system.

The ICMJE Recommendations, updated January 2026, retain four authorship criteria: substantive contribution; drafting or critical review; final approval; and accountability for accuracy and integrity. Writing assistance alone does not confer authorship. An AI system cannot be an author or approve a manuscript. Under the January 2026 recommendations, disclose the tool and purpose of AI assistance in the appropriate manuscript section and at submission according to the journal’s policy; accountable humans verify accuracy, attribution, and confidentiality. A skill/software citation does not replace that disclosure.

## Research ethics

The World Medical Association states that the **2024 Declaration of Helsinki** is the current official version. It applies to medical research involving human participants, including identifiable material or data, and emphasizes:

- participant rights and interests over research goals;
- privacy and confidentiality;
- scientific validity and a documented protocol;
- independent research-ethics review;
- informed consent;
- transparency and reporting.

This skill neither performs ethics review nor determines whether an activity is research, exempt, or authorized.

## Clinical-record confidentiality

AMA Code of Medical Ethics Opinion 3.3.2 states that information recorded in patient care is confidential regardless of form and identifies access restriction, audit capability, security/integrity, retrieval, sharing, third-party access, and disposition as responsibilities for electronic records.

Use institution-controlled systems for real clinical records. Local draft manifests should contain source locators and hashes rather than PHI.

## Required reviewers by artifact

| Domain | Reviewer responsibility |
|---|---|
| Clinical case facts | Qualified clinician verifies facts, uncertainty, chronology, and interpretation |
| Radiology | Qualified radiologist authors findings/impression and communication status |
| Pathology | Qualified pathologist selects protocol/version and authors diagnosis |
| Laboratory | Authorized laboratory professional verifies released result, method, status, and corrections |
| Statistics | Qualified statistician verifies analysis set, estimand, method, denominator, missingness, and output |
| Safety | Qualified safety professional verifies coding, seriousness, severity, causality, expectedness, and reportability |
| Privacy/legal | Authorized reviewer verifies data use, consent/authorization, disclosure, de-identification method, and jurisdiction |
| Regulatory | Qualified professional verifies adopted guidance, regional requirements, format, and submission process |
| Publication | All accountable authors verify content and current journal instructions |

## Review record

Record:

- reviewer role, not a fabricated name;
- scope reviewed;
- source version and data cut;
- unresolved conflicts and limitations;
- review date;
- decision in the authorized workflow;
- reference to the real sign-off record.

Do not place a signature, license number, direct contact detail, or copied approval document in a synthetic asset.

## Prohibited claims

Never state that a script or checklist proves:

- clinical correctness;
- HIPAA compliance or de-identification;
- GCP compliance;
- CARE, CONSORT, SPIRIT, ICH, ACR, CAP, or CLIA compliance;
- ethics approval or informed consent;
- regulatory reportability;
- readiness for signature, filing, publication, or submission.

Permitted script language is limited to structural findings such as `BLOCKED`, `STRUCTURE_COMPLETE_REVIEW_REQUIRED`, or `PROCESS_DOCUMENTED_REVIEW_REQUIRED`.

## Corrections and conflicts

- Never overwrite a source fact.
- Keep original and corrected versions linked.
- Expose conflicting sources and stop dependent claims.
- Require the responsible reviewer to resolve conflicts in the authorized system.
- Re-run structural and consistency checks after any correction.

No local script signs, timestamps an approval, files, transmits, or submits an artifact.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

