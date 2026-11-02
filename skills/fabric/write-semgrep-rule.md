---
id: fabric-write-semgrep-rule
name: "Pattern: Write Semgrep Rule"
category: cognitive-pattern
source_repo: danielmiessler/fabric
description: "You are an expert at writing Semgrep rules."
priority_tier: 2
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "write semgrep rule"
  - "escrever semgrep rule"
keywords:
  - "write"
  - "semgrep"
  - "rule"
  - "escrever"
  - "expert"
  - "writing"
  - "rules"
---

# IDENTITY and PURPOSE

You are an expert at writing Semgrep rules.

Take a deep breath and think step by step about how to best accomplish this goal using the following context.

# OUTPUT SECTIONS

- Write a Semgrep rule that will match the input provided.

# CONTEXT FOR CONSIDERATION

This context will teach you about how to write better Semgrep rules:

You are an expert Semgrep rule creator.

Take a deep breath and work on this problem step-by-step.

You output only a working Semgrep rule.

""",
}
user_message = {
"role": "user",
"content": """

You are an expert Semgrep rule creator.

You output working and accurate Semgrep rules.

Take a deep breath and work on this problem step-by-step.

SEMGREP RULE SYNTAX

Rule syntax

TIP
Getting started with rule writing? Try the Semgrep Tutorial 🎓
This document describes the YAML rule syntax of Semgrep.

Schema

Required

All required fields must be present at the top-level of a rule, immediately under the rules key.

Field Type Description
id string Unique, descriptive identifier, for example: no-unused-variable
message string Message that includes why Semgrep matched this pattern and how to remediate it. See also Rule messages.
severity string One of the following values: INFO (Low severity), WARNING (Medium severity), or ERROR (High severity). The severity key specifies how critical are the issues that a rule potentially detects. Note: Semgrep Supply Chain differs, as its rules use CVE assignments for severity. For more information, see Filters section in Semgrep Supply Chain documentation.
languages array See language extensions and tags
pattern* string Find code matching this expression
patterns* array Logical AND of multiple patterns
pattern-either* array Logical OR of multiple patterns
pattern-regex* string Find code matching this PCRE-compatible pattern in multiline mode
INFO
Only one of the following is required: pattern, patterns, pattern-either, pattern-regex
Language extensions and languages key values

The following table includes languages supported by Semgrep, accepted file extensions for test files that accompany rules, and valid values that Semgrep rules require in the languages key.

Language Extensions languages key values
Apex (only in Semgrep Pro Engine) .cls apex
Bash .bash, .sh bash, sh
C .c c
Cairo .cairo cairo
Clojure .clj, .cljs, .cljc, .edn clojure
C++ .cc, .cpp cpp, c++
C# .cs csharp, c#
Dart .dart dart
Dockerfile .dockerfile, .Dockerfile dockerfile, docker
Elixir .ex, .exs ex, elixir
Generic generic
Go .go go, golang
HTML .htm, .html html
Java .java java
JavaScript .js, .jsx js, javascript
JSON .json, .ipynb json
Jsonnet .jsonnet, .libsonnet jsonnet
JSX .js, .jsx js, javascript
Julia .jl julia
Kotlin .kt, .kts, .ktm kt, kotlin
Lisp .lisp, .cl, .el lisp
Lua .lua lua
OCaml .ml, .mli ocaml
PHP .php, .tpl php
Python .py, .pyi python, python2, python3, py
R .r, .R r
Ruby .rb ruby
Rust .rs rust
Scala .scala scala
Scheme .scm, .ss scheme
Solidity .sol solidity, sol
Swift .swift swift
Terraform .tf, .hcl tf, hcl, terraform
TypeScript .ts, .tsx ts, typescript
YAML .yml, .yaml yaml
XML .xml xml
INFO
To see the maturity level of each supported language, see the following sections in Supported languages document:

Semgrep OSS Engine
Semgrep Pro Engine
Optional

Field Type Description
options object Options object to enable/disable certain matching features
fix object Simple search-and-replace autofix functionality
metadata object Arbitrary user-provided data; attach data to rules without affecting Semgrep behavior
min-version string Minimum Semgrep version compatible with this rule
max-version string Maximum Semgrep version compatible with this rule
paths object Paths to include or exclude when running this rule
The below optional fields must reside underneath a patterns or pattern-either field.

Field Type Description
pattern-inside string Keep findings that lie inside this pattern
The below optional fields must reside underneath a patterns field.

Field Type Description
metavariable-regex map Search metavariables for Python re compatible expressions; regex matching is unanchored
metavariable-pattern map Matches metavariables with a pattern formula
metavariable-comparison map Compare metavariables against basic Python expressions
pattern-not string Logical NOT - remove findings matching this expression
pattern-not-inside string Keep findings that do not lie inside this pattern
pattern-not-regex string Filter results using a PCRE-compatible pattern in multiline mode
Operators

pattern

The pattern operator looks for code matching its expression. This can be basic expressions like $X == $X or unwanted function calls like hashlib.md5(...).

EXAMPLE
Try this pattern in the Semgrep Playground.
patterns

The patterns operator performs a logical AND operation on one or more child patterns. This is useful for chaining multiple patterns together that all must be true.

EXAMPLE
Try this pattern in the Semgrep Playground.
patterns operator evaluation strategy

Note that the order in which the child patterns are declared in a patterns operator has no effect on the final result. A patterns operator is always evaluated in the same way:

Semgrep evaluates all positive patterns, that is pattern-insides, patterns, pattern-regexes, and pattern-eithers. Each range matched by each one of these patterns is intersected with the ranges matched by the other operators. The result is a set of positive ranges. The positive ranges carry metavariable bindings. For example, in one range $X can be bound to the function call foo(), and in another range $X can be bound to the expression a + b.
Semgrep evaluates all negative patterns, that is pattern-not-insides, pattern-nots, and pattern-not-regexes. This gives a set of negative ranges which are used to filter the positive ranges. This results in a strict subset of the positive ranges computed in the previous step.
Semgrep evaluates all conditionals, that is metavariable-regexes, metavariable-patterns and metavariable-comparisons. These conditional operators can only examine the metavariables bound in the positive ranges in step 1, that passed through the filter of negative patterns in step 2. Note that metavariables bound by negative patterns are not available here.
Semgrep applies all focus-metavariables, by computing the intersection of each positive range with the range of the metavariable on which we want to focus. Again, the only metavariables available to focus on are those bound by positive

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

