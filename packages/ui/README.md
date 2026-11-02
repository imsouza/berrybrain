# UI Design System Contract

BerryBrain visual tokens, accessibility primitives, and interaction conventions implemented across `apps/web/src/`.

## Design & Accessibility Rules

- **Warm Editorial Surface Tokens**: Uses BerryBrain's semantic CSS custom properties (`bg-background`, `bg-surface`, `bg-panel`, `text-foreground`, `text-muted`, `border-border`, `text-accent`, `bb-card`, `bb-pill`, `bb-button`, `bb-action`) across light and dark themes.
- **Ontology Visual Semantics**: Every graph node class has exclusive geometry (not color alone); canonical note roots use Berry red, insights use highlighted rectangles, and provisional status uses a dedicated neutral channel rather than overloading cluster colors.
- **WCAG 2.2 AA Gate**: Visible `:focus-visible` keyboard outlines, strict contrast compliance, zero layout shift (`CLS`), and `prefers-reduced-motion: reduce` support verified continuously by `apps/web/e2e/accessibility.spec.ts` and `performance.spec.ts`.
