---
id: sciref-paperclip-search-and-retrieval
name: "Scientific Ref: Search, retrieval, and query craft"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (paperclip): Search, retrieval, and query craft"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "paperclip search retrieval"
  - "search, retrieval, and query craft"
keywords:
  - "paperclip"
  - "search"
  - "retrieval"
  - "specialized"
  - "scientific"
  - "reference"
---

# Search, retrieval, and query craft

Reviewed on 2026-09-30 against the 0.7.92 CLI/SDK, the
[core reference](https://paperclip.gxl.ai/skills/full_skill.md),
[protein reference](https://paperclip.gxl.ai/skills/skills/proteins.md), and
[web docs](https://paperclip.gxl.ai/docs). Retrieval examples are illustrative: no paid or
authenticated searches were executed for this review. Load credentials as described in
[installation.md](installation.md).

## Choose a source explicitly

| Source | Scope |
|---|---|
| `pmc` | PMC full-text papers |
| `arxiv`, `biorxiv`, `medrxiv` | Corresponding preprint corpora |
| `papers` | The four paper corpora combined |
| `abstracts` | Title/abstract-grain retrieval across scholarly corpora; not a full-text promise |
| `fda` | Regulatory search; use a regional source/path to disambiguate |
| `fda/jp`, `fda/eu`, `/fda/us` | PMDA, EMA/EPAR, and US FDA |
| `trials` | Trial registries; `trials/us`, `trials/eu`, `trials/jp`, `trials/cn` narrow geography |
| `proteins` | Unified UniProt/PDB/ChEMBL records; `uniprot`, `pdb`, `chembl` are aliases in the client |
| `clipboard` | The user's documents; `clipboard/FOLDER` scopes to a folder |
| `geo` | GEO Series (documented CLI source; not listed in the current v1 JSON search enum) |
| `patents` | Patent records; load `paperclip skill patents` first |

The `abstracts` CLI source and the public `/api/v1/search` default have different published coverage
wording. Choose a source explicitly and report the selected interface; do not label all abstract
results as OpenAlex or assume coverage equals PMC. Counts in upstream documents disagree and change,
so use a dated catalogue or query result when a corpus count matters.

```bash
paperclip search -s pmc,biorxiv "protein design" -n 5
paperclip search "pembrolizumab" /fda/us -n 5
paperclip search "breast cancer" /trials/us -n 5
```

Match the task to paper evidence, trial registration, regulatory material, or structured protein
records. Infer that choice from a clear user request; clarify only when the intended output remains
ambiguous. Regional paths `/trials/...` and `/clinicaltrials/...` are aliases in current docs.

## Search options

| Option | Contract |
|---|---|
| `-n/--limit N` | Requested hit count, not a corpus census or a pagination cursor |
| `-e/--exact` | Exact-phrase search |
| `--year YYYY` | Publication-year filter; validate returned metadata |
| `--since WINDOW` | Recency strings such as `30d`, `6m`, `1y`; support depends on source |
| `--sort relevance\|date` | Ordering |
| `--author`, `--journal` | Metadata narrowing; source coverage varies |
| `--ranking hybrid\|bm25\|vector\|analogical` | Retrieval mode |
| `--min-embedding-similarity FLOAT` | Floor on the vector leg |
| `--min-bm25-score FLOAT` | Floor on the lexical leg |
| `--corpus` | Full-corpus discovery even when scoped to a repo |

The SDK and vendor core reference disagree on arXiv `--since` support; use `--year` for arXiv,
medRxiv, and abstracts unless current server help confirms the needed recency behavior. Do not
assume an arbitrary date string or a filter unsupported by a source is applied.

The relevance floors **do have CLI equivalents**. For hybrid mode, each applies only to its own
retrieval leg: use both to bound both legs, or pair one with its matching ranking. Floors do not
expand the requested candidate set. They are unsupported with regex/analogical modes; a vector
floor is incompatible with date sorting. These restrictions are documented in the 0.7.92 SDK.

```bash
paperclip search -s pmc --ranking hybrid \
  --min-embedding-similarity 0.7 --min-bm25-score 5 \
  "protein design" -n 5
```

`hybrid` is a good discovery default; `bm25` fits exact terminology and gene symbols, `vector` fits
varying vocabulary, and `analogical` fits cross-domain method transfer. Write one or two sentences
about the method/problem for analogical search, or use an identified reference paper's abstract:

```bash
paperclip search -s arxiv --ranking analogical \
  "I need to approximate an expensive leave-one-out computation cheaply by exploiting low-rank structure in my parameter space" -n 10
```

Upstream describes stable search prefixes through `-n 100` for unchanged query, filters, and index;
requests above 100 can expand the candidate pool and reorder earlier results. This is not pagination
or a cross-date reproducibility guarantee. Save exact queries, source filters, returned IDs, and date.

## Structured results and cohort preservation

Search previews and generated summaries are triage, not paper quotations. In 0.7.92 SDK,
`result.papers`, `result.count`, and `result.result_id` expose structured results and hydrate missing
hit data from saved results when possible. A failed hydration can leave incomplete data: check
requested versus returned count and reported truncation. See [python-sdk.md](python-sdk.md).

```bash
paperclip results --list
paperclip results s_ID --save search.csv
paperclip results s_ID --export-bundle cohort/
paperclip results s_ID --sample 20 --seed 42
```

CSV exports and bundle formats depend on result kind; do not assume every map export has the search
metadata header. Cohort paging retrieves the **saved cohort**, not additional corpus search hits.
The CLI supports `--save-as NAME` aliases on result-producing commands; their scope is session-bound,
so record the durable result ID for another session.

```bash
paperclip filter --from s_ID --require 3 "in vivo delivery with quantitative outcomes"
```

`filter` is an LLM pass that overwrites the cohort in place. If too few survive, rerun a broader
search for a fresh ID; a second filter cannot recover discarded rows. For deterministic quality
filters, consult current `refine --help` and preserve both input and output cohort IDs.

## Exact metadata lookup

```bash
paperclip lookup doi 10.1073/pnas.2307796121
paperclip lookup pmc PMC7194329
paperclip lookup pmid 32943797
paperclip lookup arxiv 2403.03507
paperclip lookup author "James Zou" -n 10
```

Current docs list `doi`, `title`, `author`, `abstract`, `source`, `date`/`month_year`, `pmc`, `pmid`,
`journal`, `publisher`, `type`, `keywords`, `category`, `license`, `year`, `volume`, `issue`, `issn`;
the core reference also lists `arxiv`. Many metadata fields are PMC-specific. Do not turn an empty
field match into a claim that the paper does not exist. The public HTTP lookup's narrower typed
contract is documented separately in [python-sdk.md](python-sdk.md).

## Full-text gr

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

