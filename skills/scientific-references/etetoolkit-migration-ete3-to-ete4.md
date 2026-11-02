---
id: sciref-etetoolkit-migration-ete3-to-ete4
name: "Scientific Ref: Migrating ETE 3 Code to ETE 4"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (etetoolkit): Migrating ETE 3 Code to ETE 4"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "etetoolkit migration ete3 ete4"
  - "migrating ete 3 code to ete 4"
keywords:
  - "etetoolkit"
  - "migration"
  - "ete3"
  - "ete4"
  - "specialized"
  - "scientific"
  - "reference"
  - "migrating"
  - "code"
---

# Migrating ETE 3 Code to ETE 4

ETE 4 is a breaking API revision, not an import-only upgrade. This guide targets
ETE 4.4.0 and summarizes the official migration guide plus behavior verified
against the installed release.

## Release Baseline

- ETE 4.0.0 and 4.1.1 were released March 28, 2025.
- ETE 4.1.1 marked ETE 4 as out of beta and available on PyPI.
- ETE 4.4.0 was released September 3, 2025.
- Package name and primary import are `ete4`.

Install side by side only when a legacy project genuinely requires ETE 3:

```bash
uv pip install "ete4==4.4.0"
```

Do not leave both APIs implicit in one code path. Name compatibility boundaries
and test them separately.

## Import Changes

ETE 3:

```python
from ete3 import NCBITaxa, PhyloTree, Tree
```

ETE 4:

```python
from ete4 import GTDBTaxa, NCBITaxa, PhyloTree, Tree
```

ETE 3 exposed equivalent `TreeNode` and `Tree` classes. ETE 4 uses `Tree`.

Qt visualization imports moved:

```python
# ETE 3
from ete3 import NodeStyle, TextFace, TreeStyle

# ETE 4
from ete4.treeview import NodeStyle, TextFace, TreeStyle
```

Current web visualization uses:

```python
from ete4.smartview import Layout, PropFace, TextFace
```

SmartView and treeview `TextFace` classes are different types.

## Construction and File Input

### File path ambiguity was removed

ETE 3:

```python
tree = Tree("tree.nw", format=1)
```

ETE 4:

```python
from pathlib import Path

with Path("tree.nw").open(encoding="utf-8") as handle:
    tree = Tree(handle, parser=1)
```

Use strings for Newick text and pass an open file object for file input. ETE
4.4.0 still contains a path-like string heuristic internally, but relying on it
conflicts with the documented contract and makes input behavior ambiguous.

### New nodes with properties

ETE 3:

```python
tree = Tree(name="root", dist=0, support=1)
```

ETE 4:

```python
tree = Tree({"name": "root", "dist": 0, "support": 1})
```

ETE 4 accepts arbitrary initial properties through the dictionary.

## Property Model

ETE 3 required name, distance, and support defaults. In ETE 4 these properties
can be absent, and their convenience accessors can return `None`.

ETE 3:

```python
node.add_feature("habitat", "marine")
node.add_features(group="case", score=0.8)
print(node.features)
```

ETE 4:

```python
node.add_prop("habitat", "marine")
node.add_props(group="case", score=0.8)
print(node.props)
```

General argument renames:

- `feature` / `features` → `prop` / `props`
- `attribute` / `attributes` → `prop` / `props`
- `property` / `properties` → `prop` / `props`

Replace `hasattr(node, "x")` tests for custom metadata with:

```python
if "x" in node.props:
    value = node.props["x"]
```

## Lookup, Predicates, and Relatives

| ETE 3 | ETE 4 |
|---|---|
| `tree & "A"` | `tree["A"]` |
| `tree.get_tree_root()` | `tree.root` |
| `node.is_leaf()` | `node.is_leaf` |
| `node.is_root()` | `node.is_root` |
| `tree.get_common_ancestor(a, b)` | `tree.common_ancestor(a, b)` |
| `node.get_ancestors()` | `node.ancestors()` |
| `tree.get_leaves_by_name("A")` | `tree.search_leaves_by_name("A")` |

ETE 4 also supports positional IDs:

```python
node = tree[0, 1, 0]
print(node.id, node.level)
```

Name lookup returns the first match in both practical patterns. Validate
uniqueness when names are identifiers.

## Iterator Renames

| ETE 3 | ETE 4 |
|---|---|
| `get_leaves()` / `iter_leaves()` | `leaves()` |
| `get_descendants()` / `iter_descendants()` | `descendants()` |
| `get_edges()` / `iter_edges()` | `edges()` |
| `get_leaf_names()` | `leaf_names()` |
| `get_ancestors()` | `ancestors()` |

ETE 4 returns iterators:

```python
leaves = list(tree.leaves())
names = list(tree.leaf_names())
```

Do not call `len(tree.leaves())` or index the result without first creating a
list.

## Text and Newick I/O

### Parser rename

ETE 3:

```python
tree = Tree(newick, format=1)
newick = tree.write(format=1)
```

ETE 4:

```python
tree = Tree(newick, parser=1)
newick = tree.write(parser=1)
```

Named parser aliases include `"name"` and `"support"`.

### ASCII rename

ETE 3:

```python
print(tree.get_ascii(show_internal=True))
```

ETE 4:

```python
print(tree.to_str(show_internal=True, props=["name", "dist"]))
```

### Extended-property semantics

ETE 3 `features=[]` meant all available features. In ETE 4:

```python
tree.write(props=[])                  # no extended properties
tree.write(props=["species", "host"]) # selected properties
tree.write(props=None)                # all available properties
```

This reversal is important. Use an explicit selected list for external output.

Use keyword arguments with `write()`. Its first positional argument is
`outfile` in ETE 4, not the ETE 3 feature selection.

### Custom formatters

ETE 3:

```python
newick = tree.write(
    format=1,
    dist_formatter="%0.1f",
    name_formatter="TEST-%s",
)
```

ETE 4:

```python
from ete4.parser import newick

parser = newick.make_parser(
    1,
    dist="%0.1f",
    name="TEST-%s",
)
text = tree.write(parser=parser)
```

## Distances and Topology

| ETE 3 | ETE 4 |
|---|---|
| `A.get_distance(B)` | `tree.get_distance(A, B)` |
| `topology_only=True` | `topological=True` |
| `convert_to_ultrametric()` | `to_ultrametric()` |
| `resolve_polytomy(recursive=True)` | `resolve_polytomy(descendants=True)` |

ETE 4 adds a direct midpoint convenience:

```python
tree.set_midpoint_outgroup()
```

`get_midpoint_outgroup()` identifies the edge containing the midpoint, but
`set_outgroup()` defaults to a different cut position on that edge. Use
`set_midpoint_outgroup()` when exact placement is required.

ETE 4.4.0 adds `distance_matrix()`, which supersedes
`cophenetic_matrix()` for new code.

## Random Tree Generation

ETE 3:

```python
tree.populate(
    size,
    names_library=names,
    random_branches=True,
    dist_range=(0, 1),
)
```

ETE 4:

```python
import random

tree.populate(
    size,
    names=names,
    model="yule",
    dist_fn=random.random,
    support_fn=lambda: 1,
)
```

Set the random seed when generated topology or distances must be reproducible.

## Robinson-Foulds Unpacking

ETE 4.4.0 returns seven values:

```python
(
    rf,
    max_rf,
    common,
    edges_self,
    edges_other,
    discarded_self,
    discarded_other,
) = tree.robinson_foulds(other)
```

ETE 3 examples that unpack only five values must be updated.

Argument names also use `prop_t1` and `prop_t2` rather than feature-oriented
names.

## PhyloTree Changes and Traps

The central ETE 3 methods rema

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

