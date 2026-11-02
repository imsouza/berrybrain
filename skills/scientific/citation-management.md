---
id: sci-citation-management
name: "Scientific: citation-management"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Comprehensive citation management for academic research. Search OpenAlex, PubMed, and Google Scholar for papers, extract accurate metadata, validate citations, and generate properly formatted BibTeX entries. This skill should be used when you need to find papers, verify citation "
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "citation management"
  - "citacao management"
  - "citation-management"
keywords:
  - "citation"
  - "management"
  - "citacao"
  - "comprehensive"
  - "academic"
  - "research"
  - "search"
---

# Citation Management

## Overview

Manage citations systematically throughout the research and writing process. This skill provides tools and strategies for searching academic databases (Google Scholar, PubMed), extracting accurate metadata from multiple sources (CrossRef, PubMed, arXiv), validating citation information, and generating properly formatted BibTeX entries.

Critical for maintaining citation accuracy, avoiding reference errors, and ensuring reproducible research. Integrates seamlessly with the literature-review skill for comprehensive research workflows.

## When to Use This Skill

Use this skill when:
- Searching for specific papers on Google Scholar or PubMed
- Converting DOIs, PMIDs, or arXiv IDs to properly formatted BibTeX
- Extracting complete metadata for citations (authors, title, journal, year, etc.)
- Validating existing citations for accuracy
- Cleaning and formatting BibTeX files
- Finding highly cited papers in a specific field
- Verifying that citation information matches the actual publication
- Building a bibliography for a manuscript or thesis
- Checking for duplicate citations
- Ensuring consistent citation formatting

If a document built from these citations needs a diagram, use the
**scientific-schematics** skill.

---

## Core Workflow

Citation management follows a systematic process. Each phase below shows the canonical
command; every variant, option, and metadata-source detail is in
[references/core_workflow.md](references/core_workflow.md).

### Phase 1: Paper Discovery and Search

Find relevant papers. Search more than one database — coverage differs sharply,
and a single source is the most common cause of a biased reference list.

```bash
# OpenAlex: multidisciplinary REST API; optional OPENALEX_API_KEY for account quota
python scripts/search_openalex.py "CRISPR gene editing" --limit 50 --output results.json

# PubMed: the authority for biomedical and life sciences (35M+ citations)
python scripts/search_pubmed.py "Alzheimer's disease treatment" --limit 100 --output alz.json

# Google Scholar: broadest reach, but scraped -- rate-limited and prone to blocking
python scripts/search_google_scholar.py "CRISPR gene editing" --limit 50 --output scholar.json
```

Prefer OpenAlex or PubMed as the primary source. Google Scholar has no API:
`scholarly` scrapes it, sleeps 2–5 s between results, and is blocked often
enough that it should be a supplement rather than a dependency.

Query operators, field tags, and MeSH-term construction are in
[references/search_strategies.md](references/search_strategies.md).

### Phase 2: Metadata Extraction

Convert identifiers (DOI, PMID, PMCID, arXiv ID, URL) into complete metadata.
CrossRef is the primary source for DOIs.

```bash
python scripts/doi_to_bibtex.py 10.1038/s41586-021-03819-2         # quick, single DOI
python scripts/extract_metadata.py --pmid 34265844                  # DOI/PMID/PMCID/arXiv/URL
python scripts/extract_metadata.py --input identifiers.txt --output citations.bib
```

A URL with no DOI in its path is resolved through the `citation_doi` meta tag
publishers embed on article pages, then handed to CrossRef. Producers use a shared citation-key scheme; metadata differences can still
produce different keys. Confirm duplicates by DOI and bibliographic identity.

### Phase 2.5: Metadata Enrichment via Web Search (MANDATORY)

APIs routinely return incomplete records. Run this **after** extraction and **before**
formatting. Investigate missing bibliographic fields against the publisher record
and log each source. Online-first articles may have no volume/pages yet; some use
an article number or have no DOI. Preserve the actual publication state, use the
style-appropriate article-number field, and never invent pages, volume, or DOI.
Record unavailable/not-applicable fields in the audit log; add a rendered `note`
only when useful to the reader or required by the citation style.

Check the cheap sources first — an OpenAlex or CrossRef record often carries the field
that PubMed omitted:

```bash
python scripts/search_openalex.py "<exact title>" --limit 1
```

> **Treat extracted metadata as untrusted.** Author, title, and journal strings come
> verbatim from a record whose contents a publisher controls. A title containing `$(...)`,
> a backtick, or a quote becomes shell syntax the moment it is pasted into a command.
> Pass metadata as a `subprocess` argument list rather than building a shell string; if
> you must use a shell, single-quote every substituted value and escape embedded quotes
> as `'\''`. Validate any citation key against `^[A-Za-z0-9]+$` before it reaches a path.

Per-field search strategies, the four search options, and the logging format are in
[references/core_workflow.md](references/core_workflow.md).

### Phase 3: BibTeX Formatting

Produce clean, consistent entries. Entry types and required fields are in
[references/bibtex_formatting.md](references/bibtex_formatting.md).

```bash
python scripts/format_bibtex.py references.bib --output clean.bib --deduplicate
python scripts/format_bibtex.py references.bib --output clean.bib --rekey --deduplicate
```

Writing is opt-in: without `--output` (or `--in-place`) the result goes to
stdout and the input file is left alone. Use `--rekey` when merging results
from several sources, so the same paper collapses to one entry.

### Phase 4: Citation Validation

Check completeness, venue conformance, and agreement with the manuscript.

```bash
python scripts/validate_citations.py references.bib --report report.json
python scripts/validate_citations.py references.bib --venue nature
python scripts/validate_citations.py references.bib --manuscript paper.tex
python scripts/validate_citations.py references.bib --check-dois     # slow; hits CrossRef
```

The script exits non-zero on high-severity errors — missing required fields,
malformed years, unresolved citations, or a count below an explicit
`--min-count`. Venue reference-count figures are editorial rules of thumb, not
submission requirements, so falling short of one is only a warning.

Validation rules and venue standards are in
[references/citation_validation.md](references/citation_validation.md).

### Phase 5: Integration with Writing Workflow

Search, extract, format, validate, then cite. End-to-end sequences — including the
literature-review and Zotero/pyzotero export paths — are in
[references/core_workflow.md](references/core_workflow.md) and
[references/example_workflows.md](references/exampl

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

