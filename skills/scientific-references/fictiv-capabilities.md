---
id: sciref-fictiv-capabilities
name: "Scientific Ref: Fictiv capabilities reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (fictiv): Fictiv capabilities reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "fictiv capabilities"
  - "fictiv capabilities reference"
keywords:
  - "fictiv"
  - "capabilities"
  - "specialized"
  - "scientific"
  - "reference"
---

# Fictiv capabilities reference

Material lists marked **(live)** are the retained September 2026 configurator snapshot, not a fresh authenticated audit. Official Help Center and specification pages were reviewed on 2026-09-30. They sometimes conflict: confirm the selected process/material, final quote, drawing requirements and account-specific options before ordering. An upload widget's accept list is not proof that a format can be manufactured. Re-check dropdown options with `scripts/list_dropdown_options.js`.

## Contents
1. Processes at a glance
2. File formats
3. CNC machining: materials (live), finishes (live), tolerances, surface, threads, design rules
4. 3D printing: technologies, materials (live), tolerances, build sizes, design rules
5. Sheet metal
6. Urethane casting
7. Injection molding
8. Compression molding, die casting
9. Inspection and certificates
10. Lead-time mechanics and holidays
11. Compliance: export control, ITAR, IP, NDA
12. Tools: Materials.AI, Atlas, Punchout; public API verification limits

---

## 1. Processes at a glance

Advertised fastest times and recorded material counts are planning aids, not an order commitment. The configured quote determines availability, timing and cost; casting/molding sample timing does not imply completed production tooling/runs.

| Process (card name) | Quote | "As fast as" | Account needed | Notes |
|---|---|---|---|---|
| **CNC Machining**: mill, lathe, EDM, gear hobbing, 3/5-axis | Instant; complex or drawing parts go to a human (under 2 h) | 1 day | any | 70+ materials. Tolerances to ±0.001" reliably with a drawing; marketing claims ±0.0001". Finishing, assembly, welding, inserts. |
| **3D Printing**: FDM, SLS, SLA, PolyJet, MJF, Carbon DLS | Instant | 1 day | any | 45+ materials, 11 finishes. No DMLS/metal printing listed. |
| **Urethane Casting** | Instant for simple parts, else manual | 7–10 days | company email | 12 materials. About 20 castings per silicone mold. |
| **Sheet Metal**: cutting, forming, welding, inserts | Instant | 2 days | any | 11 materials, 11 finishes |
| **Injection Molding**: production, family, multi-cavity, overmolding | Instant IM is advertised for eligible parts; other projects require review | 10 days (T1) | company email | 30+ standard / 100+ custom resins |
| **Compression Molding** | Manual (48 h) | 10 days | company email | 9 elastomers |
| **Die Casting**: high and low pressure | Manual (48 h) | 10–15 days | company email | 8 alloys, post-machining |

Fictiv doesn't design parts. It needs a 3D CAD file. Extrusion isn't a self-serve process.

## 2. File formats (live "Supported File Types" modal)

Use the [supported-format list](https://www.fictiv.com/help/uploading-and-organizing-parts/what-file-formats-does-fictiv-support). In most cases files need one solid body. The [getting-started guide](https://www.fictiv.com/help/getting-started/how-to-get-started-with-fictiv) permits modeled-in CNC pins/inserts; other separate CNC bodies must be split. The dedicated 3DP multi-body policy has functional exceptions (§4.5).

- **Parametric CAD (all processes):**
  - Dassault: `.sldprt .3dxml .catpart .catshape .cgr .dlv .exp .model .session`
  - Siemens: `.jt .par .prt .x_t .x_b`
  - STEP: `.stp .step`
  - Autodesk: `.ipt`
  - PTC: `.prt`
  - Other: `.3dm .vda .x3dv .ifc .xpr .xas .mf1 .neu .prc .sab .sat .u3d`
  - The historical uploader additionally listed `.3mf .arc .gts .ifczip .pkg .unv .xmt .xmt_txt`; public manufacturing support for these was not verified. Export STEP or a documented mesh format. `.wrl` and `.acs` are mesh formats, not CNC formats.
- **Mesh (3D printing only):** `.stl .3ds .collada .dae .obj .off .ply .v3d .pts .tri .acs .x3d .wrl`
- **PDF drawings:** must accompany a CAD file and cannot be quoted alone. The drawing guide excludes normal 3DP drawing attachment, while the quoting-time guide describes a drawing for 3DP inserts: confirm that special workflow with Fictiv before promising it.
- **Assemblies (BOM only, not quotable):** `.sldasm .asm .iam .catproduct`
- **Not supported:** IGES, `.f3d`, `.slddrw`, `.dxf`, `.catdrawing`, native Solid Edge `.psm` and `.pwd` (export STEP).
- **SolidWorks:** save a single configuration, because multi-config files are rejected.
- **File size limit:** not documented.

**Best choice:** STEP (AP214 or AP242), one part per file, modeled at true size.

## 3. CNC machining

### 3.1 Materials (live list)

- **Aluminum:** 2024 (T3/T351/T4), 5052 (H32), 6061 (T6/T651/T6511), 6063 (T5/T52), 7050 (T7451), 7075 (T6/T651/T6511/T7351), MIC-6
- **Stainless steel:** 15-5 PH, 17-4 PH (Annealed / H1150 / H900), 303, 304/304L, 316/316L, 410, 416, 420, 440C, A286, Nitronic 60
- **Steel:** 1045, 1215, 12L14, 4130, 4140, 4340, 8620, A2 tool, A36, A514, Cast Iron, D2 tool, Inconel 625, Inconel 718, O1 tool, 1018, Zinc-Galvanized Low-Carbon Steel, Galvannealed Steel
- **Copper, brass, bronze:** 101 Cu, 110 Cu, 260 Brass, 360 Brass, 544 / 932 / 954 Bearing Bronze
- **Plastic:** ABS, Acrylic, Chemical-Resistant PVC, Delrin (20% GF), Delrin 150, Delrin AF (13% PTFE), Garolite G-10, HDPE, Nylon (30% GF), Nylon 6/6, PEEK, PEEK (30% GF), Polycarbonate, Polypropylene, PPS, PTFE (Teflon), Torlon PAI 4301, UHMW, ULTEM 1000
- **Titanium:** Grade 2, Grade 5
- **Exotic:** AZ31B / AZ61B / AZ91D Magnesium, Invar 36, Kovar, Zamak 3
- **Custom Materials, Other:** these force a manual quote

Machinability affects price. Aluminum and brass are fastest and cheapest. Stainless, titanium, Inconel and tool steels cost more and take longer.

### 3.2 Finishes

Live menu for 6061:
- Anodize per MIL-PRF-8625 **Type II**
- **Type III** (hardcoat)
- **Type III w/ PTFE**
- **Chem Film (Alodine™)**
- **ENP** (electroless nickel)
- **Media Blasting** (Fictiv's name for bead blast)
- **Nickel Plating**
- **Powder Coating**
- **Vibratory Tumble**

Type II colors (live): Natural, Black, Blue, Gold, Red, all sealed. Type II added 2 days in the prior quote snapshot; the current [finish specification guide](https://www.fictiv.com/specifications/surface-finishes) lists a general 5–10 day range. Use the actual quote delta, not a fixed promise.

Other finishes by material (Help Center):
- **Steel and stainless:** Black Oxide, Passivation, Electropolish, Zinc Plating, ENP, Powder coat, Media blast, Tumble
- **Acrylic:** Hand polish
- **Polycarbonate:** Vapor polish

The recorded configurator default was **As machined: ISO Grade N7, Ra 1.6 µm / 63 µin**. The current [CNC specifications](https://w

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

