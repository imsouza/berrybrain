---
id: sciref-pymatgen-transformations-workflows
name: "Scientific Ref: Transformations and provenance-preserving workflows"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pymatgen): Transformations and provenance-preserving workflows"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pymatgen transformations workflows"
  - "transformations and provenance-preserving workflows"
keywords:
  - "pymatgen"
  - "transformations"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
  - "provenance"
---

# Transformations and provenance-preserving workflows

Transformations create scientific hypotheses and derived structures. They are
not harmless cleanup. Always retain the original, make assumptions explicit,
bound candidate growth, and record parent/child checksums.

## Transformation contract

A pymatgen transformation exposes `apply_transformation(structure, ...)`.
One-to-one transformations return a structure; one-to-many transformations can
return ranked dictionaries when explicitly requested.

```python
from pymatgen.transformations.standard_transformations import (
    SubstitutionTransformation,
    SupercellTransformation,
)

parent = structure.copy()
supercell = SupercellTransformation([2, 2, 2]).apply_transformation(parent)
substituted = SubstitutionTransformation({"Na": "K"}).apply_transformation(
    parent
)
```

Even if a transformation currently returns a new object, keep `parent`
unchanged and assert it against a pre-operation checksum.

For every transformation, record:

- fully qualified class and package versions
- constructor arguments and defaults relied upon
- parent artifact/checksum
- occupancy, oxidation-state, charge, spin, and site-property assumptions
- candidate count/ranking method
- warnings and external executable use
- child artifact/checksum

## Supercells

```python
from pymatgen.transformations.standard_transformations import (
    SupercellTransformation,
)

transformation = SupercellTransformation(
    [[2, 0, 0], [0, 2, 0], [0, 0, 2]]
)
child = transformation.apply_transformation(parent)
```

Check:

- scaling-matrix determinant is a positive integer
- expected site-count multiplier
- volume-per-site consistency
- atom/site-property mapping
- periodic boundary conditions
- memory and output growth

Reject a matrix or candidate whose determinant/site count exceeds the reviewed
bound. A non-diagonal matrix changes the cell basis and site ordering.

## Substitution and disorder

Complete substitution:

```python
from pymatgen.transformations.standard_transformations import (
    SubstitutionTransformation,
)

child = SubstitutionTransformation({"Fe": "Mn"}).apply_transformation(parent)
```

Partial substitution creates disorder:

```python
disordered = SubstitutionTransformation(
    {"Fe": {"Fe": 0.5, "Mn": 0.5}}
).apply_transformation(parent)
```

Verify composition, charge model, oxidation states, occupancy sums, and whether
all intended sites—not just a selected sublattice—were transformed. Partial
occupancy is an average/disordered representation, not one ordered atomic
configuration.

## Removing species and sites

```python
from pymatgen.transformations.standard_transformations import (
    RemoveSpeciesTransformation,
)

child = RemoveSpeciesTransformation(["H"]).apply_transformation(parent)
```

Removing species changes composition, charge, and possibly connectivity.
Never use it as silent parser cleanup. Record removed site indices/species and
validate charge/stoichiometry afterward.

## Primitive and conventional cells

```python
from pymatgen.transformations.standard_transformations import (
    ConventionalCellTransformation,
    PrimitiveCellTransformation,
)

primitive = PrimitiveCellTransformation(
    tolerance=0.5,
).apply_transformation(parent)
conventional = ConventionalCellTransformation(
    symprec=0.01,
    angle_tolerance=5,
).apply_transformation(parent)
```

These results depend on symmetry tolerances and can change site order or site
properties. Compare formula and volume per atom, preserve exact tolerances, and
do not treat standardized cells from different conventions as byte-identical.

## Strain and deformation

```python
from pymatgen.transformations.standard_transformations import (
    DeformStructureTransformation,
)

deformed = DeformStructureTransformation(
    [[1.01, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
).apply_transformation(parent)
```

State whether a matrix is a deformation gradient, strain-like approximation,
or lattice transform. Bound determinant, condition number, minimum distances,
and strain magnitude. Generate positive and negative strains under one
manifest for tensor fitting.

## Oxidation-state decoration

Oxidation states are inputs to several transformations and electrostatic
rankings. Decoration can be explicit or guessed. Prefer explicit mappings
grounded in chemistry:

```python
decorated = parent.copy()
decorated.add_oxidation_state_by_element({"Li": 1, "O": -2})
```

If a guesser is explicitly approved, bound complexity and preserve all
candidate assignments and assumptions. Do not present the first guess as a
measured charge state.

## Ordering disordered structures

```python
from pymatgen.transformations.standard_transformations import (
    OrderDisorderedStructureTransformation,
)

transformation = OrderDisorderedStructureTransformation()
ranked = transformation.apply_transformation(
    disordered,
    return_ranked_list=20,
)
```

Ordering can grow combinatorially. Before running:

- verify rational occupancies and the required supercell
- require oxidation states if electrostatic ranking needs them
- cap maximum cell size, sites, candidates, runtime, RAM, and disk
- state the ranking model and ties
- preserve unreturned-candidate count when known

The top-ranked ordering is model-dependent, not a unique ground state.

## EnumerateStructureTransformation and enumlib

`EnumerateStructureTransformation` generates symmetrically distinct orderings
and requires the external enumlib executables (`enum.x` and `makestr.x`).
Several advanced transformations, including magnetic ordering, can rely on
enumeration.

Current installation docs recommend Enumlib.jl, which provides both executables
in recent releases, alongside the original Fortran implementation. The docs
record `makestr.x` tolerance failures on some inputs and a `makeStr.py` fallback;
verify the selected implementation on the actual structure. Current pymatgen
idealizes coordinates within the declared symmetry tolerance and raises when
fewer structures are produced than enumerated. Preserve those warnings and
the returned count. External enumlib execution was not tested in this refresh.

Treat enumlib as a separate native-code execution:

1. verify official source, version, build instructions, license, and hash
2. resolve the executable path explicitly
3. review exact argv and working directory
4. isolate untrusted inputs
5. enforce cell-size, candidate, CPU, RAM, disk, and wall-time limits
6. preserve stdout/stderr and exit 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

