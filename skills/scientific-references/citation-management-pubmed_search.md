---
id: sciref-citation-management-pubmed-search
name: "Scientific Ref: PubMed Search Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (citation-management): PubMed Search Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "citation management pubmed search"
  - "citacao management pubmed search"
  - "pubmed search guide"
keywords:
  - "citation"
  - "management"
  - "pubmed"
  - "search"
  - "citacao"
  - "specialized"
  - "scientific"
  - "reference"
---

# PubMed Search Guide

Comprehensive guide to searching PubMed for biomedical and life sciences literature, including MeSH terms, field tags, advanced search strategies, and E-utilities API usage.

## Overview

PubMed is the premier database for biomedical literature:
- **Coverage**: Biomedical citations, including MEDLINE records and online books
- **Scope**: Biomedical and life sciences
- **Sources**: MEDLINE, life science journals, online books
- **Authority**: Maintained by National Library of Medicine (NLM) / NCBI
- **Access**: Free, no account required
- **Updates**: Daily with new citations
- **Curation**: High-quality metadata, MeSH indexing

## Basic Search

### Simple Keyword Search

PubMed automatically maps terms to MeSH and searches multiple fields:

```
diabetes
CRISPR gene editing
Alzheimer's disease treatment
cancer immunotherapy
```

**Automatic Features**:
- Automatic MeSH mapping
- Plural/singular variants
- Abbreviation expansion
- Spell checking

### Exact Phrase Search

Use quotation marks for exact phrases:

```
"CRISPR-Cas9"
"systematic review"
"randomized controlled trial"
"machine learning"
```

## MeSH (Medical Subject Headings)

### What is MeSH?

MeSH is a controlled vocabulary thesaurus for indexing biomedical literature:
- **Hierarchical structure**: Organized in tree structures
- **Consistent indexing**: Same concept always tagged the same way
- **Comprehensive**: Covers diseases, drugs, anatomy, techniques, etc.
- **Indexing**: NLM assigns MeSH using automated indexing and curation; recent and non-MEDLINE records can lack MeSH

### Finding MeSH Terms

**MeSH Browser**: https://meshb.nlm.nih.gov/search

**Example**:
```
Search: "heart attack"
MeSH term: "Myocardial Infarction"
```

**In PubMed**:
1. Search with keyword
2. Open a relevant article record and inspect its MeSH terms when present
3. Confirm descriptors in the MeSH Browser
4. Combine descriptors with title/abstract synonyms

### Using MeSH in Searches

**Basic MeSH search**:
```
"Diabetes Mellitus"[MeSH]
"CRISPR-Cas Systems"[MeSH]
"Alzheimer Disease"[MeSH]
"Neoplasms"[MeSH]
```

**MeSH with subheadings**:
```
"Diabetes Mellitus/drug therapy"[MeSH]
"Neoplasms/genetics"[MeSH]
"Heart Failure/prevention and control"[MeSH]
```

**Common subheadings**:
- `/drug therapy`: Drug treatment
- `/diagnosis`: Diagnostic aspects
- `/genetics`: Genetic aspects
- `/epidemiology`: Occurrence and distribution
- `/prevention and control`: Prevention methods
- `/etiology`: Causes
- `/surgery`: Surgical treatment
- `/metabolism`: Metabolic aspects

### MeSH Explosion

By default, MeSH searches include narrower terms (explosion):

```
"Neoplasms"[MeSH]
# Includes: Breast Neoplasms, Lung Neoplasms, etc.
```

**Disable explosion** (exact term only):
```
"Neoplasms"[MeSH:NoExp]
```

### MeSH Major Topic

Search only where MeSH term is a major focus:

```
"Diabetes Mellitus"[MeSH Major Topic]
# Only papers where diabetes is main topic
```

## Field Tags

Field tags specify which part of the record to search.

### Common Field Tags

**Title and Abstract**:
```
cancer[Title]                    # In title only
treatment[Title/Abstract]        # In title or abstract
"machine learning"[Title/Abstract]
```

**Author**:
```
"Smith J"[Author]
"Doudna JA"[Author]
"Collins FS"[Author]
```

**Author - Full Name**:
```
"Smith, John"[Full Author Name]
```

**Journal**:
```
"Nature"[Journal]
"Science"[Journal]
"New England Journal of Medicine"[Journal]
"Nat Commun"[Journal]           # Abbreviated form
```

**Publication Date**:
```
2023[Publication Date]
2020:2024[Publication Date]      # Date range
2023/01/01:2023/12/31[Publication Date]
```

**Date Created**:
```
2023[Date - Create]              # When added to PubMed
```

**Publication Type**:
```
"Review"[Publication Type]
"Clinical Trial"[Publication Type]
"Meta-Analysis"[Publication Type]
"Randomized Controlled Trial"[Publication Type]
```

**Language**:
```
English[Language]
French[Language]
```

**DOI**:
```
10.1038/nature12345[DOI]
```

**PMID (PubMed ID)**:
```
12345678[PMID]
```

**Article ID**:
```
PMC1234567[PMC]                  # PubMed Central ID
```

### Less Common But Useful Tags

```
humans[MeSH Terms]               # Only human studies
animals[MeSH Terms]              # Only animal studies
"United States"[Place of Publication]
nih[Grant Number]                # NIH-funded research
"Female"[MeSH Terms]                    # Female subjects
"Aged, 80 and over"[MeSH Terms]        # Elderly subjects
```

## Boolean Operators

Combine search terms with Boolean logic.

### AND

Both terms must be present (default behavior):

```
diabetes AND treatment
"CRISPR-Cas9" AND "gene editing"
cancer AND immunotherapy AND "clinical trial"[Publication Type]
```

### OR

Either term must be present:

```
"heart attack" OR "myocardial infarction"
diabetes OR "diabetes mellitus"
CRISPR OR Cas9 OR "gene editing"
```

**Use case**: Synonyms and related terms

### NOT

Exclude terms:

```
cancer NOT review
diabetes NOT animal
"machine learning" NOT "deep learning"
```

**Caution**: May exclude relevant papers that mention both terms.

### Combining Operators

Use parentheses for complex logic:

```
(diabetes OR "diabetes mellitus") AND (treatment OR therapy)

("CRISPR" OR "gene editing") AND ("therapeutic" OR "therapy") 
  AND 2020:2024[Publication Date]

(cancer OR neoplasm) AND (immunotherapy OR "immune checkpoint inhibitor") 
  AND ("clinical trial"[Publication Type] OR "randomized controlled trial"[Publication Type])
```

## Advanced Search Builder

**Access**: https://pubmed.ncbi.nlm.nih.gov/advanced/

**Features**:
- Visual query builder
- Add multiple query boxes
- Select field tags from dropdowns
- Combine with AND/OR/NOT
- Preview results
- Shows final query string
- Save queries

**Workflow**:
1. Add search terms in separate boxes
2. Select field tags
3. Choose Boolean operators
4. Preview results
5. Refine as needed
6. Copy final query string
7. Use in scripts or save

**Example built query**:
```
#1: "Diabetes Mellitus, Type 2"[MeSH]
#2: "Metformin"[MeSH]
#3: "Clinical Trial"[Publication Type]
#4: 2020:2024[Publication Date]
#5: #1 AND #2 AND #3 AND #4
```

## Filters and Limits

### Article Types

```
"Review"[Publication Type]
"Systematic Review"[Publication Type]
"Meta-Analysis"[Publication Type]
"Clinical Trial"[Publication Type]
"Randomized Controlled Trial"[Publication Type]
"Case Reports"[Publication Type]
"Comparative Study"[Publication Type]
```

### Specie

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

