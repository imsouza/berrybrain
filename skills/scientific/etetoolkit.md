---
id: sci-etetoolkit
name: "Scientific: etetoolkit"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Analyzes, manipulates, compares, annotates, and visualizes phylogenetic or other hierarchical trees with ETE 4. Supports Newick/Nexus tree I/O, topology edits and pattern matching, Robinson-Foulds comparisons, gene-tree evolutionary events and reconciliation, NCBI/GTDB taxonomy, "
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "etetoolkit"
keywords:
  - "etetoolkit"
  - "analyzes"
  - "manipulates"
  - "compares"
  - "annotates"
  - "visualizes"
  - "phylogenetic"
---

# ETE Toolkit 4

## Scope

Use ETE 4 to work with an existing tree:

- Read Newick/Nexus, then inspect, annotate, transform, root, prune, and write
  Newick trees
- Compare topologies and calculate phylogenetic distances
- Find repeated subtree topologies with `TreePattern`
- Analyze gene trees with `PhyloTree`
- Query local NCBI or GTDB taxonomy databases
- Explore large trees interactively with SmartView
- Render PNG with SmartView or PNG/PDF/SVG with the optional Qt treeview

ETE does not replace sequence alignment or phylogenetic inference software. For
raw sequences, first use MAFFT or another aligner and IQ-TREE 2, FastTree, or
another inference tool; then load the resulting tree into ETE.

## Current Target

This skill targets **ETE 4.4.0**, released September 3, 2025 and verified as the
current PyPI release on September 30, 2026.
Core, phylogeny, local synthetic taxonomy and helper checks target this released
package, not unreleased upstream changes. See
[`references/review.md`](references/review.md) for executed coverage and limitations.

Use `https://etetoolkit.github.io/ete/` for ETE 4 documentation. The
`etetoolkit.org/docs/latest` pages are legacy ETE 3 documentation despite the
URL name.

Do not silently translate these examples back to ETE 3:

- Package and import: `ete4`, not `ete3`
- File input: pass an open file object; use strings for Newick text and do not
  rely on path-string heuristics retained in ETE 4.4.0
- Newick selection: `parser=`, not `format=`
- Node metadata: `props`, `add_prop()`, and `add_props()`
- Iteration: `leaves()`, `descendants()`, and related methods return iterators
- Predicates: `node.is_leaf` and `node.is_root` are properties, not methods
- Node lookup: `tree["name"]`, not `tree & "name"`

For porting older code, load
[`references/migration-ete3-to-ete4.md`](references/migration-ete3-to-ete4.md).

## Installation

Install the pinned base package:

```bash
uv pip install "ete4==4.4.0"
```

Add only the visualization extra required by the workflow:

```bash
# SmartView static PNG screenshots
uv pip install "ete4[render-sm]==4.4.0"

# Legacy Qt renderer for PNG, PDF, and SVG
uv pip install "ete4[treeview]==4.4.0"
```

Confirm the active environment:

```bash
uv run --no-project --isolated --with "ete4==4.4.0" python -c "import ete4; print(ete4.__version__)"
```

No credentials are required. NCBI and GTDB workflows download public taxonomy
data and can consume substantial disk space; see
[`references/taxonomy.md`](references/taxonomy.md) before the first update.

## Quick Start

```python
from pathlib import Path

from ete4 import Tree

# Use an open file object for files; reserve strings for Newick text.
with Path("tree.nw").open(encoding="utf-8") as handle:
    tree = Tree(handle, parser=1)  # parser 1: internal node names

print(tree.to_str(props=["name", "dist"], compact=True))
print("Leaves:", list(tree.leaf_names()))

# Search and annotate.
focal = tree["species1"]
focal.add_props(host="human", status="focal")

# Keep selected tips while preserving pairwise branch-length distances.
tree.prune(
    ["species1", "species2", "species3"],
    preserve_branch_length=True,
)

# Root and serialize explicitly.
tree.set_midpoint_outgroup()
tree.write(
    outfile="processed.nw",
    parser=1,
    props=["host", "status"],
)
```

Choose the parser deliberately. A parser mismatch is the most common cause of
`NewickError`, lost internal labels, or support values being read as names.
See [`references/api_reference.md`](references/api_reference.md).

## Core Workflows

### Inspect and transform a tree

```python
from ete4 import Tree

tree = Tree("((A:1,B:1)CladeAB:0.4,C:2)Root;", parser=1)

for node in tree.traverse("preorder"):
    label = node.name if node.name is not None else node.id
    print(label, node.level, node.is_leaf, node.dist)

tree["A"].add_prop("group", "case")
tree["B"].add_prop("group", "control")

mrca = tree.common_ancestor("A", "B")
print(mrca.name)

tree.write(
    outfile="annotated.nhx",
    parser=1,
    props=["group"],
    format_root_node=True,
)
```

Node names need not be unique. `tree["A"]` returns the first match; use
`list(tree.search_nodes(name="A"))` and validate the count when duplicates are
possible.

### Compare two topologies

```python
from ete4 import Tree

tree_a = Tree("((A,B),(C,D));")
tree_b = Tree("((A,C),(B,D));")

(
    rf,
    max_rf,
    common_leaves,
    edges_a,
    edges_b,
    discarded_a,
    discarded_b,
) = tree_a.robinson_foulds(tree_b)

normalized_rf = rf / max_rf if max_rf > 0 else None
print(rf, max_rf, normalized_rf, sorted(common_leaves))
```

RF comparison uses shared leaf labels and requires meaningful, preferably
unique names. A zero maximum means no comparable splits; normalized RF is
undefined (`None`), not evidence of agreement. Decide explicitly whether rooted or unrooted comparison is
scientifically appropriate.

### Detect duplication and speciation events

```python
from ete4 import PhyloTree

gene_tree = PhyloTree(
    "((Hsa|g1,Ptr|g1),(Hsa|g2,Mmu|g1));",
    sp_naming_function=lambda name: name.split("|", 1)[0],
)

for event in gene_tree.get_descendant_evol_events(sos_thr=0.0):
    relationship = "speciation/orthology" if event.etype == "S" else "duplication/paralogy"
    print(relationship, sorted(event.in_seqs), sorted(event.out_seqs))
```

Species-overlap calls are inferences from the supplied topology and naming
function, not independent evidence of orthology. Pass the naming function
explicitly, and use a rooted, fully bifurcating gene tree. For strict
reconciliation, use a curated species tree and
`gene_tree.reconcile(species_tree)`.

### Query taxonomy

Name lookups can return several TaxIDs. Resolve ambiguity using rank and lineage
before selecting a match. The guard below was checked with synthetic mappings;
the database-dependent workflow is illustrative until run against your snapshot.

```python
from ete4 import NCBITaxa

ncbi = NCBITaxa()
names = ["Homo sapiens", "Pan troglodytes", "Mus musculus"]
name_to_taxids = ncbi.get_name_translator(names)

unresolved = {
    name: name_to_taxids.get(name, [])
    for name in names if len(name_to_taxids.get(name, [])) != 1
}
if unresolved:
    raise ValueError(f"Names need NCBI taxonomy disambiguation: {unresolved}")

taxids = [name_to_taxids[name][0] for name in names]
taxonomy_tree = ncbi.get_topology(taxids)
print(taxonomy_tree.to_str(props=["sci_name", "rank"]))
```

ETE 4 also provides `GTDBTaxa` for genome-cent

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

