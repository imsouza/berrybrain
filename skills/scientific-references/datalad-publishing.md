---
id: sciref-datalad-publishing
name: "Scientific Ref: Siblings, publishing, and credentials"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (datalad): Siblings, publishing, and credentials"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "datalad publishing"
  - "siblings, publishing, and credentials"
keywords:
  - "datalad"
  - "publishing"
  - "specialized"
  - "scientific"
  - "reference"
  - "siblings"
---

# Siblings, publishing, and credentials

## The two-target model

A DataLad dataset almost never publishes to one place. The Git history and the annexed
content usually go to different targets, because Git hosting services will not store the
data. The normal shape is a Git sibling plus a storage sibling, with a declared dependency
between them.

Getting this wrong produces the most common broken publication: collaborators clone
successfully, see every file listed, and then find every `datalad get` failing because the
content was never uploaded anywhere reachable.

## Managing siblings

```
datalad siblings [-h] [-d DATASET] [-s NAME] [--url [URL]] [--pushurl PUSHURL]
    [-D DESCRIPTION] [--fetch] [--as-common-datasrc NAME] [--publish-depends SIBLINGNAME]
    [--publish-by-default REFSPEC] [--annex-wanted EXPR] [--annex-required EXPR]
    [--annex-group EXPR] [--annex-groupwanted EXPR] [--inherit] [--no-annex-info]
    [-r] [-R LEVELS] [--version] [{query|add|remove|configure|enable}]
```

Five actions. `query` is the default and reports known siblings. `add` and `configure` are
the same operation except that adding a sibling whose name already exists fails while
reconfiguring does not. `enable` completes access for a git-annex special remote in a
fresh clone. `remove` de-configures a sibling.

Options that carry real consequences:

- `--publish-depends SIBLINGNAME` adds "a dependency such that the given existing sibling
  is always published prior to the new sibling". Set this on the Git sibling, naming the
  storage sibling, and the ordering problem stops being something anyone has to remember.
- `--annex-wanted EXPR` sets a git-annex preferred-content expression for the sibling, for
  example `standard` combined with a group, or `include=*.nii.gz`. `--annex-required`
  makes content mandatory there rather than merely wanted.
- `--pushurl` supplies a separate write URL when the read URL cannot be pushed to, the
  usual case for an HTTPS read path with an SSH write path.
- `--as-common-datasrc NAME` configures a sibling "as a common data source of the dataset
  that can be automatically used by all consumers", which is how a public mirror becomes
  usable by anyone who clones without them configuring anything.
- `--inherit` takes configuration from the superdataset's corresponding sibling, which
  matters when publishing a nested dataset hierarchy.

## Creating siblings

Rather than configuring by hand, use the `create-sibling-*` family, which creates the
remote side and configures the local side together:

| Command                                           | Target                          |
| ------------------------------------------------- | ------------------------------- |
| `datalad create-sibling-github`                   | A GitHub repository             |
| `datalad create-sibling-gitlab`                   | A GitLab project                |
| `datalad create-sibling-gogs` / `-gin` / `-gitea` | GOGS, GIN, and Gitea instances  |
| `datalad create-sibling-ria`                      | A RIA store                     |
| `datalad create-sibling`                          | A generic sibling over SSH      |

The `create-sibling-*` family covers *Git* siblings (a Git remote plus a hosting-service
repository or project) and the RIA layout, which packages a Git remote and a matching
git-annex special remote together. Storage-only targets — S3 buckets, WebDAV, plain SSH
directories, rclone-reachable services — are git-annex *special remotes* rather than Git
remotes, and they are created with `git annex initremote` rather than `create-sibling-*`.
That distinction is what the two-target model turns on: the Git sibling carries history,
the storage sibling carries content. RIA stores, GIN, and suitable filesystem/SSH
Git-annex repositories can serve both from one infrastructure location.

GIN is worth knowing about in a neuroscience context because it hosts annexed content
directly, which collapses the two-target model back into one target.

## RIA stores

A RIA store is a flat, filesystem-level layout for holding many datasets, designed for
cluster and institutional storage where per-dataset repositories are impractical. Clone
URLs use a `ria+` prefix and a fragment identifying the dataset:

```bash
datalad clone "ria+ssh://user@hostname/absolute/path/to/ria-store#DATASET-UUID"
datalad clone "ria+file://${HOME}/myriastore#~dl-101"
```

The fragment is either the full dataset ID or an alias prefixed with `~`. Aliases exist
because dataset IDs are UUIDs and nobody remembers them.

```bash
datalad create-sibling-ria -s ria-backup --alias dl-101 --new-store-ok \
  "ria+file://${HOME}/myriastore"
```

- `--new-store-ok` permits creating the store when it does not already exist. Without it,
  pointing at a nonexistent path is an error rather than a silent creation.
- `--alias` sets the friendly name used in the clone fragment.
- `--storage-sibling` controls the git-annex special remote. `off` disables it, and `only`
  creates the special remote without the regular RIA sibling.
- `--shared` sets multi-user permissions using the values `git init --shared` accepts.

By default the command creates both a regular sibling and a storage sibling named with a
`-storage` suffix and sets their publication dependency. RIA HTTP(S) access is read-only;
provide an SSH/file `--push-url` for writes. Quote RIA URLs so shell `#`, `~`, and bracket
interpretation cannot change them. Do not run ordinary git-annex commands directly
inside a RIA store; access its special layout through the ORA remote.

## Pushing

```
datalad push [-h] [-d DATASET] [--to SIBLING] [--since SINCE] [--data
    {anything|nothing|auto|auto-if-wanted}] [-f
    {all|gitpush|checkdatapresent}] [-r] [-R LEVELS] [-J NJOBS]
    [--version] [PATH ...]
```

`--data` controls annexed content transfer, and the default is `auto-if-wanted`:

| Value | Behaviour |
|---|---|
| `anything` | Transfer selected current annexed content without preferred-content filtering |
| `nothing` | Skip `git annex copy` entirely, publishing history only |
| `auto` | Let wanted expressions and required copy counts select transfers |
| `auto-if-wanted` | Default. Apply auto mode when wanted is configured; otherwise behave as `anything` |

Without a wanted expression, the default does transfer selected content; it is not a
history-only push. All modes are bounded by selected paths/current revision and local
content availability. A push is not an archive of every h

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

