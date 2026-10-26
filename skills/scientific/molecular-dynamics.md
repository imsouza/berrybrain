---
id: sci-molecular-dynamics
name: "Scientific: molecular-dynamics"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Runs and analyzes molecular dynamics simulations with OpenMM and MDAnalysis. Sets up protein/small molecule systems, defines force fields, runs energy minimization and production MD, and analyzes trajectories (RMSD, RMSF, contact maps, free energy surfaces). For structural biolog"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "molecular dynamics"
  - "molecular-dynamics"
keywords:
  - "molecular"
  - "dynamics"
  - "runs"
  - "analyzes"
  - "simulations"
  - "openmm"
---

# Molecular Dynamics

## Overview

Molecular dynamics (MD) simulation computationally models the time evolution of molecular systems by integrating Newton's equations of motion. This skill covers two complementary tools:

- **OpenMM** (https://openmm.org/): High-performance MD simulation engine with GPU support, Python API, and flexible force field support
- **MDAnalysis** (https://mdanalysis.org/): Python library for reading, writing, and analyzing MD trajectories from all major simulation packages

**Reviewed versions:** OpenMM 8.6.1 and MDAnalysis 2.10.0. Reference-platform
smoke checks use small synthetic systems; GPU performance and scientific convergence
are not established by them. OpenMM latest API pages identify a development build,
so the installed 8.6.1 API is the executable reference.

**Installation into a dedicated environment:**
```bash
uv venv --python 3.12 .venv-md
uv pip install --python .venv-md/bin/python "openmm==8.6.1" "MDAnalysis==2.10.0" matplotlib pandas
# Windows: use .venv-md/Scripts/python.exe instead
```

## When to Use This Skill

Use molecular dynamics when:

- **Protein stability analysis**: How does a mutation affect protein dynamics?
- **Drug binding simulations**: Characterize binding mode and residence time of a ligand
- **Conformational sampling**: Explore protein flexibility and conformational changes
- **Protein-protein interaction**: Model interface dynamics and binding energetics
- **RMSD/RMSF analysis**: Quantify structural fluctuations from a reference structure
- **Free energy estimation**: Compute binding free energy or conformational free energy
- **Membrane simulations**: Model proteins in lipid bilayers
- **Intrinsically disordered proteins**: Study IDR conformational ensembles

## Core Workflow: OpenMM Simulation

Examples require system-specific preparation and validation. Review biological
assembly, alternate locations, missing loops, termini, protonation, disulfides,
ligands and cofactors before parameterization. An MD trajectory alone does not
establish binding free energy or residence time.

The functions below form one Python module: execute their import blocks together.
Use a new output prefix for every stage to avoid overwriting earlier results.

### 1. System Preparation

```python
from openmm.app import *
from openmm import *
from openmm.unit import *

def prepare_system_from_pdb(pdb_file, forcefield_name="amber14-all.xml",
                              water_model="amber14/tip3pfb.xml", ph=7.0):
    """
    Prepare an OpenMM system from a PDB file.

    Args:
        pdb_file: Path to cleaned PDB file (use PDBFixer for raw PDB files)
        forcefield_name: Force field XML file
        water_model: Water model XML file

    Returns:
        modeller, system
    """
    # Load PDB
    pdb = PDBFile(pdb_file)

    # Load force field
    forcefield = ForceField(forcefield_name, water_model)

    # Add hydrogens and solvate
    modeller = Modeller(pdb.topology, pdb.positions)
    modeller.addHydrogens(forcefield, pH=ph)

    # TIP3P geometry also serves TIP3P-FB; XML supplies the parameters.
    # 10 Å padding; added salt excludes neutralizing counterions.
    modeller.addSolvent(
        forcefield,
        model='tip3p',
        padding=10*angstroms,
        ionicStrength=0.15*molar, neutralize=True
    )

    print(f"System: {modeller.topology.getNumAtoms()} atoms, "
          f"{modeller.topology.getNumResidues()} residues")

    # Create system
    system = forcefield.createSystem(
        modeller.topology,
        nonbondedMethod=PME,         # Particle Mesh Ewald for long-range electrostatics
        nonbondedCutoff=1.0*nanometer,
        constraints=HBonds,           # Constrain bonds involving H (not intermolecular H-bonds)
        rigidWater=True,
        ewaldErrorTolerance=0.0005
    )

    return modeller, system
```

### 2. Energy Minimization

```python
from openmm.app import *
from openmm import *
from openmm.unit import *

def minimize_energy(modeller, system, output_pdb="minimized.pdb",
                     max_iterations=1000, tolerance=10.0, platform_name=None):
    """
    Energy minimize the system to remove steric clashes.

    Args:
        modeller: Modeller object with topology and positions
        system: OpenMM System
        output_pdb: Path to save minimized structure
        max_iterations: Maximum minimization steps
        tolerance: Convergence criterion in kJ/mol/nm

    Returns:
        simulation object with minimized positions
    """
    # Keep the integrator at 2 fs for the subsequent NVT/NPT examples.
    integrator = LangevinMiddleIntegrator(300*kelvin, 1/picosecond, 0.002*picoseconds)

    # Automatic platform selection, or an explicit tested platform (e.g. CPU).
    # A registered GPU plugin does not prove a working device or driver.
    platform = Platform.getPlatformByName(platform_name) if platform_name else None
    simulation = Simulation(modeller.topology, system, integrator, platform)
    simulation.context.setPositions(modeller.positions)

    # Check initial energy
    state = simulation.context.getState(getEnergy=True)
    print(f"Initial energy: {state.getPotentialEnergy()}")

    # Minimize
    simulation.minimizeEnergy(
        tolerance=tolerance*kilojoules_per_mole/nanometer,
        maxIterations=max_iterations
    )

    state = simulation.context.getState(getEnergy=True, getPositions=True)
    print(f"Minimized energy: {state.getPotentialEnergy()}")

    # Save minimized structure
    with open(output_pdb, 'w') as f:
        PDBFile.writeFile(simulation.topology, state.getPositions(), f)

    return simulation
```

### 3. NVT Equilibration

```python
from openmm.app import *
from openmm import *
from openmm.unit import *

def run_nvt_equilibration(simulation, n_steps=50000, temperature=300,
                            report_interval=1000, output_prefix="nvt"):
    """
    NVT equilibration: constant N, V, T.
    Equilibrate velocities to target temperature.

    Args:
        simulation: OpenMM Simulation (after minimization)
        n_steps: Number of MD steps (50000 × 2fs = 100 ps)
        temperature: Temperature in Kelvin
        report_interval: Steps between data reports
        output_prefix: File prefix for trajectory and log
    """
    # This example is unrestrained; add validated restraints before Context creation.
    if any("Barostat" in type(f).__name__ and f.getFrequency() > 0
           for f in simulation.system.getForces()):
        raise V

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

