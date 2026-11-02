---
id: sciref-etetoolkit-visualization
name: "Scientific Ref: ETE 4 Visualization"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (etetoolkit): ETE 4 Visualization"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "etetoolkit visualization"
  - "ete 4 visualization"
keywords:
  - "etetoolkit"
  - "visualization"
  - "specialized"
  - "scientific"
  - "reference"
---

# ETE 4 Visualization

ETE 4 has two drawing systems:

- **SmartView**: current web-based explorer and adaptive renderer; best for
  interactive work and very large trees
- **Treeview**: optional Qt renderer retained for static PNG, PDF, and SVG

Do not mix their layout or face classes. SmartView classes live under
`ete4.smartview`; Qt classes live under `ete4.treeview`.

## Renderer Decision

Use SmartView when:

- Exploring, searching, collapsing, or editing interactively
- Serving a tree locally or through an SSH tunnel
- Exploring from a long-lived Jupyter kernel through the browser
- Creating a raster PNG screenshot
- Manually downloading the current browser view as SVG or PNG
- Working with a tree too large to draw fully expanded

Use Qt treeview when:

- Programmatic or headless output must be PDF or SVG
- Physical drawing dimensions or raster DPI matter
- Maintaining an existing ETE treeview layout

## Installation

Interactive SmartView is included in the base package:

```bash
uv pip install "ete4==4.4.0"
```

Static SmartView screenshots use Selenium:

```bash
uv pip install "ete4[render-sm]==4.4.0"
```

Qt rendering uses PyQt6:

```bash
uv pip install "ete4[treeview]==4.4.0"
```

## Interactive SmartView

### Python

```python
from pathlib import Path

from ete4 import Tree

with Path("tree.nw").open(encoding="utf-8") as handle:
    tree = Tree(handle, parser=1)

tree.explore()
```

With no `layouts` argument, ETE applies `BASIC_LAYOUT`, which displays leaf
names, branch lengths, and support.

`explore()` returns immediately. A standalone script must keep the process
alive, for example with `input()`, or use `keep_server=True`. The bundled
visualization helper waits and stops the server cleanly.

In Jupyter/IPython, SmartView is still browser-based; the current documentation
does not provide an inline SmartView widget. Keep the kernel alive and open the
served URL.

### Command line

```bash
ete4 explore -t tree.nw --src_tree_format 1
```

Inspect the active release's full options:

```bash
ete4 explore --help
```

The CLI supports basic source-tree selection and parser options. Although ETE
4.4.0 help exposes `--face`, its handler does not apply that argument; use
Python `Layout` objects for customization.

### Control the server

```python
tree.explore(
    host="127.0.0.1",
    port=5000,
    open_browser=False,
)
```

Keep the default loopback binding unless remote access is intentionally
secured. For a remote host, tunnel the loopback port:

```bash
ssh -L 5000:localhost:5000 user@remote-host
```

Then open `http://localhost:5000` locally. Do not expose an unauthenticated
explorer on `0.0.0.0` to an untrusted network.

## SmartView Layouts

A SmartView `Layout` combines:

- `draw_tree(tree)`: tree-wide style and header/legend faces
- `draw_node(node[, collapsed])`: styles and faces for individual nodes
- `name`: GUI identifier
- `cache_size`: memoization control for node drawing

### Circular tree with labels and support

```python
from ete4 import Tree
from ete4.smartview import Layout, PropFace, TextFace

tree = Tree("((A:1,B:1)95:0.2,C:1);", parser="support")


def draw_tree(_tree):
    yield {
        "shape": "circular",
        "node-height-min": 8,
        "content-height-min": 4,
    }
    yield TextFace(
        "Example phylogeny",
        fs_min=8,
        fs_max=22,
        position="header",
    )


def draw_node(node):
    if node.is_leaf:
        yield PropFace(
            "name",
            fs_min=4,
            fs_max=16,
            position="right",
        )
        return

    if node.support is not None:
        yield TextFace(
            f"{node.support:g}",
            fs_min=3,
            fs_max=12,
            style={"fill": "#555"},
            position="top",
        )


layout = Layout(
    "circular labels and support",
    draw_tree=draw_tree,
    draw_node=draw_node,
)

tree.explore(layouts=[layout])
```

### Conditional node styling

Support values may be fractions or percentages. Set one explicit convention
for the entire source; a value of 1 cannot disambiguate them:

```python
import math
from ete4 import Tree
from ete4.smartview import Layout, PropFace

tree = Tree("((A:1,B:1)95:0.2,C:1);", parser="support")
SUPPORT_MAX = 100  # use 1 only for a verified fractional source


def support_fraction(value):
    if value is None:
        return None
    if not math.isfinite(value) or not 0 <= value <= SUPPORT_MAX:
        raise ValueError("Support is outside the declared source range")
    return value / SUPPORT_MAX


def draw_node(node):
    if node.is_leaf:
        yield PropFace("name", position="right")

    support = support_fraction(node.support)
    if support is None:
        color = "#888"
    elif support >= 0.9:
        color = "#1b7837"
    elif support >= 0.7:
        color = "#e08214"
    else:
        color = "#b2182b"

    yield {
        "dot": {
            "shape": "circle",
            "radius": 5,
            "fill": color,
        }
    }


layout = Layout("support colors", draw_node=draw_node)
tree.explore(layouts=[layout])
```

### Tree style keys

Common tree-wide keys:

- `shape`: `"rectangular"` or `"circular"`
- `radius`: circular layout radius
- `angle-start`, `angle-end`, `angle-span`: circular extent
- `node-height-min`: collapse threshold in pixels
- `content-height-min`: minimum height before faces appear
- `collapsed`: collapsed-node style
- `show-popup-props`, `hide-popup-props`: property disclosure
- `is-leaf-fn`: dynamic terminal-node rule
- `box`, `dot`, `hz-line`, `vt-line`: default CSS-like styles

Example:

```python
tree_style = {
    "shape": "circular",
    "angle-start": -180,
    "angle-span": 180,
    "node-height-min": 10,
    "collapsed": {
        "shape": "outline",
        "fill-opacity": 0.6,
    },
    "show-popup-props": ["name", "dist", "support", "group"],
}

layout = Layout("semicircle", draw_tree=tree_style)
tree.explore(layouts=[layout])
```

Limit popup properties when nodes contain sensitive or irrelevant metadata.

## SmartView Faces

Common classes from `ete4.smartview`:

- `TextFace`: literal text
- `PropFace`: one node property with optional formatting
- `EvalTextFace`: expression-derived text
- `CircleFace`, `RectFace`, `BoxFace`: shapes
- `ImageFace`: image
- `SeqFace`: molecular sequence
- `LegendFace`: legend

Positions include `top`, `bottom`, `left`, `right`, and `aligned`; tree-level
text can also use `header`.

### Aligned metadata columns

```python
fro

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

