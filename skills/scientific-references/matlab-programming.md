---
id: sciref-matlab-programming
name: "Scientific Ref: Programming, Projects, Analysis, and Tests"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matlab): Programming, Projects, Analysis, and Tests"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matlab programming"
  - "programming, projects, analysis, and tests"
keywords:
  - "matlab"
  - "programming"
  - "specialized"
  - "scientific"
  - "reference"
  - "projects"
---

# Programming, Projects, Analysis, and Tests

This reference targets MATLAB R2026a. Base MATLAB, separately licensed
products, and GNU Octave must not be conflated.

## Choose the right code artifact

| Artifact | Workspace | Best use | Main risk |
|---|---|---|---|
| script `.m` | caller/base workspace | small reviewed orchestration | hidden inputs, leaked variables, path/state dependence |
| function `.m` | local workspace | reusable computation and automation | implicit conversions or undocumented side effects |
| live script `.mlx` | script-like interactive workspace | narrative exploration and teaching | opaque archive, embedded output, weak text review |
| class `.m` | object state and methods | durable abstractions | constructors, listeners, serialization callbacks |
| MEX | native process code | approved performance/interface work | arbitrary native execution |

Prefer a function with explicit inputs, outputs, and an `arguments` block.
Keep a top-level script thin. Export reviewed live code to plain `.m` before
static inspection. Never open or run an untrusted project, live script, app,
class, MEX file, or package.

Scripts share the base workspace and leave variables there. Functions,
including local functions, have private workspaces. Since R2024a, local
functions in scripts can appear anywhere in the file except inside conditional
contexts. The main function should match its filename.

```matlab
function summary = summarizeSignal(signal, options)
%SUMMARIZESIGNAL Return deterministic summary statistics.
arguments
    signal (:,1) double {mustBeFinite}
    options.Center (1,1) logical = true
end

if options.Center
    signal = signal - mean(signal);
end
summary = struct( ...
    "Count", numel(signal), ...
    "Mean", mean(signal), ...
    "StandardDeviation", std(signal));
end
```

### Argument validation details

- A size declaration such as `(:,1)` permits a column of any height.
- Size declarations also reshape compatible vectors or expand scalars. If
  orientation must be rejected rather than normalized, use a validator such
  as `mustBeColumn` without a size declaration that reshapes first.
- A class declaration can convert compatible input. Do not mistake conversion
  for validation.
- Validators such as `mustBeFinite` check values without changing them.
- A default makes an argument optional. Required positional inputs precede
  optional inputs.
- Name-value inputs use a structure name in the signature and dotted fields in
  the block.
- `namelengthmax` is 2048 from R2025a onward; filesystem limits can be shorter.
  The bundled static helpers intentionally retain a 63-character subset.
- Code generation support is a MATLAB Coder capability with additional
  restrictions and a separate license; an `arguments` block alone does not
  make code generation available.

## Workspace and path hygiene

1. Derive files from a confirmed project root, not the user's incidental
   current folder.
2. Use `fullfile`; never construct paths by concatenating separators.
3. Add the narrowest reviewed directory. Avoid broad `genpath` because it can
   expose hidden, generated, test, private, or malicious files.
4. Do not silently mutate `path`, `userpath`, preferences, startup files, or
   Java/native search paths.
5. Avoid `global`, `persistent` cache state without invalidation, and broad
   clearing. `clear all` can clear loaded functions and disrupt debugging.
6. Use `onCleanup` for resources such as files and temporary state.
7. Pass loaded data through a structure (`S = load(...)`) rather than injecting
   names into a function or base workspace—but only after the MAT file is
   trusted.

MATLAB runs `startup.m` when it is found on the search path and `finish.m` on
normal exit. Projects can add paths and run startup/shutdown actions. Review all
of these before execution.

## Dynamic and external execution surfaces

Escalate any use of:

- `eval`, `evalin`, `assignin`, `str2func`, text-derived `feval`, dynamic
  property or callback names;
- shell entry points (`system`, `unix`, `dos`, `!`);
- Java class paths/methods, .NET assemblies, Python (`py.*`, `pyrun`,
  `pyrunfile`), MEX, C/C++ libraries, and generated code;
- timers, UI callbacks, listeners, project tasks, build tasks, package startup,
  and test fixtures with external effects;
- object loading (`loadobj`, `matlab.mixin.CustomElementSerialization`) and
  System object load hooks.

Function handles are safer than text dispatch only when the handle itself comes
from trusted code. Never pass untrusted text into a dispatch mechanism. Static
scanning is triage, not proof of absence.

## MATLAB Projects

A project can track files, control the path, declare references and packages,
run startup/shutdown tasks, integrate source control, and analyze dependencies.
Use project APIs only after reviewing project metadata and tasks.

Recommended project record:

- project name and root;
- MATLAB release and architecture;
- entry points and test roots;
- required and optional MathWorks products, each with license status
  `unknown`, `confirmed`, or `unavailable`;
- external system dependencies and generated artifacts;
- startup/shutdown actions and path changes;
- RNG/tolerance/data-schema policy.

Dependency Analyzer and `matlab.codetools.requiredFilesAndProducts` use static
analysis. Dynamic dispatch, overloaded methods, callbacks, generated names, and
conditional paths can cause misses or false positives. Their product lists do
not prove that a license can be checked out.

## Code Analyzer and compatibility checks

Use these only on trusted text:

- `codeIssues(path)` returns a structured Code Analyzer result and supports
  programmatic fixes for eligible issues.
- `checkcode(path)` remains useful for text-oriented or legacy automation.
- `codeCompatibilityReport(path)` finds potential issues after a release
  upgrade.
- Project Upgrade can check and apply some release migrations and produce a
  report.

Do not auto-apply fixes across a scientific codebase without tests. Analyzer
silence does not establish numerical correctness, security, toolbox
availability, or Octave compatibility.

Migration sequence:

1. Freeze representative outputs and tolerance rationale in the old release.
2. Record release, products, compilers, BLAS/threading context, RNG algorithm
   and seed, and external data schema.
3. Run static compatibility and dependency analysis.
4. Read every relevant product's release notes and bug reports.
5. Migrate shared

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

