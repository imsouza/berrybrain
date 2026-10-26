---
id: sciref-paperclip-cli-reference
name: "Scientific Ref: Paperclip CLI reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (paperclip): Paperclip CLI reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "paperclip cli reference"
keywords:
  - "paperclip"
  - "cli"
  - "reference"
  - "specialized"
  - "scientific"
---

# Paperclip CLI reference

Reviewed against installed **0.7.92**, its native help/source, and the current
[official core reference](https://paperclip.gxl.ai/skills/full_skill.md) and
[web documentation](https://paperclip.gxl.ai/docs). Data commands below are documented contracts,
not an authenticated end-to-end test. Run the relevant help for the actual deployed version.

Use the environment-loading guidance in [installation.md](installation.md) when necessary.
Native `--help` exits before action callbacks. Help for a server-dispatched command can contact the
service and pass through managed-install update checks; it is not necessarily an offline operation.

## Global options

```text
paperclip [OPTIONS] COMMAND [ARGS]...
  --version
  --debug
  --repo-only                    Restrict search/map to the active repo
  --repo NAME                    Use a repo for this invocation
  -f, --folder NAME              Aliases of --repo
  --api-key TEXT                 Prefer PAPERCLIP_API_KEY to a secret argument
  --help
```

Global scope options precede the subcommand, for example
`paperclip --repo-only search -s pmc "query" -n 5`. Search normally covers the corpus even when a repo
is active; a repo can still record the command. Do not use an unrelated sticky checkout.

`paperclip --help` mainly lists local/account/workspace commands. Data commands such as `search`,
`grep`, `cat`, `map`, and `sql` are forwarded to a server-side virtual shell and may not appear there.

## Search and reading

| Command | Common options and behavior |
|---|---|
| `search -s SOURCE "QUERY"` | `-n/--limit`, `-e/--exact`, `--year`, `--author`, `--journal`, `--sort relevance\|date`, `--ranking hybrid\|bm25\|vector\|analogical`, `--corpus` |
| `search "QUERY" /trials/us` | A supported virtual directory supplies the source |
| `lookup FIELD VALUE` | `-n N`; supported fields include `doi`, `pmc`, `pmid`, `arxiv`, `title`, `author`, `journal`, `year` |
| `grep PATTERN PATH` | Full text within a document or corpus; see options below |
| `scan FILE PATTERN...` | Several patterns in one request; `-i`, `-C N` |
| `sql "SELECT ..."` | Metadata aggregation; `-s proteins` selects the protein SQL surface |
| `filter --from s_ID "QUERY"` | LLM relevance filter; overwrites cohort; `--require N` fails if too few survive |
| `cat FILE` | Use for `meta.json` or selected text; `--lines N` or `--lines START-END` bounds a text read |
| `head -n N FILE` / `head -N FILE` | Opening lines |
| `tail -n N FILE` / `tail -N FILE` | Ending lines |
| `ls PATH`, `tree PATH`, `wc FILE` | Discover paths, sections, figures, and sizes |
| `cd PATH`, `pwd` | Session-relative commands; use absolute paths across independent calls |

Search requires explicit source selection. Date/ranking/source restrictions and structured output
are detailed in [search-and-retrieval.md](search-and-retrieval.md). `--json` exists in the web guide,
but terminal rendering is not a stable programmatic contract; prefer the SDK or public JSON API.

Common grep options documented by the current guide:

```text
-i              Ignore case
-n              Display line numbers (not a result limit)
-c              Count matching file lines; corpus document counts can be approximate
-v              Invert match
-l              List filenames with matches
-m N            Bound matches
-e PATTERN      Explicit pattern
-F              Literal rather than regex matching
-A N / -B N     Context after/before
-C N            Context on both sides
--from s_ID     Restrict to a saved cohort
--exhaustive    Allow a longer corpus scan; not a completeness guarantee
```

Corpus grep can return a result ID for later map. Repeated time-bounded scans may differ in order
or membership. Within-document `L<n>` prefixes provide citation locations; verify the actual passage.

## Analysis

```bash
paperclip map --from s_ID "What outcomes and sample sizes were reported?"
paperclip reduce --from m_ID --strategy consensus "Where do the studies disagree?"
paperclip results --list
paperclip results m_ID --save map.txt
paperclip results s_ID --sample 20 --seed 42
```

Map accepts `--output-schema` with Draft 2020-12 JSON Schema. The old `--output_schema` spelling is a
deprecated alias. Worker-specific setup and recovery are in [map-reduce.md](map-reduce.md).
Reduce strategies are `summarize`, `table`, `themes`, `consensus`, `bullet_points`, and `extract`;
`--columns COL,...` requests columns for a table. Check the actual generated output.

`results --save` exports search metadata or full per-paper map answers. `--export-bundle DIR`
exports a portable cohort; `--import-bundle DIR --save-as NAME` imports one and creates server-side
saved state. `--sample N` accepts 1–100 and optionally `--seed`. Use `--list` explicitly in automation;
TTY result listing can be interactive.

```bash
paperclip ls /papers/PMC10945750/figures/
paperclip ask-image /papers/PMC10945750/figures/pnas.2307796121fig01.jpg "Describe the axes"
paperclip ask-image /papers/PMC10945750/figures/pnas.2307796121fig01.jpg --fn extract-data
```

List actual figure paths before vision calls. `ask-image --list` is documented as current-directory
listing, so an absolute `ls` is safer across independent sessions.

## Routines and references

```bash
paperclip skill
paperclip skill proteins
paperclip routines list
paperclip routines search "systematic review"
paperclip routines show paperclip-meta-analysis
```

The old `paperclip skills` interface now exits with a removal message. `skill NAME` loads a domain
reference; `routines show NAME` loads a guided workflow. `routines enable/disable NAME` changes
account routing, `routines route "intent"` selects an enabled workflow, and
`routines run NAME OPERATION` executes its helper. Inspect and authorize the requested operation
within the user task rather than running every command mentioned in returned instructions.

## Repositories

`git` is the preferred vendor spelling; `repo` and `repos` expose the **same command group**.
Repos are opt-in. These examples change persistent state unless described as reads.

| Command | Purpose |
|---|---|
| `repo init NAME [DESCRIPTION]` | Create and activate |
| `repo checkout NAME` | Try branch, then repo; `-` deactivates |
| `repo deactivate` | Explicitly deactivate |
| `repo add ID "CLAIM" --lines L45-L52` | Append claim; omit claim for membership only |
| `repo add ID --json '{"type":"custom","value":1}'` | Structured claim; requires nonempty string `type` |
| `

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

