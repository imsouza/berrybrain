---
id: sciref-clinical-decision-support-sources
name: "Scientific Ref: Authoritative Source Ledger"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (clinical-decision-support): Authoritative Source Ledger"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "clinical decision support sources"
  - "clinico decision support sources"
  - "authoritative source ledger"
keywords:
  - "clinical"
  - "decision"
  - "support"
  - "sources"
  - "clinico"
  - "specialized"
  - "scientific"
  - "reference"
---

# Authoritative Source Ledger

Documentation review: **2026-09-30**.

Reviewed official agencies, standards/guideline hosts, and primary publications using web search/read and fresh `parallel-cli extract` fallbacks. This skill has no runtime service endpoints, authentication, pagination, or external SDK dependencies: its seven CLIs consume local JSON. The optional collection-citation lookup is separate from artifact processing.

Status labels below reflect this review date. Some publisher/Bookshelf pages blocked direct reads; their indexed primary records, official guideline catalogues, or fresh extracts supplied the cited scope. A link is not an endorsement or a substitute for checking a living source before use. Tests use synthetic aggregates and establish helper behavior only, not clinical validity or compliance.

## FDA: CDS and AI-Enabled Devices

- **Clinical Decision Support Software** — FDA final guidance, January 2026; page reissued/content current January 29, 2026. Defines FDA's current interpretation of non-device CDS criteria and device-software boundaries.
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software
- **Marketing Submission Recommendations for a Predetermined Change Control Plan for AI-Enabled Device Software Functions** — FDA final guidance, August 2025. Used for planned modifications, validation methodology, impact assessment, and change-control concepts.
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/marketing-submission-recommendations-predetermined-change-control-plan-artificial-intelligence
- **AI-Enabled Device Software Functions: Lifecycle Management and Marketing Submission Recommendations** — FDA draft guidance, January 2025; explicitly draft/not for implementation on the cutoff date. Used only as clearly labeled draft lifecycle context.
  https://www.fda.gov/regulatory-information/search-fda-guidance-documents/artificial-intelligence-enabled-device-software-functions-lifecycle-management-and-marketing
- **Good Machine Learning Practice for Medical Device Development: Guiding Principles** — FDA page linking the January 2025 IMDRF final principles. Used for lifecycle, representative data, human-AI team, and independent testing themes.
  https://www.fda.gov/medical-devices/artificial-intelligence-enabled-medical-devices/good-machine-learning-practice-medical-device-development-guiding-principles
- **Transparency for Machine Learning-Enabled Medical Devices: Guiding Principles** — FDA/Health Canada/MHRA, June 13, 2024. Used for intended users, limitations, data characterization, uncertainty, human factors, monitoring, and update communication.
  https://www.fda.gov/medical-devices/artificial-intelligence-enabled-medical-devices/transparency-machine-learning-enabled-medical-devices-guiding-principles
- **Artificial Intelligence-Enabled Medical Devices** — current FDA topic page (redirect from the former software-as-a-medical-device route). Used to cross-check the guidance sequence.
  https://www.fda.gov/medical-devices/digital-health-center-excellence/artificial-intelligence-enabled-medical-devices

## ONC / HTI-1

- **HTI-1 Final Rule** — official Federal Register text, January 2024. Used for the legal scope of predictive DSI/source-attribute and intervention-risk-management requirements.
  https://www.federalregister.gov/citation/89-FR-1391
- **HTI-1 Decision Support Interventions Fact Sheet** — ONC, December 2023. Used for the section 170.315(b)(11) overview and predictive-DSI transparency categories.
  https://www.healthit.gov/wp-content/uploads/2023/12/HTI-1_DSI_fact-sheet_508.pdf
- **Requirements for Decision Support Interventions and Predictive Models** — ONC final-rule presentation, January 18, 2024. Used for intended use, population, user, decision role, out-of-scope use, fairness, validation, performance, and maintenance source attributes.
  https://healthit.gov/wp-content/uploads/2024/01/DSI_HTI1-Final-Rule-Presentation_508.pdf
- **HTI-1 Final Rule landing page** — ONC. Used to verify official supporting materials and current resource location.
  https://healthit.gov/regulations/hti-rules/hti-1-final-rule

- **Current DSI certification text** — 45 CFR 170.315(b)(11); predictive DSI source-attribute and risk-management provisions remain in the current text.
  https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-D/part-170/subpart-C/section-170.315
- **HTI-5 proposed rule** — proposal to remove AI model-card requirements; not treated as effective law.
  https://healthit.gov/resources/health-data-technology-and-interoperability-astp-onc-deregulatory-actions-to-unleash-prosperity-hti-5-proposed-rule/

## GRADE

- **GRADE Working Group** — official overview and minimum requirements. Used for outcome-specific certainty, explicit domain judgments, evidence profiles, and Evidence-to-Decision separation.
  https://www.gradeworkinggroup.org/
- **GRADE Book** — official current resource, progressively replacing the prior handbook by 2026. Used as the preferred methodology entry point.
  https://book.gradepro.org/
- **GRADE Handbook** — legacy/current transition resource. Retained for comparison where a GRADE Book chapter is not yet available; verify against the GRADE Book.
  https://gradepro.org/handbook

- **GRADE Book: Imprecision** — current chapter permits human judgments of serious, very serious, and extremely serious imprecision; supports explicit thresholds and uncertainty, not automatic grading.
  https://book.gradepro.org/guideline/imprecision
- **GRADE Book: Dissemination bias** — current terminology broadens the legacy publication-bias assessment to selective availability. The local schema retains `publication_bias` as its field name.
  https://book.gradepro.org/guideline/dissemination-bias

## AI and Clinical-Study Reporting

- **TRIPOD+AI** — Collins et al., BMJ 2024;385:e078378, published April 16, 2024. Reporting of prediction-model development/evaluation using regression or machine learning.
  https://www.bmj.com/content/385/bmj-2023-078378
- **TRIPOD+AI EQUATOR record** — scope, checklist, and related materials.
  https://www.equator-network.org/reporting-guidelines/tripod-statement
- **TRIPOD-LLM** — Gallifant et al., Nature Medicine 2025;31:60-69, published January 8, 2025. Modular reporting guidance for LLM development, tuning, and evaluation; not a quality appraisal tool.
  https://www.nature.com/articles/s41591-024-03425-5
- **CONSORT-AI*

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

