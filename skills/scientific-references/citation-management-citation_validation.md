---
id: sciref-citation-management-citation-validation
name: "Scientific Ref: Citation Validation Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (citation-management): Citation Validation Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "citation management citation validation"
  - "citacao management citacao validation"
  - "citation validation guide"
keywords:
  - "citation"
  - "management"
  - "validation"
  - "citacao"
  - "specialized"
  - "scientific"
  - "reference"
---

# Citation Validation Guide

Comprehensive guide to validating citation accuracy, completeness, and formatting in BibTeX files.

## Overview

Citation validation ensures:
- All citations are accurate and complete
- DOIs resolve correctly
- Required fields are present
- No duplicate entries
- Proper formatting and syntax
- Links are accessible

Validation should be performed:
- After extracting metadata
- Before manuscript submission
- After manual edits to BibTeX files
- Periodically for maintained bibliographies

## Validation Categories

### 1. DOI Verification

**Purpose**: Ensure DOIs are valid and resolve correctly.

#### What to Check

**DOI format**:
```
Valid:   10.1038/s41586-021-03819-2
Valid:   10.1126/science.aam9317
Syntactically plausible but requires lookup: 10.1038/invalid
Invalid: doi:10.1038/... (should omit "doi:" prefix in BibTeX)
```

**DOI resolution**:
- DOI should resolve via https://doi.org/
- Should redirect to actual article
- Should not return 404 or error

**Metadata consistency**:
- CrossRef metadata should match BibTeX
- Author names should align
- Title should match
- Year should match

#### How to Validate

**Manual check**:
1. Copy DOI from BibTeX
2. Visit https://doi.org/10.1038/nature12345
3. Verify it redirects to correct article
4. Check metadata matches

**Automated check** (recommended):
```bash
python scripts/validate_citations.py references.bib --check-dois
```

**Process**:
1. Extract all DOIs from BibTeX file
2. Query Crossref `/works/{doi}`; on 404, query DataCite `/dois/{doi}`
3. If both lack a record, GET `doi.org/{doi}` without following the redirect
4. A registration record or resolver redirect confirms registration; resolver 404 is an error
5. Report timeouts, 429/5xx, and malformed responses as `doi_unverified` warnings

The script does not compare bibliographic fields or test the publisher landing
page. Review title/authors/year manually; a registered DOI can still identify
the wrong work. Retraction status also requires a separate publisher check.

#### Common Issues

**Broken DOIs**:
- Typos in DOI
- Publisher changed DOI (rare)
- A retracted article normally retains its DOI; check its publication status separately
- Solution: Find correct DOI from publisher site

**Mismatched metadata**:
- BibTeX has old/incorrect information
- Solution: Re-extract metadata from CrossRef

**Missing DOIs**:
- Older articles may not have DOIs
- Acceptable for pre-2000 publications
- Add URL or PMID instead

### 2. Required Fields

**Purpose**: Ensure all necessary information is present.

#### Required by Entry Type

**@article**:
```bibtex
author   % REQUIRED
title    % REQUIRED
journal  % REQUIRED
year     % REQUIRED
volume   % Highly recommended
pages    % Highly recommended
doi      % Highly recommended for modern papers
```

**@book**:
```bibtex
author OR editor  % REQUIRED (at least one)
title            % REQUIRED
publisher        % REQUIRED
year             % REQUIRED
isbn             % Recommended
```

**@inproceedings**:
```bibtex
author     % REQUIRED
title      % REQUIRED
booktitle  % REQUIRED (conference/proceedings name)
year       % REQUIRED
pages      % Recommended
```

**@incollection** (book chapter):
```bibtex
author     % REQUIRED
title      % REQUIRED (chapter title)
booktitle  % REQUIRED (book title)
publisher  % REQUIRED
year       % REQUIRED
editor     % Recommended
pages      % Recommended
```

**@phdthesis**:
```bibtex
author  % REQUIRED
title   % REQUIRED
school  % REQUIRED
year    % REQUIRED
```

**@misc** (preprints, datasets, etc.):
```bibtex
author  % REQUIRED
title   % REQUIRED
year    % REQUIRED
howpublished  % Recommended (bioRxiv, Zenodo, etc.)
doi OR url    % At least one required
```

#### Validation Script

```bash
python scripts/validate_citations.py references.bib
```

**Output**:
```
Error: Entry 'Smith2024' missing required field 'journal'
Error: Entry 'Doe2023' missing required field 'year'
Warning: Entry 'Jones2022' missing recommended field 'volume'
```

### 3. Author Name Formatting

**Purpose**: Ensure consistent, correct author name formatting.

#### Proper Format

**Recommended BibTeX format**:
```bibtex
author = {Last1, First1 and Last2, First2 and Last3, First3}
```

**Examples**:
```bibtex
% Correct
author = {Smith, John}
author = {Smith, John A.}
author = {Smith, John Andrew}
author = {Smith, John and Doe, Jane}
author = {Smith, John and Doe, Jane and Johnson, Mary}

% For many authors
author = {Smith, John and Doe, Jane and others}

% Incorrect
author = {John Smith}  % First Last format (not recommended)
author = {Smith, J.; Doe, J.}  % Semicolon separator (wrong)
author = {Smith J, Doe J}  % Missing commas
```

#### Special Cases

**Suffixes (Jr., III, etc.)**:
```bibtex
author = {King, Jr., Martin Luther}
```

**Multiple surnames (hyphenated)**:
```bibtex
author = {Smith-Jones, Mary}
```

**Van, von, de, etc.**:
```bibtex
author = {van der Waals, Johannes}
author = {de Broglie, Louis}
```

**Organizations as authors**:
```bibtex
author = {{World Health Organization}}
% Double braces treat as single author
```

#### Validation Checks

**Automated validation**:
```bash
python scripts/validate_citations.py references.bib
```

**Checks for**:
- Proper separator (and, not &, ; , etc.)
- Comma placement
- Empty author fields
- Malformed names

### 4. Data Consistency

**Purpose**: Ensure all fields contain valid, reasonable values.

#### Year Validation

**Valid years**:
```bibtex
year = {2024}    % Current/recent
year = {1953}    % Watson & Crick DNA structure (historical)
year = {1665}    % Hooke's Micrographia (very old)
```

**Invalid years**:
```bibtex
year = {24}      % Two digits (ambiguous)
year = {202}     % Typo
year = {3025}    % Implausible future year
year = {0}       % Obviously wrong
```

**Check**:
- Four digits
- Reasonable range (1600-current+1)
- Not all zeros

#### Volume/Number Validation

```bibtex
volume = {123}      % Numeric
volume = {12}       % Valid
number = {3}        % Valid
number = {S1}       % Supplement issue (valid)
```

**Invalid**:
```bibtex
volume = {Vol. 123}  % Should be just number
number = {Issue 3}   % Should be just number
```

#### Page Range Validation

**Correct format**:
```bibtex
pages = {123--145}    % En-dash (two hyphens)
pages = {e0123456}    % PLOS-style article ID
pages = {123}         % Single page
```

**Incorrect format**:
```bibtex
pages = {123-145}     % Single hyphen (use --)
pages = {pp. 123-145} % Remove "pp."
pages = {123–145}    

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

