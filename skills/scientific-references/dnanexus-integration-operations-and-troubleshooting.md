---
id: sciref-dnanexus-integration-operations-and-troubleshooting
name: "Scientific Ref: Operations and Troubleshooting"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (dnanexus-integration): Operations and Troubleshooting"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "dnanexus integration operations troubleshooting"
  - "operations and troubleshooting"
keywords:
  - "dnanexus"
  - "integration"
  - "operations"
  - "troubleshooting"
  - "specialized"
  - "scientific"
  - "reference"
---

# Operations and Troubleshooting

## Quick Navigation

- [Baseline and first questions](#non-secret-baseline)
- [Authentication and context](#authentication-and-context)
- [Path and object resolution](#path-and-object-resolution)
- [Upload and download problems](#upload-problems)
- [Job states and failure reasons](#job-state-problems)
- [Workflow analysis failures](#workflow-analysis-failures)
- [Nextflow and dxCompiler](#nextflow)
- [Debug access](#debug-access)
- [Service limits and cost review](#service-limits)
- [Destructive operations](#destructive-operations)
- [Support bundle](#support-bundle)

## Non-Secret Baseline

Start with:

```bash
dx --version
dx whoami
dx pwd
```

Do not run `dx env`, `dx env --bash`, or `ua --env` in captured output; they
display credentials.

Record:

- dx-toolkit/dxpy version
- User ID
- Project ID and region
- Exact object/execution ID
- UTC time window
- Operation attempted
- API request ID, if available

Do not record tokens, whole environments, signed URLs, or unredacted PHI.

## First Questions

1. Is the failure local, API-side, or inside a job?
2. Is the object a file, record, applet, workflow, job, or analysis?
3. Is the ID project-qualified?
4. Is the file closed and live?
5. Does the user have the required access?
6. Is an environment variable overriding saved CLI state?
7. Did the operation cross a region, billing entity, TRE, or restricted
   project boundary?
8. Is the execution using the intended app version and instance?
9. Is the failure deterministic or transient?
10. Would retrying incur charges without changing the cause?

## Authentication and Context

### Symptom

- `AuthError`
- `PermissionDenied`
- Unexpected user/project after `dx login`
- An object visible in the UI is invisible to the CLI

### Checks

```bash
dx whoami
dx pwd
```

Shell variables override `~/.dnanexus_config/environment.json`. If the saved
CLI state should win:

```bash
source "$HOME/.dnanexus_config/unsetenv"
dx whoami
dx pwd
```

If saved state should be discarded:

```bash
dx clearenv
```

Then authenticate again. Do not compare token values.

Also check:

- Token expiration/revocation
- Token scope (selected projects versus all projects); user-generated API
  tokens cannot access UKB RAP resources
- Login-session timeout: two hours idle and at most 18 hours from issuance
  under the normal policy, potentially shorter under organization policy
- Project membership and access level
- Organization license/policy
- Download restrictions
- TRE/Data Access Request association
- Whether the project/object is in another region

Do not solve a context error by broadening permissions automatically.

## Path and Object Resolution

### Symptom

- Ambiguous path
- Wrong object selected
- `ResourceNotFound`
- A script sees different data than the UI

### Checks

```bash
dx ls "project-xxxx:/folder"
dx find data \
  --path "project-xxxx:/folder" \
  --name "sample.bam" \
  --name-mode exact \
  --json
```

DNAnexus permits duplicate object names. For mutation, select by ID after
reviewing all matches.

Use project-qualified links:

```python
dxpy.dxlink("file-xxxx", "project-xxxx")
```

## Upload Problems

### File remains open/closing

Possible causes:

- Interrupted multipart upload
- A part never completed
- Upload process exited before closure
- Network loss

For Upload Agent, repeat the same command to resume. Use `--wait-on-close` for
automation that needs a closed file.

Inspect state by ID. A dependent job can be submitted while an input is open
or closing, but it remains `waiting_on_input`; do not expect compute to start
until the file closes.

Abandoned files can remain billable until platform cleanup or explicit
removal. Confirm the exact incomplete object before deleting it.

### Upload Agent creates `.gz`

This is expected for uncompressed inputs. Upload Agent compresses by default.
Use `--do-not-compress` when preserving original bytes or naming is required.

### Upload retries create duplicates

Upload Agent identifies resumable files from a signature that includes path,
size, modification time, compression mode, and chunk size. Changing those
inputs can create a new object.

Review incomplete/closed matches before using `--do-not-resume`.

## Download Problems

### Archived file

Archived files cannot be downloaded until unarchive completes. Confirm
retrieval cost and timing before requesting unarchive.

### Malicious-file warning

Current dx-toolkit warns when a file or generated download URL has been flagged
as malicious. Treat this as a stop condition:

1. Do not execute or preview the content.
2. Confirm the file ID and security status.
3. Ask whether an approved malware-containment environment exists.
4. Download only into that environment if explicitly authorized.

### Large batch is slow or fragile

Use Download Agent with a reviewed manifest. Check free space, run `progress`,
and use `inspect` after completion. Rerun the same manifest to repair missing
or checksum-mismatched parts.

## Job State Problems

### `waiting_on_input`

Check:

- Input files and linked hidden objects are closed.
- Upstream JBORs resolve.
- `depends_on` jobs reached `done`.
- The upstream execution did not fail.
- Input objects can be cloned into the execution context.

### `runnable` for a long time

Check:

- Instance availability in the region
- Spot wait policy and priority
- Retired or unavailable instance type
- Dynamic instance selector transitions
- User/org worker limits

Do not immediately switch to a larger/on-demand instance without estimating
cost.

### `waiting_on_output`

Check:

- Descendant jobs still running
- Output files still closing
- Unresolved output JBORs
- A child failed but the tree is still settling

## Failure Reasons

### `InputError`

- Inspect executable help and current input spec.
- Confirm classes and array shapes.
- Confirm required fields.
- Confirm files are closed and accessible.
- Use DNAnexus links, not local paths.

### `OutputError`

- Compare returned keys to `outputSpec`.
- Check every file output is a valid DNAnexus link.
- Check array versus scalar class.
- Check descendant output references.
- Ensure `job_output.json` contains `{}` when there are no outputs.

### `AppError`

Expected app-recognized problem. Follow the actionable message and fix input or
configuration. Do not retry unchanged.

### `AppInternalError`

Unexpected application failure or nonzero process exit:

1. Review `stdout`/`stderr`.
2. Identify the

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

