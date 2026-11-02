---
id: sciref-datamol-reactions-data
name: "Scientific Ref: Datamol reactions and bundled data (0.13.0)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (datamol): Datamol reactions and bundled data (0.13.0)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "datamol reactions"
  - "datamol reactions and bundled data (0.13.0)"
keywords:
  - "datamol"
  - "reactions"
  - "specialized"
  - "scientific"
  - "reference"
---

# Datamol reactions and bundled data (0.13.0)

Sources: [reaction API](https://docs.datamol.io/stable/api/datamol.reactions.html),
[data API](https://docs.datamol.io/stable/api/datamol.data.html), and released source.

## Reaction outputs and validation

`dm.reactions.apply_reaction(rxn, reactants, product_index=None,
single_product_group=False, as_smiles=False, rm_attach=False, sanitize=True)`
returns all product groups by default. With `product_index=None`, each group is a list
of product molecules. `product_index=0` instead selects the first product slot from
each group, producing a flat list. No matches return `[]`; failed sanitization can leave
`None` entries. `single_product_group=True` randomly chooses a group; it is not a
chemically ranked or deterministically first product. Retain all groups for enumeration.

```python
import datamol as dm
from rdkit.Chem import rdChemReactions
# Computational substitution pattern; no reaction conditions or yield are implied.
rxn = rdChemReactions.ReactionFromSmarts("[C:1](=[O:2])[OH:3]>>[C:1](=[O:2])[Cl:3]")
reactant = dm.to_mol("CC(=O)O")
groups = dm.reactions.apply_reaction(rxn, (reactant,), single_product_group=False)
products = [p for group in groups for p in group if p is not None]
product_smiles = sorted({dm.to_smiles(p) for p in products})
assert product_smiles == ["CC(=O)Cl"]
assert dm.reactions.apply_reaction(rxn, (dm.to_mol("CC"),)) == []
```

`rxn_from_smarts`, `rxn_from_block`, and `rxn_from_block_file` initialize reaction
objects; `rxn_to_smarts`, `rxn_to_block`, and `rxn_to_block_file` export them.
`can_react(rxn, mol)` checks reactant-pattern matching. `is_reaction_ok(rxn)` invokes
RDKit preprocessing/sanitization; it does not validate synthetic feasibility, conditions,
selectivity, safety or yield. Atom mapping tracks atoms in a computational template;
it does not imply atom-balanced laboratory chemistry. Deduplicate products by an explicit
stereochemistry/tautomer policy and keep input/product-group provenance.

These simple templates were executed on matching toy reactants; they are illustrative
chemical transformations, not validated synthesis instructions:

```python
amide_rxn = rdChemReactions.ReactionFromSmarts(
    "[N;H1,H2:1].[C:2](=[O:3])[OH]>>[N:1][C:2](=[O:3])"
)
suzuki_rxn = rdChemReactions.ReactionFromSmarts(
    "[c:1][Br].[c:2][B]([OH])[OH]>>[c:1][c:2]"
)
esterification = rdChemReactions.ReactionFromSmarts(
    "[C:1][OH:2].[C:3](=[O:4])[Cl]>>[C:1][O:2][C:3](=[O:4])"
)
```

For a library, preserve `(source_id, product_group, product_slot)` and log both empty
matches and invalid products; do not silently append nested groups as though they were Mol.

## Bundled datasets

| Call | Verified 0.13.0 snapshot |
|---|---|
| `dm.data.cdk2(as_df=True, mol_column="mol")` | 47 rows, including structures, ID, Cluster and modelling metadata. No measured activity column is supplied. |
| `dm.data.freesolv(as_df=True)` | 642 rows: `iupac`, `smiles`, `expt`, `calc`; hydration free energies in kcal/mol. No Mol column by default. |
| `dm.data.solubility(as_df=True, mol_column="mol")` | 1,282 rows: `mol`, `ID`, `NAME`, `SOL`, `SOL_classification`, `smiles`, `split`. Target is `SOL`, not `solubility`. |

All three accept `as_df=False` for molecules. These are bundled toy snapshots, not a
fresh download of the originating datasets. Inspect target definitions, units, duplicates,
license and source provenance before drawing research conclusions. A bundled split is
an example boundary, not evidence that it is scaffold-disjoint or suitable for your task.

```python
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
sol = dm.data.solubility()
train = sol.loc[sol["split"] == "train"]
test = sol.loc[sol["split"] == "test"]
# One molecule per call: dm.to_fp does not featurize a pandas Series.
X_train = np.stack([dm.to_fp(m, radius=2) for m in train["mol"]])
X_test = np.stack([dm.to_fp(m, radius=2) for m in test["mol"]])
model = RandomForestRegressor(n_estimators=20, random_state=42, n_jobs=1)
model.fit(X_train, train["SOL"].astype(float))
predictions = model.predict(X_test)
mae = mean_absolute_error(test["SOL"].astype(float), predictions)
print(f"Toy held-out MAE: {mae:.3f}")
```

This small executed baseline checks the API and feature/label alignment. It is not a
benchmark claim or evidence of prospective predictive performance.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

