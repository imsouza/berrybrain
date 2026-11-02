---
id: sciref-fictiv-troubleshooting
name: "Scientific Ref: Troubleshooting Fictiv"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (fictiv): Troubleshooting Fictiv"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "fictiv troubleshooting"
  - "troubleshooting fictiv"
keywords:
  - "fictiv"
  - "troubleshooting"
  - "specialized"
  - "scientific"
  - "reference"
---

# Troubleshooting Fictiv

Find the symptom, then apply the fix. The entries marked "(seen live)" were reproduced on app.fictiv.com in Sep 2026.

## Contents
1. Login / access / account
2. Upload problems
3. DFM feedback: what each warning means and what to do
4. Configuration and pricing problems
5. Lead time and delivery problems
6. Checkout and payment problems
7. Order and post-order problems
8. Browser-automation problems

---

## 1. Login / access / account

| Symptom | Cause | Fix |
|---|---|---|
| Redirected to a login page | Session expired | Ask the user to log in themselves, or use a password-manager credential tool if the environment has one. Never type passwords from chat. |
| Injection molding, urethane, die casting or compression molding is missing; no PO option; no Materials.AI | Personal-email account (Gmail and similar) | The user verifies a company email (banner prompt, or hello@fictiv.com) |
| Checklist says "Verify my email address" | Email is unverified | The user clicks the link in the verification email |
| Can't see a colleague's quote or order | Not shared to your workspace | The colleague shares it via Share → Team workspace |

## 2. Upload problems

Run `scripts/check_cad_file.py` first for format and heuristic STEP/STL checks. Native CAD geometry, PDF contents, functional multi-body eligibility and actual manufacturability require separate review.

| Symptom | Cause | Fix |
|---|---|---|
| Upload zone greyed out, nothing happens on file select (seen live) | No process card selected (the URL has no `?process=`) | Click the process **card** text, not the radio input, then upload again |
| File picked but nothing happens | Ad blocker, or a corporate firewall blocking uploads | Disable the ad blocker for app.fictiv.com and refresh; try another network |
| File rejected by type | IGES, F3D, DXF, native PSM/PWD, drawing-only, assembly | Export STEP (one part per file); attach the PDF to its part |
| Mesh rejected for CNC, urethane or IM | Mesh is 3DP-only | Upload STEP or native CAD |
| Multi-body file loses instant pricing or is rejected | Multiple solids need review | Split separate parts. CNC modeled-in pins/inserts and functional 3DP interlinked components have documented exceptions; separate floating 3DP bodies are unacceptable. A manual quote is not proof that an unsupported file can be manufactured. |
| "Not watertight" / non-manifold | Holes in the mesh (surface modelers) | Repair (Netfabb, Meshmixer) or re-export as a solid |
| SolidWorks part rejected | Multiple configurations | Save a single-configuration copy, or export STEP |
| Part 25.4× too big or small | Units mismatch (unitless mesh, or wrong mm/in toggle) | Delete the part and re-upload with the correct units; confirm the bounding box in the viewer |
| Part larger than the process envelope | Too big | Pick a bigger-envelope technology, split the part, or contact sales for the large-part program |
| Stuck on "Analyzing geometry…" for more than about 3 minutes | Heavy file or backend delay | Reload the quote page. If still stuck, delete the row and re-upload a lighter STEP. |
| Quote and files vanished after upload | ITAR language detected, so the quote is auto-deleted | Don't re-upload. Fictiv doesn't accept ITAR. |

## 3. DFM feedback: meaning and response

In every case, tell the user what Fictiv said, then offer three paths: **proceed as is**, **fix the CAD and click "Upload revision"**, or **ask Fictiv via "Chat with us"**. Warnings don't block ordering, but they're Fictiv's heads-up that the result may differ from the model.

| Warning (Fictiv's wording) | Meaning | Typical fix |
|---|---|---|
| **Thin walls detected** (seen live): "areas on this model that fall below our minimum thickness (0.5mm for metals), and they may not hold up…" | Walls too thin (metal under 0.5 mm, plastic under 1 mm) | Thicken the walls. Or accept the risk of breakage and deflection. |
| **Fillets: Added (Metals)** (seen live): "Fillets will be added in all sharp internal edges… may also be eligible for EDM (requiring extra lead time and cost)" | Sharp internal corners can't be cut with round tools | Add internal radii of at least 0.8 mm (bigger for deep pockets), or accept tool-radius fillets. If sharp corners are essential, EDM costs more. |
| Fillets to be increased | Radii smaller than practical tools | Optional: enlarge the radii to save cost |
| Depth of cut | Pocket deeper than about 10× tool diameter | Shallower pocket, wider pocket, or bigger corner radius |
| Depth of hole | Drilled deeper than about 12× diameter | Shorten or widen the hole |
| Non-standard thread (produced at risk) | No gauge exists for the thread | Switch to a standard thread |
| Warping may occur | Heavy material removal | Rethink the geometry, add ribs, or choose another process |
| Not optimized for CNC machining | Geometry unsuited to CNC | Consider 3DP or casting; ask Fictiv |
| Unreachable volume | A tool can't reach the feature | Redesign, split the part, or ask about 5-axis or EDM |
| EDM may limit lead time options | Feature needs EDM | Redesign if a fast or domestic lead time matters |
| Gear hobbing may limit lead time options | Hobbing is overseas-only | Accept overseas, or redesign |
| Manual deburring may be necessary | Chamfers unreachable by tools | Remove the chamfers or accept |
| Thin stock not available for chosen material | Part thinner than available stock | Change material or thickness |
| Tight tolerance plastics | Tolerance under about ±0.1 mm on plastic | Loosen it, or use PEEK |
| Non-matching drawing and CAD model / Material mismatch | The drawing disagrees with the config or model | Fix whichever is wrong; model and drawing must agree |
| Part will be reworked from McMaster part number | Fictiv will modify a stock part | Usually fine; tell the user |
| "Please request a quote to receive manufacturability feedback" (seen live) | The part is on the manual-quote path | DFM comes from the quoting team after Request quote |

**Injection-molding DFM reports:** open the Manufacturability feedback tab, click "Show DFM topics", annotate each slide marked "Approval required" or "Revision required", then click **Notify Fictiv**. Confirm with the user before notifying.

## 4. Configuration and pricing problems

| Symptom | Cause | Fix |
|---|---|---|
| No prices at all, banner "Required: Are these parts for prototype or commercial use?" (seen live) | End use not declared | Ask the user and click Prototype or Comme

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

