---
id: sciref-pi-agent-tui
name: "Scientific Ref: TUI Components"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): TUI Components"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent tui"
  - "tui components"
keywords:
  - "agent"
  - "tui"
  - "specialized"
  - "scientific"
  - "reference"
  - "components"
---

# TUI Components

Source: https://pi.dev/docs/latest/tui

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

Extensions and custom tools render custom terminal UI through `@earendil-works/pi-tui`.

## Component Interface

```ts
interface Component {
  render(width: number): string[];
  handleInput?(data: string): void;
  wantsKeyRelease?: boolean;   // receive key release events (Kitty protocol)
  invalidate(): void;          // clear cached render state; called on theme changes
}
```

Each line from `render(width)` **must not exceed `width`**. The TUI appends a full SGR reset and OSC 8 reset at the end of every rendered line, so styles do not carry across lines — reapply styles per line or use `wrapTextWithAnsi()`.

Width helpers: `visibleWidth(str)` (ignores ANSI), `truncateToWidth(str, width, ellipsis?)`, `wrapTextWithAnsi(str, width)`.

## Focusable and IME

Components that draw a text cursor should implement `Focusable { focused: boolean }`. When focused, the TUI sets `focused = true`, scans output for `CURSOR_MARKER` (a zero-width APC sequence emitted right before the fake cursor), and positions the hardware cursor there. The cursor stays hidden by default; some terminals need it visible for IME candidate windows — enable with `showHardwareCursor`, `setShowHardwareCursor(true)`, or `PI_HARDWARE_CURSOR=1`. The built-in `Editor` and `Input` already implement this.

Container components (dialogs, selectors) that embed an `Input`/`Editor` must implement `Focusable` and propagate `focused` to the child, or IME candidate windows appear in the wrong place.

## Usage

```ts
const result = await ctx.ui.custom<string | null>((tui, theme, keybindings, done) =>
  new MyComponent({ theme, keybindings, onChange: () => tui.requestRender(), onSelect: done, onCancel: () => done(null) })
);
```

The same call works inside a custom tool's `execute(toolCallId, params, signal, onUpdate, ctx)`. Returning a plain `{ render, invalidate, handleInput }` object is also fine.

## Overlays

Pass `{ overlay: true }` to render on top of existing content without clearing the screen. `overlayOptions` controls layout:

- Size: `width`, `minWidth`, `maxHeight` (numbers or percentage strings)
- Position: `anchor` (9 positions, default `"center"`), `offsetX`/`offsetY`, or `row`/`col`
- Margins: `margin` (number or `{ top, right, bottom, left }`)
- Responsive: `visible(termWidth, termHeight)`

`onHandle: (handle) => …` gives `focus()` (focus and bring to front), `unfocus()` (release input to the normal fallback), `unfocus({ target })` (hand input to a specific component, or `null` for none), `setHidden(true|false)`, and `hide()` (permanent removal).

A focused visible overlay keeps input ownership across temporary non-overlay UI and can reclaim input when that UI closes. Overlay components are disposed when closed — never reuse a reference; call the show function again to re-show.

## Built-in Components

Import from `@earendil-works/pi-tui`: `Text` (multi-line with word wrapping, `new Text(content, paddingX, paddingY, bgFn?)`, `setText()`), `Box` (padding + background, `addChild`, `setBgFn`), `Container` (vertical grouping, `addChild`/`removeChild`/`clear`), `Spacer(lines)`, `Markdown(text, paddingX, paddingY, theme)`, `Image(base64, mimeType, theme, { maxWidthCells, maxHeightCells })` (Kitty, iTerm2, Ghostty, WezTerm, Warp), `SelectList(items, visibleCount, theme)` with `SelectItem { value, label, description? }`, `SettingsList(items, visibleCount, theme, onChange, onClose, { enableSearch })` with `SettingItem { id, label, currentValue, values }`, plus `AutocompleteItem` types.

From `@earendil-works/pi-coding-agent`: `DynamicBorder`, `BorderedLoader` (spinner + abort signal + `onAbort`), `CustomEditor`, `getMarkdownTheme()`, `getSettingsListTheme()`, `keyHint`/`keyText`/`rawKeyHint`, `highlightCode`, `getLanguageFromPath`.

## Keyboard Input

```ts
import { matchesKey, Key } from "@earendil-works/pi-tui";

if (matchesKey(data, Key.up)) { /* ... */ }
if (matchesKey(data, Key.ctrl("c"))) { /* ... */ }
```

`Key.enter`, `Key.escape`, `Key.tab`, `Key.space`, `Key.backspace`, `Key.delete`, `Key.home`, `Key.end`, arrows, and modifier helpers `Key.ctrl`, `Key.shift`, `Key.alt`, `Key.ctrlShift`. String literals (`"enter"`, `"ctrl+c"`, `"shift+tab"`) also work.

## Theming

Use the `theme` passed into the callback or renderer — never import a global theme. `theme.fg(color, text)` covers general (`text`, `accent`, `muted`, `dim`, `searchMatchText`), status (`success`, `error`, `warning`), borders (`border`, `borderAccent`, `borderMuted`), messages (`userMessageText`, `customMessageText`, `customMessageLabel`), tools (`toolTitle`, `toolOutput`), diffs (`toolDiffAdded`/`Removed`/`Context`), markdown (`md*`), syntax (`syntax*`), thinking levels (`thinkingOff`…`thinkingMax`), and `bashMode`. `theme.bg(color, text)` covers `selectedBg`, `searchMatchBg`, `userMessageBg`, `customMessageBg`, `toolPendingBg`, `toolSuccessBg`, `toolErrorBg`. Text styles: `theme.bold`, `theme.italic`, `theme.strikethrough`; `theme.style()` composes styles, `theme.colors` exposes resolved colors, and `theme.appearance` reports light/dark.

Components that pre-bake theme colors into cached strings must rebuild that content in `invalidate()` — clearing a render cache is not enough. This applies to `theme.fg`/`theme.bg` strings stored in child components, `highlightCode()` output, and child trees that embed colors. It is unnecessary when you pass theme callbacks that run at render time, for simple containers, or for stateless render.

## Common Patterns

1. **Selection dialog** — `SelectList` framed with `DynamicBorder`, `onSelect`/`onCancel` calling `done`.
2. **Async with cancel** — `BorderedLoader(tui, theme, "Fetching…")`, pass `loader.signal` to the async work, `loader.onAbort = () => done(null)`.
3. **Settings toggles** — `SettingsList` with `getSettingsListTheme()`.
4. **Persistent status** — `ctx.ui.setStatus("my-ext", text)`; clear with `undefined`.
5. **Working indicator** — `ctx.ui.setWorkingIndicator({ frames, intervalMs })`; `{ frames: [] }` hides it, no argument restores the default spinner. Frames render verbatim, so add colors yourself. Compaction and retry loaders keep built-in styling. `setWorkingMessage()` and `setWorkingVisible()` control the loader row.
6. **Widgets** — `ctx.ui.setWidget(key, lines | factory, { placement: "aboveEditor" | "belowEditor" })`; `undefined` clears.
7. **Custo

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

