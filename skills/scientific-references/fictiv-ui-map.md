---
id: sciref-fictiv-ui-map
name: "Scientific Ref: Fictiv web app: UI map and browser-automation notes"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (fictiv): Fictiv web app: UI map and browser-automation notes"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "fictiv map"
  - "fictiv web app: ui map and browser-automation notes"
keywords:
  - "fictiv"
  - "map"
  - "specialized"
  - "scientific"
  - "reference"
  - "browser"
---

# Fictiv web app: UI map and browser-automation notes

Retained from an authenticated September 2026 app snapshot; not revalidated in an authenticated session during the 2026-09-30 public-documentation review. Browser URLs below are UI routes, not REST endpoints or a supported API contract. Fictiv ships UI changes often, so treat labels as hints rather than guarantees. If something has moved, use `find`/`read_page` with the label text rather than fixed coordinates.

## Contents
1. URL routes
2. Global layout
3. New-quote page (process picker + upload)
4. Quote page
5. Part modal (Configuration / Threads / Manufacturability feedback)
6. Checkout page
7. Account, Library, Orders
8. Automation techniques that work (and ones that don't)

---

## 1. URL routes

| Page | URL |
|---|---|
| Home / dashboard | `https://app.fictiv.com/home` |
| Quotes list | `/pages/quotes` |
| New quote (process picker + upload) | `/pages/quotes/upload` (adds `?process=cnc` once a process card is clicked) |
| Quote detail | `/pages/quotes/<quoteId>` |
| Part modal, config tab | `/pages/quotes/<quoteId>/part/<partId>/configuration` |
| Part modal, threads tab | `/pages/quotes/<quoteId>/part/<partId>/threads` |
| Part modal, DFM tab | `/pages/quotes/<quoteId>/part/<partId>/feedback` |
| Checkout for a quote | `/pages/orders/quote/<quoteId>` |
| Orders list | `/orders` |
| Parts Library | `/library/parts` (tabs: Parts, Molds) |
| My Account | `/pages/my-account` |
| Help Center | `https://www.fictiv.com/help` (`/help-center` and the old `help.fictiv.com` article links redirect here) |
| DFM tool Atlas | `https://atlas.fictiv.com` (separate app; public upload/login page observed in documentation extraction) |

The recorded quote/part IDs were UUIDs. Verify navigation in the current session before relying on these deep links; an HTTP 200 or login redirect does not validate an authenticated route. Re-opening a quote URL throws away unsaved edits in an open part modal, which is a clean way to back out of a half-finished edit.

## 2. Global layout

- **Left nav:** Home, Library, *My workspace* → Quotes, Orders, *Team workspaces* → (teams), "Create a workspace".
- **Top right:** "Invite to Fictiv", "Learn about TEAMS", and an avatar menu with **My Account**, **Help & Resources**, **Log out** (shows the signed-in email).
- **Home page cards:** "Start a new quote", "View your Library", a **dedicated account manager** card (name, email, phone, "Book a meeting"), an onboarding checklist, and "Helpful resources" (FAQ, capabilities, Materials.AI, Atlas DFM, sample part download, tariff notes).
- **Survey and feedback widgets** ("How would you rate your experience…") show up in page text. Ignore them.

## 3. New-quote page: `/pages/quotes/upload`

**Step 1, "Select a process".** Pick one of the cards:
- *Instant quoting available:* **CNC Machining**, **3D Printing**, **Urethane Casting**, **Sheet Metal**
- *Quote available within 48 hours:* **Injection Molding**, **Compression Molding**, **Die Casting**

Each card shows sub-processes, material count and "As fast as N days". The radio inputs have values `cnc, 3dp, rtv, sheet, im, cmprmold, diecast`.

> ⚠️ **Click the card itself** (its title text or body), not the hidden radio input. Clicking the radio by ref left it unchecked and the upload zone stayed greyed out. After a correct click the URL gains `?process=<value>` and the right pane turns active.

**Step 2, "Upload your files".** Drag-and-drop zone, "Select files or folder to upload", and "See all supported file types" (a modal with "Most Processes" and "3D Printing" tabs).
- The upload control is a hidden `<input type=file multiple>`. **Upload by setting files on that input** (e.g. the browser tool's file-upload action with the input's ref). Don't click the button, because a native file picker is invisible to you.
- Read the current export-control declaration. The [project-submission guide](https://www.fictiv.com/help/getting-a-quote/how-to-submit-an-export-controlled-project) permits EAR99/9E991 self-serve, excludes ITAR, and routes other ECCNs through review; do not generalize old upload-banner wording to every EAR classification.
- "+ New quote from Parts Library" (top right) builds a quote from previously ordered parts.

After an upload the app **creates the quote automatically** and redirects to `/pages/quotes/<id>`. The quote is named `<lastname>_<MMDDYY>`, which you can rename with the pencil icon. A first-time "Upload complete! Next steps…" tour modal may appear. Dismiss it with **"No, I've got this"**.

## 4. Quote page: `/pages/quotes/<quoteId>`

Top to bottom:

1. **Header:** "Save and back", the quote name with a ✏️ rename icon, "Last modified", **View activity log** (a timestamped list of who configured, classified or created what), **Share** and **Delete**.
2. **Banner.** It changes with the quote's state (the `banner` field in `scripts/quote_state.js`):
   - `Required: Are these parts for prototype or commercial use?` shows two cards, **Prototype** and **Commercial**. **Pricing and lead times stay hidden until one is chosen.**
   - `Configure parts to receive lead times` means at least one part is unconfigured.
   - `Determining available lead times` is a transient loading state.
   - `Select regional preference` is the lead-time picker (below). A small Prototype/Commercial dropdown sits at its top right.
3. **Lead-time picker** ("Select regional preference"), shown when every part is configured:
   - **North America** column (with a **"USA only"** checkbox) and **Overseas** column.
   - Each column has three radio tiers: Fastest, Standard, Cost-effective. Radio values: `domesticFastest`, `domesticStandard`, `domesticCostEffective`, `overseasFastest`, `overseasStandard`, `overseasCostEffective`.
   - Example seen: USA 4 days $745.84 / 6 days $520.80 / 13 days $259.49, and overseas 8 days $200.01 / 11 days $150.61 / 15 days $136.74, for a one-off anodized 6061 bracket.
   - **Choosing a tier opens a confirm dialog:** "Are you sure you want to change lead times? … will update the production speeds of all parts…" with Cancel / Continue and a "Don't ask again" checkbox. That is easy to trigger by accident, so read the dialog and press Cancel if it wasn't intended.
   - Prices show `$ --` when any part needs a manual quote.
4. **Toolbar:** "Select files or drag and drop here to upload" (adds parts to *this* quote), **Configure via drawing** (enabled once parts are selected), **Select all**. When rows are

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

