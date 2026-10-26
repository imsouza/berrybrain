---
id: sciref-literature-review-core-workflow
name: "Scientific Ref: Core Workflow"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (literature-review): Core Workflow"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "literature review core workflow"
  - "literatura revisao core workflow"
  - "core workflow"
keywords:
  - "literature"
  - "review"
  - "core"
  - "workflow"
  - "literatura"
  - "revisao"
  - "specialized"
  - "scientific"
  - "reference"
---

# Core Workflow

Illustrative workflow; example queries, dates, counts, and numerical findings are not executed review results. Run commands from this skill directory, using paths to your review workspace.

All seven phases in full: planning and scoping, systematic search, screening and
selection, data extraction and quality assessment, synthesis and analysis, citation
verification, and document generation.

## Core Workflow

Literature reviews follow a structured, multi-phase workflow:

### Phase 1: Planning and Scoping

1. **Define Research Question**: Use PICO framework (Population, Intervention, Comparison, Outcome) for clinical/biomedical reviews
   - Example: "What is the efficacy of CRISPR-Cas9 (I) for treating sickle cell disease (P) compared to standard care (C)?"

2. **Establish Scope and Objectives**:
   - Define clear, specific research questions
   - Determine review type (narrative, systematic, scoping, meta-analysis)
   - Set boundaries (time period, geographic scope, study types)

3. **Develop Search Strategy**:
   - Identify 2-4 main concepts from research question
   - List synonyms, abbreviations, and related terms for each concept
   - Plan Boolean operators (AND, OR, NOT) to combine terms
   - Select complementary bibliographic databases and registries appropriate to the question
   - **Optionally use parallel-web (`parallel-cli search`) for initial scoping** to quickly gauge the landscape before formal database searches

4. **Set Inclusion/Exclusion Criteria**:
   - Date range (e.g., the explicitly historical interval 2015-2024)
   - Language (typically English, or specify multilingual)
   - Publication types (peer-reviewed, preprints, reviews)
   - Study designs (RCTs, observational, in vitro, etc.)
   - Document all criteria clearly

### Phase 2: Systematic Literature Search

1. **Multi-Database Search**:

   Select bibliographic databases and registries appropriate for the domain. Use optional web search for scoping and supplementary discovery; record it separately from database exports.

   **Supplementary web discovery (parallel-web):**
   - Use `parallel-cli search` with academic domain filtering for broad scholarly coverage
   - Consider academic-focused and general searches; ranked samples do not guarantee complete retrieval
   ```bash
   mkdir -p sources
   # Illustrative ranked sample; not a complete search
   parallel-cli search "your research topic" -q "keyword1" -q "keyword2" \
     --json --max-results 10 --excerpt-max-chars-total 27000 \
     --include-domains "scholar.google.com,arxiv.org,pubmed.ncbi.nlm.nih.gov,semanticscholar.org,biorxiv.org,medrxiv.org,ncbi.nlm.nih.gov,nature.com,science.org,ieee.org,acm.org,springer.com,wiley.com,cell.com,pnas.org,nih.gov" \
     -o sources/litreview_<topic>-academic.json

   # General search for supplementary sources
   parallel-cli search "your research topic" -q "keyword1" -q "keyword2" \
     --json --max-results 10 --excerpt-max-chars-total 27000 \
     -o sources/litreview_<topic>-general.json
   ```
   - Use `parallel-cli extract --full-content` to request content from accessible paper URLs; check for truncation and retrieval errors
   ```bash
   parallel-cli extract "https://arxiv.org/abs/1706.03762" --full-content --json
   ```

   **Biomedical & Life Sciences:**
   - Search PubMed via its interface or E-utilities; PMC has different full-text coverage
   - Search bioRxiv/medRxiv interfaces, or retrieve date-range API metadata and explicitly filter it
   - See `database_strategies.md` for exact requests, authentication, and export limits

   **General Scientific Literature:**
   - Search arXiv via direct API (preprints in physics, math, CS, q-bio)
   - Search Semantic Scholar using its documented relevance or bulk API as appropriate
   - Use Google Scholar manually for supplementary discovery and citation chaining; preserve search and screening limits

   Biological entity databases can inform background, but do not count as
   bibliographic sources simply because they contain references.

2. **Document Search Parameters**:
   ```markdown
   ## Search Strategy

   ### Database: PubMed
   - **Date searched**: 2024-10-25
   - **Date range**: 2015-01-01 to 2024-10-25
   - **Search string**:
     ```
     ("CRISPR"[Title] OR "Cas9"[Title])
     AND ("Anemia, Sickle Cell"[MeSH Terms] OR "SCD"[Title/Abstract])
     AND 2015:2024[Publication Date]
     ```
   - **Results**: 247 articles
   ```

   Repeat for each database searched.

3. **Export and Aggregate Results**:
   - Export results in JSON format from each database
   - Normalize raw provider responses into a JSON array, preserving raw exports and provenance separately
   - Use `scripts/search_databases.py` for post-processing:
     ```bash
     python scripts/search_databases.py combined_results.json \
       --deduplicate \
       --format markdown \
       --output aggregated_results.md
     ```

### Phase 3: Screening and Selection

1. **Deduplication**:
   ```bash
   python scripts/search_databases.py results.json --deduplicate --format json --output unique_results.json
   ```
   - Keeps first normalized DOI; title fallback compares DOI-less records only. Review matches and retain raw duplicates for enrichment
   - Document number of duplicates removed

2. **Title Screening**:
   - Review all titles against inclusion/exclusion criteria
   - Exclude obviously irrelevant studies
   - Document number excluded at this stage

3. **Abstract Screening**:
   - Read abstracts of remaining studies
   - Apply inclusion/exclusion criteria rigorously
   - Document reasons for exclusion

4. **Full-Text Screening**:
   - Obtain full texts of remaining studies
   - Conduct detailed review against all criteria
   - Document specific reasons for exclusion
   - Record final number of included studies

5. **Create PRISMA Flow Diagram**:
   - Use the official template matching new/updated review and source types.
   - Track records identified and removed before screening, records screened
     and excluded, reports sought/not retrieved/assessed, excluded reports with
     reasons, and included studies plus reports of those studies.
   - Reconcile counts at each transition; do not invent one included-study count
     from the number of publications. Maintain a study-to-report map.

### Phase 4: Data Extraction and Quality Assessment

1. **Extract Key Data** from each included study:
   - Study metadata (authors, year, journal, DOI)
   - Study design and methods


*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

