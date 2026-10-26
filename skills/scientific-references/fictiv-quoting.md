---
id: sciref-fictiv-quoting
name: "Scientific Ref: Quoting on Fictiv: the full workflow"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (fictiv): Quoting on Fictiv: the full workflow"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "fictiv quoting"
  - "quoting on fictiv: the full workflow"
keywords:
  - "fictiv"
  - "quoting"
  - "specialized"
  - "scientific"
  - "reference"
---

# Quoting on Fictiv: the full workflow

This covers everything from a CAD file to a priced quote that is ready for checkout. For the exact labels and layout, see `ui-map.md`. For process and material facts, see `capabilities.md`. For anything that goes wrong, see `troubleshooting.md`.

## Contents
1. Gather requirements first
2. Pre-flight the files
3. Create the quote and upload
4. Classify end use (Prototype / Commercial)
5. Configure each part
   - 5.1 Process and material
   - 5.2 Quantity and quantity tiers
   - 5.3 Finish, masking
   - 5.4 Threads
   - 5.5 Drawing, tolerances, inspections, certificates
   - 5.6 Bulk configuration
6. Review DFM feedback
7. Pick lead time and region
8. Instant price vs. manual quote ("Request quote")
9. Share, forward, download, organize
10. Report the quote back to the user

---

## 1. Gather requirements first

A Fictiv quote is only as good as its configuration. Before you touch the UI, make sure you know the following. Ask the user for anything that is missing, and don't invent specs, because the wrong material or finish produces a real, paid-for wrong part.

| Need | Why it matters | Sensible default if the user explicitly says "you choose" |
|---|---|---|
| Files (paths) and which part is which | Upload | — |
| Process | Changes the materials, price and lead time | CNC for metal or tight fits; 3DP for plastic prototypes and complex organic shapes |
| Material (exact grade) | Price and properties | 6061-T6 aluminum (CNC), Nylon 12 SLS or PA 12 MJF (3DP) |
| Finish and color | Adds cost and days | As machined / as printed |
| Quantity (and whether to compare tiers) | Price breaks | — |
| Threads (size per hole) | Tapped holes are only made if specified | None |
| Tolerances tighter than ISO 2768-m, GD&T, cosmetic reqs | Needs a PDF drawing, and usually a manual quote | ISO 2768-m |
| Inspection or certs (CoC, material cert, CMM, FAI) | Adds cost and days | Standard inspection (free) |
| Prototype vs. Commercial end use | Required; affects tariffs | — (ask; it is a legal declaration) |
| Deadline / need-by date, budget | Choosing the lead-time tier and region | Standard tier |
| Domestic only? ("USA only") | Tariffs, ITAR-adjacent concerns, customer requirements | No |
| Ship-to address (US or Canada) | Tax, shipping, delivery date | — |
| Export classification | Fictiv accepts only EAR99 / 9E991 self-serve; **never ITAR** | — (ask if the part is defense/aerospace-related) |

## 2. Pre-flight the files

Run the checker before uploading:

```bash
python3 <skill>/scripts/check_cad_file.py part1.step part2.sldprt --process cnc
```

It flags likely problems; it is not a CAD kernel or export-control classifier. It inspects STEP text and STL edges, but not native CAD geometry or PDF text. Unknown STEP units stay unitless in its output, and its approximate vertex box can miss curved extrema. A clean result does not certify manufacturability. It flags:
- unsupported formats (IGES, F3D, DXF, assemblies, a drawing on its own)
- mesh files for non-3DP processes
- multi-body or surface-only STEP files (CNC pins/inserts and functional 3DP bodies require manual eligibility review)
- unknown STEP units and small unitless STL dimensions (inch STEP boxes are converted to mm)
- non-watertight STL
- oversize parts
- ITAR text markings

Fix blocking items before uploading. For example, ask the user to export STEP or to split bodies. If the user can't fix the file, explain the consequence (e.g. "this will go to manual review").

## 3. Create the quote and upload

1. Go to `https://app.fictiv.com/pages/quotes/upload`. For an existing quote, open it and use "Select files or drag and drop here to upload" to add parts.
2. **Click the process card** (e.g. "CNC Machining"). Confirm the URL gains `?process=cnc` and the upload pane is active.
3. If a units toggle (mm/in) is shown, set it *before* uploading. This matters most for STL and other unitless mesh files. STEP carries its own units.
4. `find` the `input[type=file]` and upload the file paths to it. You can upload several files at once. When prompted, enable auto-attachment and verify every CAD/PDF pairing; similar names can pair, while duplicates/mismatches may fail. For CNC, drawing reconciliation can populate configuration automatically.
5. The app creates the quote and navigates to `/pages/quotes/<id>`. Record the quote ID and name. If a "Upload complete!" tour appears, click "No, I've got this".
6. Wait for "Analyzing parts (n/N)" to finish. Each row goes "Analyzing geometry…" → "Configuring part…" → a **Configure** button. Poll `quote_state.js` until `analyzing` is false.
7. **Verify the size.** Open the part and read the bounding box in the viewer's bottom right (e.g. `60.00 x 40.00 x 15.00 mm`). Compare it with what the user expects, or with `check_cad_file.py`. A factor of 25.4 means the units are wrong: delete the part and re-upload with the right units.

## 4. Classify end use

The **"Required: Are these parts for prototype or commercial use?"** banner blocks all pricing until answered:
- **Prototype:** "exclusively for development, testing, product evaluation or quality control".
- **Commercial:** "incorporate these components into products that are sold for commercial use".

Ask the user. This is a customs and tariff declaration, so don't guess. Click the card. Afterwards a small dropdown at the top right of the lead-time banner lets you change it.

## 5. Configure each part

Click **Configure** in the row. This opens the part modal on the Configuration tab.

### 5.1 Process and material
- The Process select is pre-set from the card you chose. You can change it per part. Options: CNC, 3D Printing, Urethane Casting, Sheet Metal ("Instant/manual quote") and Injection Molding, Compression Molding, Die Casting ("Quote available within 48 hours").
- **Material:** click the field, type a distinctive fragment (`6061`, `17-4`, `PEEK`, `Nylon 12`, `Accura 25`), then press Enter. Check the field text afterwards. To list everything, open the dropdown and run `list_dropdown_options.js`. The full lists captured in Sep 2026 are in `capabilities.md`. "Custom Materials" and "Other" exist but force a manual quote.
- Set **Quantity**, then click **Apply configuration**. The panel collapses into a summary with a per-unit price (e.g. `$234.80/ea`). The price here reflects the default lead-time tier.
- To change the process or material later, click **Edit** next to the summary, change it, then click **Save**. Finishes

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

