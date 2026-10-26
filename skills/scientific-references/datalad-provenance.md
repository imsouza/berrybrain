---
id: sciref-datalad-provenance
name: "Scientific Ref: Computational provenance with DataLad"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (datalad): Computational provenance with DataLad"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "datalad provenance"
  - "computational provenance with datalad"
keywords:
  - "datalad"
  - "provenance"
  - "specialized"
  - "scientific"
  - "reference"
  - "computational"
---

# Computational provenance with DataLad

## Why this is the interesting half

Version control tells you that a file changed. Provenance tells you what produced it, from
what, and with which software. `datalad run` records the command and tracked inputs/outputs in the same commit as the change. Capturing software versions additionally requires a versioned environment specification or a tracked container; an executable name alone does not identify its installed build. `datalad
rerun` then reads that record back and re-executes it, so "is this reproducible" becomes a
command rather than an argument.

## Principles: STAMPED, and the YODA layout it grew out of

YODA ("YODAs Organigram on Data Analysis") is the convention DataLad analyses were
originally built on, and it is still what `datalad create -c yoda` configures. Its three
principles (one thing one dataset, record where the data came from, record what was done
to it) describe what a well-formed analysis looks like, but they were inspirational rather
than operational: there is nothing in them to check a dataset against.

STAMPED (<https://stamped-principles.org>) is the operationalized successor, formalized by
some of the original YODA authors. It states seven properties of a reproducible research
object, each backed by normative MUST/SHOULD/MAY requirements:

| Property | Core requirement |
|---|---|
| **S**elf-contained | Everything essential to replicate the computation is reachable within a single top-level research object |
| **T**racked | Persistent content identification and provenance are recorded for every component and every modification, including the versions involved |
| **A**ctionable | The object carries enough instruction to reproduce all results, specified as *executable* specifications rather than prose |
| **M**odular | Components are organized as independently versioned modules, included directly or linked as subdatasets |
| **P**ortable | Procedures depend on no undocumented host state; environments are explicitly specified and version controlled |
| **E**phemeral | Results are produced in disposable environments built only from the object's own contents |
| **D**istributable | Every referenced module and component is persistently retrievable by others |

**Actionable is the property `datalad run` exists to satisfy.** A README describing how a
figure was produced is documentation; a run record is an executable specification, and
`datalad rerun` is what makes it executable. The same commit satisfies Tracked, because
the command, its inputs, its outputs, and the versions they were taken at are recorded
next to the change rather than in a separate log that can drift away from it. Modular maps
onto subdatasets, Portable onto tracked images and runtime specifications, Ephemeral onto disposable
execution environments, and Distributable onto
siblings and RIA stores (see [publishing.md](publishing.md)).

Two companion resources make this checkable rather than aspirational:
<https://checklist.stamped-principles.org> walks the requirements as a MUST/SHOULD/MAY
checklist, and <https://examples.stamped-principles.org> collects worked patterns,
including ones built directly on `datalad run` and `datalad rerun`.

### The YODA layout in practice

Apply the layout at creation time:

```bash
datalad create -c yoda "my_analysis"
```

That produces:

```text
.
├── .gitattributes
├── CHANGELOG.md
├── code
│   ├── .gitattributes
│   └── README.md
└── README.md
```

The configuration matters more than the directories. Everything in `code/`, plus
`README.md` and `CHANGELOG.md`, is tracked by Git rather than git-annex, so scripts stay
directly readable and diffable in a clone that has fetched no data at all. Input data is
then added as a subdataset:

```bash
datalad clone -d . https://github.com/OpenNeuroDatasets/ds000001.git inputs/raw
```

The `-d .` is what registers the clone as a subdataset of the analysis rather than leaving
an unrelated repository sitting inside it.

## datalad run

```
datalad run [-h] [-d DATASET] [-i PATH] [-o PATH] [--expand {inputs|outputs|both}]
    [--assume-ready {inputs|outputs|both}] [--explicit] [-m MESSAGE]
    [--sidecar {yes|no}] [--dry-run {basic|command}]
    [--on-cmd-failure {error|save|all}] [-J NJOBS]
    [--version] ...
```

| Option | Documented behaviour | Practical consequence |
|---|---|---|
| `-i/--input PATH` | "A dependency for the run. Before running the command, the content for this relative path will be retrieved." | The command does not fail on an unfetched pointer, and `rerun` knows what to fetch elsewhere |
| `-o/--output PATH` | "Prepare this relative path to be an output file of the command." | Unlocks or removes the target so git-annex write protection does not block the write |
| `--explicit` | "Consider the specification of inputs and outputs to be explicit. Don't warn if the repository is dirty." | Lets a run proceed in a dirty dataset, and saves only the declared outputs |
| `--assume-ready {inputs\|outputs\|both}` | "Assume that inputs do not need to be retrieved and/or outputs do not need to unlocked or removed." | Skips preparation for speed; only safe when you have already done it |
| `--expand {inputs\|outputs\|both}` | "Expand globs when storing inputs and/or outputs in the commit message." | Records the concrete file list rather than the glob, which is what you want when the glob's meaning could change |
| `--dry-run {basic\|command}` | "Do not run the command; just display details about the command execution." | Check placeholder expansion before committing anything |
| `--sidecar {yes\|no}` | Store the run record in a separate file rather than in the commit message | Keeps long records out of `git log` output |

Placeholders available in the command string: `{pwd}` (current working directory),
`{dspath}` (dataset path), `{tmpdir}` (a temporary directory), `{inputs}` and `{outputs}`
(the values of the corresponding flags), and `{inputs[0]}` for indexed access.

Globs are permitted in `--input` and `--output`, and multiple flags may be given:

```bash
datalad run -m "second-level model" \
  -i "derivatives/sub-*/func/*_bold.nii.gz" \
  -i "code/model.py" \
  -o "results/group_map.nii.gz" \
  --expand inputs \
  "python code/model.py {outputs}"
```

### The run record

The commit message carries a machine-readable JSON block between the markers
`=== Do not change lines below ===` and `^^^ Do not change lines above ^^^`. It records
the command, the dataset ID, 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

