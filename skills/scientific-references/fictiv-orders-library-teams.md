---
id: sciref-fictiv-orders-library-teams
name: "Scientific Ref: After the order: tracking, documents, changes, returns, reorders, Library, Teams, account"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (fictiv): After the order: tracking, documents, changes, returns, reorders, Library, Teams, account"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "fictiv orders library teams"
  - "after the order: tracking, documents, changes, returns, reorders, library, teams, account"
keywords:
  - "fictiv"
  - "orders"
  - "library"
  - "teams"
  - "specialized"
  - "scientific"
  - "reference"
  - "after"
  - "order"
---

# After the order: tracking, documents, changes, returns, reorders, Library, Teams, account

The order-detail workflows were checked against the official Help Center on 2026-09-30; this refresh did not inspect an authenticated order. The prior test account had no orders either. Match visible labels and confirm the current state rather than assuming the retained route/selector snapshot is current.

## Contents
1. Order lifecycle
2. Finding and tracking orders
3. Documents: receipts, invoices, inspection reports, photos
4. Changing or cancelling an order
5. Quality problems, returns and remakes
6. Reordering
7. Parts Library and revisions
8. Mold Library (tooling)
9. Teams and workspaces
10. Account settings
11. Contacts: who to ask for what

---

## 1. Order lifecycle

1. **Production Assignment:** "smart sourcing" picks a manufacturing partner. There is no bidding.
2. **Manufacturing.**
3. **Partner Inspection:** at least ISO 2768-m with hand metrology, plus drawing callouts. The partner uploads photos.
4. **Quality Review:** Fictiv QC reviews photos and data remotely.
5. **Packing & Shipping:** a tracking number is posted.

Lead time counts business days from the order date. Orders placed after the daily cutoff start the next business day. Holidays (US, plus Chinese holidays for overseas production) are excluded.

## 2. Finding and tracking orders

- Go to **Orders** (`/orders`). The **Search** box matches order name, part name or PO number.
  - Search terms must be **contiguous substrings**: "1010_back" matches, "1010 back plate" may not.
  - Colleagues' orders only appear if they've been shared into a Teams workspace.
- **View order detail** shows the stage tracker, estimated ship and delivery dates, and your program manager. After shipment it shows the carrier and tracking number, with a **Track Shipment** tab.
- To report status to the user, open the order detail and give: current stage, ship-by date, tracking number and carrier, and any hold or message from Fictiv. `get_page_text` is usually enough.

## 3. Documents

On the order detail page:
- **Download Order confirmation:** the receipt, with part specs, unit and total cost and payment.
- **Invoice:** PO orders are invoiced by AR after the last line ships.
- **Inspection report data** (top of the order): the standard inspection report, CoC and material certs if ordered, and high-resolution photos. Per part there is **View inspection** or "Part Status → View Quality Docs".
- Drawings (under the part name), the 3D viewer, DFM feedback and thread callouts.

Download requested order documents within the task scope and report which files were saved.

## 4. Changing or cancelling an order

- **Terms of Service:** orders can't be cancelled once placed.
- **In practice:**
  - The Help Center gives 5–10 minutes after an afternoon order, or before 10 am PT after an overnight order, as examples of a chance to cancel before production. These are not guaranteed windows.
  - Once production starts, cancellation is difficult and may carry fees.
- **How:** contact the **program manager** named on the order, or hello@fictiv.com, *immediately*. Say the order number and what you want.
- **Design, material or quantity changes** usually mean cancel and re-order. There is an **ECO** (engineering change order) process, usually with fees and lead-time impact. Fictiv doesn't guarantee to honor CAD or PDF updates sent after ordering.
- **Address or shipping method** can be changed before the ship date via the PM or hello@fictiv.com.

Prepare the concrete message and send only when the user has authorized contacting that recipient about the requested change.

## 5. Quality problems, returns, remakes

- **Inspect immediately and contact Fictiv promptly for an RMA.** [Terms §§11 and 13](https://www.fictiv.com/terms) state a standard 72-hour warranty unless the quote says otherwise, and §11 also requires return with an RMA within 72 hours. Do not promise that notification alone preserves a claim or ship a return without Fictiv instructions. Review the actual quote/contract and obtain return instructions immediately.
- **What the Help Center treats as a non-conformance:** a measurable dimension or defined feature missing the agreed requirements at ordering or during fulfillment. Examples: a dimension out of tolerance, missing threads, wrong color, sink, a wrong finish.
- **Not covered:** requirements that were never specified. Examples: a tolerance tighter than ISO 2768-m with no drawing, or threads not configured.
- **How to report:** contact the order's program manager with the order number, part, photos, measurements vs. requirements, and quantity affected. Fictiv assesses whether repair/remanufacture or refund applies. Do not guarantee a free remedy: the Terms contain exclusions including designated High Risk Products and first-article/prototype/pre-production/test products; inspection costs can apply if Fictiv finds the part conforming.
- Help the user by assembling the evidence (photos, measurements, the relevant drawing callout or config line from the order) into a clear, factual message.

## 6. Reordering

- **From an order:** Orders → the order → **Reorder**, and optionally pick parts. You get a fully configured quote ready to check out. To change anything (quantity, finish, lead time), click **Unlock quote**. This re-prices at current rates and may re-run DFM.
- **From the Library:** tick parts, then **Add to quote** (a new or existing quote). This uses the latest revision by default. Or open the part and "Add to quote" on a specific revision.
- **From the new-quote page:** "+ New quote from Parts Library".
- Then continue with the normal quote review and checkout, approval gate included.

## 7. Parts Library and revisions

- `/library/parts`. It fills automatically with purchased parts and is empty until the first order.
  - Search by part number, file name, order name, mold name or PO. Filter by purchase date or purchaser.
- **Part details** has an editable part number (defaults to the filename), a description, and tabs **Purchased Revisions**, **Active Quotes** and **Part Activity**. An orange icon means the part wasn't bought on the platform, so its requirements may be incomplete.
- **New revision:** in a quote, open the row's "…" menu and choose **Upload part revision**. On upload, duplicate detection offers "Use existing revision from Library", "Upload as a new revision" or "Track as a new part number". **View revision history** shows

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

