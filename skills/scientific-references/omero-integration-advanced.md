---
id: sciref-omero-integration-advanced
name: "Scientific Ref: Permissions, Filesets, Web APIs, and High-Risk Operations"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (omero-integration): Permissions, Filesets, Web APIs, and High-Risk Operations"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "omero integration advanced"
  - "permissions, filesets, web apis, and high-risk operations"
keywords:
  - "omero"
  - "integration"
  - "advanced"
  - "specialized"
  - "scientific"
  - "reference"
  - "permissions"
---

# Permissions, Filesets, Web APIs, and High-Risk Operations

This reference covers features that can broaden scope, expose original data,
or mutate server state. Apply the operating contract in `SKILL.md` first.

## Group Permissions

OMERO group permissions are commonly represented as:

- private: `rw----`
- read-only: `rwr---`
- read-annotate: `rwra--`
- read-write: `rwrw--`

The string describes group policy, not a guarantee that a specific operation
is allowed. Ownership, administrator privileges, object state, and link rules
also matter.

Inspect, do not infer:

```python
image = conn.getObject("Image", image_id)
if image is None:
    raise LookupError("Image unavailable")

details = image.getDetails()
permissions = details.getPermissions()
print(
    {
        "group_id": details.getGroup().getId(),
        "owner_id": details.getOwner().getId(),
        "can_edit": permissions.canEdit(),
        "can_annotate": permissions.canAnnotate(),
        "can_link": permissions.canLink(),
        "can_delete": permissions.canDelete(),
    }
)
```

Do not print owner/group names or email addresses unless needed.

## Cross-Group and Substitute-User Operations

`conn.SERVICE_OPTS.setOmeroGroup("-1")` requests all accessible groups. It can
multiply query scope and expose data from collaborations not intended for the
current task. Require explicit cross-group approval, a total cap, and
group IDs in output.

`suConn()` and CLI `--sudo` are privileged impersonation mechanisms. Use only
for an administrator-approved task with:

- initiating administrator identity;
- target user;
- target group;
- exact operation and IDs;
- audit/logging expectations;
- immediate closure of the substitute connection.

Never create a substitute connection merely to work around a permission error.

## Filesets and Original Data

Filesets represent original imported file collections. One fileset may back
multiple images and include nested paths:

```python
fileset = image.getFileset()
if fileset is not None:
    print(fileset.getId())
```

Original-file paths and names can expose acquisition layout or identifiers.
Do not enumerate them in a general inventory.

The current CLI can download one explicit object:

```bash
omero download OriginalFile:123 ./reviewed-file
omero download FileAnnotation:456 ./reviewed-file
omero download Image:789 ./reviewed-empty-directory
omero download Fileset:321 ./reviewed-empty-directory
```

`Image` and `Fileset` may expand to multiple files. The current download CLI
looks these up with cross-group context; verify the object’s actual group
first instead of relying on the session group. First inspect count/size,
then use a dedicated destination with collision/symlink checks. Authenticate
through a prompted stored session; do not add password or key flags.

Direct `RawFileStore` usage must be bounded and closed:

```python
max_bytes = 50 * 1024 * 1024
store = conn.createRawFileStore()
try:
    store.setFileId(original_file_id, conn.SERVICE_OPTS)
    size = store.size(conn.SERVICE_OPTS)
    if size > max_bytes:
        raise ValueError("OriginalFile exceeds approved byte limit")
    chunk = store.read(0, min(size, 1024 * 1024), conn.SERVICE_OPTS)
finally:
    store.close()
```

This sample intentionally reads at most one chunk. A full download needs a
loop with cumulative byte checks and a caller-selected safe path.

## Destructive Commands

`conn.deleteObjects(type, ids, wait=True)` submits an OMERO command. The exact
impact depends on object type, links, ownership, and server graph rules. Do not
promise a cascade/orphan result from intuition.

Required delete workflow:

1. Resolve explicit object type and IDs in one group.
2. Read current object/link summaries and permissions.
3. Show counts and likely related objects from documented queries.
4. Obtain explicit approval for those exact IDs.
5. Submit with `wait=True` or monitor the returned command callback.
6. Inspect command response for errors.
7. Record success/failure per ID.
8. Close callbacks/handles and the gateway.

Never select delete targets by a broad name/namespace query without an ID
review. Never add delete mode to inventory/export scripts.

Unlinking an annotation, table, image, or dataset is a different graph change
from deleting the child. State which one is intended.

## Ownership and Group Changes

Changing ownership or moving data between groups can alter access for many
linked objects. Current CLI documentation says ownership changes require full
admin, an appropriately privileged restricted admin, or group owner.

Before:

- enumerate exact root objects and affected links;
- confirm source and destination groups;
- confirm target owner membership;
- check whether filesets/annotations/tables move with the object graph;
- obtain administrator approval;
- use current documented CLI/API methods, not direct `_obj.details.owner`
  manipulation copied from old examples.

Do not write private model fields to bypass service-level policy.

## HQL and Query Service

Use fixed HQL and typed parameters:

```python
import omero.sys

parameters = omero.sys.ParametersI()
parameters.addLong("image_id", image_id)

query = "select i from Image i where i.id = :image_id"
model_image = conn.getQueryService().findByQuery(query, parameters, conn.SERVICE_OPTS)
```

Never interpolate names, namespaces, IDs, ordering, or arbitrary user text
into HQL. Map user choices to allowlisted fixed query templates. Apply a
server-side result limit to list queries.

## Deprecated Service Surface

The current generated API marks at least these interfaces deprecated:

- `IRoi`
- `IShare`

`IRoi.findByImage` remains in current official Python examples, but should be
isolated and version-checked. Do not build new sharing workflows on
`IShare`; use current administrator-supported OMERO.web/public-data features
instead.

Deprecation does not mean immediate removal. It means callers must not claim
long-term stability or invent a replacement.

## OMERO.web: What Is Publicly Supported

Official OMERO.web developer documentation says only these included apps are
stable public APIs:

- `api`
- `webgateway`

Other apps, including `webclient`, expose internal URLs and methods that may
change in minor releases. A URL currently used by the UI is not automatically
a supported integration endpoint.

### JSON API

The documented OMERO JSON API:

- is implemented by the `api` Django app;
- advertises supported major versions at `GET /api/`;
- advertises starting

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

