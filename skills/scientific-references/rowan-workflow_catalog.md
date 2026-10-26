---
id: sciref-rowan-workflow-catalog
name: "Scientific Ref: Rowan Workflow Catalog"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (rowan): Rowan Workflow Catalog"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "rowan workflow catalog"
keywords:
  - "rowan"
  - "workflow"
  - "catalog"
  - "specialized"
  - "scientific"
  - "reference"
---

# Rowan Workflow Catalog

Submission code, options, and result shapes for the common workflow categories, followed
by the SDK workflow directory. Hosted calls are illustrative, not authenticated service tests.
The source baseline is [rowan-python 3.2.0](https://pypi.org/project/rowan-python/3.2.0/);
see the [official workflow reference](https://docs.rowansci.com/api/python/v3/).

## Common workflow categories

### 1. Descriptors

A lightweight entry point for batch triage, SAR, or exploratory scripts.

```python
wf = rowan.submit_descriptors_workflow(
    rowan.Molecule.from_smiles("CC(=O)Oc1ccccc1C(=O)O"),
    name="aspirin descriptors",
)

result = wf.result()
print(result.descriptors["MW"])       # exact/monoisotopic mass
print(result.descriptors["SLogP"])    # model-dependent value
print(result.descriptors["TopoPSA"])  # topological PSA
print(result.descriptors["nHBAcc"])   # H-bond acceptor count
```

**Common descriptor keys:**

| Key | Description | Typical drug range |
|-----|-------------|-------------------|
| `MW` | Exact/monoisotopic mass (Da), not average MW | Do not substitute for average MW in strict filters |
| `SLogP` | Calculated LogP (lipophilicity) | -2 to +5 |
| `TopoPSA` | Topological polar surface area (Å²) | <140 for oral bioavailability |
| `TPSA` | 3D charged surface area, not topological PSA | — |
| `nHBDon` | H-bond donor count | ≤5 (Lipinski) |
| `nHBAcc` | H-bond acceptor count | ≤10 (Lipinski) |
| `nRot` | Rotatable bond count | <10 for oral drugs |
| `nRing` | Ring count | — |
| `nHeavyAtom` | Heavy atom count | — |
| `FilterItLogS` | Estimated aqueous solubility (LogS) | >-4 preferred |
| `Lipinski` | Lipinski Ro5 pass (1.0) or fail (0.0) | — |

The descriptor count and available keys depend on the service calculation; do not
hardcode a count. `result.descriptors` may be `None` before completion. For average
molecular weight, calculate it separately (for example, RDKit `MolWt`).

### 2. Microscopic pKa

For protonation-state energetics and acid/base behavior of a specific structure.

Four methods are available:

| Method | Input | Speed | Covers | Use when |
|--------|-------|-------|--------|----------|
| `chemprop_nevolianis2025` | SMILES string | Fast | Deprotonation only | Acidic groups only; quick screening |
| `starling` | SMILES string | Fast | Acid + base | SMILES-based acid/base site prediction |
| `aimnet2_wagen2024` | 3D molecule object | Slower | Acid + base | You already have a 3D structure |
| `gxtb_wagen2026` (**default**) | 3D molecule object | Slower | Acid + base | Current SDK default; set `method=` explicitly for reproducibility |

```python
# Fast path: SMILES input with full acid+base coverage (use starling method when available)
wf = rowan.submit_pka_workflow(
    initial_molecule="c1ccccc1O",       # phenol SMILES; param is initial_molecule, not initial_smiles
    method="starling",   # fast SMILES method, covers acid+base; chemprop_nevolianis2025 is deprotonation-only
    name="phenol pKa",
)

result = wf.result()
print(result.strongest_acid)    # float or None; do not treat a past prediction as a guarantee
print(result.strongest_base)    # None when no basic site is found
print(result.conjugate_bases)   # list of pKaMicrostate objects
# Each microstate has .pka and .atom_index. SMILES methods populate .smiles;
# 3D methods populate .delta_g (kcal/mol); Chemprop also populates .uncertainty.
```

### 3. MacropKa

For pH-dependent protonation behavior across a range.

```python
wf = rowan.submit_macropka_workflow(
    initial_smiles="c1ncc[nH]1",  # imidazole
    method="starling",  # 3.2.0 also accepts starling_ii; pin the intended model
    min_pH=0,
    max_pH=14,
    min_charge=-2,  # default
    max_charge=2,   # default
    compute_aqueous_solubility=True,  # default
    name="imidazole macropKa",
)

result = wf.result()
print([(v.initial_charge, v.final_charge, v.pka) for v in result.pka_values])
print(result.logd_by_ph)               # list of (pH, logD) pairs
print(result.aqueous_solubility_by_ph) # list of (pH, log-solubility) pairs
print(result.isoelectric_point)        # isoelectric point
print(result.data)
# Raw keys use pKa_values, logD_by_pH, aqueous_solubility_by_pH.
# Consult the method documentation before interpreting solubility units.
```

### 4. Conformer search

For 3D ensemble generation when ensemble quality matters.

```python
wf = rowan.submit_conformer_search_workflow(
    initial_molecule="CCOC(=O)N1CCC(CC1)Oc1ncnc2ccccc12",
    name="conformer search",
)

result = wf.result()
print(result.num_conformers)
print(result.get_energies())    # absolute energies in Hartree
print(result.get_energies(relative=True))  # relative kcal/mol, minimum is zero
print(result.get_conformers())  # list of 3D molecules
print(result.get_conformer(0).molecule)  # get_conformer returns a Calculation

# There is no num_conformers submit parameter. Configure the generator and
# ensemble through conf_gen_settings.
```

### 5. Tautomer search

For heterocycles and systems where tautomer state affects downstream modeling.

```python
wf = rowan.submit_tautomer_search_workflow(
    initial_molecule=rowan.Molecule.from_smiles("O=c1cccc[nH]1"),
    name="2-pyridone tautomers",
)

result = wf.result()
print(result.best_tautomer)  # highest-weight Molecule, or None
print(result.tautomers)      # Tautomer records: energy (Hartree), weight, structure_uuids
print(result.molecules)      # List of molecule objects
```

### 6. Docking

For protein-ligand docking with optional pose refinement and conformer generation.

```python
# Upload protein once, reuse in multiple workflows
protein = rowan.upload_protein(
    name="CDK2",
    file_path="cdk2.pdb",
)

# Supply a validated pocket for this exact prepared receptor.
# pocket.json contains [[center_x, center_y, center_z], [size_x, size_y, size_z]] in Å.
import json
from pathlib import Path
pocket = json.loads(Path("pocket.json").read_text())

# Submit docking
wf = rowan.submit_docking_workflow(
    protein=protein,
    pocket=pocket,
    initial_molecule=rowan.Molecule.from_smiles(
        "Nc1ncc(F)cc1"
    ),
    docking_settings=rowan.VinaSettings(scoring_function="vinardo"),
    do_pose_refinement=True,
    do_csearch=True,
    name="lead docking",
)

result = wf.result()
print([s.score for s in result.scores])  # DockingScore records; .score is kcal/mol
print(result.best_pose)  # Mol object with 3D coordinates
print(result.data)  # Raw result dict
```

**Protein preparation tips:**


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

