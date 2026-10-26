---
id: sciref-dnanexus-integration-job-execution
name: "Scientific Ref: Jobs, Analyses, and Execution"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dnanexus-integration): Jobs, Analyses, and Execution"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dnanexus integration job execution"
  - "jobs, analyses, and execution"
keywords:
  - "dnanexus"
  - "integration"
  - "job"
  - "execution"
  - "specialized"
  - "scientific"
  - "reference"
  - "jobs"
---

# Jobs, Analyses, and Execution

## Quick Navigation

- [Concepts and preflight](#concepts)
- [Launch apps/applets](#launch-an-app-or-applet)
- [Launch workflows](#launch-a-workflow)
- [Lifecycle and monitoring](#lifecycle)
- [Safe waits and outputs](#wait-safely-with-dxpy)
- [Subjobs and reuse](#scattergather-with-subjobs)
- [Instances and restarts](#instance-selection)
- [Cost controls](#cost-controls)
- [Failure triage](#failure-triage)
- [Rerun and termination](#rerun)

## Concepts

- **Job** (`job-...`): execution of one app or applet entry point.
- **Analysis** (`analysis-...`): execution of a workflow and its stages.
- **Origin execution**: user-initiated root of an execution tree.
- **Master job**: app/applet run with its own temporary workspace.
- **Subjob**: another entry point created with `/job/new`; normally shares its
  parent job's workspace.
- **Job-based object reference (JBOR)**: dependency on a field of another
  execution's future output.

Do not treat `analysis-...` as a job. Use `DXAnalysis` and
`find_analyses()` for workflow runs.

## Preflight for a Launch

Before a billable run:

1. Resolve executable to an immutable ID/version.
2. Inspect current input names and types.
3. Resolve every data path to a project-qualified link.
4. Confirm output project/folder.
5. Confirm billing entity and available permission.
6. Review instance/resource policy.
7. Review job reuse and forced reruns.
8. Set an appropriate timeout and cost limit.
9. Confirm tags/properties contain no sensitive values.
10. Obtain user approval unless the exact run was already requested.

Inspect CLI inputs:

```bash
dx run "applet-xxxx" -h
dx pwd
```

## Launch an App or Applet

Interactive confirmation is safest:

```bash
dx run "applet-xxxx" \
  --input-json-file "inputs.json" \
  --destination "project-xxxx:/runs/run-001" \
  --cost-limit 25
```

Use `--yes` only after automation has resolved and validated all targets.

With dxpy:

```python
import dxpy

job = dxpy.DXApplet(
    "applet-xxxx",
    project="project-xxxx",
).run(
    {
        "reads": dxpy.dxlink(
            "file-xxxx",
            "project-xxxx",
        ),
        "min_quality": 20,
    },
    project="project-xxxx",
    folder="/runs/run-001",
    name="S001 QC",
    priority="normal",
    tags=["qc"],
    properties={"sample_id": "S001"},
    cost_limit=25,
)

print(job.get_id())
```

Never launch by an ambiguous app name when version stability matters. Use an
app ID/version or an applet ID.

## Launch a Workflow

CLI:

```bash
dx run "workflow-xxxx" \
  --input-json-file "workflow-inputs.json" \
  --destination "project-xxxx:/runs/run-002" \
  --cost-limit 50
```

This returns an `analysis-...` ID.

Python:

```python
import dxpy

analysis = dxpy.DXWorkflow(
    "workflow-xxxx",
    project="project-xxxx",
).run(
    {
        "0.reads": dxpy.dxlink(
            "file-xxxx",
            "project-xxxx",
        )
    },
    project="project-xxxx",
    folder="/runs/run-002",
    cost_limit=50,
)
```

Workflow input keys can use:

- `"<stage-index>.<input-name>"`
- `"<stage-name>.<input-name>"`
- `"<stage-id>.<input-name>"`
- A promoted workflow-level input name

Use `dx run workflow-xxxx -h` rather than guessing stage keys.

## Lifecycle

Successful jobs normally pass:

```text
idle → runnable → running → done
```

Additional states:

- `waiting_on_input`: dependency, JBOR, or file closure not ready
- `waiting_on_output`: descendant/output closure not ready
- `restartable`: eligible for another try
- `restarted`: prior try was restarted
- `terminating`: teardown underway
- `debug_hold`: failed worker held for approved debugging
- `failed`: terminal failure
- `terminated`: terminal user/system termination

Analyses begin `in_progress` and finish `done`, `failed`, or `terminated`.
`partially_failed` means at least one stage failed while other stages remain
non-terminal.

Jobs normally have a 30-day runtime limit.

## Monitor

Recent executions:

```bash
dx find executions --created-after=-2h
dx find jobs --created-after=-2h
dx find analyses --created-after=-2h
```

Failures:

```bash
dx find jobs --state failed --created-after=-7d
dx find executions --include-restarted --created-after=-7d
```

Watch a job:

```bash
dx watch "job-xxxx"
dx watch "job-xxxx" --get-stdout
dx watch "job-xxxx" --get-stderr
dx watch "job-xxxx" --get-streams
dx watch "job-xxxx" --tree
```

`dx watch` is job-focused. Inspect workflow analyses through `dx find
executions`, `dx describe analysis-xxxx`, the Monitor UI, and individual stage
jobs.

Do not copy logs into public issues without checking for patient identifiers,
project names, signed URLs, or secrets written by app code.

## Wait Safely with dxpy

```python
from dxpy.exceptions import DXError, DXJobFailureError

try:
    job.wait_on_done(interval=10, timeout=6 * 60 * 60)
except DXJobFailureError as error:
    status = job.describe(
        fields={
            "state": True,
            "failureReason": True,
            "failureMessage": True,
        }
    )
    state = status.get("state")
    if state not in {"failed", "terminated"}:
        raise TimeoutError(
            f"local wait ended while remote job state is {state!r}"
        ) from error
    reason = status.get("failureReason") or "Terminated"
    message = status.get("failureMessage") or str(error)
    raise RuntimeError(f"{reason}: {message}") from error
except DXError:
    # SDK/API failure while polling; re-describe before deciding what to do.
    raise
```

Despite its docstring, dxpy 0.415.0 raises `DXJobFailureError` for remote
failure, termination, **and local wait timeout**. Classify the exception by
re-describing the remote state. A local timeout does not terminate the remote
execution.

`DXAnalysis.wait_on_done()` also requires re-describing the analysis after an
exception. Only `done`, `failed`, and `terminated` are terminal analysis states.
`partially_failed` reports a stage failure while other stages are still nonterminal:
inspect those stages and continue monitoring before cleanup or a replacement launch.
Do not equate a locally ended wait with completion or termination of the analysis.

## Outputs

After success:

```python
description = job.describe(fields={"state": True, "output": True})
outputs = description["output"]
```

Output files may still briefly be closing before the job reaches `done`; the
platform waits for required outputs to resolve.

For a future output:

```python
reference = job.get_outpu

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

