---
id: sciref-labarchive-integration-integrations
name: "Scientific Ref: Official LabArchives Integrations"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (labarchive-integration): Official LabArchives Integrations"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "labarchive integration integrations"
  - "official labarchives integrations"
keywords:
  - "labarchive"
  - "integration"
  - "integrations"
  - "specialized"
  - "scientific"
  - "reference"
  - "official"
---

# Official LabArchives Integrations

Verified against the official help-center integration section on
**2026-09-30**:
https://help.labarchives.com/hc/en-us/sections/11732611360660-Integrations

The current index lists:

- External Integrations Overview
- GraphPad Prism
- SnapGene
- Geneious
- Proofig AI
- Jupyter
- REDCap
- Protocols.io
- Qeios
- SciSpace
- Vernier Logger Pro
- DataCite

Availability can depend on product, license, regional server, institutional
policy, and administrator configuration. Check the exact article and local
approval before moving research data.

## Integration is not a generic API contract

An advertised integration may be:

- a file upload/viewer,
- a vendor-side export,
- a locally installed external module,
- a product-specific account connection,
- or a LabArchives UI feature.

Do not convert those workflows into guessed ELN methods, Inventory routes, or
OAuth endpoints. The official sources reviewed do not establish generic
`/oauth/authorize` or `/oauth/token` endpoints, client-ID scopes, refresh tokens,
or a universal LabArchives OAuth 2.0 flow.

The legacy ELN API has a documented **OAuth-like API user-login redirect** using
`/api_user_login`, a signed redirect URI, an authorization code, and
`users::user_access_info`. That is a separate API authorization mechanism; see
[`authentication_guide.md`](authentication_guide.md).

## Jupyter

Official article, updated **2025-09-08**:
https://help.labarchives.com/hc/en-us/articles/11780569021972-Jupyter-Integration

Verified behavior:

- Upload an `.ipynb` as an Attachment Entry or by drag-and-drop.
- LabArchives shows a preview and opens the file in its Docs Viewer.
- Edit the notebook locally and upload a replacement to change its contents.
- Page revisions retain prior uploaded versions.
- Viewer annotations are not included in revision history.

This is an attachment/viewer workflow, not evidence of a live Jupyter kernel,
two-way synchronization, or an API-specific notebook-entry type. Preserve the
original `.ipynb`; consider attaching an environment lock/export separately
according to institutional policy.

## REDCap

Official article, updated **2025-09-05**:
https://help.labarchives.com/hc/en-us/articles/11780613160980-REDCap-Integration

Verified behavior:

- Mass General Brigham's REDCap team developed the **MGB LabArchives** External
  Module.
- An institution's REDCap administrators install and configure it.
- A user connects with the email matching their LabArchives account and a
  LabArchives temporary token in place of a password.
- The module uploads selected REDCap reports to a chosen owned notebook.
- The feature may be unavailable or unapproved at an organization.

This is not a generic “sync all REDCap data” API. Before upload, select the exact
report and remove/de-identify data as required. Never claim that the integration
itself makes a workflow HIPAA- or 21 CFR Part 11-compliant.

The help article links the module source:
https://github.com/PHSERIS/redcap_lab_archives_em

Treat it as a separate community/institutional dependency. Review and pin the
approved release/commit through the REDCap administrator rather than installing
it from this skill.

## Protocols.io

Official article, updated **2025-09-22**:
https://help.labarchives.com/hc/en-us/articles/11780572389524-Protocols-io-Integration

Verified behavior:

- Connection starts in Protocols.io under **Settings > Apps > LabArchives**.
- The user selects the correct LabArchives regional server.
- A connected user can export a protocol or protocol run record.
- The result is saved in the LabArchives notebook as a PDF.
- SSO users may need a LabArchives temporary token.
- The connection remains active until deactivated in Protocols.io.

Do not replace this supported vendor workflow with a fabricated
`entries::create_entry` script or assume HTML, comments, versions, or metadata
are synchronized beyond what the article states.

## GraphPad Prism

Official article:
https://help.labarchives.com/hc/en-us/articles/11780457243668-GraphPad-Prism-Integration

The article (2026-06-25) documents Prism 8+ and regional configuration for
AU/UK/EU/CA using `labarchivesconfig.txt`; US accounts skip that configuration.
A first save goes to the LabArchives Inbox, where the user moves it to a page.
On later saves, choose between a new Inbox copy and updating the existing file
version. Do not post files to an inferred endpoint. Copy region configuration
values carefully: the article's Canada hyperlink targets currently point to EU
hosts even though the displayed Canada URLs use `ca-` / `caapi`. Use the
verified regional table in `authentication_guide.md` and confirm the destination.

## SnapGene

Official article:
https://help.labarchives.com/hc/en-us/articles/11780512729492-SnapGene-Integration

The article (2025-11-03) documents SnapGene 4.2+, **Preferences > Files >
Enable file exchange with LabArchives**, then **File > Save to LabArchives**
or **Open File from LabArchives**. Use the correct regional API server; its
Canada link has the same displayed-URL/target mismatch as the Prism article.
SSO uses a temporary token. Do not assume a SnapGene CLI or universal file
compatibility; the article makes support dependent on version and data structure.

## Geneious and other indexed integrations

Use the current help-center index to open the exact article for Geneious,
Proofig AI, Qeios, SciSpace, Vernier Logger Pro, or DataCite. The presence of a
name in the index verifies an official help topic, not a programmable API or
bidirectional synchronization capability.

For every integration:

1. Identify where the connection is configured.
2. Confirm the user's region and organizational approval.
3. Record what data leaves each system and in which direction.
4. Determine whether the operation stores a copy, link, preview, or live
   connection.
5. Use temporary tokens only through the documented product UI and never store
   them in scripts.
6. Test with non-sensitive data in an approved test notebook.
7. Verify the resulting file/object and revision behavior.

## Custom integration boundary

Only build a custom integration when the official product workflow does not
meet the requirement and API access has been approved.

- For ELN data, select a method from the current official ELN class tree.
- For Inventory, select an exact `/public/v1/...` page.
- Keep source-system authentication separate from LabArchives authentication.
- Use a redacted dry run for eve

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

