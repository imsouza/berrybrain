---
id: sciref-geniml-bedspace
name: "Scientific Ref: BEDspace"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (geniml): BEDspace"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "geniml bedspace"
  - "bedspace"
keywords:
  - "geniml"
  - "bedspace"
  - "specialized"
  - "scientific"
  - "reference"
---

# BEDspace

Verified against `geniml==0.8.4` release source, the official BEDbase tutorial,
and the archived StarSpace repository on 2026-10-01.

## Status

BEDspace jointly embeds region sets and metadata labels using the external
StarSpace program. The primary paper evaluates label-to-region,
region-to-label, and region-to-region retrieval.

Primary source: Gharavi et al. (2024), *Joint representation learning for
retrieval and annotation of genomic interval sets*,
doi:[10.3390/bioengineering11030263](https://doi.org/10.3390/bioengineering11030263).

The code path still exists in Geniml 0.8.4, but it is a **legacy reproduction
workflow**:

- StarSpace is not a Python dependency and must be compiled separately.
- `facebookresearch/StarSpace` is archived.
- Geniml does not state or enforce a compatible StarSpace version.
- several official examples and 0.8.4 CLI/API details disagree;
- with Gtars 0.10.0, `data_preparation` calls the removed
  `unknown_token_id()` API and assumes token objects instead of BatchEncoding;
  its broad exception handler prints an error and returns a blank document;
- the eight-worker preprocessing pool passes a Rust Tokenizer between workers;
  native pickling/process compatibility needs separate verification;
- the 0.8.4 `bedspace search` dispatcher imports a `main` function that is
  absent from `geniml.bedspace.search`.

Do not choose BEDspace by default for a new production search service. Use it
when reproducing the published method or an existing pinned workflow, and
record the limitations.

## Data and privacy contract

Required inputs:

- a local directory of validated BED files;
- a local metadata CSV with a file-path/name column and selected label columns;
- a local universe BED;
- explicit train/test manifests grouped by patient/donor;
- one assembly, coordinate convention, and contig policy.

Metadata values can reveal diagnoses, cell types, tissues, treatment, cohort,
or donor identity. BEDspace places selected labels directly into training text
and writes filenames/labels into result CSVs. Keep inputs and outputs in a
restricted project directory. Default logs should report only row/file counts
and schema names, not values.

Before preprocessing:

1. Split complete patients/donors into train/validation/test.
2. Build or select the universe using training data only.
3. Validate every BED and the universe against the same chromosome sizes.
4. Confirm metadata path values resolve to intended local regular files.
5. Reject URLs, symlinks, duplicate paths, missing files, and mixed assemblies.
6. Decide how missing/multi-valued labels are encoded.

```bash
python skills/geniml/scripts/corpus_auditor.py \
  --manifest data/bedspace.tsv \
  --group-column patient_id \
  --split-column split \
  --assembly-column assembly
```

## Exact 0.8.4 CLI surface

The release exposes:

```text
geniml bedspace preprocess
geniml bedspace train
geniml bedspace distances
geniml bedspace search
```

The following are source/parser-checked reproduction templates, not a working
pipeline on the current stack. The synthetic `data_preparation` call was
executed and returned a blank document for valid input. Resolve that upstream
compatibility failure and verify nonempty documents before training; a zero
exit status or file presence is insufficient. StarSpace was not built or run.
Use installed `--help` as the final authority for flags.

### Preprocess

```bash
geniml bedspace preprocess \
  --input /absolute/project/beds/ \
  --metadata /absolute/project/train.csv \
  --universe /absolute/project/universe.bed \
  --labels "cell_type,target" \
  --output /absolute/project/preprocessed/
```

The implementation creates a Gtars `Tokenizer` from the universe, uses a
hard-coded pool of eight processes, and writes:

```text
<output>train_input.txt
```

The code joins this filename by string concatenation, not `os.path.join`, so
the output argument must end in a path separator. The metadata helper also
concatenates the input directory and `file_name`, so `--input` and `--files`
need trailing separators. Use the exact `file_name` metadata column; commas
in path/label values are not preserved by its split-based representation. Create and validate the
directory first. The preprocessing text contains labels and tokenized genomic
content; protect it as sensitive derived data.

The current source does not expose worker bounds through the CLI. Run only
after estimating memory and CPU impact, or invoke a reviewed wrapper that
controls resources.

### Train

The long source flag is misspelled:

```text
--path-to-starsapce
```

Use the stable short form `-s`. Its value must be the **directory containing**
the executable named `starspace`; despite some help text, do not pass the
executable itself.

```bash
geniml bedspace train \
  -s /absolute/project/vendor/StarSpace \
  --input /absolute/project/preprocessed/train_input.txt \
  --output /absolute/project/model/ \
  --dim 100 \
  --epochs 50 \
  --lr 0.05
```

Geniml invokes an argv list equivalent to:

```text
starspace train
  -trainFile INPUT
  -model OUTPUT/starspace_trained_model
  -trainMode 0
  -dim DIM
  -epoch EPOCHS
  -negSearchLimit 5
  -thread 20
  -lr LEARNING_RATE
```

The thread count is hard-coded to 20. The implementation waits for the process
but does not check a nonzero return code. Verify output existence, size, and
checksums yourself. If an existing model path is present, Geniml adds
`-initModel` and resumes/mutates training; use a fresh output directory unless
resume is intentional.

### Distances

```bash
geniml bedspace distances \
  -i /absolute/project/model/starspace_trained_model \
  -s /absolute/project/vendor/StarSpace \
  --metadata-train /absolute/project/train.csv \
  --metadata-test /absolute/project/test.csv \
  --universe /absolute/project/universe.bed \
  --project-name heldout \
  --files /absolute/project/beds/ \
  --labels "cell_type,target" \
  --output /absolute/project/distances/ \
  --threshold 0.5
```

The current outputs are CSV/text files, not a single pickle:

- `raw_cosdist_rl.csv`
- `similarity_score_rl.csv`
- `similarity_score_rr.csv`
- `<project>_starspace_embed.txt`
- `<project>_train_starspace_embed.txt`

The implementation also uses `~/.bedspace/test_documents.txt` and
`~/.bedspace/train_documents.txt`. Use an isolated user account/environment or review that cache before
running on sensitive data. Output CSVs contain filenames and labels; never
paste unredacted rows into chat o

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

