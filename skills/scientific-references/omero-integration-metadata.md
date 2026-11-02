---
id: sciref-omero-integration-metadata
name: "Scientific Ref: Metadata and Annotations"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (omero-integration): Metadata and Annotations"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "omero integration metadata"
  - "metadata and annotations"
keywords:
  - "omero"
  - "integration"
  - "metadata"
  - "specialized"
  - "scientific"
  - "reference"
---

# Metadata and Annotations

Annotations may contain participant identifiers, sample names, unpublished
results, free text, remote filenames, or attached files. Read and export the
minimum fields needed.

## Current Annotation Types

The OMERO structured annotation model includes:

- `TagAnnotation`
- `MapAnnotation`
- `FileAnnotation`
- `CommentAnnotation`
- `BooleanAnnotation`
- `LongAnnotation`
- `DoubleAnnotation`
- `TimestampAnnotation`
- `TermAnnotation`
- `XmlAnnotation`
- annotation hierarchies through annotation-to-annotation links

Current `omero.gateway` exports corresponding wrappers, including
`TagAnnotationWrapper`, `MapAnnotationWrapper`,
`FileAnnotationWrapper`, and `CommentAnnotationWrapper`. Do not import a
historical `BaseAnnotationWrapper`; the current public wrapper is
`AnnotationWrapper`.

Annotations can be linked to multiple objects. Their ownership and the
ownership of each link may differ. Deleting an annotation is not the same as
deleting one link.

## Bounded Read

`listAnnotations()` supports a namespace filter but not a page-size argument.
Cap client iteration and report truncation:

```python
from itertools import islice

image = conn.getObject("Image", image_id)
if image is None:
    raise LookupError("Image unavailable")

max_annotations = 100
items = list(islice(image.listAnnotations(), max_annotations + 1))
truncated = len(items) > max_annotations

for annotation in items[:max_annotations]:
    print(annotation.getId(), type(annotation).__name__, annotation.getNs())

print({"truncated": truncated})
```

Avoid `getValue()` when values are outside the export scope. However,
`listAnnotations()` loads linked annotations, including their values, before
yielding, and its namespace filter is applied locally. Thus redaction and
iteration caps protect output; they do not prevent transfer into client memory
or bound the server query. Annotation wrappers inherit `OMERO_CLASS=None`;
use their concrete wrapper class for an annotation type name.

For explicit parent IDs, annotation links can be queried:

```python
image_ids = [101, 102]
for link in islice(
    conn.getAnnotationLinks("Image", parent_ids=image_ids),
    200,
):
    print(link.getParent().getId(), link.getChild().getId())
```

Keep both the parent-ID list and returned-link count bounded.

## Redacted Inventory

A safe default record contains identifiers and type, not values:

```python
def annotation_summary(annotation):
    details = annotation.getDetails()
    owner = details.getOwner() if details is not None else None
    return {
        "id": annotation.getId(),
        "type": type(annotation).__name__.removesuffix("Wrapper"),
        "namespace": annotation.getNs(),
        "owner_id": owner.getId() if owner is not None else None,
        "value_redacted": True,
    }
```

Owner names, annotation values, file names, descriptions, and link-owner names
require separate inclusion decisions.

The bundled exporter defaults to redaction:

```bash
python -B scripts/export_image_metadata.py \
  --image-id 101 \
  --max-annotations-per-image 100 \
  --max-rois-per-image 100 \
  --output ./image-101-metadata.json

# Review, then connect. Add inclusion flags only when approved.
python -B scripts/export_image_metadata.py \
  --image-id 101 \
  --max-annotations-per-image 100 \
  --max-rois-per-image 100 \
  --execute \
  --output ./image-101-metadata.json
```

It never downloads FileAnnotation bytes or pixel data.

## Namespaces

Namespaces let tools assign semantics:

```python
for annotation in image.listAnnotations(ns="org.example.analysis.v1"):
    print(annotation.getId())
```

Use an organization-controlled URI or reverse-domain pattern and document its
schema/version. Do not claim a custom namespace is an OME standard.

The current client constant for client map annotations is:

```python
from omero.constants.metadata import NSCLIENTMAPANNOTATION
```

OME's Python example warns that a client map annotation should be linked to
only one object. Create a separate map annotation for each target when using
that namespace.

## Map Annotations

Read key/value pairs only when approved:

```python
from omero.gateway import MapAnnotationWrapper

for annotation in image.listAnnotations(ns="org.example.analysis.v1"):
    if isinstance(annotation, MapAnnotationWrapper):
        pairs = annotation.getValue()
        for key, value in pairs[:50]:
            print(key, value)
```

Apply independent limits to annotation count, pair count, key length, and
value length. Keys can be sensitive too; a “values redacted” export that leaves
participant IDs in keys is not redacted.

Creating and linking is a write:

```python
from omero.constants.metadata import NSCLIENTMAPANNOTATION
from omero.gateway import MapAnnotationWrapper

image = conn.getObject("Image", image_id)
if image is None:
    raise LookupError("Image unavailable")

pairs = [["Analysis version", "2.1"], ["Status", "reviewed"]]
annotation = MapAnnotationWrapper(conn)
annotation.setNs(NSCLIENTMAPANNOTATION)
annotation.setValue(pairs)
annotation.save()
image.linkAnnotation(annotation)
```

Before running this:

- confirm image ID and group;
- confirm write permission and namespace;
- validate pair count and string lengths;
- decide rollback behavior if save succeeds but link creation fails;
- never create duplicate metadata merely because an earlier query was scoped
  to the wrong group.

## Tags and Comments

Tag creation and linking are separate writes:

```python
from omero.gateway import TagAnnotationWrapper

tag = TagAnnotationWrapper(conn)
tag.setValue("Reviewed")
tag.setDescription("Reviewed under protocol v2")
tag.save()

image = conn.getObject("Image", image_id)
if image is None:
    raise LookupError("Image unavailable")
image.linkAnnotation(tag)
```

Query for an existing controlled tag before creating another. Check group and
owner semantics; do not reuse a same-named tag from an unintended group.

Comments are free text and often the most sensitive annotation type. Do not
include them in a general inventory. Never pass untrusted comments into shell,
HTML, SQL/HQL, filenames, or dynamic code.

## File Annotations

Inspect metadata without downloading bytes:

```python
from omero.gateway import FileAnnotationWrapper

for annotation in image.listAnnotations():
    if isinstance(annotation, FileAnnotationWrapper):
        original = annotation.getFile()
        print(
            {
                "annotation_id": annotation.getId(),
         

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

