---
id: sci-bioservices
name: "Scientific: bioservices"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Provides a Python interface to bioinformatics services including UniProt, KEGG, ChEMBL, Reactome, QuickGO, and UniChem. Used for cross-database protein annotation, pathway retrieval, chemical identifier mapping, and integrated biological data workflows with BioServices."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "bioservices"
keywords:
  - "bioservices"
  - "provides"
  - "python"
  - "interface"
  - "bioinformatics"
  - "services"
  - "including"
---

# BioServices

## When to use

Use BioServices when combining protein annotation, gene/pathway membership,
compound cross-references, or genomic resources in Python. Its service clients
share transport helpers, but their request parameters and return types differ.
Use [the service reference](references/services_reference.md) before composing
clients; method names from PubChemPy, mygene, or older BioServices are not portable.

Targets **bioservices 1.16.0**, the current PyPI release at review. Package metadata
allows Python >=3.9,<4; the bundled tests were run in an isolated Python 3.13
environment. The previous 3.12 upper bound was not a package requirement.

```bash
uv pip install "bioservices==1.16.0"
```

## Workflow

1. Resolve the requested organism and entity to stable accessions. Review search
   hits before selecting one; gene symbols and compound names may be ambiguous.
2. Inspect the service's actual response type, including pagination and errors.
   BioServices can return an integer-like HTTP error or `None`, not only raise.
3. Preserve one-to-many mappings, failed identifiers, taxonomy, database release,
   query parameters, and retrieval date alongside derived tables.
4. Distinguish annotations and inferred associations from experimental evidence.
   Pathway membership alone is not an enrichment analysis or causal finding.
5. Run a small lookup before batching; honor provider limits and retain failures
   separately from confirmed empty results.

## Protein search, sequence retrieval, and mapping

```python
from bioservices import UniProt

u = UniProt(verbose=False)
u.services.TIMEOUT = 30
rows = u.search(
    "gene_exact:ZAP70 AND organism_id:9606 AND reviewed:true",
    frmt="tsv", columns="accession,gene_names,organism_name,length",
    limit=5, size=5,
)
if not isinstance(rows, str):
    raise RuntimeError("UniProt search failed")
print(rows)
fasta = u.retrieve("P43403", frmt="fasta")
record = u.retrieve("P43403", frmt="json")

mapping = u.mapping(fr="UniProtKB_AC-ID", to="KEGG", query="P43403")
if not isinstance(mapping, dict) or "results" not in mapping:
    raise RuntimeError("Mapping incomplete or failed")
kegg_ids = [row["to"] for row in mapping["results"] if row["from"] == "P43403"]
print(kegg_ids, mapping.get("failedIds", []))
```

Use `frmt="tsv"`, not `"tab"`; current field names include `accession`,
`gene_names`, `organism_name`, `protein_name`, `go_id`, and `xref_pdb`.
`mapping()` returns a `results`/`failedIds` envelope, **not** a source-to-list
dictionary. Mapping **to** UniProt uses `to="UniProtKB"` and returns full records
in `row["to"]`; extract `primaryAccession`. `UniProtKB_AC-ID` is a source code.
See [identifier mapping](references/identifier_mapping.md) for allowed pairs,
normalization, and limits. For bounded searches set `size=limit` (at most 500);
1.16.0 mixes the two values in its pagination loop.

## KEGG pathways and networks

```python
from bioservices import KEGG

k = KEGG(verbose=False)
k.services.url = "https://rest.kegg.jp"
pathway_names = k.get_pathway_by_gene("7535", "hsa")  # dict: pathway ID -> name
print(pathway_names)
kgml = k.parse_kgml_pathway("hsa04660")
entries = {entry["id"]: entry for entry in kgml["entries"]}
for relation in kgml["relations"][:5]:
    print(entries[relation["entry1"]]["name"], relation["name"],
          entries[relation["entry2"]]["name"])
```

The reviewed `/list/organism` endpoint returned HTTP 400 despite remaining in
the manual. SDK methods that validate against that catalogue can fail. The
bundled compound and pathway-list scripts use the documented scoped endpoints
through `k.services.http_get` to avoid that unrelated catalogue dependency.

KEGG `get` permits at most ten entries; KGML permits one pathway per request.
Keep requests at or below three per second. `list`/`find` return TSV strings;
`get` returns a flat-file string unless an option changes the representation.
KGML entries include genes, compounds, groups, and maps. A relation can produce
several subtype records; those counts are neither unique genes nor independent
physical interactions. Entry IDs are local to each pathway. The bundled SIF
export namespaces them as `pathway#entry` so combining pathways cannot merge
unrelated nodes. `pathway2sif(..., uniprot=False)` is an optional lossy projection
of gene-to-gene activation/inhibition, not a complete pathway network.

## Compound cross-references

```python
from bioservices import UniChem

uc = UniChem(verbose=False)
response = uc.get_compounds("CHEBI:15365", "chebi")  # aspirin
if not isinstance(response, dict) or "compounds" not in response:
    raise RuntimeError("UniChem request failed")
chembl_ids = sorted({source["compoundId"]
    for match in response["compounds"] for source in match.get("sources", [])
    if source.get("shortName") == "chembl"})
print(chembl_ids)
```

UniChem 2 uses `POST /api/v1/compounds` with a JSON body; BioServices assembles it.
Discover source names through `uc.source_ids`; KEGG is absent at review. From a
KEGG compound, preserve every ChEBI cross-reference and use only a uniquely
resolved, structurally reviewed candidate. Check charge, stereochemistry, salts,
and parent forms before merging data. Multiple unresolved name hits or mappings remain
unresolved in the bundled compound script. Empty results do not prove absence.

## QuickGO annotations

```python
from bioservices import QuickGO

g = QuickGO(verbose=False)
terms = g.get_go_terms("GO:0003824")  # list of term dictionaries
page = g.Annotation(geneProductId="UniProtKB:P43403", includeFields="goName",
                    limit=100, page=1)
if not isinstance(page, dict) or "results" not in page:
    raise RuntimeError("QuickGO request failed")
for annotation in page["results"][:5]:
    print(annotation["goId"], annotation["goName"], annotation["goAspect"])
print(page["pageInfo"])  # current, total, resultsPerPage
```

`Term`, `Annotation(protein=..., format="tsv")`, and fixed TSV column offsets
belong to the old API. Fetch pages 1 through `pageInfo.total`; the SDK permits
1–100 rows per page. Preserve qualifiers, evidence codes, references and taxon.
The protein script summarizes distinct positive terms and excludes `NOT`
assertions; its summary is not a raw annotation export or an enrichment test.

## Sequence similarity and associations

`NCBIblast` wraps **EMBL-EBI Job Dispatcher**, not NCBI's BLAST URL API.
The SDK's current methods are `get_status`, `get_result`, `get_result_types`,
and `get_p

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

