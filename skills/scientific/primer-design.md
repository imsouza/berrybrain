---
id: sci-primer-design
name: "Scientific: primer-design"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Designs and audits PCR and RT-qPCR primers with Primer3, explicit thermodynamic conditions, reference-based off-target amplification searches, and traceable sequence coordinates. Use for designing primer pairs, checking existing primers, exon-junction or isoform-specific assays, "
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "primer design"
  - "primer-design"
keywords:
  - "primer"
  - "design"
  - "designs"
  - "audits"
  - "qpcr"
  - "primers"
  - "explicit"
---

# Primer design and specificity

Produce candidate oligos in 5-prime-to-3-prime orientation, with the exact template,
chemistry, intended products, and search scope behind each conclusion. Calculate
sequence-dependent quantities with the supplied tools. A familiar gene name, good
Primer3 penalty, or a single BLAST alignment cannot establish primer specificity.

## Choose the workflow

| Request | Start here |
| --- | --- |
| New genomic PCR or RT-qPCR pair | Define the assay and reference; design; assess thermodynamics; screen products. |
| Check an existing pair | Prepare pair TSV; assess both full oligos and annealing cores; screen with explicit intended coordinates. |
| Exon junction, transcript isoform, allele discrimination | Read [design-workflows.md](references/design-workflows.md); supply sequence annotation before imposing constraints. |
| Cloning/adaptor-tailed primers | Design annealing cores, append declared 5-prime tails, reassess full oligos, reconstruct the final product. |
| Multiplex panel | Enable `--multiplex` in both thermodynamics and specificity tools to assess oligo interactions and cross-pair products. |
| Degenerate, bisulfite, probe, or modified-base assay | Use the specialized workflow in [design-workflows.md](references/design-workflows.md); the bundled ordinary-DNA model is insufficient. |

The local tooling supports paired primers with unambiguous ACGT cores. Advanced assay
types have substantive design and validation guidance, but are not silently reduced
to ordinary PCR. This skill designs assays; expression normalization, experimental
diagnostic validation, and guide-RNA design are separate tasks.

## Establish the assay contract

Obtain what changes the result; use explicit provisional assumptions for an exploratory
design, and identify them in the report:

- **Purpose and template:** genomic DNA, cDNA, plasmid, or another defined substrate;
  target organism, accession **with version**, assembly/transcript release, strand,
  desired isoforms, and product-size range. Name wanted and unwanted templates.
- **Sequence evidence:** local FASTA plus source/retrieval date and its SHA-256 hash.
  A locus excerpt uses local coordinates; record its mapping to the full reference.
  Include relevant paralogs, pseudogenes, alternate contigs, transcript isoforms,
  vector backbone, and host sequence in the appropriate screen.
- **Reaction conditions:** polymerase/buffer, monovalent salt, total divalent salt,
  total dNTP, and oligo concentrations. Primer3 uses mM for salts/dNTP and nM for DNA.
  Record the initial reaction concentration separately from Primer3's effective
  annealing-oligo concentration parameter. Engine defaults are assumptions.
- **Constraints:** target interval, allowed/excluded binding regions, junctions,
  variant exclusions and their source, fixed primers, tails, or multiplex membership.
  Do not guess exon boundaries or silently substitute another assembly.
- **Definition of an acceptable result:** relevant off-target references, amplicon
  lengths, mismatch search limits, controls, and experimental validation appropriate
  to the assay. There is no universal thermodynamic cutoff that validates all PCRs.

Use [input-contract.md](references/input-contract.md) for file schemas and coordinate
examples. Copy [assay-report-template.md](assets/assay-report-template.md) into the
analysis directory to collect evidence. Reference retrieval may be manual or through
an established sequence API; preserve accession/version and verify the returned
sequence. The supplied scripts use local files and do not submit sequences online.

## Install and verify

Set `SKILL_DIR` to this skill's actual installed directory. Work in a separate analysis
directory so environments, reference databases, and results do not enter the skill.

```bash
uv venv --python 3.13 .venv-primer
uv pip install --python .venv-primer/bin/python -r "$SKILL_DIR/assets/requirements.txt"
.venv-primer/bin/python "$SKILL_DIR/scripts/design_primers.py" --help
```

Use the environment's `Scripts/python.exe` on Windows. The design/thermodynamic
examples target primer3-py **2.3.1**, tested with Python **3.13**. For the optional
BLAST engine, install NCBI BLAST+ from its official distribution and check:

```bash
blastn -version
makeblastdb -version
```

Local integration checks also exercise BLAST+ 2.17.0; other releases require checking
their output and search behavior before claiming equivalent coverage.

Read [sources.md](references/sources.md) when updating dependencies or API assumptions.
The scripts record engine versions and effective settings in their JSON reports.

## 1. Design candidates

For an initial functional demonstration, use the bundled synthetic sequence. It is
nonbiological example input, not an experimentally validated assay:

```bash
.venv-primer/bin/python "$SKILL_DIR/scripts/design_primers.py" \
  --template "$SKILL_DIR/assets/demo-template.fasta" \
  --preset qpcr --config "$SKILL_DIR/assets/qpcr-config.json" \
  --output design.json --pairs-out pairs.tsv --expected-out expected.tsv
```

For actual work, substitute the reviewed target FASTA and constraints. A multi-record
FASTA requires `--record` with its exact ID. The `pcr` preset requests 100–1000 bp;
`qpcr` requests 70–200 bp. Override these starting ranges in the configuration.
The example overrides its range to 90–180 bp and includes a specific target interval.
Multiple `SEQUENCE_TARGET` intervals are alternatives: Primer3 flanks at least one.
To require coverage of every interval, supply one enclosing target and verify the
returned product; separate assays require separate design runs.

The tool:

- Passes validated `sequence_args` and `global_args` to Primer3. Unsupported or
  misspelled tags fail rather than silently changing the task.
- Converts ambiguous template positions to `N` and forbids ambiguous primer bases.
  It does not interpret lowercase sequence as a repeat mask; use explicit exclusions.
- Optionally imports `--mask-bed` exclusions in **the supplied template's coordinates**.
  Use BED intervals for variant/repeat masking only after validating the reference
  mapping; it does not infer allele frequencies or convert arbitrary VCFs.
- Verifies returned forward and reverse sequences against the template and checks
  product lengths. Primer3's right-primer position is converted into a half-open
  binding interval; the reverse primer is already in ordering orientation.
- Optionally appends `--forward-

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

