---
id: sciref-datamol-review
name: "Scientific Ref: Review provenance — September 30, 2026"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (datamol): Review provenance — September 30, 2026"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "datamol review"
  - "datamol revisao"
  - "review provenance — september 30, 2026"
keywords:
  - "datamol"
  - "review"
  - "revisao"
  - "specialized"
  - "scientific"
  - "reference"
  - "provenance"
---

# Review provenance — September 30, 2026

Target: Datamol 0.13.0 / RDKit 2026.03.6, Python 3.13 on macOS. This skill uses a
local Python API; it specifies no hosted molecular-service REST endpoints. S3/GCS/HTTPS
examples are provider-dependent paths, not verified live access or write operations.

## Primary sources checked

- [PyPI release metadata and artifacts](https://pypi.org/project/datamol/0.13.0/):
  release September 9, 2026, Python >=3.11. Runtime includes cloud/viz/Excel/SELFIES dependencies.
- [Official release](https://github.com/datamol-io/datamol/releases/tag/0.13.0) and
  [upgrade guide](https://docs.datamol.io/stable/migration.html): supported stack,
  heterocycles descriptor-key spelling, symmetry-aware RMS, binary/JSON interchange.
- [Release source tree](https://github.com/datamol-io/datamol/tree/0.13.0/datamol):
  checked installed wheel source against signatures/behavior rather than relying on stale
  prose/type hints (notably reaction return shapes and MMPA fragment strings).
- [Molecule API](https://docs.datamol.io/stable/api/datamol.mol.html),
  [conversions](https://docs.datamol.io/stable/api/datamol.convert.html),
  [fingerprints](https://docs.datamol.io/stable/api/datamol.fp.html),
  [similarity](https://docs.datamol.io/stable/api/datamol.similarity.html), and
  [clustering](https://docs.datamol.io/stable/api/datamol.cluster.html).
- [I/O](https://docs.datamol.io/stable/api/datamol.io.html),
  [descriptors](https://docs.datamol.io/stable/api/datamol.descriptors.html),
  [visualization](https://docs.datamol.io/stable/api/datamol.viz.html), and
  [conformers](https://docs.datamol.io/stable/api/datamol.conformers.html).
- [Scaffolds](https://docs.datamol.io/stable/api/datamol.scaffold.html),
  [fragments](https://docs.datamol.io/stable/api/datamol.fragment.html),
  [reactions](https://docs.datamol.io/stable/api/datamol.reactions.html), and
  [bundled data](https://docs.datamol.io/stable/api/datamol.data.html).

## Runtime scope

The repository's Datamol suite executes the local reference examples and checks parsed
failure retention, source-ID/selection correspondence, binary and JSON round trips,
descriptor definitions, fingerprint and distance shapes, selection/cluster return contracts,
Murcko frameworks, labelled BRICS fragments, MMPA pairs, fuzzy-scaffold DataFrames,
reaction product groups, and the full small bundled solubility example. It verifies
SDF/SMI/MOL/MOL2/PDB/CSV/Excel/Parquet/JSON paths, genuine PNG/SVG encodings, finite conformer
coordinates/energies, RMS cutoff, SASA, and conformer-ID/energy correspondence after selection.
Two-worker batches were also exercised. Parallel descriptor batching requires an explicit
positive `batch_size` on this stack; the default None raises in joblib.

The toy regression is an API check, not a validated benchmark. Finite conformer energy
is not proof of minimization convergence or population weighting. Notebook widget construction
was exercised; interactive browser rendering was not. Remote authentication, cloud writes,
Windows FreeSASA, other Python/RDKit combinations and large-library scaling were not tested.
Datamol explicitly disables its SASA wrapper on Windows. Source files and original molecular
records remain necessary because a parsed table cannot recover text from invalid source records.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

