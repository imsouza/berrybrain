---
id: sciref-pymatgen-io-formats
name: "Scientific Ref: I/O: parsers, writers, VASP, Q-Chem, and trust boundaries"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pymatgen): I/O: parsers, writers, VASP, Q-Chem, and trust boundaries"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pymatgen formats"
  - "i/o: parsers, writers, vasp, q-chem, and trust boundaries"
keywords:
  - "pymatgen"
  - "formats"
  - "specialized"
  - "scientific"
  - "reference"
  - "parsers"
  - "writers"
---

# I/O: parsers, writers, VASP, Q-Chem, and trust boundaries

This reference targets `pymatgen-core==2026.9.23`, which now owns core and
electronic-structure-code I/O under the unchanged `pymatgen.io` namespace.

## I/O is a semantic conversion

Parsing and writing are not neutral byte operations. Before any conversion,
record:

- object kind: periodic `Structure` or non-periodic `Molecule`
- input and output formats, including format variants
- lattice/PBC and coordinate mode
- units
- species order, labels, occupancies/disorder, and oxidation states
- charge/spin for molecules
- site properties such as selective dynamics, velocities, forces, and magmoms
- parser warnings and any automatic corrections

Never overwrite the input or an existing output. Write a new artifact,
round-trip it, and compare the properties the workflow depends on.

## Convenience interface

```python
from pymatgen.core import Molecule, Structure

structure = Structure.from_file("input.cif", primitive=False, sort=False)
cif_text = structure.to(fmt="cif")
poscar_text = structure.to(fmt="poscar")

molecule = Molecule.from_file("molecule.xyz")
xyz_text = molecule.to(fmt="xyz")
```

Use explicit `fmt` when a filename or extension is ambiguous. Never assume
automatic detection means the detected interpretation was scientifically
correct.

## CIF

Use the current parser method and retain all warnings:

```python
import warnings
from pymatgen.io.cif import CifParser

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    parser = CifParser(
        "input.cif",
        occupancy_tolerance=1.0,
        site_tolerance=1e-4,
        frac_tolerance=1e-4,
        check_cif=True,
        comp_tol=0.01,
    )
    structures = parser.parse_structures(
        primitive=False,
        symmetrized=False,
        check_occu=True,
        on_error="raise",
    )

parser_warnings = list(parser.warnings)
python_warnings = [str(item.message) for item in caught]
```

Important behavior:

- A CIF can contain multiple data blocks/structures. Select an index explicitly.
- The parser attempts to repair some out-of-spec content and reports changes.
- Sites close within `site_tolerance` can be merged.
- Occupancy slightly above 1 can be rescaled when it falls within
  `occupancy_tolerance`; increasing that tolerance is a scientific decision,
  not a generic repair.
- `frac_tolerance` can round coordinates near common fractions.
- `check_cif` compares parsed structure composition against CIF composition and
  may warn about omissions such as difficult-to-locate hydrogens.
- `parse_structures(primitive=False)` is the current explicit behavior. Do not
  rely on historical defaults.

Writing:

```python
from pymatgen.io.cif import CifWriter

writer = CifWriter(
    structure,
    symprec=None,
    significant_figures=8,
    write_site_properties=False,
)
cif_text = str(writer)
```

Setting `symprec` asks the writer to find symmetry and can refine to a
conventional representation depending on `refine_struct`; that changes the
representation. Report `symprec`, `angle_tolerance`, and `refine_struct`.

### Untrusted CIFs

A critical arbitrary-code-execution vulnerability in magnetic CIF
transformation parsing affected pymatgen through 2024.2.8 and was fixed in
2024.2.20. Use a current pinned release, but still parse attacker-controlled
files only in a low-privilege isolated process with byte, CPU, memory, disk,
site-count, and wall-time limits.

## POSCAR/CONTCAR

```python
from pymatgen.io.vasp import Poscar

poscar = Poscar.from_file(
    "POSCAR",
    check_for_potcar=False,
    read_velocities=True,
)
structure = poscar.structure

direct_text = poscar.get_str(direct=True, significant_figures=16)
cartesian_text = poscar.get_str(direct=False, significant_figures=16)
```

Record:

- direct/fractional versus Cartesian coordinates
- scale factor interpretation and units
- element-name source, especially VASP 4 files
- species order
- selective-dynamics flags
- velocities, predictor-corrector data, and lattice velocities if present

POSCAR cannot faithfully represent partial occupancies. Oxidation states and
arbitrary site properties generally do not round-trip. Never "fix" a POSCAR by
searching nearby directories for POTCAR files without explicit approval.

## XYZ and other low-context formats

XYZ is a Cartesian, non-periodic coordinate format. Converting a periodic
structure to XYZ drops lattice and periodicity. Basic XYZ also does not define
oxidation states, partial occupancies, bonds, charge, spin multiplicity, or
arbitrary site properties.

`Structure.to(fmt="xyz")` is unsupported in the tested registry. The bundled
converter uses `pymatgen.io.xyz.XYZ(structure)` explicitly, after acknowledging
the loss of lattice/PBC. Read the result as a `Molecule`.

CSSR and XSF have their own representational limits. Treat support in
`Structure.to()` as syntactic capability, not proof of losslessness.

## JSON and MSON

Pymatgen core objects implement `as_dict()`/`from_dict()`:

```python
import json
from pymatgen.core import Structure

text = json.dumps(structure.as_dict(), allow_nan=False, sort_keys=True)
payload = json.loads(text)
restored = Structure.from_dict(payload)
```

For untrusted input, use a bounded strict JSON parser, reject duplicate keys and
non-finite values, validate the expected schema, and call a specific
constructor. Do not use pickle. Do not pass attacker-controlled `@module` or
`@class` metadata to a general dynamic object decoder.

`Structure.from_dict()` itself decodes site-property MSON values. The bundled
loader therefore rejects nested MSON metadata, duplicate keys and non-finite
numbers before constructing a structure. It accepts plain `.json`/`.mson`
files only; decompress and inspect compressed JSON separately.

YAML is not used by the bundled CLIs. If a workflow truly needs YAML, use a
safe loader plus schema validation; YAML safety does not solve object-schema or
resource-exhaustion risks.

## VASP input objects

```python
from pymatgen.io.vasp import Incar, Kpoints, Poscar

incar = Incar({"ENCUT": 520, "ISMEAR": 0, "SIGMA": 0.05})
kpoints = Kpoints.automatic_density(structure, 1000)
poscar = Poscar(structure)
```

Input sets encode versioned methodological choices:

```python
from pymatgen.io.vasp.sets import MPNonSCFSet, MPRelaxSet, MPStaticSet

relax = MPRelaxSet(structure)
static = MPStaticSet(structure)
bands = MPNonSCFSet(structure, mode="line")
```

Before writing:

1. ins

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

