---
id: sciref-rdkit-review
name: "Scientific Ref: RDKit review record"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (rdkit): RDKit review record"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "rdkit review"
  - "rdkit revisao"
  - "rdkit review record"
keywords:
  - "rdkit"
  - "review"
  - "revisao"
  - "specialized"
  - "scientific"
  - "reference"
---

# RDKit review record

Reviewed 2026-10-01 against stable RDKit **2026.03.6**, PyPI package
`rdkit==2026.3.6`, executed on macOS ARM64 / Python 3.13. Development branches and
pre-release APIs were not adopted. `FindPotentialStereo` and multithreaded
suppliers remain explicitly experimental even in the stable package.

## Official sources checked

- [Stable release](https://github.com/rdkit/rdkit/releases/tag/Release_2026_03_6)
  and [PyPI metadata](https://pypi.org/pypi/rdkit/json): stable version and wheel availability.
- [Installation](https://www.rdkit.org/docs/Install.html) and
  [Python introduction](https://www.rdkit.org/docs/GettingStartedInPython.html):
  binary packaging, parsing, suppliers, conformers, drawing.
- [RDKit Book](https://www.rdkit.org/docs/RDKit_Book.html): SMARTS semantics,
  sanitization, stereochemistry, reactions, hydrogen handling, thread caveats.
- [2026.03.1 release notes](https://github.com/rdkit/rdkit/releases/tag/Release_2026_03_1):
  canonical stereo/Kekulization changes, H removal and MolToSmarts behavior.
  The standalone backwards-incompatible-changes page stops at older releases;
  release notes are necessary for current changes.
- [Molecular files](https://www.rdkit.org/docs/source/rdkit.Chem.rdmolfiles.html),
  [graph operations](https://www.rdkit.org/docs/source/rdkit.Chem.rdmolops.html),
  [molecule/atom/bond API](https://www.rdkit.org/docs/source/rdkit.Chem.rdchem.html).
- [Fingerprint generators](https://www.rdkit.org/docs/source/rdkit.Chem.rdFingerprintGenerator.html),
  [atom pairs](https://www.rdkit.org/docs/source/rdkit.Chem.AtomPairs.Pairs.html),
  [torsions](https://www.rdkit.org/docs/source/rdkit.Chem.AtomPairs.Torsions.html),
  [similarities](https://www.rdkit.org/docs/source/rdkit.DataStructs.html),
  [Butina](https://www.rdkit.org/docs/source/rdkit.ML.Cluster.Butina.html).
- [Descriptors](https://www.rdkit.org/docs/source/rdkit.Chem.Descriptors.html),
  [molecular descriptors](https://www.rdkit.org/docs/source/rdkit.Chem.rdMolDescriptors.html),
  [tagged Lipinski definitions](https://github.com/rdkit/rdkit/blob/Release_2026_03_6/rdkit/Chem/Lipinski.py).
- [Standardization API](https://www.rdkit.org/docs/source/rdkit.Chem.MolStandardize.rdMolStandardize.html)
  and [released implementation](https://github.com/rdkit/rdkit/blob/Release_2026_03_6/Code/GraphMol/MolStandardize/MolStandardize.cpp):
  Cleanup retains disconnected salts; FragmentParent, Uncharger and tautomer
  operations are separate, scientifically consequential policies.
- [Embedding](https://www.rdkit.org/docs/source/rdkit.Chem.rdDistGeom.html),
  [released force-field wrapper](https://github.com/rdkit/rdkit/blob/Release_2026_03_6/Code/GraphMol/ForceFieldHelpers/Wrap/rdForceFields.cpp),
  [drawing](https://www.rdkit.org/docs/source/rdkit.Chem.Draw.html).
- [Reactions](https://www.rdkit.org/docs/source/rdkit.Chem.rdChemReactions.html),
  [hashes](https://www.rdkit.org/docs/source/rdkit.Chem.rdMolHash.html),
  [scaffolds](https://www.rdkit.org/docs/source/rdkit.Chem.Scaffolds.MurckoScaffold.html),
  [PAINS catalogue](https://www.rdkit.org/docs/source/rdkit.Chem.FilterCatalog.html).

Installed stable docstrings/signatures supplemented web pages that omitted
compiled-function details. These are local APIs: no hosted chemistry endpoint,
credential, pagination, remote inference, or scientific database request is
required by the bundled scripts.

## Executed checks and boundaries

The isolated per-skill suite exercises the three CLIs plus shared file reader,
known positive/negative functional groups, invalid exclusions, source record
identity, empty inputs, query cardinality, fingerprint dimensions/thresholds,
enantiomers, specified versus unspecified stereo, isotope/charge/tautomer
identity, Cleanup/fragment/uncharging distinctions, valence failure, converged
conformers, force-field coverage, units, reactions and depiction copies.

Supplementary tiny-molecule smoke checks covered 72 named descriptors, 12
`rdMolDescriptors` entries, MOL/SDF/SMILES/gzip/PDB/InChI/peptide I/O, multithreaded
source IDs, graph edits, hashes/scaffolds/features, Avalon/ErG, legacy fingerprint
aliases, bit visualization, similarity metrics/Butina, UFF/MMFF, RMSD/alignment,
constrained embedding, template depiction and reaction fingerprints. An attribute
and signature audit covered the entire named module API inventory.

Two observed behaviors deserve attention:

- Fresh `SmilesMolSupplier` passed directly to `list()` returned no records in
  the tested build; iteration/comprehensions worked. The bundled reader parses
  physical SMILES lines itself and preserves their source IDs.
- Chirality-aware 2048-bit atom-pair fingerprints collided for simple
  enantiomers; sparse count representations distinguished them. Similarity 1
  must never substitute for a declared chemical identity policy.

Reference snippets with input paths, undefined molecules/indices or notebook
objects are illustrative templates. MOL2 chemical-typing conventions and optional
Jupyter integration are documentation/signature reviewed, not executed here.
No performance/concurrency stress benchmark, cross-platform binary verification,
experimental validation, pH/tautomer-population inference, or predictive model
validation is claimed. Tiny organic examples do not establish parameter coverage
for organometallics, unusual valences, macrocycles or proteins.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

