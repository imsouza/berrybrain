---
id: sci-lamindb
name: "Scientific: lamindb"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Manages biological datasets and models with LaminDB, including artifact registration, lineage tracking, schema validation, Bionty ontology annotation, query/search, collections, branches, storage, and workflow integrations. Use for reproducible biological data curation or a Lamin"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "lamindb"
keywords:
  - "lamindb"
  - "manages"
  - "biological"
  - "datasets"
  - "models"
  - "including"
---

# LaminDB

## When to use

Use for registering biological datasets, curating DataFrame/AnnData metadata,
querying annotated artifacts, and tracking scientific scripts or workflows.
LaminDB stores metadata in SQLite/PostgreSQL and files in configured storage;
registration alone does not establish scientific validity or FAIR compliance.

This skill targets **LaminDB 2.10.0 and Bionty 2.5.0**. The local examples were
executed on Python 3.12, pandas 3.0.6, and AnnData 0.13.2. The LaminDB release
caps AnnData at 0.13.2; preserve its dependency constraints. Install IPython for
registry synonym helpers (`add_synonym()` imports it in this release).

## Workflow

1. Confirm the intended instance, storage, and write scope with `lamin info`.
   Use a new local development directory for experiments. See
   [setup and deployment](references/setup-deployment.md).
2. Define typed `Feature` records and a `Schema` for the biological data.
   Use registry-backed categorical dtypes for controlled vocabularies;
   `dtype=str` only checks strings. See
   [annotation and validation](references/annotation-validation.md).
3. Review the ontology source/version and organism. Standardize only reviewed
   synonyms and preserve unresolved annotations. See
   [Bionty ontologies](references/ontologies.md).
4. In a script or notebook, start `ln.track()`, load registered inputs, validate,
   and save outputs. `curator.validate()` returns `None` on success and raises
   `ln.errors.ValidationError` on failure. Repair, then validate again.
5. Save through the curator or a schema-aware artifact constructor. Check the
   stored schema and round-trip content; finish a successful run with `ln.finish()`.
6. Query metadata before loading content. Record artifact UIDs and schema/source
   provenance for reproducibility; a key can resolve to a newer version later.
   See [queries and streaming](references/data-management.md).

## Local worked example

Run in a dedicated environment and an empty project directory:

```bash
uv venv --python 3.12
uv pip install 'lamindb==2.10.0' 'bionty==2.5.0' 'ipython==9.17.1'
source .venv/bin/activate
lamin init --storage ./storage --name biology-demo --modules bionty
```

Save the following as `curate_qc.py`, then run `python curate_qc.py`:

```python
import pandas as pd
import lamindb as ln

ln.track(params={"analysis": "QC metadata curation"})
count = ln.Feature(name="gene_count", dtype=int).save()
condition = ln.Feature(name="condition", dtype=str).save()
schema = ln.Schema(
    name="qc_metadata",
    features=[count, condition],
    maximal_set=True,  # reject extra columns
).save()
df = pd.DataFrame({
    "gene_count": [120, 130],
    "condition": ["control", "treated"],
})
curator = ln.curators.DataFrameCurator(df, schema)
curator.validate()  # raises on invalid data; do not use as an if condition
artifact = curator.save_artifact(key="experiments/qc.parquet")
assert artifact.schema == schema
pd.testing.assert_frame_equal(artifact.load(), df)
ln.finish()
```

This validates table structure/types, not whether the counts satisfy assay QC.
Add assay-specific checks (units, allowed ranges, missingness, duplicate sample
IDs, batch balance) before publication or downstream analysis.

## Core objects and contracts

| Object | Purpose and important constraint |
| --- | --- |
| `Artifact` | A file/folder or serialized dataset; `cache()` gets a local path, `load()` materializes content, `open()` returns a format-specific accessor. |
| `Feature` | A typed metadata field; save its definition before `artifact.features.set_values(...)`. |
| `Schema` | Validation rules and feature membership; `maximal_set=True` rejects extras. `flexible=False` alone does not. |
| `Record`, `ULabel` | Experimental entities and simple labels. A custom term is not an ontology assertion. |
| `Run`, `Transform` | An execution and its code definition. Inputs are `run.input_artifacts`; outputs are `run.output_artifacts`. |
| `Collection` | A versioned group of artifacts; iterate `collection.artifacts.all()`. |
| `Project`, `Branch`, `Space` | Grouping, change organization, and access scope; branches do not replace permissions. |

Use `@ln.flow()` for a workflow entry point and `@ln.step()` within it. Lineage
captures tracked accesses, not arbitrary reads outside LaminDB. Review
[core concepts](references/core-concepts.md) for tracking, labels, and revisions.

## Failure patterns to avoid

- `Artifact.backed()`, `delete_cache()`, and `is_cached()` are absent in 2.10.0.
  Use the supported `open()`/`cache()` contracts and cache settings.
- A Parquet `open()` result is a PyArrow dataset, not a byte stream. An AnnData
  accessor is a context manager; materialize a slice with `.to_memory()`.
- There is no `Artifact.is_valid` query field. Query the exact `schema` used and
  retain validation evidence. Assigning a schema ID does not substitute for curation.
- `curator.cat.add_ontology()` and `inspect_standardize()` are absent. Define the
  feature's Bionty dtype, use source-backed records, and use `cat.standardize()`.
  For AnnData use `curator.slots["obs"].cat`, not `curator.cat`.
- Bionty `from_values()` can omit unresolved values and return unsaved records.
  Check all values explicitly and save records before linking them.
- Do not install `lamindb-wetlab` as a Lamin Labs module. Official current docs
  describe `pertdb` for perturbations and `Record` for flexible lab entities.
- Do not invent administrative commands. Current setup uses
  `lamin settings cache-dir ...`, `lamin disconnect`, and `lamin migrate deploy`;
  cloud sharing and backups require their actual documented systems.

## Integrations and verification boundary

Read [integrations](references/integrations.md) for Nextflow `nf-lamin`, external
ML run IDs, DuckDB, Git, and links to official workflow examples. Examples requiring
private Hub access, cloud writes, external workflow services, or public ontology
downloads are illustrative/source-verified unless explicitly marked executed.

Local regression coverage includes DataFrame and AnnData curation, invalid-data
rejection, round trips, features, revisions, collection access, local Bionty
synonyms/hierarchies, and tracked input/output lineage. The release/source review
is recorded in [review sources](references/sources.md).

Keep API keys, cloud credentials, and database passwords out of outputs. Use
workload identity or named environment variables for authenticated work. A local
trial must not change an exi

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

