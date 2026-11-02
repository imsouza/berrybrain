---
id: sciref-etetoolkit-workflows
name: "Scientific Ref: ETE 4 Workflows"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (etetoolkit): ETE 4 Workflows"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "etetoolkit workflows"
  - "ete 4 workflows"
keywords:
  - "etetoolkit"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
---

# ETE 4 Workflows

Complete patterns for common ETE 4.4.0 tasks. Adapt parsers and biological
assumptions to the actual data source.

## Guide Map

- Validate names, branch lengths, and support before analysis
- Preprocess and root an existing tree reproducibly
- Compare rooted or unrooted topologies
- Join metadata without silently dropping records
- Detect evolutionary events or reconcile against a species tree
- Split duplicated gene families
- Query NCBI or GTDB taxonomy
- Batch-process and cache large trees
- Hand off clustering and tree inference to the right upstream tools
- Match trusted topology patterns

The fenced Python snippets are examples within this Markdown guide, not a
single executable program. Run only the section needed for the current task.

## 1. Validate Before Analysis

Name-based operations and tree comparisons become unreliable when labels are
empty or duplicated.

```python
from collections import Counter
from pathlib import Path

from ete4 import Tree


def load_and_validate(path: Path, parser=1) -> Tree:
    with path.open(encoding="utf-8") as handle:
        tree = Tree(handle, parser=parser)

    names = list(tree.leaf_names())
    empty = [leaf.id for leaf in tree.leaves() if not leaf.name]
    duplicate_counts = {
        name: count
        for name, count in Counter(names).items()
        if name and count > 1
    }

    if empty:
        raise ValueError(f"{path}: unnamed leaves at positions {empty[:10]}")
    if duplicate_counts:
        raise ValueError(f"{path}: duplicate leaf names {duplicate_counts}")
    if len(names) < 2:
        raise ValueError(f"{path}: expected at least two leaves")

    return tree


tree = load_and_validate(Path("tree.nw"), parser=1)
```

Also verify that the parsed support and branch-length ranges are plausible for
the program that produced the tree:

```python
supports = [
    node.support
    for node in tree.traverse()
    if not node.is_leaf and node.support is not None
]
distances = [
    node.dist
    for node in tree.traverse()
    if not node.is_root and node.dist is not None
]

if any(distance < 0 for distance in distances):
    raise ValueError("Negative branch length detected")

print("support range:", (min(supports), max(supports)) if supports else None)
print("distance range:", (min(distances), max(distances)) if distances else None)
```

Support may be represented as fractions or percentages. Do not apply a
threshold before checking its scale.

## 2. Reproducible Tree Preprocessing

```python
from collections import Counter
from pathlib import Path

from ete4 import Tree

input_path = Path("inferred_tree.nw")
output_path = Path("processed_tree.nw")

with input_path.open(encoding="utf-8") as handle:
    tree = Tree(handle, parser="support")

# Keep a known sample set and preserve retained pairwise distances.
keep = ["sample_A", "sample_B", "sample_C", "outgroup"]
counts = Counter(tree.leaf_names())
invalid = {name: counts[name] for name in keep if counts[name] != 1}
if invalid:
    raise ValueError(f"Requested tips must exist exactly once: {invalid}")
tips = {leaf.name: leaf for leaf in tree.leaves()}
tree.prune([tips[name] for name in keep], preserve_branch_length=True)

# Prefer a biological outgroup when justified.
tree.set_outgroup(tips["outgroup"])

# Stable presentation order only; this does not alter clade membership.
tree.ladderize()

tree.write(
    outfile=str(output_path),
    parser="support",
    props=[],
)
```

Record the original input checksum, ETE version, parser, retained sample set,
rooting rule, and output parser in an analysis manifest.

## 3. Midpoint Rooting

Midpoint rooting is useful when a defensible biological outgroup is not
available, but it assumes the longest leaf-to-leaf path can approximate a
clock-like split.

```python
from ete4 import Tree

tree = Tree("((A:1,B:1):1,(C:2,D:2):1);")
tree.set_midpoint_outgroup()
print(tree.write(props=[]))
```

For auditability:

```python
tree = Tree("((A:1,B:1):1,(C:2,D:2):1);")
candidate = tree.get_midpoint_outgroup()
candidate_id = candidate.id
tree.set_midpoint_outgroup()
print("midpoint candidate:", candidate_id)
```

The candidate identifies an edge. Calling `set_outgroup(candidate)` instead
uses the default cut along that edge and can miss the exact diameter midpoint.

Do not describe midpoint rooting as evidence for the direction of evolution.

## 4. Compare Two Trees

```python
from collections import Counter
from pathlib import Path

from ete4 import Tree


def load(path: Path, parser=1) -> Tree:
    with path.open(encoding="utf-8") as handle:
        return Tree(handle, parser=parser)


def assert_unique_leaf_names(tree: Tree, label: str) -> None:
    counts = Counter(tree.leaf_names())
    if any(not name for name in counts):
        raise ValueError(f"{label} has unnamed leaves")
    duplicates = sorted(name for name, count in counts.items() if count > 1)
    if duplicates:
        raise ValueError(f"{label} has duplicate leaves: {duplicates}")


tree_a = load(Path("method_a.nw"))
tree_b = load(Path("method_b.nw"))
assert_unique_leaf_names(tree_a, "method_a")
assert_unique_leaf_names(tree_b, "method_b")

(
    rf,
    max_rf,
    common,
    edges_a,
    edges_b,
    discarded_a,
    discarded_b,
) = tree_a.robinson_foulds(
    tree_b,
    unrooted_trees=True,
)

print(
    {
        "rf": rf,
        "max_rf": max_rf,
        "normalized_rf": rf / max_rf if max_rf > 0 else None,
        "common_leaf_count": len(common),
        "discarded_edges_a": len(discarded_a),
        "discarded_edges_b": len(discarded_b),
    }
)
```

Checklist:

- Rooted and unrooted RF answer different questions.
- ETE compares the intersection when leaf sets differ; report its size.
- Require at least two shared tips. With no eligible splits (`max_rf <= 0`),
  normalized RF is undefined, not zero.
- Duplicate labels violate the usual tip-identity assumption.
- Support filtering and polytomy expansion materially change results.
- A high RF distance does not explain which biological split is preferable.

For a higher-level result:

```python
summary = tree_a.compare(tree_b, unrooted=True)
print(summary["rf"], summary["max_rf"], summary["norm_rf"])
```

Keep labels unique. Do not use `Tree.compare(has_duplications=True)` in ETE
4.4.0; upstream marks that TreeKO branch as likely broken. The packaged
`ete4 compare` CLI also fails because it still passes the removed `format=`
keyword, so use the methods above or `scripts/tree_operations.py compa

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

