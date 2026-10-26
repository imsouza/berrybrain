---
id: sciref-rdkit-api-reference
name: "Scientific Ref: RDKit API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (rdkit): RDKit API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "rdkit api reference"
keywords:
  - "rdkit"
  - "api"
  - "reference"
  - "specialized"
  - "scientific"
---

# RDKit API Reference

This document provides a selected reference for RDKit's Python API, organized by functionality.

Signatures below show selected keyword arguments, not complete overloads. Tested
on RDKit 2026.03.6; use keywords when omitted arguments precede them.

## Core Module: rdkit.Chem

The fundamental module for working with molecules.

### Molecule I/O

**Reading Molecules:**

- `Chem.MolFromSmiles(smiles, sanitize=True)` - Parse SMILES string
- `Chem.MolFromSmarts(smarts)` - Parse SMARTS pattern
- `Chem.MolFromMolFile(filename, sanitize=True, removeHs=True)` - Read MOL file
- `Chem.MolFromMolBlock(molblock, sanitize=True, removeHs=True)` - Parse MOL block string
- `Chem.MolFromMol2File(filename, sanitize=True, removeHs=True)` - Read MOL2 file
- `Chem.MolFromMol2Block(molblock, sanitize=True, removeHs=True)` - Parse MOL2 block
- `Chem.MolFromPDBFile(filename, sanitize=True, removeHs=True)` - Read PDB file
- `Chem.MolFromPDBBlock(pdbblock, sanitize=True, removeHs=True)` - Parse PDB block
- `Chem.MolFromInchi(inchi, sanitize=True, removeHs=True)` - Parse InChI string
- `Chem.MolFromSequence(text, sanitize=True)` - Create molecule from peptide sequence

MOL2 parsing expects supported atom typing (notably Corina conventions); PDB
connectivity inference does not validate bond orders, protonation, missing atoms
or biological assembly identity. These are format readers, not preparation pipelines.

**Writing Molecules:**

- `Chem.MolToSmiles(mol, isomericSmiles=True, canonical=True)` - Convert to SMILES
- `Chem.MolToSmarts(mol, isomericSmiles=True)` - Convert to SMARTS
- `Chem.MolToMolBlock(mol, includeStereo=True, confId=-1)` - Convert to MOL block
- `Chem.MolToMolFile(mol, filename, includeStereo=True, confId=-1)` - Write MOL file
- `Chem.MolToPDBBlock(mol, confId=-1)` - Convert to PDB block
- `Chem.MolToPDBFile(mol, filename, confId=-1)` - Write PDB file
- `Chem.MolToInchi(mol, options='')` - Convert to InChI
- `Chem.MolToInchiKey(mol, options='')` - Generate InChI key
- `Chem.MolToSequence(mol)` - Convert to peptide sequence

**Batch I/O:**

- `Chem.SDMolSupplier(filename, sanitize=True, removeHs=True)` - SDF file reader
- `Chem.ForwardSDMolSupplier(fileobj, sanitize=True, removeHs=True)` - Forward-only SDF reader
- `Chem.MultithreadedSDMolSupplier(filename, numWriterThreads=1)` - Parallel SDF reader; experimental, output order may change
- `Chem.SmilesMolSupplier(filename, delimiter=' ', titleLine=True)` - SMILES file reader
- `Chem.SDWriter(filename)` - SDF file writer
- `Chem.SmilesWriter(filename, delimiter=' ', includeHeader=True)` - SMILES file writer

### Molecular Manipulation

**Sanitization:**

- `Chem.SanitizeMol(mol, sanitizeOps=SANITIZE_ALL, catchErrors=False)` - Sanitize molecule
- `Chem.DetectChemistryProblems(mol, sanitizeOps=SANITIZE_ALL)` - Detect sanitization issues
- `Chem.AssignStereochemistry(mol, cleanIt=False, force=False)` - Assign stereochemistry
- `Chem.FindPotentialStereo(mol)` - Potential stereoelements; upstream still marks this API experimental
- `Chem.AssignStereochemistryFrom3D(mol, confId=-1)` - Assign stereo from 3D coords

**Hydrogen Management:**

- `Chem.AddHs(mol, explicitOnly=False, addCoords=False)` - Add explicit hydrogens
- `Chem.RemoveHs(mol, implicitOnly=False, updateExplicitCount=False)` - Remove hydrogens
- `Chem.RemoveAllHs(mol)` - Remove all hydrogens

`RemoveHs` normally preserves isotopic hydrogen; `RemoveAllHs` can discard it.
Choose explicit isotope/stereo preservation policy before either operation.

**Aromaticity:**

- `Chem.SetAromaticity(mol, model=AROMATICITY_RDKIT)` - Set aromaticity model
- `Chem.Kekulize(mol, clearAromaticFlags=False)` - Kekulize aromatic bonds
- `Chem.SetConjugation(mol)` - Set conjugation flags

**Fragments:**

- `Chem.GetMolFrags(mol, asMols=False, sanitizeFrags=True)` - Get disconnected fragments
- `Chem.FragmentOnBonds(mol, bondIndices, addDummies=True)` - Fragment on specific bonds
- `Chem.ReplaceSubstructs(mol, query, replacement, replaceAll=False)` - Replace substructures
- `Chem.DeleteSubstructs(mol, query, onlyFrags=False)` - Delete substructures

**Stereochemistry:**

- `Chem.FindMolChiralCenters(mol, includeUnassigned=False, useLegacyImplementation=None)` - Find chiral centers
- `Chem.FindPotentialStereo(mol, cleanIt=False)` - Find potential stereocenters

### Substructure Searching

**Basic Matching:**

- `mol.HasSubstructMatch(query, useChirality=False)` - Check for substructure match
- `mol.GetSubstructMatch(query, useChirality=False)` - Get first match
- `mol.GetSubstructMatches(query, uniquify=True, useChirality=False)` - Get all matches
- `mol.GetSubstructMatches(query, maxMatches=1000)` - Limit number of matches

### Molecular Properties

**Atom Methods:**

- `atom.GetSymbol()` - Atomic symbol
- `atom.GetAtomicNum()` - Atomic number
- `atom.GetDegree()` - Number of bonds
- `atom.GetTotalDegree()` - Including hydrogens
- `atom.GetFormalCharge()` - Formal charge
- `atom.GetNumRadicalElectrons()` - Radical electrons
- `atom.GetIsAromatic()` - Aromaticity flag
- `atom.GetHybridization()` - Hybridization (SP, SP2, SP3, etc.)
- `atom.GetIdx()` - Atom index
- `atom.IsInRing()` - In any ring
- `atom.IsInRingSize(size)` - In ring of specific size
- `atom.GetChiralTag()` - Chirality tag

**Bond Methods:**

- `bond.GetBondType()` - Bond type (SINGLE, DOUBLE, TRIPLE, AROMATIC)
- `bond.GetBeginAtomIdx()` - Starting atom index
- `bond.GetEndAtomIdx()` - Ending atom index
- `bond.GetIsConjugated()` - Conjugation flag
- `bond.GetIsAromatic()` - Aromaticity flag
- `bond.IsInRing()` - In any ring
- `bond.GetStereo()` - Stereochemistry (STEREONONE, STEREOZ, STEREOE, etc.)

**Molecule Methods:**

- `mol.GetNumAtoms(onlyExplicit=True)` - Number of atoms
- `mol.GetNumHeavyAtoms()` - Number of heavy atoms
- `mol.GetNumBonds()` - Number of bonds
- `mol.GetAtoms()` - Iterator over atoms
- `mol.GetBonds()` - Iterator over bonds
- `mol.GetAtomWithIdx(idx)` - Get specific atom
- `mol.GetBondWithIdx(idx)` - Get specific bond
- `mol.GetRingInfo()` - Ring information object

**Ring Information:**

- `Chem.GetSymmSSSR(mol)` - Symmetrized smallest-ring set (can exceed SSSR size)
- `Chem.GetSSSR(mol)` - Smallest set of smallest rings; not an alias (cubane: 5 versus 6 symmetrized rings)
- `ring_info.NumRings()` - Number of rings
- `ring_info.AtomRings()` - Tuples of atom indices in rings
- `ring_info.BondRings()` - Tuples of bond indices in rings

## rdkit.Chem.AllChem

Extended chemistry functionality.

##

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

