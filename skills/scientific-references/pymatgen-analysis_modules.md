---
id: sciref-pymatgen-analysis-modules
name: "Scientific Ref: Analysis: tolerances, computed entries, bands, DOS, and model limits"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pymatgen): Analysis: tolerances, computed entries, bands, DOS, and model limits"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pymatgen analysis modules"
  - "pymatgen analise modules"
  - "analysis: tolerances, computed entries, bands, dos, and model limits"
keywords:
  - "pymatgen"
  - "analysis"
  - "modules"
  - "analise"
  - "specialized"
  - "scientific"
  - "reference"
  - "tolerances"
---

# Analysis: tolerances, computed entries, bands, DOS, and model limits

This reference targets `pymatgen==2026.9.24` with
`pymatgen-core==2026.9.23`. An analysis object returning a value does not
establish convergence, uncertainty, experimental agreement, or suitability of
the underlying model.

## Symmetry

```python
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

analyzer = SpacegroupAnalyzer(
    structure,
    symprec=0.01,          # Å
    angle_tolerance=5.0,   # degrees
)

result = {
    "symbol": analyzer.get_space_group_symbol(),
    "number": analyzer.get_space_group_number(),
    "crystal_system": str(analyzer.get_crystal_system()),
    "point_group": analyzer.get_point_group_symbol(),
    "operation_count": len(analyzer.get_symmetry_operations()),
}
symmetrized = analyzer.get_symmetrized_structure()
equivalent_indices = symmetrized.equivalent_indices
wyckoff_symbols = symmetrized.wyckoff_symbols
```

The documented pymatgen default is `symprec=0.01 Å`; a looser value such as
`0.1 Å` is often used for relaxed structures and by the Materials Project
pipeline. Results can change with:

- coordinate precision and relaxation noise
- occupancy/disorder model
- oxidation/spin/site properties used or ignored
- primitive/conventional representation
- `symprec`, `angle_tolerance`, and spglib version

Always sweep justified tolerances and report the entire sensitivity grid. Do
not choose a tolerance solely because it gives a desired group.

Standardized or primitive structures are new representations:

```python
conventional = analyzer.get_conventional_standard_structure(
    keep_site_properties=False
)
primitive = analyzer.get_primitive_standard_structure(
    keep_site_properties=False
)
```

Site properties can be lost or propagated without symmetry-aware adjustment.
Preserve the parent and compare composition, volume per atom, magnetic order,
and property semantics.

## Structure matching

```python
from pymatgen.analysis.structure_matcher import StructureMatcher

matcher = StructureMatcher(
    ltol=0.2,
    stol=0.3,
    angle_tol=5,
    primitive_cell=True,
    scale=True,
)
matches = matcher.fit(first, second)
```

Record every tolerance and option. A match is equivalence under the chosen
algorithm, reductions, scaling, and species comparator—not identity of files,
provenance, defects, magnetic states, or experimental phases.

`fit()` is directional. For order-independent grouping use
`matcher.group_structures(structures, symmetric=True)` in this snapshot;
the new option is ignored for anonymous matching. Current mixed-functional
entry processing also sorts inputs and uses symmetric grouping, fixing earlier
hash-seed-dependent hulls. Recompute old mixed hulls when comparing versions.

## Local environments

```python
from pymatgen.analysis.local_env import CrystalNN, VoronoiNN

crystal_nn = CrystalNN()
neighbors = crystal_nn.get_nn_info(structure, 0)

voronoi_nn = VoronoiNN()
voronoi_neighbors = voronoi_nn.get_nn_info(structure, 0)
```

Coordination depends on the method, radii/oxidation information, weights,
cutoffs, disorder, and geometry. Preserve:

- algorithm and pymatgen version
- all constructor settings
- oxidation-state decoration
- site index/label mapping
- warnings and failures
- whether weighted or integer coordination was reported

Bound the number of sites and neighbors emitted. Cross-check model-sensitive
conclusions with more than one justified definition.

## Phase diagrams

An `Entry` contains a composition and a total energy:

```python
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.entries.computed_entries import ComputedEntry

entries = [
    ComputedEntry("Li", -1.0, entry_id="local-Li"),
    ComputedEntry("O2", -2.0, entry_id="local-O2"),
    ComputedEntry("Li2O", -4.0, entry_id="local-Li2O"),
]
diagram = PhaseDiagram(entries)

for entry in entries:
    print(
        entry.entry_id,
        diagram.get_form_energy_per_atom(entry),
        diagram.get_e_above_hull(entry),
    )
```

`ComputedEntry.energy` is total eV for the represented composition, not
eV/atom. `energy_per_atom`, formation energy, and hull distance are normalized
values.

### Comparability gate

Before constructing a hull, verify that entries share a compatible:

- functional and correction/mixing scheme
- pseudopotential family and valence configuration
- magnetic, spin, and SOC treatment
- reference-state convention
- numerical convergence level
- temperature/pressure model

Include elemental endpoints and all relevant competing phases. Missing phases
can make unstable entries appear stable. Duplicate compositions are allowed as
polymorphs only when their energies are comparable and provenance is distinct.

`diagram.stable_entries` means on the computed zero-temperature convex hull for
that exact entry set. It is not experimental stability or synthesizability.

### Decomposition

```python
from pymatgen.core import Composition

target = Composition("Li2O", strict=True)
decomposition = diagram.get_decomposition(target)
```

For an existing entry, use `get_e_above_hull(entry)`. A bare composition has no
candidate energy, so it has a hull decomposition but no intrinsic energy above
hull.

### Plotting

```python
from pymatgen.analysis.phase_diagram import PDPlotter

plotter = PDPlotter(diagram, show_unstable=0.2, backend="matplotlib")
plotter.write_image("phase.new.svg", image_format="svg")
```

Plot to a new path, bound unstable points and output size, and preserve the
machine-readable entry table. Plotting backends and image export can introduce
optional dependencies. The default Plotly backend needs its image-export stack;
the bundled CLI selects Matplotlib so PNG/PDF/SVG export works with the tested
package set.

## Chemical-potential and Pourbaix analyses

`ChemicalPotentialDiagram` and `PourbaixDiagram` add assumptions beyond a
composition hull. Record reference states, open species, aqueous ion data,
concentrations, pH, electrochemical potential, temperature, corrections, and
solvent convention. Do not reuse a solid-state entry set as a valid aqueous
thermodynamic model without the required transformations and references.

## Electronic band structures

The following VASP snippets are illustrative because they require the user's
calculation files; the current method signatures were verified.

```python
from pymatgen.io.vasp import Vasprun

run = Vasprun(
    "vasprun.xml",
    parse_dos=False,
    parse_eigen=True,
    parse_projected_e

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

