---
id: sci-primekg
name: "Scientific: primekg"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Queries a pinned Precision Medicine Knowledge Graph (PrimeKG) CSV for typed gene, drug, disease, and phenotype nodes, direct associations, disease context, and one- or two-hop paths. Use for PrimeKG reproducibility, biological association lookup, and hypothesis generation with re"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "primekg"
keywords:
  - "primekg"
  - "queries"
  - "pinned"
  - "precision"
  - "medicine"
  - "knowledge"
  - "graph"
---

# PrimeKG Knowledge Graph

## When to use

Use for reproducing PrimeKG analyses, resolving entities in a specific graph artifact,
or exploring recorded gene, drug, disease, phenotype, anatomy, and pathway associations.
A path supports a research hypothesis; it does not establish causality, treatment efficacy,
a prescribing recommendation, or a diagnostic conclusion.

[PrimeKG upstream](https://github.com/mims-harvard/PrimeKG) now recommends OptimusKG for
new work. This skill remains scoped to PrimeKG CSVs; the helper is not an OptimusKG client.
Published PrimeKG integrates 20 resources, with approximately 129,000 nodes and
4.05 million undirected relationships. CSVs contain reverse rows, so row counts differ
from distinct undirected relationship counts. Count the actual pinned artifact.

## 1. Pin and verify the input

The [official dataset](https://doi.org/10.7910/DVN/IXA7BM) remained **V2.1**, published
2022-05-02, at the 2026-10-01 review. Its `kg.csv` has Dataverse file ID **6180620**,
size **981751236 bytes**, and provider MD5 **aac8191d4fbc5bf09cdf8c3c78b4e75f**.
The record declares **CC0 1.0**; upstream construction code is MIT. These are distinct
from this skill's retained license declaration and from terms of individual source
resources used in a rebuild.

Use the [artifact and API reference](references/data-contract.md) to obtain metadata,
verify the file checksum, or distinguish `kg.csv`, `kg_grouped.csv`, features, and PyTDC.
The 2023 construction/OMIM updates in GitHub do not make the published 2022 artifact a
2023 dataset. Record DOI, version, filename, file ID, checksum, retrieval date, and any
subset/rebuild steps with every result.

The helper makes **no remote graph queries**. Download the CSV deliberately after
checking storage and RAM. This full-download example is illustrative; validation used
small HTTP byte ranges and synthetic data, not the 982 MB file:

```bash
curl --fail --location --output kg.csv \
  'https://dataverse.harvard.edu/api/access/datafile/6180620'
export PRIMEKG_DATA="$PWD/kg.csv"
```

`PRIMEKG_DATA` is read when the module is imported; the default is `data/PrimeKG/kg.csv`.
The module reads the whole CSV for each public query. `low_memory` parsing is not a
bounded-memory graph engine. For many queries or limited RAM, build an indexed local
store from the pinned file and validate its node keys, edge multiplicities, and counts.

## 2. Resolve a typed entity before traversal

Run from this skill's directory with pandas installed, so `scripts.query_primekg` is
importable. The following is an illustrative real-data query; no disease result or ID
is promised without inspecting the pinned file:

```python
from scripts.query_primekg import search_nodes, get_neighbors

candidates = search_nodes("Alzheimer", node_type="disease", limit=None)
for node in candidates:
    print(node)  # id, type, name, source, and index when present

# Review the candidates and select the intended disease before calling:
# get_neighbors(selected["id"], node_type=selected["type"],
#               node_source=selected["source"])
```

Search is literal, case insensitive, and returns at most 20 matches by default;
`limit=None` removes that cap. Preserve IDs as strings, including numeric-looking and
underscore-joined IDs. Drug nodes use DrugBank identifiers; diseases can use
`MONDO` or `MONDO_grouped`, including IDs joining multiple diseases. Do not invent EFO,
ChEMBL, Wikidata, or prefixed MONDO IDs from labels. `x_index`/`y_index` are local release
indexes, not ontology accessions and not stable across rebuilds.

The helper identifies a node by **(id, type, source)** and rejects ambiguous bare IDs
or a key mapping to multiple release indexes. Supply `node_type` and `node_source`
from the search result. Equal numeric IDs from different namespaces are different nodes.

## 3. Retrieve associations without losing their meaning

`get_neighbors(node_id, relation_type=None, *, node_type=None, node_source=None)`
collects both stored orientations. Reverse rows are consolidated into one adjacency
per neighboring identity/name, `relation`, and `display_relation`; all original rows
remain in `edge_rows`. Extra CSV evidence columns and release indexes are preserved.
Do not multiply evidence counts by the number of reverse copies.

Use exact stored relation names. Common published relations include:

| `relation` | Interpretation to retain |
| --- | --- |
| `protein_protein` | Protein interaction; not an inferred direction of action |
| `drug_protein` | Inspect `display_relation`: target, enzyme, carrier, or transporter |
| `disease_protein` | Disease-associated gene/protein; not `disease_gene` |
| `indication` | Recorded drug-disease indication |
| `contraindication` | Recorded drug-disease contraindication; never count as treatment support |
| `off-label use` | Separate from indication and contraindication |
| `disease_phenotype_positive` | Recorded phenotype presence |
| `disease_phenotype_negative` | Recorded phenotype absence; retain the sign |
| `disease_disease` | Ontology association/hierarchy, not necessarily comorbidity |

There is no generic `drug_disease`, `disease_phenotype`, or `gwas` relation to assume
in this artifact. The phenotype node type is **`effect/phenotype`**, not `phenotype`.
Inspect the actual relation inventory for other biological scales or custom rebuilds.

Stored x/y orientation is not causal direction: the construction code adds reverse
rows with the same relation label. Hierarchy labels such as `parent-child` cannot be
interpreted from x/y alone in the symmetrized CSV; consult the source ontology.
`x_source`/`y_source` identify node namespaces, not edge-specific studies or evidence
strength. The bundled CSV helper does not retrieve clinical text, publications,
confidence scores, or current approval status.

## 4. Disease summaries and short paths

`get_disease_context(name)` prefers an exact case-insensitive disease name, otherwise
requires a unique substring match. An ambiguous name returns an error and candidates;
it never silently selects the first hit. Results include `associated_genes`,
`associated_drugs`, `phenotypes`, and `related_diseases`. `drug_relations` separates
indication, contraindication, and off-label records. Phenotype records retain positive
versus negative relations; an absent edge means unknown, not a negative association.

`find_paths(start_id, end_id, max_depth=2, ...)` enumerates simple one- and two-hop
**undirected** association

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

