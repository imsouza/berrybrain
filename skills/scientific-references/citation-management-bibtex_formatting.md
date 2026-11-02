---
id: sciref-citation-management-bibtex-formatting
name: "Scientific Ref: BibTeX Formatting Guide"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (citation-management): BibTeX Formatting Guide"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "citation management bibtex formatting"
  - "citacao management bibtex formatting"
  - "bibtex formatting guide"
keywords:
  - "citation"
  - "management"
  - "bibtex"
  - "formatting"
  - "citacao"
  - "specialized"
  - "scientific"
  - "reference"
---

# BibTeX Formatting Guide

Comprehensive guide to BibTeX entry types, required fields, formatting conventions, and best practices.

## Overview

BibTeX is the standard bibliography format for LaTeX documents. Proper formatting ensures:
- Correct citation rendering
- Consistent formatting
- Compatibility with citation styles
- No compilation errors

This guide covers all common entry types and formatting rules.

## Entry Types

### @article - Journal Articles

**Most common entry type** for peer-reviewed journal articles.

**Required fields**:
- `author`: Author names
- `title`: Article title
- `journal`: Journal name
- `year`: Publication year

**Optional fields**:
- `volume`: Volume number
- `number`: Issue number
- `pages`: Page range
- `month`: Publication month
- `doi`: Digital Object Identifier
- `url`: URL
- `note`: Additional notes

**Template**:
```bibtex
@article{CitationKey2024,
  author  = {Last1, First1 and Last2, First2},
  title   = {Article Title Here},
  journal = {Journal Name},
  year    = {2024},
  volume  = {10},
  number  = {3},
  pages   = {123--145},
  doi     = {10.1234/journal.2024.123456},
  month   = jan
}
```

**Example**:
```bibtex
@article{Jumper2021,
  author  = {Jumper, John and Evans, Richard and Pritzel, Alexander and others},
  title   = {Highly Accurate Protein Structure Prediction with {AlphaFold}},
  journal = {Nature},
  year    = {2021},
  volume  = {596},
  number  = {7873},
  pages   = {583--589},
  doi     = {10.1038/s41586-021-03819-2}
}
```

### @book - Books

**For entire books**.

**Required fields**:
- `author` OR `editor`: Author(s) or editor(s)
- `title`: Book title
- `publisher`: Publisher name
- `year`: Publication year

**Optional fields**:
- `volume`: Volume number (if multi-volume)
- `series`: Series name
- `address`: Publisher location
- `edition`: Edition number
- `isbn`: ISBN
- `url`: URL

**Template**:
```bibtex
@book{CitationKey2024,
  author    = {Last, First},
  title     = {Book Title},
  publisher = {Publisher Name},
  year      = {2024},
  edition   = {3},
  address   = {City, Country},
  isbn      = {978-0-123-45678-9}
}
```

**Example**:
```bibtex
@book{Kumar2021,
  author    = {Kumar, Vinay and Abbas, Abul K. and Aster, Jon C.},
  title     = {Robbins and Cotran Pathologic Basis of Disease},
  publisher = {Elsevier},
  year      = {2021},
  edition   = {10},
  address   = {Philadelphia, PA},
  isbn      = {978-0-323-53113-9}
}
```

### @inproceedings - Conference Papers

**For papers in conference proceedings**.

**Required fields**:
- `author`: Author names
- `title`: Paper title
- `booktitle`: Conference/proceedings name
- `year`: Year

**Optional fields**:
- `editor`: Proceedings editor(s)
- `volume`: Volume number
- `series`: Series name
- `pages`: Page range
- `address`: Conference location
- `month`: Conference month
- `organization`: Organizing body
- `publisher`: Publisher
- `doi`: DOI

**Template**:
```bibtex
@inproceedings{CitationKey2024,
  author    = {Last, First},
  title     = {Paper Title},
  booktitle = {Proceedings of Conference Name},
  year      = {2024},
  pages     = {123--145},
  address   = {City, Country},
  month     = jun
}
```

**Example**:
```bibtex
@inproceedings{Vaswani2017,
  author    = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and others},
  title     = {Attention is All You Need},
  booktitle = {Advances in Neural Information Processing Systems 30 (NeurIPS 2017)},
  year      = {2017},
  pages     = {5998--6008},
  address   = {Long Beach, CA}
}
```

**Note**: `@conference` is an alias for `@inproceedings`.

### @incollection - Book Chapters

**For chapters in edited books**.

**Required fields**:
- `author`: Chapter author(s)
- `title`: Chapter title
- `booktitle`: Book title
- `publisher`: Publisher name
- `year`: Publication year

**Optional fields**:
- `editor`: Book editor(s)
- `volume`: Volume number
- `series`: Series name
- `type`: Type of section (e.g., "chapter")
- `chapter`: Chapter number
- `pages`: Page range
- `address`: Publisher location
- `edition`: Edition
- `month`: Month

**Template**:
```bibtex
@incollection{CitationKey2024,
  author    = {Last, First},
  title     = {Chapter Title},
  booktitle = {Book Title},
  editor    = {Editor, Last and Editor2, Last},
  publisher = {Publisher Name},
  year      = {2024},
  pages     = {123--145},
  chapter   = {5}
}
```

**Example**:
```bibtex
@incollection{Brown2020,
  author    = {Brown, Peter O. and Botstein, David},
  title     = {Exploring the New World of the Genome with {DNA} Microarrays},
  booktitle = {DNA Microarrays: A Molecular Cloning Manual},
  editor    = {Eisen, Michael B. and Brown, Patrick O.},
  publisher = {Cold Spring Harbor Laboratory Press},
  year      = {2020},
  pages     = {1--45},
  address   = {Cold Spring Harbor, NY}
}
```

### @phdthesis - Doctoral Dissertations

**For PhD dissertations and theses**.

**Required fields**:
- `author`: Author name
- `title`: Thesis title
- `school`: Institution
- `year`: Year

**Optional fields**:
- `type`: Type (e.g., "PhD dissertation", "PhD thesis")
- `address`: Institution location
- `month`: Month
- `url`: URL
- `note`: Additional notes

**Template**:
```bibtex
@phdthesis{CitationKey2024,
  author = {Last, First},
  title  = {Dissertation Title},
  school = {University Name},
  year   = {2024},
  type   = {{PhD} dissertation},
  address = {City, State}
}
```

**Example**:
```bibtex
@phdthesis{Johnson2023,
  author  = {Johnson, Mary L.},
  title   = {Novel Approaches to Cancer Immunotherapy Using {CRISPR} Technology},
  school  = {Stanford University},
  year    = {2023},
  type    = {{PhD} dissertation},
  address = {Stanford, CA}
}
```

**Note**: `@mastersthesis` is similar but for Master's theses.

### @mastersthesis - Master's Theses

**For Master's theses**.

**Required fields**:
- `author`: Author name
- `title`: Thesis title
- `school`: Institution
- `year`: Year

**Template**:
```bibtex
@mastersthesis{CitationKey2024,
  author = {Last, First},
  title  = {Thesis Title},
  school = {University Name},
  year   = {2024}
}
```

### @misc - Miscellaneous

**For items that don't fit other categories** (preprints, datasets, software, websites, etc.).

**Required fields**:
- `author` (if known)
- `title`
- `year`

**Optional fields**:
- `howpublished`: Repository, website, format
- `url`: URL
- `doi`: DOI
- `note`: Additional information
- `month`: Month

**Template for preprints**:
```bibtex
@misc{CitationKey2024,
  author       = {Last, F

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

