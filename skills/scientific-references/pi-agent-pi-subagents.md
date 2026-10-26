---
id: sciref-pi-agent-pi-subagents
name: "Scientific Ref: pi-subagents Package"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pi-agent): pi-subagents Package"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "agent subagents"
  - "pi-subagents package"
keywords:
  - "agent"
  - "subagents"
  - "specialized"
  - "scientific"
  - "reference"
  - "package"
---

# pi-subagents Package

Source: https://pi.dev/packages/pi-subagents (docs: `https://github.com/nicobailon/pi-subagents/tree/main/docs`)

Reviewed against Pi 0.99.2 and the package versions listed in `../SKILL.md` on 2026-09-30.

Delegate work to focused child Pi sessions: code review, scouting, implementation, parallel audits, saved workflows, background jobs. Installing the extension does not start anything automatically — it supplies `subagent` and, on models supporting dynamic tool additions, a small `subagents_enable` loader. Version 0.74.0 requires Pi 0.86.1+; this review used Pi 0.99.2. `toolActivation` is `auto` by default, or `dynamic`/`eager`.

```bash
pi install npm:pi-subagents
```

Users normally ask in plain language ("Use reviewer to review this diff", "Run parallel reviewers for correctness, tests, and complexity"). Pi decides whether to call the tool, which agent to use, and how to compose the work.

## Built-in Agents

| Agent | Purpose |
|---|---|
| `scout` | Fast local codebase recon: relevant files, entry points, data flow, risks, where to start |
| `researcher` | Web/docs research with sources; needs `pi-web-access` for `web_search`/`fetch_content`/`get_search_content` |
| `worker` | Implementation, including approved oracle handoffs; escalates unapproved decisions |
| `reviewer` | Code review and small fixes against task/plan, tests, edge cases, simplicity |
| `oracle` (alias `advisor`) | Second opinion before acting; challenges assumptions, no edits |
| `delegate` | Lightweight general delegate close to parent behavior (append prompt mode) |

Builtins load at the lowest priority and inherit the current Pi default model unless `subagents.defaultModel` or an override says otherwise. Packaged `worker` defaults to fresh context; `oracle` and `advisor` prefer fork context, falling back to fresh only when that implicit preference cannot use a persisted parent leaf. Builtins opt into project-instruction inheritance so they follow repo rules.

Recommended implementation loop: **clarify → scout → worker → fresh reviewers → worker**.

## Execution in 0.74.0

For one child, call `subagent({ agent: "scout", task: "Analyze the auth flow" })`. For composition, write exactly one `js workflow` fenced block in the same assistant reply as one `subagent({ workflow: true })` call:

```js workflow
const scan = await runs.run("scan", { agent: "scout", task: "Analyze auth" });
const reviews = await runs.all([
  { key: "correctness", agent: "reviewer", task: "Review correctness: " + scan.output },
  { key: "tests", agent: "reviewer", task: "Review tests: " + scan.output }
]);
return reviews.map(r => r.output);
```

```javascript
subagent({ workflow: true })
```

`workflow: "./workflows/review.js"` loads a file relative to `cwd`; a string without a path separator resolves a named resource such as `review` or `run-ci`. `workflowScript` and `workflowScriptPath` were **removed**. RPC spawn uses `script` for inline text and `workflow` for a path/resource. Validate without launching with `{ action: "validate", workflow: "./workflows/review.js" }`.

Scripts are JavaScript statement bodies with top-level await and explicit return. Globals include `runs.run`, `runs.all` (ordered array result), `runs.lanes`, `runs.steer`, `runs.status`, `runs.ref`/`refs`, `emit`, `console`, frozen JSON `args`, `state.get/set` for missions, and `prompts.render`. Nested async functions/arrows/methods are rejected for Node/Bun portability. Observe every launched child promise; never read `.output` from an unawaited launch. The sandbox has no filesystem, shell, or arbitrary Pi tools. Only authorized named resources may expose `runs.host`.

Workflows normally run in the background. `async: false` watches in the foreground; composite workflows have no default parent deadline. Set a finite `timeoutMs` when required (maximum 2,147,483,647ms). Explicit child `async: true` returns a **launch receipt** with `ok: false`, `state: "running"`, and empty output; it does not await successful completion. Omit child `async` to await its final result.

`prompts.render` uses `package:<name>`, `user:<name>`, or `project:<name>` for a top-level Markdown prompt, strips frontmatter, and substitutes scalar `{{name}}` values. Pass its returned text as the child's task.

### Key Tool Parameters

`agent`, `action`, `topic`, `config`, `context` (`fresh`/`fork`/`profile` — an explicit value overrides every workflow child; otherwise global `defaultSubagentContext` precedes each child's `defaultContext`), `missionId`, `mission` (object or `false`), `handoffPath`, `view` (`fleet`/`transcript`), `lines` (default 80, max 500), `agentScope`, `async`, `chatProgress`, `timeoutMs`/`maxRuntimeMs`, `toolTimeoutMs`, `turnBudget`, `toolBudget`, `usageBudget`, `cwd`, `maxOutput` (200 KB / 5000 lines), `artifacts`, `includeProgress`, `share`, `sessionDir`, `acceptance`, `gate`, plus per-item `output`, `outputMode`, `skill`, `model`, `worktree`, `resume`.

Budgets: `turnBudget` is `{ maxTurns, graceTurns }` (warn at `maxTurns`, terminate at the next assistant boundary after the grace window); `toolBudget` is `{ soft?, hard, block? }` (block defaults to `read`/`grep`/`find`/`ls`; `"*"` blocks everything, final assistant text never blocked); `usageBudget` is root-only `{ tokens?: { soft?, hard }, costUsd?: { soft?, hard } }` where soft limits are status-only and hard limits prevent later child launches without stopping running ones. **Do not** set turn, hard tool, or tight usage budgets on mutation-capable children (implementation workers, fix workers, reviewers with edit authority) — none of those measure whether a delivery slice is buildable, and a default tool budget blocks read/search tools rather than mutations. Bound writers with a narrow task and an outer `timeoutMs` instead, and request a checkpoint via `steer` before the deadline.

`context: "fork"` fails fast when the parent session is not persisted, the leaf is missing, or the branched session cannot be created — it never silently downgrades to `fresh`. Forking strips signed Anthropic `thinking`/`redacted_thinking` replay blocks; the child keeps its requested thinking level and reasons afresh. Implicit global/profile fork preferences may fall back to fresh when there is no persisted parent leaf; an explicit fork request never silently downgrades.

`outputMode: "file-only"` returns a compact pointer (`Output saved to: /abs/report.md (48.2 KB, 2847 lines)…`) instead of inline text; failed runs

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

