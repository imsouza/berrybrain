---
id: sci-matlab
name: "Scientific: matlab"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Builds, reviews, migrates, and plans MATLAB or GNU Octave numerical workflows. Use for arrays, tabular/time data, tests, projects, graphics, MAT files, and explicit Python interoperability."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "matlab"
keywords:
  - "matlab"
  - "builds"
  - "reviews"
  - "migrates"
  - "plans"
  - "octave"
---

# MATLAB and GNU Octave

Use this skill to design or review numerical code, migrate MATLAB releases,
prepare reproducible projects, and plan trusted execution. MATLAB and GNU
Octave are distinct products: compatibility is partial, not a license or
behavior guarantee.

## Review scope

Reviewed against current MathWorks R2026b documentation and GNU Octave 11.3.0
sources on 2026-10-01. The bundled Engine planner and MATLAB examples retain
an explicit R2026a baseline. R2026b supports CPython 3.10-3.14; do not reuse
the R2026a Engine package for it. MATLAB/Octave examples are illustrative and
were not executed in this review; the Python helpers have local synthetic tests.
This skill uses local runtime APIs, with no remote service endpoint or API key.

## Product and license gate

- **MATLAB R2026a is proprietary.** Do not assume MATLAB, MATLAB Online, a
  named toolbox, MATLAB Test, MATLAB Compiler, MATLAB Coder, Parallel Computing
  Toolbox, or an add-on is installed, licensed, or available to the user.
- **MATLAB Runtime is not MATLAB.** It runs compatible applications produced
  with MATLAB Compiler; it cannot run arbitrary source or host MATLAB Engine
  for Python. Building artifacts needs the applicable licensed compiler and
  every product used by the source.
- **GNU Octave 11.3.0 is free software under GPLv3+.** Octave packages are not
  MATLAB toolboxes. Similar names do not imply API, numerical, graphics, or
  licensing equivalence.
- Ask which runtime, release, platform, installed products, and license context
  the user actually has. Treat availability as `unknown` until confirmed.

See [Octave compatibility](references/octave-compatibility.md) and
[execution/product boundaries](references/executing-scripts.md).

## Nonnegotiable safety boundary

Never run an untrusted `.m`, `.mlx`, MEX binary, MAT file, project startup or
shutdown action, package installer, or generated artifact. Static review does
not prove safety.

Treat these as execution or code-loading surfaces:

- `eval`, `evalin`, `assignin`, text-derived `feval`, `str2func`, callbacks,
  timers, app callbacks, and dynamically modified paths;
- `system`, `unix`, `dos`, shell escape `!`, Java, .NET, Python (`py.*`,
  `pyrun`, `pyrunfile`), MEX, and native libraries;
- `mex`, `codegen`, MATLAB Compiler, build tasks, package/project startup, and
  generated code;
- `load`, object deserialization (`loadobj`, custom serialization), function
  handles, Java/System objects, and class code reachable from MAT files.

`.mlx` is an opaque archive for this toolkit and MEX is native executable code.
Do not use Python pickle for exchange. Inspect first, isolate when appropriate,
obtain explicit approval, then invoke a user-confirmed executable and license.
Bundled scripts are static or dry-run tools: none launches MATLAB, Octave,
Python Engine, a compiler, or a subprocess.

## Default workflow

1. **Clarify target.** Record MATLAB release or Octave version, OS/architecture,
   base product versus required toolboxes/packages, expected inputs/outputs,
   numerical tolerances, and whether execution is authorized.
2. **Inventory statically.** Scan `.m` files, opaque artifacts, project paths,
   required products, and MAT headers before any runtime loads them.
3. **Choose code form.** Prefer functions with an `arguments` block for
   automation. Use scripts only for controlled orchestration and live scripts
   for reviewed interactive narratives.
4. **Make semantics explicit.** Record shapes, classes, units, missing-value
   rules, indexing, implicit expansion, RNG algorithm/seed, tolerances, and
   output formats.
5. **Test without hidden state.** Keep fixtures synthetic, paths project-local,
   graphics deterministic, and tests independent of base-workspace residue.
6. **Plan execution.** Generate an argv plan, review startup/path effects and
   licenses, and launch only after explicit approval outside these helpers.
7. **Capture provenance.** Hash named inputs/code and record release, products,
   RNG policy, tolerances, and command plan without dumping the environment.

## Language and data checklist

### Scripts, functions, and live scripts

- Scripts share the caller/base workspace and leave variables behind.
  Functions have local workspaces and explicit inputs/outputs.
- Live scripts (`.mlx`) mix code and rich output but are not plain-text
  review artifacts. Export reviewed code to `.m` for static inspection.
- Avoid `clear all`, broad `addpath(genpath(...))`, dependence on `pwd`, global
  variables, and silent name shadowing. Use project roots and `fullfile`.
- Validate sizes, classes, and values in `arguments` blocks. Remember that
  type declarations can convert inputs and size declarations can reshape or
  expand compatible inputs; validators check without converting.
- A main function file should match the main function name. Local functions
  are private to the file; since R2024a they can appear anywhere in a script
  outside conditional contexts.

```matlab
function y = scaleSignal(x, options)
arguments
    x (:,1) double {mustBeFinite}
    options.Scale (1,1) double {mustBeFinite, mustBeNonzero} = 1
end
y = x .* options.Scale;
end
```

Read [programming](references/programming.md).

### Arrays, indexing, and numerics

- MATLAB uses 1-based, column-major indexing. `A(i,j)`, `A(k)`, `A(:,j)`,
  `A{...}`, and `A.(name)` have different semantics.
- `*`, `/`, `\`, and `^` are matrix operations; dotted forms are
  element-wise. Use `A\b`, not `inv(A)*b`.
- After a linear solve, inspect conditioning/rank and a scale-aware residual;
  backslash can continue after a singularity warning, and a small residual alone
  does not establish an accurate solution. For underdetermined systems, state
  whether minimum norm is required (`lsqminnorm`), rather than assuming `A\b`
  returns it. See the [mldivide contract](https://www.mathworks.com/help/matlab/ref/double.mldivide.html).
- Since R2016b, compatible dimensions expand implicitly. Assert intended shape
  before operations that could accidentally form an outer result.
- Preallocate when output size is known, but do not vectorize at the cost of
  huge temporaries or unreadable code. Measure with `timeit` or the profiler.
- Compare floating-point results with domain-chosen absolute and relative
  tolerances, not blanket `==` or a magic multiple of `eps`.
- Pin both random algorithm and seed. Use named `RandStream` substreams for
  independent parallel work; do not use time-based `

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

