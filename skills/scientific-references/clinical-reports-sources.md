---
id: sciref-clinical-reports-sources
name: "Scientific Ref: Official Source Ledger"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (clinical-reports): Official Source Ledger"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "clinical reports sources"
  - "clinico reports sources"
  - "official source ledger"
keywords:
  - "clinical"
  - "reports"
  - "sources"
  - "clinico"
  - "specialized"
  - "scientific"
  - "reference"
  - "official"
---

# Official Source Ledger

**Research cutoff and access date:** 2026-09-30
**Method:** live official-page/PDF review, with public-page extraction for ACR and BMJ when direct access was blocked. Local scripts, templates, and synthetic tests were audited separately; this skill has no network API client, authentication, pagination, or submission implementation to test.
**Use:** source routing and version awareness only. Always verify the live source, jurisdictional adoption, and local requirements before real-world use.

## Case reports

- **CARE Case Report Guidelines — home and current toolkit.** Identifies the 2013 checklist and 2017 explanation. <https://www.care-statement.org/>
- **2013 CARE Checklist.** Thirteen main reporting items. <https://www.care-statement.org/checklist>
- **CARE publications.** Primary 2013 statement and 2017 explanation/elaboration references. <https://www.care-statement.org/publications>

## Randomized-trial protocols and results

- **SPIRIT–CONSORT official site.** SPIRIT 2025: 34-item protocol checklist and figure. CONSORT 2025: 30-item results checklist and flow diagram. <https://www.consort-spirit.org/>
- **CONSORT/SPIRIT extension catalogue.** Current design, data, intervention, and population extensions; catalogue notes which base statement each extension used. <https://www.consort-spirit.org/extensions>
- **CONSORT 2025 primary statement.** Published 2025-04-14. <https://www.bmj.com/content/389/bmj-2024-081123>
- **SPIRIT 2025 primary statement.** Published 2025-04-28; states that SPIRIT 2025 supersedes SPIRIT 2013. <https://www.bmj.com/content/389/bmj-2024-081477>
- **SPIRIT 2025 explanation and elaboration.** Published 2025-04-28. <https://www.bmj.com/content/389/bmj-2024-081660>

## ICH clinical-study and GCP guidance

- **ICH E3 — Structure and Content of Clinical Study Reports.** Step 4, 1995-11-30. <https://database.ich.org/sites/default/files/E3_Guideline.pdf>
- **ICH E3 Questions & Answers (R1).** Current version dated 2012-07-06; clarifies that E3 is adaptable guidance, not a rigid template. <https://database.ich.org/sites/default/files/E3_Q%26As_R1_Q%26As.pdf>
- **ICH E6(R3) consolidated final guideline.** Principles, Annex 1, and Annex 2; adopted 2026-06-16. <https://database.ich.org/sites/default/files/ICH%20E6%28R3%29_Step4_FinalConsolidatedGuideline_2026_0616_.pdf>
- **ICH E6(R3) Annex 2 final.** Adopted 2026-06-03. <https://database.ich.org/sites/default/files/ICH_E6%28R3%29_Annex%202_Guideline_Step%204_2026_0603_0.pdf>
- **FDA ICH guidance index.** General US ICH entry point; its E6 text still describes R2, so it is not sufficient evidence of current regional E6 adoption. <https://www.fda.gov/science-research/clinical-trials-and-human-subject-protection/ich-guidance-documents>
- **FDA E6(R3) Good Clinical Practice.** Dedicated final-guidance page, September 2025; review the actual regional document and Annex 2 status separately from the ICH consolidated version. <https://www.fda.gov/regulatory-information/search-fda-guidance-documents/e6r3-good-clinical-practice-gcp>

## Safety reporting

- **ICH E2A — Clinical Safety Data Management: Definitions and Standards for Expedited Reporting.** Step 4, 1994-10-27. <https://database.ich.org/sites/default/files/E2A_Guideline.pdf>
- **ICH E2B(R3) ICSR specification and related files.** Catalogue entry point for implementation guide, Q&As, and code lists; current file list could not be extracted during this review. <https://www.ich.org/page/e2br3-individual-case-safety-report-icsr-specification-and-related-files>
- **FDA E2B(R3) implementation guide.** Final April 2022 adoption page with ICH message specification, XML schemas, examples, and FDA regional additions. No message generation or transmission is performed here. <https://www.fda.gov/regulatory-information/search-fda-guidance-documents/e2br3-electronic-transmission-individual-case-safety-reports-implementation-guide-data-elements-and>
- **ICH E2C(R2) PBRER.** Final Step 4 text corrected 2012-12-17; periodic benefit-risk aggregate reporting, distinct from ICSR message structure. <https://database.ich.org/sites/default/files/E2C_R2_Guideline.pdf>
- **ICH E2D(R1) — Post-Approval Safety Data: Definitions and Standards for Management and Reporting of Individual Case Safety Reports.** Adopted 2025-09-15. <https://database.ich.org/sites/default/files/ICH_E2D%28R1%29_Step4_FinalGuideline_2025_0819.pdf>
- **21 CFR 312.32 — IND safety reporting.** Current eCFR text; verify current effective text and official annual CFR. <https://www.ecfr.gov/current/title-21/chapter-I/subchapter-D/part-312/subpart-B/section-312.32>
- **FDA IND Application Reporting: IND Safety Reports.** Checked 2026-09-30; includes AEMS/E2B(R3) electronic route effective 2026-04-01 within stated scope. <https://www.fda.gov/drugs/investigational-new-drug-application-ind/ind-application-reporting-ind-safety-reports>
- **FDA AEMS Electronic Submissions.** Postmarketing E2B(R2) transition ends 2026-09-30; ESG NextGen ICSRs require E2B(R3) from 2026-10-01. SRP users need no action for this transition. <https://www.fda.gov/drugs/fda-adverse-event-monitoring-system-aems/fda-adverse-event-monitoring-system-aems-electronic-submissions>
- **FDA Sponsor Responsibilities — Safety Reporting Requirements and Safety Assessment for IND and BA/BE Studies.** Final guidance, December 2025. <https://www.fda.gov/regulatory-information/search-fda-guidance-documents/sponsor-responsibilities-safety-reporting-requirements-and-safety-assessment-ind-and>
- **FDA Investigator Responsibilities — Safety Reporting for Investigational Drugs and Devices.** Final guidance, December 2025. <https://www.fda.gov/regulatory-information/search-fda-guidance-documents/investigator-responsibilities-safety-reporting-investigational-drugs-and-devices>
- **FDA Postmarketing Adverse Event Reporting Compliance Program.** Current inspection-program scope, distinct from individual event reportability. <https://www.fda.gov/drugs/surveillance-post-drug-approval-activities/postmarketing-adverse-event-reporting-compliance-program>

## Privacy and de-identification

- **HHS Guidance Regarding Methods for De-identification of PHI.** Safe Harbor and Expert Determination under 45 CFR 164.514(b); including the limits on identifier-derived codes; public content rechecked. <https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html>
- **HHS Minimum Necessary Requirement.** 45 CFR 164.502(b) and 164.514(d), 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

