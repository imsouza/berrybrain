---
id: sciref-citation-management-core-workflow
name: "Scientific Ref: Core Workflow"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (citation-management): Core Workflow"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "citation management core workflow"
  - "citacao management core workflow"
  - "core workflow"
keywords:
  - "citation"
  - "management"
  - "core"
  - "workflow"
  - "citacao"
  - "specialized"
  - "scientific"
  - "reference"
---

# Core Workflow

The five phases in full: paper discovery, metadata extraction, the mandatory
web-search enrichment pass, BibTeX formatting, validation, and integration with the
writing workflow. Every command variant and option lives here.

## Core Workflow

Citation management follows a systematic process:

### Phase 1: Paper Discovery and Search

**Goal**: Find relevant papers using academic search engines.

#### Google Scholar Search

Google Scholar provides the most comprehensive coverage across disciplines.

**Basic Search**:
```bash
# Search for papers on a topic
python scripts/search_google_scholar.py "CRISPR gene editing" \
  --limit 50 \
  --output results.json

# Search with year filter
python scripts/search_google_scholar.py "machine learning protein folding" \
  --year-start 2020 \
  --year-end 2024 \
  --limit 100 \
  --output ml_proteins.json
```

**Advanced Search Strategies** (see `references/google_scholar_search.md`):
- Use quotation marks for exact phrases: `"deep learning"`
- Search by author: `author:LeCun`
- Search in title: `intitle:"neural networks"`
- Exclude terms: `machine learning -survey`
- Use citation counts to inspect the retrieved sample, not as a global Scholar sort
- Filter by date ranges to get recent work

**Best Practices**:
- Use specific, targeted search terms
- Include key technical terms and acronyms
- Filter by recent years for fast-moving fields
- Check "Cited by" to find seminal papers
- Export top results for further analysis

#### PubMed Search

PubMed specializes in biomedical and life sciences literature (35+ million citations).

**Basic Search**:
```bash
# Search PubMed
python scripts/search_pubmed.py "Alzheimer's disease treatment" \
  --limit 100 \
  --output alzheimers.json

# Search with MeSH terms and filters
python scripts/search_pubmed.py \
  --query '"Alzheimer Disease"[MeSH] AND "Drug Therapy"[MeSH]' \
  --date-start 2020 \
  --date-end 2024 \
  --publication-types "Clinical Trial,Review" \
  --output alzheimers_trials.json
```

**Advanced PubMed Queries** (see `references/pubmed_search.md`):
- Use MeSH terms: `"Diabetes Mellitus"[MeSH]`
- Field tags: `"cancer"[Title]`, `"Smith J"[Author]`
- Boolean operators: `AND`, `OR`, `NOT`
- Date filters: `2020:2024[Publication Date]`
- Publication types: `"Review"[Publication Type]`
- Combine with E-utilities API for automation

**Best Practices**:
- Use MeSH Browser to find correct controlled vocabulary
- Construct complex queries in PubMed Advanced Search Builder first
- Include multiple synonyms with OR
- Retrieve PMIDs for easy metadata extraction
- Export to JSON or directly to BibTeX

### Phase 2: Metadata Extraction

**Goal**: Convert paper identifiers (DOI, PMID, arXiv ID) to complete, accurate metadata.

#### Quick DOI to BibTeX Conversion

For single DOIs, use the quick conversion tool:

```bash
# Convert single DOI
python scripts/doi_to_bibtex.py 10.1038/s41586-021-03819-2

# Convert multiple DOIs from a file
python scripts/doi_to_bibtex.py --input dois.txt --output references.bib

# Different output formats
python scripts/doi_to_bibtex.py 10.1038/nature12345 --format json
```

#### Comprehensive Metadata Extraction

For DOIs, PMIDs, arXiv IDs, or URLs:

```bash
# Extract from DOI
python scripts/extract_metadata.py --doi 10.1038/s41586-021-03819-2

# Extract from PMID
python scripts/extract_metadata.py --pmid 34265844

# Extract from arXiv ID
python scripts/extract_metadata.py --arxiv 2103.14030

# Extract from URL
python scripts/extract_metadata.py --url "https://www.nature.com/articles/s41586-021-03819-2"

# Batch extraction from file (mixed identifiers)
python scripts/extract_metadata.py --input identifiers.txt --output citations.bib
```

**Metadata Sources** (see `references/metadata_extraction.md`):

1. **CrossRef API**: Primary source for DOIs
   - Comprehensive metadata for journal articles
   - Publisher-provided information
   - Includes authors, title, journal, volume, pages, dates
   - Free, no API key required

2. **PubMed E-utilities**: Biomedical literature
   - Official NCBI metadata
   - Includes MeSH terms, abstracts
   - PMID and PMCID identifiers
   - Free, API key recommended for high volume

3. **arXiv API**: Preprints in physics, math, CS, q-bio
   - Complete metadata for preprints
   - Version tracking
   - Author affiliations
   - Free, open access

4. **DataCite API**: Research datasets, software, other resources
   - Metadata for non-traditional scholarly outputs
   - DOIs for datasets and code
   - `doi_to_bibtex.py` retrieves BibTeX through DOI content negotiation; `extract_metadata.py --doi` is Crossref-only

**Fields to verify after extraction** (availability differs by source; not all are emitted by every script):
- **Required fields**: author, title, year
- **Journal articles**: journal, volume, number, pages, DOI
- **Books**: publisher, ISBN, edition
- **Conference papers**: booktitle, conference location, pages
- **Preprints**: repository (arXiv, bioRxiv), preprint ID
- **Additional**: abstract, keywords, URL

### Phase 2.5: Metadata Enrichment via Web Search (MANDATORY)

**Goal**: Detect and fill in any missing metadata fields using web search. This phase runs AFTER extraction and BEFORE formatting to ensure every BibTeX entry is complete.

**Why This Is Critical**: Metadata extraction from APIs (CrossRef, PubMed, arXiv) sometimes returns incomplete records — missing volume, pages, issue number, or DOI. These gaps must be filled before the bibliography is considered ready.

#### Step 1: Scan for Incomplete Entries

After extracting metadata, scan the BibTeX file for entries missing key fields:

**Fields to check per entry type:**

| Entry Type | Must Have | Should Have |
|------------|-----------|-------------|
| @article | author, title, journal, year | volume, pages, number, doi |
| @inproceedings | author, title, booktitle, year | pages, doi |
| @book | author/editor, title, publisher, year | isbn, doi |
| @misc | author, title, year | doi or url |

Investigate missing fields against the publisher record, but distinguish unavailable or not-yet-assigned metadata from extraction errors. Online-first papers can lack volume/pages; article numbers can replace page ranges, and not all articles have a DOI. Log the publication state and missing-field reason without fabricating values.

#### Step 2: Web Search for Missing Metadata

For each incomplete entry, use the **parallel-web skill** to search for the missing information:

> **Treat m

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

