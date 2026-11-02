---
id: sci-datamol
name: "Scientific: datamol"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Pythonic wrapper around RDKit with simplified interface and sensible defaults. Preferred for standard drug discovery including SMILES parsing, standardization, descriptors, fingerprints, clustering, 3D conformers, parallel processing. Returns native rdkit.Chem.Mol objects. For ad"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "datamol"
keywords:
  - "datamol"
  - "pythonic"
  - "wrapper"
  - "around"
  - "rdkit"
  - "simplified"
  - "interface"
---

# Datamol Cheminformatics Skill

## Overview

Datamol is a Python library that provides a lightweight, Pythonic abstraction layer over RDKit for molecular cheminformatics. Simplify complex molecular operations with sensible defaults, efficient parallelization, and modern I/O capabilities. All molecular objects are native `rdkit.Chem.Mol` instances, ensuring full compatibility with the RDKit ecosystem.

**Verified target:** datamol **0.13.0**, released September 9, 2026. Local checks used
Python 3.13 and RDKit 2026.03.6. Python 3.11+ and RDKit 2024.09+ are required.
The 0.13 distribution includes SELFIES, visualization, cloud, Excel and Parquet
runtime dependencies. Current API examples and verification limits are recorded in
[references/review.md](references/review.md). Pin the environment: RDKit upgrades can
change canonical representations and retained conformers. Compare chemical invariants,
not a fixed conformer count or an exact version-dependent canonical string.

**Key capabilities**:
- Molecular format conversion (SMILES, SELFIES, InChI)
- Structure standardization and sanitization
- Molecular descriptors and fingerprints
- 3D conformer generation and analysis
- Clustering and diversity selection
- Scaffold and fragment analysis
- Chemical reaction application
- Visualization and alignment
- Batch processing with parallelization
- Cloud storage support via fsspec

## Installation and Setup

Guide users to install datamol:

```bash
uv pip install "datamol==0.13.0"
```

RDKit and the S3/GCS, Excel/Parquet, visualization and SELFIES dependencies are
installed by the current distribution; separate feature extras are not required.
Use an isolated environment to avoid conflicting scientific-package requirements.

**Import convention**:
```python
import datamol as dm
```

## Core Workflows

Ten workflow areas, each with worked code, are documented in
[references/core_workflows.md](references/core_workflows.md):

| # | Area | Covers |
| --- | --- | --- |
| 1 | Basic molecule handling | `to_mol`, batch conversion, error handling, canonical and isomeric SMILES, sanitization and full standardization |
| 2 | Reading and writing files | SDF, SMILES, CSV, Excel with rendered structures, the universal reader/writer, and cloud or HTTPS paths |
| 3 | Descriptors and properties | the standard descriptor set, parallel computation, aromaticity, stereochemistry, flexibility, and filtering |
| 4 | Fingerprints and similarity | ECFP4 and other types, pairwise and cross-set distances, nearest-neighbour lookup (Tanimoto distance = 1 − similarity) |
| 5 | Clustering and diversity | similarity clustering, diverse subset picking, and cluster centroids |
| 6 | Scaffold analysis | Bemis-Murcko scaffolds, grouping and counting, and scaffold-disjoint train/test splits |
| 7 | Fragmentation | fragmenting molecules, finding common fragments across a library, and fragment-based scoring |
| 8 | 3D conformers | generation, access, RMSD clustering, representative selection, and SASA |
| 9 | Visualization | grids, files, publication SVG, substructure alignment, atom and bond highlighting, conformer display |
| 10 | Chemical reactions | reaction SMARTS, applying to a molecule or a whole library |

Three end-to-end pipelines — load/filter/analyze, SAR by scaffold series, and virtual
screening — are in [references/workflow_patterns.md](references/workflow_patterns.md).

## Parallelization

Datamol includes built-in parallelization for many operations. Use `n_jobs` parameter:
- `n_jobs=1`: Sequential (no parallelization)
- `n_jobs=-1`: Use all available CPU cores
- `n_jobs=4`: Use 4 cores

**Functions supporting parallelization**:
- `dm.read_sdf(..., n_jobs=-1)`
- `dm.descriptors.batch_compute_many_descriptors(..., n_jobs=-1, batch_size=128)`
- `dm.cluster_mols(..., n_jobs=-1)`
- `dm.pdist(..., n_jobs=-1)`
- `dm.conformers.sasa(..., n_jobs=-1)`

**Progress bars**: Many batch operations support `progress=True` parameter.
For parallel descriptor batches, supply a positive `batch_size` (for example 128).
In the tested 0.13.0 stack the default None reaches joblib and raises when parallelism is enabled.

## Reference Documentation

For detailed API documentation, consult these reference files:

- **`references/core_api.md`**: Core namespace functions (conversions, standardization, fingerprints, clustering)
- **`references/io_module.md`**: File I/O operations (read/write SDF, CSV, Excel, remote files)
- **`references/conformers_module.md`**: 3D conformer generation, clustering, SASA calculations
- **`references/descriptors_viz.md`**: Molecular descriptors and visualization functions
- **`references/fragments_scaffolds.md`**: Scaffold extraction, BRICS/RECAP fragmentation
- **`references/reactions_data.md`**: Chemical reactions and toy datasets

## Best Practices

1. **Choose and record a task-specific standardization policy** for external molecules.
   Preserve original structures and IDs alongside transformed ones; metal disconnection,
   neutralization, salt stripping, and stereochemistry changes can alter the assayed entity.
   Do not apply these transformations automatically to organometallic or formulation tasks.
   The following is an illustrative policy for inputs where metal disconnection is intended:
   ```python
   mol = dm.standardize_mol(mol, disconnect_metals=True, normalize=True, reionize=True)
   ```

2. **Check for None values** after molecule parsing:
   ```python
   mol = dm.to_mol(smiles)
   if mol is None:
       raise ValueError("Invalid SMILES; retain the source row in the rejection log")
   ```

3. **Use parallel processing** for large datasets:
   ```python
   result = dm.parallelized(dm.to_mol, smiles_list, n_jobs=-1, progress=True)
   ```

4. **Use cloud I/O for the requested remote paths** with the selected provider credentials:
   ```python
   df = dm.read_sdf("s3://bucket/compounds.sdf", as_df=True, mol_column="mol")
   ```

5. **Use appropriate fingerprints** for similarity:
   - ECFP (Morgan): General purpose, structural similarity
   - MACCS: Fast, smaller feature space
   - Atom pairs: Considers atom pairs and distances

6. **Consider scale limitations**:
   - Butina clustering stores O(N²) pairwise distances; choose a size limit from the memory budget.
   - For larger datasets: use `pick_diverse` with a bounded `npick`; hierarchical clustering can also need quadratic memory.

7. **Scaffold splitting for ML**: Ensure proper train/test separation by scaffold

8. **Align molecules** when

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

