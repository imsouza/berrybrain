---
id: sciref-matlab-executing-scripts
name: "Scientific Ref: Command-Line Execution, Products, and Migration"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matlab): Command-Line Execution, Products, and Migration"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matlab executing scripts"
  - "command-line execution, products, and migration"
keywords:
  - "matlab"
  - "executing"
  - "scripts"
  - "specialized"
  - "scientific"
  - "reference"
  - "command"
  - "line"
---

# Command-Line Execution, Products, and Migration

This reference explains reviewed execution plans. Bundled helpers never launch
MATLAB, GNU Octave, MATLAB Engine, MEX, a compiler, or any subprocess.

## Authorization gate

Before execution, confirm all of the following:

1. every `.m` file is trusted and statically reviewed;
2. no unreviewed `.mlx`, `.fig`, `.mlapp`, MEX, MAT object, project action,
   startup file, package, or generated artifact is reachable;
3. inputs and outputs are strict local paths with bounds and overwrite policy;
4. runtime, exact release, architecture, required products, and license are
   confirmed;
5. shell/native/Java/.NET/Python/code-generation surfaces are approved;
6. network, credentials, displays, and external services are understood;
7. the planned argv is shown to the user and execution is explicitly approved.

Static scan findings are not proof of safety. Never execute a file solely to
discover what it does.

## MATLAB R2026a `-batch`

MathWorks recommends `-batch` for noninteractive command-line workflows.
Conceptually, an approved plan looks like:

```text
["matlab", "-batch", "run('/reviewed/project/main.m')"]
```

This is argv, not an instruction to run untrusted code.

Official R2026a behavior:

- starts without the desktop or splash screen;
- executes the quoted statement noninteractively;
- logs text to standard output/error;
- disables settings changes and toolbox caching;
- can display figures unless paired with `-noFigureWindows` or `-nodisplay`;
- exits automatically with code 0 on success and nonzero on failure;
- errors if code requests interactive dialog input (except supported app-test
  fixtures);
- must not be combined with `-r`;
- requires the target to be in the startup folder or on the MATLAB path.

Use `-sd <reviewed-folder>` to set the initial folder. Do not embed untrusted
text in a MATLAB statement. Prefer a fixed function name and JSON-validated
scalar/list arguments converted by the planner.

MATLAB startup still matters. On Linux, the launcher processes
`.matlab7rc.sh`; MATLAB also runs `matlabrc.m` and the first executable
`startup` on its path. `finish.m` can run at normal exit. A MATLAB Project can
add paths and run startup/shutdown actions. `-sd` is not a security sandbox.

`-r` is for interactive workflows and has not been recommended for
noninteractive use since R2019a. Older `-r "...; exit"` patterns are easier to
hang or mask errors.

## Nonexecuting batch planner

```bash
python scripts/plan_batch_command.py matlab script src/main.m --root .
python scripts/plan_batch_command.py matlab function src/analyze.m \
  --root . --arg-json '{"value": 3}'
python scripts/plan_batch_command.py matlab tests tests/TestAnalyze.m --root .
```

The planner:

- validates a single `.m` target under `--root`;
- rejects symlinks, URLs, traversal, `.mlx`, MEX, and oversized paths;
- validates MATLAB identifiers and JSON values;
- returns argv, a MATLAB statement, assumptions, and warnings;
- marks `executes=false`;
- never checks `PATH`, calls a runtime, reads credentials, or spawns a process.

JSON objects become scalar structs, including fields containing empty or
heterogeneous lists; the constructor wraps each field value in a scalar cell
to prevent struct-array expansion. Numeric rectangular lists become numeric
arrays. String lists become MATLAB string arrays or Octave cell arrays of
character vectors; other lists become cells. JSON `null` becomes `[]` and an
empty list becomes `{}`. Octave strings use single quotes with doubled internal
apostrophes, preserving literal backslashes. Review these shapes before use.

## GNU Octave 11.3.0 plans

The current manual documents:

- `--eval`/`-e` to evaluate code and exit;
- a filename argument to execute a script and exit;
- `--no-gui`, `--quiet`, and `--no-history`;
- `--no-init-all`/`--norc` to skip system and user initialization;
- `--path` to add a narrow function path;
- `--no-window-system` to disable graphics entirely.

For deterministic reviewed plans, prefer `--no-init-all --no-history
--quiet --no-gui`. Use `--no-window-system` only when graphics are not needed.
Octave also has site, version, user, local `.octaverc`, and MATLAB-compatible
`startup.m` files; skipping them changes expected user configuration and must
be a conscious choice.

Octave does not implement MATLAB `-batch`, Projects, or
`matlab.unittest`. Its BIST `test` function and `%!test` blocks are different.
Do not use an Octave result as proof that MATLAB code, graphics, toolboxes, or
deployment will behave identically.

## Functions, scripts, and test entry points

For automation:

- prefer a main function with explicit inputs/outputs;
- keep scripts free of base-workspace assumptions;
- avoid current-folder dependence and broad path mutation;
- return status through tests/errors rather than calling `exit` inside library
  code;
- place all output under a reviewed output root;
- do not request interactive input.

R2026a `runtests` automatically opens and closes a project when tests belong
to a project not already open. Review project startup/shutdown behavior before
using it.

Base MATLAB has `matlab.unittest`; parallel execution requires Parallel
Computing Toolbox. Advanced dependency selection, dashboards, generated tests,
coverage/equivalence features can require MATLAB Test or other products.

## Required products and license boundaries

Separate four questions:

1. **Static dependency:** Which products might code reference?
2. **Installation:** Which products/add-ons are installed?
3. **Entitlement:** Which licenses may this user/system use?
4. **Checkout:** Which licenses are available for this run?

`matlab.codetools.requiredFilesAndProducts` and Dependency Analyzer address
the first question imperfectly. `license("inuse")` observes only products used
on executed paths and itself requires launching MATLAB. None grants a license.

Do not automatically install MATLAB or a toolbox. Downloads, installers,
network-license configuration, and unattended automation are governed by the
user's MathWorks account, administrator, and license terms. The R2026a Program
Offering Guide has specific automation-server and external-application terms;
do not paraphrase it as legal permission.

## Compiler and generated-code boundaries

- **MATLAB Compiler** creates standalone/web applications that run with a
  release-compatible MATLAB Runtime.
- **MATLAB Compiler SDK** creates components for external languages.
- **M

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

