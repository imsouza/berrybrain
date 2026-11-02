---
id: sciref-iso-standards-readiness-source-ledger
name: "Scientific Ref: Official Source Ledger"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (iso-standards-readiness): Official Source Ledger"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "iso standards readiness source ledger"
  - "official source ledger"
keywords:
  - "iso"
  - "standards"
  - "readiness"
  - "source"
  - "ledger"
  - "specialized"
  - "scientific"
  - "reference"
  - "official"
---

# Official Source Ledger

**Research baseline:** 2026-10-01. This refresh directly read official ISO catalogue
metadata, FDA/eCFR, MDSAP, Global ACI, CMS/CAP, and Commission sources. It replaces
the July 2026 baseline. Retrieval exceptions are recorded below; search-indexed
metadata is not a controlled requirements source.

**Purpose:** version baseline for evidence preparation; not an applicability decision,
certification or accreditation criteria, or a substitute for controlled source copies.
No proprietary standard text is reproduced. Recheck time-sensitive sources before
operational use, and obtain authorized standards and scheme documents.

## ISO standards and copyright

### ISO 13485:2016

- Official page:
  [ISO 13485:2016](https://www.iso.org/standard/59752.html)
- Verified metadata: Edition 3; publication date 2016-03; stage 90.93
  (confirmed); confirmation recorded 2025-10-31.
- Use: identifies the current international edition and lifecycle status.
- Limitation: the ISO page is not the complete normative text. Obtain an authorized
  copy.

### EN ISO 13485:2016/A11:2021 distinction

- Current Commission index:
  [Harmonised standards](https://health.ec.europa.eu/medical-devices-topics-interest/harmonised-standards_en)
- Current MDR decision:
  [Consolidated Decision (EU) 2021/1182, 2026-06-17](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02021D1182-20260617)
- IVDR amendment decision:
  [Decision (EU) 2022/729](https://eur-lex.europa.eu/eli/dec_impl/2022/729/oj)
- Commission summary lists for both MDR and IVDR, generated 2026-06-17, directly
  confirmed EN ISO 13485:2016, AC:2018, and A11:2021. A11:2021 is a European EN amendment, not an ISO international
  “Amendment 1:2021.”
- Evidence: [MDR summary source page](https://single-market-economy.ec.europa.eu/single-market/goods/european-standards/harmonised-standards/medical-devices_en)
  and [IVDR summary source page](https://single-market-economy.ec.europa.eu/single-market/goods/european-standards/harmonised-standards/iv-diagnostic-medical-devices_en).
  The linked PDF contents were read; their filenames retain older dates. Direct
  EUR-Lex decision retrieval returned an access challenge. Commission summaries have
  no independent legal effect.
- Limitation: verify the latest OJEU citation and the exact requirements for which
  presumption of conformity is claimed; use of harmonised standards is not a blanket
  product-conformity decision.

### ISO 14971:2019 and European A11

- Official page:
  [ISO 14971:2019](https://www.iso.org/standard/72704.html)
- Verified metadata: Edition 3; publication 2019-12; stage 90.93, confirmed 2025-03-07.
- EU source:
  [Decision (EU) 2022/757](https://eur-lex.europa.eu/eli/dec_impl/2022/757/oj/eng)
- Verified fact: the Commission MDR and IVDR summary PDFs cited above both list
  EN ISO 14971:2019/A11:2021. A11 is European; it does not change the
  international ISO 14971 normative part.
- Limitation: risk-management evidence remains product- and jurisdiction-specific.

### ISO/TR 24971:2020

- Official page:
  [ISO/TR 24971:2020](https://www.iso.org/standard/74437.html)
- Verified catalogue metadata: Edition 2, published 2020-06; remains the published
  guidance companion to ISO 14971:2019. Stage 90.92 (to be revised), 2026-07-06.
- Proposed successor: [ISO/AWI TS 24971-1](https://www.iso.org/standard/94297.html),
  stage 20.00 (new project registered). This is an approved work item under
  development, not a published replacement, amendment, or new normative requirement.
- Verified status: a Technical Report. Its guidance is informative, not normative, and
  conformity is claimed to ISO 14971, never to ISO/TR 24971.
- Limitation: a TR cannot be used to relax or reinterpret a normative requirement.
  Record which guidance the organization adopted and why.

### ISO/IEC 17025:2017

- Official page:
  [ISO/IEC 17025:2017](https://www.iso.org/standard/66912.html)
- Landing page:
  [ISO/IEC 17025 — Testing and calibration laboratories](https://www.iso.org/ISO-IEC-17025-testing-and-calibration-laboratories.html)
- Verified catalogue metadata: Edition 3, published 2017-11, confirmed 2023-08-18;
  no successor edition identified. Listed 2018 corrections concern French and
  Spanish versions, not a replacement English edition.
- Use: identifies the current edition for laboratory competence work.
- Limitation: use laboratory accreditation as the assurance lane here; a private
  certificate or an ISO 9001 certificate does not establish ISO/IEC 17025 accreditation. Accreditation is granted by an accreditation body for a
  defined scope of laboratory activities; nothing in this skill grants or predicts it.

### ISO 15189:2022

- Official page:
  [ISO 15189:2022](https://www.iso.org/standard/76677.html)
- ILAC announcement:
  [ISO 15189:2022 for medical labs published](https://ilac.org/latest_ilac_news/iso-151892022-for-medical-labs-published/)
- Verified metadata: Edition 4; published December 2022; cancels and replaces
  ISO 15189:2012. Catalogue lists ISO 15189:2012 and ISO 22870:2016 as withdrawn.
- Verified structural facts: the 2022 edition aligns structurally with
  ISO/IEC 17025:2017 and incorporates point-of-care testing requirements previously
  held in ISO 22870. Scheme coverage can still be narrower: CAP 15189 excludes POCT.
- Verified transition: the ILAC-agreed transition period for accredited medical
  laboratories ran to **December 2025**. Treat the 2022 edition as implemented, not
  upcoming; a 2012-based quality system is out of date, not "in transition."
- Limitation: accreditation scope is per laboratory, per location, and per
  examination. It is not organization-wide and not equivalent to licensure.

### ISO copyright

- Official page: [ISO copyright](https://www.iso.org/copyright.html)
- Verified fact: ISO publications are copyright protected; unauthorized copying,
  scanning, or distribution is prohibited, and reproduction requires permission.
- Operational rule: this skill summarizes processes and bibliographic metadata only.
  Do not paste or generate copyrighted clause text.

## United States: FDA QMSR

### Final rule

- Source:
  [Medical Devices; Quality System Regulation Amendments](https://www.federalregister.gov/documents/2024/02/02/2024-01709/medical-devices-quality-system-regulation-amendments)
- Citation/date: 89 FR 7496; published 2024-02-02.
- Verified effective date: **2026-02-02**.
- Verified boundary: ISO certification does not exempt a 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

