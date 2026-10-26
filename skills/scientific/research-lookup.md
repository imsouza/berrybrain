---
id: sci-research-lookup
name: "Scientific: research-lookup"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Compiles current scholarly evidence for a scientific manuscript or research brief when the user explicitly asks to gather literature, references, background evidence, competing findings, or a manuscript research packet. Uses Parallel Search by default, Parallel Extract for source"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "research lookup"
  - "pesquisa lookup"
  - "research-lookup"
keywords:
  - "research"
  - "lookup"
  - "pesquisa"
  - "compiles"
  - "current"
  - "scholarly"
  - "evidence"
  - "scientific"
  - "manuscript"
---

# Research Lookup

Compile the external evidence needed to plan and write a high-quality scientific
manuscript. The default academic workflow targets **60 verified, unique references**
and produces a manuscript-ready research packet rather than a loose list of links.
Here `verified_references` counts successful retrieval of nonempty Extract excerpts,
excluding flagged retractions. It does not establish bibliographic identity, claim
support, peer review, or absence of corrections; those require source review.

## Scope and boundaries

Use this skill when the user explicitly wants:

- literature and background research for a manuscript
- many high-quality academic references
- evidence supporting or contradicting a scientific claim
- a structured evidence matrix or claim-to-source map
- current studies, methods precedent, mechanisms, limitations, or research gaps

Do not activate it for casual factual questions that do not need research, private
or unpublished material, or a claim that can be answered from user-provided files.
Query text is sent to Parallel. It is sent to OpenRouter only when Perplexity is
explicitly selected or the user enables that fallback.

This skill compiles **external evidence**. It cannot supply the user's unpublished
study data, decide what their Results show, or guarantee systematic-review
completeness. For a PRISMA-style systematic review, use `literature-review` for
protocols, database-specific searching, screening, exclusion reasons, and risk of
bias.

## Parallel-first routing

| Need | Backend | Selection |
|---|---|---|
| Manuscript literature and references | Parallel Search + Extract | Default; use `--academic` |
| Fast bounded web lookup | Parallel Search | Use `--no-academic` |
| Deep/exhaustive multi-source report | Parallel Research | Explicit `--force-backend research` |
| OpenAI-compatible synthesis with research basis | Parallel Chat | Explicit `--force-backend chat` |
| Optional alternative academic search | Perplexity via OpenRouter | Explicit or enabled failure fallback |

Important compatibility behavior:

- A bare script query uses **Parallel Search**. Chat Completions remains available
  only through explicit backend selection.
- `--force-backend parallel` remains an alias for explicit Parallel Research.
- Academic keywords select the multi-pass Parallel academic strategy; they do not
  silently switch the provider to Perplexity.
- `--batch`, `--json`, `-o/--output`, the `ResearchLookup` class, progress output,
  and the existing result envelope remain supported.

## Recommended manuscript workflow

### 1. Capture manuscript context

Use the user's available context to constrain retrieval:

- research question or hypothesis
- study type
- population or biological/technical system
- intervention or exposure
- comparator
- outcomes
- field and date range
- target journal, if known

The script accepts a JSON object through `--context-file`. Do not invent missing
study details. A bare topic is supported, but the packet will flag its section briefs
as broad.

Example:

```json
{
  "research_question": "How does intervention X affect outcome Y?",
  "study_type": "prospective cohort",
  "population": "adults with condition Z",
  "exposure": "intervention X",
  "comparator": "standard care",
  "outcomes": ["primary outcome Y", "adverse events"],
  "field": "clinical epidemiology",
  "target_journal": "Journal Name"
}
```

### 2. Run the academic evidence pipeline

From the repository root (illustrative paid-service run; review its scope first):

```bash
python skills/research-lookup/scripts/research_lookup.py \
  "Evidence relevant to the manuscript's research question" \
  --academic \
  --target-references 60 \
  --context-file manuscript-context.json \
  --packet-dir sources/manuscript-research \
  --json
```

The academic pipeline runs bounded `advanced` Search passes for:

1. recent peer-reviewed primary studies
2. systematic reviews, meta-analyses, and consensus evidence
3. seminal and foundational publications
4. methods, protocols, validation, benchmarks, and mechanisms
5. contradictory, null, negative, replication, and limitation evidence
6. an unrestricted companion search when filtered passes do not reach the target

It prioritizes PubMed/PMC, Europe PMC, Crossref, OpenAlex, Semantic Scholar,
arXiv/bioRxiv/medRxiv, major journals, and authoritative institutional sources.
Domain filters are not treated as exhaustive; the companion pass reduces blind spots.

### 3. Verify promising sources with Parallel Extract

Search candidates are deduplicated and ranked before batched extraction. Extraction
requests source-supported:

- authors, year, venue, DOI, and PMID
- publication and study design
- population/system and sample size
- methods, intervention/exposure, comparator, and outcomes
- quantitative findings, uncertainty, and statistical values
- limitations and conclusions
- preprint, correction, retraction, or withdrawal status

The default extraction limit equals `--target-references`. Use `--extract-limit N`
to reduce cost or `--no-extract` only when unverified search results are acceptable.
The coverage report will not count search-only records as verified, even when they
contain a DOI or PMID. Successful extraction is only a retrieval check: inspect each
excerpt against the proposed claim, confirm bibliographic identity, and verify
correction/retraction status at the publisher or authoritative index. Batched Extract
can return both `results` and per-URL `errors`. The ledger preserves errors, warnings,
and unresolved URLs, including empty responses or redirects requiring reconciliation.
Only the successfully extracted excerpts become retrieved evidence; candidate search
snippets remain in the raw response audit trail.

### 4. Review the manuscript research packet

`--packet-dir` writes:

- `packet.json` and `packet.md` — complete machine/human packet
- `references.json` and `references.bib` — citation-ready records
- `evidence-matrix.json` — structured study evidence
- `claim-source-map.json` — proposed claims linked to source excerpts
- `synthesis.json` — consensus candidates, conflicts, methods patterns, and gaps
- `section-briefs.json` — Introduction, Methods-rationale, and Discussion evidence
- `coverage.json` — target shortfall, quality mix, dates, source mix, and limitations
- `search-ledger.json` — exact objectives, filters, timestamps, counts, and IDs

Raw Parallel responses remain in `packet.json` for auditability. Trea

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

