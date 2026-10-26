---
id: sciref-biopython-phylogenetics
name: "Scientific Ref: Phylogenetics with Bio.Phylo"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (biopython): Phylogenetics with Bio.Phylo"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "biopython phylogenetics"
  - "phylogenetics with bio.phylo"
keywords:
  - "biopython"
  - "phylogenetics"
  - "specialized"
  - "scientific"
  - "reference"
  - "phylo"
---

# Phylogenetics with Bio.Phylo

## Overview

Bio.Phylo provides a unified toolkit for reading, writing, analyzing, and visualizing phylogenetic trees. It supports multiple file formats including Newick, NEXUS, phyloXML, NeXML, and CDAO.

## Supported File Formats

- **Newick** - Simple tree representation (most common)
- **NEXUS** - Extended format with additional data
- **phyloXML** - XML-based format with rich annotations
- **NeXML** - Modern XML format
- **CDAO** - Comparative Data Analysis Ontology

## Reading and Writing Trees

### Reading Trees

```python
from Bio import Phylo

# Read a tree from file
tree = Phylo.read("tree.nwk", "newick")

# Parse multiple trees from a file
trees = list(Phylo.parse("trees.nwk", "newick"))
print(f"Found {len(trees)} trees")
```

### Writing Trees

```python
# Write tree to file
Phylo.write(tree, "output.nwk", "newick")

# Write multiple trees
Phylo.write(trees, "output.nex", "nexus")
```

### Format Conversion

```python
# Convert between formats
count = Phylo.convert("input.nwk", "newick", "output.xml", "phyloxml")
print(f"Converted {count} trees")
```

## Tree Structure and Navigation

### Basic Tree Components

Trees consist of:
- **Clade** - A node (internal or terminal) in the tree
- **Terminal clades** - Leaves/tips (taxa)
- **Internal clades** - Internal nodes
- **Branch length** - Evolutionary distance

### Accessing Tree Properties

```python
# Tree root
root = tree.root

# Terminal nodes (leaves)
terminals = tree.get_terminals()
print(f"Number of taxa: {len(terminals)}")

# Non-terminal nodes
nonterminals = tree.get_nonterminals()
print(f"Number of internal nodes: {len(nonterminals)}")

# All clades
all_clades = list(tree.find_clades())
print(f"Total clades: {len(all_clades)}")
```

### Traversing Trees

```python
# Iterate through all clades
for clade in tree.find_clades():
    if clade.name:
        print(f"Clade: {clade.name}, Branch length: {clade.branch_length}")

# Iterate through terminals only
for terminal in tree.get_terminals():
    print(f"Taxon: {terminal.name}")

# Depth-first traversal
for clade in tree.find_clades(order="preorder"):
    print(clade.name)

# Level-order (breadth-first) traversal
for clade in tree.find_clades(order="level"):
    print(clade.name)
```

### Finding Specific Clades

```python
# Find clade by name
clade = tree.find_any(name="Species_A")

# Find all clades matching criteria
def is_long_branch(clade):
    return clade.branch_length and clade.branch_length > 0.5

long_branches = tree.find_clades(is_long_branch)
```

## Tree Analysis

### Tree Statistics

```python
# Total branch length
total_length = tree.total_branch_length()
print(f"Total tree length: {total_length:.3f}")

# Tree depth (root to furthest leaf)
depths = tree.depths()
max_depth = max(depths.values())
print(f"Maximum depth: {max_depth:.3f}")

# Terminal count
terminal_count = tree.count_terminals()
print(f"Number of taxa: {terminal_count}")
```

### Distance Calculations

```python
# Distance between two taxa
distance = tree.distance("Species_A", "Species_B")
print(f"Distance: {distance:.3f}")

# Create distance matrix
from Bio import Phylo

terminals = tree.get_terminals()
taxa_names = [t.name for t in terminals]

print("Distance Matrix:")
for taxon1 in taxa_names:
    row = []
    for taxon2 in taxa_names:
        if taxon1 == taxon2:
            row.append(0)
        else:
            dist = tree.distance(taxon1, taxon2)
            row.append(dist)
    print(f"{taxon1}: {row}")
```

### Common Ancestors

```python
# Find common ancestor of two clades
clade1 = tree.find_any(name="Species_A")
clade2 = tree.find_any(name="Species_B")
ancestor = tree.common_ancestor(clade1, clade2)
print(f"Common ancestor: {ancestor.name}")

# Find common ancestor of multiple clades
clades = [tree.find_any(name=n) for n in ["Species_A", "Species_B", "Species_C"]]
ancestor = tree.common_ancestor(*clades)
```

### Tree Comparison

```python
# Compare pairwise path lengths (not a topology test)
def compare_trees(tree1, tree2):
    """Compare branch-length distances for the same uniquely named taxa."""
    # Get terminal names
    taxa1 = set(t.name for t in tree1.get_terminals())
    taxa2 = set(t.name for t in tree2.get_terminals())

    # Check if they have same taxa
    if taxa1 != taxa2:
        return False, "Different taxa"

    # Compare distances
    differences = []
    for taxon1 in taxa1:
        for taxon2 in taxa1:
            if taxon1 < taxon2:
                dist1 = tree1.distance(taxon1, taxon2)
                dist2 = tree2.distance(taxon1, taxon2)
                if abs(dist1 - dist2) > 0.01:
                    differences.append((taxon1, taxon2, dist1, dist2))

    return len(differences) == 0, differences
```

## Tree Manipulation

### Pruning Trees

```python
# Prune (remove) specific taxa
import copy
tree_copy = copy.deepcopy(tree)
tree_copy.prune("Species_A")

# Keep only specific taxa
taxa_to_keep = ["Species_B", "Species_C", "Species_D"]
terminals = tree_copy.get_terminals()
for terminal in terminals:
    if terminal.name not in taxa_to_keep:
        tree_copy.prune(terminal)
```

### Collapsing Short Branches

```python
# Collapse branches shorter than threshold
def collapse_short_branches(tree, threshold=0.01):
    """Collapse branches shorter than threshold."""
    tree.collapse_all(lambda clade: clade.branch_length is not None
                      and clade.branch_length < threshold)
    return tree
```

### Ladderizing Trees

```python
# Ladderize tree (sort branches by size)
tree.ladderize()  # ascending order
tree.ladderize(reverse=True)  # descending order
```

### Rerooting Trees

```python
# Reroot at midpoint
tree.root_at_midpoint()

# Reroot with outgroup
outgroup = tree.find_any(name="Outgroup_Species")
tree.root_with_outgroup(outgroup)

# Reroot at internal node
internal = tree.get_nonterminals()[0]
tree.root_with_outgroup(internal)
```

## Tree Visualization

### Basic ASCII Drawing

```python
# Draw tree to console
Phylo.draw_ascii(tree)

# Draw with custom format
Phylo.draw_ascii(tree, column_width=80)
```

### Matplotlib Visualization

```python
import matplotlib.pyplot as plt
from Bio import Phylo

# Simple plot
fig = plt.figure(figsize=(10, 8))
axes = fig.add_subplot(1, 1, 1)
Phylo.draw(tree, axes=axes)
plt.show()

# Customize plot
fig = plt.figure(figsize=(10, 8))
axes = fig.add_subplot(1, 1, 1)
Phylo.draw(tree, axes=axes, do_show=False)
axes.set_title("Phylogenetic Tree")
plt.tight_layout()
pl

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

