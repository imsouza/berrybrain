---
id: sciref-bioservices-services-reference
name: "Scientific Ref: BioServices service contracts"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (bioservices): BioServices service contracts"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "bioservices services reference"
  - "bioservices service contracts"
keywords:
  - "bioservices"
  - "services"
  - "reference"
  - "specialized"
  - "scientific"
  - "service"
---

# BioServices service contracts

Reviewed 2026-09-30 against bioservices 1.16.0, the
[official SDK reference](https://bioservices.readthedocs.io/en/main/references.html),
its linked source, and representative unauthenticated provider reads. These are
service-specific contracts, not a promise that all providers are always available.
JSON field names below refer to the response, not to a uniform BioServices model.

## Core clients

### UniProt

Base: `https://rest.uniprot.org`. `search(query, frmt="tsv", columns=None,
limit=None, size=25, ...)` calls `GET /uniprotkb/search`; `columns` becomes
`fields`. Current fields include `accession,id,gene_names,organism_name,length,
protein_name,go_id,xref_pdb`. Search supports TSV/JSON/FASTA/GFF/XLSX, not `tab`,
XML or plain text. Use `organism_id:9606` in queries. The removed
`searchUniProtId` helper is not available.

`retrieve(accession, frmt="json")` calls the legacy `/uniprot/{id}.{format}`
route, which was verified redirecting to `/uniprotkb/{id}.{format}`. JSON gives
one entry dictionary (`primaryAccession`, `organism.taxonId`); FASTA/TXT/XML
return text. `retrieve(..., frmt="tab")` is invalid.

`mapping(fr, to, query, polling_interval_seconds=3, max_waiting_time=100,
progress=True)` submits form fields `from`, `to`, `ids` to `POST /idmapping/run`,
polls `/idmapping/status/{jobId}`, follows results pagination, and returns
`{"results": [{"from": ..., "to": ...}], "failedIds": [...]}`. Timeout may
return `None`; a target may be a record rather than an ID. See
[identifier mapping](identifier_mapping.md). `valid_mapping` retrieves
`GET /configure/idmapping/fields`; use it to check a pair before submission.

The SDK's search pagination mixes `limit` and `size` and removes its `sort`
parameter before transmission. For small bounded lookups use `size=limit<=500`.
For a full search use `limit=None` with a supported page size and verify counts;
do not describe a bounded result as exhaustive or assume SDK `sort` is applied.

Sources: [SDK source](https://bioservices.readthedocs.io/en/main/_modules/bioservices/uniprot.html),
[live mapping configuration](https://rest.uniprot.org/configure/idmapping/fields).

### KEGG

Set `k.services.url = "https://rest.kegg.jp"` because 1.16.0 initializes HTTP.
`list(database, organism=None)` calls `/list/{database}[/{organism}]`;
`find(database, query, option=None)` calls `/find/{database}/{query}[/{option}]`.
Both return TSV strings. At review `/list/organism` returned HTTP 400 despite
being documented. This breaks `organism` assignment and `find`/`conv`/`link`
validation in 1.16.0. Prefer scoped requests through `k.services.http_get` when
this catalogue is unavailable; the bundled scripts demonstrate that workaround. `get(entries, option=None, parse=False)` calls
`/get/{entries}[/{option}]`; default output is flat-file text. `parse` returns a
dictionary. `lookfor_organism`/`lookfor_pathway` filter the downloaded lists;
`get_pathway_by_gene(gene, organism)` parses the gene's `PATHWAY` section into
an ID-to-name dictionary (or `None`), not a list.

`conv(target, source)` and `link(target, source)` call the respective REST
operations; the wrapper reduces them to a dictionary and can overwrite repeated
source rows. Preserve raw TSV when one-to-many relationships matter.
`parse_kgml_pathway(id)` retrieves `/get/{id}/kgml` and returns `entries` and
`relations`. A relation subtype is a separate row (`entry1`, `entry2`, `link`,
`name`, `value`); subtype-less relations have `name=None`. Nodes have `id`,
`name`, `type`, `gene_names`, and `link`. Local numeric node IDs are not gene IDs.

`pathway2sif(id, uniprot=False)` returns lists `[source, 1 or -1, target]` for
PPrel activation/inhibition between gene entries. It discards other relation
classes and group nodes. The default UniProt conversion selects the first gene
from multi-gene entries; use the explicit `False` form and review multiplicity.

Use <=3 requests/sec. `get` allows ten flat-file entries per call and one KGML
pathway. API access is limited to academic use; consult provider licensing for
other use. Sources: [REST manual](https://www.kegg.jp/kegg/rest/keggapi.html),
[access rules](https://www.kegg.jp/kegg/rest/), [KGML](https://www.kegg.jp/kegg/xml/docs/).

### QuickGO

Base: `https://www.ebi.ac.uk/QuickGO/services`.
`get_go_terms("GO:0003824")` calls `/ontology/go/terms/{ids}` and extracts the
`results` list. `go_search(query, limit=600, page=1)` calls `/ontology/go/search`
and also extracts a list, losing pagination metadata.
`Annotation(geneProductId="UniProtKB:P43403", includeFields="goName",
limit=100, page=1, ...)` calls `/annotation/search` and returns the full JSON
object with `numberOfHits`, `results`, and `pageInfo`. Increment `page` through
`pageInfo.total`; the SDK limits annotation page size to 100.

Annotation rows use `goId`, `goName`, `goAspect` (full names such as
`biological_process`), `qualifier`, `evidenceCode`, `reference`, and `taxonId`.
There is no `Term` method or `protein`, `format` argument to `Annotation`.
Do not reuse the stale SDK docstring's `limit=-1` advice: its code rejects it.
[Provider API](https://www.ebi.ac.uk/QuickGO/api/index.html),
[SDK source](https://bioservices.readthedocs.io/en/main/_modules/bioservices/quickgo.html).

### ChEBI, ChEMBL, and UniChem

| Client | Current methods and requests | Response and caveats |
| --- | --- | --- |
| ChEBI | `getCompleteEntity(id)` -> `GET https://www.ebi.ac.uk/chebi/backend/api/public/compound/{numeric_id}`; `getLiteEntity(search, maximumResults=...)` -> `GET /es_search/?term=...&size=...` | REST `ChebiEntity` dict-like wrapper retains aliases `chebiId`, `chebiAsciiName`, `formula`, `mass`. `getCompleteEntityByList(ids)` loops single requests. Lite search's `searchCategory` and `stars` arguments are ignored by this backend; never claim a filter was applied. |
| ChEMBL | Base `https://www.ebi.ac.uk/chembl/api/data`; `get_molecule("CHEMBL25")`, `get_target(id)`, `get_assay(...)`; `get_similarity(structure, similarity=80, limit=20, offset=0)`, `get_substructure(structure, ...)` | Single molecule is a dict; `molecule_properties` and `molecule_structures` may be null. Collection calls (`query=None`) return lists, may fetch 1,000 rows before trimming to `limit`, and expose `page_meta` on the client. `filters` is a string or list of `field=value` strings, not a dictionary. `get_assays` does not exist. `get_molecule_form` retrieves hierarchy/form relations, not full properties. |
| U

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

