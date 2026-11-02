---
id: sciref-biopython-structure
name: "Scientific Ref: Structural Bioinformatics with Bio.PDB"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (biopython): Structural Bioinformatics with Bio.PDB"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "biopython structure"
  - "structural bioinformatics with bio.pdb"
keywords:
  - "biopython"
  - "structure"
  - "specialized"
  - "scientific"
  - "reference"
  - "structural"
  - "bioinformatics"
---

# Structural Bioinformatics with Bio.PDB

## Overview

Bio.PDB provides tools for working with macromolecular 3D structures from PDB and mmCIF files. The module uses the SMCRA (Structure/Model/Chain/Residue/Atom) architecture to represent protein structures hierarchically.

## SMCRA Architecture

The Bio.PDB module organizes structures hierarchically:

```
Structure
  └── Model       (multiple models for NMR structures)
      └── Chain   (e.g., chain A, B, C)
          └── Residue  (amino acids, nucleotides, heteroatoms)
              └── Atom (individual atoms)
```

## Parsing Structure Files

### PDB Format

```python
from Bio.PDB import PDBParser

# Create parser
parser = PDBParser(QUIET=True)  # QUIET=True suppresses warnings

# Parse structure
structure = parser.get_structure("1crn", "1crn.pdb")

# Access basic information
print(f"Structure ID: {structure.id}")
print(f"Number of models: {len(structure)}")
```

### mmCIF Format

mmCIF format is more modern and handles large structures better:

```python
from Bio.PDB import MMCIFParser

# Create parser
parser = MMCIFParser(QUIET=True)

# Parse structure
structure = parser.get_structure("1crn", "1crn.cif")
```

### Download from PDB

```python
from Bio.PDB import PDBList

# Create PDB list object
pdbl = PDBList()

# Download PDB file
pdbl.retrieve_pdb_file("1CRN", file_format="pdb", pdir="structures/")

# Download mmCIF file
pdbl.retrieve_pdb_file("1CRN", file_format="mmCif", pdir="structures/")

# For an accession confirmed obsolete in the PDB archive only:
# pdbl.retrieve_pdb_file(obsolete_id, obsolete=True, file_format="mmCif", pdir="structures/")
```

## Navigating Structure Hierarchy

### Access Models

```python
# Get first model
model = structure[0]

# Iterate through all models
for model in structure:
    print(f"Model {model.id}")
```

### Access Chains

```python
# Get specific chain
chain = model["A"]

# Iterate through all chains
for chain in model:
    print(f"Chain {chain.id}")
```

### Access Residues

```python
# Iterate through residues in a chain
for residue in chain:
    print(f"Residue: {residue.resname} {residue.id[1]}")

# Get specific residue by ID
# Residue ID is tuple: (hetfield, sequence_id, insertion_code)
residue = chain[(" ", 10, " ")]  # Standard amino acid at position 10
```

### Access Atoms

```python
# Iterate through atoms in a residue
for atom in residue:
    print(f"Atom: {atom.name}, Coordinates: {atom.coord}")

# Get specific atom
ca_atom = residue["CA"]  # Alpha carbon
print(f"CA coordinates: {ca_atom.coord}")
```

### Alternative Access Patterns

```python
# Direct access through hierarchy
atom = structure[0]["A"][10]["CA"]

# Get all atoms
atoms = list(structure.get_atoms())
print(f"Total atoms: {len(atoms)}")

# Get all residues
residues = list(structure.get_residues())

# Get all chains
chains = list(structure.get_chains())
```

## Working with Atom Coordinates

### Accessing Coordinates

```python
# Get atom coordinates
coord = atom.coord
print(f"X: {coord[0]}, Y: {coord[1]}, Z: {coord[2]}")

# Get B-factor (temperature factor)
b_factor = atom.bfactor

# Get occupancy
occupancy = atom.occupancy

# Get element
element = atom.element
```

### Calculate Distances

```python
from Bio.PDB import Vector

# Calculate distance between two atoms
atom1 = residue1["CA"]
atom2 = residue2["CA"]

distance = atom1 - atom2  # Returns distance in Angstroms
print(f"Distance: {distance:.2f} Å")
```

### Calculate Angles

```python
from Bio.PDB.vectors import calc_angle

# Calculate angle between three atoms
angle = calc_angle(
    atom1.get_vector(),
    atom2.get_vector(),
    atom3.get_vector()
)
print(f"Angle: {angle:.2f} radians")
```

### Calculate Dihedrals

```python
from Bio.PDB.vectors import calc_dihedral

# Calculate dihedral angle between four atoms
dihedral = calc_dihedral(
    atom1.get_vector(),
    atom2.get_vector(),
    atom3.get_vector(),
    atom4.get_vector()
)
print(f"Dihedral: {dihedral:.2f} radians")
```

## Structure Analysis

### Secondary Structure (DSSP)

DSSP assigns secondary structure to protein structures:

```python
from Bio.PDB import DSSP, PDBParser

# Parse structure
parser = PDBParser()
structure = parser.get_structure("1crn", "1crn.pdb")

# Run DSSP (requires DSSP executable installed)
model = structure[0]
dssp = DSSP(model, "1crn.pdb")

# Access results
for residue_key in dssp.keys():
    dssp_data = dssp[residue_key]
    residue_id = residue_key[1]
    ss = dssp_data[2]  # Secondary structure code
    phi = dssp_data[4]  # Phi angle
    psi = dssp_data[5]  # Psi angle
    print(f"Residue {residue_id}: {ss}, φ={phi:.1f}°, ψ={psi:.1f}°")
```

Secondary structure codes:
- `H` - Alpha helix
- `B` - Beta bridge
- `E` - Strand
- `G` - 3-10 helix
- `I` - Pi helix
- `T` - Turn
- `S` - Bend
- `-` - Coil/loop

### Solvent Accessibility (DSSP)

```python
# Get relative solvent accessibility
for residue_key in dssp.keys():
    acc = dssp[residue_key][3]  # Relative accessibility
    print(f"Residue {residue_key[1]}: {acc:.2f} relative accessibility")
```

### Neighbor Search

Find nearby atoms efficiently:

```python
from Bio.PDB import NeighborSearch

# Get all atoms
atoms = list(structure.get_atoms())

# Create neighbor search object
ns = NeighborSearch(atoms)

# Find atoms within radius
center_atom = structure[0]["A"][10]["CA"]
nearby_atoms = ns.search(center_atom.coord, 5.0)  # 5 Å radius
print(f"Found {len(nearby_atoms)} atoms within 5 Å")

# Find residues within radius
nearby_residues = ns.search(center_atom.coord, 5.0, level="R")

# Find chains within radius
nearby_chains = ns.search(center_atom.coord, 10.0, level="C")
```

### Contact Map

```python
def calculate_contact_map(chain, distance_threshold=8.0):
    """Calculate residue-residue contact map."""
    residues = list(chain.get_residues())
    n = len(residues)
    contact_map = [[0] * n for _ in range(n)]

    for i, res1 in enumerate(residues):
        for j, res2 in enumerate(residues):
            if i < j:
                # Get CA atoms
                if res1.has_id("CA") and res2.has_id("CA"):
                    dist = res1["CA"] - res2["CA"]
                    if dist < distance_threshold:
                        contact_map[i][j] = 1
                        contact_map[j][i] = 1

    return contact_map
```

## Structure Quality Assessment

### Ramachandran Plot Data

```python
from Bio.PDB import Polypeptide

def get_phi_psi(structure):
    """Extract phi and psi angles for Ramachandran plot."""
  

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

