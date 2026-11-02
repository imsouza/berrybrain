---
id: sci-paperclip
name: "Scientific: paperclip"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Searches and reads biomedical papers, FDA/PMDA/EMA documents, clinical trials, and protein records with the GXL Paperclip CLI and Python SDK. Supports source-scoped search, full-text grep, metadata SQL, map/reduce extraction, figure analysis, optional repositories and claim verif"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "paperclip"
keywords:
  - "paperclip"
  - "searches"
  - "reads"
  - "biomedical"
  - "papers"
  - "pmda"
  - "documents"
---

# Paperclip CLI

Paperclip by GXL exposes scientific documents through a virtual filesystem and server-side search
and readers. This is **GXL Paperclip** at `paperclip.gxl.ai`, not the unrelated Paperclip agent-company
application. Use the source requested by the user; other providers have their own skills.

This revision checks official docs, the public API schema, and installed CLI/SDK **0.7.92**.
Local help, SDK request construction, and public metadata were checked. Authenticated retrieval,
LLM readers, uploads, and repository mutations were not run during this review; their examples
are illustrative. Server behavior can change independently of the CLI version.

## Preflight and authentication

```bash
command -v paperclip
paperclip --version
paperclip --help
```

If installed, use the existing account or a key configured privately at
`https://paperclip.gxl.ai/keys`. Do not ask for a key in chat or print credential files.
Paperclip does not automatically load a project `.env`. If the user has supplied a **trusted,
shell-compatible** `.env`, export it in the same shell invocation as the command:

```bash
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi
paperclip config 2>&1 | grep -E 'Auth:|Health:'
```

Sourcing `.env` executes shell code: use only a trusted file, and keep it out of Git. Repeat the
export when a tool starts a fresh shell; an already-exported environment needs no prefix. A bearer
token can take precedence over an API key, and absent environment credentials may fall back to a
stored OAuth identity. Check the intended account rather than assuming any OAuth login is wrong.
`Auth` reports credential presence; `Health` probes public reachability. Neither proves the
credential is valid. Check authentication on the next task-authorized request.

Use browser `paperclip login` when the user is available to complete sign-in. Installation and
`paperclip install` also contain prompts; see [installation.md](references/installation.md).
Do not run update, uninstall, account changes, or uploads merely to test documentation.

## Choose the retrieval operation

| Goal | Command | Interpretation |
|---|---|---|
| Papers about a topic | `search -s pmc "..." -n 5` | Ranked discovery; summaries are triage |
| Exact terms in full text | `grep "TP53" /papers/` | May be time- or match-limited |
| Known DOI/PMID | `lookup doi 10.1073/pnas.2307796121` | Resolve identity before reading |
| Counts and metadata | `sql "SELECT ..."` | Metadata aggregation, not body-text search |
| Methodological analogues | `search -s arxiv --ranking analogical "..."` | Describe the method or problem in full sentences |
| The same fields across papers | `map --from s_ID "..."` | LLM extraction; verify material evidence |

Always pass a source or virtual directory to `search`. Comma-separated sources work, but separate
targeted queries are easier to interpret when mixing papers, trials, and regulatory evidence.
Use `paperclip skill proteins` before protein queries and `paperclip skill patents` before patents.

## Find, read, and cite

```bash
paperclip search -s pmc "CRISPR base editing delivery" -n 5
paperclip cat /papers/PMC10945750/meta.json
paperclip head -40 /papers/PMC10945750/content.lines
paperclip ls /papers/PMC10945750/sections/
paperclip grep -n "lipid nanoparticle" /papers/PMC10945750/content.lines
paperclip scan /papers/PMC10945750/content.lines "IC50" "off-target" "efficiency"
```

Capture the returned result ID; do not reuse the illustrative IDs in this skill. `s_` IDs identify
saved search/grep/filter cohorts, `m_` map runs, and `r_` reduce artifacts. Recover recent IDs with
`paperclip results --list`. Terminal output can be a truncated preview, so use saved results or
SDK `result.papers` for structured hits, not a regex over rendered paper titles. See
[search-and-retrieval.md](references/search-and-retrieval.md) and
[python-sdk.md](references/python-sdk.md).

Use absolute virtual paths. Prefer `head`, sections, `grep`, and `scan` to dumping a whole paper.
A failed read or empty, bounded grep result does not establish scientific absence.

### Multi-paper extraction

```bash
paperclip search -s pmc "lipid nanoparticle mRNA delivery" -n 5
# Substitute the actual search ID below.
paperclip filter --from s_ID "in vivo delivery with quantified efficiency"
paperclip map --from s_ID "Report delivery vector, target cell type, efficiency, and supporting lines. State 'not reported' when absent."
paperclip results m_ID --save map.txt
```

`filter` modifies its saved cohort in place. Save the original search separately if it must remain
reproducible. Start with 3–10 papers; readers incur service work and quota. Use Draft 2020-12 JSON
Schema through `--output-schema` when exact fields matter. For a persistent Paperclip extraction
dataset, inspect `paperclip routines show paperclip-data-extraction` and the current extraction
workflow before creating it. A returned routine does not authorize extra persistence or sharing.

`reduce --from m_ID --strategy table "Compare the results"` requests a table, but validate the actual
output and construct the final table from verified map results when necessary. Map/reduce are LLM
outputs, not primary evidence. Read the relevant source lines for material quantitative claims and
quotes; verify document IDs and line pins rather than trusting generated citation markers.
See [map-reduce.md](references/map-reduce.md).

### Regulatory, trial, and figure reads

```bash
paperclip search -s fda "pembrolizumab accelerated approval" -n 5
paperclip search -s trials/us "HER2 breast cancer trastuzumab deruxtecan" -n 5
paperclip cat /trials/NCT04752059/meta.json
paperclip ls /papers/PMC10945750/figures/
# Use the actual filename returned by ls.
paperclip ask-image /papers/PMC10945750/figures/pnas.2307796121fig01.jpg "What is plotted on each axis?"
```

Figure names are publisher-specific. Vision-derived numbers are estimates; prefer reported text
or supplementary data. Do not obtain image bytes with `cat` redirected to a local image file:
the SDK transport is textual, and `pull()` does not itself write binary data to disk.

## Virtual filesystem

```text
/papers/        PMC, arXiv, bioRxiv, medRxiv
/fda/           us/, jp/ (PMDA), eu/ (EMA/EPAR)
/trials/        us/, cn/, jp/, eu/, intl/; /clinicaltrials/ is an alias
/proteins/      UniProt, PDB, ChEMBL, addressed by UniProt accession
/geo/           GEO Series; inspect current domain instructions before querying
/patents/      

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

