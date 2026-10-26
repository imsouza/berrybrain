---
id: sciref-rdkit-smarts-patterns
name: "Scientific Ref: SMARTS patterns and their limits"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (rdkit): SMARTS patterns and their limits"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "rdkit smarts patterns"
  - "smarts patterns and their limits"
keywords:
  - "rdkit"
  - "smarts"
  - "patterns"
  - "specialized"
  - "scientific"
  - "reference"
---

# SMARTS patterns and their limits

These are motif queries tested with RDKit 2026.03.6. A matched subgraph is not
molecular identity, a pKa prediction, toxicity evidence, or evidence that a
reaction will occur. Choose charge/tautomer/stereo policy before matching and
validate positives **and near negatives** for the dataset. SMARTS and SMILES are
different query languages even when a string is legal in both.

## Functional groups

The following neutral-state motifs cover common examples; they are not exhaustive
classifications of all resonance forms, organometallics, or charged species.
`[#6]` includes both aromatic and aliphatic carbon. `C` and `[C]` both mean
aliphatic carbon in SMARTS; lowercase `c` means aromatic carbon.

| Motif | SMARTS | Positive SMILES | Near negative SMILES |
| --- | --- | --- | --- |
| Alcohol on saturated C | `[OX2H1][CX4]` | `CCO` | `CC(=O)O` |
| Primary alcohol, excluding methanol | `[CX4H2][OX2H1]` | `CCO` | `CC(O)C` |
| Secondary alcohol | `[CX4H1][OX2H1]` | `CC(O)C` | `CCO` |
| Tertiary alcohol | `[CX4H0]([OX2H1])([#6])([#6])[#6]` | `CC(C)(C)O` | `CC(O)C` |
| Phenol | `c[OX2H1]` | `Oc1ccccc1` | `COc1ccccc1` |
| Aldehyde with carbon substituent | `[#6][CX3H1]=O` | `CC=O` | `CC(=O)C` |
| Ketone | `[#6][CX3](=O)[#6]` | `CC(=O)C` | `CC(=O)O` |
| Carbonyl | `[CX3]=O` | `CC=O` | `CCO` |
| Carboxylic acid | `[CX3](=O)[OX2H1]` | `CC(=O)O` | `CC(=O)[O-]` |
| Carboxylate | `[CX3](=O)[O-]` | `CC(=O)[O-]` | `CC(=O)O` |
| Ester motif | `[CX3](=O)[OX2H0][#6]` | `CC(=O)OC` | `CC(=O)O` |
| Amide | `[CX3](=O)[NX3]` | `CC(=O)N` | `CCN` |
| Neutral amine motif | `[NX3;$(N-[#6]);!$(N-C=O);!$(N-S(=O)=O);!$(N-P=O);!$(N=*)]` | `CCN` | `CC(=O)N` |
| Primary amine motif | `[NX3H2;!$(N-C=O);!$(N-S(=O)=O);!$(N-P=O)]` | `CN` | `CNC` |
| Ether excluding ester O | `[#6][OX2H0;!$(O-C=O)][#6]` | `COC` | `CC(=O)OC` |
| Alkyl halide | `[CX4][F,Cl,Br,I]` | `CCCl` | `Clc1ccccc1` |
| Aryl halide | `c[F,Cl,Br,I]` | `Clc1ccccc1` | `CCCl` |
| Nitrile | `C#N` | `CC#N` | `CCN` |
| Nitro | `[N+](=O)[O-]` | `C[N+](=O)[O-]` | `CN` |
| Thiol | `[#6][SX2H1]` | `CCS` | `CSC` |
| Sulfide | `[#6][SX2H0][#6]` | `CSC` | `CS(=O)C` |
| Sulfoxide | `[#6][SX3](=O)[#6]` | `CS(=O)C` | `CS(=O)(=O)C` |
| Sulfone | `[#6][SX4](=O)(=O)[#6]` | `CS(=O)(=O)C` | `CS(=O)C` |

An ester motif may also match a larger derivative such as an anhydride; an
amine motif needs further exclusions to classify unusual N–N/N–O compounds.
Ammonium, deprotonated alcohols, and aromatic `[nH]` need separate rules. The
bundled filter exposes a subset of these patterns; its library names describe
motifs, not universally disjoint chemical classes.

## Rings and scaffolds

| Motif | SMARTS |
| --- | --- |
| Benzene | `c1ccccc1` |
| Cyclohexane | `C1CCCCC1` |
| Pyridine | `n1ccccc1` |
| Pyrrole, allowing N-substitution | `n1cccc1` |
| Furan | `o1cccc1` |
| Thiophene | `s1cccc1` |
| Imidazole | `n1cncc1` |
| Pyrimidine | `n1cnccc1` |
| Thiazole | `n1ccsc1` |
| Oxazole | `n1ccoc1` |
| Naphthalene | `c1ccc2ccccc2c1` |
| Indole with N–H | `c1ccc2[nH]ccc2c1` |
| Benzimidazole with N–H | `c1ccc2[nH]cnc2c1` |
| Biphenyl | `c1ccccc1-c2ccccc2` |
| Piperazine | `N1CCNCC1` |
| Piperidine | `N1CCCCC1` |
| Morpholine | `N1CCOCC1` |

A ring SMARTS can match a fused or substituted structure; it is not an exact
scaffold identity test. Use Murcko scaffold extraction or a defined graph
identity policy when that is the scientific question.

`[r6]` means an atom whose **smallest ring** has size 6. `[r{12-}]` means smallest
ring size at least 12, not a general detector for every large cycle in a fused or
bridged graph. `[R]` means any ring atom; `[R2]` depends on the perceived ring set.
`[R]~[R]` merely joins two ring atoms and also matches within one ring. Use
`[*]@[*]` for a ring bond and `[R]!@[R]` for a non-ring bond between ring atoms
(e.g. biphenyl). A symmetrized ring count is not a count of distinct ring systems.

## Atom and bond primitives

| Query | Meaning |
| --- | --- |
| `[*]` | Any atom, including explicit H |
| `[!#1]` | Any non-hydrogen atom |
| `[#6]` | Carbon, aromatic or aliphatic |
| `[!#6;!#1]` | Neither carbon nor hydrogen |
| `[a]` / `[A]` | Aromatic / aliphatic atom |
| `[D2]` | Two explicit neighboring atoms |
| `[X4]` | Total connectivity four, including hydrogens |
| `[H1]` | Atom with one attached hydrogen (not hydrogen element identity) |
| `[#1]` | An explicit hydrogen atom |
| `[^2]` | RDKit extension for sp2 hybridization |
| `[CX3]` | Aliphatic carbon with connectivity three; not a universal sp2 query |
| `[+1]` / `[-1]` | Exactly the specified formal charge |
| `C-C`, `C=C`, `C#C` | Specified single, double, triple bond |
| `c:c` | Aromatic bond |
| `[*]~[*]` | Any bond |
| `[C;D2]([#6])[#6]` | Aliphatic C with exactly two explicit neighbors, both carbon |

`[!C]` also matches aromatic carbon; it does not mean “not element carbon”.
Hydrogen syntax is context-sensitive: use atomic numbers for element exclusion.
SMARTS `@` in a **bond** query is ring membership; atom stereo uses a different
meaning. Omitting a bond generally permits single or aromatic bonds.

## Stereo queries

Stereo matching is disabled by default. A lone `[C@]` is not a reliable test for
“any chiral atom”; use stereo perception to enumerate potential or specified
centers. `@`/`@@` encode local neighbor order, not absolute R/S labels.

```python
from rdkit import Chem
query = Chem.MolFromSmarts('C[C@H](O)F')
same = Chem.MolFromSmiles('C[C@H](O)F')
opposite = Chem.MolFromSmiles('C[C@@H](O)F')
assert same.HasSubstructMatch(query, useChirality=True)
assert not opposite.HasSubstructMatch(query, useChirality=True)
assert opposite.HasSubstructMatch(query)  # stereo ignored

# E/Z examples need stereo-aware matching as well.
trans = Chem.MolFromSmarts('C/C=C/C')
cis = Chem.MolFromSmiles(r'C/C=C\C')
assert not cis.HasSubstructMatch(trans, useChirality=True)
```

## Pharmacophores and chemical alerts

Use `ChemicalFeatures.BuildFeatureFactory` with `BaseFeatures.fdef` for named
RDKit donor/acceptor features. `[O,N]` is not an acceptor definition: protonated
amines and amide N are counterexamples. Graph features are not proof of binding
or metal coordination; geometric feature positions require coordinates.

Acyl chloride `C(=O)Cl`, epoxide `C1OC1`, catechol `Oc1ccccc1O`, rhodanine
`O=C1CSC(=S)N1`, and Michael-acceptor motif `C=CC(=O)` are illustrative structural
alerts. Their presence does not establish toxicity or assay interference.
The helper's legacy `pains

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

