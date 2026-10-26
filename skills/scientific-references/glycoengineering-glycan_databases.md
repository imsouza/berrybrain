---
id: sciref-glycoengineering-glycan-databases
name: "Scientific Ref: Glycan databases, evidence and notation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (glycoengineering): Glycan databases, evidence and notation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "glycoengineering glycan databases"
  - "glycan databases, evidence and notation"
keywords:
  - "glycoengineering"
  - "glycan"
  - "databases"
  - "specialized"
  - "scientific"
  - "reference"
---

# Glycan databases, evidence and notation

Reviewed 2026-10-01. Public read-only probes below did not use credentials or
submit sequences, structures or private data. A successful transport probe is not
evidence that a database's scientific content is current or complete.

## GlyTouCan: accession to WURCS

[GlyTouCan](https://glytoucan.org/) assigns identifiers to glycan descriptions,
including descriptions with unresolved features. An accession alone does not
establish a fully resolved structure or biological occurrence.

The former example `https://api.glytoucan.org/glycan/{id}` is unsupported here
(the G00055MO probe returned 404). Use the project's documented
[SPARQL structure query](https://code.glytoucan.org/rdf-ontology/sparql-queries/),
restricted to the desired accession:

```python
from glytoucan_lookup import lookup_wurcs

sequences = lookup_wurcs("G00055MO")
print(sequences)
# Live review returned one sequence beginning WURCS=2.0/2,2,1/...
```

Import [scripts/glytoucan_lookup.py](../scripts/glytoucan_lookup.py) from the
skill's scripts directory. Tested with requests 2.34.2.

| Contract | Verified behavior |
| --- | --- |
| Request | Public `GET https://ts.glytoucan.org/sparql`; URL-encoded `query` and `format=application/sparql-results+json`, plus the matching `Accept` header. No API version path or credentials used. |
| Data selection | Named graphs `http://rdf.glytoucan.org/core` and `http://rdf.glytoucan.org/sequence/wurcs`; exact `VALUES ?PrimaryId` match. Accession validation prevents interpolating arbitrary SPARQL. |
| Response | JSON `head.vars` and `results.bindings`; each binding has `PrimaryId.value` and `Sequence.value`. Keep WURCS uncertainty. |
| Pagination | Single-accession lookup has no client pagination or artificial LIMIT. Bulk queries use SPARQL `ORDER BY` and explicit `LIMIT`/`OFFSET`, not a REST cursor. Do not claim a changing dataset was completely enumerated without a stable snapshot. |
| Failure | HTTP, timeout, invalid JSON and schema errors remain errors. An empty binding list means no matching WURCS in the queried graphs, not proof of absence from GlyTouCan. |

The helper sets connection/read timeouts, raises for HTTP failures, checks the
response type, validates the returned accession, and retains all distinct WURCS
sequences. It does not validate WURCS chemistry or register glycans.

## GlyConnect: protein, site and glycan evidence

[GlyConnect](https://glyconnect.expasy.org/) links glycan and protein evidence.
Use its search interface with a UniProt accession, then check species, isoform,
site, glycan/composition, experimental context and publication. The homepage
reports version 2.6.0 dated 2025-11-21; older linked pages still show 1.3.0.
Do not infer one synchronized release across these surfaces.

REST access is currently **unverified**: the official
[Swagger entry point](https://glyconnect.expasy.org/api/docs) redirects with a
schema URL `/api/assets/swagger.json`, which returned 404. The old
`/api/proteins/uniprot/P00533` returned 500; `/api/compositions/protein/1` returned
404. These failures establish neither a supported schema nor no biological data.
The previous functions returning `{}` or `[]` on these errors have been removed.
Do not invent replacements, response envelopes, auth requirements or pagination.

The official [RDF documentation](https://glyconnect.expasy.org/rdf) supports a
SPARQL alternative. This **transport check**, with explicit response negotiation,
was executed and returned one RDF schema triple:

```python
import requests

response = requests.post(
    "https://glyconnect.expasy.org/sparql",
    data="SELECT * { ?s ?p ?o } LIMIT 1",
    headers={"Content-Type": "application/sparql-query",
             "Accept": "application/sparql-results+json"},
    timeout=(10, 45),
)
response.raise_for_status()
if not response.headers.get("Content-Type", "").startswith("application/sparql-results+json"):
    raise ValueError("SPARQL service did not return negotiated JSON")
rows = response.json()["results"]["bindings"]
print(rows)
```

It is a read query despite HTTP POST; no credentials were needed. Form-encoded
`format=json` alone returned CSV during review, so retain the headers above.
JSON follows SPARQL binding objects, not a `data` list. Pagination, when needed,
belongs in the query with stable ordering and `LIMIT`/`OFFSET`; no cursor was
advertised. The live endpoint returned no rows for a bounded UniProt-object probe
and no named graphs for a bounded graph query. Linked protein/site sample query
files also failed. **Protein/site/composition retrieval was not established**;
a successful generic query must not be reported as a successful glycoprotein
lookup. Consult the current ontology/examples and verify actual records before
automating scientific extraction.

## Other resources and tools

| Resource | Use and limits |
| --- | --- |
| [KEGG GLYCAN](https://www.genome.jp/kegg/glycan/) | Glycan G-number records linked to biosynthesis/pathway maps; composition, name and ID search. A pathway association does not demonstrate occupancy on a given protein. |
| [CAZy](https://www.cazy.org/) | Carbohydrate-active enzyme families for enzyme candidate research. Family membership does not uniquely determine substrate specificity. Direct page access returned 403 during review, so current data/release was not verified. |
| [UniCarb-DR](https://unicarb-dr.glycosmos.org/) | Non-curated repository of annotated glycomic MS/MS data with MIRAGE metadata, distinct from curated UniCarb-DB. Review original spectra and experimental context. |
| [GlycoWorkbench archive](https://code.google.com/archive/p/glycoworkbench/) | Legacy Java glycan drawing/mass-spectrum annotation tool; use the official archive linked by UniCarb-DR's [MIRAGE protocol](https://unicarb-dr.glycosmos.org/assets/samplefiles/MIRAGEprotocolv2.0.pdf), not third-party installer mirrors. Modern OS/Java execution was not tested. |
| [Byonic](https://www.proteinmetrics.com/products/byonic) | Commercial glycopeptide database search and spectral annotation. It is not generally a de novo full glycan-structure solver; see the entrypoint's composition/localization caveats. |
| [Mascot](https://www.matrixscience.com/help/o-fucosylated_cid_spectra.html) | Modification-aware peptide search; glycan neutral-loss behavior and residue specificity must be modeled. A generic modification hit is not complete glycan structural assignment. |
| [GlycoMine study](https://pubmed.ncbi.nlm.nih.g

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

