---
id: sciref-gget-workflows
name: "Scientific Ref: gget workflow examples"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (gget): gget workflow examples"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "gget workflows"
  - "gget workflow examples"
keywords:
  - "gget"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
  - "workflow"
---

# gget workflow examples

These are **illustrative integration recipes**, checked against gget 0.30.8
signatures and response contracts, not fully executed scientific analyses.
Remote results, optional dependencies, licenses, and input files vary. The
[database contracts](database_info.md) record public verification and failures.
Use the bundled scripts for tested export/control-flow behavior.

## Gene discovery to annotations and sequences

`search` matches descriptions and synonyms. A search for `TP53` can return other
genes before TP53; never use the first search hit as an exact identifier mapping.

```python
import gget
from pathlib import Path

symbol = "TP53"
hits = gget.search(symbol, species="homo_sapiens")
if hits is None:
    raise RuntimeError("Search failed")
exact = hits.loc[hits["gene_name"].eq(symbol)].drop_duplicates("ensembl_id")
if len(exact) != 1:
    raise ValueError("Resolve missing or ambiguous symbol before proceeding")
gene_id = exact.iloc[0]["ensembl_id"]

info = gget.info(gene_id, pdb=True)
if info is None or info.empty:
    raise RuntimeError("No annotation returned; inspect service errors")
# Query IDs live in the index. Annotation fields can be missing or multi-valued.
info.to_csv("tp53_info.csv", index_label="query_ensembl_id")
print(info[["primary_gene_name", "ensembl_gene_name", "ensembl_description"]])

protein_fasta = gget.seq(gene_id, translate=True)
if not protein_fasta:
    raise RuntimeError("No protein sequence returned")
Path("tp53_protein.fasta").write_text("\n".join(protein_fasta) + "\n")
```

The released Ensembl HTTP adapter failed in this review. Do not treat that as
absence of the gene; resolve transport before running this full recipe.
Nucleotide `gget.seq(gene_id)` is genomic sequence, not an automatically selected CDS.

## Comparative sequences and structures

Choose orthologs from `gget.bgee(..., type="orthologs")`; verify species and
one-to-many orthology before comparing. Save flat FASTA records, not nested
lists of the output from `seq`.

```python
import gget
from pathlib import Path

orthologs = gget.bgee("ENSG00000169174", type="orthologs")  # human PCSK9
print(orthologs[["gene_id", "gene_name", "species"]])
# Select a confirmed mouse ortholog from the response, rather than guessing an ID.
mouse = orthologs.loc[orthologs["species"].eq("musculus")]
if len(mouse) != 1:
    raise ValueError("Choose the intended mouse ortholog explicitly")
human_lines = gget.seq("ENSG00000169174", translate=True)
mouse_lines = gget.seq(mouse.iloc[0]["gene_id"], translate=True)
if not human_lines or not mouse_lines:
    raise RuntimeError("Sequence retrieval failed")
Path("orthologs.fasta").write_text("\n".join(human_lines + mouse_lines) + "\n")
gget.muscle("orthologs.fasta", out="orthologs.afa")  # returns None

# G2P connects a specified protein to existing isoforms and structures.
structure_map = gget.g2p("TP53", uniprot_id="P04637", resource="map")
if structure_map is not None:
    print(structure_map[["UniProt Isoform", "PDB Ids List"]])
# An explicitly chosen structure, after checking chain and residue coverage:
structure = gget.pdb("1TUP", resource="mmcif")
if structure is not None:
    Path("1TUP.cif").write_text(structure)
```

Do not extract a PDB accession by splitting free-text BLAST descriptions.
Check chain sequence, residue numbering, coverage, ligands, experimental method,
and structure quality. Predicted structure confidence is not experimental
validation. The gget AlphaFold wrapper is deprecated and is not part of this recipe.

## Cancer and drug associations

```python
import gget

gene_id = "ENSG00000146648"  # EGFR, human
associations = gget.opentargets(gene_id, resource="diseases", limit=10)
print(associations[["disease.id", "disease.name", "score"]])
drugs = gget.opentargets(gene_id, resource="drugs", limit=10)
if not drugs.empty:
    print(drugs[["drug.name", "drug.drugType", "drug.maximumClinicalStage"]])
tractability = gget.opentargets(gene_id, resource="tractability")
print(tractability)

expression = gget.opentargets(gene_id, resource="expression", limit=100)
if not expression.empty:
    print(expression[["median", "unit", "datasourceId", "datatypeId"]])
interactions = gget.opentargets(gene_id, resource="interactions", limit=10)
print(interactions.reindex(columns=["targetB.id", "targetB.approvedSymbol", "score"]))
```

These are bounded exploratory slices. gget does not traverse Open Targets pages;
local filters cannot retrieve records outside the fetched page. A filter applied
after `limit=10` searches only those ten rows. The disease score does not validate
a target, and an associated drug is not a treatment recommendation. Do not label
candidate targets “validated” from these queries alone.

cBioPortal and COSMIC are separate input routes:

```bash
# Optional dependencies; then discover and select appropriate studies.
gget setup cbio
gget cbio search breast
# Illustrative: downloads study data and writes a heatmap.
gget cbio plot -s msk_impact_2017 -g EGFR TP53 -st tissue -vt mutation_occurrences
# Requires a previously downloaded, licensed COSMIC TSV and matching project.
gget cosmic EGFR --cosmic_project cancer --cosmic_tsv_path cosmic_data.tsv -l 10
```

Record study/sample coverage, assembly, mutation definitions, and denominators.
A missing file or adapter failure is not a zero-mutation result.

## Expression and enrichment

```python
import gget

bulk = gget.archs4("TP53", which="tissue", species="human")
print(bulk[["id", "median"]].head())
correlated = gget.archs4("TP53", which="correlation", gene_count=20)
print(correlated[["gene_symbol", "pearson_correlation"]])
```

For a differential-expression list, supply the genes actually tested as the
background; record mapped/unmapped counts and use an organism-appropriate full
library identifier. The following uploads the lists to Enrichr and is illustrative:

```python
import gget
from pathlib import Path

selected = Path("selected_gene_symbols.txt").read_text().splitlines()
tested = Path("tested_gene_symbols.txt").read_text().splitlines()
if not set(selected).issubset(tested):
    raise ValueError("Selected genes must belong to the tested universe")
result = gget.enrichr(selected, database="GO_Biological_Process_2021",
                      background_list=tested, species="human", plot=False)
if result is None:
    raise RuntimeError("Enrichment failed")
result.to_csv("enrichment.csv", index=False)
significant = result.loc[result["adj_p_val"] < 0.05]
print(sig

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

