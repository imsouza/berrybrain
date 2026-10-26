---
id: sciref-datamol-core-workflows
name: "Scientific Ref: Datamol core workflows (0.13.0)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (datamol): Datamol core workflows (0.13.0)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "datamol core workflows"
  - "datamol core workflows (0.13.0)"
keywords:
  - "datamol"
  - "core"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
---

# Datamol core workflows (0.13.0)

These local snippets were executed with Python 3.13 / RDKit 2026.03.6. Run the setup
first. Each step preserves the relationship between input structures and outputs.
Use [the pipeline patterns](workflow_patterns.md) for rejected-row and selection provenance.

## 1. Molecules and explicit structure policy

```python
import datamol as dm
import numpy as np
import pandas as pd
from pathlib import Path
from tempfile import TemporaryDirectory

smiles_list = ["CCO", "CCCO", "c1ccccc1O", "c1ccccc1CCN", "c1ccncc1", "CC(=O)O"]
mols = [dm.to_mol(s) for s in smiles_list]
assert all(m is not None for m in mols)
with dm.without_rdkit_log():
    invalid = dm.to_mol("invalid_smiles")
assert invalid is None
mol = mols[0]  # keep a valid molecule for subsequent examples
smiles = dm.to_smiles(mol, canonical=True, isomeric=True)
inchi, inchikey, selfies = dm.to_inchi(mol), dm.to_inchikey(mol), dm.to_selfies(mol)
assert dm.from_selfies(selfies, as_mol=True) is not None
# Illustrative, deliberately specified policy for these ordinary organic molecules.
standardized = dm.standardize_mol(mol, disconnect_metals=False, normalize=True,
                                  reionize=True, uncharge=False, stereo=True)
assert standardized is not None
```

Choose the policy from the assayed entity before standardizing. Preserve source structures;
metal disconnection, salt/fragment selection and neutralization are not universally appropriate.
Sanitization/fixing is not evidence that an invalid source structure has been recovered.

## 2. Local I/O and portable tables

```python
with TemporaryDirectory() as directory:
    base = Path(directory)
    dm.to_sdf(mols, base / "compounds.sdf")
    df = dm.read_sdf(base / "compounds.sdf", as_df=True, mol_column="mol",
                     discard_invalid=False)
    assert len(df) == len(mols)
    dm.to_smi(mols, base / "molecules.smi", error_if_empty=True)
    assert len(dm.read_smi(base / "molecules.smi")) == len(mols)
    dm.to_xlsx(df, base / "compounds.xlsx", mol_column="mol")
    portable = df.drop(columns="mol")
    dm.save_df(portable, str(base / "compounds.parquet"))
    assert len(dm.open_df(str(base / "compounds.parquet"))) == len(mols)
```

`read_sdf` returns a list unless `as_df=True`; `open_df` selects DataFrame mode for SDF.
Do not serialize Python Mol objects into Parquet/CSV. Use SMILES plus scalar properties
and reconstruct on read. See [I/O contracts](io_module.md) for rejection handling,
file-format parameters, and illustrative cloud paths. Remote credentials/writes were not tested.

## 3. Descriptors with an explicit feature schema

```python
properties = {"mw": "MolWt", "logp": "MolLogP", "hbd": "NumHDonors",
              "hba": "NumHAcceptors", "tpsa": "TPSA"}
desc_df = dm.descriptors.batch_compute_many_descriptors(
    mols, properties_fn=properties, add_properties=False, n_jobs=1,
)
passes_screen = ((desc_df["mw"] <= 500) & (desc_df["logp"] <= 5)
                 & (desc_df["hbd"] <= 5) & (desc_df["hba"] <= 10))
selected = [m for m, keep in zip(mols, passes_screen) if keep]
assert len(desc_df) == len(mols)
n_aromatic = dm.descriptors.n_aromatic_atoms(mol)
n_stereo = dm.descriptors.n_stereo_centers(mol)
n_unspecified = dm.descriptors.n_stereo_centers_unspecified(mol)
n_rigid = dm.descriptors.n_rigid_bonds(mol)
```

This defines average MolWt and RDKit donor/acceptor counts. Datamol defaults instead use
exact mass (`mw`), `clogp`, `n_lipinski_hbd`, and `n_lipinski_hba`. See
[descriptor semantics](descriptors_viz.md). Screen passage is not validated drug-likeness.

## 4. Fingerprints and similarities

```python
fp_options = dict(fp_type="ecfp", radius=2, fpSize=2048, includeChirality=True)
fps = np.stack([dm.to_fp(m, **fp_options) for m in mols])
distance_matrix = dm.pdist(mols, n_jobs=1, **fp_options)  # square by default
query_distances = dm.cdist(mols[:1], mols, n_jobs=1, **fp_options)
nearest = np.argsort(query_distances[0])
assert nearest[0] == 0 and np.isclose(query_distances[0, 0], 0)
for fp_type in ["maccs", "topological", "atompair", "rdkit"]:
    assert dm.to_fp(mol, fp_type=fp_type).ndim == 1
```

ECFP radius 2 is ECFP4; Datamol defaults to radius 3. Use `fpSize`, not `n_bits`.
`pdist(..., squareform=False)` returns condensed distances; calling SciPy `squareform`
on the default square output would convert it into a vector. Binary Tanimoto similarity
is 1 - distance. Compare libraries only with the same fingerprint configuration.

## 5. Clustering and diversity

```python
from functools import partial
feature_fn = partial(dm.to_fp, as_array=False, **fp_options)
cluster_indices, cluster_molecules = dm.cluster_mols(mols, cutoff=0.2, feature_fn=feature_fn)
for indices, molecules in zip(cluster_indices, cluster_molecules):
    assert len(indices) == len(molecules)
picked_indices, diverse_mols = dm.pick_diverse(mols, npick=min(3, len(mols)),
                                              feature_fn=feature_fn, seed=42)
centroid_indices, centroid_mols = dm.pick_centroids(mols, npick=3, feature_fn=feature_fn)
```

Both selectors return `(indices, molecules)`; preserve indices for labels/IDs. Butina needs
quadratic distance storage. Select a resource budget, not a universal molecule-count cutoff.
The sphere centroid selector may return fewer than requested due to its distance threshold.

## 6. Scaffolds and a toy scaffold-disjoint split

```python
from collections import defaultdict
import random
scaffold_groups = defaultdict(list)
for index, molecule in enumerate(mols):
    key = dm.to_smiles(dm.to_scaffold_murcko(molecule))
    scaffold_groups[key].append(index)
keys = sorted(scaffold_groups)
random.Random(42).shuffle(keys)
split_index = int(0.8 * len(keys))
train_keys, test_keys = keys[:split_index], keys[split_index:]
train_indices = [i for key in train_keys for i in scaffold_groups[key]]
test_indices = [i for key in test_keys for i in scaffold_groups[key]]
assert set(train_keys).isdisjoint(test_keys)
assert set(train_indices).isdisjoint(test_indices)
```

This divides scaffold groups, not exactly 80% of molecules. All acyclic molecules share an
empty Murcko scaffold here; report that policy and inspect resulting class/size balance.
Validate chemical duplicate/analog and task-specific leakage separately.

## 7. Fragmentation

```python
from collections import Counter
fragment_counts = Counter()
for molecule in mols:
    fragments = dm.fragment.brics(molecule, remove_parent=True, fix=False)
    fragment_counts

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

