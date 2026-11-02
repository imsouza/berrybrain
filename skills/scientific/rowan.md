---
id: sci-rowan
name: "Scientific: rowan"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Rowan is a cloud-native molecular modeling and medicinal-chemistry workflow platform with a Python API. Use for pKa and macropKa prediction, conformer and tautomer ensembles, docking and analogue docking, protein-ligand cofolding, MSA generation, molecular dynamics, permeability,"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "rowan"
keywords:
  - "rowan"
  - "cloud"
  - "native"
  - "molecular"
  - "modeling"
  - "medicinal"
---

# Rowan: Cloud-Native Molecular-Modeling and Drug-Design Workflows

## Overview

Rowan is a cloud-native workflow platform for molecular simulation, medicinal chemistry, and structure-based design. Its Python API exposes a unified interface for small-molecule modeling, property prediction, docking, molecular dynamics, and AI structure workflows.

Use Rowan when you want to run medicinal-chemistry or molecular-design workflows programmatically without maintaining local HPC infrastructure, GPU provisioning, or a collection of separate modeling tools. The service manages hosted compute and results; available workflows depend on the account.

## When to use Rowan

**Rowan is a good fit for:**

- Quantum chemistry, semiempirical methods, or neural network potentials
- Batch property prediction (pKa, descriptors, permeability, solubility)
- Conformer and tautomer ensemble generation
- Docking workflows (single-ligand, analogue series, pose refinement)
- Protein-ligand cofolding and MSA generation
- Multi-step chemistry pipelines (e.g., tautomer search → docking → pose analysis)
- Batch medicinal-chemistry campaigns where you need consistent, scalable infrastructure

**Rowan is not the right fit for:**
- Simple molecular I/O (use RDKit directly)
- Methods or element/charge regimes outside the selected engine's documented support

## Quick start

```bash
uv pip install "rowan-python==3.2.0"
```

```python
import rowan
# Reads ROWAN_API_KEY from the environment.

# Descriptors require a 3D Molecule, not a bare SMILES string.
mol = rowan.Molecule.from_smiles("CC(=O)Oc1ccccc1C(=O)O")
wf = rowan.submit_descriptors_workflow(mol, name="aspirin")
result = wf.result()

print(result.descriptors["MW"])       # exact/monoisotopic mass
print(result.descriptors["SLogP"])
print(result.descriptors["TopoPSA"])  # topological PSA
```

This submits a hosted calculation and consumes credits. Examples target
[`rowan-python` 3.2.0](https://pypi.org/project/rowan-python/3.2.0/), reviewed
2026-09-30 against the released SDK and [official reference](https://docs.rowansci.com/api/python/v3/).
Local schema/serialization smoke tests used `stjames` 0.0.279. Hosted examples
are illustrative: no authenticated workflows were run for this refresh. Lock
both package versions for a reproducible campaign.

## Installation

```bash
uv pip install "rowan-python==3.2.0"
# Lock dependencies in your own environment; do not install the unrelated "rowan" package.
```

## Authentication and account access

### Authentication

Set an API key via environment variable (recommended):

```bash
export ROWAN_API_KEY="your_api_key_here"
```

Or set directly in Python:

```python
import rowan
rowan.api_key = "your_api_key_here"
```

Verify authentication:

```python
import rowan
user = rowan.whoami()  # Returns user info if authenticated
print(f"User: {user.email}")
print(f"Credits available: {user.credits_available_string()}")
print(user.enabled_workflows)  # Account-specific backend workflow slugs
```

## Molecule input formats

Use SMILES for topology-based methods and real 3D structures for geometry-based
methods. SMARTS is a substructure-query language, not a general workflow molecule
input; convert InChI with a chemistry toolkit before passing a supported input.
Record stereochemistry, charge, protonation state, and the original identifier.
Canonicalization alone does not resolve these scientific choices.

### SMILES strings versus molecule objects

- pKa: `starling` and `chemprop_nevolianis2025` require a SMILES string;
  `gxtb_wagen2026` (default) and `aimnet2_wagen2024` require coordinates.
- Conformer search: SMILES works with OpenConf (default) or ETKDG; CREST/MCMM
  require a 3D molecule.
- Membrane permeability: `gnn-mtl` requires SMILES; `pypermm` requires a 3D molecule.
- ADMET, LogP, macropKa, and solubility are SMILES-based; pose-analysis MD needs
  ligand SMILES **and a protein complex containing its bound pose**.
- Descriptors, tautomers, docking, analogue docking, BDE, NMR, and Fukui need a
  `rowan.Molecule`, `stjames.Molecule`, or RDKit molecule with a conformer.
  `Chem.MolFromSmiles()` alone has no coordinates. Generate them explicitly with
  `rowan.Molecule.from_smiles()` or import an existing geometry. For analogue
  docking, preserve the reference pose in the receptor's coordinate frame.

**Tip:** Use RDKit to validate SMILES before submission:

```python
from rdkit import Chem
smiles = "CCO"
mol = Chem.MolFromSmiles(smiles)
if mol is None:
    raise ValueError(f"Invalid SMILES: {smiles}")
```

## Core usage pattern

Most Rowan tasks follow the same three-step pattern:

1. **Submit** a workflow
2. **Wait** for completion (with optional streaming)
3. **Retrieve** typed results with convenience properties

```python
import rowan

# 1. Submit — named functions build and validate workflow-specific payloads
workflow = rowan.submit_descriptors_workflow(
    rowan.Molecule.from_smiles("CC(=O)Oc1ccccc1C(=O)O"),
    name="aspirin descriptors",
)

# 2. & 3. Wait and retrieve
result = workflow.result()  # Blocks until done (default: wait=True, poll_interval=5)
print(result.data)              # Raw dict
print(result.descriptors["MW"]) # exact mass; no result.molecular_weight property
```

For long-running workflows, use streaming:

```python
for partial in workflow.stream_result(poll_interval=5):
    print(f"Complete: {partial.complete}")  # bool, not a percentage
    print(partial.data)
```

### result() vs. stream_result()

| Pattern | Use when |
|---|---|
| `result()` | The process can block for completion |
| `stream_result()` | Polling snapshots are useful while the job runs |

`stream_result()` polls; it is not a server-pushed event stream. Partial typed
properties may be unavailable, so inspect `.data` until `.complete` is true.
`result(wait=False)` can return partial data or raise `WorkflowError` if no data
exists yet. `done()` includes failed and stopped runs, not only successes.

## Working with results

Rowan's API includes **typed workflow result objects** with convenience properties.

### Using typed properties and .data

Results have two access patterns:

1. **Convenience properties** (recommended first): `result.descriptors`, `result.best_pose`, `result.scores`. Result classes differ: conformer search uses `get_energies()` and `get_conformers()` methods.
2. **Raw fallback**: `result.data` — raw dictionary from the API

Example:

```python
result = rowan.submit_descriptors_workflow(
    rowan.Molecule.from_s

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

