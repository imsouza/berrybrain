---
id: sciref-citation-management-metadata-extraction
name: "Scientific Ref: Metadata Extraction Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (citation-management): Metadata Extraction Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "citation management metadata extraction"
  - "citacao management metadata extraction"
  - "metadata extraction guide"
keywords:
  - "citation"
  - "management"
  - "metadata"
  - "extraction"
  - "citacao"
  - "specialized"
  - "scientific"
  - "reference"
---

# Metadata Extraction Guide

Comprehensive guide to extracting accurate citation metadata from DOIs, PMIDs, arXiv IDs, and URLs using various APIs and services.

## Overview

Accurate metadata is essential for proper citations. This guide covers:
- Identifying paper identifiers (DOI, PMID, arXiv ID)
- Querying metadata APIs (CrossRef, PubMed, arXiv, DataCite)
- Required BibTeX fields by entry type
- Handling edge cases and special situations
- Validating extracted metadata

## Paper Identifiers

### DOI (Digital Object Identifier)

**Format**: `10.XXXX/suffix`

**Examples**:
```
10.1038/s41586-021-03819-2    # Nature article
10.1126/science.aam9317       # Science article
10.1016/j.cell.2023.01.001    # Cell article
10.1371/journal.pone.0123456  # PLOS ONE article
```

**Properties**:
- Permanent identifier
- Most reliable for metadata
- Resolves to current location
- Publisher-assigned

**Where to find**:
- First page of article
- Article webpage
- CrossRef, Google Scholar, PubMed
- Usually prominent on publisher site

### PMID (PubMed ID)

**Format**: 8-digit number (typically)

**Examples**:
```
34265844
28445112
35476778
```

**Properties**:
- Specific to PubMed database
- Biomedical literature only
- Assigned by NCBI
- Permanent identifier

**Where to find**:
- PubMed search results
- Article page on PubMed
- Often in article PDF footer
- PMC (PubMed Central) pages

### PMCID (PubMed Central ID)

**Format**: PMC followed by numbers

**Examples**:
```
PMC8287551
PMC7456789
```

**Properties**:
- Free full-text articles in PMC
- Subset of PubMed articles
- Open access or author manuscripts

### arXiv ID

**Format**: YYMM.NNNNN or archive/YYMMNNN

**Examples**:
```
2103.14030        # New format (since 2007)
2401.12345        # 2024 submission
arXiv:hep-th/9901001  # Old format
```

**Properties**:
- Preprints (not peer-reviewed)
- Physics, math, CS, q-bio, etc.
- Version tracking (v1, v2, etc.)
- Free, open access

**Where to find**:
- arXiv.org
- Often cited before publication
- Paper PDF header

### Other Identifiers

**ISBN** (Books):
```
978-0-12-345678-9
0-123-45678-9
```

**arXiv category**:
```
cs.LG    # Computer Science - Machine Learning
q-bio.QM # Quantitative Biology - Quantitative Methods
math.ST  # Mathematics - Statistics
```

## Metadata APIs

### CrossRef API

**Primary source for DOIs** - Most comprehensive metadata for journal articles.

**Base URL**: `https://api.crossref.org/works/`

**No API key required**. Identify your application with `User-Agent`; add your
own contact email as `mailto` for the polite pool. Single-record requests are
limited to 5/s public or 10/s polite; list queries to 1/s or 3/s respectively.
Read response rate/concurrency headers and back off on 429. See the current
[Crossref limits](https://community.crossref.org/t/refining-rest-api-limits-for-improved-stability-and-reliability/16137).

#### Basic DOI Lookup

**Request**:
```
GET https://api.crossref.org/works/10.1038/s41586-021-03819-2
```

**Response** (simplified):
```json
{
  "message": {
    "DOI": "10.1038/s41586-021-03819-2",
    "title": ["Article title here"],
    "author": [
      {"given": "John", "family": "Smith"},
      {"given": "Jane", "family": "Doe"}
    ],
    "container-title": ["Nature"],
    "volume": "595",
    "issue": "7865",
    "page": "123-128",
    "published-print": {"date-parts": [[2021, 7, 1]]},
    "publisher": "Springer Nature",
    "type": "journal-article",
    "ISSN": ["0028-0836"]
  }
}
```

#### Fields Available

**Identity/type fields**:
- `DOI`: Digital Object Identifier
- `title`: Article title (array; may be absent or empty)
- `type`: Content type (journal-article, book-chapter, etc.)

**Usually present**:
- `author`: Array of author objects
- `container-title`: Journal/book title
- `published-print`, `published-online`, `published`, or `issued`: Publication date (do not substitute registration/deposit dates)
- `volume`, `issue`, `page`: Publication details
- `publisher`: Publisher name

**Sometimes present**:
- `abstract`: Article abstract
- `subject`: Subject categories
- `ISSN`: Journal ISSN
- `ISBN`: Book ISBN
- `reference`: Reference list
- `is-referenced-by-count`: Citation count

#### Content Types

CrossRef `type` field values:
- `journal-article`: Journal articles
- `book-chapter`: Book chapters
- `book`: Books
- `proceedings-article`: Conference papers
- `posted-content`: Preprints
- `dataset`: Research datasets
- `report`: Technical reports
- `dissertation`: Theses/dissertations

### PubMed E-utilities API

**Specialized for biomedical literature** - Curated metadata with MeSH terms.

**Base URL**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`

**API key recommended** (free):
- Higher rate limits
- Better performance

#### PMID to Metadata

**Step 1: EFetch for full record**

```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?
  db=pubmed&
  id=34265844&
  retmode=xml&
  api_key=YOUR_KEY
```

**Response**: XML with comprehensive metadata

**Step 2: Parse XML**

Key fields:
```xml
<PubmedArticle>
  <MedlineCitation>
    <PMID>34265844</PMID>
    <Article>
      <ArticleTitle>Title here</ArticleTitle>
      <AuthorList>
        <Author><LastName>Smith</LastName><ForeName>John</ForeName></Author>
      </AuthorList>
      <Journal>
        <Title>Nature</Title>
        <JournalIssue>
          <Volume>595</Volume>
          <Issue>7865</Issue>
          <PubDate><Year>2021</Year></PubDate>
        </JournalIssue>
      </Journal>
      <Pagination><MedlinePgn>123-128</MedlinePgn></Pagination>
      <Abstract><AbstractText>Abstract text here</AbstractText></Abstract>
    </Article>
  </MedlineCitation>
  <PubmedData>
    <ArticleIdList>
      <ArticleId IdType="doi">10.1038/s41586-021-03819-2</ArticleId>
      <ArticleId IdType="pmc">PMC8287551</ArticleId>
    </ArticleIdList>
  </PubmedData>
</PubmedArticle>
```

#### Unique PubMed Fields

**MeSH Terms**: Controlled vocabulary
```xml
<MeshHeadingList>
  <MeshHeading>
    <DescriptorName UI="D003920">Diabetes Mellitus</DescriptorName>
  </MeshHeading>
</MeshHeadingList>
```

**Publication Types**:
```xml
<PublicationTypeList>
  <PublicationType UI="D016428">Journal Article</PublicationType>
  <PublicationType UI="D016449">Randomized Controlled Trial</PublicationType>
</PublicationTypeList>
```

**Grant Information**:
```xml
<GrantList>
  <Grant>
    <GrantID>R01-123456</GrantID>
    <Agency>NIAID NIH HHS</Agency>
    <Country>United States</Country>
  </Grant>
</

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

