---
id: sciref-omero-integration-data-access
name: "Scientific Ref: Data Access, Hierarchies, and Transfers"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (omero-integration): Data Access, Hierarchies, and Transfers"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "omero integration access"
  - "data access, hierarchies, and transfers"
keywords:
  - "omero"
  - "integration"
  - "access"
  - "specialized"
  - "scientific"
  - "reference"
---

# Data Access, Hierarchies, and Transfers

Use this reference for bounded reads and explicit import/export scopes. Read
[`connection.md`](connection.md) first.

## Object Hierarchies

Common container paths are:

```text
Project -> Dataset -> Image
Screen -> Plate -> Well -> WellSample -> Image
Image -> Pixels -> Channel
Image -> Fileset -> OriginalFile(s)
```

Links are model objects and may be many-to-many. Do not assume an image has
exactly one dataset or a dataset exactly one project. Traverse links returned
by the server instead of synthesizing parent paths.

Common BlitzGateway object names documented by OME include:

- `Project`, `Dataset`, `Image`
- `Screen`, `Plate`, `PlateAcquisition`, `Well`
- `Roi`, `Shape`
- `Experimenter`, `ExperimenterGroup`
- `OriginalFile`, `Fileset`
- `Annotation` and specific annotation subtypes

Object-name support is not permission. A returned `None` may mean nonexistent
or inaccessible.

## One Object by ID

Use explicit IDs whenever possible:

```python
image_id = 123
image = conn.getObject("Image", image_id)
if image is None:
    raise LookupError("Image was not found or is not accessible")

print(image.getId())
print(image.getSizeX(), image.getSizeY())
```

Do not print names, descriptions, owner names, or acquisition metadata unless
the requested output includes them.

For multiple explicit IDs:

```python
requested_ids = [101, 102, 103]
for image in conn.getObjects(
    "Image",
    requested_ids,
    respect_order=True,
):
    print(image.getId())
```

Keep the input list bounded. Check whether inaccessible IDs were omitted.

## Bounded Pagination

`getObjects()` returns a generator. Use both an overall cap and page size:

```python
def iter_bounded(conn, object_type, *, limit=100, page_size=25):
    if not 1 <= limit <= 1000:
        raise ValueError("limit must be between 1 and 1000")
    if not 1 <= page_size <= min(limit, 200):
        raise ValueError("page_size must be between 1 and min(limit, 200)")

    emitted = 0
    offset = 0
    while emitted < limit:
        size = min(page_size, limit - emitted)
        page = list(
            conn.getObjects(
                object_type,
                opts={
                    "limit": size,
                    "offset": offset,
                    "order_by": "obj.id",
                },
            )
        )
        if not page:
            return

        for obj in page:
            yield obj
            emitted += 1

        if len(page) < size:
            return
        offset += len(page)
```

Do not write `list(conn.getObjects(...))` without server-side limits. If
another process changes rows during offset paging, results may shift; record
the extraction time and selected group.

The bundled inventory helper implements a cap of 1000 and page cap of 200:

```bash
python -B scripts/inventory.py \
  --object-type Image \
  --limit 50 \
  --page-size 25

# Review the dry-run JSON, then explicitly connect:
python -B scripts/inventory.py \
  --object-type Image \
  --limit 50 \
  --page-size 25 \
  --execute \
  --output ./image-inventory.json
```

Names are redacted unless `--include-names` is requested.

## Group and Owner Filters

Prefer one selected group:

```python
group_id = 42
conn.SERVICE_OPTS.setOmeroGroup(str(group_id))

for project in conn.getObjects(
    "Project",
    opts={"limit": 20, "offset": 0, "order_by": "obj.id"},
):
    print(project.getId())
```

Filters can further narrow a query:

```python
owner_id = conn.getUser().getId()
conn.SERVICE_OPTS.setOmeroGroup(str(group_id))
projects = conn.getObjects(
    "Project",
    opts={
        "owner": owner_id,
        "limit": 20,
        "offset": 0,
        "order_by": "obj.id",
    },
)
```

Cross-group context (`-1`) must be separately approved and paired with a hard
limit. Never use it as a fallback when an object is not found.

## Traversing Containers

Downward traversal lazily loads children:

```python
project = conn.getObject("Project", project_id)
if project is None:
    raise LookupError("Project unavailable")

dataset_limit = 10
for dataset_index, dataset in enumerate(project.listChildren()):
    if dataset_index >= dataset_limit:
        break
    print(dataset.getId())

    image_limit = 25
    for image_index, image in enumerate(dataset.listChildren()):
        if image_index >= image_limit:
            break
        print(image.getId())
```

`listChildren()` can materialize the child collection before yielding; these
loop caps bound output, not the query or memory. Prefer paged `getObjects()`
with `project`, `dataset`, or `plate` filters for large containers.
`countChildren()` can help plan a cap but does not replace one. A count may
change before retrieval.

For a direct dataset image query, prefer a server filter:

```python
images = conn.getObjects(
    "Image",
    opts={
        "dataset": dataset_id,
        "limit": 50,
        "offset": 0,
        "order_by": "obj.id",
    },
)
```

## Screening Data

Bound each hierarchy level:

```python
plate = conn.getObject("Plate", plate_id)
if plate is None:
    raise LookupError("Plate unavailable")

for well_index, well in enumerate(plate.listChildren()):
    if well_index >= 96:
        break
    print(well.getId())

    field_count = min(well.countWellSample(), 10)
    for field_index in range(field_count):
        image = well.getImage(field_index)
        if image is not None:
            print(image.getId())
```

A Well may load all WellSamples before `countWellSample()` or `getImage()`
returns. The field cap above limits output, not the loaded graph.

Well rows/columns and field counts can reveal experiment design. Include them
only when requested.

## Image Metadata

Basic dimensions do not retrieve pixel planes:

```python
summary = {
    "id": image.getId(),
    "size_x": image.getSizeX(),
    "size_y": image.getSizeY(),
    "size_z": image.getSizeZ(),
    "size_c": image.getSizeC(),
    "size_t": image.getSizeT(),
    "pixels_type": image.getPixelsType(),
}
```

Physical sizes may be absent:

```python
size_x = image.getPixelSizeX(units=True)
if size_x is not None:
    print(size_x.getValue(), size_x.getSymbol())
```

Names, descriptions, acquisition dates, owner names, group names, and channel
labels are potentially sensitive metadata. Redact by default in broad reports.

## Filesets and Original Files

A fileset groups original imported files and may represent several images.
Inspect metadata before downloading:

```python
fileset =

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

