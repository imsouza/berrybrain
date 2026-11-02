---
id: sciref-latchbio-integration-workflow-creation
name: "Scientific Ref: Python Workflow Creation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (latchbio-integration): Python Workflow Creation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "latchbio integration workflow creation"
  - "python workflow creation"
keywords:
  - "latchbio"
  - "integration"
  - "workflow"
  - "creation"
  - "specialized"
  - "scientific"
  - "reference"
  - "python"
---

# Python Workflow Creation

This reference targets `latch==2.77.1`. Check the installed SDK with
`scripts/inspect_latch_sdk.py` before using version-sensitive symbols.

## Mental Model

- A function decorated with `@workflow` defines a graph.
- A function decorated with a task decorator runs in its own containerized task.
- Calling a task inside a workflow creates a node; it does not execute ordinary
  Python at graph-construction time.
- Workflow inputs and outputs must be typed.
- Put file I/O, subprocesses, network calls, secret lookup, and scientific
  computation inside tasks.
- Keep module import time deterministic and free of external side effects.

## Initialize a Project

```bash
latch init my-workflow --template subprocess
```

Current template choices are exposed by `latch init --help`; common choices
include `subprocess`, `conda`, `r`, and `empty`. A project commonly contains a
`wf/` Python package, a `version` file, dependency inputs, and optional
`Dockerfile` and metadata files.

Do not assume a hand-written Dockerfile is required. Registration can generate
one. If a Dockerfile is present at the project root, registration uses it.

## Tasks and Workflows

```python
from latch import small_task, workflow


@small_task
def normalize_name(sample_name: str) -> str:
    return sample_name.strip().replace(" ", "_")


@workflow
def normalize_sample(sample_name: str) -> str:
    """Normalize a sample identifier.

    Replace embedded spaces with underscores.
    """
    return normalize_name(sample_name=sample_name)
```

In SDK 2.77.1, an explicit workflow docstring must contain a newline: the
decorator splits it into a title and description. A one-line docstring raises
`ValueError` during import. Use a multiline docstring, as above, or omit it.

Use keyword arguments for task calls. They make graph wiring explicit and
survive parameter reordering.

### File input and output

`LatchFile` and `LatchDir` remain the most established workflow signature types.
Inputs are staged onto the task machine. Returned values pair a local path with
a remote destination.

```python
from pathlib import Path

from latch import small_task, workflow
from latch.types import LatchFile, LatchOutputDir


@small_task
def count_lines(input_file: LatchFile, output_dir: LatchOutputDir) -> LatchFile:
    source = Path(input_file.local_path)
    destination = Path("/root/line-count.txt")

    with source.open("r", encoding="utf-8") as handle:
        count = sum(1 for _ in handle)
    destination.write_text(f"{count}\n", encoding="utf-8")

    remote_dir = output_dir.remote_path
    if remote_dir is None:
        raise ValueError("output_dir must have a remote Latch path")

    return LatchFile(
        str(destination),
        f"{remote_dir.rstrip('/')}/line-count.txt",
    )


@workflow
def line_count_workflow(
    input_file: LatchFile,
    output_dir: LatchOutputDir,
) -> LatchFile:
    return count_lines(input_file=input_file, output_dir=output_dir)
```

For new imperative remote-path operations, prefer `LPath`; see
`references/data-management.md`. Do not silently replace typed workflow
parameters with plain strings merely to avoid learning the file types.

## Custom Workflow Metadata

Without metadata, the SDK derives a basic interface from the workflow
signature. Add `LatchMetadata` when the form needs deliberate design.

```python
from pathlib import Path

from latch import small_task, workflow
from latch.types import LatchFile
from latch.types.metadata import (
    LatchAuthor,
    LatchMetadata,
    LatchParameter,
    LatchRule,
)


@small_task
def validate_task(reads: LatchFile) -> bool:
    return Path(reads.local_path).stat().st_size > 0


metadata = LatchMetadata(
    display_name="FASTQ Validator",
    author=LatchAuthor(name="Workflow Team"),
    license="MIT",
    repository="https://github.com/example/fastq-validator",
    parameters={
        "reads": LatchParameter(
            display_name="Reads",
            description="Input FASTQ or compressed FASTQ file.",
            rules=[
                LatchRule(
                    regex=r".*\.(fastq|fq)(\.gz)?$",
                    message="Choose a .fastq, .fq, .fastq.gz, or .fq.gz file.",
                )
            ],
        )
    },
)


@workflow(metadata)
def validate_fastq(reads: LatchFile) -> bool:
    return validate_task(reads=reads)
```

Metadata keys must match workflow parameter names. In SDK 2.77.1, the
decorator drops unmatched metadata keys before its mismatch check; a typo can
silently lose labels or rules. Compare the key sets before applying the
decorator instead of relying on an exception.

Although `about_page_path` is documented, SDK 2.77.1 can fail while serializing
its `Path` value. Use `documentation=` and a descriptive workflow docstring
until that defect is fixed.

See `references/ui-and-automation.md` for sections, samplesheets, launch plans,
messages, and result links.

## Parallel Mapping

Use `map_task` when one task should run over a list. Mapping produces a single
map node rather than thousands of graph nodes.

```python
from pathlib import Path

from latch import map_task, small_task, workflow
from latch.types import LatchFile


@small_task
def validate_one(reads: LatchFile) -> bool:
    return Path(reads.local_path).stat().st_size > 0


@workflow
def validate_batch(reads: list[LatchFile]) -> list[bool]:
    return map_task(validate_one)(reads=reads)
```

Map task inputs must line up with the mapped function's parameter names.
Resource overrides are Flyte overrides and should be tested against the
installed SDK.

## Conditional Nodes

Ordinary Python `if` statements cannot branch on task promises. Build a
conditional node:

```python
from latch import create_conditional_section, small_task, workflow


@small_task
def double(value: float) -> float:
    return value * 2


@small_task
def square(value: float) -> float:
    return value**2


@workflow
def transform(value: float) -> float:
    doubled = double(value=value)
    return (
        create_conditional_section("choose-transform")
        .if_(doubled < 0.0)
        .then(double(value=doubled))
        .elif_(doubled > 0.0)
        .then(square(value=doubled))
        .else_()
        .fail("Zero is not accepted")
    )
```

Use `&` and `|` for compound promise expressions. For a task-produced Boolean,
use its promise truth checks rather than Python unary `not`.

## Caching, Retries, and Timeouts

Named task decorators forward Flyte task opt

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

