---
id: sciref-cobrapy-api-quick-reference
name: "Scientific Ref: COBRApy API reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (cobrapy): COBRApy API reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "cobrapy api quick reference"
  - "cobrapy api reference"
keywords:
  - "cobrapy"
  - "api"
  - "quick"
  - "reference"
  - "specialized"
  - "scientific"
---

# COBRApy API reference

Checked against cobra **0.32.1** installed signatures/source and current official
docs. Examples with `model` assume a fresh `load_model("textbook")`; placeholders
such as `filename` are illustrative, not standalone runnable commands.

## Model I/O and repository contracts

```python
from cobra.io import (
    load_model, read_sbml_model, write_sbml_model,
    load_json_model, save_json_model, load_yaml_model, save_yaml_model,
    load_matlab_model, save_matlab_model,
)

model = load_model("textbook")  # Local, model.id == "e_coli_core"
# Also local: load_model("iJO1366"), load_model("salmonella")
# Remote illustrative calls; adapters may fail at redirects (see below):
# model = load_model("e_coli_core")
# model = load_model("iML1515")

# Illustrative file I/O: use your actual paths.
# model = read_sbml_model("model.xml.gz")
# write_sbml_model(model, "model.xml")
# save_json_model(model, "model.json", pretty=True)
# model = load_json_model("model.json")
# save_yaml_model(model, "model.yml")
# model = load_yaml_model("model.yml")
# save_matlab_model(model, "model.mat", varname="model")
# model = load_matlab_model("model.mat", variable_name="model")
```

MATLAB I/O needs SciPy (`cobra[array]`). Keep the default SBML `f_replace` mapping
unless intentionally preserving SBML-encoded IDs; `f_replace={}` disables prefix
and character conversion. Verify identifiers after round-trip before selecting an
objective. Formats may not retain arbitrary custom solver constraints; store those
separately and reconstruct them on reload.

`load_model(model_id, repositories=..., cache=True)` searches bundled data, BiGG,
then BioModels. In released 0.32.1 the `cache` argument is unused despite its
docstring: save downloaded files explicitly. A non-404 HTTP failure aborts lookup;
it does not necessarily fall through to the next provider. Repository-specific
IDs are not interchangeable. The BioModels adapter only supports a directly listed
XML file; OMEX-only records require an explicitly chosen SBML extraction workflow.

Verified unauthenticated provider routes (2026-09-30):

| Provider | Request and response | Current adapter caveat |
| --- | --- | --- |
| BiGG | `GET https://bigg.ucsd.edu/static/models/{id}.xml.gz` returns gzip-compressed SBML; iML1515 parsed as 2,712 reactions | 0.32.1 uses HTTP and does not follow the HTTP-to-HTTPS redirect |
| BioModels files | `GET https://www.biomodels.org/model/files/{id}` with `Accept: application/json`; `main` is a list of file records with `name` and `fileSize` | 0.32.1 uses the bare hostname and does not follow its listing redirect |
| BioModels download | `GET https://www.biomodels.org/model/download/{id}?filename={name}` returns the selected file; follow redirects | Select an actual XML name from the listing, not an invented name or arbitrary first file |

These are single-model/file operations with no pagination or credentials. The
`MODEL1510010000` listing and selected XML download were executed and parsed. That BioModels file lacked an optimization objective and many explicit flux bounds,
so its successful parse is not a validated FBA model. SDK
remote failures were observed separately; they do not mean the services retired.

A bounded BiGG fallback, executed on iML1515:

```python
from pathlib import Path
from urllib.request import urlopen
from cobra.io import read_sbml_model

path = Path("iML1515.xml.gz")  # Use the task's output directory.
with urlopen("https://bigg.ucsd.edu/static/models/iML1515.xml.gz", timeout=30) as response:
    data = response.read(16 * 1024 * 1024 + 1)
if len(data) > 16 * 1024 * 1024:
    raise ValueError("Model exceeds this example's 16 MiB download limit")
path.write_bytes(data)
model = read_sbml_model(path)
assert len(model.reactions) == 2712
```

For BioModels, fetch the JSON listing, choose `main` entries whose `name` ends in
`.xml`, URL-encode that filename using `urllib.parse.urlencode`, and use the download
route in the table with the same finite timeout/size check. Save the original file,
retrieval date and checksum. Do not assume every SBML record is a constraint-based
metabolic model with the required objective and flux bounds.

## Core objects and editing

```python
from cobra import Model, Reaction, Metabolite, Gene
from cobra.io import load_model

model = load_model("textbook")
reaction = model.reactions.get_by_id("PFK")
metabolite = model.metabolites.get_by_id("atp_c")
print(reaction.bounds, reaction.gene_reaction_rule, metabolite.formula)
print(model.exchanges, model.demands, model.sinks, model.boundary)

# DictList.query uses a regular expression, case-sensitive by default.
import re
matches = model.reactions.query(re.compile("atp", re.IGNORECASE))
glycolytic = model.reactions.query(lambda r: r.subsystem == "Glycolysis")
assert "PFK" in model.reactions

# Temporary changes are restored when the model context exits.
with model:
    reaction.bounds = (0, 5)
    reaction.gene_reaction_rule = "gene1 and (gene2 or gene3)"
    model.genes.get_by_id("gene1").knock_out()
    solution = model.optimize()
```

Use `add_reactions([reaction])`, not removed `add_reaction`. Set GPRs on reactions
so associated genes and reverse links are updated; do not mutate `model.genes`
directly to remove genes. For permanent deletion use
`cobra.manipulation.remove_genes(model, ["gene_id"], remove_reactions=True)` and
inspect affected GPRs/reactions. `remove_reactions([...])` accepts IDs or objects;
`remove_metabolites([...], destructive=False)` removes them from stoichiometries
and needs biological review.

`model.copy()` creates an independent model. To form a subset, copy each reaction:
`new_model.add_reactions([r.copy() for r in chosen_reactions])`; adding the same
Reaction objects to another model risks moving their model/solver associations.
A reaction is reversible when **both** `lower_bound < 0` and `upper_bound > 0`.

### Balanced toy network and gap filling

A mass/charge-balanced isomerization illustrates building without creating an
unphysical ATP source. Boundary reactions deliberately connect the model to its
environment. The toy's demand objective is product export, not a growth rate.

```python
from cobra import Model, Reaction, Metabolite
from cobra.flux_analysis import gapfill

model = Model("toy")
model.solver = "glpk"
a_e = Metabolite("a_e", formula="C6H12O6", charge=0, compartment="e")
a_c = Metabolite("a_c", formula="C6H12O6", charge=0, compartment="c")
b_c = Metabolite("b_c", formula="C6H1

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

