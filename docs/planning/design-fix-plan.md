# BerryBrain — UI, Graph, Language and Organic Data Plan

## Objective

Improve BerryBrain's visual quality and core experience, with special attention to BrainView and graph visualization, while standardizing the entire application in English and eliminating mocked or hardcoded product data. The existing `docs/DESIGN.md` must be the visual source of truth.

## Global constraints

- [x] Preserve all existing behavior during visual-only changes.
- [x] Do not remove, rename or alter existing functional flows as part of the visual redesign.
- [x] Apply `docs/DESIGN.md` consistently across the landing page and every authenticated BerryBrain page.
- [x] Keep the entire current product, source code and user-facing experience in English.
- [x] Do not implement Brazilian Portuguese, Spanish or any other localization in this phase.
- [x] Ensure new features use real application data and organic generation flows.
- [x] Validate desktop and responsive layouts after every major visual change.
- [x] Respect accessibility requirements, including keyboard navigation, focus states, contrast and reduced-motion preferences.

---

## 1. Graph visualization

### 1.1 Obsidian-style visual language

- [x] Redesign graph nodes using Obsidian-inspired proportions, shapes and visual hierarchy.
- [x] Use circular nodes as the default shape.
- [x] Define a restrained minimum and maximum node radius to prevent oversized or unreadable nodes.
- [x] Scale node size according to meaningful graph data, such as link count or relevance, rather than arbitrary values.
- [x] Keep isolated and low-connectivity nodes visible without giving them excessive visual weight.
- [x] Use category or folder colors generated from real vault organization data.
- [x] Use a premium color palette consistent with `docs/DESIGN.md`.
- [x] Add subtle node outlines, glow and depth without reducing readability.
- [x] Keep node labels legible at useful zoom levels.
- [x] Hide or simplify labels progressively when zoomed out to avoid visual clutter.
- [x] Highlight important or highly connected nodes without overwhelming the rest of the graph.

### 1.2 Edges

- [x] Redesign edges with thin, refined strokes inspired by Obsidian's graph view.
- [x] Adjust edge opacity based on context and relevance.
- [x] Avoid visually heavy lines and excessive glow.
- [x] Use smooth edge movement while nodes reposition.
- [x] Ensure edges remain correctly attached to nodes throughout drag and physics animations.
- [x] Visually distinguish the active node's connected edges from inactive edges.
- [x] Preserve edge clarity in dense graph regions.

### 1.3 Hover and selection focus

- [x] On node hover, temporarily focus that node and its direct connections.
- [x] On node click, persist the focused state until it is cleared or another node is selected.
- [x] Keep the active node, directly connected nodes and connecting edges fully visible.
- [x] Dim every unrelated node and edge across the entire graph.
- [x] Use a refined opacity transition instead of abruptly hiding unrelated elements.
- [x] Make hover state temporary and click state persistent.
- [x] Allow the focused state to be cleared by clicking the graph background.
- [x] Allow `Escape` to clear the focused state.
- [x] Define predictable behavior when hovering another node while a clicked node is selected.
- [x] Ensure selection remains understandable at every zoom level.
- [x] Show useful node information without obscuring the graph.

### 1.4 Motion and graph physics

- [x] Add a soft bubble-like entrance animation when the graph view opens.
- [x] Animate nodes from a compact initial formation into their calculated positions.
- [x] Add subtle organic motion while the graph settles.
- [x] Avoid continuous movement that makes reading or selecting nodes difficult.
- [x] Smoothly animate node and edge updates when the graph structure changes.
- [x] Keep physics stable during dragging and release.
- [x] Add gentle inertia when a dragged node is released.
- [x] Prevent nodes from overlapping excessively.
- [x] Prevent extreme graph expansion or nodes escaping the useful viewport.
- [x] Respect `prefers-reduced-motion` with a simplified, near-instant alternative.
- [x] Maintain acceptable performance with large vaults and dense graphs.

### 1.5 Graph controls and states

- [x] Restyle zoom, fit, reset and filter controls according to `docs/DESIGN.md`.
- [x] Provide clear loading, empty and error states in English.
- [x] Add a clear action to fit the complete graph into view.
- [x] Preserve the user's graph position when opening and closing node details where appropriate.
- [x] Ensure mouse, trackpad and keyboard interactions feel consistent.
- [x] Test graph rendering with small, medium and large vaults.

### Acceptance criteria

- [x] The graph resembles Obsidian in node scale, circular form, visual density and edge subtlety.
- [x] Hovering or selecting a node dims all unrelated elements across the full graph.
- [x] Only the active node, its direct neighbors and their connecting edges remain emphasized.
- [x] Opening the graph produces a smooth bubble/settling animation.
- [x] Dragging nodes updates vertices and edges smoothly without detachment or visual jumps.
- [x] The graph remains readable and responsive with dense real-world data.

---

## 2. BrainView — primary product experience

- [x] Treat BrainView as the main visual and interaction priority of the application.
- [x] Rework BrainView's hierarchy to make the brain, active context and primary actions immediately understandable.
- [x] Apply the full visual system from `docs/DESIGN.md`.
- [x] Improve spacing, typography, surfaces, borders, shadows and depth.
- [x] Remove unnecessary visual noise and competing focal points.
- [x] Make navigation between brain content, graph and Ask feel seamless.
- [x] Improve the presentation of notes, sources, relationships and generated insights.
- [x] Add polished skeleton, loading, empty, processing, success and error states.
- [x] Use motion to communicate state changes without delaying interaction.
- [x] Keep primary actions visible and secondary actions discoverable.
- [x] Ensure BrainView works well on smaller desktop widths and responsive layouts.
- [x] Verify that visual changes do not modify existing BrainView business logic.

### Acceptance criteria

- [x] BrainView is visually recognizable as BerryBrain's main workspace.
- [x] Primary actions and content hierarchy are clear without onboarding explanation.
- [x] Graph, content and Ask entry points share one consistent visual language.
- [x] All BrainView states are polished and written in English.

---

## 3. Global design-system application

### 3.1 Foundation

- [x] Use `docs/DESIGN.md` as the single visual reference for the whole system.
- [x] Consolidate reusable design tokens for colors, typography, spacing, radius, borders, shadows, motion and layering.
- [x] Remove inconsistent one-off styling when an approved token or component exists.
- [x] Standardize buttons, inputs, cards, dialogs, dropdowns, tabs, tooltips and navigation elements.
- [x] Standardize hover, active, selected, disabled, loading and focus-visible states.
- [x] Use consistent icon sizing, stroke weight and alignment.
- [x] Keep dark and light themes coherent if both currently exist.

### 3.2 Landing page

- [x] Apply `docs/DESIGN.md` to the complete landing page.
- [x] Improve hero hierarchy, typography, spacing and product presentation.
- [x] Present the graph and BrainView as premium core product experiences.
- [x] Standardize calls to action and supporting sections.
- [x] Ensure every visible string is in English.
- [x] Remove placeholder testimonials, fake metrics, fabricated logos or other mocked marketing content.
- [x] Use real product capabilities and real product visuals only.
- [x] Improve responsive behavior and mobile readability.

### 3.3 BerryBrain application pages

- [x] Apply the design system to every BerryBrain page.
- [x] Standardize the application shell, navbar, sidebar and page headers.
- [x] Standardize page spacing and maximum content widths.
- [x] Standardize lists, tables, cards, forms, dialogs and notifications.
- [x] Audit every empty, loading, error and success state.
- [x] Ensure all pages visually belong to the same product.
- [x] Preserve existing functions while changing presentation.

### Acceptance criteria

- [x] Landing page and application use the same design tokens and component language.
- [x] No page appears unfinished, visually disconnected or based on placeholder styling.
- [x] Visual-only work introduces no functional regressions.

---

## 4. Ask entry point

- [x] Add an `Ask` entry point to the main BerryBrain experience.
- [x] Choose its final placement based on the hierarchy defined in `docs/DESIGN.md`.
- [x] Prefer a visible navbar action when Ask is a global action available from every page.
- [x] Prefer a prominent BrainView action when Ask depends on the current brain context.
- [x] If appropriate, expose both a compact global entry point and a contextual BrainView action without duplicating the experience.
- [x] Use a clear English label, icon and tooltip.
- [x] Define active, hover, focus, loading and unavailable states.
- [x] Ensure Ask opens with the correct active brain and vault context.
- [x] Ensure the action is keyboard accessible.
- [x] Ensure the placement remains usable in responsive layouts.

### Acceptance criteria

- [x] Ask is discoverable from the main BerryBrain experience.
- [x] Its placement follows the product hierarchy instead of appearing as an isolated feature.
- [x] Ask always uses the correct real brain and vault context.

---

## 5. English-only product and codebase

### 5.1 User-facing language

- [x] Audit every visible string in the landing page and BerryBrain application.
- [x] Convert Portuguese, Spanish and mixed-language content to natural English.
- [x] Convert navigation, buttons, labels, placeholders, tooltips and form help text to English.
- [x] Convert loading, empty, success, warning and error states to English.
- [x] Convert validation messages, notifications and toast messages to English.
- [x] Convert email, onboarding and generated-content templates to English where applicable.
- [x] Remove references to unavailable future locales from the current interface.

### 5.2 Prompts

- [x] Perform a dedicated audit of `/prompts`.
- [x] Rewrite every system, user, assistant and tool prompt in English.
- [x] Ensure prompts explicitly produce English brains, titles, summaries, folders, tags and relationships.
- [x] Remove Portuguese or Spanish examples that could influence model output.
- [x] Standardize BerryBrain terminology across all prompts.
- [x] Make prompt output contracts and structured fields use English names.
- [x] Ensure fallback messages and recovery instructions are in English.
- [x] Verify that user-provided non-English source material does not change the product's default organizational language unless a future localization feature explicitly allows it.

### 5.3 Source code and technical identifiers

- [x] Audit component, function, variable, type, interface, enum and file names.
- [x] Rename non-English technical identifiers to clear English names.
- [x] Convert code comments, documentation comments and developer messages to English.
- [x] Convert logs, internal errors and analytics event names to English.
- [x] Convert database-facing labels and generated keys to English where migration safety allows.
- [x] Plan safe migrations for persisted non-English keys instead of silently breaking stored data.
- [x] Keep external protocol fields unchanged when controlled by third-party specifications.

### Acceptance criteria

- [x] All first-party UI text is in English.
- [x] All `/prompts` content and expected outputs are in English.
- [x] All newly generated brains and organizational structures default to English.
- [x] First-party source identifiers, comments and logs are in English.
- [x] No persisted data or external integration is broken by identifier changes.

---

## 6. Mocked and hardcoded data audit

### 6.1 Full-system inventory

- [x] Search the entire codebase for mocks, fixtures, fake data, seed-only content and placeholders used at runtime.
- [x] Audit hardcoded brains, vaults, notes, folders, tags, graph nodes, graph edges and conversations.
- [x] Audit hardcoded user names, avatars, counts, dates, statistics and activity records.
- [x] Audit hardcoded AI responses, summaries, recommendations and relationships.
- [x] Audit hardcoded marketing claims, metrics, testimonials, logos and product screenshots.
- [x] Audit fallback paths that silently display fabricated content after API failures.
- [x] Audit development flags that accidentally enable mock services in production.
- [x] Document each finding with location, runtime impact, intended source and replacement strategy.

### 6.2 Classification

- [x] Distinguish mocked product data from legitimate static configuration.
- [x] Keep only valid constants such as route names, supported file types, limits, design tokens and protocol values.
- [x] Treat sample content as development or test-only data.
- [x] Ensure fixtures cannot be bundled into or activated by the production application.
- [x] Replace runtime mock data with API, database, ingestion or AI-generated data from the real user context.
- [x] Replace fabricated fallbacks with honest loading, empty or error states.

### 6.3 Organic generation

- [x] Ensure brains originate from real user actions, connected sources or ingestion pipelines.
- [x] Ensure vault structures derive from actual content and detected relationships.
- [x] Ensure graph nodes and edges derive from persisted entities and relationships.
- [x] Ensure summaries, labels, tags and recommendations are generated from real content.
- [x] Persist generated results so the interface remains consistent across sessions.
- [x] Track provenance for generated folders, tags and relationships where useful.
- [x] Provide deterministic safeguards around AI output schemas.
- [x] Avoid silently inventing content when source information is insufficient.

### Acceptance criteria

- [x] No mocked or fabricated data appears in production runtime flows.
- [x] Empty accounts display genuine onboarding or empty states.
- [x] Every visible brain, vault, note, relationship and metric has a real source.
- [x] Legitimate configuration constants remain documented and are not incorrectly removed.

---

## 7. Automatic vault organization

### 7.1 Organic folder and subfolder generation

- [x] Automatically analyze vault content for topics and correlations.
- [x] Automatically organize related content into folders and subfolders.
- [x] Generate folder names in English.
- [x] Use semantic relationships rather than filename-only rules.
- [x] Define confidence thresholds before moving or grouping content.
- [x] Avoid creating excessive, shallow or single-item folders.
- [x] Avoid deeply nested or unstable folder trees.
- [x] Merge strongly overlapping topics when appropriate.
- [x] Preserve user-created organization and explicit manual decisions.
- [x] Define how automatic organization behaves after the user manually moves or renames an item.
- [x] Reorganize incrementally when new content is added instead of rebuilding the entire vault unnecessarily.
- [x] Prevent duplicate notes or references during reorganization.
- [x] Keep organization operations recoverable and auditable.

### 7.2 Automatic sidebar colors

- [x] Generate sidebar colors automatically for folders and correlated subjects.
- [x] Use a stable color assignment so colors do not change between sessions.
- [x] Derive colors from folder or topic identity rather than list position.
- [x] Keep related topics visually coherent without making distinct folders indistinguishable.
- [x] Maintain sufficient text and icon contrast.
- [x] Prevent overly saturated, visually noisy or inaccessible combinations.
- [x] Apply the palette and color behavior defined by `docs/DESIGN.md`.

### 7.3 Settings and user control

- [x] Add an `Automatic vault organization` setting.
- [x] Enable `Automatic vault organization` by default for new users and new brains.
- [x] Allow the user to disable and re-enable it at any time.
- [x] Explain in English what the setting changes.
- [x] Define whether disabling stops future organization only or also offers a safe rollback.
- [x] Preserve the user's explicit setting choice across sessions.
- [x] Avoid overwriting an existing user's explicit preference during migration.
- [x] Show organization progress and failures honestly.

### Acceptance criteria

- [x] A new vault is automatically grouped into meaningful folders and subfolders from real content.
- [x] Folder names and generated metadata are in English.
- [x] Sidebar colors are automatic, stable, accessible and tied to real topics.
- [x] Manual user organization is respected.
- [x] The feature starts enabled and can be disabled in Settings.

---

## 8. Default intelligence settings

- [x] Enable `Automatic vault organization` by default.
- [x] Enable `HippoRAG` by default.
- [x] Enable `Judge` by default.
- [x] Allow each setting to be disabled independently.
- [x] Add concise English descriptions explaining the effect of each setting.
- [x] Persist each user's selection.
- [x] Apply defaults only when no prior explicit preference exists.
- [x] Ensure backend behavior matches the visible toggle state.
- [x] Define loading and error behavior when settings cannot be retrieved or saved.
- [x] Verify defaults for new accounts, new brains and migrated existing accounts.

### Default-state matrix

| Setting | Default | User can disable | Persistence required |
| --- | --- | --- | --- |
| Automatic vault organization | Enabled | Yes | Yes |
| HippoRAG | Enabled | Yes | Yes |
| Judge | Enabled | Yes | Yes |

### Acceptance criteria

- [x] All three settings appear enabled for users without a previous preference.
- [x] Each setting can be changed independently.
- [x] A refresh or new session preserves the user's explicit choices.
- [x] The interface and backend never disagree about the active state.

---

## 9. Quality assurance

### Visual regression

- [x] Review the landing page at desktop, tablet and mobile breakpoints.
- [x] Review every BerryBrain page at supported breakpoints.
- [x] Review BrainView and graph states with different data densities.
- [x] Compare shared components across pages for visual consistency.
- [x] Verify dark/light themes if supported.

### Functional regression

- [x] Confirm visual changes do not alter existing functions.
- [x] Test graph hover, click, drag, zoom, pan, reset and focus clearing.
- [x] Test Ask entry point and context propagation.
- [x] Test Settings defaults, updates and persistence.
- [x] Test automatic organization with new and existing vaults.
- [x] Test manual overrides and disable/re-enable flows.

### Language validation

- [x] Search the full repository for Portuguese, Spanish and mixed-language first-party strings.
- [x] Review `/prompts` outputs with representative content.
- [x] Verify all generated brain structures use English by default.
- [x] Verify no locale-specific assumptions remain in dates, labels or templates.

### Data integrity and production readiness

- [x] Verify production builds contain no runtime mocks or fixtures.
- [x] Verify graph data originates from persisted real entities.
- [x] Verify automatic organization never loses or duplicates content.
- [x] Verify settings migrations preserve explicit user choices.
- [x] Measure graph performance with a large vault.
- [x] Check browser console, server logs and network failures.
- [x] Complete accessibility and reduced-motion checks.

---

## 10. Recommended implementation order

- [x] **Phase 1 — Audit and baseline:** map current pages, prompts, language, mock data, settings and graph behavior.
- [x] **Phase 2 — Design foundation:** implement the reusable tokens and components defined by `docs/DESIGN.md`.
- [x] **Phase 3 — BrainView:** establish the primary product hierarchy and polished core states.
- [x] **Phase 4 — Graph:** implement Obsidian-style nodes, edges, focus behavior, physics and entrance motion.
- [x] **Phase 5 — Global UI:** apply the system to all application pages and the landing page.
- [x] **Phase 6 — Ask:** add the primary entry point and validate brain/vault context.
- [x] **Phase 7 — English standardization:** update UI, `/prompts`, source identifiers, logs and generated outputs.
- [x] **Phase 8 — Organic data:** remove runtime mocks and connect every experience to real data sources.
- [x] **Phase 9 — Vault intelligence:** implement automatic folders, subfolders, topic colors and user overrides.
- [x] **Phase 10 — Defaults and migration:** enable Automatic organization, HippoRAG and Judge safely.
- [x] **Phase 11 — Final QA:** complete visual, functional, language, data-integrity, accessibility and performance validation.

---

## Definition of done

- [x] The entire landing page and BerryBrain application follow `docs/DESIGN.md`.
- [x] BrainView has the strongest and clearest product experience.
- [x] The graph has premium Obsidian-inspired nodes, edges and motion.
- [x] Node hover and selection isolate the complete direct connection neighborhood visually.
- [x] Ask is clearly accessible from the main BerryBrain experience.
- [x] All first-party UI, prompts, generated brains and source code are in English.
- [x] No production feature relies on mocked or fabricated runtime data.
- [x] Vaults organize themselves organically into meaningful folders and subfolders.
- [x] Sidebar topic colors are automatic, stable and accessible.
- [x] Automatic vault organization, HippoRAG and Judge start enabled and remain user-configurable.
- [x] Existing functionality remains intact except for the explicitly requested new features.
- [x] Responsive, accessibility, performance and data-integrity checks pass.
