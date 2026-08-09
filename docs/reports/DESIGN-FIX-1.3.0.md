# BerryBrain 1.3.0 — design-fix evidence

## Visual system

- Primary accent: `#BF1755`; success: `#83A637` in light, dark, persisted-theme and graph palettes.
- Brain hero uses `/iconelogo.png` as a monochrome CSS mask.
- Home Ask stays on `/brain`, opens an accessible modal, submits automatically, and retains evidence, Flow, online research and insight actions.
- Home uses a balanced two-column layout; recent activity fills the space below recent connections.

## Graph

- First graph open per session defaults to `brain` layout and the Knowledge map filter.
- D3.js v7 drives `forceCollide` (`node radius + 11`), `forceManyBody`, elastic `forceLink`, weak centering and `velocityDecay(0.15)`.
- Nodes spawn in a compact center cluster. D3 zoom-to-fit runs at 450 ms, 1.25 s and 2.4 s while the graph settles, unless the user moves the camera.
- D3 zoom provides pointer-centered zoom and unbounded pan. Drag pins the node and reheats the network with `alphaTarget(0.3)`; release restores fluid settling.
- Graphs below 8,000 nodes keep a live interactive simulation. Extreme graphs run the same D3 forces in a Web Worker to preserve main-thread interaction.
- Labels are centered inside nodes and use semantic zoom. Focus isolates the selected/hovered node and every direct neighbor.
- Node colors come from persisted `pending`, `semantic` and `vault` palettes. Edge colors use relation types; unknown types receive a deterministic FNV-based HSL color.
- The 42-node demonstration fixture exists only in Playwright and is never bundled as runtime data.

## Review today

- `GET /api/v1/reviews?due=true` loads due cards.
- Reveal exposes grounded expected points.
- Rating posts to `/api/v1/reviews/{id}/grade`, removes the completed card and advances the schedule.
- Production-container E2E covers navigation, reveal, `good` persistence and the empty completion state.

## Verification

- API: 355 tests passed; coverage 82%.
- Worker: 44 tests passed. HippoRAG sidecar: 7 tests passed.
- Web: 46 scenarios passed; one pre-existing autofocus race passed on retry, was fixed, then its workflow passed 3/3 repeated runs.
- WCAG A/AA and reduced-motion gates passed.
- Final production build: 24 static pages; `/brain` 56.7 kB route, 230 kB first load.
- 10k graph: cold first visual 1.86 s, complete load 5.55 s, interaction p95 164.3 ms, heap 35.1 MB.
- Runtime image: targeted D3 and Review today tests passed against Docker production.
- Planning: 259/259 evidence-backed items checked in `docs/planning/planejamento-design-fix.md`.
