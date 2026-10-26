---
id: sciref-paperclip-repos-and-workspace
name: "Scientific Ref: Paper repositories, clipboard, and library"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (paperclip): Paper repositories, clipboard, and library"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "paperclip repos workspace"
  - "paper repositories, clipboard, and library"
keywords:
  - "paperclip"
  - "repos"
  - "workspace"
  - "specialized"
  - "scientific"
  - "reference"
  - "paper"
  - "repositories"
---

# Paper repositories, clipboard, and library

Reviewed on 2026-09-30 against installed 0.7.92 native help/source and the current
[core reference](https://paperclip.gxl.ai/skills/full_skill.md). These are illustrative workflows;
no repositories, uploads, sync, sharing, or library mutations were executed during this review.

| Store | Holds | Main commands |
|---|---|---|
| Repo | Paper membership, claims, verification state, snapshots | `git` / `repo` / `repos` |
| Clipboard | Uploaded PDFs, corpus links, generated artifacts | `upload`, `cp`, `sync` |
| Library | Imported papers and unmatched bibliographic records | `library`, `import` |

A repo does not copy the source into the clipboard, and a commit does not save an arbitrary report
file. `upload` persists named local artifacts. All persistent changes must fit the user's task;
read-and-cite research does not require creating a repo.

## Repo selection

`paperclip git`, `paperclip repo`, and `paperclip repos` are aliases of the same group; they do not
have different subsets of commands in 0.7.92.

```bash
paperclip repo init my-review "Evidence for delivery vectors"
paperclip repo
paperclip repo -n 0
paperclip repo info my-review
paperclip repo checkout my-review
paperclip repo deactivate
```

Native CLI checkout is sticky. `checkout NAME` tries a branch of the active repo, then another repo;
`checkout -` also deactivates. Hosted MCP is stateless: supply `--repo NAME` on each call instead of
assuming a prior checkout carries over.

```bash
paperclip --repo my-review search -s pmc "delivery vector" -n 5
paperclip --repo-only search -s pmc "delivery vector" -n 5
paperclip search -s pmc "delivery vector" --corpus -n 5
```

A normal search covers the corpus even with an active repo; the repo can record the command.
`--repo-only` restricts discovery to repo papers. Do not append unrelated papers to a leftover repo.

## Claims and verification

Illustrative placeholders below must be replaced with actual IDs, claims, and observed source lines:

```bash
paperclip repo add DOCUMENT_ID "A claim supported by the source passage" --lines L45-L52
paperclip repo add DOCUMENT_ID
paperclip repo add DOCUMENT_ID --json '{"type":"custom","value":0.42,"unit":"reported unit"}' --lines L88
paperclip repo claims
paperclip repo commit -m "Initial verified extraction"
paperclip repo status
```

Adding a claim appends an entry; membership-only additions are not verified claims. `--json` is a
boolean switch telling the CLI to parse the positional claim as an object with a nonempty string
`type`. It is not a domain-specific scientific schema. A free-text claim is not a poolable effect
estimate: for systematic reviews/meta-analysis inspect
`paperclip routines show paperclip-meta-analysis` before designing the collection.

Commit verifies unresolved claims and creates a metadata snapshot. **It does not always succeed**:
unresolved verifier errors block the snapshot so the command can retry. A generic repo's conclusive
`[X]` verdict is advisory and can coexist with a snapshot; specialized extraction/meta-analysis
compilation requires its own stricter gates. Previously resolved verdicts are not automatically
rechecked. `--no-verify` skips verification and cannot establish support.

Inspect `repo status` before reporting a verified collection. Cite supported claims and verify
primary passages. A claim's `[OK]` does not validate every claim about the same paper, the statistical
analysis, or the generalization to another population.

For targeted repair, remove the selected **claim**, not the whole paper and its other claims:

```bash
paperclip repo remove-claim clm_ID --dry-run --json
paperclip repo remove-claim clm_ID --expected-count 1 --reason "Replace incorrect extracted value"
paperclip repo add DOCUMENT_ID "Corrected claim" --lines L80-L82
paperclip repo commit -m "Correct extraction"
paperclip repo status
```

Check the dry-run targets. `--expected-count` is required for actual claim removal.
`repo remove DOCUMENT_ID` removes the paper and is appropriate only when the paper itself should
leave the collection.

## Branches, history, and export

```bash
paperclip repo branch safety-concerns
paperclip repo checkout main
paperclip repo merge safety-concerns
paperclip repo log
paperclip repo history -p 1 -n 20 --json
paperclip repo export bibtex -o review.bib
paperclip repo export ris -o review.ris
paperclip repo export markdown -o review.md
paperclip repo export csv -o review.csv
paperclip repo citations
```

Branches isolate collection work; merge takes the union of papers. Inspect claims after merging.
History pages are one-based (`-p`) with `-n` rows per page; history is the command trail, while `log`
is the commit trail. Citation counts/graphs are discovery metadata with source coverage and update
limits, not proof of scientific quality. `repo citations --graph` requests relationships.

`repos-feature enable/disable` changes the feature setting. `repo delete` permanently removes a
repo's state; it is not needed for ordinary editing or verification.

## Clipboard and local artifacts

```bash
paperclip cp /papers/PMC10945750 /clipboard/my-review/
paperclip ls /clipboard/my-review/
paperclip search -s clipboard/my-review "delivery vector" -n 5
paperclip upload analysis.json report.md --into analyses/my-topic
```

A corpus link reads through to the original paper. An uploaded PDF is parsed and can have its own
`usr_` identifier; do not assume its line numbers match a corpus copy or a new parsing version.
The current official limits are **200 MB/file, 2,000 pages/PDF, 10,000 documents, and 10 GB total**
per user. PDF is the parsed-document input; JSON/HTML/CSV/MD/PDF can also be stored as artifacts through
`upload`. Treat account/server error messages as authoritative if limits differ.

A local path passed to `cp`, `upload`, `import`, or `sync` sends its content to GXL. Restrict it to
requested files/folders. Hosted MCP cannot read local machine paths through `cp` or `import`; use
the connected upload mechanism rather than pretending a path exists on the server.

## Folder sync

```bash
paperclip sync upload /path/to/papers/
paperclip sync add /path/to/papers/ --prefix my-review
paperclip sync run --dry-run
paperclip sync run
paperclip sync list
paperclip sync status
paperclip sync remove /path/to/papers/
```

Registration enables later synchronization of a folder; `sync run` uploads new/modified PDFs and
can propagate detected local deletions to the remote 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

