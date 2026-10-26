---
id: sciref-benchling-integration-sdk-reference
name: "Scientific Ref: Benchling Python SDK Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (benchling-integration): Benchling Python SDK Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "benchling integration sdk reference"
  - "benchling python sdk reference"
keywords:
  - "benchling"
  - "integration"
  - "sdk"
  - "reference"
  - "specialized"
  - "scientific"
---

# Benchling Python SDK Reference

Targets **1.25.0**, the stable release verified on 2026-09-30. Python requirement:
`>=3.9,<4`. Install with `uv pip install "benchling-sdk==1.25.0"`.
Examples assume an initialized `benchling` client from [authentication](authentication.md).
All IDs and schema fields are placeholders. Model serialization and request construction
were tested offline; server behavior remains illustrative until checked in your tenant.

Source of truth: [versioned SDK reference](https://benchling.com/sdk-docs/1.25.0/index.html)
and the released `benchling-sdk` / `benchling-api-client` Python packages. The
[interaction guide](https://docs.benchling.com/docs/common-sdk-interactions-and-examples)
explains the patterns; use installed signatures when guide snippets differ.

## Schemas and fields

```python
from benchling_sdk.helpers.serialization_helpers import fields

custom_fields = fields({
    "concentration": {"value": 100.0},
    "notes": {"value": "QC passed"},
})
schema = benchling.schemas.get_entity_schema_by_id("ts_example")
```

Use actual field names, numeric types, units, multiplicity, and dropdown **option IDs**
from the schema. `fields()` is a serializer, not schema validation. A field named
`concentration` may be a custom number; it is not the inventory contents concentration.
Omitting a field preserves it on a partial update; `{"value": None}` explicitly clears it
when allowed. Do not confuse `fields` with the free-text `custom_fields` property.

## Registry entities

### DNA: create, register, read, update, archive

```python
from benchling_sdk.models import (
    DnaSequenceCreate, DnaSequenceUpdate, EntityArchiveReason, NamingStrategy,
)
from benchling_sdk.helpers.serialization_helpers import fields

payload = DnaSequenceCreate(
    name="Construct-001",
    bases="ATCGATCG",
    is_circular=True,
    folder_id="lib_example",
    schema_id="ts_example",
    registry_id="src_example",
    naming_strategy=NamingStrategy.NEW_IDS,
    fields=fields({"gene_name": {"value": "GFP"}}),
)
sequence = benchling.dna_sequences.create(payload)
print(sequence.id, sequence.entity_registry_id)
sequence = benchling.dna_sequences.get_by_id(sequence.id)
updated = benchling.dna_sequences.update(
    dna_sequence_id=sequence.id,
    dna_sequence=DnaSequenceUpdate(
        fields=fields({"gene_name": {"value": "mCherry"}}),
    ),
)
```

For an unregistered entity omit `registry_id` and the naming arguments. For an explicit
human registry ID, replace `naming_strategy` with `entity_registry_id="CONSTRUCT001"`.
These are mutually exclusive. Required schema fields are enforced during registration.
`sequence.id` is the API ID; `sequence.entity_registry_id` is the human registry ID.

Archival is a separate requested operation, with an iterable of IDs and an enum:

```python
benchling.dna_sequences.archive(
    dna_sequence_ids=["seq_example"],
    reason=EntityArchiveReason.RETIRED,
)
```

### RNA, proteins, and custom entities

```python
from benchling_sdk.models import (
    RnaSequenceCreate, RnaSequenceUpdate, AaSequenceCreate,
    CustomEntityCreate, CustomEntityUpdate,
)

rna = benchling.rna_sequences.create(RnaSequenceCreate(
    name="gRNA-001", bases="AUCGAUCG", is_circular=False,
    folder_id="lib_example",
))
benchling.rna_sequences.update(
    rna_sequence_id=rna.id,
    rna_sequence=RnaSequenceUpdate(name="gRNA-001-validated"),
)
protein = benchling.aa_sequences.create(AaSequenceCreate(
    name="Peptide-001", amino_acids="MSKGEELFTGVVPIL",
    folder_id="lib_example",
))
cell_line = benchling.custom_entities.create(CustomEntityCreate(
    name="HEK293T-Clone5", schema_id="ts_cellline", folder_id="lib_example",
    fields=fields({"passage_number": {"value": 15}}),
))
benchling.custom_entities.update(
    entity_id=cell_line.id,
    entity=CustomEntityUpdate(fields=fields({"passage_number": {"value": 16}})),
)
```

### Mixtures

`IngredientWriteParams` uses separate amount and units, with explicit nullable provenance
fields. There is no `IngredientCreate` in this release.

```python
from benchling_sdk.models import MixtureCreate, IngredientWriteParams, IngredientMeasurementUnits

ingredient = IngredientWriteParams(
    component_entity_id="bfi_component",
    amount="100", units=IngredientMeasurementUnits.MG,
    catalog_identifier=None, component_lot_container_id=None,
    component_lot_entity_id=None, component_lot_text=None, notes=None,
)
mixture = benchling.mixtures.create(MixtureCreate(
    name="Example formulation", schema_id="ts_mixture", folder_id="lib_example",
    ingredients=[ingredient],
))
```

Resolve ingredient identity/lot and measurement dimensions before transfer or formulation;
serialization does not establish material balance or concentration correctness.

## Inventory

### Storage and physical movement

```python
from benchling_sdk.models import ContainerCreate, ContainerUpdate, BoxCreate, LocationCreate

location = benchling.locations.create(LocationCreate(
    name="Freezer A - Shelf 2", schema_id="locsch_example",
    parent_storage_id="loc_freezer",
))
box = benchling.boxes.create(BoxCreate(
    name="Box 01", schema_id="boxsch_example", parent_storage_id=location.id,
))
container = benchling.containers.create(ContainerCreate(
    name="Sample 001", schema_id="consch_example", parent_storage_id=box.id,
))
moved = benchling.containers.update(
    container_id=container.id,
    container=ContainerUpdate(parent_storage_id="loc_destination"),
)
for page in benchling.containers.list(ancestor_storage_id=box.id):
    for item in page:
        print(item.id, item.name)
```

When placing a container into a box, resolve the supported box position identifier from
the box contents/reference; don't guess coordinates or assume every box has free space.

### Check out and in

```python
from benchling_sdk.models import ContainersCheckout, ContainersCheckin

benchling.containers.checkout(ContainersCheckout(
    assignee_id="usr_example", container_ids=["con_example"], comment="At bench",
))
benchling.containers.checkin(ContainersCheckin(
    container_ids=["con_example"], comments="Returned",
))
```

Check-in does not take a `location_id`. Change physical storage separately if needed.

### Plates and material transfer

```python
from benchling_sdk.models import PlateCreate

plate = benchling.plates.create(PlateCreate(
    name="PCR plate", schema_id="pltsch_example", barcode="PLATE001",
))
```

`PlateCreate.wells`, when used, is a `PlateCreateWells` mappin

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

