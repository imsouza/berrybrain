---
id: sci-datalad
name: "Scientific: datalad"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Retrieves, versions, and publishes scientific datasets with DataLad and git-annex, and captures computational provenance with datalad run, rerun, and containers-run. Use when cloning or fetching data from OpenNeuro, DANDI, datasets.datalad.org, or any DataLad dataset; when a file"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "datalad"
keywords:
  - "datalad"
  - "retrieves"
  - "versions"
  - "publishes"
  - "scientific"
  - "datasets"
---

# DataLad

## Overview

DataLad is a data management layer over Git and git-annex. Git tracks the dataset
structure, small text files, and the history. git-annex tracks the *content* of large
files, storing each file as a key and keeping the bytes somewhere that is not necessarily
the local repository.

A normal clone retrieves Git history and the top-level file listing while leaving
annexed bytes unfetched. Installed subdatasets have their own histories; a clone does not
automatically populate them. Clone cost depends on Git history and file count, not just
the data volume. Retrieve annexed bytes selectively with `datalad get`.

The second thing DataLad adds is provenance. `datalad run` executes a command and commits
the result together with a machine-readable record of the command, its inputs, and its
outputs. `datalad rerun` reads that record back and re-executes it. This turns "how was
this figure produced" from an archaeology problem into a command.

## When to use DataLad instead of plain Git

Use DataLad when any of the following holds:

- Files are too large for Git to handle comfortably, or the total exceeds what every
  collaborator wants on disk.
- Data lives in more than one place (a lab server, a cluster scratch, S3, a supercomputer)
  and you need to know which copies exist.
- The analysis must be re-executable, and a plain commit message is not enough evidence.
- You are consuming published datasets from OpenNeuro, DANDI, or `datasets.datalad.org`,
  which are distributed as DataLad datasets.
- The project nests other datasets inside it and you want each one to keep its own
  independent history.

Use plain Git when the repository is code and text only, everything fits comfortably in
Git, and nobody needs partial checkouts. DataLad on top of a small pure-code repository
adds indirection without buying anything.

## Installation

```bash
# git-annex is NOT written in Python but is available from PyPI if you already
# have git itself installed:
uv pip install git-annex
# You can also install it first from the system
# (Debian/Ubuntu: apt install git-annex; macOS: brew install git-annex;
#  conda-forge: conda install -c conda-forge git-annex)
uv pip install "datalad==1.6.5"
uv pip install "datalad-container==1.2.6"   # only for containers-run

datalad wtf --section dependencies   # confirm git-annex version is visible
```

The PyPI `git-annex` package supplies platform-specific binaries. The reviewed
10.20260901.post1 wheels cover Linux glibc 2.34+ (x86_64/ARM64), macOS ARM64 14+ and
x86_64 15+, and Windows x86_64. Use a system package when no wheel matches. Keep its
environment on `PATH` and verify the executable; the wheel does not supply Git itself.
Configure Git author name/email before creating or saving a dataset.

`datalad wtf` prints the resolved environment and is the first thing to run when behaviour
looks impossible. An old or missing git-annex is behind a large share of confusing errors.

DataLad is MIT licensed; git-annex has a separate AGPL license. Consult the upstream
license when redistributing either tool.

## The failure that bites first: pointers are not data

After `datalad clone`, annexed files exist as symlinks into `.git/annex/objects/` (or as
small pointer files where symlinks are unavailable, such as on Windows or a crippled
filesystem). Nothing has downloaded the content yet.

Illustrative remote-data example; inspect the selected revision for the exact path and
install NiBabel before the Python read. The refresh tested equivalent local pointer/get
behavior without downloading imaging data.

```bash
datalad clone https://github.com/OpenNeuroDatasets/ds000001.git
cd ds000001
ls sub-01/anat/            # the file is listed
python -c "import nibabel; nibabel.load('sub-01/anat/sub-01_T1w.nii.gz')"   # fails
datalad get sub-01/anat/sub-01_T1w.nii.gz                                   # now it works
```

The failure mode to recognise: a tool reports the file as empty, truncated, corrupt, "not
a gzip file", or a broken symlink, and the file size on disk is a few hundred bytes. These symptoms can indicate an unfetched annex pointer; confirm with annex status
before diagnosing corruption. **Run `datalad get` before reading data, and treat
"file exists" as insufficient evidence that its content is present.**

Before an analysis touches a directory, fetch it explicitly:

```bash
datalad get sub-01/                  # everything under a path
datalad get -r .                     # everything, including subdatasets
datalad get -n -r .                  # subdataset structure only, no file content
```

`datalad status --annex availability` checks which content is present locally, and
`git annex whereis <path>` reports which repositories hold a given file. `whereis` reads
recorded state and does not contact the remotes, so it tells you what git-annex last
learned rather than what is true right now.

See [data-access.md](references/data-access.md) for finding datasets, subdataset
behaviour, dropping content safely, and repairing a dataset.

## Recording provenance with datalad run

`datalad run` is the reason to reach for DataLad in a methods context. It saves the
command alongside its effect, in the same commit:

Illustrative FSL example (requires `bet` and an existing `derivatives/` directory):

```bash
datalad run -m "extract brain and mask" \
  --input "sub-01/anat/sub-01_T1w.nii.gz" \
  --output "derivatives/sub-01_brain.nii.gz" \
  --output "derivatives/sub-01_brain_mask.nii.gz" \
  "bet {inputs[0]} {outputs[0]} -m"
```

What each part does, and why skipping it hurts:

- `--input` retrieves the content before running, so the command does not fail on a
  pointer. It also records the dependency, which is what lets `rerun` fetch the same
  inputs on a different machine.
- `--output` unlocks or removes the target first, so git-annex does not refuse to write
  over content it is protecting. Without it, a second run of the same command commonly
  fails with a permission error on an annexed file that looks read-only.
- `{inputs}` and `{outputs}` expand to those values. `{pwd}`, `{dspath}`, and `{tmpdir}`
  are also available, and `{inputs[0]}` indexes individual entries.
- The commit message carries a JSON run record between `=== Do not change lines below ===`
  and `^^^ Do not change lines above ^^^`. Do not hand-edit that block; `rerun` parses it.

`datalad run` refuses to start when the dataset has unsaved modifications, because an
unclean starting state m

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

