---
id: sciref-rdkit-descriptors-reference
name: "Scientific Ref: RDKit Molecular Descriptors Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (rdkit): RDKit Molecular Descriptors Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "rdkit descriptors reference"
  - "rdkit molecular descriptors reference"
keywords:
  - "rdkit"
  - "descriptors"
  - "reference"
  - "specialized"
  - "scientific"
  - "molecular"
---

# RDKit Molecular Descriptors Reference

Selected reference for molecular descriptors available in RDKit's `Descriptors` module.

## Usage

```python
from rdkit import Chem
from rdkit.Chem import Descriptors

mol = Chem.MolFromSmiles('CCO')

# Calculate individual descriptor
mw = Descriptors.MolWt(mol)

# Calculate all descriptors at once
all_desc = Descriptors.CalcMolDescriptors(mol)
```

## Molecular Weight and Mass

### MolWt
Average molecular weight (numerically g/mol), including implicit hydrogens.
```python
Descriptors.MolWt(mol)
```

### ExactMolWt
Monoisotopic mass (Da), honoring specified isotopes; not an ion m/z calculation.
```python
Descriptors.ExactMolWt(mol)
```

### HeavyAtomMolWt
Average molecular weight ignoring hydrogens.
```python
Descriptors.HeavyAtomMolWt(mol)
```

## Lipophilicity

### MolLogP
Wildman-Crippen estimate of octanol/water logP; not measured logP or pH-dependent logD.
```python
Descriptors.MolLogP(mol)
```

### MolMR
Wildman-Crippen molar refractivity.
```python
Descriptors.MolMR(mol)
```

## Polar Surface Area

### TPSA
Fragment-based TPSA in square angstrom. The default excludes sulfur/phosphorus
contributions; request `rdMolDescriptors.CalcTPSA(mol, includeSandP=True)` explicitly
if that is the intended definition.
```python
Descriptors.TPSA(mol)
```

### LabuteASA
Labute's Approximate Surface Area (ASA).
```python
Descriptors.LabuteASA(mol)
```

## Hydrogen Bonding

### NumHDonors
Count under RDKit donor SMARTS rules; includes eligible N, O and S sites.
```python
Descriptors.NumHDonors(mol)
```

### NumHAcceptors
Count under RDKit acceptor SMARTS rules; not simply the count of N/O atoms.
```python
Descriptors.NumHAcceptors(mol)
```

### NOCount
Number of N and O atoms.
```python
Descriptors.NOCount(mol)
```

### NHOHCount
Number of N-H and O-H bonds.
```python
Descriptors.NHOHCount(mol)
```

## Atom Counts

### HeavyAtomCount
Number of heavy atoms (non-hydrogen).
```python
Descriptors.HeavyAtomCount(mol)
```

### NumHeteroatoms
Number of heteroatoms (non-C and non-H).
```python
Descriptors.NumHeteroatoms(mol)
```

### NumValenceElectrons
Total number of valence electrons.
```python
Descriptors.NumValenceElectrons(mol)
```

### NumRadicalElectrons
Number of radical electrons.
```python
Descriptors.NumRadicalElectrons(mol)
```

## Ring Descriptors

### RingCount
Number of rings.
```python
Descriptors.RingCount(mol)
```

### NumAromaticRings
Number of aromatic rings.
```python
Descriptors.NumAromaticRings(mol)
```

### NumSaturatedRings
Number of saturated rings.
```python
Descriptors.NumSaturatedRings(mol)
```

### NumAliphaticRings
Number of aliphatic (non-aromatic) rings.
```python
Descriptors.NumAliphaticRings(mol)
```

### NumAromaticCarbocycles
Number of aromatic carbocycles (rings with only carbons).
```python
Descriptors.NumAromaticCarbocycles(mol)
```

### NumAromaticHeterocycles
Number of aromatic heterocycles (rings with heteroatoms).
```python
Descriptors.NumAromaticHeterocycles(mol)
```

### NumSaturatedCarbocycles
Number of saturated carbocycles.
```python
Descriptors.NumSaturatedCarbocycles(mol)
```

### NumSaturatedHeterocycles
Number of saturated heterocycles.
```python
Descriptors.NumSaturatedHeterocycles(mol)
```

### NumAliphaticCarbocycles
Number of aliphatic carbocycles.
```python
Descriptors.NumAliphaticCarbocycles(mol)
```

### NumAliphaticHeterocycles
Number of aliphatic heterocycles.
```python
Descriptors.NumAliphaticHeterocycles(mol)
```

## Rotatable Bonds

### NumRotatableBonds
Number of rotatable bonds (flexibility).
```python
Descriptors.NumRotatableBonds(mol)
```

## Aromatic Atoms

### NumAromaticAtoms
Number of aromatic atoms.
```python
sum(atom.GetIsAromatic() for atom in mol.GetAtoms())
```

## Fraction Descriptors

### FractionCSP3
Fraction of carbons that are sp3 hybridized.
```python
Descriptors.FractionCSP3(mol)  # also Lipinski.FractionCSP3(mol)
```

## Complexity Descriptors

### BertzCT
Bertz complexity index.
```python
Descriptors.BertzCT(mol)
```

### Ipc
Information content (complexity measure).
```python
Descriptors.Ipc(mol)
```

## Kappa Shape Indices

Molecular shape descriptors based on graph invariants.

### Kappa1
First kappa shape index.
```python
Descriptors.Kappa1(mol)
```

### Kappa2
Second kappa shape index.
```python
Descriptors.Kappa2(mol)
```

### Kappa3
Third kappa shape index.
```python
Descriptors.Kappa3(mol)
```

## Chi Connectivity Indices

Molecular connectivity indices.

### Chi0 and Chi1
Unmodified connectivity indices (higher orders use the n/v families below).
```python
Descriptors.Chi0(mol)
Descriptors.Chi1(mol)
```

### Chi0n, Chi1n, Chi2n, Chi3n, Chi4n
Valence-modified chi connectivity indices.
```python
Descriptors.Chi0n(mol)
Descriptors.Chi1n(mol)
Descriptors.Chi2n(mol)
Descriptors.Chi3n(mol)
Descriptors.Chi4n(mol)
```

### Chi0v, Chi1v, Chi2v, Chi3v, Chi4v
Valence chi connectivity indices.
```python
Descriptors.Chi0v(mol)
Descriptors.Chi1v(mol)
Descriptors.Chi2v(mol)
Descriptors.Chi3v(mol)
Descriptors.Chi4v(mol)
```

## Hall-Kier Alpha

### HallKierAlpha
Hall-Kier alpha value (molecular flexibility).
```python
Descriptors.HallKierAlpha(mol)
```

## Balaban's J Index

### BalabanJ
Balaban's J index (branching descriptor).
```python
Descriptors.BalabanJ(mol)
```

## EState Indices

Electrotopological state indices.

### MaxEStateIndex
Maximum E-state value.
```python
Descriptors.MaxEStateIndex(mol)
```

### MinEStateIndex
Minimum E-state value.
```python
Descriptors.MinEStateIndex(mol)
```

### MaxAbsEStateIndex
Maximum absolute E-state value.
```python
Descriptors.MaxAbsEStateIndex(mol)
```

### MinAbsEStateIndex
Minimum absolute E-state value.
```python
Descriptors.MinAbsEStateIndex(mol)
```

## Partial Charges

### MaxPartialCharge
Maximum partial charge.
```python
Descriptors.MaxPartialCharge(mol)
```

### MinPartialCharge
Minimum partial charge.
```python
Descriptors.MinPartialCharge(mol)
```

### MaxAbsPartialCharge
Maximum absolute partial charge.
```python
Descriptors.MaxAbsPartialCharge(mol)
```

### MinAbsPartialCharge
Minimum absolute partial charge.
```python
Descriptors.MinAbsPartialCharge(mol)
```

## Fingerprint Density

Measures the density of molecular fingerprints.

### FpDensityMorgan1
Morgan fingerprint density at radius 1.
```python
Descriptors.FpDensityMorgan1(mol)
```

### FpDensityMorgan2
Morgan fingerprint density at radius 2.
```python
Descriptors.FpDensityMorgan2(mol)
```

### FpDensityMorgan3
Morgan fingerprint density at radius 3.
```python
D

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

