---
id: sciref-matlab-octave-compatibility
name: "Scientific Ref: GNU Octave 11.3.0 Compatibility"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matlab): GNU Octave 11.3.0 Compatibility"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matlab octave compatibility"
  - "gnu octave 11.3.0 compatibility"
keywords:
  - "matlab"
  - "octave"
  - "compatibility"
  - "specialized"
  - "scientific"
  - "reference"
---

# GNU Octave 11.3.0 Compatibility

GNU Octave 11.3.0 is the current stable release as of 2026-10-01 (released
2026-06-01). It is free software under GPLv3+. MATLAB R2026a is proprietary.
Do not describe Octave as MATLAB, a licensed toolbox substitute, or a
drop-in guarantee.

## Compatibility policy

Use three labels:

- **portable subset**: tested in both exact target versions;
- **MATLAB-only**: depends on MATLAB syntax, objects, projects, products, or
  deployment;
- **Octave-only**: uses Octave syntax, packages, BIST, or runtime behavior.

Source resemblance is not enough. Compare outputs with scientific tolerances,
edge cases, warnings, graphics, performance, and file round trips.

## Current release changes

Octave 11 introduced improved `classdef` support, broadcasting for sparse,
diagonal, and permutation matrices, more MATLAB-compatible `nanflag`/`vecdim`
behavior, and many function/performance changes. It is still not fully
compatible. NEWS-11 also records behavior changes that can break older Octave
code, including stricter accepted types for several statistics functions.

Read both the current manual and NEWS before migrating to 11.3.0. The online
`latest` manual reviewed on this date identifies its generated content as
11.1.0 while the project download/news page identifies 11.3.0 as current;
consult NEWS-11 for the maintenance-release delta.

## Command-line differences

Reviewed Octave argv usually includes:

```text
["octave", "--no-init-all", "--no-history", "--quiet", "--no-gui", "main.m"]
```

The bundled planner returns argv but never executes it.

Current manual behavior:

- `--eval`/`-e` evaluates code and exits unless `--persist` is set;
- a filename executes and exits;
- `--no-gui` selects CLI;
- `--no-window-system` disables graphics/window-system use;
- `--no-init-all`/`--norc` skips system and user initialization;
- `--path` adds a function path;
- `--quiet` suppresses greeting; `--no-history` avoids history writes.

Octave startup can execute site/version files, user configuration,
project-local `.octaverc`, and MATLAB-compatible `startup.m`. Skipping all
startup files can improve reproducibility but can also remove expected package
or path setup. Review the plan.

MATLAB uses `-batch`, has different startup processing, and has no Octave
`--no-init-all` option. Never pass the same flags to both.

## Syntax: portable versus Octave-only

Prefer:

- `%` comments;
- `...` continuation;
- `end` block terminators;
- explicit `x = x + 1`;
- intermediate variables before indexing a function result;
- short-circuit `&&`/`||` for scalar conditions;
- ordinary `.m` functions with matching filenames.

Avoid these Octave-only extensions in portable code:

- `#` comments;
- `endif`, `endfor`, `endfunction`;
- `++`, `--`, `+=`, and related compound assignment;
- `do ... until`;
- indexing directly into an expression result;
- backslash line continuation;
- Octave package/BIST directives in MATLAB production files unless isolated.

Both support implicit expansion/broadcasting in many modern cases, but special
classes and edge cases differ. Octave 11 expanded broadcasting for special
matrix types. Test orientation, sparse output, empty dimensions, and mixed
classes in both.

## MATLAB features with no assumed Octave equivalent

The current Octave manual does not establish drop-in equivalents for:

- MATLAB `arguments` blocks and all validators/name-value semantics;
- `table`/`timetable` workflows and their R2026a JSON conversions;
- MATLAB Projects, dependency analyzer, Project Upgrade, or project-aware
  `runtests`;
- `matlab.unittest`, MATLAB Test, Code Quality Dashboard;
- live scripts `.mlx`, App Designer `.mlapp`, `.fig` object compatibility;
- Simulink and MathWorks toolbox APIs;
- MATLAB Engine API for Python, MATLAB Compiler/Runtime, MATLAB Coder, or
  MathWorks deployment products;
- full MATLAB `classdef`, events/listeners, serialization, and metaclass
  behavior.

Use feature detection and separate adapters only after testing. Do not silently
replace a missing MATLAB toolbox function with a similarly named Octave
package function.

## Packages versus toolboxes

Octave packages are distributed separately from core Octave. MATLAB toolboxes
are separately licensed MathWorks products. APIs, algorithms, defaults,
validation, object models, and release schedules differ.

Never run `pkg install`, load an untrusted package, or alter `.octaverc`
automatically. Package installation can fetch/build/execute code. Record exact
package name/version/source/checksum and obtain approval.

`pkg load` mutates the function path and can shadow core or project functions.
Test `which`/resolution only in a trusted approved runtime.

## Tests

Octave's built-in self-test system scans `%!` blocks and uses `test`. It is not
`matlab.unittest`.

```matlab
%!test
%! observed = hypot(3, 4);
%! assert(observed, 5, 1e-12);
```

Portable production functions and runtime-specific test harnesses should be
separate when test syntax differs. The nonexecuting planner can prepare an
Octave BIST argv, but an approved runtime is required to run it.

## MAT and HDF5 compatibility

Octave 11 supports writing MATLAB v4, v6, and v7 binary formats. It **does not
implement saving MATLAB v7.3**.

Octave can save its own HDF5 representation when built with HDF5. Its `load
-hdf5` has limited ability to read MATLAB v7.3, mainly for supported numeric
content; many types are unsupported. An Octave HDF5 file is not automatically
a MATLAB v7.3 file.

Octave's current manual states that `classdef` objects are saved as structures
in supporting formats and are not restored as `classdef` objects. This differs
substantially from MATLAB object serialization.

Never load untrusted MAT/HDF5 files in either runtime. Use the bundled bounded
technical inventory first, then escalate object/opaque/function/external-link
content.

For portable simple data, use MATLAB v7 only after testing classes, shapes,
text, sparse/complex values, and metadata. Prefer schema-documented
language-neutral formats where feasible.

## Graphics

Basic calls such as `plot`, labels, legends, images, surfaces, and `print` are
similar, but renderers, fonts, properties, layout, transparency, callbacks,
and export formats differ.

Do not assume Octave implements R2026a `exportgraphics`, SVG/HTML web canvas,
`tiledlayout`, UI objects, or property behavior. Build a small compatibility
test and compare exported dimensions, font embedding, vector/raster c

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

