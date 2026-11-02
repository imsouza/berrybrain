---
id: sciref-literature-review-citation-styles
name: "Scientific Ref: Citation Styles Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (literature-review): Citation Styles Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "literature review citation styles"
  - "literatura revisao citacao styles"
  - "citation styles reference"
keywords:
  - "literature"
  - "review"
  - "citation"
  - "styles"
  - "literatura"
  - "revisao"
  - "citacao"
  - "specialized"
  - "scientific"
  - "reference"
---

# Citation Styles Reference

Reviewed 2026-09-30. This is a formatting aid; all sample author/title/page combinations below are illustrative, not verified references. Replace placeholders and use a current CSL style plus the target venue instructions for final output. The DOI-checking script verifies registration/metadata, not style compliance.

## APA Style (7th Edition)

### Journal Articles

**Format**: Author, A. A., Author, B. B., & Author, C. C. (Year). Title of article. *Title of Periodical*, *volume*(issue), page range. https://doi.org/xx.xxx/yyyy

**Example**: Smith, J. D., Johnson, M. L., & Williams, K. R. (2023). Machine learning approaches in drug discovery. *Nature Reviews Drug Discovery*, *22*(4), 301-318. [DOI URL]

### Books

**Format**: Author, A. A. (Year). *Title of work: Capital letter also for subtitle*. Publisher Name. https://doi.org/xxxx

**Example**: Kumar, V., Abbas, A. K., & Aster, J. C. (2021). *Robbins and Cotran pathologic basis of disease* (10th ed.). Elsevier.

### Book Chapters

**Format**: Author, A. A., & Author, B. B. (Year). Title of chapter. In E. E. Editor & F. F. Editor (Eds.), *Title of book* (pp. xx-xx). Publisher.

**Example**: Brown, P. O., & Botstein, D. (2020). Exploring the new world of the genome with DNA microarrays. In M. B. Eisen & P. O. Brown (Eds.), *DNA microarrays: A molecular cloning manual* (pp. 1-45). Cold Spring Harbor Laboratory Press.

### Preprints

**Format**: Author, A. A., & Author, B. B. (Year). Title of preprint. *Repository Name*. https://doi.org/xxxx

**Example**: Zhang, Y., Chen, L., & Wang, H. (2024). Novel therapeutic targets in Alzheimer's disease. *bioRxiv*. [preprint DOI URL]

### Conference Papers

**Format**: Author, A. A. (Year, Month day-day). Title of paper. In E. E. Editor (Ed.), *Title of conference proceedings* (pp. xx-xx). Publisher. https://doi.org/xxxx

---

## Nature Style

### Journal Articles

**Format**: Author, A. A., Author, B. B. & Author, C. C. Title of article. *J. Name* **volume**, page range (year).

**Example**: Smith, J. D., Johnson, M. L. & Williams, K. R. Machine learning approaches in drug discovery. *Nat. Rev. Drug Discov.* **22**, 301-318 (2023).

### Books

**Format**: Author, A. A. & Author, B. B. *Book Title* (Publisher, Year).

**Example**: Kumar, V., Abbas, A. K. & Aster, J. C. *Robbins and Cotran Pathologic Basis of Disease* 10th edn (Elsevier, 2021).

### Multiple Authors

- Nature reference lists: list all authors through five; above five use the first author followed by "et al.". Other Nature Portfolio journals may differ; check the actual journal instructions.

**Example**: Zhang, Y. et al. Novel therapeutic targets in Alzheimer's disease. *bioRxiv* [preprint DOI URL] (2024).

---

## Chicago Style (18th Edition, Author-Date)

### Journal Articles

**Format**: Author, First Name Middle Initial. Year. "Article Title." *Journal Title* volume, no. issue (Month): page range. https://doi.org/xxxx.

**Example**: Smith, John D., Mary L. Johnson, and Karen R. Williams. 2023. "Machine Learning Approaches in Drug Discovery." *Nature Reviews Drug Discovery* 22, no. 4 (April): 301-318. [DOI URL].

Reference lists include up to six authors; above six list the first three plus et al. Three or more authors use first author plus et al. in text. Current Chicago no longer requires a book publication place.

### Books

**Format**: Author, First Name Middle Initial. Year. *Book Title: Subtitle*. Edition. Publisher.

**Example**: Kumar, Vinay, Abul K. Abbas, and Jon C. Aster. 2021. *Robbins and Cotran Pathologic Basis of Disease*. 10th ed. Elsevier.

---

## Vancouver Style (Numbered)

### Journal Articles

**Format**: Author AA, Author BB, Author CC. Title of article. Abbreviated Journal Name. Year;volume(issue):page range.

**Example**: Smith JD, Johnson ML, Williams KR. Machine learning approaches in drug discovery. Nat Rev Drug Discov. 2023;22(4):301-18.

### Books

**Format**: Author AA, Author BB. Title of book. Edition. Place: Publisher; Year.

**Example**: Kumar V, Abbas AK, Aster JC. Robbins and Cotran pathologic basis of disease. 10th ed. Philadelphia: Elsevier; 2021.

### Citation in Text

Use superscript numbers in order of appearance: "Recent studies^1,2^ have shown..."

---

## IEEE Style

### Journal Articles

**Format**: [#] A. A. Author, B. B. Author, and C. C. Author, "Title of article," *Abbreviated Journal Name*, vol. x, no. x, pp. xxx-xxx, Month Year.

**Example**: [1] J. D. Smith, M. L. Johnson, and K. R. Williams, "Machine learning approaches in drug discovery," *Nat. Rev. Drug Discov.*, vol. 22, no. 4, pp. 301-318, Apr. 2023.

### Books

**Format**: [#] A. A. Author, *Title of Book*, xth ed. City, State: Publisher, Year.

**Example**: [2] V. Kumar, A. K. Abbas, and J. C. Aster, *Robbins and Cotran Pathologic Basis of Disease*, 10th ed. Philadelphia, PA: Elsevier, 2021.

---

## Common Abbreviations for Journal Names

- Nature: Nature (single-word journal titles are not shortened)
- Science: Science
- Cell: Cell
- Nature Reviews Drug Discovery: Nat. Rev. Drug Discov.
- Journal of the American Chemical Society: J. Am. Chem. Soc.
- Proceedings of the National Academy of Sciences: Proc. Natl. Acad. Sci. U.S.A.
- PLOS ONE: PLoS ONE
- Bioinformatics: Bioinformatics
- Nucleic Acids Research: Nucleic Acids Res.

---

## DOI Best Practices

1. **Always verify DOIs**: Use the verify_citations.py script to check all DOIs
2. **Format as URLs**: https://doi.org/10.xxxx/yyyy (preferred over doi:10.xxxx/yyyy)
3. **Separate punctuation from identifiers**: APA omits a final period after a DOI URL; other styles may differ. Do not copy prose punctuation into the identifier
4. **Resolve redirects**: Check that DOIs resolve to the correct article

---

## In-Text Citation Guidelines

### APA Style
- (Smith et al., 2023)
- Smith et al. (2023) demonstrated...
- Multiple citations: (Brown, 2022; Smith et al., 2023; Zhang, 2024)

### Nature Style
- Superscript numbers: Recent studies^1,2^ have shown...
- Or: Recent studies (refs 1,2) have shown...

### Chicago Style
- (Smith et al. 2023) for three or more authors
- Smith et al. (2023) found...

---

## Reference List Organization

### By Citation Style
- **APA, Chicago**: Alphabetical by first author's last name
- **Nature, Vancouver, IEEE**: Numerical order of first appearance in text

### Hanging Indents
Most styles use hanging indents where the first line is flush left and subsequent lines are indented.

### Consistency
Maintain consi

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

