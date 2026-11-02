---
id: sciref-etetoolkit-api-reference
name: "Scientific Ref: ETE 4 API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (etetoolkit): ETE 4 API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "etetoolkit api reference"
  - "ete 4 api reference"
keywords:
  - "etetoolkit"
  - "api"
  - "reference"
  - "specialized"
  - "scientific"
---

# ETE 4 API Reference

This is a task-oriented reference for **ETE 4.4.0**. It was checked against the
official ETE 4 documentation and an installed `ete4==4.4.0` package on
September 30, 2026. Use the upstream API reference for less common parameters.

## Imports and Public Classes

```python
from ete4 import (
    EvolTree,
    GTDBTaxa,
    NCBITaxa,
    PhyloTree,
    SeqGroup,
    Tree,
)
```

Frequently used classes:

- `Tree`: general rooted or unrooted tree data structure
- `PhyloTree`: `Tree` subclass with species, alignment, event, and
  reconciliation methods
- `NCBITaxa`: local NCBI taxonomy database interface
- `GTDBTaxa`: local Genome Taxonomy Database interface
- `SeqGroup`: sequence/alignment container
- `EvolTree`: evolutionary-model support, including external PAML workflows

`ClusterTree` is not exported by ETE 4.4.0. Do not port ETE 3 clustering
examples by changing only the import. Use a normal `Tree` for dendrogram
topology and calculate matrix/cluster statistics with a maintained numerical
library.

## Constructing and Parsing Trees

### Empty node or node properties

```python
from ete4 import Tree

empty = Tree()
root = Tree({"name": "root", "dist": 0.0, "study": "trial-7"})
```

ETE 4 nodes do not automatically have a non-null name, distance, or support.
`node.name`, `node.dist`, and `node.support` can therefore be `None`.

### Newick string

```python
tree = Tree("((A:1,B:2)CladeAB:0.5,C:3)Root;", parser=1)
```

Use Python strings for Newick text. ETE 4.4.0 retains a path-like string
heuristic internally, but the documented and reproducible file form is an open
file object; do not depend on the heuristic.

### Newick file

```python
from pathlib import Path

with Path("tree.nw").open(encoding="utf-8") as handle:
    tree = Tree(handle, parser=1)
```

Pass an open text file object. This distinction removes the ETE 3 ambiguity
between file names and Newick strings.

### Common Newick parsers

- `parser="support"` or `parser=0`: flexible branch lengths; internal field is
  support
- `parser="name"` or `parser=1`: flexible branch lengths; internal field is a
  name
- `parser=8`: all node names, no branch lengths required
- `parser=9`: leaf names only
- `parser=100`: topology only

Other numeric parsers encode stricter combinations of names and branch
lengths. Prefer the parser that matches the actual producer's Newick schema.
Inspect a round trip before processing a large collection:

```python
tree = Tree("((A:1,B:1)95:0.2,C:1);", parser="support")
assert tree.write(parser="support", props=[]) == "((A:1,B:1)95:0.2,C:1);"
```

### Nexus files

ETE's Nexus parser returns a dictionary of tree names to `Tree` objects and
applies any Nexus translation table:

```python
from pathlib import Path

from ete4.parser import nexus

with Path("trees.nex").open(encoding="utf-8") as handle:
    trees = nexus.load(handle, parser=9)

for tree_name, tree in trees.items():
    print(tree_name, list(tree.leaf_names()))
```

Use the parser expected by the Newick strings inside the Nexus `TREES` block.
The current Nexus module is a reader; serialize processed trees explicitly as
Newick unless another library is responsible for writing Nexus.

## Node Structure and Properties

Core structural attributes:

```python
node.up           # parent or None
node.children     # child list
node.root         # absolute root
node.is_leaf      # bool property
node.is_root      # bool property
node.level        # edges between node and root
node.id           # positional tuple, such as (0, 1, 0)
```

Biological or user metadata belongs in `props`:

```python
node.add_prop("habitat", "marine")
node.add_props(sample_count=12, qc_pass=True)

habitat = node.get_prop("habitat", "unknown")
same_value = node.props.get("habitat", "unknown")

node.del_prop("qc_pass")
```

`name`, `dist`, and `support` are special property-backed conveniences:

```python
assert node.name == node.props.get("name")
```

Use `add_prop()` rather than assigning arbitrary Python attributes if the value
must participate in search, serialization, or visualization.

## Traversal and Navigation

ETE 4's collection-like methods return iterators.

```python
# Includes the current node.
for node in tree.traverse("preorder"):
    ...

# Excludes the current node.
for node in tree.descendants("postorder"):
    ...

for leaf in tree.leaves():
    ...

leaves = list(tree.leaves())
names = list(tree.leaf_names())
ancestors = list(node.ancestors())
```

Valid traversal strategies are `"levelorder"` (default), `"preorder"`, and
`"postorder"`.

### Dynamic leaf criteria

```python
def stop_at_named_clade(node):
    return node.name in {"Mammalia", "Aves"}

for visible_node in tree.traverse(is_leaf_fn=stop_at_named_clade):
    ...
```

This presents selected internal nodes as terminal during that operation
without changing the topology.

## Search and Lookup

```python
first_a = tree["A"]
by_position = tree[0, 1, 0]

all_a = list(tree.search_nodes(name="A"))
long_branches = [n for n in tree.traverse() if (n.dist or 0) > 1]
leaf_a = next(tree.search_leaves_by_name("A"))

mrca = tree.common_ancestor("A", "B")
mrca_from_list = tree.common_ancestor(["A", "B"])
```

Name lookup returns the first match. Validate uniqueness when names are
identifiers:

```python
from collections import Counter

leaf_names = list(tree.leaf_names())
duplicates = sorted(name for name, count in Counter(leaf_names).items() if count > 1)
if duplicates:
    raise ValueError(f"Duplicate leaf names: {duplicates}")
```

## Topology Modification

### Add and remove nodes

```python
child = tree.add_child(name="A", dist=0.5)
sister = child.add_sister(name="B", dist=0.7)

subtree = child.detach()  # remove child plus all descendants
tree.add_child(subtree)   # attach it elsewhere

internal.delete(preserve_branch_length=True)  # remove node, retain children
```

`detach()` cuts a complete subtree. `delete()` eliminates only the selected
node and reconnects its children.

### Prune

```python
tree.prune(
    ["A", "B", "C"],
    preserve_branch_length=True,
)
```

`preserve_branch_length=True` transfers deleted branch lengths so distances
among retained nodes remain unchanged.

### Root and unroot

```python
tree.set_outgroup(tree["Outgroup"])
tree.set_midpoint_outgroup()
tree.unroot()
```

For inspection without immediately modifying the tree:

```python
midpoint_node = tree.get_midpoint_outgroup()
print(midpoint_node.id)
tree.set_midpoint_outgroup()  # exact midpoint placeme

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

