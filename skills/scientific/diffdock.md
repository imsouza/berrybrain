---
id: sci-diffdock
name: "Scientific: diffdock"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Predicts protein-small-molecule binding poses with DiffDock and DiffDock-L from PDB or sequence plus SMILES/SDF/MOL2. Covers batch docking, pose triage, confidence interpretation, and validation. Use for molecular docking and virtual-screening pose generation, not binding-affinit"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "diffdock"
keywords:
  - "diffdock"
  - "predicts"
  - "protein"
  - "small"
  - "molecule"
  - "binding"
  - "poses"
---

# DiffDock: protein-small-molecule docking

DiffDock-L generates candidate ligand poses and ranks them by model confidence.
Confidence is neither a measured probability of correctness nor binding affinity.
Use this skill for one pair, batches, or separate receptor conformations; treat
library-wide confidence sorting as pose triage, not hit identification.

## Verified scope

Targets the current [v1.1.3 release](https://github.com/gcorso/DiffDock/releases/tag/v1.1.3).
Released source and current main's identical `inference.py` were checked on
2026-09-30. Bundled helpers were tested on tiny synthetic inputs; pretrained docking,
ESMFold, CUDA, Docker, GNINA, and hosted-demo execution were **not** run in this
review. Commands requiring those components are source-verified recipes, not
successful end-to-end demonstrations.

## Set up the upstream environment

```bash
git clone --branch v1.1.3 --depth 1 https://github.com/gcorso/DiffDock.git
cd DiffDock
conda env create --file environment.yml
conda activate diffdock
```

The upstream environment pins Python 3.9.18, CUDA 11.7 Torch/PyG wheels and old
scientific dependencies. Do not substitute current `torch` or the unrelated PyPI
`esm` package for `fair-esm`. The published CUDA environment is not a macOS-native
installation recipe. Follow upstream Docker instructions if suitable:

```bash
docker pull rbgcsail/diffdock
docker run -it --gpus all --entrypoint /bin/bash rbgcsail/diffdock
micromamba activate diffdock
```

Record the image digest: its unversioned tag need not equal the checked source.
PDB-based inference has a CPU path; sequence folding calls `.cuda()` unconditionally.
ESM2 embeddings are needed even for PDB inputs. First use can download docking,
ESM2 and (for sequence inputs) ESMFold weights and build SO(2)/SO(3) tables. Budget
storage and memory for all components; do not assume a single small checkpoint.

Run this skill's checker from the **DiffDock checkout** using its absolute path:

```bash
python /path/to/diffdock-skill/scripts/setup_check.py
```

It checks imports/files, not successful model loading, scientific validity, or full
version compatibility. An existing but incomplete score-model directory suppresses
upstream's automatic download; inspect checkpoint files when restoring a partial run.

## Prepare traceable inputs

1. Select the biological assembly/chains and a defensible protonation/tautomer state.
   Record receptor and ligand identifiers, file hashes, preparation choices, source
   coordinates, software versions, and intended stereochemistry. Missing atoms,
   waters, cofactors, metal coordination, and induced fit need explicit judgment.
2. Use PDB for the receptor or a complete amino-acid sequence. No ellipses. Upstream
   ESM2 truncates each chain at 1022 residues; longer chains can cause graph/embedding
   mismatches. Do not silently trim a biological target to make a run pass.
3. Use a SMILES or ligand file. Source readers support `.sdf`, `.mol2`, `.pdb`,
   `.pdbqt`; SDF input uses its first record. Existing ligand coordinates are
   discarded and a conformer regenerated. Inputting a pose does not restrain docking.
4. Use a fresh output directory for each run. Reusing one can leave old rank files
   from failed or differently sampled jobs. Preserve the expected input-ID manifest.

## Single pair

Run from the upstream repository root, with real prepared inputs:

```bash
python -m inference \
  --config default_inference_args.yaml \
  --protein_path protein.pdb \
  --ligand_description "CC(=O)Oc1ccccc1C(=O)O" \
  --out_dir results/run_001/ \
  --loglevel INFO
```

For sequence input, replace `--protein_path` with `--protein_sequence` and a full
sequence; this adds ESMFold/CUDA requirements and structural uncertainty.
Use the registered name `--ligand_description`, not argparse's implicit abbreviation
`--ligand` from the README.

Typical output (scores shown here are illustrative):

```text
results/run_001/complex_0/
  rank1.sdf
  rank1_confidence0.87.sdf
  rank2_confidence0.42.sdf
  ...
  rank10_confidence-1.23.sdf
```

`rank1.sdf` duplicates the top pose. Filename confidence is rounded to two decimals;
upstream rank reflects the original model score. `--save_visualisation` additionally
writes `rank<N>_reverseprocess.pdb`, not the SDFs themselves.

## Batch and ensemble runs

CSV columns are `complex_name,protein_path,ligand_description,protein_sequence`.
Use unique explicit names; paths resolve relative to the **inference working
directory**, not the CSV's directory. Protein path takes precedence over sequence.
The helper deliberately rejects unsafe/duplicate/blank names, empty batches,
duplicate headers and malformed sequence strings before inference.

```bash
python /path/to/diffdock-skill/scripts/prepare_batch_csv.py --create --output batch.csv
# Replace all example rows with the real inputs; run validation from inference CWD.
python /path/to/diffdock-skill/scripts/prepare_batch_csv.py batch.csv --validate
python -m inference --config default_inference_args.yaml \
  --protein_ligand_csv batch.csv --out_dir results/batch_001/ --batch_size 10
```

Validation checks paths and SMILES, not PDB/file chemistry or model suitability.
If validating elsewhere, `--base-dir` must equal the later inference working
directory; it does not rewrite the CSV. A SMILES slash or backslash encodes bond
stereochemistry and must not be treated as a path separator.

For an ensemble, provide one row per receptor conformation with distinct names.
Preserve each conformation's coordinates and identity. Confidence across structures
is not calibrated and cannot select a thermodynamically preferred state.

`batch_size` batches candidate poses within a complex; complexes are processed
sequentially. Arbitrary user-complex inference has **no** `--esm_embeddings_path`
or `--chain_cutoff` option. It creates ESM2 embeddings internally; benchmark dataset
preparation scripts are not a user-complex embedding cache. See the
[parameter contract](references/parameters_reference.md) before adapting examples.

## Change sampling safely

**YAML overwrites matching CLI values.** Appending `--samples_per_complex 20` to the
default configuration command still uses 10. Copy the bundled configuration and edit
its existing values:

```bash
cp /path/to/diffdock-skill/assets/custom_inference_config.yaml run_config.yaml
```

For example, change `samples_per_complex: 10` to `samples_per_complex: 20` in that
file, then run with `--config run_config.yaml

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

